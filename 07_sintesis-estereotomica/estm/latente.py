"""Genoma de diseño y síntesis propositiva por interpolación esférica (slerp).

Cada obra se describe por un genoma de 10 parámetros con significado
constructivo. Se normaliza a [-1, 1] con cotas FIJAS (no estadísticas del
corpus), de modo que el espacio latente no cambia al ingerir obras nuevas.

slerp: la dirección se interpola sobre la hiperesfera unidad y la norma de
forma lineal. Frente a la interpolación lineal conserva la "intensidad" de
los rasgos a mitad de camino (la media lineal de dos vectores casi opuestos
colapsa hacia el origen, es decir, hacia una obra genérica sin carácter).
"""

import numpy as np

GENOMA = [
    # nombre, mínimo, máximo, tipo, descripción
    ("orden_radial", 4, 12, "par", "Lados del polígono de planta"),
    ("salto_estrella_rel", 0.0, 0.5, "estrella", "k/n del polígono estrellado de nervios {n/k}"),
    ("terceletes", 0, 1, "binario", "Terceletes y ligaduras (bóveda estrellada)"),
    ("apuntamiento", 0.0, 1.0, "continuo", "0 medio punto -> 1 apuntado equilátero"),
    ("beta_superficie", 0.0, 1.0, "continuo", "0 arista (crucería) -> 1 cúpula / paños"),
    ("espesor_rel", 0.012, 0.10, "continuo", "Espesor de plementería / luz"),
    ("mocarabe_rel", 0.0, 0.9, "continuo", "Fracción radial ocupada por celdas voladas"),
    ("inclinacion_junta", 0.0, 1.0, "continuo", "0 lechos horizontales (voladizo) -> 1 juntas normales"),
    ("despiece", 6, 14, "entero", "Hiladas de la cáscara (tamaño de pieza)"),
    ("canto_nervio_rel", 0.0, 0.06, "continuo", "Canto de nervio / luz (0 = sin nervios)"),
]
NOMBRES = [g[0] for g in GENOMA]
LO = np.array([g[1] for g in GENOMA], float)
HI = np.array([g[2] for g in GENOMA], float)


def codificar(genoma):
    x = np.array([float(genoma[n]) for n in NOMBRES])
    return 2 * (x - LO) / (HI - LO) - 1


def decodificar(z):
    x = LO + (np.clip(z, -1, 1) + 1) / 2 * (HI - LO)
    g = {}
    for (nombre, lo, hi, tipo, _), v in zip(GENOMA, x):
        if tipo == "par":
            v = float(int(np.clip(2 * round(v / 2), lo, hi)))
        elif tipo in ("entero", "binario"):
            v = float(int(round(v)))
        g[nombre] = float(v)
    n = int(g["orden_radial"])
    k = int(np.clip(round(g["salto_estrella_rel"] * n), 0, n // 2))
    g["salto_estrella_rel"] = k / n
    if g["canto_nervio_rel"] < 0.004:
        g["canto_nervio_rel"] = 0.0
    return g


def slerp(z0, z1, t):
    z0, z1 = np.asarray(z0, float), np.asarray(z1, float)
    r0, r1 = np.linalg.norm(z0), np.linalg.norm(z1)
    if r0 < 1e-12 or r1 < 1e-12:
        return (1 - t) * z0 + t * z1
    u0, u1 = z0 / r0, z1 / r1
    om = np.arccos(np.clip(np.dot(u0, u1), -1, 1))
    if om < 1e-6:
        u = u0
    else:
        u = (np.sin((1 - t) * om) * u0 + np.sin(t * om) * u1) / np.sin(om)
    return u * ((1 - t) * r0 + t * r1)


def serie(genoma_a, genoma_b, ts):
    za, zb = codificar(genoma_a), codificar(genoma_b)
    return [(float(t), decodificar(slerp(za, zb, t))) for t in ts]


def distancia(genoma_a, genoma_b):
    return float(np.linalg.norm(codificar(genoma_a) - codificar(genoma_b)))
