"""
Genera un informe simple de calidad de datos para revisar si el MVP está listo para demo comercial.

Entrada:
- dashboard/data/oportunidades_demo.json

Salida:
- reports/data_quality.html
"""

import datetime as dt
import html
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = REPO_ROOT / "dashboard" / "data" / "oportunidades_demo.json"
REPORTS_DIR = REPO_ROOT / "reports"
OUT = REPORTS_DIR / "data_quality.html"

REQUIRED_FIELDS = [
    ("ID", "id"),
    ("Título", "titulo"),
    ("Comprador", "comprador"),
    ("Subrubro", "subrubro"),
    ("Estado", "estado"),
    ("Fecha cierre", "fecha_cierre"),
    ("Monto", "monto_estimado"),
    ("Plazo ejecución", "plazo_ejecucion"),
    ("Modalidad pago", "modalidad_pago"),
    ("Fuente", "source"),
    ("Score", "score"),
    ("Semáforo", "semaforo"),
]

CLOSED_WORDS = ["cerrada", "adjudicada", "desierta", "revocada", "suspendida", "cancelada", "anulada"]


def esc(value):
    return html.escape(str(value if value is not None else ""))


def is_known(value) -> bool:
    if value in (None, ""):
        return False
    return "por confirmar" not in str(value).strip().lower()


def parse_date(value):
    if not is_known(value):
        return None
    text = str(value)
    iso = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text)
    if iso:
        try:
            return dt.date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return None
    dmy = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", text)
    if dmy:
        try:
            return dt.date(int(dmy.group(3)), int(dmy.group(2)), int(dmy.group(1)))
        except ValueError:
            return None
    return None


def row_status(item):
    issues = []
    warnings = []
    for label, key in REQUIRED_FIELDS:
        if not is_known(item.get(key)):
            warnings.append(f"Falta o no confirmado: {label}")
    estado = str(item.get("estado", "")).lower()
    if any(word in estado for word in CLOSED_WORDS):
        issues.append("Estado no vigente")
    cierre = parse_date(item.get("fecha_cierre"))
    if cierre and cierre < dt.date.today():
        issues.append("Fecha de cierre vencida")
    source = str(item.get("source", ""))
    if source and "mercadopublico.cl" not in source:
        warnings.append("Fuente no apunta a ficha Mercado Público")
    return issues, warnings


def pct(num, den):
    return round((num / den) * 100) if den else 0


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    items = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else []
    total = len(items)
    with_monto = sum(1 for i in items if is_known(i.get("monto_estimado")))
    with_cierre = sum(1 for i in items if is_known(i.get("fecha_cierre")))
    with_plazo = sum(1 for i in items if is_known(i.get("plazo_ejecucion")))
    with_source = sum(1 for i in items if "mercadopublico.cl" in str(i.get("source", "")))
    conviene = sum(1 for i in items if i.get("semaforo") == "Conviene")

    rows = []
    issue_count = 0
    warning_count = 0
    for item in items:
        issues, warnings = row_status(item)
        issue_count += len(issues)
        warning_count += len(warnings)
        status = "OK" if not issues else "Revisar"
        rows.append(f"""
        <tr>
          <td><strong>{esc(item.get('id'))}</strong></td>
          <td>{esc(item.get('titulo'))}<br><span>{esc(item.get('comprador'))}</span></td>
          <td>{esc(item.get('subrubro'))}</td>
          <td>{esc(item.get('monto_estimado'))}</td>
          <td>{esc(item.get('fecha_cierre'))}</td>
          <td>{esc(status)}</td>
          <td>{esc('; '.join(issues + warnings) or 'Sin observaciones')}</td>
        </tr>""")

    generated_at = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    html_out = f"""<!doctype html>
<html lang=\"es\">
<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Calidad de datos - Reporte Estado Pro</title>
<style>body{{font-family:Inter,Segoe UI,Arial,sans-serif;background:#f6f5f2;color:#2f2b26;margin:0}}main{{max-width:1180px;margin:28px auto;background:#fff;border:1px solid #ded8cf;border-radius:18px;padding:28px;box-shadow:0 14px 42px rgba(48,43,38,.08)}}h1{{margin:0 0 6px}}p,span{{color:#756d64}}.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}}.kpi{{border:1px solid #ded8cf;border-radius:14px;padding:14px;background:#fbfaf8}}.num{{font-size:26px;font-weight:900}}table{{width:100%;border-collapse:collapse;margin-top:18px}}th,td{{border-bottom:1px solid #ebe6de;text-align:left;padding:12px;font-size:13px;vertical-align:top}}th{{background:#f2eee8;text-transform:uppercase;font-size:12px;color:#62584e}}a{{color:#6d5f52;font-weight:800}}@media(max-width:900px){{.kpis{{grid-template-columns:1fr 1fr}}}}</style></head>
<body><main>
<h1>Informe de calidad de datos</h1>
<p>Generado: {generated_at}</p>
<p><a href=\"../dashboard/\">Volver al dashboard</a></p>
<div class=\"kpis\">
  <div class=\"kpi\"><div class=\"num\">{total}</div><p>Oportunidades</p></div>
  <div class=\"kpi\"><div class=\"num\">{pct(with_monto,total)}%</div><p>Con monto</p></div>
  <div class=\"kpi\"><div class=\"num\">{pct(with_cierre,total)}%</div><p>Con cierre</p></div>
  <div class=\"kpi\"><div class=\"num\">{pct(with_plazo,total)}%</div><p>Con plazo ejecución</p></div>
  <div class=\"kpi\"><div class=\"num\">{conviene}</div><p>Conviene</p></div>
</div>
<p><strong>Observaciones totales:</strong> {warning_count} advertencias y {issue_count} problemas críticos. El objetivo comercial es tener pocas oportunidades, pero bien explicadas.</p>
<table><thead><tr><th>ID</th><th>Oportunidad</th><th>Subrubro</th><th>Monto</th><th>Cierre</th><th>Estado QA</th><th>Observaciones</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
</main></body></html>"""
    OUT.write_text(html_out, encoding="utf-8")
    print(f"Informe de calidad generado: {OUT}. Total: {total}, con monto: {with_monto}, con cierre: {with_cierre}, con plazo: {with_plazo}, fuente oficial: {with_source}")


if __name__ == "__main__":
    main()
