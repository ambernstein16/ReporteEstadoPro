# Radar Estado Pro - MVP Demo

Dashboard estático para validar comercialmente una solución B2B de oportunidades de Mercado Público para empresas de mantención.

## Qué contiene

- `dashboard/index.html`: dashboard demo, sin backend.
- `dashboard/data/oportunidades_demo.json`: dataset inicial de oportunidades y señales.
- `dashboard/scripts/update_data.py`: esqueleto para actualizar datos con la API de Mercado Público.
- `dashboard/.github/workflows/update-data.yml`: workflow programado para actualización diaria cuando exista ticket API.

## Cómo publicarlo en GitHub Pages

1. Crear un repositorio, por ejemplo `radar-estado-pro`.
2. Subir la carpeta `dashboard` al repositorio.
3. En GitHub, ir a **Settings > Pages**.
4. Elegir publicación desde branch `main`, carpeta `/dashboard`.
5. Guardar y esperar el despliegue.

Alternativa recomendada si se usará build/automatización: configurar Pages con GitHub Actions.

## Automatización

ChileCompra informa que el acceso a la API requiere solicitar un ticket y que existe un límite diario de 10.000 solicitudes por ticket. Cuando tengas el ticket:

1. En GitHub, ir a **Settings > Secrets and variables > Actions**.
2. Crear secret `MERCADO_PUBLICO_TICKET`.
3. Ajustar `scripts/update_data.py` con los endpoints vigentes de `api.mercadopublico.cl`.
4. Ejecutar manualmente el workflow `Update Radar Estado Pro data` o esperar el cron.

## Advertencias de uso

- Esta versión es demo comercial; no debe usarse para decisiones oficiales sin revisar las bases en Mercado Público.
- GitHub Pages publica contenido en internet. No subir datos sensibles, credenciales, leads privados ni información de clientes.
- Para versión pagada se recomienda backend, login, base de datos y servidor propio.
