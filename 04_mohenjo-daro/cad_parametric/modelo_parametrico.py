"""Generador por reglas de Mohenjo-daro.

Reglas (MD-H1, MD-H2):
  R1  Retícula ortogonal de calles principales de anchura fija.
  R2  Cada manzana se divide en franjas E-O separadas por callejones y cada
      franja en lotes; las medidas varían dentro de un rango (crecimiento
      orgánico dentro de una norma).
  R3  Toda medida de lote y de muro se ajusta a un múltiplo del módulo del
      ladrillo (largo + junta): la norma del material gobierna la del lote.
  R4  La ciudadela es una plataforma artificial separada de la Ciudad Baja.

El modelo cuantifica la densidad resultante para contrastarla con la
fracción de ocupación estimada en descriptores.json (MD-H3).

Uso:  python3 modelo_parametrico.py   ->  salida/mohenjo_daro_*.{svg,obj,json}
"""

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "06_global-data-vault" / "pipelines"))

from archimorph import geometry, io_utils  # noqa: E402

STEM = "mohenjo_daro"


def build(P):
    rng = np.random.default_rng(P["semilla"])
    m = geometry.Model("Mohenjo-daro", "MD", parametros=P)
    lb = P["ladrillo"]
    mod = lb["largo_m"] + lb["junta_m"]

    def snap(x):
        return max(round(x / mod), 1) * mod

    cb = P["ciudad_baja"]
    bx, by = cb["manzana_largo_ew_m"], cb["manzana_ancho_ns_m"]
    street = cb["calle_principal_m"]
    lane = cb["callejon_m"]
    total_w = cb["manzanas_x"] * bx + (cb["manzanas_x"] - 1) * street
    total_h = cb["manzanas_y"] * by + (cb["manzanas_y"] - 1) * street
    x0, y0 = -total_w / 2, -total_h / 2

    houses, lots_area, roof_area = 0, 0.0, 0.0
    for i in range(cb["manzanas_x"]):
        for j in range(cb["manzanas_y"]):
            mx = x0 + i * (bx + street)
            my = y0 + j * (by + street)
            m.prisma(f"Manzana {i + 1}-{j + 1}", mx + bx / 2, my + by / 2, bx, by, capa="terreno")
            y = my
            while y < my + by - cb["franja_ns_min_m"]:
                fh = snap(rng.uniform(cb["franja_ns_min_m"], cb["franja_ns_max_m"]))
                fh = min(fh, my + by - y)
                x = mx
                while x < mx + bx - cb["lote_ew_min_m"]:
                    lw = snap(rng.uniform(cb["lote_ew_min_m"], cb["lote_ew_max_m"]))
                    lw = min(lw, mx + bx - x)
                    wall = snap(cb["muro_casa_m"])
                    patio = cb["patio_frac"]
                    p = m.prisma(f"Casa {houses + 1}", x + lw / 2, y + fh / 2, lw, fh,
                                 h=cb["alto_casa_m"], capa="masa_sec")
                    # patio central: vacío dibujado en planta, descontado de la cubierta
                    pw, ph = snap(lw * patio ** 0.5), snap(fh * patio ** 0.5)
                    m.prisma(f"Patio {houses + 1}", x + lw / 2, y + fh / 2, pw, ph, capa="vacio")
                    p["muro_m"] = wall
                    houses += 1
                    lots_area += lw * fh
                    roof_area += lw * fh - pw * ph
                    x += lw
                y += fh + lane

    ci = P["ciudadela"]
    cx = x0 - ci["separacion_ciudad_baja_m"] - ci["ancho_ew_m"] / 2
    m.prisma("Ciudadela (plataforma)", cx, 0, ci["ancho_ew_m"], ci["largo_ns_m"], h=ci["alto_m"],
             capa="terraza")
    gb = P["gran_bano"]
    gy = gb["y_rel_ciudadela_m"]
    m.prisma("Edificio del Gran Baño", cx, gy, gb["edificio_ew_m"], gb["edificio_ns_m"], h=4,
             z0=ci["alto_m"], capa="galeria")
    m.prisma("Gran Baño (estanque)", cx, gy, gb["estanque_ew_m"], gb["estanque_ns_m"], capa="agua")
    m.linea(x0 - 20, 0, -x0 + 20, 0)
    m.linea(0, y0 - 20, 0, -y0 + 20)

    block_area = cb["manzanas_x"] * cb["manzanas_y"] * bx * by
    est = P["fraccion_ocupacion_estimada"]
    m.computos = {
        "modulo_ladrillo_m": mod,
        "proporcion_ladrillo": [lb["grueso_m"] / lb["grueso_m"], lb["ancho_m"] / lb["grueso_m"],
                                lb["largo_m"] / lb["grueso_m"]],
        "n_casas_generadas": houses,
        "superficie_media_lote_m2": lots_area / houses,
        "fraccion_huella_lotes": lots_area / block_area,
        "fraccion_cubierta": roof_area / block_area,
        "test_MD_H3": {
            "fraccion_ocupacion_estimada": est,
            "fraccion_cubierta_modelo": roof_area / block_area,
            "desviacion_rel": (roof_area / block_area - est) / est,
        },
        "gran_bano": {
            "razon_planta": gb["estanque_ns_m"] / gb["estanque_ew_m"],
            "volumen_m3": gb["estanque_ns_m"] * gb["estanque_ew_m"] * gb["profundidad_m"],
            "largo_en_ladrillos": gb["estanque_ns_m"] / mod,
            "ancho_en_ladrillos": gb["estanque_ew_m"] / mod,
        },
        "ciudadela_volumen_relleno_m3": ci["ancho_ew_m"] * ci["largo_ns_m"] * ci["alto_m"] * 0.85,
    }
    return m


def main():
    P = io_utils.read_json(HERE / "parametros.json")
    m = build(P)
    m.export(HERE / "salida", stem=STEM, svg_width=1100)
    return m


if __name__ == "__main__":
    model = main()
    c = model.computos
    print(f"Mohenjo-daro: {c['n_casas_generadas']} casas, cubierta {c['fraccion_cubierta']:.2f} "
          f"(estimada {c['test_MD_H3']['fraccion_ocupacion_estimada']})")
