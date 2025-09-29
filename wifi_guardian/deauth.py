"""
Detección de tramas 802.11 de desautenticación (deauth).
Requiere Linux + interfaz en modo monitor (ej.: wlan0mon).
"""

from typing import List
import platform
from scapy.all import Dot11, Dot11Deauth, sniff  # type: ignore

def detect_deauth(iface: str, minutes: int = 5) -> List[str]:
    """
    Captura durante 'minutes' en 'iface' y cuenta tramas deauth.
    También muestra top emisores (dirección MAC fuente) si los hay.

    Importante:
      - En Windows, el modo monitor no está soportado de forma general con Scapy.
      - En Linux, habilita modo monitor antes (airmon-ng/iw).
    """
    if platform.system().lower() != "linux":
        return ["Dectector de deauth solo soportado en Linux con modo monitor."]

    count = {"total": 0}
    offenders = {}  # mac → nº de deauth observadas

    def handler(pkt):
        # Un frame de deauth lleva capa Dot11Deauth; Dot11 tiene direcciones MAC.
        if pkt.haslayer(Dot11Deauth) and pkt.haslayer(Dot11):
            count["total"] += 1
            src = pkt[Dot11].addr2 or "desconocido"
            offenders[src] = offenders.get(src, 0) + 1

    sniff(iface=iface, prn=handler, store=False, timeout=minutes*60)

    # Preparamos notas para el informe
    notes = [f"Deauth frames totales: {count['total']}"]
    if offenders:
        top = sorted(offenders.items(), key=lambda x: x[1], reverse=True)[:5]
        for mac, c in top:
            notes.append(f"Posible emisor de deauth {mac}: {c} frames")
    if count["total"] == 0:
        notes.append("No se observaron deauth en el periodo.")
    return notes
