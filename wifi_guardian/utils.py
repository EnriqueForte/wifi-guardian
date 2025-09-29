"""
Funciones auxiliares de red:
- Conversión (IP, máscara) → CIDR.
- Reverse DNS para intentar obtener el hostname de una IP.
"""

import ipaddress
import socket
from typing import Optional

def cidr_from_ip_mask(ip: str, netmask: str) -> Optional[str]:
    """
    Dado una IP y su máscara, devuelve la red en formato CIDR (ej. '192.168.1.0/24').

    Por qué: muchos escaneos (como ARP) trabajan mejor cuando les pasas una red CIDR.
    """
    try:
        network = ipaddress.IPv4Network((ip, netmask), strict=False)  # strict=False permite IP de host
        return str(network)
    except Exception:
        return None

def try_reverse_dns(ip: str) -> str:
    """
    Intenta resolver el nombre de host (PTR) para una IP.
    Si falla, devuelve cadena vacía.

    Útil para enriquecer informes con nombres de dispositivos.
    """
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        return name
    except Exception:
        return ""