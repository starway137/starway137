"""Selección de obras nuevas: ¿comparte la obra las características del corpus?

El corpus de referencia son fábricas de ALTA COMPLEJIDAD: bóvedas de
crucería y estrelladas, nervadas y de mocárabes. Lo que las distingue de una
fábrica corriente se mide sobre la geometría pura (sin etiquetas):

    simetria      orden de simetría rotacional de la planta (n >= 3)
    curvatura     doble curvatura de la superficie media: cuádrica ajustada a
                  los centroides en el marco principal; razón |k_min|/|k_max|
                  (0 cilindro o plano, 1 esfera) y curvatura relativa |k_max|·L
    juntas        entropía normalizada de la orientación de los contactos en
                  la semiesfera (estereotomía: juntas de orientación variable,
                  sea por inclinación —dovelas— o por acimut —mocárabes—)
    formas        entropía normalizada de las clases de forma de las piezas
                  (despiece no repetitivo: cada hilada es distinta)
    escala        número de piezas

Una obra se SELECCIONA si cumple todas las condiciones mínimas y su índice
de complejidad supera el umbral calibrado con las referencias (fracción
`margen` del mínimo de las referencias). La afinidad con cada referencia se
mide después, sobre el genoma inferido, en el espacio latente normalizado.
"""

import numpy as np

from . import latente
from .interpretacion import marco

MINIMOS = {"simetria": 3, "curvatura_razon": 0.3, "curvatura_rel": 0.5, "entropia_juntas": 0.45,
           "entropia_formas": 0.3, "piezas": 60}
PESOS = {"curvatura": 0.3, "entropia_juntas": 0.3, "entropia_formas": 0.3, "simetria": 0.1}


def _entropia(cuentas, normal):
    p = np.asarray([c for c in cuentas if c > 0], float)
    if len(p) < 2 or normal <= 1:
        return 0.0
    p /= p.sum()
    return float(-(p * np.log(p)).sum() / np.log(normal))


def curvatura(C):
    """Cuádrica w = au² + buv + cv² + du + ev + f ajustada a los centroides.

    w es la vertical (los levantamientos están nivelados) salvo que la planta
    sea degenerada (un muro, un arco): entonces w es el eje de menor varianza."""
    X = C - C.mean(axis=0)
    sv = np.linalg.svd(X[:, :2], compute_uv=False)        # planta degenerada: invariante al giro
    if sv[1] > 0.2 * sv[0]:
        marcos = [np.eye(3)]
    else:                                              # w: dirección de menor varianza
        _, _, Vt = np.linalg.svd(X, full_matrices=False)
        marcos = [Vt]
    mejor = None
    for M in marcos:
        P = X @ M.T
        u, v, w = P[:, 0], P[:, 1], P[:, 2]
        L = float(max(np.ptp(u), np.ptp(v)))
        A = np.column_stack([u * u, u * v, v * v, u, v, np.ones_like(u)])
        coef, *_ = np.linalg.lstsq(A, w, rcond=None)
        res = float(np.sqrt(np.mean((A @ coef - w) ** 2)) / L)
        if mejor is None or res < mejor[0]:
            mejor = (res, coef, L)
    res, coef, L = mejor
    a, b, c = coef[:3]
    k = np.linalg.eigvalsh(np.array([[2 * a, b], [b, 2 * c]]))
    kmax, kmin = np.max(np.abs(k)), np.min(np.abs(k))
    return {"razon": float(kmin / kmax) if kmax > 1e-12 else 0.0, "relativa": float(kmax * L),
            "residuo_rel": res}


def entropia_orientaciones(grafo):
    """Entropía de las normales de contacto en la semiesfera, ponderada por
    área: una celda para los lechos (inclinación < 15°, acimut indefinido) y
    5 bandas de 15° x 12 sectores de acimut módulo 180°; normalizada por log(61)."""
    lechos, H = 0.0, np.zeros((5, 12))
    for d in grafo.aristas.values():
        if "normal" not in d:
            continue
        nx, ny, nz = d["normal"]
        inc = np.degrees(np.arccos(min(1.0, abs(nz))))
        a = d.get("area_m2", 1.0)
        if inc < 15:
            lechos += a
        else:
            az = np.degrees(np.arctan2(ny, nx)) % 180
            H[min(int(inc // 15) - 1, 4), min(int(az // 15), 11)] += a
    return _entropia(np.concatenate([[lechos], H.ravel()]), 1 + H.size)


def clases_forma(grafo, tol=0.04):
    """Agrupa piezas congruentes (volumen y extensiones dentro de `tol` relativo)."""
    firmas = sorted((np.log(grafo.nodos[n]["volumen_m3"]), *np.log(np.sort(grafo.nodos[n]["extensiones_m"])))
                    for n in grafo.piezas())
    clases = []
    for f in firmas:
        f = np.array(f)
        for c in clases:
            if np.all(np.abs(c[0] - f) < tol):
                c[1] += 1
                break
        else:
            clases.append([f, 1])
    return [c[1] for c in clases]


def indices(grafo, mc=None):
    mc = mc or marco(grafo)
    C = np.array([grafo.nodos[n]["centroide"] for n in grafo.piezas()])
    cur = curvatura(C)
    inc = [d["inclinacion_deg"] for d in grafo.aristas.values() if "inclinacion_deg" in d]
    h_i = _entropia(np.histogram(inc, bins=9, range=(0, 90))[0], 9)
    h_j = entropia_orientaciones(grafo)
    formas = clases_forma(grafo)
    h_f = _entropia(formas, len(C))
    return {"piezas": len(C), "simetria": int(mc["n"]), "curvatura_razon": cur["razon"],
            "curvatura_rel": cur["relativa"], "entropia_juntas": h_j, "entropia_inclinacion": h_i, "entropia_formas": h_f,
            "clases_forma": len(formas), "contactos": len(inc)}


def complejidad(ind):
    c = min(1.0, ind["curvatura_razon"]) * min(1.0, ind["curvatura_rel"] / 2)
    s = min(1.0, ind["simetria"] / 8) if ind["simetria"] >= 3 else 0.0
    return float(PESOS["curvatura"] * c + PESOS["entropia_juntas"] * ind["entropia_juntas"]
                 + PESOS["entropia_formas"] * ind["entropia_formas"] + PESOS["simetria"] * s)


class Selector:
    def __init__(self, margen=0.8):
        self.margen = margen
        self.referencias = {}          # id -> {"indices", "complejidad", "genoma", "tradicion"}
        self.umbral = None

    def calibrar(self, refs):
        """refs: {id: (grafo_ciego, genoma, tradicion)}"""
        for rid, (g, gen, trad) in refs.items():
            ind = indices(g)
            self.referencias[rid] = {"indices": ind, "complejidad": complejidad(ind), "genoma": gen,
                                     "tradicion": trad}
        self.umbral = self.margen * min(r["complejidad"] for r in self.referencias.values())
        return self.umbral

    def evaluar(self, grafo, mc=None):
        ind = indices(grafo, mc)
        cx = complejidad(ind)
        fallos = [k for k, m in MINIMOS.items() if ind[k] < m]
        return {"indices": ind, "complejidad": cx, "umbral": self.umbral, "condiciones_fallidas": fallos,
                "seleccionada": not fallos and cx >= self.umbral}

    def afinidad(self, genoma, holgura=0.05):
        """Distancias latentes a cada referencia y novedad por genes: un gen es
        nuevo si su valor queda fuera del rango del corpus (holgura en el espacio
        normalizado [-1, 1]) o, si es discreto (orden, estrella, terceletes), si
        ese valor no aparece en ninguna referencia."""
        d = {rid: latente.distancia(genoma, r["genoma"]) for rid, r in self.referencias.items()}
        cercana = min(d, key=d.get)
        z = latente.codificar(genoma)
        Z = np.array([latente.codificar(r["genoma"]) for r in self.referencias.values()])
        nuevos = []
        for i, nombre in enumerate(latente.NOMBRES):
            if nombre in ("orden_radial", "terceletes"):
                vistos = {round(r["genoma"][nombre]) for r in self.referencias.values()}
                if round(genoma[nombre]) not in vistos:
                    nuevos.append(nombre)
            elif nombre == "salto_estrella_rel":
                k = round(genoma[nombre] * genoma["orden_radial"])
                vistos = {(round(r["genoma"]["orden_radial"]), round(r["genoma"][nombre] * r["genoma"]["orden_radial"]))
                          for r in self.referencias.values()}
                if (round(genoma["orden_radial"]), k) not in vistos:
                    nuevos.append("estrella_{n/k}")
            elif not (Z[:, i].min() - holgura <= z[i] <= Z[:, i].max() + holgura):
                nuevos.append(nombre)
        return {"distancias": d, "mas_cercana": cercana, "tradicion_cercana": self.referencias[cercana]["tradicion"],
                "distancia_min": d[cercana], "genes_nuevos": nuevos, "novedad": bool(nuevos)}

    def incorporar(self, rid, grafo, genoma, tradicion):
        """Autoampliación: una obra verificada pasa a ser referencia (el umbral no baja)."""
        ind = indices(grafo)
        self.referencias[rid] = {"indices": ind, "complejidad": complejidad(ind), "genoma": genoma,
                                 "tradicion": tradicion}
