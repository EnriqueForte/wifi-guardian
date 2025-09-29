"""
Estrategias extra para resolver nombres de host cuando DNS inverso falla.
- Windows: 'nbtstat -A <ip>' (NetBIOS)
- Linux/macOS: 'getent hosts <ip>' o 'avahi-resolve -a <ip>' si está disponible
Todas las llamadas son 'best-effort': si fallan, devolvemos "".
"""

import platform
import subprocess
import re
from typing import Optional

def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=3)
        return out.stdout or ""
    except Exception:
        return ""

def resolve_extra(ip: str) -> str:
    osname = platform.system().lower()

    if "windows" in osname:
        # nbtstat -A <ip> devuelve un bloque con nombres NetBIOS
        # Buscamos la primera línea con <nombre> <TIPO> <ESTADO>
        text = _run(["nbtstat", "-A", ip])
        # Ejemplos de línea (ES): "Nombre de nodo           Tipo         Estado"
        # Buscamos líneas con el nombre y <00> o similar
        for line in text.splitlines():
            # captura un nombre al principio de la línea (letras/números/-/_), seguido de espacios y un <..>
            m = re.match(r"^\s*([A-Za-z0-9\-\_\.]+)\s+<\w\w>\s+", line)
            if m:
                name = m.group(1).strip()
                # Evita nombres genéricos tipo "WORKGROUP"
                if name and name.upper() not in {"WORKGROUP", "HOME", "MSHOME"}:
                    return name
        return ""

    # Linux / macOS
    # 1) getent hosts <ip>
    text = _run(["getent", "hosts", ip])
    # Formato típico: "192.168.1.10   hostname.local"
    m = re.search(r"\b([A-Za-z0-9\-\_\.]+)\b\s*$", text.strip(), re.MULTILINE)
    if m:
        name = m.group(1)
        if name and name != ip:
            return name

    # 2) avahi-resolve -a <ip>  → "ip\tname.local"
    text = _run(["avahi-resolve", "-a", ip])
    m = re.search(r"\b([A-Za-z0-9\-\_\.]+)\b\s*$", text.strip(), re.MULTILINE)
    if m:
        name = m.group(1)
        if name and name != ip:
            return name

    return ""
