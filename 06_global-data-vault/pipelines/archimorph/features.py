"""Extracción de features morfométricas a partir de elementos.csv + descriptores.json.

Todas las features se calculan a partir de los datos de cada caso de estudio,
de modo que una corrección en `data/` se propaga a todo el vault al volver a
ejecutar el pipeline.
"""

import copy
import math

import numpy as np

from . import canons, io_utils, paths, stats, structural

INCERT_POR_CALIDAD = {"A": 0.02, "B": 0.05, "C": 0.15}

# (nombre, unidad, descripción) — el orden define las columnas del dataset ML
CONTINUAS = [
    ("relacion_aspecto_recinto", "adim", "Largo/ancho del recinto principal (>=1)"),
    ("desviacion_canon_abs", "adim", "Desviación relativa absoluta respecto del canon más próximo"),
    ("razon_anidamiento_r", "adim", "Razón geométrica r de la cadena de recintos (L_k = L_0 r^k)"),
    ("r2_anidamiento", "adim", "R² del ajuste exponencial de la cadena de recintos"),
    ("niveles_jerarquicos", "conteo", "Número de niveles en la cadena de inclusión"),
    ("log10_escala_sitio_m", "log10 m", "Dimensión mayor del nivel 0"),
    ("log10_area_sitio_m2", "log10 m²", "Área del nivel 0"),
    ("log10_escala_en_modulos", "log10 módulos", "Dimensión del nivel 0 expresada en módulos métricos locales"),
    ("log10_altura_max_m", "log10 m", "Altura de la masa portante más alta"),
    ("esbeltez_masa_principal", "adim", "Altura / base equivalente (raíz del área) de la masa principal"),
    ("factor_volumen_masa_principal", "adim", "V / (A·H) de la masa principal"),
    ("tension_base_MPa", "MPa", "Tensión media de peso propio en la base de la masa principal"),
    ("log10_factor_seguridad", "log10 adim", "log10(fc_min / tensión) de la masa principal"),
    ("fraccion_ocupacion", "adim", "Fracción de huella construida dentro del recinto principal (masa/vacío)"),
    ("porosidad_vanos", "adim", "Proporción de vano en alzados"),
    ("orden_simetria_rotacional", "conteo", "Orden n del grupo de simetría (C_n / D_n)"),
    ("simetria_reflexion", "binario", "1 si el grupo contiene reflexiones"),
    ("eje_cos_n", "adim", "cos(n·azimut): vector axial invariante a la simetría de orden n"),
    ("eje_sin_n", "adim", "sin(n·azimut)"),
    ("fecha_media", "año (negativo = a.C.)", "Punto medio del intervalo de construcción"),
]

CATEGORICAS = [
    ("tipologia", "Tipología arquitectónica"),
    ("patron_compositivo", "Patrón compositivo dominante"),
    ("proceso_constructivo", "Aditivo / sustractivo / modular / encapsulamiento"),
    ("sistema_estructural", "Sistema estructural"),
    ("cosmograma", "Modelo cosmológico de referencia"),
    ("grupo_simetria", "Grupo de simetría en planta"),
    ("canon_cercano", "Canon de proporción más próximo al recinto principal"),
]


def load_materials():
    rows = io_utils.read_csv(paths.SCHEMA / "materiales.csv")
    return {r["material_id"]: r for r in rows}


def load_site(sid):
    elems = io_utils.read_csv(paths.elementos_path(sid))
    desc = io_utils.read_json(paths.descriptores_path(sid))
    return elems, desc


def _dims(e):
    return e["largo_m"], e["ancho_m"]


def area(e):
    return structural.footprint_area(e["forma_planta"], *_dims(e))


def base_equivalente(e):
    return structural.equivalent_base(e["forma_planta"], *_dims(e))


def mass_metrics(e, materials):
    """Esbeltez, tensión y factor de seguridad de un elemento portante."""
    mat = materials.get(e["material"])
    B = base_equivalente(e)
    out = {"base_equivalente_m": B, "esbeltez": e["alto_m"] / B}
    if mat and mat["fc_min_MPa"] and e["factor_volumen"]:
        sigma = structural.base_stress_mpa(mat["densidad_kg_m3"], e["alto_m"], e["factor_volumen"])
        out.update({
            "tension_base_MPa": sigma,
            "factor_seguridad_min": structural.safety_factor(mat["fc_min_MPa"], sigma),
            "factor_seguridad_max": structural.safety_factor(mat["fc_max_MPa"], sigma),
            "densidad_kg_m3": mat["densidad_kg_m3"],
            "volumen_m3": e["factor_volumen"] * area(e) * e["alto_m"],
            "masa_t": e["factor_volumen"] * area(e) * e["alto_m"] * mat["densidad_kg_m3"] / 1000,
        })
    return out


def nesting_fit(elems):
    chain = sorted((e for e in elems if e["nivel_jerarquico"] is not None),
                   key=lambda e: e["nivel_jerarquico"])
    k = [e["nivel_jerarquico"] for e in chain]
    L = [max(_dims(e)) for e in chain]
    fit = stats.fit_exponential(k, L)
    ratios = [b / a for a, b in zip(L, L[1:])]
    return chain, {
        "niveles": k,
        "dimension_mayor_m": L,
        "elementos": [e["element_id"] for e in chain],
        "razones_sucesivas": ratios,
        "r": fit["r"],
        "r_ic95": fit.get("r_ic"),
        "r2": fit["r2"],
        "n": fit["n"],
    }


def site_features(sid, elems, desc, materials):
    E = {e["element_id"]: e for e in elems}
    chain, nest = nesting_fit(elems)
    level0 = chain[0]

    rec = E[desc["recinto_principal_id"]]
    aspect = canons.normalize_ratio(rec["largo_m"] / rec["ancho_m"])
    canon = canons.canon_report(aspect)

    main = E[desc["masa_principal_id"]]
    mm = mass_metrics(main, materials)

    masses = [e for e in elems if e["es_masa_portante"] == 1 and e["alto_m"]]
    h_max = max(e["alto_m"] for e in masses)

    sym = desc["simetria"]
    n = max(int(sym["orden_rotacional"]), 1)
    theta = math.radians(desc["eje_principal"]["azimut_frente_deg"])
    crono = desc["cronologia"]
    est = desc["estimaciones"]

    f = {
        "relacion_aspecto_recinto": aspect,
        "desviacion_canon_abs": abs(canon["desviacion_rel"]),
        "razon_anidamiento_r": nest["r"],
        "r2_anidamiento": nest["r2"],
        "niveles_jerarquicos": float(len(chain)),
        "log10_escala_sitio_m": math.log10(max(_dims(level0))),
        "log10_area_sitio_m2": math.log10(area(level0)),
        "log10_escala_en_modulos": math.log10(max(_dims(level0)) / desc["modulo_metrico"]["valor_m"]),
        "log10_altura_max_m": math.log10(h_max),
        "esbeltez_masa_principal": mm["esbeltez"],
        "factor_volumen_masa_principal": main["factor_volumen"],
        "tension_base_MPa": mm["tension_base_MPa"],
        "log10_factor_seguridad": math.log10(mm["factor_seguridad_min"]),
        "fraccion_ocupacion": est["fraccion_ocupacion"]["valor"],
        "porosidad_vanos": est["porosidad_vanos"]["valor"],
        "orden_simetria_rotacional": float(n),
        "simetria_reflexion": 1.0 if sym["reflexion"] else 0.0,
        "eje_cos_n": round(math.cos(n * theta), 12),
        "eje_sin_n": round(math.sin(n * theta), 12),
        "fecha_media": (crono["inicio"] + crono["fin"]) / 2,
    }
    cat = {
        "tipologia": desc["tipologia"],
        "patron_compositivo": desc["patron_compositivo"],
        "proceso_constructivo": desc["proceso_constructivo"],
        "sistema_estructural": desc["sistema_estructural"],
        "cosmograma": desc["cosmograma"],
        "grupo_simetria": sym["grupo"],
        "canon_cercano": canon["canon_cercano"],
    }
    calidades = [e["calidad_dato"] for e in elems]
    return {
        "sitio_id": sid,
        "nombre": desc["nombre"],
        "azimut_frente_deg": desc["eje_principal"]["azimut_frente_deg"],
        "features": f,
        "categoricas": cat,
        "etiquetas_morfologicas": desc["etiquetas_morfologicas"],
        "diagnosticos": {
            "anidamiento": nest,
            "canon_recinto_principal": canon,
            "masa_principal": {"element_id": main["element_id"], **mm},
        },
        "calidad": {
            "proporcion_A": calidades.count("A") / len(calidades),
            "proporcion_B": calidades.count("B") / len(calidades),
            "proporcion_C": calidades.count("C") / len(calidades),
        },
    }


def element_rows(sid, elems, materials):
    rows = []
    for e in elems:
        r = {
            "sitio_id": sid,
            "element_id": e["element_id"],
            "nombre": e["nombre"],
            "tipo": e["tipo"],
            "nivel_jerarquico": e["nivel_jerarquico"],
            "es_masa_portante": e["es_masa_portante"],
            "forma_planta": e["forma_planta"],
            "material": e["material"],
            "largo_m": e["largo_m"],
            "ancho_m": e["ancho_m"],
            "alto_m": e["alto_m"],
            "factor_volumen": e["factor_volumen"],
            "log10_largo": math.log10(e["largo_m"]),
            "log10_area": math.log10(area(e)),
            "aspecto": canons.normalize_ratio(e["largo_m"] / e["ancho_m"]),
            "fecha_aprox": e["fecha_aprox"],
            "calidad_dato": e["calidad_dato"],
            "incertidumbre_rel": e["incertidumbre_rel"],
            "fuente_id": e["fuente_id"],
        }
        if e["es_masa_portante"] == 1 and e["alto_m"]:
            mm = mass_metrics(e, materials)
            r.update({
                "log10_alto": math.log10(e["alto_m"]),
                "base_equivalente_m": mm["base_equivalente_m"],
                "esbeltez": mm["esbeltez"],
                "tension_base_MPa": mm.get("tension_base_MPa"),
                "factor_seguridad_min": mm.get("factor_seguridad_min"),
                "volumen_m3": mm.get("volumen_m3"),
                "masa_t": mm.get("masa_t"),
            })
        rows.append(r)
    return rows


def perturb(elems, desc, rng):
    """Variante sintética: cada medida se perturba con su incertidumbre declarada
    (log-normal), y cada estimación con la incertidumbre asociada a su calidad."""
    elems = copy.deepcopy(elems)
    desc = copy.deepcopy(desc)
    for e in elems:
        u = e["incertidumbre_rel"] or INCERT_POR_CALIDAD[e["calidad_dato"]]
        for key in ("largo_m", "ancho_m", "alto_m"):
            if e[key]:
                e[key] *= math.exp(rng.normal(0, u))
        if e["forma_planta"] in ("circulo", "cuadrado"):
            e["ancho_m"] = e["largo_m"]
        if e["factor_volumen"] and e["factor_volumen"] < 1:
            e["factor_volumen"] = min(e["factor_volumen"] * math.exp(rng.normal(0, u)), 1.0)
    for est in desc["estimaciones"].values():
        u = INCERT_POR_CALIDAD[est["calidad"]]
        est["valor"] = float(np.clip(est["valor"] * math.exp(rng.normal(0, u)), 0, 1))
    return elems, desc
