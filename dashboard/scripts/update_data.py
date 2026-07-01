"""
Reporte Estado Pro - actualización diaria desde API Mercado Público.

Uso previsto en GitHub Actions:
1) Crear un secret de repositorio llamado MERCADO_PUBLICO_TICKET.
2) El workflow ejecuta este script de lunes a viernes.
3) El script consulta licitaciones del día, filtra rubros de mantención y obras civiles, y escribe dashboard/data/oportunidades_demo.json.

Nota: esta es una primera integración MVP. Debe validarse con el ticket real y con ejemplos actuales de la API.
"""

import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "oportunidades_demo.json"
TICKET = os.getenv("MERCADO_PUBLICO_TICKET", "").strip()
INCLUDE_DEMO_ROWS = os.getenv("INCLUDE_DEMO_ROWS", "true").lower() == "true"

API_BASE = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

KEYWORDS = {
    "Climatización": ["climatización", "climatizacion", "aire acondicionado", "chiller", "caldera", "central térmica", "hvac"],
    "Eléctrica / luminarias": ["mantención eléctrica", "mantencion electrica", "alumbrado", "luminaria", "tablero", "redes eléctricas", "redes electricas"],
    "Mantención integral / obras menores": ["mantención integral", "mantencion integral", "mantenimiento integral", "obras menores", "reparación", "reparacion", "edificio", "sala cuna", "jardín infantil", "jardin infantil"],
    "Obras civiles": ["obras civiles", "obra civil", "conservación", "conservacion", "mejoramiento", "reposición", "reposicion", "pavimentos", "veredas", "cubierta", "techumbre", "demolición", "demolicion", "remodelación", "remodelacion", "habilitación", "habilitacion", "construcción", "construccion", "infraestructura"],
}

OBSERVATION_WORDS = [
    "garantía", "garantia", "visita a terreno", "experiencia", "certificación", "certificacion",
    "registro de proveedores", "beneficiarios finales", "boleta", "seguro", "plazo",
    "permiso municipal", "recepción municipal", "recepcion municipal", "prevención de riesgos", "prevencion de riesgos"
]

DEMO_ROWS = [
    {
        "id": "DEMO-OC-001",
        "titulo": "Conservación y reparación de infraestructura municipal",
        "comprador": "Municipalidad / demo comercial",
        "region": "Metropolitana",
        "subrubro": "Obras civiles",
        "estado": "Demo / revisar oportunidad similar",
        "fecha_cierre": "Por confirmar",
        "monto_estimado": "Por confirmar",
        "tipo": "LE / LP",
        "score": 86,
        "semaforo": "Conviene",
        "plazo_critico": "Validar visita a terreno, itemizado, cubicaciones y garantías",
        "observaciones_importantes": [
            "Puede exigir experiencia en obras civiles similares",
            "Revisar itemizado, plazo de ejecución y multas",
            "Validar permisos, recepción y prevención de riesgos"
        ],
        "accion": "Solicitar revisión técnica del itemizado y confirmar capacidad de cuadrilla antes de ofertar.",
        "fit": "Alta compatibilidad para empresas que ejecutan obras menores, conservación y reparación de infraestructura.",
        "source": "https://www.mercadopublico.cl/"
    },
    {
        "id": "DEMO-OC-002",
        "titulo": "Mejoramiento de veredas, pavimentos y accesos en recinto público",
        "comprador": "Organismo público / demo comercial",
        "region": "Valparaíso",
        "subrubro": "Obras civiles / obras menores",
        "estado": "Demo / oportunidad tipo",
        "fecha_cierre": "Por confirmar",
        "monto_estimado": "Por confirmar",
        "tipo": "LE",
        "score": 79,
        "semaforo": "Revisar",
        "plazo_critico": "Confirmar cubicaciones, especificaciones técnicas y visita a terreno",
        "observaciones_importantes": [
            "Puede requerir profesional responsable o experiencia acreditada",
            "Revisar garantías, seguros y prevención de riesgos",
            "Confirmar disponibilidad de materiales y plazo de ejecución"
        ],
        "accion": "Revisar bases y decidir si conviene según plazo, distancia y margen esperado.",
        "fit": "Buena oportunidad para empresas de obras civiles livianas y mantenimiento de infraestructura.",
        "source": "https://www.mercadopublico.cl/"
    }
]


def today_cl_format() -> str:
    """Formato usado por la API: ddmmyyyy."""
    return dt.datetime.now().strftime("%d%m%Y")


def api_get(params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "ReporteEstadoPro/0.1"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def classify_subrubro(item: dict) -> str:
    text = json.dumps(item, ensure_ascii=False).lower()
    matches = []
    for subrubro, words in KEYWORDS.items():
        if any(word in text for word in words):
            matches.append(subrubro)
    return " / ".join(matches) if matches else "Por clasificar"


def has_relevant_fit(item: dict) -> bool:
    text = json.dumps(item, ensure_ascii=False).lower()
    return any(word in text for words in KEYWORDS.values() for word in words)


def score_item(item: dict) -> int:
    text = json.dumps(item, ensure_ascii=False).lower()
    score = 50
    if any(k in text for k in KEYWORDS["Climatización"]):
        score += 18
    if any(k in text for k in KEYWORDS["Eléctrica / luminarias"]):
        score += 16
    if any(k in text for k in KEYWORDS["Mantención integral / obras menores"]):
        score += 15
    if any(k in text for k in KEYWORDS["Obras civiles"]):
        score += 17
    if "publicada" in text:
        score += 8
    if any(k in text for k in ["garantía", "garantia", "visita a terreno"]):
        score -= 5
    return max(0, min(score, 100))


def semaforo(score: int) -> str:
    if score >= 80:
        return "Conviene"
    if score >= 60:
        return "Revisar"
    return "Descartar"


def build_observations(item: dict) -> list[str]:
    text = json.dumps(item, ensure_ascii=False).lower()
    observations = []
    for word in OBSERVATION_WORDS:
        if word in text:
            observations.append(f"Revisar posible requisito asociado a: {word}")
    if not observations:
        observations = [
            "Validar requisitos técnicos en bases",
            "Validar garantías, anexos y experiencia solicitada",
            "Confirmar fecha de cierre, preguntas y visita a terreno"
        ]
    return observations[:4]


def get_nested(item: dict, *keys, default="Por confirmar"):
    value = item
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value or default


def normalize(item: dict) -> dict:
    score = score_item(item)
    codigo = item.get("CodigoExterno") or item.get("Codigo") or item.get("codigo") or "sin-id"
    titulo = item.get("Nombre") or item.get("nombre") or "Sin título"
    comprador = get_nested(item, "Comprador", "NombreOrganismo")
    estado = item.get("Estado") or item.get("estado") or "Por confirmar"
    fecha_cierre = item.get("FechaCierre") or item.get("fechaCierre") or "Por confirmar"
    tipo = item.get("Tipo") or item.get("TipoLicitacion") or "Por confirmar"

    return {
        "id": codigo,
        "titulo": titulo,
        "comprador": comprador,
        "region": "Por confirmar",
        "subrubro": classify_subrubro(item),
        "estado": estado,
        "fecha_cierre": fecha_cierre,
        "monto_estimado": "Por confirmar",
        "tipo": tipo,
        "score": score,
        "semaforo": semaforo(score),
        "plazo_critico": "Revisar fecha de cierre, preguntas, visita a terreno, garantías y antecedentes técnicos",
        "observaciones_importantes": build_observations(item),
        "accion": "Descargar bases y revisar anexos críticos antes de decidir postulación.",
        "fit": "Clasificación automática inicial para mantención y obras civiles; requiere revisión humana en piloto.",
        "source": f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"
    }


def fetch_daily_licitaciones(fecha: str) -> list[dict]:
    payload = api_get({"fecha": fecha, "ticket": TICKET})
    listado = payload.get("Listado") or payload.get("listado") or []
    if isinstance(listado, dict):
        listado = listado.get("Licitacion", []) or listado.get("licitacion", [])
    return listado if isinstance(listado, list) else []


def merge_demo_rows(rows: list[dict]) -> list[dict]:
    if not INCLUDE_DEMO_ROWS:
        return rows
    existing_ids = {row.get("id") for row in rows}
    merged = rows + [row for row in DEMO_ROWS if row["id"] not in existing_ids]
    merged.sort(key=lambda x: x.get("score", 0), reverse=True)
    return merged


def main():
    if not TICKET:
        print("Sin MERCADO_PUBLICO_TICKET. Mantengo dataset demo existente.")
        return

    fecha = today_cl_format()
    try:
        raw_items = fetch_daily_licitaciones(fecha)
    except urllib.error.HTTPError as exc:
        print(f"Error HTTP consultando API Mercado Público: {exc.code} {exc.reason}")
        return
    except Exception as exc:
        print(f"Error consultando API Mercado Público: {exc}")
        return

    filtered = [item for item in raw_items if has_relevant_fit(item)]
    normalized = [normalize(item) for item in filtered]
    normalized = merge_demo_rows(normalized)
    normalized.sort(key=lambda x: x["score"], reverse=True)

    if not normalized:
        print(f"Sin oportunidades de mantención u obras civiles detectadas para {fecha}. Mantengo dataset existente.")
        return

    OUT.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Actualizadas {len(normalized)} oportunidades para {fecha}: {dt.datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
