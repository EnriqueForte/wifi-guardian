"""
CLI de WiFi Guardian con Typer.
Comandos:
  - scan: escaneo ARP/ICMP + baseline + informe (+ opcional: actualizar base OUI)
  - watch-arp: escucha cambios ARP (posible ARP spoof)
  - deauth: detector de deauth (Linux + monitor)
  - vendors-update: actualiza la base OUI (fabricantes) sin escanear
"""

from __future__ import annotations
import typer
from rich import print
from pathlib import Path

from .scan import infer_default_iface_and_cidr, arp_scan, monitor_arp_spoof
from .baseline import load_baseline, save_baseline, diff_baseline
from .report import write_reports
from .deauth import detect_deauth
from .aliases import load_aliases, apply_aliases  # <-- para alias amigables

app = typer.Typer(add_completion=False, help="WiFi Guardian - escaneo y monitor de tu red local")

@app.command()
def scan(
    cidr: str = typer.Option(None, help="CIDR de la subred (ej: 192.168.1.0/24)"),
    iface: str = typer.Option(None, help="Interfaz a usar (ej: wlan0, Ethernet)"),
    report_dir: Path = typer.Option(Path("reports"), help="Directorio de informes"),
    baseline_file: Path = typer.Option(Path(".wg_baseline.json"), help="Archivo de baseline"),
    aliases_file: Path = typer.Option(Path("device_alias.json"), help="Archivo de alias amigables (IP/MAC→nombre)"),
    update_vendors: bool = typer.Option(False, help="Actualizar la base OUI (requiere Internet) antes de escanear")
):
    """
    Escaneo ARP/ICMP de la red, comparación con baseline y generación de informe.
    Opcionalmente, actualiza la base de OUIs (fabricantes) para anotar vendor:<nombre>.
    """
    try:
        # (Opcional) Actualizar base OUI
        if update_vendors:
            try:
                from .vendor import update_local_db
                ok = update_local_db()
                if ok:
                    print("[yellow]Base OUI actualizada correctamente.[/yellow]")
                else:
                    print("[red]No se pudo actualizar la base OUI (se usará la caché local si existe).[/red]")
            except Exception as e:
                print(f"[red]Error actualizando OUI:[/red] {e}")

        # Autodetección si faltan parámetros
        if not cidr or not iface:
            di, dc = infer_default_iface_and_cidr()
            iface = iface or di
            cidr  = cidr or dc

        print(f"[bold]Interfaz:[/bold] {iface}  [bold]Red:[/bold] {cidr}")

        # Descubrimiento de dispositivos
        devices = arp_scan(cidr=cidr, iface=iface)

        # Aplicar alias amigables
        try:
            aliases = load_aliases(aliases_file)
            n_alias = apply_aliases(devices, aliases)
            if n_alias:
                print(f"[cyan]{n_alias} alias aplicados desde {aliases_file}[/cyan]")
        except Exception as e:
            print(f"[yellow]No se pudieron aplicar alias:[/yellow] {e}")

        # Comparación con baseline anterior
        old = load_baseline(baseline_file)
        added, removed = diff_baseline(old, devices)

        anomalies = []
        if added:
            anomalies.append(f"Nuevos dispositivos: {len(added)}")
        if removed:
            anomalies.append(f"Dispositivos ausentes respecto a baseline: {len(removed)}")

        summary = {
            "iface": iface,
            "cidr": cidr,
            "total_devices": len(devices),
            "added_since_baseline": [d.get("ip") for d in added],
            "removed_since_baseline": [d.get("ip") for d in removed],
        }

        out = write_reports(report_dir, "WiFi Guardian - Informe de escaneo", summary, devices, anomalies)
        print(f"[green]Informe generado:[/green] {out}")

        # Guardar baseline actual
        save_baseline(baseline_file, devices)
        print(f"[green]Baseline actualizada:[/green] {baseline_file}")

    except Exception as e:
        print(f"[red]Error:[/red] {e}")

@app.command("watch-arp")
def watch_arp(
    seconds: int = typer.Option(120, help="Duración de la escucha en segundos"),
    report_dir: Path = typer.Option(Path("reports"), help="Directorio de informes")
):
    """
    Escucha ARP durante 'seconds' y registra cambios sospechosos IP→MAC.
    Sin Npcap en Windows, se generará una nota informativa en el informe.
    """
    print(f"Escuchando ARP durante {seconds} segundos...")
    anomalies = monitor_arp_spoof(duration_sec=seconds)
    summary = {"duration_sec": seconds, "arp_anomalies": len(anomalies)}
    out = write_reports(report_dir, "WiFi Guardian - Monitor ARP", summary, [], anomalies)
    print(f"[green]Informe generado:[/green] {out}")

@app.command("deauth")
def deauth_cmd(
    iface: str = typer.Option(..., help="Interfaz en modo monitor (Linux)"),
    minutes: int = typer.Option(5, help="Minutos de captura"),
    report_dir: Path = typer.Option(Path("reports"), help="Directorio de informes")
):
    """
    Detecta tramas de desautenticación en redes Wi-Fi.
    Requiere Linux + interfaz en modo monitor (ej.: wlan0mon).
    """
    notes = detect_deauth(iface=iface, minutes=minutes)
    anomalies = [n for n in notes if "0" not in n]
    summary = {"iface": iface, "minutes": minutes, "notes": notes}
    out = write_reports(report_dir, "WiFi Guardian - Detector Deauth", summary, [], anomalies)
    print(f"[green]Informe generado:[/green] {out}")

@app.command("vendors-update")
def vendors_update():
    """
    Actualiza la base de fabricantes (OUI) usada para anotar vendor:<nombre> en los informes.
    No realiza escaneo; solo actualiza la DB local.
    """
    try:
        from .vendor import update_local_db
        ok = update_local_db()
        if ok:
            print("[green]Base OUI actualizada correctamente.[/green]")
        else:
            print("[red]No se pudo actualizar la base OUI (se usará la caché local si existe).[/red]")
    except Exception as e:
        print(f"[red]Error actualizando OUI:[/red] {e}")

if __name__ == "__main__":
    app()
