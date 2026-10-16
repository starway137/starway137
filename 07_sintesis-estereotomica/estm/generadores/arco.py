"""Arco de dovelas: estereotomía clásica con juntas de inclinación variable.

inclinacion_junta j:  1 -> juntas normales al intradós (dovelas, regla de la
                      estereotomía);  0 -> juntas horizontales (aproximación
                      por hiladas voladas, como en arcos falsos o mocárabes).
La sección resultante alimenta tanto el grafo como el análisis de Heyman.
"""

import numpy as np

from .. import materiales
from ..geometria import centroide_poligono_2d, prisma_extruido
from ..grafo import GrafoAtribuido
from ..superficie import centro_radio
from .obra import Obra

G = 9.81


def _interseca_circulo(a, d, C, r):
    w = a - C
    B = 2 * np.dot(w, d)
    Cc = np.dot(w, w) - r * r
    disc = B * B - 4 * Cc
    return a + d * (-B + np.sqrt(max(disc, 0.0))) / 2


def semiarco(semiluz, p, t, n, j, muestras=6):
    """Juntas y polígonos de las dovelas del semiarco derecho (x >= 0).

    Devuelve (juntas (n+1, 2, 2), poligonos[n]) ordenados desde la clave.
    """
    c, R = centro_radio(semiluz, p)
    C = np.array([-c, 0.0])
    Re = R + t
    phic = np.arccos(c / R)
    phis = np.linspace(phic, 0.0, n + 1)
    juntas = []
    for i, ph in enumerate(phis):
        a = C + R * np.array([np.cos(ph), np.sin(ph)])
        if i == 0:
            b = np.array([0.0, np.sqrt(Re ** 2 - c ** 2)])
        else:
            ur = np.array([np.cos(ph), np.sin(ph)])
            d = (1 - j) * np.array([1.0, 0.0]) + j * ur
            b = _interseca_circulo(a, d / np.linalg.norm(d), C, Re)
        juntas.append((a, b))
    juntas = np.array(juntas)
    poligonos = []
    for i in range(n):
        ai, bi = juntas[i]
        aj, bj = juntas[i + 1]
        ang_int = np.linspace(phis[i], phis[i + 1], muestras + 1)[1:-1]
        ang_bi = np.arctan2(*(bi - C)[::-1])
        ang_bj = np.arctan2(*(bj - C)[::-1])
        ang_ext = np.linspace(ang_bj, ang_bi, muestras + 1)[1:-1]
        intr = [C + R * np.array([np.cos(a), np.sin(a)]) for a in ang_int]
        extr = [C + Re * np.array([np.cos(a), np.sin(a)]) for a in ang_ext]
        poligonos.append(np.array([ai, *intr, aj, bj, *extr, bi]))
    return juntas, poligonos


def seccion_arco(semiluz, p, n, j, profundidad, densidad, muestras=6):
    """Constructor t -> (juntas, piezas) para espesor_minimo / linea_empujes."""
    def constructor(t):
        juntas, polis = semiarco(semiluz, p, t, n, j, muestras)
        piezas = []
        for P in polis:
            cen, A = centroide_poligono_2d(P)
            piezas.append((abs(A) * profundidad * densidad * G, cen[0], cen[1]))
        return juntas, np.array(piezas)
    return constructor


def arco_dovelas(id_, nombre, tradicion, luz, apuntamiento, espesor, dovelas_semiarco,
                 inclinacion_junta=1.0, profundidad=0.6, material="caliza", meta=None):
    a = luz / 2
    rho = materiales.densidad(material)
    juntas, polis = semiarco(a, apuntamiento, espesor, dovelas_semiarco, inclinacion_junta)
    g = GrafoAtribuido(nombre, id=id_, tradicion=tradicion, tipologia="arco",
                       material=material, luz_m=luz)
    y0, y1 = -profundidad / 2, profundidad / 2

    def espejo(P):
        return np.column_stack([-P[:, 0], P[:, 1]])[::-1]

    # La clave une las dos mitades de la primera dovela (una sola pieza en el eje)
    der = polis[0]
    izq = espejo(der)
    k_int = np.where(np.isclose(der[:, 0], 0.0) & np.isclose(der[:, 1], juntas[0][0][1]))[0][0]
    k_ext = np.where(np.isclose(der[:, 0], 0.0) & np.isclose(der[:, 1], juntas[0][1][1]))[0][0]
    # der: a0 ... a1 b1 ... b0 ; izq (espejo invertido): b0' ... b1' a1' ... a0'
    clave = np.vstack([der[k_int:k_ext + 1], izq[1:-1]])
    g.add_nodo("clave", "clave", prisma_extruido(clave, y0, y1), densidad=rho, hilada=0,
               inclinacion_junta_deg=0.0)
    lado_ids = {"D": ["clave"], "I": ["clave"]}
    for i in range(1, dovelas_semiarco):
        for lado, P in (("D", polis[i]), ("I", espejo(polis[i]))):
            nid = f"dovela_{lado}{i:02d}"
            aj, bj = juntas[i]
            inc = float(np.degrees(np.arctan2(abs(bj[1] - aj[1]), abs(bj[0] - aj[0]))))
            g.add_nodo(nid, "dovela", prisma_extruido(P, y0, y1), densidad=rho, hilada=i,
                       lado=lado, inclinacion_junta_deg=inc)
            prev = lado_ids[lado][-1]
            tipo = "junta_radial" if inclinacion_junta >= 0.5 else "lecho"
            g.add_arista(prev, nid, tipo)
            lado_ids[lado].append(nid)
    for lado in ("D", "I"):
        g.add_nodo(f"apoyo_{lado}", "apoyo")
        g.add_arista(lado_ids[lado][-1], f"apoyo_{lado}", "apoyo", calcular_contacto=False)

    genoma = {"orden_radial": 2, "salto_estrella_rel": 0.0, "terceletes": 0,
              "apuntamiento": apuntamiento, "beta_superficie": 0.0,
              "espesor_rel": espesor / luz, "mocarabe_rel": 0.0,
              "inclinacion_junta": inclinacion_junta, "despiece": dovelas_semiarco,
              "canto_nervio_rel": 0.0}
    obra = Obra(id_, nombre, tradicion, genoma, g, meta or {},
                seccion=seccion_arco(a, apuntamiento, dovelas_semiarco, inclinacion_junta,
                                     profundidad, rho),
                espesor=espesor)
    obra.meta.setdefault("radio_medio_m", centro_radio(a, apuntamiento)[1] + espesor / 2)
    return obra
