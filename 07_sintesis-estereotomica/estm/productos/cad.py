"""Planos y modelos CAD en DXF (AutoCAD, BricsCAD, DraftSight, LibreCAD,
SketchUp Pro, Rhino, Revit como vínculo). DWG: ver dwg.py.

    modelo_3d.dxf       una POLYFACE por pieza, capa por tipo, XDATA ESTM (id,
                        tipo, masa, orden de montaje, método de fabricación)
    planta_replanteo.dxf  planta acotada: polígono, trazas de nervios, contorno de
                        cada pieza en proyección, puntos de replanteo numerados
                        (los mismos de replanteo.csv) y cotas de luz
    montea.dxf          secciones verticales por los ejes de simetría (lado y
                        vértice): la "montea" del cantero, a escala 1:1
    plantillas.dxf      plantillas de corte: cada cara de cada clase de pieza
                        desarrollada en su plano, con su número de unidades
"""

from pathlib import Path

import ezdxf
import numpy as np
from ezdxf import colors as ezcolors
from ezdxf.enums import TextEntityAlignment

from .mallas import color

APPID = "ESTM"


def _doc():
    doc = ezdxf.new("R2018", setup=True)
    doc.units = ezdxf.units.M
    doc.header["$INSUNITS"] = 6
    doc.header["$MEASUREMENT"] = 1
    doc.appids.add(APPID)
    return doc


def _capa(doc, nombre, rgb=None, aci=7):
    if nombre not in doc.layers:
        capa = doc.layers.add(nombre, color=aci)
        if rgb:
            capa.true_color = ezcolors.rgb2int(rgb)
    return nombre


def _texto(msp, s, p, h, capa):
    msp.add_text(s, height=h, dxfattribs={"layer": capa}).set_placement(
        (float(p[0]), float(p[1])), align=TextEntityAlignment.MIDDLE_CENTER)


# ------------------------------------------------------------------ modelo 3D
def modelo_3d(obra, ruta):
    doc = _doc()
    msp = doc.modelspace()
    g = obra.grafo
    for nid in g.piezas():
        d, geo = g.nodos[nid], g.geometrias[nid]
        capa = _capa(doc, f"ESTM_{d['tipo']}", color(d["tipo"]))
        pf = msp.add_polyface(dxfattribs={"layer": capa})
        pf.append_faces([[tuple(map(float, geo.V[i])) for i in f] for f in geo.F])
        pf.optimize()
        pf.set_xdata(APPID, [(1000, nid), (1000, d["tipo"]), (1040, float(d.get("masa_kg", 0.0))),
                             (1070, int(d.get("orden_montaje", -1))), (1000, str(d.get("metodo_recomendado", "")))])
    doc.saveas(ruta)
    return [Path(ruta)]


# ------------------------------------------------------------------ planta y replanteo
def _hull(P):
    P = sorted(map(tuple, np.round(P, 6)))
    if len(P) < 3:
        return np.array(P)

    def giro(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    inf, sup = [], []
    for p in P:
        while len(inf) >= 2 and giro(inf[-2], inf[-1], p) <= 0:
            inf.pop()
        inf.append(p)
    for p in reversed(P):
        while len(sup) >= 2 and giro(sup[-2], sup[-1], p) <= 0:
            sup.pop()
        sup.append(p)
    return np.array(inf[:-1] + sup[:-1])


def planta_replanteo(obra, ruta, puntos):
    doc = _doc()
    msp = doc.modelspace()
    g, sup = obra.grafo, obra.superficie
    escala = sup.R / 6
    vert = sup.vertices()
    c = _capa(doc, "ESTM_CONTORNO", aci=7)
    msp.add_lwpolyline([tuple(v) for v in vert], close=True, dxfattribs={"layer": c, "const_width": 0.0})
    cp = _capa(doc, "ESTM_PIEZAS_PLANTA", aci=8)
    for nid in g.piezas():
        H = _hull(g.geometrias[nid].V[:, :2])
        if len(H) >= 3:
            msp.add_lwpolyline([tuple(p) for p in H], close=True, dxfattribs={"layer": cp})
    cn = _capa(doc, "ESTM_EJES_NERVIOS", (120, 92, 70))
    for fam, a, b in obra.meta.get("nervios_planta", []):
        msp.add_line(tuple(a[:2]), tuple(b[:2]), dxfattribs={"layer": cn, "linetype": "DASHDOT"})
    cr = _capa(doc, "ESTM_REPLANTEO", (200, 30, 30))
    for p in puntos:
        msp.add_point((p["x"], p["y"], p["z"]), dxfattribs={"layer": cr})
        msp.add_circle((p["x"], p["y"]), 0.02 * escala, dxfattribs={"layer": cr})
        _texto(msp, p["id"], (p["x"] + 0.1 * escala, p["y"] + 0.1 * escala), 0.1 * escala, cr)
    cc = _capa(doc, "ESTM_COTAS", aci=3)
    estilo = {"dimtxt": 0.25 * escala, "dimasz": 0.15 * escala, "dimexe": 0.05 * escala, "dimexo": 0.05 * escala,
              "dimlfac": 1.0, "dimdec": 2, "dimtad": 1, "dimgap": 0.05 * escala}
    a, b = vert[0], vert[len(vert) // 2]
    msp.add_aligned_dim(p1=tuple(a), p2=tuple(b), distance=0.4 * escala, override=estilo,
                        dxfattribs={"layer": cc}).render()
    A = sup.A
    msp.add_linear_dim(base=(0, -A - 0.6 * escala), p1=(-A, 0), p2=(A, 0), override=estilo,
                       dxfattribs={"layer": cc}).render()
    ct = _capa(doc, "ESTM_ROTULO", aci=7)
    _texto(msp, f"{obra.id} - {obra.nombre}", (0, -A - 1.4 * escala), 0.12 * escala, ct)
    _texto(msp, f"Planta y replanteo - luz {2 * A:.2f} m - unidades: m - puntos en replanteo.csv",
           (0, -A - 1.8 * escala), 0.07 * escala, ct)
    doc.saveas(ruta)
    return [Path(ruta)]


# ------------------------------------------------------------------ montea (secciones)
def _corte(geo, origen, u):
    """Segmentos de la intersección de las caras con el plano vertical que contiene u."""
    nrm = np.array([-u[1], u[0], 0.0])
    s = (geo.V - origen) @ nrm
    segs = []
    for f in geo.F:
        pts = []
        for i, j in zip(f, f[1:] + f[:1]):
            if (s[i] > 0) != (s[j] > 0):
                t = s[i] / (s[i] - s[j])
                p = geo.V[i] + t * (geo.V[j] - geo.V[i])
                pts.append((float(np.dot(p[:2] - origen[:2], u[:2])), float(p[2])))
        if len(pts) >= 2:
            segs.append(pts[:2])
    return segs


def montea(obra, ruta):
    doc = _doc()
    msp = doc.modelspace()
    g, sup = obra.grafo, obra.superficie
    n = sup.n
    ejes = [("por el eje de un lado", np.array([1.0, 0.0])),
            ("por un vértice", np.array([np.cos(np.pi / n), np.sin(np.pi / n)]))]
    dx = 2.6 * sup.R
    for k, (nombre, u) in enumerate(ejes):
        u3 = np.array([u[0], u[1], 0.0])
        for nid in g.piezas():
            capa = _capa(doc, f"ESTM_SECCION_{g.nodos[nid]['tipo']}", color(g.nodos[nid]["tipo"]))
            for a, b in _corte(g.geometrias[nid], np.zeros(3), u3):
                msp.add_line((a[0] + k * dx, a[1]), (b[0] + k * dx, b[1]), dxfattribs={"layer": capa})
        ci = _capa(doc, "ESTM_INTRADOS_TEORICO", aci=1)
        r = np.linspace(-sup.R, sup.R, 241) if k else np.linspace(-sup.A, sup.A, 241)
        z = sup.z(r * u[0], r * u[1])
        msp.add_lwpolyline([(float(a + k * dx), float(b)) for a, b in zip(r, z)], dxfattribs={"layer": ci})
        msp.add_line((-sup.R + k * dx, 0), (sup.R + k * dx, 0), dxfattribs={"layer": _capa(doc, "ESTM_LINEA_IMPOSTA", aci=8)})
        _texto(msp, f"Sección {nombre}", (k * dx, -0.25 * sup.R), 0.05 * sup.R, _capa(doc, "ESTM_ROTULO"))
    doc.saveas(ruta)
    return [Path(ruta)]


# ------------------------------------------------------------------ plantillas de corte
def _desarrollo(P):
    c = P.mean(axis=0)
    n = np.cross(P[1] - P[0], P[2] - P[0])
    n /= np.linalg.norm(n) or 1
    e1 = (P[1] - P[0]) / (np.linalg.norm(P[1] - P[0]) or 1)
    e2 = np.cross(n, e1)
    return np.column_stack([(P - c) @ e1, (P - c) @ e2])


def clases_piezas(grafo, tol=0.04):
    """Representante y unidades de cada clase de piezas congruentes."""
    clases = []
    for nid in grafo.piezas():
        d = grafo.nodos[nid]
        f = np.array([np.log(d["volumen_m3"]), *np.log(np.sort(d["extensiones_m"]))])
        for c in clases:
            if c["tipo"] == d["tipo"] and np.all(np.abs(c["firma"] - f) < tol):
                c["ids"].append(nid)
                break
        else:
            clases.append({"tipo": d["tipo"], "firma": f, "ids": [nid]})
    for k, c in enumerate(clases):
        c["clase"] = f"C{k + 1:03d}"
    return clases


def plantillas(obra, ruta, clases, maximo=60):
    doc = _doc()
    msp = doc.modelspace()
    g = obra.grafo
    cl = _capa(doc, "ESTM_PLANTILLA", aci=7)
    ct = _capa(doc, "ESTM_PLANTILLA_TEXTO", aci=3)
    x0 = y0 = 0.0
    fila_h = 0.0
    ancho_max = 14.0
    for c in clases[:maximo]:
        geo = g.geometrias[c["ids"][0]]
        h = 0.0
        x_c = x0
        for i, f in enumerate(geo.F):
            Q = _desarrollo(geo.V[f])
            w = np.ptp(Q[:, 0]) + 0.1
            Q = Q - Q.min(axis=0) + [x_c, y0]
            msp.add_lwpolyline([tuple(q) for q in Q], close=True, dxfattribs={"layer": cl})
            _texto(msp, f"{i}", Q.mean(axis=0), 0.03, ct)
            x_c += w
            h = max(h, np.ptp(Q[:, 1]))
        _texto(msp, f"{c['clase']} {c['tipo']} x{len(c['ids'])} (rep. {c['ids'][0]})", ((x0 + x_c) / 2, y0 - 0.08),
               0.05, ct)
        fila_h = max(fila_h, h)
        x0 = x_c + 0.4
        if x0 > ancho_max:
            x0, y0 = 0.0, y0 - fila_h - 0.4
            fila_h = 0.0
    doc.saveas(ruta)
    return [Path(ruta)]
