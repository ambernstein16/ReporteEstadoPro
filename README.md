# Reporte Estado Pro - MVP Demo

Dashboard estático para validar comercialmente una solución B2B de oportunidades de Mercado Público para empresas de mantención y obras civiles.

## Qué contiene

- `index.html`: entrada para GitHub Pages; redirige al dashboard.
- `dashboard/index.html`: dashboard demo, sin backend.
- `dashboard/data/oportunidades_demo.json`: oportunidades vigentes normalizadas que alimentan el dashboard.
- `dashboard/data/config_keywords.json`: palabras clave iniciales por subrubro.
- `dashboard/scripts/update_data_active.py`: capturador automático con ventana móvil; consulta API, deduplica por código, filtra vigentes y enriquece con detalle.
- `dashboard/scripts/update_data.py`: versión anterior de respaldo.
- `dashboard/scripts/generate_reports.py`: genera reportes HTML y PDF por oportunidad.
- `.github/workflows/update-data.yml`: workflow programado para actualización diaria.
- `reports/`: reportes HTML/PDF generados por licitación de interés.
- `report/`: reporte demo comercial original.

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
3. Ejecutar manualmente el workflow `Update Radar Estado Pro data` o esperar el cron diario.

El workflow actual usa `dashboard/scripts/update_data_active.py` y busca licitaciones publicadas en una ventana móvil de días hacia atrás, por defecto 21 días. Luego:

1. Deduplica por código de licitación.
2. Filtra por rubros relevantes: mantención, climatización, electricidad, obras menores y obras civiles.
3. Consulta detalle por código cuando es posible.
4. Excluye licitaciones vencidas, cerradas, adjudicadas, desiertas, revocadas o suspendidas.
5. Genera el JSON del dashboard.
6. Genera reportes HTML/PDF por oportunidad vigente.

Al ejecutar manualmente el workflow puedes cambiar el parámetro `lookback_days`, por ejemplo 14, 21 o 30 días.

## Advertencias de uso

- Esta versión es demo comercial; no debe usarse para decisiones oficiales sin revisar las bases en Mercado Público.
- GitHub Pages publica contenido en internet. No subir datos sensibles, credenciales, leads privados ni información de clientes.
- Para una versión pagada se recomienda backend, login, base de datos y servidor propio.
