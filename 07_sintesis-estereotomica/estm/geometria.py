"""Poliedros de pieza: volumen, centroide, caras, contacto y caja orientada.

Convenciones: metros, eje z vertical. Las caras se guardan como listas de
índices de vértices orientadas hacia fuera (se corrige al construir).
"""

import numpy as np


class Poliedro:
    def __init__(self, V, F):
        self.V = np.asarray(V, dtype=float)
        self.F = [list(f) for f in F]
        if self._volumen_signado() < 0:
            self.F = [f[::-1] for f in self.F]

    # ------------------------------------------------------------ magnitudes
    def _volumen_signado(self):
        c0 = self.V.mean(axis=0)
        vol = 0.0
        for f in self.F:
            p0 = self.V[f[0]] - c0
            for a, b in zip(f[1:-1], f[2:]):
                vol += np.dot(p0, np.cross(self.V[a] - c0, self.V[b] - c0)) / 6
        return vol

    def volumen_centroide(self):
        c0 = self.V.mean(axis=0)
        vol, cen = 0.0, np.zeros(3)
        for f in self.F:
            p0 = self.V[f[0]]
            for a, b in zip(f[1:-1], f[2:]):
                p1, p2 = self.V[a], self.V[b]
                v = np.dot(p0 - c0, np.cross(p1 - c0, p2 - c0)) / 6
                vol += v
                cen += v * (p0 + p1 + p2 + c0) / 4
        return vol, cen / vol if vol else c0

    def cara(self, i):
        return self.V[self.F[i]]

    def area_normal(self, i):
        """Área y normal unitaria exterior por el método de Newell."""
        P = self.cara(i)
        n = np.zeros(3)
        for a, b in zip(P, np.roll(P, -1, axis=0)):
            n += np.cross(a, b)
        area = np.linalg.norm(n) / 2
        return area, (n / (2 * area) if area > 0 else n)

    def centro_cara(self, i):
        return self.cara(i).mean(axis=0)

    def planaridad(self, i):
        """Desviación máxima (m) de los vértices de la cara a su plano medio."""
        P = self.cara(i)
        if len(P) <= 3:
            return 0.0
        Q = P - P.mean(axis=0)
        normal = np.linalg.svd(Q)[2][-1]
        return float(np.abs(Q @ normal).max())

    def caja_orientada(self):
        """Extensiones (ordenadas de mayor a menor) en los ejes principales (PCA)."""
        Q = self.V - self.V.mean(axis=0)
        ejes = np.linalg.svd(Q, full_matrices=False)[2]
        proy = Q @ ejes.T
        ext = proy.max(axis=0) - proy.min(axis=0)
        orden = np.argsort(ext)[::-1]
        return ext[orden], ejes[orden]

    def caja_alineada(self):
        return self.V.min(axis=0), self.V.max(axis=0)

    def diedro_minimo(self):
        """Ángulo diedro interior mínimo (grados) entre caras adyacentes."""
        aristas = {}
        for i, f in enumerate(self.F):
            for a, b in zip(f, f[1:] + f[:1]):
                aristas.setdefault(frozenset((a, b)), []).append(i)
        minimo = 180.0
        for caras in aristas.values():
            if len(caras) != 2:
                continue
            n1 = self.area_normal(caras[0])[1]
            n2 = self.area_normal(caras[1])[1]
            ang = 180.0 - np.degrees(np.arccos(np.clip(np.dot(n1, n2), -1, 1)))
            minimo = min(minimo, ang)
        return minimo

    def trasladado(self, d):
        return Poliedro(self.V + np.asarray(d), self.F)

    def a_dict(self, decimales=4):
        return {"vertices": np.round(self.V, decimales).tolist(), "caras": self.F}

    @staticmethod
    def de_dict(d):
        return Poliedro(d["vertices"], d["caras"])


# ------------------------------------------------------------ constructores
def hexaedro(intrados, extrados):
    """Pieza de seis caras a partir de dos cuadriláteros correspondientes.

    intrados, extrados: arrays (4, 3) recorridos en el mismo sentido.
    Caras: 0 intradós, 1 trasdós, 2..5 juntas (laterales).
    """
    V = np.vstack([intrados, extrados])
    F = [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]]
    return Poliedro(V, F)


def prisma_entre(inferior, superior):
    """Prisma (posiblemente oblicuo o ahusado) entre dos polígonos de k vértices."""
    inferior, superior = np.asarray(inferior), np.asarray(superior)
    k = len(inferior)
    V = np.vstack([inferior, superior])
    F = [list(range(k))[::-1], list(range(k, 2 * k))]
    for i in range(k):
        j = (i + 1) % k
        F.append([i, j, k + j, k + i])
    return Poliedro(V, F)


def prisma_extruido(poligono_xz, y0, y1):
    """Extrusión en y de un polígono contenido en el plano xz (arcos de dovelas)."""
    P = np.asarray(poligono_xz)
    inf = np.column_stack([P[:, 0], np.full(len(P), y0), P[:, 1]])
    sup = np.column_stack([P[:, 0], np.full(len(P), y1), P[:, 1]])
    return prisma_entre(inf, sup)


def poligono_regular(centro, radio, lados, z=0.0, giro=0.0):
    ang = giro + 2 * np.pi * np.arange(lados) / lados
    return np.column_stack([centro[0] + radio * np.cos(ang), centro[1] + radio * np.sin(ang),
                            np.full(lados, z)])


def contacto(pa, pb, tol=1e-3):
    """Busca la cara compartida entre dos poliedros (centros coincidentes y
    normales opuestas). Devuelve área, normal (de A hacia B), centro e
    inclinación respecto de la horizontal, o None si no hay cara común."""
    mejor = None
    for i in range(len(pa.F)):
        ca = pa.centro_cara(i)
        aa, na = pa.area_normal(i)
        for j in range(len(pb.F)):
            d = np.linalg.norm(ca - pb.centro_cara(j))
            if d > tol * max(1.0, np.sqrt(aa)):
                continue
            ab, nb = pb.area_normal(j)
            if np.dot(na, nb) < -0.95 and (mejor is None or d < mejor[0]):
                mejor = (d, min(aa, ab), na, ca)
    if mejor is None:
        return None
    _, area, n, c = mejor
    return {"area_m2": float(area), "normal": [float(x) for x in np.round(n, 5)],
            "centro": [float(x) for x in np.round(c, 4)],
            "inclinacion_deg": float(np.degrees(np.arccos(min(1.0, abs(n[2])))))}


def area_poligono_2d(P):
    x, y = np.asarray(P)[:, 0], np.asarray(P)[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def centroide_poligono_2d(P):
    P = np.asarray(P)
    x, y = P[:, 0], P[:, 1]
    xs, ys = np.roll(x, -1), np.roll(y, -1)
    cr = x * ys - xs * y
    A = cr.sum() / 2
    return np.array([((x + xs) * cr).sum() / (6 * A), ((y + ys) * cr).sum() / (6 * A)]), A
