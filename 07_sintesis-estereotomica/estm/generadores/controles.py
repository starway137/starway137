"""Controles negativos para el selector de obras de alta complejidad.

Son fábricas reales y bien construidas, pero sin las características que
definen el corpus (doble curvatura, simetría rotacional de orden >= 3,
juntas de inclinación variable, diversidad de piezas). El selector debe
rechazarlas; si no lo hiciera, su criterio no discriminaría nada.

Devuelven piezas sin semántica [(id, V, F)], como llegaría un levantamiento.
"""

import numpy as np

from ..geometria import hexaedro, prisma_entre


def _caja(x0, x1, y0, y1, z0, z1):
    inf = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]])
    return prisma_entre(inf, inf + [0, 0, z1 - z0])


def muro_silleria(largo=8.0, alto=4.0, espesor=0.6, sillar=(0.9, 0.45)):
    """Muro de sillería a soga con hiladas alternadas a matajunta."""
    piezas, L, H = [], sillar[0], sillar[1]
    for i in range(int(round(alto / H))):
        x = -L / 2 if i % 2 else 0.0
        k = 0
        while x < largo - 1e-9:
            x0, x1 = max(x, 0.0), min(x + L, largo)
            g = _caja(x0, x1, 0, espesor, i * H, (i + 1) * H)
            piezas.append((f"s{i:02d}_{k:02d}", g.V, g.F))
            x, k = x + L, k + 1
    return piezas


def losa_vigas(luz=6.0, ancho=6.0, n_vigas=5, canto=0.45, b=0.25, e_losa=0.18):
    """Forjado de losas prefabricadas sobre vigas de piedra o hormigón."""
    piezas, paso = [], ancho / (n_vigas - 1)
    for i in range(n_vigas):
        y = i * paso
        g = _caja(0, luz, y - b / 2, y + b / 2, 0, canto)
        piezas.append((f"v{i}", g.V, g.F))
    for i in range(n_vigas - 1):
        for k in range(4):
            g = _caja(k * luz / 4, (k + 1) * luz / 4, i * paso, (i + 1) * paso, canto, canto + e_losa)
            piezas.append((f"l{i}_{k}", g.V, g.F))
    return piezas


def canon_corrido(luz=6.0, largo=8.0, espesor=0.35, dovelas=13, anillos=8):
    """Bóveda de cañón de medio punto: curvatura simple, simetría bilateral."""
    piezas, R = [], luz / 2
    fi = np.linspace(np.pi, 0, dovelas + 1)
    ys = np.linspace(0, largo, anillos + 1)
    for a in range(anillos):
        desfase = 0.5 * (a % 2)                         # aparejo a matajunta entre anillos
        bordes = np.clip(fi + desfase * (fi[1] - fi[0]), 0, np.pi) if desfase else fi
        bordes = np.unique(np.concatenate([[np.pi], bordes, [0.0]]))[::-1]
        for i in range(len(bordes) - 1):
            f0, f1 = bordes[i], bordes[i + 1]
            if f0 - f1 < 1e-6:
                continue

            def p(f, r, y):
                return [r * np.cos(f), y, r * np.sin(f)]
            y0, y1 = ys[a], ys[a + 1]
            intr = np.array([p(f0, R, y0), p(f1, R, y0), p(f1, R, y1), p(f0, R, y1)])
            extr = np.array([p(f0, R + espesor, y0), p(f1, R + espesor, y0),
                             p(f1, R + espesor, y1), p(f0, R + espesor, y1)])
            g = hexaedro(intr, extr)
            piezas.append((f"c{a}_{i:02d}", g.V, g.F))
    return piezas


CONTROLES = {
    "NC-MUR": ("Muro de sillería a matajunta", muro_silleria),
    "NC-LOS": ("Forjado de losas sobre vigas", losa_vigas),
    "NC-CAN": ("Bóveda de cañón corrido de medio punto", canon_corrido),
}
