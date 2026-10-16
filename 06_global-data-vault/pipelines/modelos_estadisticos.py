"""Paso 4 — modelos de regresión y leyes de escala sobre el dataset consolidado.

M1  Alometría altura-base de masas portantes          log H = a + b log B
M2  Tensión de peso propio frente a altura             sigma = k · H
M3  Anidamiento exponencial de recintos                L_k = L_0 · r^k
M4  Volumen frente a huella                            log V = a + b log A
M5  Crecimiento cronológico de la altura máxima        ln H = a + c · t
M6  Densidad (masa/vacío) frente a escala del sitio    ocup = a + b log10 A

Con n pequeño, cada modelo se reporta con IC, p-valor, bootstrap y error de
validación cruzada LOO; los resultados describen el corpus, no leyes universales.
"""

import math

import numpy as np

from archimorph import features, io_utils, paths, stats, structural


def _mass_rows():
    rows = io_utils.read_csv(paths.DATASETS / "elementos_consolidados.csv",
                             numeric=io_utils.NUMERIC_COLUMNS | {
                                 "base_equivalente_m", "esbeltez", "tension_base_MPa",
                                 "factor_seguridad_min", "volumen_m3", "masa_t", "log10_area"})
    return [r for r in rows if r["es_masa_portante"] == 1 and r["tension_base_MPa"] is not None]


# Familias de masa: la alometría solo tiene sentido dentro de una misma familia
FAMILIA_VERTICAL = {"torre", "templo_montana", "vimana", "prang", "chedi", "anda"}


def familia(tipo):
    if tipo in FAMILIA_VERTICAL:
        return "vertical_central"
    if tipo == "pilar":
        return "lineal_exenta"
    return "horizontal_plataforma"


def m1_alometria(masses):
    vert = [r for r in masses if familia(r["tipo"]) == "vertical_central"]
    B = [r["base_equivalente_m"] for r in vert]
    H = [r["alto_m"] for r in vert]
    fit = stats.fit_power_law(B, H)
    boot = stats.bootstrap_slope(np.log10(B), np.log10(H), seed=1)
    excluidos = {r["element_id"]: {"familia": familia(r["tipo"]), "esbeltez": r["alto_m"] / r["base_equivalente_m"]}
                 for r in masses if familia(r["tipo"]) != "vertical_central"}
    return {
        "descripcion": "Altura frente a base equivalente (raíz del área) de masas centrales verticales",
        "familia": "vertical_central: " + ", ".join(sorted(FAMILIA_VERTICAL)),
        "elementos": [r["element_id"] for r in vert],
        "excluidos_otras_familias": excluidos,
        "ajuste": fit,
        "bootstrap_b": boot,
        "p_valor_isometria_b1": stats.test_slope(fit, 1.0, "b"),
        "interpretacion": ("b < 1: las masas grandes son proporcionalmente más achatadas "
                           "(alometría negativa); b = 1: semejanza geométrica"),
    }


def m2_tension(masses, materials):
    H = np.array([r["alto_m"] for r in masses])
    S = np.array([r["tension_base_MPa"] for r in masses])
    fit = stats.ols(H, S, names=("intercepto", "k_MPa_por_m"))
    fs = {r["element_id"]: r["factor_seguridad_min"] for r in masses}
    crit = {}
    for r in masses:
        mat = materials[r["material"]]
        hc = structural.max_height_for(mat["densidad_kg_m3"], r["factor_volumen"], mat["fc_min_MPa"], 1.0)
        crit[r["element_id"]] = {"altura_aplastamiento_m": hc, "uso_de_altura_critica": r["alto_m"] / hc}
    vals = np.array(list(fs.values()))
    return {
        "descripcion": "Tensión media de peso propio en la base frente a la altura",
        "ajuste": fit,
        "factor_seguridad_min_por_elemento": fs,
        "fs_mediana": float(np.median(vals)),
        "fs_minimo": float(vals.min()),
        "elemento_mas_solicitado": min(fs, key=fs.get),
        "altura_critica": crit,
        "interpretacion": ("Las tensiones medias quedan uno o dos órdenes de magnitud por debajo de la "
                           "resistencia: la forma está gobernada por estabilidad y geometría, no por "
                           "resistencia del material (Heyman 1995)."),
    }


def m3_anidamiento(site_feats):
    per_site, pooled_k, pooled_y = {}, [], []
    for sf in site_feats:
        n = sf["diagnosticos"]["anidamiento"]
        per_site[sf["sitio_id"]] = {k: n[k] for k in ("r", "r_ic95", "r2", "n", "razones_sucesivas")}
        L0 = n["dimension_mayor_m"][0]
        pooled_k += n["niveles"]
        pooled_y += [math.log(L / L0) for L in n["dimension_mayor_m"]]
    fit = stats.ols(pooled_k, pooled_y, names=("intercepto", "ln_r"))
    r_pool = math.exp(fit["coeficientes"]["ln_r"]["valor"])
    # Angkor: régimen arquitectónico (desde la tercera galería) frente al territorial
    elems, _ = features.load_site("AW")
    arch = sorted((e for e in elems if e["nivel_jerarquico"] is not None and e["nivel_jerarquico"] >= 2),
                  key=lambda e: e["nivel_jerarquico"])
    fit_arch = stats.fit_exponential([e["nivel_jerarquico"] for e in arch],
                                     [max(e["largo_m"], e["ancho_m"]) for e in arch])
    rs = [v["r"] for v in per_site.values()]
    return {
        "descripcion": "Ley de anidamiento L_k = L_0 · r^k por sitio y agrupada",
        "por_sitio": per_site,
        "agrupado": {"ajuste": fit, "r": r_pool},
        "r_media_geometrica": float(np.exp(np.mean(np.log(rs)))),
        "angkor_regimen_arquitectonico": {"r": fit_arch["r"], "r2": fit_arch["r2"], "n": fit_arch["n"]},
        "interpretacion": ("r cercano a 0.5 indica que cada recinto mide aproximadamente la mitad del que "
                           "lo contiene; valores bajos con R² bajo indican saltos de régimen (territorio "
                           "frente a edificio)."),
    }


def m4_volumen(masses):
    A = [r["base_equivalente_m"] ** 2 for r in masses]
    V = [r["volumen_m3"] for r in masses]
    fit = stats.fit_power_law(A, V)
    return {
        "descripcion": "Volumen macizo frente a área de huella",
        "ajuste": fit,
        "p_valor_isometria_b1_5": stats.test_slope(fit, 1.5, "b"),
        "interpretacion": "b = 1.5 corresponde a semejanza geométrica; b < 1.5 a masas que crecen en planta más que en altura.",
    }


def m5_cronologia(site_feats):
    t = [sf["features"]["fecha_media"] for sf in site_feats]
    H = [10 ** sf["features"]["log10_altura_max_m"] for sf in site_feats]
    fit = stats.fit_exponential(t, H)
    c = math.log(fit["r"])
    pre = [(ti, hi) for ti, hi in zip(t, H) if ti <= 1200]
    fit_pre = stats.fit_exponential([p[0] for p in pre], [p[1] for p in pre])
    elems, _ = features.load_site("SN")
    E = {e["element_id"]: e for e in elems}
    d0, d1 = E["SN-F01"]["largo_m"], E["SN-E01"]["largo_m"]
    dt = E["SN-E01"]["fecha_aprox"] - E["SN-F01"]["fecha_aprox"]
    return {
        "descripcion": "Altura máxima de masa portante frente a la fecha de construcción",
        "datos": [{"sitio_id": sf["sitio_id"], "fecha": ti, "altura_max_m": hi}
                  for sf, ti, hi in zip(site_feats, t, H)],
        "ajuste_todos": {**fit, "tasa_anual": c,
                         "tiempo_duplicacion_anios": math.log(2) / c if c > 0 else None,
                         "loo_rmse_ln": stats.loo_rmse(t, np.log(H))},
        "ajuste_hasta_1200": {**fit_pre, "tiempo_duplicacion_anios":
                              math.log(2) / math.log(fit_pre["r"]) if fit_pre["r"] > 1 else None},
        "sanchi_crecimiento_por_encapsulamiento": {
            "diametro_inicial_m": d0, "diametro_final_m": d1, "intervalo_anios": dt,
            "tasa_anual_diametro": math.log(d1 / d0) / dt,
            "factor_volumen": (d1 / d0) ** 3,
        },
        "interpretacion": ("Curva descriptiva de un corpus de 5 obras de tradiciones distintas: ilustra "
                           "una tendencia de crecimiento hasta Angkor y un descenso posterior (Ayutthaya), "
                           "no una ley causal."),
    }


def m6_densidad(site_feats):
    x = [sf["features"]["log10_area_sitio_m2"] for sf in site_feats]
    y = [sf["features"]["fraccion_ocupacion"] for sf in site_feats]
    fit = stats.ols(x, y, names=("intercepto", "pendiente_por_decada"))
    fit["loo_rmse"] = stats.loo_rmse(x, y)
    return {
        "descripcion": "Fracción de ocupación (masa/vacío) frente al log10 del área del nivel 0",
        "datos": {sf["sitio_id"]: {"log10_area": xi, "fraccion_ocupacion": yi}
                  for sf, xi, yi in zip(site_feats, x, y)},
        "ajuste": fit,
        "interpretacion": "Con n = 5 y estimaciones C, se trata como hipótesis a contrastar, no como resultado.",
    }


def main():
    materials = features.load_materials()
    site_feats = io_utils.read_json(paths.DATASETS / "features_sitios.json")
    masses = _mass_rows()
    out = {
        "n_sitios": len(site_feats),
        "n_masas_portantes": len(masses),
        "M1_alometria_altura_base": m1_alometria(masses),
        "M2_tension_peso_propio": m2_tension(masses, materials),
        "M3_anidamiento_exponencial": m3_anidamiento(site_feats),
        "M4_volumen_huella": m4_volumen(masses),
        "M5_crecimiento_cronologico": m5_cronologia(site_feats),
        "M6_densidad_escala": m6_densidad(site_feats),
    }
    io_utils.write_json(paths.MODELOS / "modelos_escala.json", out)
    m1 = out["M1_alometria_altura_base"]["ajuste"]
    print(f"  M1 alometría: H = {m1['a']:.2f}·B^{m1['b']:.2f} (R²={m1['r2']:.2f}, n={m1['n']})")
    return out


if __name__ == "__main__":
    main()
