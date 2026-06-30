# Reporte Estado Pro - MVP Demo

Dashboard estático para validar comercialmente una solución B2B de oportunidades de Mercado Público para empresas de mantención.

## Qué contiene

- `index.html`: entrada para GitHub Pages; redirige al dashboard.
- `dashboard/index.html`: dashboard demo, sin backend.
- `dashboard/data/oportunidades_demo.json`: dataset inicial de oportunidades y señales.
- `dashboard/data/config_keywords.json`: palabras clave iniciales por subrubro.
- `dashboard/scripts/update_data.py`: esqueleto para actualizar datos con la API de Mercado Público.
- `.github/workflows/update-data.yml`: workflow programado para actualización diaria cuando exista ticket API.
- `report/`: reporte demo comercial en HTML y PDF.

## Cómo publicarlo en GitHub Pages

Recomendación para este repositorio:

1. Ir a **Settings > Pages**.
2. En **Build and deployment**, elegir **Deploy from a branch**.
3. Seleccionar la rama `geriaactiva`.
4. Seleccionar carpeta `/root`.
5. Guardar.

La página de inicio (`index.html`) redirige automáticamente al dashboard demo.

## Automatización

Cuando tengas el ticket de la API de Mercado Público:

1. Ir a **Settings > Secrets and variables > Actions**.
2. Crear el secret `MERCADO_PUBLICO_TICKET`.
3. Ajustar `dashboard/scripts/update_data.py` con los endpoints vigentes de `api.mercadopublico.cl`.
4. Ejecutar manualmente el workflow `Update Radar Estado Pro data` o esperar el cron diario.

## Advertencias de uso

- Esta versión es demo comercial; no debe usarse para decisiones oficiales sin revisar las bases en Mercado Público.
- GitHub Pages publica contenido en internet. No subir datos sensibles, credenciales, leads privados ni información de clientes.
- Para una versión pagada se recomienda backend, login, base de datos y servidor propio.
