"""Ingeniería inversa paramétrica de Wat Chaiwatthanaram (Ayutthaya).

Regla generativa: el esquema jemer del templo-montaña (quincunce + recinto)
se reescala y se reorienta hacia el río. El modelo calcula las proporciones
adimensionales que permiten contrastar AY-H1 (transferencia de la regla
compositiva de Angkor con un cambio de escala) frente a una copia literal.

Uso:  python3 modelo_parametrico.py   ->  salida/wat_chaiwatthanaram_*.{svg,obj,json}
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "06_global-data-vault" / "pipelines"))

from archimorph import geometry, io_utils  # noqa: E402

STEM = "wat_chaiwatthanaram"


def build(P):
    m = geometry.Model("Wat Chaiwatthanaram", "AY", parametros=P)
    wa = P["modulo_wa_m"]
    g = P["galeria"]
    m.marco("Galería perimetral (phra rabiang)", 0, 0, g["largo_m"], g["ancho_m"], g["espesor_m"],
            h=g["alto_m"], capa="galeria")

    mu = P["merus"]
    hx, hy = g["largo_m"] / 2 - g["espesor_m"] / 2, g["ancho_m"] / 2 - g["espesor_m"] / 2
    puntos = [(sx * hx, sy * hy) for sx in (-1, 1) for sy in (-1, 1)]
    puntos += [(0, hy), (0, -hy), (hx, 0), (-hx, 0)]
    for i, (x, y) in enumerate(puntos, start=1):
        m.torre_escalonada(f"Meru thit {i}", x, y, mu["lado_m"], mu["alto_m"], mu["niveles"],
                           mu["ratio_cima"], capa="masa_sec")

    pf = P["plataforma"]
    m.prisma("Plataforma del quincunce", 0, 0, pf["lado_m"], pf["lado_m"], h=pf["alto_m"],
             capa="terraza")
    pc = P["prang_central"]
    m.torre_escalonada("Prang central", 0, 0, pc["base_m"], pc["alto_total_m"] - pf["alto_m"],
                       pc["niveles"], pc["ratio_cima"], z0=pf["alto_m"], capa="masa")
    pe = P["prangs_esquina"]
    off = pf["lado_m"] / 2 - pe["retranqueo_m"]
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1)), start=1):
        m.torre_escalonada(f"Prang de esquina {i}", sx * off, sy * off, pe["base_m"], pe["alto_m"],
                           pe["niveles"], pe["ratio_cima"], z0=pf["alto_m"], capa="masa_sec")

    ub = P["ubosot"]
    x_ub = g["largo_m"] / 2 + ub["separacion_galeria_m"] + ub["largo_m"] / 2
    m.prisma("Ubosot (sala de ordenación)", x_ub, 0, ub["largo_m"], ub["ancho_m"], h=ub["alto_m"],
             capa="galeria")
    rio = P["orilla_rio_x_m"]
    m.prisma("Río Chao Phraya (orilla)", rio + 15, 0, 30, g["ancho_m"] * 2, capa="agua")
    m.linea(-g["largo_m"] / 2 - 10, 0, rio, 0)

    ref = P["referencia_angkor"]
    m.computos = {
        "dimensiones_en_wa": {
            "galeria_largo": g["largo_m"] / wa,
            "galeria_ancho": g["ancho_m"] / wa,
            "plataforma_lado": pf["lado_m"] / wa,
            "altura_prang": pc["alto_total_m"] / wa,
        },
        "proporciones_adimensionales": {
            "altura_prang_sobre_largo_galeria": pc["alto_total_m"] / g["largo_m"],
            "plataforma_sobre_galeria": pf["lado_m"] / g["largo_m"],
            "base_prang_sobre_plataforma": pc["base_m"] / pf["lado_m"],
            "base_esquina_sobre_base_central": pe["base_m"] / pc["base_m"],
        },
        "test_AY_H1": {
            "angkor_altura_sobre_galeria_exterior": ref["altura_m"] / ref["largo_galeria_III_m"],
            "angkor_bakan_sobre_galeria_exterior": ref["lado_bakan_m"] / ref["largo_galeria_III_m"],
            "factor_escala_lineal_vs_angkor": g["largo_m"] / ref["largo_galeria_III_m"],
            "factor_escala_altura_vs_angkor": pc["alto_total_m"] / ref["altura_m"],
            "nota": "Si la regla se transfiere por homotecia, ambos factores de escala coincidirían; "
                    "un factor de altura mayor indica verticalización del modelo jemer.",
        },
        "volumen_macizo_m3": m.volumen(capas={"masa", "masa_sec", "terraza"}),
    }
    return m


def main():
    P = io_utils.read_json(HERE / "parametros.json")
    m = build(P)
    m.export(HERE / "salida", stem=STEM)
    return m


if __name__ == "__main__":
    model = main()
    t = model.computos["test_AY_H1"]
    print(f"Wat Chaiwatthanaram: escala lineal {t['factor_escala_lineal_vs_angkor']:.2f}, "
          f"escala de altura {t['factor_escala_altura_vs_angkor']:.2f} respecto de Angkor")
