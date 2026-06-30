"""
Radar Estado Pro - actualización de datos demo / API Mercado Público.

Uso previsto en GitHub Actions:
1) Crear un secret de repositorio llamado MERCADO_PUBLICO_TICKET.
2) Ajustar keywords y endpoints cuando el ticket esté activo.
3) Este script debe escribir dashboard/data/oportunidades_demo.json.

Nota: los endpoints exactos pueden variar según documentación vigente de api.mercadopublico.cl.
"""
import json, os, datetime, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "oportunidades_demo.json"
TICKET = os.getenv("MERCADO_PUBLICO_TICKET", "").strip()
KEYWORDS = ["mantención climatización", "mantención eléctrica", "obras menores", "calderas", "alumbrado público"]

def score_item(item):
    text = json.dumps(item, ensure_ascii=False).lower()
    score = 50
    if any(k in text for k in ["climatización", "caldera", "aire acondicionado", "chiller"]): score += 18
    if any(k in text for k in ["eléctrica", "alumbrado", "luminaria"]): score += 16
    if any(k in text for k in ["mantención", "mantenimiento", "reparación"]): score += 15
    if any(k in text for k in ["garantía", "visita a terreno"]): score -= 6
    return max(0, min(score, 100))

def semaforo(score):
    return "Conviene" if score >= 80 else "Revisar" if score >= 60 else "Descartar"

def fetch_api_placeholder():
    # Reemplazar por endpoint vigente de api.mercadopublico.cl al activar ticket.
    # Ejemplo conceptual:
    # url = f"https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json?fecha={fecha}&ticket={TICKET}"
    # with urllib.request.urlopen(url, timeout=30) as r:
    #     return json.load(r)
    return []

def main():
    if not TICKET:
        print("Sin MERCADO_PUBLICO_TICKET. Mantengo dataset demo existente.")
        return
    raw = fetch_api_placeholder()
    normalized = []
    for item in raw:
        s = score_item(item)
        normalized.append({
            "id": item.get("CodigoExterno") or item.get("codigo") or "sin-id",
            "titulo": item.get("Nombre") or item.get("nombre") or "Sin título",
            "comprador": item.get("Comprador", {}).get("NombreOrganismo", "Por confirmar") if isinstance(item.get("Comprador"), dict) else "Por confirmar",
            "region": "Por confirmar",
            "subrubro": "Por clasificar",
            "estado": item.get("Estado", "Por confirmar"),
            "fecha_cierre": item.get("FechaCierre", "Por confirmar"),
            "monto_estimado": "Por confirmar",
            "tipo": item.get("Tipo", "Por confirmar"),
            "score": s,
            "semaforo": semaforo(s),
            "plazo_critico": "Revisar fecha de cierre, preguntas y visita a terreno",
            "riesgos": ["Validar requisitos técnicos", "Validar garantías", "Validar experiencia solicitada"],
            "accion": "Descargar bases y revisar anexos críticos.",
            "fit": "Clasificación automática inicial; requiere revisión humana en piloto.",
            "source": "https://www.mercadopublico.cl/"
        })
    OUT.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Actualizadas {len(normalized)} oportunidades: {datetime.datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
