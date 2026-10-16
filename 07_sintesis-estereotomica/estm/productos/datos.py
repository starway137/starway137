"""Tablas de obra: despiece (lista de piezas / BOM), puntos de replanteo y
piezas en JSON (fuente única para el visor, SketchUp y Grasshopper)."""

import csv
import json
from pathlib import Path

import numpy as np


def puntos_replanteo(obra):
    """Puntos de replanteo numerados.

    V   vértices de la planta en la línea de impostas (z = 0)
    A   arranques: centroide y cota inferior de cada jarja
    C   claves: centroide (cota de clave)
    N   extremos de las trazas de nervios en planta, con su cota de intradós
    K   cimbras: intradós a lo largo del eje de cada sector, en cada hilada
    """
    sup, g = obra.superficie, obra.grafo
    P = []

    def add(pref, x, y, z, desc):
        P.append({"id": f"{pref}{sum(p['id'][0] == pref for p in P) + 1:03d}", "x": round(float(x), 4),
                  "y": round(float(y), 4), "z": round(float(z), 4), "descripcion": desc})
    for i, v in enumerate(sup.vertices()):
        add("V", v[0], v[1], 0.0, f"vértice {i} de la planta (línea de impostas)")
    for nid in g.piezas():
        d = g.nodos[nid]
        if d["tipo"] == "jarja":
            c = d["centroide"]
            add("A", c[0], c[1], g.geometrias[nid].V[:, 2].min(), f"arranque {nid} (cota de asiento)")
    for nid in g.piezas():
        d = g.nodos[nid]
        if d["tipo"] == "clave":
            c = d["centroide"]
            add("C", c[0], c[1], c[2], f"clave {nid} (centroide)")
    vistos = set()
    for fam, a, b in obra.meta.get("nervios_planta", []):
        for q in (a, b):
            k = (round(q[0], 3), round(q[1], 3))
            if k in vistos:
                continue
            vistos.add(k)
            add("N", q[0], q[1], float(sup.z(np.array([q[0] * 0.999]), np.array([q[1] * 0.999]))[0]),
                f"nervio {fam}: punto de traza")
    K = int(obra.genoma.get("despiece", 8))
    normales = sup.normales_lado()
    for s, nrm in enumerate(normales):
        for k in range(K + 1):
            q = sup.A * k / K
            x, y = q * nrm * 0.999
            add("K", x, y, float(sup.z(np.array([x]), np.array([y]))[0]), f"cimbra del sector {s}, hilada {k}")
    return P


def escribir_replanteo(puntos, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "x", "y", "z", "descripcion"])
        w.writeheader()
        w.writerows(puntos)
    return [Path(ruta)]


def despiece(obra, ruta, clases):
    clase_de = {nid: c["clase"] for c in clases for nid in c["ids"]}
    g = obra.grafo
    campos = ["id", "tipo", "clase", "hilada", "sector", "orden_montaje", "volumen_m3", "masa_kg",
              "largo_m", "ancho_m", "grueso_m", "cx", "cy", "cz", "metodo_recomendado", "cnc_ok", "cnc_fallos",
              "3dcp_ok", "3dcp_fallos", "requiere_cimbra"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(campos)
        for nid in sorted(g.piezas(), key=lambda n: g.nodos[n].get("orden_montaje", 0)):
            d = g.nodos[nid]
            e = d["extensiones_m"]
            c = d["centroide"]
            fc, f3 = d.get("fab_cnc", {}), d.get("fab_3dcp", {})
            w.writerow([nid, d["tipo"], clase_de.get(nid, ""), d.get("hilada", ""), d.get("sector", ""),
                        d.get("orden_montaje", ""), f"{d['volumen_m3']:.5f}", f"{d.get('masa_kg', 0):.1f}",
                        e[0], e[1], e[2], c[0], c[1], c[2], d.get("metodo_recomendado", ""),
                        int(bool(fc.get("ok"))), "|".join(fc.get("fallos", [])), int(bool(f3.get("ok"))),
                        "|".join(f3.get("fallos", [])), int(bool(d.get("requiere_cimbra")))])
    return [Path(ruta)]


def piezas_json(obra, ruta):
    g = obra.grafo
    est = obra.analisis.get("estructura", {})
    datos = {"obra": obra.id, "nombre": obra.nombre, "unidades": "m", "eje_vertical": "z",
             "genoma": obra.genoma, "equilibrio": {"admisible": est.get("admisible"), "GSF": est.get("GSF"),
                                                   "metodo": est.get("metodo")},
             "piezas": [{"id": nid, "tipo": g.nodos[nid]["tipo"], "orden": g.nodos[nid].get("orden_montaje", 0),
                         "masa_kg": round(g.nodos[nid].get("masa_kg", 0.0), 1),
                         "metodo": g.nodos[nid].get("metodo_recomendado", ""),
                         "V": np.round(g.geometrias[nid].V, 4).tolist(), "F": g.geometrias[nid].F}
                        for nid in g.piezas()],
             "juntas": [[a, b, d["tipo"]] for (a, b), d in sorted(g.aristas.items())
                        if a in g.geometrias and b in g.geometrias]}
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return [Path(ruta)]
