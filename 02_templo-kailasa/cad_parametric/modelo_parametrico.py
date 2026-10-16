"""Ingeniería inversa sustractiva del Templo de Kailasa (Ellora, Cueva 16).

Regla generativa: excavar dos zanjas paralelas y una transversal en la ladera
basáltica, aislar un bloque y tallarlo de arriba abajo. El diseño se define por
lo que NO se extrae. El modelo:
  * calcula el volumen del patio con el terreno en pendiente (frente oeste
    más bajo que el fondo este),
  * resta el volumen retenido (plinto, mandapas, vimana, pilares, elefantes),
  * contrasta la masa extraída con la cifra citada (~200 000 t; KL-H1),
  * estima el ritmo de extracción implícito en la duración atribuida (KL-H3).

Uso:  python3 modelo_parametrico.py   ->  salida/kailasa_*.{svg,obj,json}
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "06_global-data-vault" / "pipelines"))

from archimorph import geometry, io_utils  # noqa: E402

STEM = "kailasa"


def _macizo(prim, factor):
    prim["factor_macizo"] = factor
    prim["volumen_m3"] *= factor
    return prim


def build(P):
    m = geometry.Model("Templo de Kailasa", "KL", parametros=P)
    pa = P["patio"]
    L, W = pa["largo_m"], pa["ancho_m"]
    d_mean = (pa["prof_frente_oeste_m"] + pa["prof_fondo_este_m"]) / 2

    # El patio se dibuja como vacío; su volumen se computa aparte (no es masa)
    m.prisma("Patio excavado (vacío)", 0, 0, L, W, h=0, capa="vacio")
    m.marco("Paredes de roca del escarpe", 0, 0, L + 12, W + 12, 6, capa="terreno")

    pl = P["plinto"]
    _macizo(m.prisma("Plinto con friso de elefantes", pl["x_m"], 0, pl["largo_m"], pl["ancho_m"],
                     h=pl["alto_m"], capa="masa_sec"), pl["factor_macizo"])
    mp = P["mandapa"]
    _macizo(m.prisma("Mandapa principal", pl["x_m"] + mp["x_rel_plinto_m"], 0, mp["lado_m"],
                     mp["lado_m"], h=mp["alto_m"], z0=pl["alto_m"], capa="galeria"),
            mp["factor_macizo"])
    vm = P["vimana"]
    m.torre_escalonada("Vimana", pl["x_m"] + vm["x_rel_plinto_m"], 0, vm["base_m"],
                       vm["alto_sobre_plinto_m"], vm["niveles"], vm["ratio_cima"],
                       z0=pl["alto_m"], capa="masa")
    nd = P["nandi_mandapa"]
    _macizo(m.prisma("Nandi mandapa", nd["x_m"], 0, nd["lado_m"], nd["lado_m"], h=nd["alto_m"],
                     capa="masa_sec"), nd["factor_macizo"])
    x_a, x_b = nd["x_m"] + nd["lado_m"] / 2, pl["x_m"] - pl["largo_m"] / 2
    m.prisma("Puente Nandi-mandapa", (x_a + x_b) / 2, 0, x_b - x_a, 3, h=1.2,
             z0=pl["alto_m"] - 1.2, capa="terraza")
    dv = P["dhvajastambha"]
    for i, (x, y) in enumerate(dv["posiciones"], start=1):
        m.prisma(f"Dhvajastambha {i}", x, y, dv["lado_m"], dv["lado_m"], h=dv["alto_m"], capa="masa")
    el = P["elefantes"]
    for i, (x, y) in enumerate(el["posiciones"], start=1):
        m.prisma(f"Elefante monolítico {i}", x, y, el["largo_m"], el["ancho_m"], h=el["alto_m"],
                 capa="masa_sec")
    m.linea(-L / 2 - 10, 0, L / 2 + 10, 0)

    # ------------------------------------------------------------ balance sustractivo
    v_patio = L * W * d_mean
    v_retenido = sum(p["volumen_m3"] for p in m.prims if p["capa"] in ("masa", "masa_sec", "galeria", "terraza"))
    v_extraido = v_patio - v_retenido
    masa_t = v_extraido * P["densidad_basalto_kg_m3"] / 1000
    citada = P["masa_extraida_citada_t"]
    anios = P["hipotesis_duracion_obra_anios"]
    m.computos = {
        "volumen_envolvente_patio_m3": v_patio,
        "volumen_retenido_templo_m3": v_retenido,
        "volumen_extraido_m3": v_extraido,
        "masa_extraida_t": masa_t,
        "test_KL_H1": {
            "masa_citada_t": citada,
            "desviacion_rel": (masa_t - citada) / citada,
            "nota": "La masa citada en la literatura es una cifra redonda; una coincidencia ±25 % se considera consistente.",
        },
        "razon_retenido_extraido": v_retenido / v_extraido,
        "test_KL_H3": {
            "duracion_hipotetica_anios": anios,
            "ritmo_m3_dia": v_extraido / (anios * 365),
            "ritmo_t_dia": masa_t / (anios * 365),
        },
        "altura_vimana_sobre_patio_m": pl["alto_m"] + vm["alto_sobre_plinto_m"],
    }
    return m


def main():
    P = io_utils.read_json(HERE / "parametros.json")
    m = build(P)
    m.export(HERE / "salida", stem=STEM)
    return m


if __name__ == "__main__":
    model = main()
    c = model.computos
    print(f"Kailasa: extraído {c['volumen_extraido_m3']:.0f} m³ = {c['masa_extraida_t']:.0f} t "
          f"(desv. {100 * c['test_KL_H1']['desviacion_rel']:+.1f} % vs citado)")
