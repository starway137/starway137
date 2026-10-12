"""Prior generativo y conjunto de restricciones para co-diseño.

El dataset no se usa como catálogo de formas a copiar sino como:
  1. Prior: distribuciones (log-normales) de proporciones, razones de
     anidamiento, esbelteces y densidades observadas en los cinco casos.
  2. Restricciones: reglas duras (estática de peso propio con material
     contemporáneo) y blandas (rango histórico observado) que acotan el
     espacio de diseño.
  3. Métrica de afinidad: distancia estandarizada entre un proyecto y cada caso,
     útil para rediseño ("¿a qué lógica histórica se parece esta propuesta?").
"""

import math

import numpy as np

from . import geometry, structural

# Features que se trasladan al espacio de diseño: (nombre, espacio)
PRIOR_FEATURES = [
    ("relacion_aspecto_recinto", "log"),
    ("razon_anidamiento_r", "log"),
    ("niveles_jerarquicos", "lineal"),
    ("esbeltez_masa_principal", "log"),
    ("factor_volumen_masa_principal", "log"),
    ("fraccion_ocupacion", "logit"),
    ("porosidad_vanos", "logit"),
]
TORRE_NIVELES = 6
TORRE_RATIO_CIMA = 0.3

AFINIDAD_FEATURES = [
    "relacion_aspecto_recinto", "razon_anidamiento_r", "esbeltez_masa_principal",
    "factor_volumen_masa_principal", "fraccion_ocupacion", "porosidad_vanos",
    "orden_simetria_rotacional", "simetria_reflexion",
]


def _fwd(x, space):
    if space == "log":
        return math.log(x)
    if space == "logit":
        x = min(max(x, 1e-3), 1 - 1e-3)
        return math.log(x / (1 - x))
    return x


def _inv(z, space):
    if space == "log":
        return math.exp(z)
    if space == "logit":
        return 1 / (1 + math.exp(-z))
    return z


def build_prior(site_feats, modelos):
    sids = [s["sitio_id"] for s in site_feats]
    cont = {}
    for name, space in PRIOR_FEATURES:
        vals = {s["sitio_id"]: s["features"][name] for s in site_feats}
        z = np.array([_fwd(v, space) for v in vals.values()])
        cont[name] = {
            "espacio": space,
            "media_transformada": float(z.mean()),
            "desv_transformada": float(z.std(ddof=1)),
            "min": min(vals.values()),
            "max": max(vals.values()),
            "por_sitio": vals,
        }
    cats = {}
    for name in ("grupo_simetria", "patron_compositivo", "proceso_constructivo", "tipologia"):
        por_sitio = {s["sitio_id"]: s["categoricas"][name] for s in site_feats}
        freq = {}
        for v in por_sitio.values():
            freq[v] = freq.get(v, 0) + 1 / len(sids)
        cats[name] = {"frecuencias": freq, "por_sitio": por_sitio}
    sym = {s["sitio_id"]: {"orden": s["features"]["orden_simetria_rotacional"],
                           "reflexion": bool(s["features"]["simetria_reflexion"])}
           for s in site_feats}
    allo = modelos["M1_alometria_altura_base"]["ajuste"]
    return {
        "descripcion": "Prior generativo derivado de los cinco casos de estudio",
        "sitios": sids,
        "continuas": cont,
        "categoricas": cats,
        "simetria_por_sitio": sym,
        "orientacion_por_sitio": {s["sitio_id"]: s["azimut_frente_deg"] for s in site_feats},
        "alometria": {
            "forma": "log10 H = log10_a + b · log10 B",
            "log10_a": allo["coeficientes"]["log10_a"]["valor"],
            "b": allo["b"],
            "sigma_resid_log10": allo["sigma_resid"],
        },
        "restricciones": [
            {"id": "R1", "tipo": "dura", "regla": "tension_base <= fc_min / FS",
             "descripcion": "Estática de peso propio con el material contemporáneo elegido"},
            {"id": "R2", "tipo": "blanda", "regla": "esbeltez en [min, max] histórico ±20 %",
             "descripcion": "Esbeltez de la masa principal dentro del rango observado"},
            {"id": "R3", "tipo": "blanda", "regla": "razon_anidamiento_r en [min, max] histórico",
             "descripcion": "Gradiente de escala entre recintos sucesivos"},
            {"id": "R4", "tipo": "blanda", "regla": "fraccion_ocupacion en [min, max] histórico",
             "descripcion": "Balance masa/vacío del recinto principal"},
            {"id": "R5", "tipo": "dura", "regla": "dimension del nivel k+1 < dimension del nivel k",
             "descripcion": "Inclusión estricta de la cadena de recintos"},
            {"id": "R6", "tipo": "dura", "regla": "lado del núcleo >= base_min",
             "descripcion": "Truncamiento de la cadena por tamaño constructivo mínimo del núcleo"},
        ],
    }


def _mix(prior, name, weights, tau, rng):
    c = prior["continuas"][name]
    z = sum(w * _fwd(c["por_sitio"][sid], c["espacio"]) for sid, w in weights.items())
    z += tau * c["desv_transformada"] * rng.normal()
    return _inv(z, c["espacio"])


def parse_weights(text, sids):
    if not text:
        return {sid: 1 / len(sids) for sid in sids}
    w = {}
    for part in text.split(","):
        k, v = part.split("=")
        k = k.strip().upper()
        if k not in sids:
            raise ValueError(f"Sitio desconocido en la mezcla: {k}")
        w[k] = float(v)
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def sample_design(prior, area_m2, material, materials, weights, fs=3.0, tau=0.3,
                  seed=0, azimut=None, base_min=8.0):
    rng = np.random.default_rng(seed)
    traza = []
    dominant = max(weights, key=weights.get)
    c = prior["continuas"]

    aspect = max(1.0, _mix(prior, "relacion_aspecto_recinto", weights, tau, rng))
    r = _mix(prior, "razon_anidamiento_r", weights, tau, rng)
    r_lo, r_hi = c["razon_anidamiento_r"]["min"], c["razon_anidamiento_r"]["max"]
    if not r_lo <= r <= r_hi:
        traza.append(f"R3: r={r:.3f} proyectada al rango histórico [{r_lo:.3f}, {r_hi:.3f}]")
        r = min(max(r, r_lo), r_hi)
    n_levels = int(round(_mix(prior, "niveles_jerarquicos", weights, tau, rng)))
    n_levels = min(max(n_levels, 3), 6)
    ocup = _mix(prior, "fraccion_ocupacion", weights, tau, rng)
    poros = _mix(prior, "porosidad_vanos", weights, tau, rng)
    f = min(_mix(prior, "factor_volumen_masa_principal", weights, tau, rng), 1.0)

    L0 = math.sqrt(area_m2 * aspect)
    # R6: la cadena se trunca cuando el núcleo cae por debajo del tamaño constructivo mínimo
    n_fit = 1 + int(math.floor(math.log(base_min / (L0 / aspect)) / math.log(r)))
    if n_fit < n_levels:
        traza.append(f"R6: cadena truncada de {n_levels} a {max(n_fit, 2)} niveles (núcleo >= {base_min:g} m)")
        n_levels = max(n_fit, 2)
    levels = []
    for k in range(n_levels):
        a_k = 1 + (aspect - 1) * (1 - k / max(n_levels - 1, 1))
        L = L0 * r ** k
        levels.append({"nivel": k, "largo_m": L, "ancho_m": L / a_k})
    B = min(levels[-1]["largo_m"], levels[-1]["ancho_m"])

    allo = prior["alometria"]
    log_h = allo["log10_a"] + allo["b"] * math.log10(B) + tau * allo["sigma_resid_log10"] * rng.normal()
    H = 10 ** log_h
    esb_lo, esb_hi = c["esbeltez_masa_principal"]["min"] * 0.8, c["esbeltez_masa_principal"]["max"] * 1.2
    if not esb_lo <= H / B <= esb_hi:
        H_new = min(max(H / B, esb_lo), esb_hi) * B
        traza.append(f"R2: esbeltez {H / B:.2f} proyectada a {H_new / B:.2f}")
        H = H_new

    sym = prior["simetria_por_sitio"][dominant]
    tip = prior["categoricas"]["tipologia"]["por_sitio"][dominant]
    patron = prior["categoricas"]["patron_compositivo"]["por_sitio"][dominant]
    if azimut is None:
        azimut = prior["orientacion_por_sitio"][dominant]
        traza.append(f"Orientación heredada del sitio dominante {dominant}: {azimut}°")
    centro = "cupula" if tip == "estupa" else "torre_escalonada"

    # La verificación usa el factor de volumen de la geometría que se exporta,
    # no el del prior (que queda como objetivo de macizo documentado).
    def f_geom(h):
        if centro == "cupula":
            return structural.spherical_cap_factor(B, h)
        return structural.stepped_factor([(1 - (1 - TORRE_RATIO_CIMA) * i / (TORRE_NIVELES - 1), 1)
                                          for i in range(TORRE_NIVELES)])

    mat = materials[material]
    fg = f_geom(H)
    h_max = structural.max_height_for(mat["densidad_kg_m3"], fg, mat["fc_min_MPa"], fs)
    if H > h_max:
        traza.append(f"R1: H={H:.1f} m excede el límite estático {h_max:.1f} m con FS={fs}; se reduce")
        H = h_max
        fg = f_geom(H)
    sigma = structural.base_stress_mpa(mat["densidad_kg_m3"], H, fg)

    return {
        "entrada": {"area_m2": area_m2, "material": material, "mezcla": weights,
                    "factor_seguridad": fs, "temperatura": tau, "semilla": seed},
        "sitio_dominante": dominant,
        "parametros": {
            "relacion_aspecto": aspect,
            "razon_anidamiento_r": r,
            "niveles": levels,
            "fraccion_ocupacion_objetivo": ocup,
            "porosidad_vanos_objetivo": poros,
            "masa_central": {"forma": centro, "base_m": B, "alto_m": H,
                             "factor_volumen": fg, "factor_volumen_prior": f, "esbeltez": H / B},
            "simetria": {"orden": int(sym["orden"]), "reflexion": sym["reflexion"]},
            "patron_compositivo": patron,
            "azimut_frente_deg": azimut,
        },
        "verificacion": {
            "tension_base_MPa": sigma,
            "fc_min_MPa": mat["fc_min_MPa"],
            "factor_seguridad_resultante": structural.safety_factor(mat["fc_min_MPa"], sigma),
            "altura_limite_estatica_m": h_max,
        },
        "trazabilidad": traza,
    }


def design_to_model(design, nombre="Propuesta de co-diseño"):
    p = design["parametros"]
    m = geometry.Model(nombre, "CODISENO", parametros=p)
    for lv in p["niveles"][:-1]:  # el último nivel es la huella de la masa central
        capa = "muro" if lv["nivel"] == 0 else "galeria"
        esp = max(0.6, 0.015 * lv["largo_m"])
        m.marco(f"Nivel {lv['nivel']}", 0, 0, lv["largo_m"], lv["ancho_m"], esp,
                h=3.0 + 1.5 * lv["nivel"], capa=capa)
    mc = p["masa_central"]
    if mc["forma"] == "cupula":
        m.casquete("Masa central (cúpula)", 0, 0, mc["base_m"], mc["alto_m"])
    else:
        m.torre_escalonada("Masa central (torre)", 0, 0, mc["base_m"], mc["alto_m"],
                           niveles=TORRE_NIVELES, ratio_cima=TORRE_RATIO_CIMA)
    n = p["simetria"]["orden"]
    outer = p["niveles"][0]
    for k in range(n):
        ang = math.radians(p["azimut_frente_deg"] + k * 360 / n)
        dx, dy = math.sin(ang), math.cos(ang)
        x = dx * outer["largo_m"] / 2
        y = dy * outer["ancho_m"] / 2
        m.prisma(f"Acceso {k + 1}", x, y, max(4, 0.05 * outer["largo_m"]),
                 max(4, 0.05 * outer["largo_m"]), h=6, capa="puerta")
    ang = math.radians(p["azimut_frente_deg"])
    m.linea(0, 0, math.sin(ang) * outer["largo_m"] * 0.6, math.cos(ang) * outer["ancho_m"] * 0.6)
    return m


def design_features(spec, materials):
    """Features comparables a las de los sitios para un proyecto descrito en JSON."""
    rec = spec["recinto"]
    niveles = spec["niveles_largo_m"]
    k = np.arange(len(niveles))
    slope = np.polyfit(k, np.log(niveles), 1)[0] if len(niveles) > 1 else 0.0
    masa = spec["masa"]
    mat = materials[masa["material"]]
    B = math.sqrt(masa["base_largo_m"] * masa["base_ancho_m"])
    sigma = structural.base_stress_mpa(mat["densidad_kg_m3"], masa["alto_m"], masa["factor_volumen"])
    return {
        "relacion_aspecto_recinto": max(rec["largo_m"], rec["ancho_m"]) / min(rec["largo_m"], rec["ancho_m"]),
        "razon_anidamiento_r": math.exp(slope),
        "niveles_jerarquicos": float(len(niveles)),
        "esbeltez_masa_principal": masa["alto_m"] / B,
        "factor_volumen_masa_principal": masa["factor_volumen"],
        "fraccion_ocupacion": spec["fraccion_ocupacion"],
        "porosidad_vanos": spec["porosidad_vanos"],
        "orden_simetria_rotacional": float(spec["simetria"]["orden"]),
        "simetria_reflexion": 1.0 if spec["simetria"]["reflexion"] else 0.0,
        "tension_base_MPa": sigma,
        "fc_min_MPa": mat["fc_min_MPa"],
    }


def evaluate_design(spec, prior, site_feats, materials, fs=3.0):
    df = design_features(spec, materials)
    space = dict(PRIOR_FEATURES)
    space.update({"orden_simetria_rotacional": "log", "simetria_reflexion": "lineal"})

    def tr(name, v):
        return _fwd(v, space[name])

    mat = {name: np.array([tr(name, s["features"][name]) for s in site_feats])
           for name in AFINIDAD_FEATURES}
    std = {name: (v.std(ddof=1) or 1.0) for name, v in mat.items()}
    dist = {}
    for i, s in enumerate(site_feats):
        d2 = sum(((tr(n, df[n]) - mat[n][i]) / std[n]) ** 2 for n in AFINIDAD_FEATURES)
        dist[s["sitio_id"]] = math.sqrt(d2 / len(AFINIDAD_FEATURES))
    logits = {k: -0.5 * v ** 2 * len(AFINIDAD_FEATURES) for k, v in dist.items()}
    mx = max(logits.values())
    expo = {k: math.exp(v - mx) for k, v in logits.items()}
    tot = sum(expo.values())
    afinidad = {k: v / tot for k, v in expo.items()}

    checks, sugerencias = [], []
    sf = structural.safety_factor(df["fc_min_MPa"], df["tension_base_MPa"])
    checks.append({"id": "R1", "cumple": sf >= fs, "valor": sf, "umbral": fs})
    if sf < fs:
        sugerencias.append(f"R1: reducir la altura o el factor de volumen un {100 * (1 - sf / fs):.0f} %, "
                           "o elegir un material más resistente")
    c = prior["continuas"]
    rules = [("R2", "esbeltez_masa_principal", 0.8, 1.2), ("R3", "razon_anidamiento_r", 1, 1),
             ("R4", "fraccion_ocupacion", 1, 1)]
    for rid, name, lo_k, hi_k in rules:
        lo, hi = c[name]["min"] * lo_k, c[name]["max"] * hi_k
        ok = lo <= df[name] <= hi
        checks.append({"id": rid, "feature": name, "cumple": ok, "valor": df[name], "rango": [lo, hi]})
        if not ok:
            nearest = min(c[name]["por_sitio"].items(), key=lambda kv: abs(kv[1] - df[name]))
            sugerencias.append(f"{rid}: {name}={df[name]:.3f} fuera de [{lo:.3f}, {hi:.3f}]; "
                               f"el referente más próximo es {nearest[0]} ({nearest[1]:.3f})")
    niveles = spec["niveles_largo_m"]
    ok = all(b < a for a, b in zip(niveles, niveles[1:]))
    checks.append({"id": "R5", "cumple": ok})
    if not ok:
        sugerencias.append("R5: la cadena de recintos debe decrecer estrictamente hacia el centro")
    return {"features_proyecto": df, "distancia_estandarizada": dist,
            "afinidad_morfologica": afinidad, "restricciones": checks, "sugerencias": sugerencias}
