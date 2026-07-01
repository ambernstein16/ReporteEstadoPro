"""
Reporte Estado Pro - actualización diaria desde API Mercado Público.

Uso previsto en GitHub Actions:
1) Crear un secret de repositorio llamado MERCADO_PUBLICO_TICKET.
2) El workflow ejecuta este script de lunes a viernes.
3) El script consulta licitaciones del día, filtra rubros de mantención y obras civiles.
4) Para cada oportunidad relevante consulta el detalle por código para rescatar monto, plazos y otros campos críticos.
5) Escribe dashboard/data/oportunidades_demo.json.

Nota: esta es una primera integración MVP. Debe validarse con el ticket real y con ejemplos actuales de la API.
"""

import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

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

TIME_UNIT = {"1": "horas", "2": "días", "3": "semanas", "4": "meses", "5": "años"}
MONEDA = {"CLP": "CLP", "CLF": "UF", "USD": "USD", "UTM": "UTM", "EUR": "EUR"}
TIPO_MONTO = {"1": "Presupuesto disponible", "2": "Precio referencial"}
MODALIDAD_PAGO = {
    "1": "Pago a 30 días", "2": "Pago a 30, 60 y 90 días", "3": "Pago al día", "4": "Pago anual",
    "5": "Pago a 60 días", "6": "Pagos mensuales", "7": "Pago contra entrega conforme",
    "8": "Pago bimensual", "9": "Pago por estado de avance", "10": "Pago trimestral"
}
ESTADOS = {"5": "Publicada", "6": "Cerrada", "7": "Desierta", "8": "Adjudicada", "18": "Revocada", "19": "Suspendida"}

DEMO_ROWS = [
    {
        "id": "DEMO-OC-001",
        "titulo": "Conservación y reparación de infraestructura municipal",
        "comprador": "Municipalidad / demo comercial",
        "region": "Metropolitana",
        "subrubro": "Obras civiles",
        "estado": "Demo / revisar oportunidad similar",
        "fecha_cierre": "Por confirmar",
        "plazo_ejecucion": "90 días corridos aprox. / validar en bases",
        "fecha_adjudicacion": "Por confirmar",
        "monto_estimado": "CLP 85.000.000 aprox. / demo",
        "tipo_monto": "Presupuesto disponible / demo",
        "moneda": "CLP",
        "modalidad_pago": "Pago por estado de avance / demo",
        "tipo": "LE / LP",
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
        "estado": "Demo / oportunidad tipo",
        "fecha_cierre": "Por confirmar",
        "plazo_ejecucion": "45 a 60 días aprox. / validar en bases",
        "fecha_adjudicacion": "Por confirmar",
        "monto_estimado": "CLP 42.000.000 aprox. / demo",
        "tipo_monto": "Precio referencial / demo",
        "moneda": "CLP",
        "modalidad_pago": "Contra entrega conforme / demo",
        "tipo": "LE",
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


def today_cl_format() -> str:
    return dt.datetime.now().strftime("%d%m%Y")


def api_get(params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "ReporteEstadoPro/0.2"})
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
    if "publicada" in text or "5" == str(find_first(item, ["Estado", "CodigoEstado"])):
        score += 8
        breakdown.append({"factor": "Estado publicada", "puntos": 8, "detalle": "Está publicada o requiere revisión inmediata"})
    if any(k in text for k in ["garantía", "garantia", "visita a terreno"]):
        score -= 5
        breakdown.append({"factor": "Complejidad operativa", "puntos": -5, "detalle": "Puede exigir garantía o visita a terreno"})
    score = max(0, min(score, 100))
    return score, breakdown


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
    codigo = item.get("CodigoExterno") or item.get("Codigo") or item.get("codigo") or find_first(item, ["CodigoExterno", "Codigo", "codigo"]) or "sin-id"
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
    plazo_ejecucion = format_duration(item)

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
        "plazo_ejecucion": plazo_ejecucion,
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

    candidates = [item for item in raw_items if has_relevant_fit(item)]
    enriched = []
    for item in candidates[:40]:
        codigo = item.get("CodigoExterno") or item.get("Codigo") or item.get("codigo") or find_first(item, ["CodigoExterno", "Codigo", "codigo"])
        detail = fetch_detail(codigo)
        enriched_item = merge_dicts(item, detail)
        enriched.append(enriched_item)

    normalized = [normalize(item) for item in enriched]
    normalized = merge_demo_rows(normalized)
    normalized.sort(key=lambda x: x["score"], reverse=True)

    if not normalized:
        print(f"Sin oportunidades de mantención u obras civiles detectadas para {fecha}. Mantengo dataset existente.")
        return

    OUT.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Actualizadas {len(normalized)} oportunidades para {fecha}: {dt.datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
