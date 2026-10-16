"""Componente Script de Grasshopper (Rhino 8, Python 3) — importador ESTM.

Entradas del componente:
    ruta   (str)   ruta a un archivo *_gh.json generado por el pipeline
    tipo   (str)   opcional: filtra por tipo de pieza (p. ej. "dovela_nervio")
Salidas:
    mallas      Mesh por pieza
    ids         identificador de pieza (mismo que el GlobalId de IFC en guids)
    guids       GlobalId IFC
    tipos       tipo de pieza
    masas       masa (kg)
    montaje     orden de montaje
    grafo       líneas entre centroides de piezas en contacto (aristas de G)
    juntas      tipo de cada arista

Uso: Rhino 8 > Grasshopper > componente "Script" (Python 3), pegar este código
y declarar las entradas/salidas anteriores. No probado dentro de Rhino en
este repositorio (no hay Rhino en el entorno de CI); la lógica de lectura se
comprueba en tests/test_estm.py sin RhinoCommon.
"""

import json

try:
    import Rhino.Geometry as rg
except ImportError:          # fuera de Rhino: permite probar la lectura del JSON
    rg = None


def leer(ruta, tipo=None):
    with open(ruta, encoding="utf-8") as fh:
        datos = json.load(fh)
    piezas = [p for p in datos["piezas"] if not tipo or p["tipo"] == tipo]
    return datos, piezas


def a_malla(pieza):
    m = rg.Mesh()
    for x, y, z in pieza["vertices"]:
        m.Vertices.Add(x, y, z)
    for cara in pieza["caras"]:
        if len(cara) in (3, 4):
            m.Faces.AddFace(*cara)
        else:                                   # n-gono: abanico de triángulos
            for a, b in zip(cara[1:-1], cara[2:]):
                m.Faces.AddFace(cara[0], a, b)
    m.Normals.ComputeNormals()
    m.Compact()
    return m


if rg is not None and "ruta" in globals():
    datos, piezas = leer(ruta, globals().get("tipo"))  # noqa: F821
    por_id = {p["id"]: p for p in datos["piezas"]}
    mallas = [a_malla(p) for p in piezas]
    ids = [p["id"] for p in piezas]
    guids = [p["guid"] for p in piezas]
    tipos = [p["tipo"] for p in piezas]
    masas = [p["masa_kg"] for p in piezas]
    montaje = [p["orden_montaje"] for p in piezas]
    grafo, juntas = [], []
    for e in datos["aristas"]:
        a, b = por_id[e["u"]]["centroide"], por_id[e["v"]]["centroide"]
        grafo.append(rg.Line(rg.Point3d(*a), rg.Point3d(*b)))
        juntas.append(e["tipo"])
