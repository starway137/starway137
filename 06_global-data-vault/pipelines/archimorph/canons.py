"""Proporciones canónicas y control estadístico de coincidencias.

Atribuir una proporción "áurea" o "armónica" a un edificio es fácil: con
suficientes cánones candidatos y una tolerancia generosa, casi cualquier
razón cae cerca de alguno (Markowsky 1992). Por eso cada coincidencia se
reporta junto con la probabilidad de obtenerla por azar.
"""

import math

PHI = (1 + 5 ** 0.5) / 2

CANONES = {
    "1:1": 1.0,
    "5:4": 1.25,
    "4:3": 4 / 3,
    "raiz2": 2 ** 0.5,
    "3:2": 1.5,
    "aurea": PHI,
    "5:3": 5 / 3,
    "raiz3": 3 ** 0.5,
    "2:1": 2.0,
    "raiz5": 5 ** 0.5,
    "3:1": 3.0,
}

# Rango de razones (>=1) sobre el que se evalúa la cobertura del azar
RANGO_NULO = (1.0, 3.0)


def normalize_ratio(ratio):
    """Razón siempre >= 1 (largo / ancho, independiente de la orientación)."""
    return ratio if ratio >= 1 else 1.0 / ratio


def nearest_canon(ratio):
    """Devuelve (nombre, valor, desviación relativa con signo)."""
    r = normalize_ratio(ratio)
    name = min(CANONES, key=lambda k: abs(math.log(r / CANONES[k])))
    value = CANONES[name]
    return name, value, (r - value) / value


def chance_probability(tol):
    """Probabilidad de que una razón log-uniforme en RANGO_NULO caiga a menos de
    `tol` (relativo) de algún canon. Une intervalos solapados."""
    lo, hi = math.log(RANGO_NULO[0]), math.log(RANGO_NULO[1])
    intervals = []
    for c in CANONES.values():
        a = max(lo, math.log(c * (1 - tol)))
        b = min(hi, math.log(c * (1 + tol)))
        if b > a:
            intervals.append((a, b))
    intervals.sort()
    covered, cur_a, cur_b = 0.0, None, None
    for a, b in intervals:
        if cur_b is None or a > cur_b:
            if cur_b is not None:
                covered += cur_b - cur_a
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    if cur_b is not None:
        covered += cur_b - cur_a
    return covered / (hi - lo)


def canon_report(ratio, tol=0.02):
    name, value, dev = nearest_canon(ratio)
    return {
        "razon": normalize_ratio(ratio),
        "canon_cercano": name,
        "valor_canon": value,
        "desviacion_rel": dev,
        "dentro_tolerancia": abs(dev) <= tol,
        "tolerancia": tol,
        "prob_coincidencia_azar": chance_probability(tol),
    }
