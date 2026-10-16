"""Interpretación de una obra ingerida sin semántica.

A partir de solo mallas y contactos:
  1. Marco de referencia: centro, base, radio de planta, orden de simetría
     rotacional y orientación del polígono.
  2. Tipo de cada pieza con el diccionario aprendido (prototipo más cercano
     sobre descriptores puramente geométricos).
  3. Genoma por ingeniería inversa: superficie (apuntamiento, β), espesor,
     regla de juntas, zona de mocárabes, polígono estrellado de nervios,
     terceletes, canto y despiece.
El genoma inferido regenera la obra con la gramática y se verifica de nuevo:
si el veredicto estructural coincide con el de la obra original, la
interpretación conserva la información necesaria.
"""

from collections import Counter

import numpy as np

from .memoria import DiccionarioPatrones
from .superficie import SuperficiePoligonal

NOMBRES_GEO = ["log10_vol_rel", "log10_alargamiento", "log10_aplanamiento", "altura_rel", "radio_rel",
               "grado", "frac_lecho", "frac_inclinada", "frac_vertical", "n_caras", "area_contacto_rel"]
ESCALAS_GEO = [0.35, 0.2, 0.2, 0.2, 0.15, 0.25, 0.3, 0.3, 0.3, 0.2, 0.3]
CASCARA = ("plemento", "celda_mocarabe")


# ------------------------------------------------------------------ marco
def _cruz(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _rot(P2, ang):
    c, s = np.cos(ang), np.sin(ang)
    return P2 @ np.array([[c, s], [-s, c]])


def simetria_rotacional(P2, L, candidatos=(12, 10, 8, 6, 4, 3, 2), tol=0.006):
    """Mayor orden n tal que la nube de centroides es invariante al giro 2π/n."""
    residuos = {}
    for n in candidatos:
        R = _rot(P2, -2 * np.pi / n)
        d = np.sqrt(((R[:, None, :] - P2[None, :, :]) ** 2).sum(-1)).min(axis=1)
        residuos[n] = float(np.median(d) / L)
    validos = [n for n in candidatos if residuos[n] < tol]
    return (max(validos) if validos else 1), residuos


def marco(grafo):
    V = np.vstack([g.V for g in grafo.geometrias.values()])
    C = np.array([grafo.nodos[n]["centroide"] for n in grafo.piezas()])
    centro = 0.5 * (V[:, :2].min(axis=0) + V[:, :2].max(axis=0))
    P2 = C[:, :2] - centro
    r_v = np.linalg.norm(V[:, :2] - centro, axis=1)
    Rmax = float(np.quantile(r_v, 0.998))
    n, residuos = simetria_rotacional(P2, 2 * Rmax)
    return {"centro": centro, "z0": float(V[:, 2].min()), "H": float(np.ptp(V[:, 2])), "Rmax": Rmax,
            "L": 2 * Rmax, "n": n, "residuos_simetria": residuos}


# ------------------------------------------------------------------ descriptores y clasificación
def descriptores(grafo, mc=None):
    mc = mc or marco(grafo)
    ady = grafo.lista_adyacencia()
    items = []
    for nid in grafo.piezas():
        d = grafo.nodos[nid]
        geo = grafo.geometrias[nid]
        ext = np.maximum(np.array(d["extensiones_m"], float), 1e-6)
        sup_total = sum(geo.area_normal(i)[0] for i in range(len(geo.F)))
        incl, area_c = [], 0.0
        for v, _ in ady[nid]:
            a = grafo.aristas[(nid, v) if nid < v else (v, nid)]
            if "inclinacion_deg" in a:
                incl.append(a["inclinacion_deg"])
                area_c += a.get("area_m2", 0.0)
        incl = np.array(incl)
        k = max(len(incl), 1)
        c = np.array(d["centroide"])
        vec = [np.log10(d["volumen_m3"] / mc["L"] ** 3), np.log10(ext[0] / ext[1]), np.log10(ext[1] / ext[2]),
               (c[2] - mc["z0"]) / max(mc["H"], 1e-6), np.linalg.norm(c[:2] - mc["centro"]) / mc["Rmax"],
               len(ady[nid]) / 8.0, float((incl < 25).sum()) / k, float(((incl >= 25) & (incl < 65)).sum()) / k,
               float((incl >= 65).sum()) / k, len(geo.F) / 12.0, area_c / max(sup_total, 1e-9)]
        items.append((nid, np.round(np.array(vec, float), 6)))
    return items


class Clasificador:
    """Clasificador de tipos de pieza con aprendizaje continuo (memoria episódica).

    Detección de novedad: una pieza cuyo prototipo más cercano está a más de
    `novedad` x umbral se etiqueta "desconocido" en lugar de forzar un tipo;
    la interpretación la ignora y el informe la cuenta."""

    def __init__(self, umbral=0.8, novedad=3.0):
        self.dicc = DiccionarioPatrones(umbral=umbral, k_memoria=8, escalas=ESCALAS_GEO)
        self.umbral_novedad = novedad * umbral

    def aprender(self, obra_id, tradicion, items, etiquetas):
        return self.dicc.ingerir(obra_id, tradicion, [(n, etiquetas[n], "", v) for n, v in items
                                                      if etiquetas.get(n, "desconocido") != "desconocido"])

    def predecir(self, items, con_distancia=False):
        out, dist = {}, {}
        for n, v in items:
            p, d = self.dicc.clasificar_libre(v)
            out[n] = p["tipo"] if p and d <= self.umbral_novedad else "desconocido"
            dist[n] = float(d)
        return (out, dist) if con_distancia else out


# ------------------------------------------------------------------ genoma inverso
def _canonico(grafo, mc, n):
    """Ángulo que lleva la normal de un lado al eje x (orientación de la gramática)."""
    V = np.vstack([g.V for g in grafo.geometrias.values()])
    P = V[:, :2] - mc["centro"]
    r = np.linalg.norm(P, axis=1)
    esquinas = P[r > 0.985 * mc["Rmax"]]
    ang = np.arctan2(esquinas[:, 1], esquinas[:, 0])
    paso = 2 * np.pi / n
    m = np.angle(np.mean(np.exp(1j * (ang % paso) * n))) / n % paso        # media circular de vértices
    return m - np.pi / n


def inferir_genoma(grafo, tipos, mc=None):
    mc = mc or marco(grafo)
    n = mc["n"]
    if n < 3:
        return None, {"motivo": "sin simetría rotacional de orden >= 3"}
    giro = _canonico(grafo, mc, n)

    def canon(P):
        P = np.atleast_2d(P)
        return _rot(P[:, :2] - mc["centro"], -giro)

    por_tipo = {}
    for nid, t in tipos.items():
        por_tipo.setdefault(t, []).append(nid)
    cascara = [nid for t in CASCARA for nid in por_tipo.get(t, [])]
    if not cascara:
        return None, {"motivo": "sin piezas de cáscara reconocidas"}
    Vs = [(canon(grafo.geometrias[nid].V), grafo.geometrias[nid].V[:, 2]) for nid in cascara]
    z_base = min(z.min() for _, z in Vs)

    XY = np.vstack([P for P, _ in Vs]) * 0.999
    Zr = np.concatenate([z for _, z in Vs]) - z_base
    inicio = np.cumsum([0] + [len(z) for _, z in Vs[:-1]])

    def ajuste(ps, betas, Rs):
        mejor = (np.inf, None)
        for R_ in Rs:
            for p_ in ps:
                for b_ in betas:
                    s_ = SuperficiePoligonal(n, R_, float(np.clip(p_, 0, 1)), float(np.clip(b_, 0, 1)))
                    m = np.minimum.reduceat(Zr - s_.z(XY[:, 0], XY[:, 1]), inicio)   # envolvente inferior por pieza
                    # error recortado (90 % menor): robusto a piezas mal clasificadas como cáscara
                    m2 = np.sort(np.square(m))
                    err = float(np.sqrt(np.mean(m2[:max(1, int(0.9 * len(m2)))])))
                    if err < mejor[0]:
                        mejor = (err, (float(np.clip(p_, 0, 1)), float(np.clip(b_, 0, 1)), R_))
        return mejor
    Rmax = mc["Rmax"]
    rms, (p, beta, R) = ajuste(np.linspace(0, 1, 11), np.linspace(0, 1, 11), Rmax * np.array([0.86, 0.9, 0.94, 0.97, 1.0]))
    rms, (p, beta, R) = ajuste(p + np.linspace(-0.1, 0.1, 9), beta + np.linspace(-0.1, 0.1, 9),
                               R * np.array([0.985, 0.995, 1.0, 1.005, 1.015]))
    A = R * np.cos(np.pi / n)
    sup = SuperficiePoligonal(n, R, p, beta)

    plem = por_tipo.get("plemento", [])
    celdas = por_tipo.get("celda_mocarabe", [])
    ext = lambda ids, i: np.array([grafo.nodos[x]["extensiones_m"][i] for x in ids])  # noqa: E731
    moc = len(celdas) > len(plem)                         # tipo de cáscara dominante
    if not moc:                                          # volumen / área media de intradós y trasdós
        esp = []
        for x in plem:
            g = grafo.geometrias[x]
            areas = sorted((g.area_normal(i)[0] for i in range(len(g.F))), reverse=True)
            esp.append(grafo.nodos[x]["volumen_m3"] / max(0.5 * (areas[0] + areas[1]), 1e-9))
        t = float(np.median(esp))
    else:
        # celdas: el trasdós es el intradós desplazado en horizontal t_m / max(N_h, 0.25)
        # (N_h: componente radial de la normal); t_m = 1.5 t
        esp = []
        for x in celdas:
            g = grafo.geometrias[x]
            for i in range(len(g.F)):
                _, nrm = g.area_normal(i)
                if abs(nrm[2]) > 0.95:
                    P = canon(g.cara(i))
                    r = np.linalg.norm(P, axis=1)
                    c = P.mean(axis=0)
                    rh = c / max(np.linalg.norm(c), 1e-9)
                    ancho = np.ptp(P @ rh)
                    pi = P[np.argmin(r)] * 0.999
                    N = sup.normal(pi[0], pi[1])
                    esp.append(ancho * np.clip(np.dot(np.ravel(N)[:2], rh), 0.25, 1.0))
        t = float(np.median(esp)) / 1.5

    # regla de juntas: ángulo de las juntas de lecho entre plementos frente al de la superficie
    j_obs = []
    if plem:
        conj = set(plem)
        for (a, b), d in grafo.aristas.items():
            if a not in conj or b not in conj or "normal" not in d:
                continue
            c2 = canon(np.array(d["centro"]))[0]
            r = np.linalg.norm(c2)
            if r < 1e-6:
                continue
            rh = c2 / r
            nrm = np.array(d["normal"])
            nrm_c = np.array([*_rot(nrm[None, :2], -giro)[0], nrm[2]])
            nh, nz = abs(np.dot(nrm_c[:2], rh)), abs(nrm_c[2])
            if np.linalg.norm(nrm_c[:2] - np.dot(nrm_c[:2], rh) * rh) > 0.5:
                continue                                  # junta lateral (tangencial)
            N = sup.normal(c2[0] * 0.999, c2[1] * 0.999)
            Nh, Nz = float(np.dot(N[:2], rh)), float(N[2])
            delta_obs = np.arctan2(nh, nz)
            js = np.linspace(0, 1, 101)
            delta = np.arctan2(js * Nz, (1 - js) + js * Nh)
            j_obs.append(js[int(np.argmin(np.abs(delta - delta_obs)))])
    j = float(np.median(j_obs)) if j_obs else 0.0

    mu = 0.0
    if celdas:
        # la zona de mocárabes es contigua de q_m al perímetro: q_m es el umbral que mejor separa
        # celdas (q >= q_m) de plementos (q < q_m), robusto a unas pocas piezas mal clasificadas
        filas = []
        for x in plem + celdas:
            P = canon(grafo.geometrias[x].V)
            filas.append((float(sup.locales(P[:, 0], P[:, 1])[1].min()), x in set(celdas)))
        filas.sort()
        es_celda = np.array([c for _, c in filas])
        errores = [int((~es_celda[i:]).sum() + es_celda[:i].sum()) for i in range(len(filas) + 1)]
        i = int(np.argmin(errores))
        q_m = filas[i][0] if i < len(filas) else A
        mu = float(np.clip(1 - q_m / A, 0, 0.9))

    # nervios: familias por distancia de su directriz al centro
    nervios = por_tipo.get("dovela_nervio", [])
    k, terc, canto = 0, 0, 0.0
    familias = Counter()
    if nervios:
        for x in nervios:
            g = grafo.geometrias[x]
            c2 = canon(g.V.mean(axis=0))[0]
            _, ejes = g.caja_orientada()
            u = _rot(ejes[0][None, :2], -giro)[0]
            if np.linalg.norm(u) < 1e-6:
                continue
            u /= np.linalg.norm(u)
            pie = c2 - np.dot(c2, u) * u                    # pie de la perpendicular desde el centro
            dist = np.linalg.norm(pie) / R
            if dist < 0.06:                                  # pasa por el centro: diagonal o ligadura
                ang = np.arctan2(u[1], u[0]) % (2 * np.pi / n)
                fam = f"k{n // 2}" if abs(ang - np.pi / n) < np.pi / (2 * n) else "ligadura"
            else:
                ang_pie = np.arctan2(pie[1], pie[0]) % (np.pi / n)
                desv = min(ang_pie, np.pi / n - ang_pie)
                # cuerda {n/k}: pie de la perpendicular sobre un eje de simetría y a distancia cos(πk/n)·R
                kk = min(range(1, n // 2 + 1), key=lambda k_: abs(np.cos(np.pi * k_ / n) - dist))
                if desv < np.radians(3) and abs(np.cos(np.pi * kk / n) - dist) < 0.025:
                    fam = "formero" if kk == 1 else f"k{kk}"
                else:
                    fam = "tercelete"
            familias[fam] += 1
        total = sum(familias.values())
        estrellas = {f: c for f, c in familias.items() if f.startswith("k") and f != "formero"}
        if estrellas:
            f_max = max(estrellas, key=estrellas.get)
            if estrellas[f_max] / total >= 0.1:
                k = int(f_max[1:])
        terc = int((familias["tercelete"] + familias["ligadura"]) / total >= 0.15)
        canto = float(np.median(ext(nervios, 1)))

    ref = celdas if moc else plem
    dq = []
    for x in ref:
        P = canon(grafo.geometrias[x].V)
        q = sup.locales(P[:, 0], P[:, 1])[1]
        dq.append(np.ptp(q))
    paso = float(np.median(dq))                          # sobrestima la hilada (incluye el trasdós)
    # niveles de hilada: el q mínimo de cada pieza es su lecho inferior de intradós (el trasdós
    # siempre queda hacia fuera), de modo que las piezas de una hilada comparten ese valor
    qc = []
    for x in ref:
        P = canon(grafo.geometrias[x].V)
        qc.append(float(sup.locales(P[:, 0], P[:, 1])[1].min()))
    qc = np.sort(qc)
    cortes = np.where(np.diff(qc) > max(0.004 * A, 0.1 * paso))[0]
    niveles = [g_.mean() for g_ in np.split(qc, cortes + 1)]
    if len(niveles) >= 3:
        paso = float((niveles[-1] - niveles[0]) / (len(niveles) - 1))
    K = A / (1.5 * paso) if moc else A / paso
    luz = 2 * A
    genoma = {"orden_radial": float(n), "salto_estrella_rel": k / n, "terceletes": float(terc),
              "apuntamiento": float(p), "beta_superficie": float(beta), "espesor_rel": t / luz,
              "mocarabe_rel": mu, "inclinacion_junta": j, "despiece": float(int(np.clip(round(K), 6, 14))),
              "canto_nervio_rel": canto / luz}
    diag = {"luz_m": luz, "R_m": R, "giro_rad": float(giro), "z_base": float(z_base), "espesor_m": t, "rms_superficie_m": rms, "familias_nervios": dict(familias),
            "juntas_medidas": len(j_obs), "n_simetria": n}
    return genoma, diag


def corregir_por_superficie(grafo, tipos, genoma, diag, mc=None, umbral=0.1):
    """Corrección física nervio/plemento: los nervios cuelgan bajo el intradós y
    los plementos quedan sobre él. Se mide la distancia vertical del centroide a
    la superficie ajustada, en espesores de cáscara, se separan las piezas en dos
    grupos (umbral de Otsu, invariante a un sesgo del ajuste) y se reasigna el
    tipo cuando contradice el grupo; si los grupos no están claramente separados
    no se corrige nada. No usa la verdad."""
    mc = mc or marco(grafo)
    n = int(round(genoma["orden_radial"]))
    sup = SuperficiePoligonal(n, diag["R_m"], genoma["apuntamiento"], genoma["beta_superficie"])
    nuevos, cambios = dict(tipos), 0
    # coherencia de conjunto: los mocárabes forman anillos completos; unas pocas celdas sueltas son plementos
    celdas = [k for k, t in tipos.items() if t == "celda_mocarabe"]
    cascara = sum(t in CASCARA for t in tipos.values())
    if celdas and len(celdas) < max(2 * n, 0.1 * cascara):
        for k in celdas:
            nuevos[k] = "plemento"
        cambios += len(celdas)
    ids, rel = [], []
    for nid, t in nuevos.items():
        if t not in ("plemento", "dovela_nervio"):
            continue
        c = np.array(grafo.nodos[nid]["centroide"])
        P = _rot((c[:2] - mc["centro"])[None, :], -diag["giro_rad"]) * 0.999
        ids.append(nid)
        rel.append((c[2] - diag["z_base"] - float(sup.z(P[:, 0], P[:, 1])[0])) / max(diag["espesor_m"], 1e-6))
    rel = np.array(rel)
    if genoma["salto_estrella_rel"] > 0 and len(rel) > 10:
        # dos grupos en altura relativa (umbral de Otsu): invariante a un sesgo del ajuste de superficie
        orden = np.sort(rel)
        mejor = (-1.0, None)
        for i in range(5, len(orden) - 5):
            a_, b_ = orden[:i], orden[i:]
            var = len(a_) * len(b_) * (a_.mean() - b_.mean()) ** 2
            if var > mejor[0]:
                mejor = (var, 0.5 * (orden[i - 1] + orden[i]), a_.mean(), b_.mean())
        _, corte, m_bajo, m_alto = mejor
        if m_alto - m_bajo > 0.6:                         # separación clara (≈ canto/2 + t/2 en las referencias)
            for nid, r in zip(ids, rel):
                t = "dovela_nervio" if r < corte else "plemento"
                if t != nuevos[nid] and abs(r - corte) > umbral:
                    nuevos[nid], cambios = t, cambios + 1
    return nuevos, cambios


def errores_genoma(inferido, verdad):
    e = {}
    for k in ("orden_radial", "terceletes"):
        e[k] = int(round(inferido[k]) == round(verdad[k]))
    e["salto_estrella"] = int(round(inferido["salto_estrella_rel"] * inferido["orden_radial"])
                              == round(verdad["salto_estrella_rel"] * verdad["orden_radial"]))
    for k in ("apuntamiento", "beta_superficie", "inclinacion_junta", "mocarabe_rel"):
        e[f"d_{k}"] = abs(inferido[k] - verdad[k])
    e["err_rel_espesor"] = abs(inferido["espesor_rel"] - verdad["espesor_rel"]) / verdad["espesor_rel"]
    e["err_rel_canto"] = (abs(inferido["canto_nervio_rel"] - verdad["canto_nervio_rel"]) / verdad["canto_nervio_rel"]
                          if verdad["canto_nervio_rel"] > 0 else float(inferido["canto_nervio_rel"] > 0))
    e["d_despiece"] = abs(inferido["despiece"] - verdad["despiece"])
    return e
