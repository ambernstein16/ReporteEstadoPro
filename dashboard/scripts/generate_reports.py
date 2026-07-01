"""
Genera reportes HTML y PDF por oportunidad de interés.

Entrada:
- dashboard/data/oportunidades_demo.json

Salida:
- reports/index.html
- reports/html/<id>.html
- reports/pdf/<id>.pdf
"""

import datetime as dt
import html
import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = REPO_ROOT / "dashboard" / "data" / "oportunidades_demo.json"
REPORTS_DIR = REPO_ROOT / "reports"
HTML_DIR = REPORTS_DIR / "html"
PDF_DIR = REPORTS_DIR / "pdf"

CORE_FIELDS = [
    ("Monto estimado", "monto_estimado"),
    ("Tipo de monto", "tipo_monto"),
    ("Moneda", "moneda"),
    ("Modalidad de pago", "modalidad_pago"),
    ("Fecha cierre postulación", "fecha_cierre"),
    ("Inicio preguntas", "fecha_inicio_preguntas"),
    ("Fin preguntas", "fecha_final_preguntas"),
    ("Fecha adjudicación", "fecha_adjudicacion"),
    ("Plazo ejecución / duración contrato", "plazo_ejecucion"),
    ("Tipo", "tipo"),
    ("Región", "region"),
    ("Estado", "estado"),
]

EXTRA_FIELDS = [
    ("Contrato", "contrato"),
    ("Obras", "obras"),
    ("Permite subcontratación", "subcontratacion"),
    ("Toma de razón", "toma_razon"),
    ("Visibilidad monto", "visibilidad_monto"),
    ("Extensión de plazo", "extension_plazo"),
    ("Fuente de financiamiento", "fuente_financiamiento"),
]


def slugify(value: str) -> str:
    value = str(value or "sin-id")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return value or "sin-id"


def esc(value) -> str:
    return html.escape(str(value if value not in (None, "") else "Por confirmar"))


def plain(value) -> str:
    return str(value if value not in (None, "") else "Por confirmar")


def decision_class(semaforo: str) -> str:
    if semaforo == "Conviene":
        return "ok"
    if semaforo == "Revisar":
        return "warn"
    return "bad"


def field_boxes(item: dict, fields: list[tuple[str, str]]) -> str:
    return "".join(
        f"<div class=\"box\"><div class=\"label\">{esc(label)}</div><div class=\"value\">{esc(item.get(key))}</div></div>"
        for label, key in fields
    )


def report_html(item: dict) -> str:
    obs = item.get("observaciones_importantes") or item.get("riesgos") or []
    obs_html = "".join(f"<li>{esc(o)}</li>" for o in obs)
    breakdown = item.get("score_desglose") or []
    breakdown_html = "".join(f"<li><strong>{esc(x.get('factor'))}:</strong> {esc(x.get('puntos'))} pts · {esc(x.get('detalle'))}</li>" for x in breakdown)
    generated_at = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    sem = item.get("semaforo", "Revisar")
    cls = decision_class(sem)

    return f"""<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Reporte licitación - {esc(item.get('id'))}</title>
  <style>
    :root{{--bg:#f6f5f2;--paper:#ffffff;--text:#2f2b26;--muted:#756d64;--line:#ded8cf;--accent:#7a6a5d;--green:#3f7a53;--yellow:#9a6a20;--red:#9b3c3c}}
    body{{margin:0;background:var(--bg);font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text);line-height:1.45}}
    .page{{max-width:980px;margin:28px auto;padding:34px;background:var(--paper);border:1px solid var(--line);border-radius:18px;box-shadow:0 14px 42px rgba(48,43,38,.08)}}
    header{{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px}} h1{{font-size:28px;letter-spacing:-.03em;margin:0 0 8px}} h2{{font-size:17px;margin:26px 0 10px;color:#2d2822}} p{{margin:8px 0}} .muted{{color:var(--muted)}}
    .badge{{display:inline-flex;padding:6px 10px;border-radius:999px;font-size:13px;font-weight:800}} .ok{{background:rgba(63,122,83,.14);color:var(--green)}} .warn{{background:rgba(154,106,32,.14);color:var(--yellow)}} .bad{{background:rgba(155,60,60,.14);color:var(--red)}}
    .grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}} .box{{border:1px solid var(--line);border-radius:12px;padding:14px;background:#fbfaf8}} .label{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:800}} .value{{font-size:15px;margin-top:4px}}
    ul{{padding-left:20px}} li{{margin:6px 0}} .actions{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}} .btn{{display:inline-block;background:var(--accent);color:white;text-decoration:none;border-radius:10px;padding:10px 13px;font-weight:800}} .btn.secondary{{background:#ebe5dc;color:#3e362f}}
    .disclaimer{{font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;margin-top:26px}}
    @media print{{body{{background:white}}.page{{box-shadow:none;border:0;margin:0;border-radius:0}}.actions{{display:none}}}} @media(max-width:700px){{.page{{margin:0;border-radius:0;padding:22px}}.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body><main class=\"page\">
  <header>
    <p class=\"muted\">Reporte Estado Pro · Resumen de licitación de interés · Generado: {generated_at}</p>
    <h1>{esc(item.get('titulo'))}</h1>
    <p><strong>ID:</strong> {esc(item.get('id'))} · <strong>Comprador:</strong> {esc(item.get('comprador'))}</p>
    <p><span class=\"badge {cls}\">{esc(sem)}</span> <strong>Score:</strong> {esc(item.get('score'))}/100</p>
  </header>
  <section><h2>Resumen ejecutivo</h2><p>{esc(item.get('fit'))}</p><p><strong>Acción recomendada:</strong> {esc(item.get('accion'))}</p></section>
  <section><h2>Datos comerciales y de plazo</h2><div class=\"grid\">{field_boxes(item, CORE_FIELDS)}</div></section>
  <section><h2>Otros datos rescatados de Mercado Público</h2><div class=\"grid\">{field_boxes(item, EXTRA_FIELDS)}</div></section>
  <section><h2>Plazos críticos</h2><p>{esc(item.get('plazo_critico'))}</p></section>
  <section><h2>Observaciones importantes</h2><ul>{obs_html}</ul></section>
  <section><h2>Cómo se construyó el score</h2><ul>{breakdown_html or '<li>Sin desglose disponible para esta oportunidad.</li>'}</ul></section>
  <section><h2>Fuente oficial</h2><p><a href=\"{esc(item.get('source'))}\" target=\"_blank\" rel=\"noopener\">{esc(item.get('source'))}</a></p></section>
  <div class=\"actions\"><a class=\"btn\" href=\"{esc(item.get('source'))}\" target=\"_blank\" rel=\"noopener\">Abrir ficha oficial</a><a class=\"btn secondary\" href=\"javascript:window.print()\">Imprimir / guardar como PDF</a><a class=\"btn secondary\" href=\"../index.html\">Volver al índice</a></div>
  <p class=\"disclaimer\">Este reporte es un resumen ejecutivo para priorización comercial. No reemplaza la revisión de bases, anexos, aclaraciones, garantías ni ficha oficial de Mercado Público.</p>
</main></body></html>"""


def index_html(items: list[dict]) -> str:
    generated_at = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    rows = []
    for item in items:
        slug = slugify(item.get("id"))
        rows.append(f"""<tr><td><strong>{esc(item.get('id'))}</strong></td><td>{esc(item.get('titulo'))}<br><span>{esc(item.get('comprador'))}</span></td><td>{esc(item.get('subrubro'))}</td><td>{esc(item.get('monto_estimado'))}</td><td>{esc(item.get('score'))}</td><td>{esc(item.get('semaforo'))}</td><td><a href=\"html/{slug}.html\">HTML</a> · <a href=\"pdf/{slug}.pdf\">PDF</a></td></tr>""")
    return f"""<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Reportes - Reporte Estado Pro</title><style>body{{font-family:Inter,Segoe UI,Arial,sans-serif;background:#f6f5f2;color:#2f2b26;margin:0}}main{{max-width:1150px;margin:28px auto;background:#fff;border:1px solid #ded8cf;border-radius:18px;padding:28px;box-shadow:0 14px 42px rgba(48,43,38,.08)}}h1{{margin:0 0 6px}}p,span{{color:#756d64}}table{{width:100%;border-collapse:collapse;margin-top:18px}}th,td{{border-bottom:1px solid #ebe6de;text-align:left;padding:12px;font-size:13px;vertical-align:top}}th{{background:#f2eee8;text-transform:uppercase;font-size:12px;color:#62584e}}a{{color:#6d5f52;font-weight:800}}</style></head><body><main><h1>Reportes de licitaciones de interés</h1><p>Generado: {generated_at}</p><p><a href=\"../dashboard/\">Volver al dashboard</a></p><table><thead><tr><th>ID</th><th>Oportunidad</th><th>Subrubro</th><th>Monto</th><th>Score</th><th>Decisión</th><th>Reporte</th></tr></thead><tbody>{''.join(rows)}</tbody></table></main></body></html>"""


def make_pdf(item: dict, pdf_path: Path) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception as exc:
        print(f"PDF omitido para {item.get('id')}: reportlab no disponible ({exc})")
        return

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SmallMuted", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#756d64"), leading=11))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#2f2b26")))
    styles.add(ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=9.2, leading=12.5))

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=1.55*cm, leftMargin=1.55*cm, topMargin=1.55*cm, bottomMargin=1.4*cm)
    story = [Paragraph("Reporte Estado Pro · Resumen de licitación de interés", styles["SmallMuted"]), Spacer(1, 6), Paragraph(esc(item.get("titulo")), styles["Title"]), Paragraph(f"ID: {esc(item.get('id'))} · Comprador: {esc(item.get('comprador'))}", styles["Body"]), Paragraph(f"Semáforo: <b>{esc(item.get('semaforo'))}</b> · Score: <b>{esc(item.get('score'))}/100</b>", styles["Body"]), Spacer(1, 10)]

    table_data = [[label, plain(item.get(key))] for label, key in CORE_FIELDS + EXTRA_FIELDS]
    table = Table(table_data, colWidths=[6*cm, 10*cm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbfaf8")), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#ded8cf")), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTSIZE", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    story.append(table)
    story.append(Paragraph("Resumen ejecutivo", styles["Section"])); story.append(Paragraph(esc(item.get("fit")), styles["Body"])); story.append(Paragraph(f"<b>Acción recomendada:</b> {esc(item.get('accion'))}", styles["Body"]))
    story.append(Paragraph("Plazos críticos", styles["Section"])); story.append(Paragraph(esc(item.get("plazo_critico")), styles["Body"]))
    story.append(Paragraph("Observaciones importantes", styles["Section"])); [story.append(Paragraph(f"• {esc(obs)}", styles["Body"])) for obs in item.get("observaciones_importantes") or item.get("riesgos") or []]
    story.append(Paragraph("Cómo se construyó el score", styles["Section"])); [story.append(Paragraph(f"• {esc(x.get('factor'))}: {esc(x.get('puntos'))} pts · {esc(x.get('detalle'))}", styles["Body"])) for x in item.get("score_desglose") or []]
    story.append(Paragraph("Fuente oficial", styles["Section"])); story.append(Paragraph(esc(item.get("source")), styles["SmallMuted"])); story.append(Spacer(1, 10)); story.append(Paragraph("Este reporte es un resumen ejecutivo para priorización comercial. No reemplaza la revisión de bases, anexos, aclaraciones, garantías ni ficha oficial de Mercado Público.", styles["SmallMuted"]))
    doc.build(story)


def main() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True); PDF_DIR.mkdir(parents=True, exist_ok=True); REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    items = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    for old in HTML_DIR.glob("*.html"): old.unlink()
    for old in PDF_DIR.glob("*.pdf"): old.unlink()
    for item in items:
        slug = slugify(item.get("id")); (HTML_DIR / f"{slug}.html").write_text(report_html(item), encoding="utf-8"); make_pdf(item, PDF_DIR / f"{slug}.pdf")
    (REPORTS_DIR / "index.html").write_text(index_html(items), encoding="utf-8")
    print(f"Generados reportes para {len(items)} oportunidades en {REPORTS_DIR}")


if __name__ == "__main__":
    main()
