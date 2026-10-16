"""Ingeniería inversa paramétrica de Angkor Wat.

Regla generativa: una cadena de recintos rectangulares concéntricos cuyo
centro se eleva por terrazas sucesivas hasta un quincunce de torres (el monte
Meru y sus cuatro picos). El modelo calcula además:
  * longitudes en hat para contrastar la hipótesis calendárica (AW-H2),
  * el factor de volumen real del templo-montaña (consistencia con AW-M01),
  * el ángulo visual de la torre central desde la puerta oeste (AW-H3).

Uso:  python3 modelo_parametrico.py   ->  salida/angkor_wat_*.{svg,obj,json}
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "06_global-data-vault" / "pipelines"))

from archimorph import geometry, io_utils  # noqa: E402

STEM = "angkor_wat"


def build(P):
    m = geometry.Model("Angkor Wat", "AW", parametros=P)
    hat = P["modulo_hat_m"]
    dx = P["desplazamiento_templo_x_m"]

    foso = P["foso"]
    m.marco("Foso", 0, 0, foso["largo_m"], foso["ancho_m"], foso["anchura_agua_m"], capa="agua")
    rec = P["recinto_exterior"]
    m.marco("Recinto exterior", 0, 0, rec["largo_m"], rec["ancho_m"], rec["espesor_m"],
            h=rec["alto_m"], capa="muro")

    # Calzadas sobre el eje oeste: foso -> puerta -> templo
    t3 = P["terrazas"][0]
    x_foso = -foso["largo_m"] / 2
    x_muro = -rec["largo_m"] / 2
    x_templo = dx - t3["largo_m"] / 2
    ancho = P["calzada_oeste"]["ancho_m"]
    m.prisma("Calzada sobre el foso", (x_foso + x_muro) / 2, 0, x_muro - x_foso, ancho, h=1.0,
             capa="terraza")
    m.prisma("Calzada interior", (x_muro + x_templo) / 2, 0, x_templo - x_muro, ancho, h=1.5,
             capa="terraza")

    # Terrazas apiladas con galería perimetral sobre cada una
    z = 0.0
    for t in P["terrazas"]:
        m.prisma(t["nombre"], dx, 0, t["largo_m"], t["ancho_m"], h=t["alto_m"], z0=z, capa="terraza")
        z += t["alto_m"]
        m.marco(f"Galería de {t['nombre']}", dx, 0, t["largo_m"], t["ancho_m"],
                t["ancho_galeria_m"], h=t["alto_galeria_m"], z0=z, capa="galeria")
    z_top = z

    q = P["quincunce"]
    tc, te = q["torre_central"], q["torres_esquina"]
    m.torre_escalonada("Torre central", dx, 0, tc["base_m"], tc["alto_m"], tc["niveles"],
                       tc["ratio_cima"], z0=z_top, capa="masa")
    off = P["terrazas"][-1]["largo_m"] / 2 - te["retranqueo_m"]
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1)), start=1):
        m.torre_escalonada(f"Torre de esquina {i}", dx + sx * off, sy * off, te["base_m"],
                           te["alto_m"], te["niveles"], te["ratio_cima"], z0=z_top, capa="masa_sec")

    m.linea(x_foso - 40, 0, foso["largo_m"] / 2 + 40, 0)
    m.linea(dx, -foso["ancho_m"] / 2 - 40, dx, foso["ancho_m"] / 2 + 40)

    # ------------------------------------------------------------ cómputos
    h_total = z_top + tc["alto_m"]
    v_solido = m.volumen(capas={"terraza", "masa", "masa_sec"}) - \
        sum(p["volumen_m3"] for p in m.prims if p["nombre"].startswith("Calzada"))
    f_vol = v_solido / (t3["largo_m"] * t3["ancho_m"] * h_total)
    d_oeste = abs(x_foso - dx)
    ref = P["referencia_stencel_1976"]["distancia_entrada_oeste_a_torre_hat"]
    m.computos = {
        "altura_total_m": h_total,
        "volumen_macizo_templo_m3": v_solido,
        "factor_volumen_templo_montana": f_vol,
        "dimensiones_en_hat": {
            "foso_largo": foso["largo_m"] / hat,
            "recinto_largo": rec["largo_m"] / hat,
            "recinto_ancho": rec["ancho_m"] / hat,
            **{f"terraza_{i}_largo": t["largo_m"] / hat for i, t in enumerate(P["terrazas"])},
            "altura_total": h_total / hat,
        },
        "test_AW_H2": {
            "distancia_borde_oeste_foso_a_torre_m": d_oeste,
            "distancia_en_hat": d_oeste / hat,
            "valor_hipotesis_hat": ref,
            "desviacion_rel": (d_oeste / hat - ref) / ref,
            "nota": "Coincidencia sensible a ±5 % en las dimensiones del foso (calidad A aproximada).",
        },
        "test_AW_H3": {
            "angulo_visual_torre_desde_puerta_oeste_deg":
                math.degrees(math.atan(h_total / abs(x_muro - dx))),
            "azimut_eje_deg": 90.0,
            "nota": "Desde la puerta oeste, el sol equinoccial nace sobre el eje E-O y, por tanto, tras la torre central.",
        },
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
    print(f"Angkor Wat: H={c['altura_total_m']:.1f} m, f_vol={c['factor_volumen_templo_montana']:.3f}, "
          f"eje oeste={c['test_AW_H2']['distancia_en_hat']:.0f} hat")
