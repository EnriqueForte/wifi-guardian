"""
Gestión del baseline: guardamos la "fotografía" de dispositivos de una ejecución
para comparar con las siguientes y detectar nuevos/desaparecidos.
"""

from pathlib import Path
import json
from typing import Dict, Any, List

def load_baseline(path: Path) -> Dict[str, Any]:
    """
    Lee baseline desde JSON (si existe). Devuelve {} si no hay o si falla.
    Estructura: {"devices": [ {ip, mac, hostname, note}, ... ]}
    """
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_baseline(path: Path, devices: List[Dict[str, Any]]) -> None:
    """
    Guarda baseline (lista de dispositivos) con indentado para fácil lectura.
    """
    data = {"devices": devices}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def diff_baseline(old: Dict[str, Any], new_devices: List[Dict[str, Any]]):
    """
    Compara baseline antiguo vs. nueva detección.

    Clave de comparación: (IP, MAC) — evita falsos positivos por DHCP si MAC coincide.
    Retorna:
      - added: dispositivos nuevos
      - removed: dispositivos que ya no están
    """
    old_map = { (d.get("ip",""), d.get("mac","")): d for d in old.get("devices", []) }
    new_map = { (d.get("ip",""), d.get("mac","")): d for d in new_devices }
    old_keys = set(old_map.keys())
    new_keys = set(new_map.keys())
    added = [new_map[k] for k in new_keys - old_keys]
    removed = [old_map[k] for k in old_keys - new_keys]
    return added, removed
