"""Ingesta de obras nuevas desde geometría pura (sin semántica).

Una obra nueva puede llegar como:
    ficha paramétrica   genoma conocido -> gramática (obras/nuevas.json)
    mallas de piezas    OBJ (un grupo por pieza) o IFC (IfcBuildingElementPart,
                        IfcMember, IfcPlate…): levantamiento segmentado, modelo
                        de otro autor, archivo de fabricante

En el segundo caso no hay tipos de pieza ni juntas: el grafo se reconstruye
detectando contactos entre caras (planos casi coincidentes con normales
opuestas y solape de área), con tolerancia al ruido de levantamiento.
"""

from pathlib import Path

import numpy as np

from .geometria import Poliedro
from .grafo import GrafoAtribuido


# ------------------------------------------------------------------ lectura
def leer_obj(ruta):
    """Devuelve [(id, V, F)]: un grupo/objeto OBJ = una pieza."""
    V_glob, piezas, actual = [], [], None
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if linea.startswith("v "):
            V_glob.append([float(x) for x in linea.split()[1:4]])
        elif linea.startswith(("g ", "o ")):
            actual = {"id": linea.split(maxsplit=1)[1].strip(), "caras": []}
            piezas.append(actual)
        elif linea.startswith("f "):
            if actual is None:
                actual = {"id": "pieza", "caras": []}
                piezas.append(actual)
            actual["caras"].append([int(t.split("/")[0]) - 1 for t in linea.split()[1:]])
    V_glob = np.array(V_glob)
    salida = []
    for p in piezas:
        if not p["caras"]:
            continue
        usados = sorted({i for f in p["caras"] for i in f})
        mapa = {g: k for k, g in enumerate(usados)}
        salida.append((p["id"], V_glob[usados], [[mapa[i] for i in f] for f in p["caras"]]))
    return salida


def escribir_obj(piezas, ruta):
    lineas, base = ["# ESTM - piezas sin semántica"], 0
    for pid, V, F in piezas:
        lineas.append(f"g {pid}")
        lineas += [f"v {x:.5f} {y:.5f} {z:.5f}" for x, y, z in V]
        lineas += ["f " + " ".join(str(base + i + 1) for i in f) for f in F]
        base += len(V)
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text("\n".join(lineas) + "\n", encoding="utf-8")


def leer_ifc(ruta, clases=("IfcBuildingElementPart", "IfcMember", "IfcPlate", "IfcBuildingElementProxy")):
    """Mallas trianguladas de los elementos IFC (coordenadas absolutas, metros)."""
    import ifcopenshell
    import ifcopenshell.geom
    f = ifcopenshell.open(str(ruta))
    ajustes = ifcopenshell.geom.settings()
    ajustes.set("use-world-coords", True)
    salida = []
    for clase in clases:
        for el in f.by_type(clase):
            if not el.Representation:
                continue
            sh = ifcopenshell.geom.create_shape(ajustes, el)
            V = np.array(sh.geometry.verts).reshape(-1, 3)
            T = np.array(sh.geometry.faces).reshape(-1, 3)
            salida.append((el.GlobalId, V, T.tolist()))
    return salida


# ------------------------------------------------------------------ alteraciones de ensayo
def ciega(piezas, semilla=0, ruido=0.0015, giro=None, traslacion=None):
    """Prepara una prueba ciega: nombres neutros, orden barajado, giro y
    traslación arbitrarios y ruido gaussiano de levantamiento por vértice.
    Devuelve (piezas_ciegas, verdad) con verdad[id_neutro] = id_original."""
    rng = np.random.default_rng(semilla)
    th = rng.uniform(0, 2 * np.pi) if giro is None else giro
    d = rng.uniform(-50, 50, 3) * [1, 1, 0] if traslacion is None else np.asarray(traslacion)
    Rz = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
    orden = rng.permutation(len(piezas))
    salida, verdad = [], {}
    for k, i in enumerate(orden):
        pid, V, F = piezas[i]
        Vn = (np.asarray(V) @ Rz.T + d) + rng.normal(0, ruido, np.shape(V))
        nid = f"p{k:04d}"
        salida.append((nid, Vn, F))
        verdad[nid] = pid
    return salida, verdad, {"giro_rad": float(th), "traslacion": [float(x) for x in d], "ruido_m": ruido}


# ------------------------------------------------------------------ contactos
def _facetas(V, F):
    out = []
    for f in F:
        P = V[f]
        n = np.zeros(3)
        for a, b in zip(P, np.roll(P, -1, axis=0)):
            n += np.cross(a, b)
        area = np.linalg.norm(n) / 2
        if area < 1e-9:
            continue
        out.append((P, n / (2 * area), P.mean(axis=0), area))
    return out


def _base_plano(n):
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(n, e1)


def _convexo(P2):
    """Envolvente convexa (monotone chain) en sentido antihorario."""
    P = sorted(map(tuple, P2))
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


def _recorte(sujeto, recorte):
    """Sutherland-Hodgman: polígono sujeto recortado por un polígono convexo antihorario."""
    salida = list(map(np.asarray, sujeto))
    for i in range(len(recorte)):
        a, b = recorte[i], recorte[(i + 1) % len(recorte)]
        entrada, salida = salida, []
        if not entrada:
            break

        def dentro(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-12

        def corte(p, q):
            d1, d2 = q - p, b - a
            den = d1[0] * d2[1] - d1[1] * d2[0]
            t = ((a[0] - p[0]) * d2[1] - (a[1] - p[1]) * d2[0]) / den if abs(den) > 1e-15 else 0.0
            return p + t * d1
        for j in range(len(entrada)):
            p, q = entrada[j], entrada[(j + 1) % len(entrada)]
            if dentro(q):
                if not dentro(p):
                    salida.append(corte(p, q))
                salida.append(q)
            elif dentro(p):
                salida.append(corte(p, q))
    return np.array(salida)


def _area2(P):
    if len(P) < 3:
        return 0.0
    x, y = P[:, 0], P[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def detectar_contactos(piezas, tol=0.02, ang_max=25.0, area_min=2e-3):
    """Contactos entre piezas: caras casi coplanares, normales opuestas y solape."""
    fac = [_facetas(np.asarray(V), F) for _, V, F in piezas]
    lo = np.array([np.min(V, axis=0) for _, V, _ in piezas]) - tol
    hi = np.array([np.max(V, axis=0) for _, V, _ in piezas]) + tol
    cos_max = np.cos(np.radians(ang_max))
    contactos = []
    for i in range(len(piezas)):
        cand = np.where(np.all(lo[i + 1:] <= hi[i], axis=1) & np.all(hi[i + 1:] >= lo[i], axis=1))[0] + i + 1
        for j in cand:
            area_tot, n_acum, c_acum = 0.0, np.zeros(3), np.zeros(3)
            for Pa, na, ca, aa in fac[i]:
                for Pb, nb, cb, ab in fac[j]:
                    if np.dot(na, nb) > -cos_max or abs(np.dot(cb - ca, na)) > tol:
                        continue
                    e1, e2 = _base_plano(na)
                    A2 = _convexo(np.column_stack([(Pa - ca) @ e1, (Pa - ca) @ e2]))
                    B2 = _convexo(np.column_stack([(Pb - ca) @ e1, (Pb - ca) @ e2]))
                    if len(A2) < 3 or len(B2) < 3:
                        continue
                    ov = _area2(_recorte(A2, B2))
                    if ov > 0:
                        area_tot += ov
                        n_acum += ov * na
                        c_acum += ov * ca
            if area_tot >= area_min:
                n = n_acum / np.linalg.norm(n_acum)
                contactos.append((piezas[i][0], piezas[j][0], {
                    "area_m2": float(area_tot), "normal": [float(x) for x in np.round(n, 5)],
                    "centro": [float(x) for x in np.round(c_acum / area_tot, 4)],
                    "inclinacion_deg": float(np.degrees(np.arccos(min(1.0, abs(n[2])))))}))
    return contactos


def grafo_desde_mallas(nombre, piezas, densidad=2400.0, **kw):
    """Grafo atribuido de una obra sin semántica: nodos 'pieza', aristas 'contacto'."""
    g = GrafoAtribuido(nombre, origen="mallas", tipologia="desconocida")
    for pid, V, F in piezas:
        g.add_nodo(pid, "pieza", Poliedro(V, F), densidad=densidad, n_caras=len(F))
    for a, b, c in detectar_contactos(piezas, **kw):
        g.add_arista(a, b, "contacto", calcular_contacto=False, **c)
    return g


def piezas_de_grafo(grafo):
    return [(nid, grafo.geometrias[nid].V, grafo.geometrias[nid].F) for nid in grafo.piezas()]
