"""Lógica de negocio de la calculadora de metas de ahorro.

Este módulo NO depende de Flask: solo recibe valores y devuelve resultados,
por eso se puede probar directamente con pytest.

Formato de entrada aceptado para montos:
  - Solo dígitos, sin separadores de miles ni símbolo de moneda.
  - Opcionalmente hasta 2 decimales, separados por punto o coma.
  - Ejemplos válidos: 2500000   2500000.50   2500000,5
  - Ejemplos inválidos: 2.500.000   $2500   abc   1e6
"""

import re
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_DOWN, Decimal

MAX_LARGO_NOMBRE = 80
PATRON_MONTO = re.compile(r"^\d+([.,]\d{1,2})?$")
CIEN = Decimal("100")


@dataclass(frozen=True)
class ResultadoMeta:
    nombre: str
    objetivo: Decimal
    ahorrado: Decimal
    mensual: Decimal
    falta: Decimal
    meses: int
    porcentaje: Decimal
    cumplida: bool


def convertir_monto(texto, etiqueta):
    """Convierte el texto de un campo en Decimal o lanza ValueError con un mensaje claro."""
    texto = (texto or "").strip()
    if not texto:
        raise ValueError(f"El campo «{etiqueta}» es obligatorio.")
    if texto.startswith("-"):
        raise ValueError(f"El campo «{etiqueta}» no puede ser negativo.")
    if not PATRON_MONTO.match(texto):
        raise ValueError(
            f"El campo «{etiqueta}» debe ser un número sin separadores de miles "
            "y con máximo 2 decimales (ejemplo: 2500000 o 2500000.50)."
        )
    return Decimal(texto.replace(",", "."))


def calcular_meta(nombre, objetivo, ahorrado, mensual):
    """Calcula cuánto falta, cuántos meses se necesitan y el porcentaje de avance.

    Reglas de negocio:
      - El nombre es obligatorio (máximo 80 caracteres).
      - El objetivo debe ser mayor que cero.
      - Ahorrado y ahorro mensual no pueden ser negativos.
      - Si ya se ahorró el objetivo (o más): falta 0, meses 0, avance 100 %.
      - Si falta dinero, el ahorro mensual debe ser mayor que cero.
      - Los meses se redondean hacia arriba (2,1 meses -> 3 meses).
      - El porcentaje se trunca a 1 decimal para no mostrar 100 % antes de tiempo.
    """
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la meta es obligatorio.")
    if len(nombre) > MAX_LARGO_NOMBRE:
        raise ValueError(f"El nombre de la meta admite máximo {MAX_LARGO_NOMBRE} caracteres.")
    if objetivo <= 0:
        raise ValueError("El valor objetivo debe ser mayor que cero.")
    if ahorrado < 0:
        raise ValueError("El dinero ahorrado no puede ser negativo.")
    if mensual < 0:
        raise ValueError("El ahorro mensual no puede ser negativo.")

    if ahorrado >= objetivo:
        return ResultadoMeta(nombre, objetivo, ahorrado, mensual,
                             falta=Decimal("0"), meses=0, porcentaje=CIEN, cumplida=True)

    falta = objetivo - ahorrado
    if mensual == 0:
        raise ValueError("Para alcanzar la meta, el ahorro mensual debe ser mayor que cero.")

    meses = int((falta / mensual).to_integral_value(rounding=ROUND_CEILING))
    porcentaje = (ahorrado / objetivo * CIEN).quantize(Decimal("0.1"), rounding=ROUND_DOWN)
    return ResultadoMeta(nombre, objetivo, ahorrado, mensual,
                         falta=falta, meses=meses, porcentaje=porcentaje, cumplida=False)


def procesar_formulario(datos):
    """Valida los campos del formulario y calcula la meta.

    Devuelve (resultado, errores): si hay errores, resultado es None.
    """
    errores = []
    montos = {}
    campos = [("objetivo", "Valor objetivo"),
              ("ahorrado", "Dinero ya ahorrado"),
              ("mensual", "Ahorro mensual")]
    for clave, etiqueta in campos:
        try:
            montos[clave] = convertir_monto(datos.get(clave), etiqueta)
        except ValueError as error:
            errores.append(str(error))

    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        errores.insert(0, "El nombre de la meta es obligatorio.")

    if errores:
        return None, errores

    try:
        return calcular_meta(nombre, montos["objetivo"], montos["ahorrado"], montos["mensual"]), []
    except ValueError as error:
        return None, [str(error)]


def formato_moneda(valor):
    """Formatea 1234567.5 como '$ 1.234.567,50' (estilo colombiano)."""
    texto = f"{valor:,.2f}"  # 1,234,567.50
    return "$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
