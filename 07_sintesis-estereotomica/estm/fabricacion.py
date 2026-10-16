"""Restricciones de fabricación digital por pieza (DfAM).

Dos rutas contemporáneas para materializar las piezas del grafo:

  piedra_cnc   corte con disco/hilo y fresado de 5 ejes de sillares
               - envolvente de máquina y masa manipulable
               - aprovechamiento del bloque (volumen pieza / caja orientada)
               - planeidad de juntas (la estereotomía exige juntas planas)
               - ángulo diedro mínimo (aristas agudas = rotura, "pico de flauta")
  3dcp         impresión 3D de hormigón por capas
               - envolvente de impresión
               - voladizo máximo sin soporte, con la mejor orientación de
                 impresión entre las direcciones principales de la pieza
               - espesor mínimo (>= 2 cordones)

Los umbrales son parámetros de proyecto por defecto, editables por obra.
"""

import numpy as np

CNC = {"envolvente_m": (3.5, 2.0, 1.5), "masa_max_kg": 6000.0, "aprovechamiento_min": 0.25,
       "planeidad_max_m": 0.003, "diedro_min_deg": 35.0}
TDCP = {"envolvente_m": (2.5, 2.5, 2.0), "voladizo_max_deg": 25.0, "espesor_min_m": 0.08,
        "diedro_min_deg": 20.0}

CARAS_JUNTA = {"plemento": [2, 3, 4, 5], "celda_mocarabe": [2, 3, 4, 5], "dovela_nervio": [0, 1]}


def _cabe(ext, env):
    return all(a <= b + 1e-9 for a, b in zip(sorted(ext, reverse=True), sorted(env, reverse=True)))


def cnc(geo, masa, tipo, p=CNC):
    vol, _ = geo.volumen_centroide()
    ext, _ = geo.caja_orientada()
    aprov = vol / max(np.prod(ext), 1e-12)
    caras = CARAS_JUNTA.get(tipo, [])
    planeidad = max([geo.planaridad(i) for i in caras], default=0.0)
    diedro = geo.diedro_minimo()
    fallos = []
    if not _cabe(ext, p["envolvente_m"]):
        fallos.append("envolvente")
    if masa > p["masa_max_kg"]:
        fallos.append("masa")
    if aprov < p["aprovechamiento_min"]:
        fallos.append("aprovechamiento")
    if planeidad > p["planeidad_max_m"]:
        fallos.append("planeidad_juntas")
    if diedro < p["diedro_min_deg"]:
        fallos.append("diedro_agudo")
    return {"ok": not fallos, "fallos": fallos, "aprovechamiento": float(aprov),
            "planeidad_juntas_mm": float(planeidad * 1000), "diedro_min_deg": float(diedro)}


def _voladizo(geo, b):
    """Voladizo máximo (grados desde la vertical) imprimiendo según la dirección b."""
    alturas = geo.V @ b
    base = alturas.min()
    peor = 0.0
    for i, f in enumerate(geo.F):
        area, n = geo.area_normal(i)
        if area < 1e-9:
            continue
        hacia_abajo = -np.dot(n, b)
        if hacia_abajo <= 1e-6:
            continue
        if np.all(alturas[f] - base < 1e-6):          # cara apoyada en la cama de impresión
            continue
        peor = max(peor, float(np.degrees(np.arcsin(min(1.0, hacia_abajo)))))
    return peor


def impresion_3d(geo, p=TDCP):
    ext, ejes = geo.caja_orientada()
    candidatos = [(f"+eje{i}", s * ejes[i]) for i in range(3) for s in (1, -1)]
    candidatos += [("+z", np.array([0, 0, 1.0])), ("-z", np.array([0, 0, -1.0]))]
    voladizos = {nombre: _voladizo(geo, b) for nombre, b in candidatos}
    mejor = min(voladizos, key=voladizos.get)
    fallos = []
    if not _cabe(ext, p["envolvente_m"]):
        fallos.append("envolvente")
    if voladizos[mejor] > p["voladizo_max_deg"]:
        fallos.append("voladizo")
    if ext[2] < p["espesor_min_m"]:
        fallos.append("espesor_minimo")
    if geo.diedro_minimo() < p["diedro_min_deg"]:
        fallos.append("diedro_agudo")
    return {"ok": not fallos, "fallos": fallos, "orientacion": mejor,
            "voladizo_deg": voladizos[mejor], "espesor_min_m": float(ext[2])}


def evaluar_obra(grafo, cnc_p=CNC, tdcp_p=TDCP):
    """Evalúa todas las piezas, anota el grafo y devuelve el resumen por ruta."""
    resumen = {"piedra_cnc": {"ok": 0, "fallos": {}}, "3dcp": {"ok": 0, "fallos": {}}, "piezas": 0}
    for nid in grafo.piezas():
        d = grafo.nodos[nid]
        geo = grafo.geometrias[nid]
        rc = cnc(geo, d.get("masa_kg", 0.0), d["tipo"], cnc_p)
        r3 = impresion_3d(geo, tdcp_p)
        d["fab_cnc"] = rc
        d["fab_3dcp"] = r3
        if rc["ok"]:
            d["metodo_recomendado"] = "piedra_cnc"
        elif r3["ok"]:
            d["metodo_recomendado"] = "3dcp"
        else:
            d["metodo_recomendado"] = "revisar"
        resumen["piezas"] += 1
        for ruta, r in (("piedra_cnc", rc), ("3dcp", r3)):
            resumen[ruta]["ok"] += r["ok"]
            for f in r["fallos"]:
                resumen[ruta]["fallos"][f] = resumen[ruta]["fallos"].get(f, 0) + 1
    for ruta in ("piedra_cnc", "3dcp"):
        resumen[ruta]["fraccion_ok"] = resumen[ruta]["ok"] / max(resumen["piezas"], 1)
    revisar = sum(1 for n in grafo.piezas() if grafo.nodos[n]["metodo_recomendado"] == "revisar")
    resumen["fraccion_fabricable"] = 1 - revisar / max(resumen["piezas"], 1)
    return resumen


def secuencia_montaje(grafo):
    """Orden de colocación: desde los apoyos hacia arriba, por adyacencia.

    Marca requiere_cimbra en piezas con juntas no horizontales (dovelas,
    plementos de juntas radiales, nervios): sólo son estables al cerrarse el
    arco. Las celdas voladas con lechos horizontales se montan sin cimbra si
    el voladizo es pequeño (comprobado en el análisis de la rebanada).
    """
    ady = grafo.lista_adyacencia()
    colocadas = {n for n, d in grafo.nodos.items() if d["tipo"] == "apoyo"}
    pendientes = set(grafo.piezas())
    orden = []
    while pendientes:
        frontera = [n for n in pendientes if any(v in colocadas for v, _ in ady[n])]
        if not frontera:
            frontera = list(pendientes)
        siguiente = min(frontera, key=lambda n: (grafo.nodos[n]["centroide"][2], n))
        orden.append(siguiente)
        colocadas.add(siguiente)
        pendientes.discard(siguiente)
    for i, n in enumerate(orden):
        d = grafo.nodos[n]
        d["orden_montaje"] = i
        juntas = [t for _, t in ady[n]]
        d["requiere_cimbra"] = bool(any(t in ("junta_radial", "encuentro_clave") for t in juntas))
    return orden
