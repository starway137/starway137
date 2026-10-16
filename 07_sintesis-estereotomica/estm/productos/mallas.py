"""Mallas de intercambio: OBJ+MTL, STL (por pieza, para CNC/impresión), glTF
binario (.glb, visores web y realidad aumentada) y COLLADA (.dae, importación
directa en SketchUp, Blender, 3ds Max, Rhino).

Cada pieza conserva su identidad (grupo, nodo o archivo con su id) y su tipo
(material), de modo que el modelo es despiezable en el programa de destino.
Unidades: metros; eje Z vertical (glTF exige Y vertical: se convierte).
"""

import io
import json
import struct
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np

from ..vista import COLORES

GRIS = (170, 170, 170)


def color(tipo):
    return COLORES.get(tipo, GRIS)


def triangulos(geo):
    """Abanico de cada cara (las caras de la gramática son convexas)."""
    T = []
    for f in geo.F:
        for a, b in zip(f[1:-1], f[2:]):
            T.append((f[0], a, b))
    return np.array(T, dtype=np.int64)


def _piezas(obra):
    g = obra.grafo
    for nid in g.piezas():
        yield nid, g.nodos[nid], g.geometrias[nid]


# ------------------------------------------------------------------ OBJ
def obj(obra, ruta):
    ruta = Path(ruta)
    tipos = sorted({d["tipo"] for _, d, _ in _piezas(obra)})
    mtl = [f"newmtl {t}\nKd {' '.join(f'{c / 255:.3f}' for c in color(t))}\n" for t in tipos]
    ruta.with_suffix(".mtl").write_text("\n".join(mtl), encoding="utf-8")
    L, base = [f"# ESTM {obra.id} · {obra.nombre} · metros, Z vertical", f"mtllib {ruta.with_suffix('.mtl').name}"], 0
    for nid, d, geo in _piezas(obra):
        L += [f"g {nid}", f"usemtl {d['tipo']}"]
        L += [f"v {x:.5f} {y:.5f} {z:.5f}" for x, y, z in geo.V]
        L += ["f " + " ".join(str(base + i + 1) for i in f) for f in geo.F]
        base += len(geo.V)
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return [ruta, ruta.with_suffix(".mtl")]


# ------------------------------------------------------------------ STL
def _stl_binario(geo, nombre):
    T = triangulos(geo)
    buf = io.BytesIO()
    buf.write(nombre.encode("ascii", "replace")[:80].ljust(80, b" "))
    buf.write(struct.pack("<I", len(T)))
    for a, b, c in T:
        p0, p1, p2 = geo.V[a], geo.V[b], geo.V[c]
        n = np.cross(p1 - p0, p2 - p0)
        n = n / (np.linalg.norm(n) or 1)
        buf.write(struct.pack("<12fH", *n, *p0, *p1, *p2, 0))
    return buf.getvalue()


def stl(obra, ruta_zip):
    """Un STL binario por pieza (nombre = id) en un zip, más el conjunto."""
    ruta_zip = Path(ruta_zip)
    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for nid, d, geo in _piezas(obra):
            info = zipfile.ZipInfo(f"{d['tipo']}/{nid}.stl", date_time=(2026, 10, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, _stl_binario(geo, f"ESTM {obra.id} {nid}"))
    return [ruta_zip]


# ------------------------------------------------------------------ glTF binario
def glb(obra, ruta):
    """glTF 2.0 binario: un nodo por pieza (con extras: id, tipo, masa, orden de montaje)."""
    tipos = sorted({d["tipo"] for _, d, _ in _piezas(obra)})
    materiales = [{"name": t, "pbrMetallicRoughness": {
        "baseColorFactor": [*(c / 255 for c in color(t)), 1.0], "metallicFactor": 0.0, "roughnessFactor": 0.9}}
        for t in tipos]
    binario, vistas, accesores, mallas, nodos = bytearray(), [], [], [], []

    def anadir(datos, destino):
        while len(binario) % 4:
            binario.append(0)
        vistas.append({"buffer": 0, "byteOffset": len(binario), "byteLength": len(datos), "target": destino})
        binario.extend(datos)
        return len(vistas) - 1

    for nid, d, geo in _piezas(obra):
        T = triangulos(geo)
        P = geo.V[T.ravel()]                               # vértices por triángulo: normales planas
        N = np.repeat(np.cross(P[1::3] - P[0::3], P[2::3] - P[0::3]), 3, axis=0)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        P = P[:, [0, 2, 1]] * [1, 1, -1]                   # Z arriba -> Y arriba
        N = N[:, [0, 2, 1]] * [1, 1, -1]
        vp = anadir(P.astype("<f4").tobytes(), 34962)
        vn = anadir(N.astype("<f4").tobytes(), 34962)
        accesores.append({"bufferView": vp, "componentType": 5126, "count": len(P), "type": "VEC3",
                          "min": P.min(axis=0).tolist(), "max": P.max(axis=0).tolist()})
        accesores.append({"bufferView": vn, "componentType": 5126, "count": len(N), "type": "VEC3"})
        mallas.append({"name": nid, "primitives": [{"attributes": {"POSITION": len(accesores) - 2,
                                                                   "NORMAL": len(accesores) - 1},
                                                    "material": tipos.index(d["tipo"])}]})
        nodos.append({"name": nid, "mesh": len(mallas) - 1,
                      "extras": {"id": nid, "tipo": d["tipo"], "masa_kg": round(d.get("masa_kg", 0.0), 2),
                                 "orden_montaje": d.get("orden_montaje"),
                                 "metodo": d.get("metodo_recomendado")}})
    gltf = {"asset": {"version": "2.0", "generator": "ESTM productos"},
            "scene": 0, "scenes": [{"name": obra.id, "nodes": list(range(len(nodos)))}],
            "nodes": nodos, "meshes": mallas, "materials": materiales, "accessors": accesores,
            "bufferViews": vistas, "buffers": [{"byteLength": len(binario)}],
            "extras": {"obra": obra.id, "nombre": obra.nombre, "unidades": "m"}}
    js = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    while len(binario) % 4:
        binario.append(0)
    total = 12 + 8 + len(js) + 8 + len(binario)
    with open(ruta, "wb") as f:
        f.write(struct.pack("<4sII", b"glTF", 2, total))
        f.write(struct.pack("<I4s", len(js), b"JSON") + js)
        f.write(struct.pack("<I4s", len(binario), b"BIN\x00") + bytes(binario))
    return [Path(ruta)]


# ------------------------------------------------------------------ COLLADA
def dae(obra, ruta):
    """COLLADA 1.4.1 (SketchUp: Archivo > Importar > .dae): un componente por pieza."""
    tipos = sorted({d["tipo"] for _, d, _ in _piezas(obra)})
    efe = "".join(f'<effect id="fx-{t}"><profile_COMMON><technique sid="c"><lambert><diffuse><color>'
                  f'{" ".join(f"{c / 255:.3f}" for c in color(t))} 1</color></diffuse></lambert></technique>'
                  f'</profile_COMMON></effect>' for t in tipos)
    mat = "".join(f'<material id="m-{t}" name="{t}"><instance_effect url="#fx-{t}"/></material>' for t in tipos)
    geos, nodos = [], []
    for nid, d, geo in _piezas(obra):
        T = triangulos(geo)
        pos = " ".join(f"{x:.5f} {y:.5f} {z:.5f}" for x, y, z in geo.V)
        idx = " ".join(str(int(i)) for i in T.ravel())
        geos.append(f'<geometry id="g-{nid}" name="{nid}"><mesh><source id="p-{nid}"><float_array id="pa-{nid}" '
                    f'count="{geo.V.size}">{pos}</float_array><technique_common><accessor source="#pa-{nid}" '
                    f'count="{len(geo.V)}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/>'
                    f'<param name="Z" type="float"/></accessor></technique_common></source><vertices id="v-{nid}">'
                    f'<input semantic="POSITION" source="#p-{nid}"/></vertices><triangles material="m" '
                    f'count="{len(T)}"><input semantic="VERTEX" source="#v-{nid}" offset="0"/><p>{idx}</p>'
                    f'</triangles></mesh></geometry>')
        nodos.append(f'<node id="n-{nid}" name="{escape(nid)}"><instance_geometry url="#g-{nid}"><bind_material>'
                     f'<technique_common><instance_material symbol="m" target="#m-{d["tipo"]}"/></technique_common>'
                     f'</bind_material></instance_geometry></node>')
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" '
           'version="1.4.1"><asset><contributor><authoring_tool>ESTM productos</authoring_tool></contributor>'
           '<created>2026-10-16T00:00:00</created><modified>2026-10-16T00:00:00</modified>'
           '<unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>'
           f'<library_effects>{efe}</library_effects><library_materials>{mat}</library_materials>'
           f'<library_geometries>{"".join(geos)}</library_geometries><library_visual_scenes>'
           f'<visual_scene id="escena" name="{escape(obra.id)}">{"".join(nodos)}</visual_scene>'
           '</library_visual_scenes><scene><instance_visual_scene url="#escena"/></scene></COLLADA>\n')
    Path(ruta).write_text(xml, encoding="utf-8")
    return [Path(ruta)]
