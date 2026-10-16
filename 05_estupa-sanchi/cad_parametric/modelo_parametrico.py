"""Ingeniería inversa paramétrica de la Gran Estupa de Sanchi.

Regla generativa: simetría radial alrededor de un eje vertical (yashti) y
crecimiento por encapsulamiento (SN-H2): la estupa ashokana de ladrillo queda
envuelta por una cáscara de piedra que casi duplica su diámetro. Los accesos
acodados de la vedika generan simetría C4 quiral (SN-H3).

Uso:  python3 modelo_parametrico.py   ->  salida/sanchi_*.{svg,obj,json}
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "06_global-data-vault" / "pipelines"))

from archimorph import geometry, io_utils, structural  # noqa: E402

STEM = "sanchi"


def build(P):
    m = geometry.Model("Gran Estupa de Sanchi", "SN", parametros=P)
    hasta = P["modulo_hasta_m"]
    an, me, ve = P["anda"], P["medhi"], P["vedika_suelo"]
    D, H = an["diametro_m"], an["alto_m"]

    m.anillo("Vedika de suelo", 0, 0, ve["diametro_m"], ve["espesor_m"], h=ve["alto_m"], capa="muro")
    m.casquete("Anda", 0, 0, D, H, capa="masa")
    m.anillo("Baranda del medhi", 0, 0, D + 2 * me["ancho_deambulatorio_m"], 0.3,
             h=me["alto_baranda_m"], z0=me["alto_m"], capa="muro")
    m.cilindro("Fase ashokana (núcleo envuelto)", 0, 0, P["fase_ashoka"]["diametro_m"], capa="fase")

    hm = P["harmika"]
    m.prisma("Harmika", 0, 0, hm["lado_m"], hm["lado_m"], h=hm["alto_m"], z0=H, capa="muro")
    ch = P["chhatra"]
    z = H + hm["alto_m"]
    m.cilindro("Yashti (eje)", 0, 0, ch["yashti_m"], h=ch["separacion_m"] * len(ch["discos_m"]) + 0.5,
               z0=H, capa="masa_sec")
    for i, d in enumerate(ch["discos_m"], start=1):
        m.cilindro(f"Chhatra {i}", 0, 0, d, h=0.25, z0=z + (i - 0.5) * ch["separacion_m"], capa="masa_sec")

    to = P["toranas"]
    R = ve["diametro_m"] / 2 + to["distancia_vedika_m"]
    for k, az in enumerate(to["azimuts_deg"], start=1):
        th = math.radians(az)
        u = (math.sin(th), math.cos(th))      # radial hacia fuera
        t = (math.cos(th), -math.sin(th))     # tangente en sentido horario
        for s in (-1, 1):
            m.prisma(f"Torana {k} pilar {'ab'[s > 0]}", R * u[0] + s * to["luz_m"] / 2 * t[0],
                     R * u[1] + s * to["luz_m"] / 2 * t[1], to["pilar_lado_m"], to["pilar_lado_m"],
                     h=to["alto_m"], capa="puerta")
        # retorno acodado de la vedika, desplazado en sentido horario: molinete
        rr = ve["diametro_m"] / 2 - ve["espesor_m"] / 2
        c = (rr * u[0] + (to["luz_m"] / 2 + to["retorno_m"] / 2) * t[0],
             rr * u[1] + (to["luz_m"] / 2 + to["retorno_m"] / 2) * t[1])
        m.prisma(f"Retorno acodado {k}", c[0] + 1.2 * u[0], c[1] + 1.2 * u[1], to["retorno_m"],
                 ve["espesor_m"], h=ve["alto_m"], rot=-az, capa="muro")
        m.linea(0, 0, (R + 6) * u[0], (R + 6) * u[1])

    f = structural.spherical_cap_factor(D, H)
    d_a = P["fase_ashoka"]["diametro_m"]
    camino_suelo = math.pi * (ve["diametro_m"] - ve["espesor_m"] + D) / 2
    m.computos = {
        "razon_altura_diametro": H / D,
        "razon_hemisferio_ideal": 0.5,
        "factor_volumen_casquete": f,
        "volumen_anda_m3": m.volumen(capas={"masa"}, prefijo="Anda"),
        "test_SN_H2": {
            "factor_crecimiento_diametro": D / d_a,
            "factor_crecimiento_volumen_homotetico": (D / d_a) ** 3,
            "volumen_cascara_m3": math.pi * H * (3 * (D / 2) ** 2 + H ** 2) / 6
            - math.pi * (H * d_a / D) * (3 * (d_a / 2) ** 2 + (H * d_a / D) ** 2) / 6,
        },
        "test_SN_H3": {
            "orden_rotacional": len(to["azimuts_deg"]),
            "reflexion": False,
            "sentido_molinete": "horario (pradakshina)",
        },
        "recorridos_pradakshina": {
            "suelo_m": camino_suelo,
            "suelo_en_hasta": camino_suelo / hasta,
            "medhi_m": math.pi * (D + me["ancho_deambulatorio_m"]),
        },
        "dimensiones_en_hasta": {"diametro_anda": D / hasta, "altura_anda": H / hasta,
                                 "diametro_vedika": ve["diametro_m"] / hasta},
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
    print(f"Sanchi: H/D={c['razon_altura_diametro']:.3f}, f={c['factor_volumen_casquete']:.3f}, "
          f"crecimiento x{c['test_SN_H2']['factor_crecimiento_diametro']:.2f} en diámetro")
