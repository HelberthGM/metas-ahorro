"""Pruebas de la lógica de negocio (sin Flask)."""

from decimal import Decimal

import pytest

from calculos import calcular_meta, convertir_monto, formato_moneda, procesar_formulario

D = Decimal


# ── Cálculo normal ──────────────────────────────────────────────
def test_calculo_normal():
    r = calcular_meta("Portátil", D("2500000"), D("500000"), D("400000"))
    assert r.falta == D("2000000")
    assert r.meses == 5
    assert r.porcentaje == D("20.0")
    assert r.cumplida is False


# ── Redondeo hacia arriba de los meses ─────────────────────────
@pytest.mark.parametrize(
    "objetivo, ahorrado, mensual, meses_esperados",
    [
        ("2500000", "500000", "300000", 7),  # 6.67 -> 7
        ("1000", "0", "999", 2),             # 1.001 -> 2
        ("1000", "0", "1000", 1),            # exacto, no sube
        ("100.50", "0", "100", 2),           # decimales
    ],
)
def test_meses_redondean_hacia_arriba(objetivo, ahorrado, mensual, meses_esperados):
    r = calcular_meta("Meta", D(objetivo), D(ahorrado), D(mensual))
    assert r.meses == meses_esperados


def test_porcentaje_no_llega_a_100_si_falta_dinero():
    r = calcular_meta("Meta", D("10000"), D("9999.99"), D("1"))
    assert r.porcentaje == D("99.9")
    assert r.cumplida is False


def test_decimal_evita_errores_de_precision():
    # Con float, 0.1 + 0.2 != 0.3. Con Decimal el resultado es exacto.
    r = calcular_meta("Meta", D("0.3"), D("0.1"), D("0.2"))
    assert r.falta == D("0.2")
    assert r.meses == 1


# ── Meta ya alcanzada ──────────────────────────────────────────
@pytest.mark.parametrize("ahorrado", ["1000", "1500"])
def test_meta_ya_alcanzada(ahorrado):
    r = calcular_meta("Viaje", D("1000"), D(ahorrado), D("0"))
    assert r.cumplida is True
    assert r.falta == 0
    assert r.meses == 0
    assert r.porcentaje == D("100")


# ── Valores negativos y cero ───────────────────────────────────
@pytest.mark.parametrize(
    "objetivo, ahorrado, mensual, mensaje",
    [
        ("-1", "0", "10", "mayor que cero"),
        ("0", "0", "10", "mayor que cero"),
        ("100", "-1", "10", "ahorrado no puede ser negativo"),
        ("100", "0", "-10", "mensual no puede ser negativo"),
    ],
)
def test_valores_invalidos_en_logica(objetivo, ahorrado, mensual, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        calcular_meta("Meta", D(objetivo), D(ahorrado), D(mensual))


def test_ahorro_mensual_cero_cuando_falta_dinero():
    with pytest.raises(ValueError, match="debe ser mayor que cero"):
        calcular_meta("Meta", D("1000"), D("200"), D("0"))


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 81])
def test_nombre_invalido(nombre):
    with pytest.raises(ValueError, match="nombre"):
        calcular_meta(nombre, D("100"), D("0"), D("10"))


# ── Conversión de entradas de texto ────────────────────────────
@pytest.mark.parametrize(
    "texto, esperado",
    [("2500000", D("2500000")), ("2500000.50", D("2500000.50")), (" 12,5 ", D("12.5")), ("0", D("0"))],
)
def test_convertir_monto_valido(texto, esperado):
    assert convertir_monto(texto, "Campo") == esperado


@pytest.mark.parametrize(
    "texto, mensaje",
    [
        ("", "obligatorio"),
        (None, "obligatorio"),
        ("-5", "negativo"),
        ("abc", "número"),
        ("2.500.000", "número"),
        ("$2500", "número"),
        ("1e6", "número"),
        ("NaN", "número"),
        ("Infinity", "número"),
        ("10.123", "número"),
    ],
)
def test_convertir_monto_invalido(texto, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        convertir_monto(texto, "Campo")


def test_procesar_formulario_acumula_errores():
    resultado, errores = procesar_formulario({"nombre": "", "objetivo": "-1", "ahorrado": "", "mensual": "x"})
    assert resultado is None
    assert len(errores) == 4


def test_procesar_formulario_valido():
    datos = {"nombre": "Bici", "objetivo": "900000", "ahorrado": "0", "mensual": "100000"}
    resultado, errores = procesar_formulario(datos)
    assert errores == []
    assert resultado.meses == 9


def test_formato_moneda():
    assert formato_moneda(D("1234567.5")) == "$ 1.234.567,50"
