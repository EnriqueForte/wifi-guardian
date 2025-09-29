"""
Gestión de alias amigables por IP/MAC.
Estructura JSON:
{
  "by_mac": { "aa:bb:cc:dd:ee:ff": {"alias": "Nombre"} },
  "by_ip":  { "192.168.1.100":     {"alias": "Nombre"} }
}
"""

from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import json

def _norm_mac(mac: str) -> str:
    return (mac or "").strip().lower().replace("-", ":") if mac else ""

def load_aliases(path: Path) -> Dict[str, Dict[str, Dict[str, str]]]:
    if not path.exists():
        return {"by_mac": {}, "by_ip": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "by_mac": { _norm_mac(k): v for k, v in (data.get("by_mac") or {}).items() },
            "by_ip":  data.get("by_ip") or {}
        }
    except Exception:
        return {"by_mac": {}, "by_ip": {}}

def apply_aliases(devs: List[Dict[str, Any]], aliases: Dict[str, Dict[str, Dict[str, str]]]) -> int:
    """
    Aplica alias a la lista de dispositivos.
    Añade la clave 'alias' al dispositivo. Devuelve nº de alias aplicados.
    Prioridad: MAC > IP.
    """
    applied = 0
    by_mac = aliases.get("by_mac", {})
    by_ip  = aliases.get("by_ip", {})
    for d in devs:
        mac = _norm_mac(d.get("mac", ""))
        ip  = d.get("ip", "")
        ali = None
        if mac and mac in by_mac and by_mac[mac].get("alias"):
            ali = by_mac[mac]["alias"]
        elif ip in by_ip and by_ip[ip].get("alias"):
            ali = by_ip[ip]["alias"]
        if ali:
            d["alias"] = ali
            note = d.get("note") or ""
            d["note"] = (note + (", " if note else "") + "alias:custom")
            applied += 1
    return applied
