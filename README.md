# Calculadora de metas de ahorro — CI/CD con GitHub Actions, GHCR y Render

Proyecto académico individual (Ingeniería de Sistemas · DevOps). Aplicación web pequeña y original
cuyo objetivo es demostrar un **ciclo completo de CI/CD**: cada push a `main` se prueba, se empaqueta
en una imagen Docker, se publica en GHCR, se despliega automáticamente en Render y se verifica.

- **URL pública:** https://metas-ahorro.onrender.com
- **Salud:** https://metas-ahorro.onrender.com/health
- **Versión desplegada:** https://metas-ahorro.onrender.com/version

> Alcance académico: no es una arquitectura de producción completa (sin base de datos, sin
> autenticación, una sola instancia en plan gratuito).

## Qué hace la aplicación

Ingresas el nombre de una meta, el valor objetivo, lo que ya ahorraste y cuánto puedes ahorrar al mes.
La app calcula cuánto falta, cuántos meses necesitas (redondeado hacia arriba) y el porcentaje de avance.

Reglas de validación:

| Caso | Comportamiento |
|---|---|
| Campo vacío | Error «El campo … es obligatorio» |
| Valor negativo | Error «… no puede ser negativo» |
| Formato inválido (`2.500.000`, `$2500`, `abc`, `1e6`, 3 decimales) | Error con el formato esperado |
| Objetivo = 0 | Error: debe ser mayor que cero |
| Falta dinero y ahorro mensual = 0 | Error: el ahorro mensual debe ser mayor que cero |
| Ahorrado ≥ objetivo | «¡Meta cumplida!», 0 meses, 100 % |

Formato de montos: solo dígitos, sin separadores de miles, hasta 2 decimales con punto o coma
(`2500000`, `2500000.50`). Los cálculos usan `Decimal` para evitar errores de precisión de `float`.

## Arquitectura

```
git push a main
      │
      ▼
GitHub Actions (.github/workflows/ci-cd.yml)
  test   ── ruff (revisión estática) + pytest (40 pruebas, reporte JUnit)
    │ needs
  image  ── docker build + push a GHCR  (etiquetas latest y sha-<commit>, se obtiene el digest)
    │ needs
  deploy ── Deploy Hook de Render con imgURL=ghcr.io/henryrivera01/metas-ahorro@sha256:<digest>
    │ needs
  verify ── consulta /version hasta que revision == SHA del commit (reintentos, máx. 8 min)
      │
      ▼
Render (Web Service desde imagen existente, plan Free) ──► https://metas-ahorro.onrender.com
```

Estructura:

```
app.py              rutas Flask (/, /health, /version) y textos de la demo
calculos.py         lógica de negocio pura (sin Flask)
templates/ static/  HTML y CSS
tests/              pruebas pytest de la lógica y de las rutas
Dockerfile          imagen de producción (gunicorn, usuario no root)
requirements.txt        dependencias de ejecución (van en la imagen)
requirements-dev.txt    dependencias de desarrollo y pruebas
```

## Ejecutar localmente

Requisitos: Python 3.14 y Git. Desde Git Bash, en la carpeta del proyecto:

```bash
python -m venv .venv
source .venv/Scripts/activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py                          # http://127.0.0.1:5000  (servidor de desarrollo, solo local)
```

## Ejecutar pruebas

```bash
ruff check .
pytest
```

## Docker

```bash
docker build --build-arg APP_REVISION=local-test -t metas-ahorro:local .
docker run --rm -e PORT=10000 -p 8080:10000 metas-ahorro:local
curl http://localhost:8080/health      # {"status":"ok"}
curl http://localhost:8080/version     # {"revision":"local-test","version":"Versión 1"}
```

El contenedor ejecuta **gunicorn** escuchando en `$PORT` (Render define `PORT=10000`); si no existe,
usa 8000. `EXPOSE` solo documenta el puerto, no lo configura.

## Variables y Secrets

| Nombre | Tipo | Dónde | Para qué |
|---|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | **Secret** | GitHub → Settings → Secrets and variables → Actions | Disparar el despliegue. Quien lo tenga puede desplegar: por eso es secreto. |
| `RENDER_SERVICE_URL` | Variable | GitHub → … → Actions → Variables | URL pública que comprueba `verify`. No es secreta. |
| `GITHUB_TOKEN` | Automático | Lo crea GitHub en cada ejecución | Publicar en GHCR (solo el job `image` tiene `packages: write`). |
| `APP_REVISION` | Build-arg (no secreto) | Lo pasa el workflow con el SHA del commit | Que `/version` diga qué commit está corriendo. |
| `PORT` | Variable de entorno | La define Render | Puerto en el que escucha gunicorn. |

No hay base de datos, por lo que no existen secretos de base de datos. La imagen en GHCR es pública,
así que Render la descarga sin credenciales.

## Cómo funciona el CI/CD

- **Pull Request a `main`:** solo se ejecuta `test`. Un PR (también de terceros) nunca publica ni despliega.
- **Push a `main`:** `test → image → deploy → verify`, encadenados con `needs`. Si las pruebas fallan,
  los demás jobs no se ejecutan.
- **Permisos mínimos:** `contents: read` global; `packages: write` solo en `image`.
- **Caché:** pip (`setup-python`) y capas Docker (`type=gha`).
- **Una sola imagen:** se construye una vez; se despliega esa misma imagen por su **digest**.
- **Sin desorden:** `concurrency` con `cancel-in-progress: false` en el despliegue: nunca se cancela uno
  en curso y, si llegan varios, queda en espera solo el más reciente.
- **Un solo origen de despliegue:** el servicio de Render se basa en imagen; solo lo actualiza el pipeline.

Solicitud aceptada ≠ despliegue completado ≠ app disponible:
1. `deploy` recibe HTTP 200 → Render **aceptó** y empezó el despliegue (202 = quedó en cola).
2. Render descarga la imagen, la arranca, pasa el health check `/health` y cambia el tráfico → **completado**.
3. `verify` ve el nuevo SHA en la URL pública → **nueva versión disponible**.

## Verificar un despliegue

- En GitHub: pestaña **Actions** → la ejecución → job **Verificar nueva versión en línea** (y el resumen).
- Manualmente: `curl https://metas-ahorro.onrender.com/version` y comparar `revision` con el SHA del commit
  (`git rev-parse HEAD`).
- En Render: servicio → **Events** (despliegues) y **Logs** (gunicorn y peticiones).

## Diagnosticar fallos

| Falla | Dónde mirar | Causa típica |
|---|---|---|
| `test` | Log de ruff/pytest y artefacto `reporte-pruebas` | Código o prueba rota |
| `image` | Log de *Construir y publicar* | Error en Dockerfile o dependencias |
| `deploy` HTTP 400 | Log de *Desplegar en Render* | La imagen del servicio en Render no es `ghcr.io/henryrivera01/metas-ahorro:<tag>` |
| `deploy` otro código | Log del job | Secret ausente o hook regenerado |
| `verify` agota tiempo | Render → Events y Logs | La app no arranca, health check falla, o la imagen no es pública |

## Volver a una imagen anterior (rollback)

1. **Recomendado (queda registrado en Git):** `git revert <commit>` y `git push`. El pipeline prueba,
   publica y despliega la versión revertida.
2. **Rápido, sin reconstruir:** buscar el digest de una imagen anterior en GHCR (paquete *metas-ahorro*
   o resumen de una ejecución pasada) y llamar al hook desde tu terminal, sin guardar el hook en ningún archivo:
   ```bash
   read -s HOOK   # pega el Deploy Hook (no se muestra) y Enter
   curl -X POST "$HOOK&imgURL=ghcr.io%2Fhenryrivera01%2Fmetas-ahorro%40sha256%3A<digest-anterior>"
   ```
3. Alternativa en el panel: Render → Events → **Rollback** sobre un despliegue anterior (si está disponible).

Comprobar con `/version` que la `revision` es la anterior. Nota: el siguiente push a `main` vuelve a
desplegar lo último de `main`.

## Límites del servicio (Render Free)

- Se suspende tras **15 minutos** sin tráfico; el siguiente acceso tarda **~1 minuto** en despertar.
- **750 horas de instancia** gratuitas por mes y espacio de trabajo.
- Sin disco persistente (no se usa). Una sola instancia, sin escalado.

## Eliminar los recursos al terminar

1. Render → servicio → Settings → **Delete Web Service**.
2. GitHub → paquete *metas-ahorro* → Package settings → **Delete this package**.
3. GitHub → Settings → Secrets → borrar `RENDER_DEPLOY_HOOK_URL` (opcional: archivar el repositorio).
