# Imagen base oficial y ligera de Python (misma versión que en local)
FROM python:3.14-slim

# Sin archivos .pyc y con logs sin búfer (se ven al instante en Render)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Primero solo las dependencias: esta capa se reutiliza (caché)
#    mientras requirements.txt no cambie.
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Después el código de la aplicación (solo lo necesario para ejecutar)
COPY app.py calculos.py ./
COPY templates/ templates/
COPY static/ static/

# Usuario sin privilegios: el proceso no corre como root
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Commit con el que se construyó la imagen. NO es un secreto: lo pasa
# GitHub Actions con --build-arg y lo devuelve la ruta /version.
# Va al final para no invalidar la caché de las capas anteriores.
ARG APP_REVISION=desconocida
ENV APP_REVISION=${APP_REVISION}

# Solo documenta el puerto por defecto; NO lo configura.
EXPOSE 8000

# gunicorn (servidor WSGI de producción) escucha en $PORT si la plataforma
# lo define (Render lo hace) o en 8000 si no. Se usa forma shell para que
# ${PORT} se expanda, y exec para que gunicorn reciba las señales de parada.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile - app:app"]
