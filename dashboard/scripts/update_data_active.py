"""
Reporte Estado Pro - captura de oportunidades vigentes.

Este script consulta una ventana móvil de días hacia atrás, deduplica licitaciones por código,
enriquece por detalle y publica solo oportunidades vigentes en dashboard/data/oportunidades_demo.json.
"""

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "oportunidades_demo.json"
TICKET = os.getenv("MERCADO_PUBLICO_TICKET", "").strip()
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "21"))
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

TIME_UNIT = {"1": "horas", "2": "días", "3": "semanas", "4": "meses", "5": "años"}
MONEDA = {"CLP": "CLP", "CLF": "UF", "USD": "USD", "UTM": "UTM", "EUR": "EUR"}
TIPO_MONTO = {"1": "Presupuesto disponible", "2": "Precio referencial"}
MODALIDAD_PAGO = {
    "1": "Pago a 30 días", "2": "Pago a 30, 60 y 90 días", "3": "Pago al día", "4": "Pago anual",
    "5": "Pago a 60 días", "6": "Pagos mensuales", "7": "Pago contra entrega conforme",
    "8": "Pago bimensual", "9": "Pago por estado de avance", "10": "Pago trimestral"
}
ESTADOS = {"5": "Publicada", "6": "Cerrada", "7": "Desierta", "8": "Adjudicada", "18": "Revocada", "19": "Suspendida"}
CLOSED_STATE_WORDS = ["cerrada", "adjudicada", "desierta", "revocada", "suspendida", "cancelada", "anulada"]

DEMO_ROWS = [
    {
        "id": "DEMO-OC-001",
        "titulo": "Conservación y reparación de infraestructura municipal",
        "comprador": "Municipalidad / demo comercial",
        "region": "Metropolitana",
        "subrubro": "Obras civiles",
        "estado": "Demo / oportunidad tipo vigente",
        "fecha_cierre": "Por confirmar",
        "fecha_inicio_preguntas": "Por confirmar",
        "fecha_final_preguntas": "Por confirmar",
        "fecha_adjudicacion": "Por confirmar",
        "plazo_ejecucion": "90 días corridos aprox. / validar en bases",
        "monto_estimado": "CLP 85.000.000 aprox. / demo",
        "tipo_monto": "Presupuesto disponible / demo",
        "moneda": "CLP",
        "modalidad_pago": "Pago por estado de avance / demo",
        "tipo": "LE / LP",
        "contrato": "Por confirmar",
        "obras": "Sí",
        "subcontratacion": "Por confirmar",
        "toma_razon": "Por confirmar",
        "visibilidad_monto": "Sí",
        "extension_plazo": "Por confirmar",
        "fuente_financiamiento": "Por confirmar",
        "score": 86,
        "semaforo": "Conviene",
        "score_desglose": [
            {"factor": "Base", "puntos": 50, "detalle": "Puntaje inicial"},
            {"factor": "Obras civiles", "puntos": 17, "detalle": "Coincide con conservación/reparación de infraestructura"},
            {"factor": "Publicada o de interés", "puntos": 8, "detalle": "Oportunidad apta para análisis comercial"},
            {"factor": "Ajuste operativo", "puntos": 11, "detalle": "Monto y alcance relevantes para empresas medianas"}
        ],
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
        "estado": "Demo / oportunidad tipo vigente",
        "fecha_cierre": "Por confirmar",
        "fecha_inicio_preguntas": "Por confirmar",
        "fecha_final_preguntas": "Por confirmar",
        "fecha_adjudicacion": "Por confirmar",
        "plazo_ejecucion": "45 a 60 días aprox. / validar en bases",
        "monto_estimado": "CLP 42.000.000 aprox. / demo",
        "tipo_monto": "Precio referencial / demo",
        "moneda": "CLP",
        "modalidad_pago": "Contra entrega conforme / demo",
        "tipo": "LE",
        "contrato": "Por confirmar",
        "obras": "Sí",
        "subcontratacion": "Por confirmar",
        "toma_razon": "Por confirmar",
        "visibilidad_monto": "Sí",
        "extension_plazo": "Por confirmar",
        "fuente_financiamiento": "Por confirmar",
        "score": 79,
        "semaforo": "Revisar",
        "score_desglose": [
            {"factor": "Base", "puntos": 50, "detalle": "Puntaje inicial"},
            {"factor": "Obras civiles", "puntos": 17, "detalle": "Coincide con pavimentos/veredas/accesos"},
            {"factor": "Ajuste operativo", "puntos": 12, "detalle": "Requiere validar margen, distancia y plazo"}
        ],
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


def today_date() -> dt.date:
    return dt.datetime.now().date()


def date_to_api(value: dt.date) -> str:
    return value.strftime("%d%m%Y")


def iter_lookback_dates(days: int):
    base = today_date()
    for offset in range(max(days, 1)):
        yield base - dt.timedelta(days=offset)


def api_get(params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "ReporteEstadoPro/0.4"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return json.loads(response.read().decode("utf-8"))


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def find_first(obj: Any, names: list[str]) -> Any:
    targets = {norm_key(n) for n in names}
    if isinstance(obj, dict):
        for key, value in obj.items():
            if norm_key(key) in targets and value not in (None, ""):
                return value
        for value in obj.values():
            found = find_first(value, names)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first(item, names)
            if found not in (None, ""):
                return found
    return None


def first_listed(payload: Any) -> dict:
    listado = payload.get("Listado") if isinstance(payload, dict) else None
    if listado is None and isinstance(payload, dict):
        listado = payload.get("listado")
    if isinstance(listado, dict):
        listado = listado.get("Licitacion") or listado.get("licitacion") or listado.get("Items") or []
    if isinstance(listado, list) and listado:
        return listado[0] if isinstance(listado[0], dict) else {}
    return {}


def list_items(payload: Any) -> list[dict]:
    listado = payload.get("Listado") if isinstance(payload, dict) else None
    if listado is None and isinstance(payload, dict):
        listado = payload.get("listado")
    if isinstance(listado, dict):
        listado = listado.get("Licitacion") or listado.get("licitacion") or listado.get("Items") or []
    return [item for item in listado if isinstance(item, dict)] if isinstance(listado, list) else []


def parse_date(value: Any) -> dt.date | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"por confirmar", "sin información", "sin informacion"}:
        return None
    iso_match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", text)
    if iso_match:
        try:
            return dt.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            return None
    slash_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", text)
    if slash_match:
        try:
            return dt.date(int(slash_match.group(3)), int(slash_match.group(2)), int(slash_match.group(1)))
        except ValueError:
            return None
    return None


def format_number(value: Any) -> str:
    if value in (None, ""):
        return "Por confirmar"
    try:
        num = float(str(value).replace(",", "."))
        if num.is_integer():
            return f"{int(num):,}".replace(",", ".")
        return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def format_amount(item: dict) -> tuple[str, str, str]:
    amount = find_first(item, ["MontoEstimado", "Monto", "MontoDisponible", "MontoTotalEstimado", "TotalEstimado"])
    currency = find_first(item, ["Moneda", "CodigoMoneda", "UnidadMonetaria", "UnidadMoneda"])
    amount_type = find_first(item, ["TipoMontoEstimado", "TipoMonto", "Estimacion", "TipoEstimacion"])
    moneda = MONEDA.get(str(currency).upper(), str(currency or "CLP"))
    tipo = TIPO_MONTO.get(str(amount_type), str(amount_type or "Por confirmar"))
    if amount in (None, ""):
        return "Por confirmar", tipo, moneda
    return f"{moneda} {format_number(amount)}", tipo, moneda


def format_duration(item: dict) -> str:
    value = find_first(item, ["TiempoDuracionContrato", "DuracionContrato", "TiempoContrato", "PlazoEjecucion", "PlazoContrato"])
    unit = find_first(item, ["UnidadTiempoDuracionContrato", "UnidadTiempo", "UnidadDuracionContrato", "UnidadPlazo"])
    if value in (None, ""):
        return "Por confirmar"
    unit_text = TIME_UNIT.get(str(unit), str(unit or ""))
    return f"{format_number(value)} {unit_text}".strip()


def map_value(value: Any, mapping: dict[str, str]) -> str:
    if value in (None, ""):
        return "Por confirmar"
    return mapping.get(str(value), str(value))


def format_bool(value: Any) -> str:
    if value in (None, ""):
        return "Por confirmar"
    text = str(value).strip().lower()
    if text in {"1", "si", "sí", "true", "yes", "2"}:
        return "Sí"
    if text in {"0", "no", "false"}:
        return "No"
    return str(value)


def get_state(item: dict) -> str:
    estado = find_first(item, ["Estado", "CodigoEstado", "EstadoLicitacion"])
    if estado in (None, ""):
        return "Por confirmar"
    return ESTADOS.get(str(estado), str(estado))


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


def scoring_breakdown(item: dict) -> tuple[int, list[dict]]:
    text = json.dumps(item, ensure_ascii=False).lower()
    breakdown = [{"factor": "Base", "puntos": 50, "detalle": "Puntaje inicial para toda licitación detectada"}]
    score = 50
    checks = [
        ("Climatización", 18, KEYWORDS["Climatización"], "Coincide con climatización, aire acondicionado, chiller o calderas"),
        ("Eléctrica / luminarias", 16, KEYWORDS["Eléctrica / luminarias"], "Coincide con mantención eléctrica, alumbrado, luminarias o tableros"),
        ("Mantención integral / obras menores", 15, KEYWORDS["Mantención integral / obras menores"], "Coincide con mantención integral, reparación u obras menores"),
        ("Obras civiles", 17, KEYWORDS["Obras civiles"], "Coincide con obras civiles, conservación, pavimentos, techumbres o infraestructura"),
    ]
    for name, points, words, detail in checks:
        if any(k in text for k in words):
            score += points
            breakdown.append({"factor": name, "puntos": points, "detalle": detail})
    if "publicada" in text or str(find_first(item, ["Estado", "CodigoEstado"])) == "5":
        score += 8
        breakdown.append({"factor": "Estado publicada", "puntos": 8, "detalle": "Está publicada o requiere revisión inmediata"})
    if any(k in text for k in ["garantía", "garantia", "visita a terreno"]):
        score -= 5
        breakdown.append({"factor": "Complejidad operativa", "puntos": -5, "detalle": "Puede exigir garantía o visita a terreno"})
    return max(0, min(score, 100)), breakdown


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
    if format_duration(item) != "Por confirmar":
        observations.append("Existe información de duración/plazo contractual; evaluar capacidad de ejecución")
    if format_amount(item)[0] != "Por confirmar":
        observations.append("Monto disponible detectado; validar si el margen justifica postulación")
    if not observations:
        observations = [
            "Validar requisitos técnicos en bases",
            "Validar garantías, anexos y experiencia solicitada",
            "Confirmar fecha de cierre, preguntas y visita a terreno"
        ]
    return observations[:5]


def get_nested(item: dict, *keys, default="Por confirmar"):
    value = item
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value or default


def licitation_code(item: dict) -> str:
    return item.get("CodigoExterno") or item.get("Codigo") or item.get("codigo") or find_first(item, ["CodigoExterno", "Codigo", "codigo"]) or "sin-id"


def fetch_detail(codigo: str) -> dict:
    if not codigo or codigo == "sin-id":
        return {}
    try:
        payload = api_get({"codigo": codigo, "ticket": TICKET})
        return first_listed(payload)
    except Exception as exc:
        print(f"No se pudo obtener detalle para {codigo}: {exc}")
        return {}


def merge_dicts(base: dict, detail: dict) -> dict:
    merged = dict(base or {})
    for key, value in (detail or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def normalize(item: dict) -> dict:
    codigo = licitation_code(item)
    titulo = item.get("Nombre") or item.get("nombre") or find_first(item, ["Nombre", "NombreLicitacion"]) or "Sin título"
    comprador = get_nested(item, "Comprador", "NombreOrganismo")
    if comprador == "Por confirmar":
        comprador = find_first(item, ["NombreOrganismo", "Organismo", "Comprador"]) or "Por confirmar"
    fecha_cierre = find_first(item, ["FechaCierre", "fechaCierre"]) or "Por confirmar"
    fecha_adjudicacion = find_first(item, ["FechaAdjudicacion", "FechaEstimadaAdjudicacion"]) or "Por confirmar"
    fecha_inicio_preguntas = find_first(item, ["FechaInicioPreguntas"]) or "Por confirmar"
    fecha_final_preguntas = find_first(item, ["FechaFinalPreguntas", "FechaFinPreguntas"]) or "Por confirmar"
    tipo = item.get("Tipo") or item.get("TipoLicitacion") or find_first(item, ["Tipo", "TipoLicitacion"]) or "Por confirmar"
    amount, tipo_monto, moneda = format_amount(item)
    score, breakdown = scoring_breakdown(item)

    return {
        "id": codigo,
        "titulo": titulo,
        "comprador": comprador,
        "region": find_first(item, ["Region", "RegionUnidad", "NombreRegion"]) or "Por confirmar",
        "subrubro": classify_subrubro(item),
        "estado": get_state(item),
        "fecha_cierre": fecha_cierre,
        "fecha_inicio_preguntas": fecha_inicio_preguntas,
        "fecha_final_preguntas": fecha_final_preguntas,
        "fecha_adjudicacion": fecha_adjudicacion,
        "plazo_ejecucion": format_duration(item),
        "monto_estimado": amount,
        "tipo_monto": tipo_monto,
        "moneda": moneda,
        "modalidad_pago": map_value(find_first(item, ["ModalidadPago", "FormaPago", "CodigoModalidadPago"]), MODALIDAD_PAGO),
        "tipo": tipo,
        "contrato": format_bool(find_first(item, ["Contrato"])),
        "obras": format_bool(find_first(item, ["Obras"])),
        "subcontratacion": format_bool(find_first(item, ["SubContratacion", "Subcontratacion"])),
        "toma_razon": format_bool(find_first(item, ["TomaRazon"])),
        "visibilidad_monto": format_bool(find_first(item, ["VisibilidadMonto"])),
        "extension_plazo": format_bool(find_first(item, ["ExtensionPlazo"])),
        "fuente_financiamiento": find_first(item, ["FuenteFinanciamiento"]) or "Por confirmar",
        "score": score,
        "semaforo": semaforo(score),
        "score_desglose": breakdown,
        "plazo_critico": "Revisar fecha de cierre, preguntas, visita a terreno, garantías y plazo de ejecución",
        "observaciones_importantes": build_observations(item),
        "accion": "Descargar bases y revisar anexos críticos antes de decidir postulación.",
        "fit": "Clasificación automática inicial para mantención y obras civiles; requiere revisión humana en piloto.",
        "source": f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={codigo}"
    }


def is_available(row: dict) -> bool:
    estado = str(row.get("estado", "")).lower()
    if estado.startswith("demo"):
        return True
    if any(word in estado for word in CLOSED_STATE_WORDS):
        return False
    cierre = parse_date(row.get("fecha_cierre"))
    if cierre is not None and cierre < today_date():
        return False
    return True


def fetch_licitaciones_for_date(value: dt.date) -> list[dict]:
    try:
        payload = api_get({"fecha": date_to_api(value), "ticket": TICKET})
        return list_items(payload)
    except Exception as exc:
        print(f"Error consultando fecha {date_to_api(value)}: {exc}")
        return []


def fetch_lookback_licitaciones() -> list[dict]:
    by_code = {}
    for value in iter_lookback_dates(LOOKBACK_DAYS):
        for item in fetch_licitaciones_for_date(value):
            code = licitation_code(item)
            if code != "sin-id" and code not in by_code:
                by_code[code] = item
    return list(by_code.values())


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

    raw_items = fetch_lookback_licitaciones()
    candidates = [item for item in raw_items if has_relevant_fit(item)]
    enriched = []
    for item in candidates[:80]:
        codigo = licitation_code(item)
        detail = fetch_detail(codigo)
        enriched.append(merge_dicts(item, detail))

    normalized_all = [normalize(item) for item in enriched]
    available = [row for row in normalized_all if is_available(row)]
    normalized = merge_demo_rows(available)
    normalized.sort(key=lambda x: x["score"], reverse=True)

    if not normalized:
        print(f"Sin oportunidades vigentes en ventana de {LOOKBACK_DAYS} días. Mantengo dataset existente.")
        return

    OUT.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Actualizadas {len(normalized)} oportunidades vigentes. "
        f"Ventana: {LOOKBACK_DAYS} días. "
        f"Revisadas: {len(raw_items)}. Relevantes: {len(candidates)}. "
        f"Filtradas vencidas/cerradas: {len(normalized_all) - len(available)}. "
        f"Hora: {dt.datetime.now().isoformat()}"
    )


if __name__ == "__main__":
    main()
