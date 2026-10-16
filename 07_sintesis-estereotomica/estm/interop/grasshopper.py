"""Grasshopper: carga útil JSON para el componente de script de Rhino 8.

El script grasshopper/importar_estm.py lee este archivo y reconstruye mallas,
atributos y el grafo (líneas entre centroides) como árboles de datos. Es el
camino sin servidor; con servidor se usa el conector de Speckle (speckle.py).
"""

import json
from pathlib import Path

from .ifc import _guid


def carga(obra):
    g = obra.grafo
    piezas = []
    for nid in g.piezas():
        d = g.nodos[nid]
        geo = g.geometrias[nid]
        piezas.append({"id": nid, "guid": _guid(f"{obra.id}/{nid}"), "tipo": d["tipo"],
                       "vertices": [[round(float(c), 5) for c in v] for v in geo.V], "caras": geo.F,
                       "centroide": d["centroide"], "masa_kg": d.get("masa_kg"),
                       "metodo": d.get("metodo_recomendado"), "orden_montaje": d.get("orden_montaje"),
                       "cimbra": d.get("requiere_cimbra")})
    aristas = [{"u": a, "v": b, "tipo": d["tipo"]} for (a, b), d in sorted(g.aristas.items())
               if a in g.geometrias and b in g.geometrias]
    return {"formato": "ESTM-GH/1", "unidades": "m", "obra": obra.id, "nombre": obra.nombre,
            "tradicion": obra.tradicion, "piezas": piezas, "aristas": aristas,
            "equilibrio": obra.analisis.get("estructura", {}).get("GSF")}


def escribir(obra, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text(json.dumps(carga(obra), ensure_ascii=False), encoding="utf-8")
