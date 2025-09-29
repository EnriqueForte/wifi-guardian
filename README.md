# WiFi Guardian 🔒

Herramienta multi-plataforma (Windows/Linux) para vigilar tu red local, detectar **nuevos/ausentes** dispositivos, alertas de **ARP spoofing** y, en Linux con modo monitor, posibles **deauth 802.11**.  
Genera un informe **HTML** con tema oscuro “hacker”, buscador, ordenación e iconos.

> ⚠️ Úsala **solo en tu propia red** o con permiso expreso. Algunas funciones requieren privilegios de administrador/root.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#)

## ✨ Novedades clave
- 🎨 **Informe HTML** mejorado (tema oscuro, verde neón, iconos SVG, copiar IP/MAC, cabecera sticky, buscador y ordenación).
- 🏷️ **Alias amigables** por IP/MAC con formato sencillo (`device_alias.json`).
- 🏭 **Fabricantes (OUI)**: opción para actualizar la base y anotar el vendor de cada MAC.
- 🧠 **Fallback inteligente**: si ARP L2 no está disponible (p. ej. sin Npcap), usa ICMP+ARP del sistema.
- 🧩 **Baseline** automática para comparar nuevos/ausentes en cada ejecución.

## 🧭 Conceptos
- **Inventario (ARP scan)**: lista IP, MAC y hostname de equipos activos.
- **Baseline**: “foto” de tu red guardada para comparar con futuras ejecuciones.
- **ARP spoofing**: misma IP con distinta MAC → posible MITM en LAN.
- **Deauth 802.11**: expulsión de clientes (requiere Linux + modo monitor).

## 📦 Requisitos
- **Python 3.10+**
- **VSCode** (extensiones: *Python*, *Pylance*)
- **Windows**:
  - **Npcap** (activa *WinPcap Compatible Mode* en el instalador).
  - Consola como **Administrador** para ARP L2.
- **Linux**:
  - `sudo apt install python3-pip net-tools iproute2`
  - (Opcional Deauth) `sudo apt install aircrack-ng` o disponer de `iw`.

## ⚙️ Instalación
```bash
# Crear proyecto y entorno
mkdir wifi-guardian && cd wifi-guardian
python -m venv .venv

# Activar entorno
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Abrir en VSCode
code .
```

**requirements.txt** mínimo:
```
scapy>=2.5.0
psutil>=5.9
typer>=0.12
rich>=13.7
Jinja2>=3.1
```

## ▶️ Uso rápido
```bash
# 1) Escaneo + baseline + informe HTML (autodetecta NIC y CIDR si faltan)
python -m wifi_guardian scan

# 2) Monitor ARP (ej. 180s) con informe
python -m wifi_guardian watch-arp --seconds 180

# 3) Deauth (Linux + modo monitor, ej. wlan0mon)
sudo python -m wifi_guardian deauth --iface wlan0mon --minutes 5
```

### Parámetros útiles
```bash
# Especificando interfaz física y red (Windows suele ser "Ethernet")
python -m wifi_guardian scan --iface "Ethernet" --cidr 192.168.1.0/24

# Aplicar alias y actualizar fabricantes (OUI) antes de escanear
python -m wifi_guardian scan --aliases-file ".\device_alias.json" --update-vendors

# Solo actualizar la base OUI (sin escanear)
python -m wifi_guardian vendors-update
```

> 💡 Listar interfaces que Scapy ve:
> ```bash
> python - << 'PY'
> from scapy.all import conf
> conf.ifaces.show()
> PY
> ```

## 🏷️ Alias amigables
### ¿Dónde pongo mi archivo de alias?

Crea un archivo **privado** con tus alias en la **raíz del proyecto**. Puedes llamarlo:

- `devices_alias.json`

> La app los detecta automáticamente si existen (o puedes pasar la ruta con `--aliases-file`).

```json
{
  "by_mac": {
    "00:90:a9:37:51:c1": { "alias": "NAS" },
    "68:28:6c:58:94:90": { "alias": "PS5" }
  },
  "by_ip": {
    "192.168.1.XXX":   { "alias": "ROUTER" },
    "192.168.1.XXX": { "alias": "SAMSUNG" },
    "192.168.1.XXX": { "alias": "PS5" },
    "192.168.1.XXX": { "alias": "NAS" },
    "192.168.1.XXX": { "alias": "IPHONE14-A" },
    "192.168.1.XXX": { "alias": "IPHONE14-B" }
  }
}
```
- Prioridad **MAC > IP** si coinciden ambos.
- Para móviles con **MAC privada**, usa alias por **IP**.

## 🧪 Informe HTML
- Tema “hacker” (oscuro/neón), KPIs (Totales/Nuevos/Ausentes).
- Tabla con **búsqueda**, **ordenación** y **copiar IP/MAC**.
- Chips de **alias**, **vendor**, “**MAC privada**” y notas técnicas.
- También se genera un resumen **Markdown**.

Los informes se guardan en `./reports/report-YYYYMMDD-HHMMSS.html`.

## 🗂️ Estructura
```
wifi-guardian/
├─ requirements.txt
├─ README.md
└─ wifi_guardian/
   ├─ __init__.py
   ├─ __main__.py        # CLI (scan, watch-arp, deauth, vendors-update)
   ├─ scan.py            # ARP/ICMP + monitor ARP
   ├─ baseline.py        # cargar/guardar baseline + diff
   ├─ report.py          # informe HTML/MD (tema oscuro con buscador & sort)
   ├─ aliases.py         # alias (by_mac/by_ip)
   ├─ utils.py           # utilidades (CIDR, DNS inversa, etc.)
   └─ deauth.py          # detector de deauth (Linux + monitor)
```

## 🧱 Limitaciones
- **Banda 2.4/5 GHz**: no se deduce por ARP/ICMP; requiere API del router o captura 802.11 (modo monitor).
- **ARP spoof** es heurístico (posibles falsos positivos).
- En Windows, para ARP L2: **Npcap** + consola **Administrador**; si no, fallback ICMP+ARP (más lento).

## 🆘 Troubleshooting
- **“Sniffing and sending packets is not available at layer 2”**  
  → Instala **Npcap** con *WinPcap Compatible Mode* y abre la consola como **Administrador**.
- **No ves tus iPhone**  
  → Usa la **interfaz física** correcta (`--iface "Ethernet"` o tu NIC Wi-Fi), y alias por **IP** si usan MAC privada.
- **Sale 192.168.56.1 (VirtualBox)**  
  → Es una red virtual; selecciona la interfaz física o el **CIDR** correcto.

## 👤 Autor
Creado por **Enrique Forte**  
[LinkedIn](https://www.linkedin.com/in/enriqueforte) · [GitHub](https://github.com/EnriqueForte)

## 📄 Licencia
MIT.


