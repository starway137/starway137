"""Vistas SVG: axonometría de piezas por tipo y sección con línea de empujes."""

from pathlib import Path

import numpy as np

COLORES = {
    "plemento": (196, 186, 168), "celda_mocarabe": (222, 160, 90), "dovela_nervio": (120, 92, 70),
    "clave": (160, 55, 45), "jarja": (80, 80, 90), "dovela": (190, 170, 140),
}
LUZ = np.array([-0.4, -0.5, 0.77])


def _proyector(az=-35.0, el=32.0):
    a, e = np.radians(az), np.radians(el)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    M = Rx @ Rz
    # pantalla: x -> derecha, z (tras rotar) -> arriba, y -> profundidad
    return lambda P: P @ M.T


def axonometria(grafo, ruta, titulo="", ancho=860, corte_y=None, leyenda=True, desde_abajo=True):
    """Axonometría con pintor. desde_abajo=True muestra el intradós (vista de gusano)."""
    proy = _proyector(el=-38.0 if desde_abajo else 32.0)
    polis = []
    for nid, geo in grafo.geometrias.items():
        tipo = grafo.nodos[nid]["tipo"]
        if corte_y is not None and grafo.nodos[nid]["centroide"][1] > corte_y:
            continue
        col = np.array(COLORES.get(tipo, (170, 170, 170)), float)
        P = proy(geo.V)
        for i, f in enumerate(geo.F):
            _, nrm = geo.area_normal(i)
            nv = proy(nrm[None])[0]
            if nv[1] > 0.05:            # cara que mira hacia atrás
                continue
            luz = LUZ * ([1, 1, -1] if desde_abajo else 1)
            sh = 0.5 + 0.5 * max(0.0, float(np.dot(nrm, luz / np.linalg.norm(luz))))
            polis.append((P[f, 1].mean(), P[f][:, [0, 2]], tuple(int(c) for c in (col * sh).clip(0, 255)), tipo))
    if not polis:
        return
    todos = np.vstack([p[1] for p in polis])
    lo, hi = todos.min(axis=0), todos.max(axis=0)
    esc = (ancho - 60) / max(hi - lo)
    alto = int((hi[1] - lo[1]) * esc + 90)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" '
           f'height="{alto}" font-family="sans-serif">', f'<rect width="{ancho}" height="{alto}" fill="#fbfaf7"/>',
           f'<text x="20" y="24" font-size="15" font-weight="600" fill="#222">{titulo}</text>']
    for _, P, c, _ in sorted(polis, key=lambda p: -p[0]):
        pts = " ".join(f"{30 + (x - lo[0]) * esc:.1f},{alto - 30 - (z - lo[1]) * esc:.1f}" for x, z in P)
        out.append(f'<polygon points="{pts}" fill="rgb{c}" stroke="#3a3530" stroke-width="0.35"/>')
    if leyenda:
        tipos = sorted({p[3] for p in polis})
        x = 20
        for tp in tipos:
            c = tuple(int(v) for v in COLORES.get(tp, (170, 170, 170)))
            out.append(f'<rect x="{x}" y="36" width="12" height="12" fill="rgb{c}"/>')
            out.append(f'<text x="{x + 16}" y="46" font-size="11" fill="#333">{tp}</text>')
            x += 22 + 6.5 * len(tp)
    out.append("</svg>")
    Path(ruta).write_text("\n".join(out) + "\n", encoding="utf-8")


def seccion_empujes(juntas, piezas_poligonos, linea, ruta, titulo="", ancho=760):
    """Semisección con dovelas, juntas y línea de empujes de máximo margen."""
    J = np.asarray(juntas)
    pts = [J.reshape(-1, 2)] + [np.asarray(p) for p in piezas_poligonos]
    todos = np.vstack(pts)
    lo, hi = todos.min(axis=0), todos.max(axis=0)
    esc = (ancho - 80) / max(hi - lo)
    alto = int((hi[1] - lo[1]) * esc + 100)

    def X(p):
        return 40 + (p[0] - lo[0]) * esc, alto - 40 - (p[1] - lo[1]) * esc

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" '
           f'height="{alto}" font-family="sans-serif">', f'<rect width="{ancho}" height="{alto}" fill="#fbfaf7"/>',
           f'<text x="20" y="24" font-size="15" font-weight="600" fill="#222">{titulo}</text>']
    for P in piezas_poligonos:
        s = " ".join("%.1f,%.1f" % X(p) for p in P)
        out.append(f'<polygon points="{s}" fill="#e3dccd" stroke="#5a5048" stroke-width="0.8"/>')
    if linea is not None:
        s = " ".join("%.1f,%.1f" % X(p) for p in linea)
        out.append(f'<polyline points="{s}" fill="none" stroke="#c0392b" stroke-width="2.2"/>')
        out.append('<text x="20" y="44" font-size="12" fill="#c0392b">línea de empujes admisible (máximo margen)</text>')
    else:
        out.append('<text x="20" y="44" font-size="12" fill="#8e2a1f">sin línea de empujes admisible</text>')
    out.append("</svg>")
    Path(ruta).write_text("\n".join(out) + "\n", encoding="utf-8")
