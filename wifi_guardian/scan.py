"""
Escaneo de red y monitorización ARP sin 'netifaces'.

- Inferencia de interfaz/red (ignorando interfaces virtuales comunes).
- Intento preferido: ARP L2 (srp) con doble pasada y reintentos.
- Fallback: ICMP sweep + lectura de ARP del SO, con "touch" TCP para poblar ARP.
- Enriquecimiento de hostnames (NetBIOS/getent/avahi) y fabricante (OUI).
- Etiqueta 'mac:private' para MAC localmente administradas (iOS/Android MAC privada).
- Monitor ARP spoof con manejo cuando no hay pcap/permisos.

Requiere: scapy, psutil. Para vendor: mac-vendor-lookup.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
import socket
import ipaddress
import psutil
import platform
import subprocess
import re
import time
import socket as pysock

from scapy.all import (  # type: ignore
    ARP, Ether, srp, conf, sniff,
    IP, ICMP, sr1
)

from .utils import cidr_from_ip_mask, try_reverse_dns
from .namer import resolve_extra
from .vendor import vendor_from_mac


# Interfaces que solemos querer ignorar para la autodetección
BAD_IFACE_KEYWORDS = (
    "vEthernet", "Hyper-V", "Loopback", "VirtualBox", "VMware",
    "Bluetooth", "TAP", "TUN", "VPN"
)


def infer_default_iface_and_cidr() -> Tuple[str, str]:
    """
    Determina interfaz “principal” y su red en CIDR sin 'netifaces'.
    Ignora interfaces virtuales conocidas.
    """
    # 1) IP local “de salida” (no envía tráfico real)
    primary_ip = None
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
    except Exception:
        primary_ip = None
    finally:
        try:
            if s:
                s.close()
        except Exception:
            pass

    # 2) Recorremos interfaces IPv4 válidas (no loopback, no virtual)
    candidates: List[Tuple[int, str, str]] = []  # (score, iface, cidr)
    for iface, addrs in psutil.net_if_addrs().items():
        if any(k.lower() in iface.lower() for k in BAD_IFACE_KEYWORDS):
            continue
        for a in addrs:
            if getattr(a, "family", None) == socket.AF_INET and a.address and a.netmask:
                if a.address.startswith("127."):
                    continue
                cidr = cidr_from_ip_mask(a.address, a.netmask)
                if cidr:
                    score = 1 if (primary_ip and a.address == primary_ip) else 0
                    candidates.append((score, iface, cidr))

    if not candidates:
        raise RuntimeError("No se pudo inferir una interfaz IPv4 válida para calcular el CIDR.")

    candidates.sort(reverse=True)
    _, best_iface, best_cidr = candidates[0]
    return best_iface, best_cidr


# -----------------------
#  Ayudas de enriquecido
# -----------------------

def _is_locally_administered(mac: str) -> bool:
    """Devuelve True si la MAC es 'locally administered' (MAC privada)."""
    try:
        first = int(mac.split(":")[0], 16)
        return bool(first & 0x02)
    except Exception:
        return False


def _enrich_hostnames(devs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Completa hostnames vacíos probando NetBIOS / getent / avahi (best-effort)."""
    for d in devs:
        if not d.get("hostname"):
            extra = resolve_extra(d["ip"])
            if extra:
                d["hostname"] = extra
                d["note"] = (d.get("note") + (", " if d.get("note") else "")) + "name:extra"
    return devs


def _enrich_vendor(devs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Añade fabricante por OUI a 'note'; marca 'mac:private' y pista de iPhone si aplica."""
    for d in devs:
        mac = (d.get("mac") or "").lower().replace("-", ":")
        host = (d.get("hostname") or "").lower()
        note = d.get("note") or ""
        if mac:
            v = vendor_from_mac(mac)
            if v:
                note += (", " if note else "") + f"vendor:{v}"
            else:
                if _is_locally_administered(mac):
                    note += (", " if note else "") + "mac:private"
                    if "iphone" in host:
                        note += ", guess:Apple(iOS private MAC)"
        d["note"] = note
    return devs


def _finalize(devs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Orden por IP, enriquecer hostname y vendor, y deduplicar por IP (último visto)."""
    # dedupe por IP
    dedup: Dict[str, Dict[str, Any]] = {}
    for d in devs:
        dedup[d["ip"]] = d
    devs = list(dedup.values())
    # enriquecer
    devs = _enrich_hostnames(devs)
    devs = _enrich_vendor(devs)
    # ordenar
    devs.sort(key=lambda d: tuple(int(x) for x in d["ip"].split(".")))
    return devs


# -----------------------
#  Escaneo L2 y Fallback
# -----------------------

def _arp_scan_layer2(cidr: str, iface: str, timeout: int = 3) -> List[Dict[str, Any]]:
    """
    Preferido: ARP a nivel 2 (rápido/fiable). Requiere pcap/Npcap en Windows.
    Hacemos 2 pasadas con retry para “despertar” clientes adormecidos.
    """
    conf.verb = 0
    net = ipaddress.IPv4Network(cidr)
    results: List[Dict[str, Any]] = []

    for _ in range(2):
        answered, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=str(net)),
            iface=iface,
            timeout=timeout + 1,   # un poco más paciente
            retry=1,
            inter=0.02
        )
        for _, r in answered:
            ip = r.psrc
            mac = r.hwsrc
            host = try_reverse_dns(ip)
            results.append({"ip": ip, "mac": mac, "hostname": host, "note": ""})
        time.sleep(0.3)

    return _finalize(results)


def _icmp_ping_sweep(cidr: str, timeout: float = 0.6) -> List[str]:
    """
    Fallback: barrido ICMP (Echo) en toda la subred. Devuelve IPs que respondieron.
    En Windows puede requerir consola de Admin para raw sockets.
    """
    live_ips: List[str] = []
    net = ipaddress.IPv4Network(cidr)
    for ip in net.hosts():
        ip_str = str(ip)
        try:
            ans = sr1(IP(dst=ip_str) / ICMP(), timeout=timeout, verbose=False)
            if ans is not None:
                live_ips.append(ip_str)
        except PermissionError:
            pass
        except Exception:
            pass
    return live_ips


def _touch_host(ip: str, ports=(80, 443, 554, 8009)) -> None:
    """Intenta conexiones TCP cortas para forzar resolución ARP del SO."""
    for p in ports:
        try:
            s = pysock.socket(pysock.AF_INET, pysock.SOCK_STREAM)
            s.settimeout(0.2)
            s.connect_ex((ip, p))  # no lanza excepción
        except Exception:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass


def _read_arp_table() -> Dict[str, str]:
    """
    Lee la tabla ARP del sistema y devuelve {ip -> mac} (minúsculas).
    - Windows: 'arp -a'
    - Linux/macOS: 'ip neigh show'
    """
    osname = platform.system().lower()
    mapping: Dict[str, str] = {}
    if "windows" in osname:
        out = subprocess.run(["arp", "-a"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        text = out.stdout
        for line in text.splitlines():
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F\-]{17})", line)
            if m:
                ip = m.group(1)
                mac = m.group(2).replace("-", ":").lower()
                mapping[ip] = mac
    else:
        out = subprocess.run(["ip", "neigh", "show"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        text = out.stdout
        for line in text.splitlines():
            m_ip = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
            m_mac = re.search(r"lladdr\s+([0-9a-fA-F:]{17})", line)
            if m_ip and m_mac:
                mapping[m_ip.group(1)] = m_mac.group(1).lower()
    return mapping


def _inventory_via_icmp_and_arp(cidr: str) -> List[Dict[str, Any]]:
    """
    Fallback completo: ICMP sweep + "touch" TCP para poblar ARP + lectura ARP del SO.
    """
    ips_up = _icmp_ping_sweep(cidr)

    # Dispara ARP en el SO hacia cada IP viva
    for ip in ips_up:
        _touch_host(ip)
    time.sleep(0.5)  # deja que el SO resuelva ARP

    arp_map = _read_arp_table()
    devices: List[Dict[str, Any]] = []
    for ip in ips_up:
        mac = arp_map.get(ip, "")
        host = try_reverse_dns(ip)
        devices.append({"ip": ip, "mac": mac, "hostname": host, "note": "icmp+os-arp"})

    return _finalize(devices)


def arp_scan(cidr: str, iface: str, timeout: int = 3) -> List[Dict[str, Any]]:
    """
    API pública del escaneo:
      1) Intentar ARP L2 (rápido).
      2) Si falla (sin pcap/Npcap o permisos), usar fallback ICMP + ARP SO.
      3) En ambos caminos, enriquecer hostnames y fabricante y ordenar.
    """
    try:
        return _arp_scan_layer2(cidr, iface, timeout=timeout)
    except Exception:
        return _inventory_via_icmp_and_arp(cidr)


# -----------------------
#  Monitor ARP Spoof
# -----------------------

def monitor_arp_spoof(duration_sec: int = 60):
    """
    Escucha ARP replies durante 'duration_sec' y alerta si una IP “cambia” de MAC.
    Sin pcap/Npcap en Windows o sin permisos, devuelve nota informativa.
    """
    ip_to_mac: Dict[str, str] = {}
    anomalies: List[str] = []

    def handler(pkt):
        if pkt.haslayer(ARP) and pkt[ARP].op == 2:  # is-at
            ip = pkt[ARP].psrc
            mac = pkt[ARP].hwsrc
            prev = ip_to_mac.get(ip)
            if prev and prev != mac:
                anomalies.append(f"ARP cambio sospechoso: {ip} -> {prev} ahora {mac}")
            ip_to_mac[ip] = mac

    try:
        sniff(filter="arp", prn=handler, store=False, timeout=duration_sec)
    except Exception:
        anomalies.append("Sniff ARP no disponible (falta Npcap/WinPcap o permisos).")

    return anomalies
