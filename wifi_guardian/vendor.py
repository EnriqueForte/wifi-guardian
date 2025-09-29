"""
Consulta de fabricante (OUI) a partir de una MAC.
Usa una base local que la librería descarga/gestiona.
"""

from __future__ import annotations
from typing import Optional
from mac_vendor_lookup import MacLookup

# Singleton simple para evitar re-cargar la DB muchas veces
_lookup: Optional[MacLookup] = None

def vendor_from_mac(mac: str) -> str:
    """
    Devuelve el nombre del fabricante para una MAC (si existe).
    - Normaliza may/min.
    - Captura excepciones y devuelve "" si no hay match.
    """
    global _lookup
    try:
        if not mac:
            return ""
        normalized = mac.strip().lower().replace("-", ":")
        if len(normalized.split(":")[0]) < 2:
            return ""
        if _lookup is None:
            _lookup = MacLookup()  # carga DB (si ya existe localmente)
        return _lookup.lookup(normalized)  # puede lanzar si no encuentra
    except Exception:
        return ""

def update_local_db() -> bool:
    """
    Descarga/actualiza la base de datos de OUIs (requiere Internet).
    Devuelve True si se actualiza sin errores.
    """
    global _lookup
    try:
        if _lookup is None:
            _lookup = MacLookup()
        _lookup.update_vendors()
        return True
    except Exception:
        return False
