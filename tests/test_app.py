"""Pruebas de las rutas web usando el cliente de pruebas de Flask."""

import pytest

import app as modulo_app


@pytest.fixture
def cliente():
    modulo_app.app.config.update(TESTING=True)
    return modulo_app.app.test_client()


def test_ruta_principal_muestra_formulario(cliente):
    r = cliente.get("/")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Calculadora de metas de ahorro" in html
    assert modulo_app.APP_VERSION in html
    assert modulo_app.MENSAJE_PORTADA in html
    assert 'name="objetivo"' in html


def test_post_valido_muestra_resultado(cliente):
    datos = {"nombre": "Comprar un portátil", "objetivo": "2500000",
             "ahorrado": "500000", "mensual": "300000"}
    r = cliente.post("/", data=datos)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "7 meses" in html
    assert "$ 2.000.000,00" in html
    assert "20.0 %" in html


def test_post_meta_cumplida(cliente):
    r = cliente.post("/", data={"nombre": "Viaje", "objetivo": "1000", "ahorrado": "1000", "mensual": "0"})
    assert r.status_code == 200
    assert "Meta cumplida" in r.get_data(as_text=True)


def test_post_invalido_muestra_errores_y_conserva_datos(cliente):
    r = cliente.post("/", data={"nombre": "Moto", "objetivo": "5000", "ahorrado": "100", "mensual": "0"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400
    assert "Revisa los datos" in html
    assert "mayor que cero" in html
    assert 'value="Moto"' in html


def test_health(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_version(cliente):
    r = cliente.get("/version")
    assert r.status_code == 200
    assert r.get_json() == {"version": modulo_app.APP_VERSION, "revision": modulo_app.APP_REVISION}
