"""Aplicación web Flask: solo rutas y presentación. La lógica está en calculos.py."""

import os

from flask import Flask, jsonify, render_template, request

from calculos import formato_moneda, procesar_formulario

# ─── Textos de demostración: cambia esto durante la sustentación ───
APP_VERSION = "Versión 1"
MENSAJE_PORTADA = "Tu próxima meta empieza hoy"
# ───────────────────────────────────────────────────────────────────

# Commit desplegado. Se incorpora a la imagen Docker en la construcción
# (ver Dockerfile). Si se ejecuta en local, vale "local".
APP_REVISION = os.environ.get("APP_REVISION", "local")

app = Flask(__name__)
app.json.ensure_ascii = False  # /version muestra "Versión" con tilde, no "Versión"
app.jinja_env.filters["moneda"] = formato_moneda


@app.route("/", methods=["GET", "POST"])
def inicio():
    resultado, errores = None, []
    datos = {}
    if request.method == "POST":
        datos = request.form
        resultado, errores = procesar_formulario(datos)
    return render_template(
        "index.html",
        version=APP_VERSION,
        mensaje=MENSAJE_PORTADA,
        revision=APP_REVISION[:7],
        datos=datos,
        resultado=resultado,
        errores=errores,
    ), (400 if errores else 200)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/version")
def version():
    return jsonify(version=APP_VERSION, revision=APP_REVISION)


if __name__ == "__main__":
    # Solo para desarrollo local. En producción se usa gunicorn (ver Dockerfile).
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
