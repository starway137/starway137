"""Speckle: objeto de intercambio compatible con el modelo de objetos de Speckle 2.

Se genera un árbol Base -> @piezas (Objects.Geometry.Mesh) -> @juntas, con
applicationId estable (el mismo identificador que el GlobalId de IFC), de modo
que los receptores de Speckle en Grasshopper/Rhino/Revit puedan actualizar
piezas en lugar de duplicarlas.

El envío al servidor (enviar) requiere specklepy, un servidor y un token
personal en la variable de entorno SPECKLE_TOKEN. No se ejecuta en el
pipeline: el repositorio no guarda credenciales.
"""

import json
import os
from pathlib import Path

from .ifc import _guid


def malla_speckle(geo, app_id, propiedades):
    caras = []
    for f in geo.F:
        caras += [len(f), *f]
    return {"speckle_type": "Objects.Geometry.Mesh", "applicationId": app_id, "units": "m",
            "vertices": [round(float(x), 5) for x in geo.V.ravel()], "faces": caras,
            "properties": propiedades}


def objeto_obra(obra):
    g = obra.grafo
    piezas = []
    for nid in g.piezas():
        d = g.nodos[nid]
        props = {k: d[k] for k in ("tipo", "hilada", "sector", "nivel", "masa_kg", "volumen_m3",
                                   "metodo_recomendado", "orden_montaje", "requiere_cimbra") if k in d}
        props["ifc_globalid"] = _guid(f"{obra.id}/{nid}")
        piezas.append(malla_speckle(g.geometrias[nid], f"{obra.id}/{nid}", props))
    juntas = [{"speckle_type": "Base", "applicationId": f"{obra.id}/{a}/{b}", "origen": a, "destino": b,
               **{k: v for k, v in d.items() if k in ("tipo", "area_m2", "inclinacion_deg")}}
              for (a, b), d in sorted(g.aristas.items())]
    return {"speckle_type": "Base", "applicationId": f"obra/{obra.id}", "name": obra.nombre,
            "units": "m", "tradicion": obra.tradicion, "genoma": obra.genoma,
            "equilibrio": {k: obra.analisis.get("estructura", {}).get(k) for k in ("admisible", "GSF", "metodo")},
            "@piezas": piezas, "@juntas": juntas}


def escribir(obra, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(objeto_obra(obra), ensure_ascii=False), encoding="utf-8")


def enviar(obra, proyecto_id, modelo_id, servidor="https://app.speckle.systems", mensaje="ESTM"):
    """Envía la obra a Speckle (specklepy >= 2.17). No probado en el pipeline: requiere red y token."""
    from specklepy.api import operations
    from specklepy.api.client import SpeckleClient
    from specklepy.objects import Base
    from specklepy.transports.server import ServerTransport

    token = os.environ["SPECKLE_TOKEN"]
    cliente = SpeckleClient(host=servidor)
    cliente.authenticate_with_token(token)
    raiz = Base.of_type("Base", **{k: v for k, v in objeto_obra(obra).items() if not k.startswith("@")})
    datos = objeto_obra(obra)
    raiz["@piezas"] = [Base.of_type("Objects.Geometry.Mesh", **m) for m in datos["@piezas"]]
    raiz["@juntas"] = [Base(**j) for j in datos["@juntas"]]
    transporte = ServerTransport(stream_id=proyecto_id, client=cliente)
    obj_id = operations.send(raiz, [transporte])
    return cliente.commit.create(stream_id=proyecto_id, object_id=obj_id, branch_name=modelo_id, message=mensaje)
