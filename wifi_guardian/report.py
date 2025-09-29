from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import json
import datetime
import html


# =============== helpers ===============

def _fmt_dt(ts: datetime.datetime | None = None) -> str:
    ts = ts or datetime.datetime.now()
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def _escape(s: str) -> str:
    return html.escape(s or "")

def _fmt_dt(ts: datetime.datetime | None = None) -> str:
    ts = ts or datetime.datetime.now()
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def _chip(text: str, kind: str = "info") -> str:
    colors = {
        "info":   ("#0e1b17", "#00ff9c"),
        "alias":  ("#10122b", "#9aa0ff"),
        "vendor": ("#122018", "#2affc8"),
        "warn":   ("#281325", "#ff2bd6"),
        "muted":  ("#1a1f24", "#8b9aa0"),
    }
    bg, fg = colors.get(kind, colors["info"])
    return f'<span class="chip" style="background:{bg};color:{fg}">{_escape(text)}</span>'

def _icon(name: str) -> str:
    # inline SVGs (stroke inherits currentColor)
    icons = {
        "added":   '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        "removed": '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        "device":  '<svg viewBox="0 0 24 24" width="16" height="16"><rect x="3" y="4" width="18" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 20h8" stroke="currentColor" stroke-width="2" /></svg>',
        "copy":    '<svg viewBox="0 0 24 24" width="14" height="14"><rect x="9" y="9" width="13" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><rect x="2" y="2" width="13" height="13" rx="2" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
        "wifi":    '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M2 8a20 20 0 0 1 20 0M5 12a14 14 0 0 1 14 0M8 16a8 8 0 0 1 8 0M12 20h0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
        "shield":  '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 3l8 4v5c0 5-3.5 8.5-8 9-4.5-.5-8-4-8-9V7l8-4z" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
    }
    return icons.get(name, "")

# ======== Autor / Branding ========

ts_now = _fmt_dt()
AUTHOR_NAME   = "Enrique Forte"
AUTHOR_GITHUB = "https://github.com/EnriqueForte" 
AUTHOR_LINKED = "https://www.linkedin.com/in/enriqueforte"

# =============== main writer ===============

def write_reports(
    report_dir: Path,
    title: str,
    summary: Dict[str, Any],
    devices: List[Dict[str, Any]],
    anomalies: List[str]
) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now()
    stamp = ts.strftime("%Y%m%d-%H%M%S")
    out_html = report_dir / f"report-{stamp}.html"

    # counts
    total = len(devices)
    added = len(summary.get("added_since_baseline") or [])
    removed = len(summary.get("removed_since_baseline") or [])

    # build device rows
    rows = []
    for d in devices:
        ip   = _escape(d.get("ip",""))
        mac  = _escape(d.get("mac",""))
        host = _escape(d.get("hostname",""))
        alias = _escape(d.get("alias",""))
        note = d.get("note","") or ""

        chips = []
        # vendor chip (si viene anotado en note como "vendor:XYZ")
        vendor = ""
        for part in note.split(","):
            part = part.strip()
            if part.lower().startswith("vendor:"):
                vendor = part.split(":",1)[1].strip()
            if part.lower().startswith("alias"):
                chips.append(_chip("alias", "alias"))
            if part.lower().startswith("mac:private"):
                chips.append(_chip("MAC privada", "muted"))
        if vendor:
            chips.append(_chip(vendor, "vendor"))

        note_txt = _escape(note)

        rows.append(f"""
        <tr>
          <td class="ip">
            <span class="mono">{ip}</span>
            <button class="copy" data-copy="{ip}" title="Copiar IP">{_icon('copy')}</button>
          </td>
          <td class="mac">
            <span class="mono">{mac}</span>
            <button class="copy" data-copy="{mac}" title="Copiar MAC">{_icon('copy')}</button>
          </td>
          <td class="host">{host}</td>
          <td class="alias">{alias}</td>
          <td class="note">{note_txt} {' '.join(chips)}</td>
        </tr>
        """)

    # anomalies list
    anomalies_html = ""
    if anomalies:
        items = "".join(f"<li>{_escape(a)}</li>" for a in anomalies)
        anomalies_html = f"""
        <div class="panel warn">
          <div class="panel-title">{_icon('shield')} Anomalías</div>
          <ul class="anom-list">{items}</ul>
        </div>
        """

    # summary JSON pretty
    summary_json = _escape(json.dumps(summary, indent=2, ensure_ascii=False))

    html_text = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{_escape(title)}</title>
<style>
  :root {{
    --bg:#0b0f10;
    --panel:#0e1417;
    --panel-2:#10161a;
    --grid:#0f171b;
    --text:#d6f5ea;
    --muted:#9ec7b8;
    --neon:#00ff9c;
    --magenta:#ff2bd6;
    --cyan:#2affc8;
    --card-shadow: 0 0 0 1px rgba(0,255,156,0.10), 0 6px 24px rgba(0,0,0,0.4);
  }}
  * {{ box-sizing:border-box }}
  html,body {{ margin:0; background:var(--bg); color:var(--text); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial; }}
  code, .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
  a {{ color: var(--neon); text-decoration:none }}
  .wrap {{ max-width: 1100px; margin: 24px auto; padding: 0 16px; }}

  header {{
    display:flex; align-items:center; gap:14px; margin-bottom:18px;
  }}
  .logo {{ display:inline-flex; align-items:center; gap:10px; color:var(--neon); }}
  .logo .badge {{ font-weight:700; letter-spacing:1px; }}
  .title {{ font-size:26px; font-weight:800; }}
  .subtitle {{ color:var(--muted); font-size:14px; }}

  .grid {{
    display:grid; gap:14px; grid-template-columns: repeat(12, 1fr);
  }}
  .col-4 {{ grid-column: span 4; }}
  .col-8 {{ grid-column: span 8; }}
  .card {{
    background: radial-gradient(1200px 350px at -10% -10%, rgba(0,255,156,0.06), transparent 60%), var(--panel);
    border-radius: 14px; padding: 16px; box-shadow: var(--card-shadow);
  }}
  .kpi {{ display:flex; align-items:center; gap:10px; }}
  .kpi .num {{ font-size:28px; font-weight:800; color:var(--neon); }}
  .kpi .lbl {{ font-size:12px; color:var(--muted); }}
  .split {{ display:flex; justify-content:space-between; align-items:center; }}

  .search {{
    display:flex; gap:10px; align-items:center; margin: 6px 0 10px;
  }}
  .search input {{
    width: 100%; padding: 10px 12px; border-radius: 10px; background: var(--panel-2); color: var(--text); border: 1px solid #142025;
    outline: none;
  }}

  table {{
    width:100%; border-collapse:separate; border-spacing:0 6px;
  }}
  thead th {{
    position: sticky; top: 0; z-index: 1;
    background: linear-gradient(0deg, rgba(0,255,156,0.04), rgba(0,255,156,0.06));
    color: var(--text); text-align: left; padding: 10px 12px; font-size: 12px; letter-spacing: 0.5px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    cursor: pointer;
  }}
  tbody tr {{
    background: var(--grid); box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 -1px 0 rgba(255,255,255,0.03) inset;
  }}
  tbody td {{ padding: 10px 12px; vertical-align: middle; font-size: 14px; }}
  tbody td .copy {{
    margin-left: 8px; background: transparent; border: 0; color: var(--muted); cursor: pointer;
  }}
  tbody tr:hover {{ outline: 1px solid rgba(0,255,156,0.18); }}
  .chip {{
    display:inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; margin-left: 6px; border: 1px solid rgba(255,255,255,0.06);
  }}
  .panel.warn {{ background: linear-gradient(180deg, rgba(255,43,214,0.07), rgba(0,0,0,0)); border:1px solid rgba(255,43,214,0.25); }}
  .panel-title {{ font-weight:700; color:#ffd5f4; margin-bottom:6px; display:flex; align-items:center; gap:8px; }}

  pre.json {{ background: #0a1113; border: 1px solid #112025; padding: 12px; border-radius: 12px; overflow: auto; max-height: 300px; }}

  @media (max-width: 900px) {{
    .col-4 {{ grid-column: span 12; }}
    .col-8 {{ grid-column: span 12; }}
    thead th:nth-child(3), tbody td:nth-child(3) {{ display:none; }} /* oculta Hostname en pantallas pequeñas */
  }}
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <div class="logo">{_icon('wifi')}{_icon('shield')} <span class="badge">WIFI GUARDIAN</span></div>
      <div>
        <div class="title">{_escape(title)}</div>
        <div class="subtitle">Fecha: {_fmt_dt(ts)} · Interfaz: {_escape(str(summary.get('iface','')))} · Red: {_escape(str(summary.get('cidr','')))}</div>
      </div>
    </header>

    <section class="grid" style="margin-bottom:12px">
      <div class="card col-4">
        <div class="kpi">{_icon('device')} <div><div class="num">{total}</div><div class="lbl">Dispositivos</div></div></div>
      </div>
      <div class="card col-4">
        <div class="kpi" style="color:#9dffc9">{_icon('added')} <div><div class="num">{added}</div><div class="lbl">Nuevos vs baseline</div></div></div>
      </div>
      <div class="card col-4">
        <div class="kpi" style="color:#ffd0f3">{_icon('removed')} <div><div class="num">{removed}</div><div class="lbl">Ausentes vs baseline</div></div></div>
      </div>
    </section>

    {anomalies_html}

    <section class="card">
      <div class="split">
        <h3 style="margin:0">Inventario</h3>
        <div class="search">
          <input id="q" type="search" placeholder="Filtrar por IP, MAC, hostname, alias, vendor..." />
        </div>
      </div>
      <div style="overflow:auto; max-height: 60vh; margin-top:6px;">
        <table id="devtbl">
          <thead>
            <tr>
              <th data-k="ip">IP</th>
              <th data-k="mac">MAC</th>
              <th data-k="host">Hostname</th>
              <th data-k="alias">Alias</th>
              <th data-k="note">Notas</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="card" style="margin-top:12px">
      <div class="panel-title">Resumen técnico (JSON)</div>
      <pre class="json"><code>{summary_json}</code></pre>
    </section>

    <footer style="opacity:.9; font-size:12px; margin:18px 4px;">
      <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; justify-content:space-between;">
        <div>
          Hecho con ❤️ por <strong>{AUTHOR_NAME}</strong> · <span class="mono">{_escape(ts_now)}</span>
        </div>
        <div style="display:flex; gap:12px; align-items:center;">
          <a href="{AUTHOR_LINKED}" target="_blank" rel="noopener" title="LinkedIn" style="display:inline-flex; align-items:center; gap:6px; color:var(--neon);">
            <svg viewBox="0 0 24 24" width="16" height="16"><path d="M4 4h4v16H4zM9 10h4v10H9zM14 10h4v10h-4z" fill="currentColor"/></svg>
            LinkedIn
          </a>
          <a href="{AUTHOR_GITHUB}" target="_blank" rel="noopener" title="GitHub" style="display:inline-flex; align-items:center; gap:6px; color:var(--neon);">
            <svg viewBox="0 0 24 24" width="16" height="16"><path d="M12 .5a12 12 0 00-3.79 23.39c.6.11.82-.26.82-.58v-2.18c-3.34.73-4.05-1.61-4.05-1.61-.55-1.41-1.35-1.79-1.35-1.79-1.1-.76.09-.74.09-.74 1.22.09 1.86 1.26 1.86 1.26 1.08 1.85 2.84 1.31 3.53 1 .11-.79.42-1.31.77-1.61-2.66-.3-5.46-1.33-5.46-5.91 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.17 0 0 1.01-.32 3.3 1.23a11.46 11.46 0 016 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.65.25 2.87.12 3.17.77.84 1.24 1.91 1.24 3.22 0 4.59-2.81 5.61-5.49 5.91.43.37.82 1.1.82 2.22v3.29c0 .32.21.7.83.58A12 12 0 0012 .5z" fill="currentColor"/></svg>
            GitHub
          </a>
        </div>
      </div>
    </footer>

  </div>

<script>
  // filtro rápido
  const q = document.getElementById('q');
  const tbody = document.querySelector('#devtbl tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));

  function norm(s) {{ return (s||'').toLowerCase(); }}

  q.addEventListener('input', () => {{
    const term = norm(q.value);
    rows.forEach(tr => {{
      const txt = norm(tr.innerText);
      tr.style.display = txt.includes(term) ? '' : 'none';
    }});
  }});

  // sort básico por columna
  let sortDir = 1, lastKey = null;
  document.querySelectorAll('#devtbl thead th').forEach(th => {{
    th.addEventListener('click', () => {{
      const k = th.getAttribute('data-k');
      if (!k) return;
      if (k === lastKey) sortDir *= -1; else sortDir = 1;
      lastKey = k;

      const getVal = (tr) => {{
        if (k === 'ip')   return tr.querySelector('td.ip .mono')?.textContent.trim() || '';
        if (k === 'mac')  return tr.querySelector('td.mac .mono')?.textContent.trim() || '';
        if (k === 'host') return tr.querySelector('td.host')?.textContent.trim() || '';
        if (k === 'alias')return tr.querySelector('td.alias')?.textContent.trim() || '';
        return tr.querySelector('td.note')?.textContent.trim() || '';
      }};
      rows.sort((a,b) => {{
        const va = getVal(a).toLowerCase();
        const vb = getVal(b).toLowerCase();
        if (va < vb) return -1 * sortDir;
        if (va > vb) return  1 * sortDir;
        return 0;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});

  // copiar al portapapeles
  document.querySelectorAll('button.copy').forEach(btn => {{
    btn.addEventListener('click', async () => {{
      const txt = btn.getAttribute('data-copy');
      try {{
        await navigator.clipboard.writeText(txt);
        btn.style.color = '#00ff9c';
        setTimeout(() => btn.style.color = '', 700);
      }} catch(e) {{ console.log('copy fail', e); }}
    }});
  }});
</script>
</body>
</html>
"""
    out_html.write_text(html_text, encoding="utf-8")
    return out_html
