# Sustentación — Calculadora de metas de ahorro

## Antes de empezar (5 minutos antes)

- [ ] Abrir https://metas-ahorro.onrender.com para **despertar** el servicio (plan Free).
- [ ] Pestañas listas: app, `/version`, GitHub **Actions**, paquete en GHCR, Render (**Events** y **Logs**).
- [ ] VS Code abierto en `app.py`; Git Bash en la carpeta del proyecto con `git status` limpio.
- [ ] Tamaño de letra grande en VS Code, terminal y navegador.

## Guion de 10 minutos

| Tiempo | Qué muestro | Qué digo |
|---|---|---|
| 0:00–1:00 | App en el navegador; hago un cálculo; `/version` | «Es una app personal original: calcula metas de ahorro. Está en Render. `/version` dice qué commit está corriendo: ahora `f629ef3…`/el último». |
| 1:00–2:00 | En VS Code, `app.py`: cambio `MENSAJE_PORTADA` a «Tu próxima meta ya tiene un plan» y `APP_VERSION` a «Versión 2» | «Hago un cambio visible. No toco nada en Render: todo lo hará el pipeline». |
| 2:00–2:30 | Git Bash: `git add app.py` · `git commit -m "Demo: versión 2"` · `git push` · `git rev-parse --short HEAD` | «Este es el SHA que debería aparecer en producción al final». |
| 2:30–3:00 | Actions: la ejecución arrancó sola | «El push disparó el workflow automáticamente». |
| 3:00–5:30 | **Mientras corre**: abro `.github/workflows/ci-cd.yml` y explico los 4 jobs y `needs`; luego el job `test` (ruff + 40 pruebas, resumen) | «En Python no hay compilación a JAR: el equivalente es la revisión estática, las pruebas y la construcción real de la imagen. Si una prueba falla, `needs` impide publicar y desplegar». |
| 5:30–6:30 | Job `image`: resumen con etiquetas y **digest**; paquete en GHCR | «La imagen se construye una sola vez. `latest` y `sha-…` son etiquetas que pueden moverse; el digest identifica exactamente ese contenido». |
| 6:30–7:30 | Job `deploy` (HTTP 200) y Render → **Events** | «El pipeline llama al deploy hook con la imagen por digest. HTTP 200 solo significa *solicitud aceptada*». |
| 7:30–8:30 | Job `verify`: los intentos y «✅ Nueva versión disponible» | «Verify no se conforma con un 200: exige que `/version` devuelva el SHA de este commit. Si respondiera la versión anterior, seguiría esperando y fallaría tras 8 minutos». |
| 8:30–9:30 | Recargo la app: aparece el nuevo texto y «Versión 2»; `/version` con el nuevo SHA; Render → **Logs** | «El cambio está en producción sin pulsar Deploy. En los logs se ve gunicorn y las peticiones». |
| 9:30–10:00 | Cierre | «Push → pruebas → imagen → GHCR → Render → verificación, en menos de 2 minutos». |

El pipeline tarda ~1 min 45 s; si termina antes de que acabe la explicación, simplemente se muestra ya en verde.

**Plan B (si algo falla en vivo):** mostrar el error en el log y explicar qué job lo detuvo y por qué no se desplegó;
eso también demuestra el valor del pipeline. No reemplazar la demo por capturas de ejecuciones anteriores.

## Preguntas y respuestas cortas

**CI vs CD.** CI (integración continua): cada cambio se integra y se valida automáticamente (lint + pruebas).
CD (despliegue continuo): si pasa, se empaqueta y se despliega automáticamente sin intervención manual.

**Imagen vs contenedor.** La imagen es la plantilla inmutable (SO base + Python + dependencias + código).
El contenedor es una instancia en ejecución de esa imagen.

**Artefacto.** El producto que genera el pipeline y se despliega: aquí, la imagen Docker publicada en GHCR.
(El reporte JUnit también se guarda como artefacto de la ejecución.)

**`needs`.** Define dependencias entre jobs: `image` espera a `test`, `deploy` a `image`, `verify` a `deploy`.
Si un job falla, los que dependen de él no se ejecutan.

**Caché.** Reutiliza trabajo previo: paquetes pip (`setup-python` con `cache: pip`) y capas Docker (`type=gha`).
En el Dockerfile se copian primero los requirements para que la capa de dependencias se reutilice.

**Variables vs Secrets.** Las variables son configuración pública (`RENDER_SERVICE_URL`). Los Secrets son
credenciales (`RENDER_DEPLOY_HOOK_URL`): cifrados, enmascarados en logs y nunca en el código.

**GHCR.** GitHub Container Registry, el registro de imágenes de GitHub. Se autentica con el `GITHUB_TOKEN`
automático; solo el job `image` tiene permiso `packages: write`.

**Etiqueta vs digest.** La etiqueta (`latest`, `sha-…`) es un nombre que puede moverse a otra imagen.
El digest (`sha256:…`) es el hash del contenido: identifica una imagen exacta e inmutable. Despliego por digest.
No confundir con el SHA del commit, que identifica el código en Git.

**¿Qué impide desplegar código con pruebas fallidas?** La cadena `needs`: si `test` falla, `image` no corre,
por lo que no hay imagen nueva ni despliegue. No se usa `continue-on-error`. Además, los PR nunca despliegan.

**¿Cómo sé qué versión está funcionando?** `GET /version` devuelve `revision` = SHA del commit, grabado en la imagen
al construirla (build-arg `APP_REVISION`). El job `verify` lo comprueba automáticamente.

**Rollback.** `git revert` + push (pasa por todo el pipeline), o llamar al deploy hook con el digest de una imagen
anterior de GHCR (sin reconstruir), o Rollback en Render. Se confirma con `/version`.

**¿Por qué no se usa el servidor de Flask en producción?** Es solo para desarrollo; gunicorn es un servidor WSGI
de producción con varios procesos (workers).

**¿Por qué usuario no root?** Si alguien comprometiera la app, tendría menos privilegios dentro del contenedor.

**¿Qué pasa si hay dos pushes seguidos?** El despliegue usa `concurrency` sin cancelar el que está en curso;
el siguiente espera, y si llegan varios solo queda el más reciente, así no se despliega fuera de orden.

## Checklist de entrega

- [ ] Confirmado con la profesora: presentación individual y uso de Python.
- [ ] Repositorio: https://github.com/HenryRivera01/metas-ahorro (público, con README).
- [ ] Workflow: `.github/workflows/ci-cd.yml` con `test → image → deploy → verify`.
- [ ] Ejecución exitosa completa en Actions (captura de los 4 jobs en verde).
- [ ] Imagen publicada en GHCR: `ghcr.io/henryrivera01/metas-ahorro` (captura con etiquetas y digest).
- [ ] URL pública funcionando: https://metas-ahorro.onrender.com y `/version` (captura).
- [ ] Evidencias: log de `verify` con «✅ Nueva versión disponible», Render → Events y Logs.
- [ ] Ensayo cronometrado realizado.
