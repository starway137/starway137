"""Pipeline ESTM: análisis, aprendizaje continuo, síntesis cruzada e interoperabilidad.

    1. Ingesta: catálogo -> gramática paramétrica -> grafo atribuido G = (V, E)
    2. Verificación: límite inferior de Heyman (arco / TNA / cortes / rebanada)
    3. Fabricación: DfAM piedra CNC y 3DCP + secuencia de montaje
    4. Patrones: firmas WL + espectro; ingesta episódica en el diccionario
    5. Síntesis: slerp entre genomas de tradiciones distintas; los híbridos se
       verifican, se reparan con la mínima corrección de espesor y se
       ingieren como episodios nuevos (el diccionario crece sin olvidar)
    6. Entregables: IFC 4.3 + IDS validado, Speckle, Grasshopper, SVG, informe

Uso:  python3 pipeline.py            (todo)
      python3 pipeline.py --rapido   (sin síntesis: obras del catálogo)
      python3 pipeline.py --interop-todo  (cargas Speckle/GH de todas las obras)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from estm import analisis, fabricacion, latente, patrones, vista  # noqa: E402
from estm.generadores import arco_dovelas, boveda_poligonal  # noqa: E402
from estm.interop import grasshopper, ids, ifc, speckle  # noqa: E402
from estm.memoria import DiccionarioPatrones  # noqa: E402

SALIDAS = RAIZ / "salidas"
LOCAL = SALIDAS / "local"                              # cargas pesadas, no versionadas
ESCALAS = [0.5, 0.3, 0.25, 0.25, 0.25] + [0.35] * 8    # escalas fijas de los descriptores
UMBRAL = 1.0
GSF_OBJETIVO = 1.5
MAX_REPARACIONES = 5


def _json(ruta, obj, compacto=False):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = (json.dumps(_red(obj), ensure_ascii=False, separators=(",", ":")) if compacto
             else json.dumps(_red(obj), ensure_ascii=False, indent=1))
    ruta.write_text(texto + "\n", encoding="utf-8")


def _red(o):
    if isinstance(o, (float, np.floating)):
        return float(f"{float(o):.6g}") if np.isfinite(o) else None
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, dict):
        return {k: _red(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [_red(v) for v in o]
    if isinstance(o, np.ndarray):
        return _red(o.tolist())
    return o


# ------------------------------------------------------------------ construcción y análisis
def construir(e, material=None):
    if e["tipo"] == "arco":
        return arco_dovelas(e["id"], e["nombre"], e["tradicion"], e["luz"], e["apuntamiento"], e["espesor"],
                            e["dovelas_semiarco"], e["inclinacion_junta"], material=material or e["material"],
                            meta={"fuente": e.get("fuente"), "calidad": e.get("calidad")})
    o = boveda_poligonal(e["id"], e["nombre"], e["tradicion"], e["genoma"], e["luz"],
                         material=material or e["material"],
                         meta={"fuente": e.get("fuente"), "calidad": e.get("calidad")})
    o.meta["relleno_rel"] = e.get("relleno_rel", 0.0)
    return o


def analizar(o):
    o.analisis["estructura"] = analisis.estructura(o)
    o.analisis["fabricacion"] = fabricacion.evaluar_obra(o.grafo)
    fabricacion.secuencia_montaje(o.grafo)
    o.analisis["grafo"] = o.grafo.resumen()
    return o


def escribir_obra(o, carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    _json(carpeta / "grafo.json", o.grafo.a_dict(con_geometria=False), compacto=True)
    _json(carpeta / "analisis.json", {"id": o.id, "nombre": o.nombre, "tradicion": o.tradicion,
                                      "genoma": o.genoma, "meta": o.meta, **o.analisis})
    est = o.analisis["estructura"]
    vista.axonometria(o.grafo, carpeta / "axonometria.svg",
                      titulo=f"{o.id} · {o.nombre} · GSF {est['GSF']:.2f} ({est['metodo']})")
    sec = o.meta.get("_seccion_dibujo")
    if sec:
        juntas, polis, linea = sec
        vista.seccion_empujes(juntas, polis, linea, carpeta / "seccion_empujes.svg",
                              titulo=f"{o.id} · sección de verificación ({est['metodo']})")


# ------------------------------------------------------------------ síntesis cruzada
def hibrido(e_a, e_b, t, material, n):
    ga, gb = e_a["genoma"], e_b["genoma"]
    genoma = latente.decodificar(latente.slerp(latente.codificar(ga), latente.codificar(gb), t))
    luz = round((1 - t) * e_a["luz"] + t * e_b["luz"], 2)
    hid = f"HX-{e_a['id']}-{e_b['id']}-{int(round(100 * t)):03d}"
    e = {"id": hid, "tipo": "boveda", "nombre": f"Híbrido {e_a['id']}→{e_b['id']} t={t:.2f}",
         "tradicion": f"hibrido:{e_a['tradicion']}+{e_b['tradicion']}", "luz": luz, "material": material,
         "relleno_rel": (1 - t) * e_a.get("relleno_rel", 0) + t * e_b.get("relleno_rel", 0),
         "genoma": genoma, "fuente": f"slerp(z_{e_a['id']}, z_{e_b['id']}, {t})", "calidad": "propuesta"}
    traza = []
    o = analizar(construir(e))
    for _ in range(MAX_REPARACIONES):
        est = o.analisis["estructura"]
        if est["admisible"] and est["GSF"] >= GSF_OBJETIVO:
            break
        nuevo = min(e["genoma"]["espesor_rel"] * 1.25, latente.HI[latente.NOMBRES.index("espesor_rel")])
        if nuevo <= e["genoma"]["espesor_rel"] + 1e-9:
            traza.append("espesor en su cota máxima: no se puede reparar más")
            break
        traza.append(f"GSF {est['GSF']:.2f} < {GSF_OBJETIVO}: espesor_rel {e['genoma']['espesor_rel']:.4f} -> {nuevo:.4f}")
        e["genoma"] = dict(e["genoma"], espesor_rel=nuevo)
        o = analizar(construir(e))
    o.meta["reparacion"] = traza
    o.meta["genoma_slerp"] = genoma
    o.meta["t"] = t
    return e, o


# ------------------------------------------------------------------ principal
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--interop-todo", action="store_true")
    args = ap.parse_args(argv)
    t0 = time.time()
    cat = json.loads((RAIZ / "obras" / "catalogo.json").read_text(encoding="utf-8"))
    por_id = {e["id"]: e for e in cat["obras"]}

    print("[1-3] Obras del catálogo: grafo, equilibrio, fabricación")
    obras = []
    for e in cat["obras"]:
        o = analizar(construir(e))
        escribir_obra(o, SALIDAS / "obras" / o.id)
        est = o.analisis["estructura"]
        print(f"   {o.id:7s} {o.grafo.resumen()['piezas']:4d} piezas · admisible={est['admisible']} "
              f"GSF={est['GSF']:.2f} ({est['metodo']}) · fabricable={o.analisis['fabricacion']['fraccion_fabricable']:.0%}")
        obras.append(o)

    print("[4] Patrones y memoria episódica")
    dicc = DiccionarioPatrones(umbral=UMBRAL, escalas=ESCALAS)
    episodios = []
    for o in obras:
        episodios.append(dicc.ingerir(o.id, o.tradicion, patrones.descriptores_piezas(o.grafo)))
    emb = {o.id: patrones.embedding_obra(o.grafo) for o in obras}

    hibridos = []
    if not args.rapido:
        print("[5] Síntesis cruzada por slerp")
        for par in cat["sintesis"]:
            for t in par["t"]:
                e, o = hibrido(por_id[par["a"]], por_id[par["b"]], t, par["material"], len(hibridos))
                escribir_obra(o, SALIDAS / "sintesis" / o.id)
                est = o.analisis["estructura"]
                print(f"   {o.id}: n={int(o.genoma['orden_radial'])} β={o.genoma['beta_superficie']:.2f} "
                      f"j={o.genoma['inclinacion_junta']:.2f} moc={o.genoma['mocarabe_rel']:.2f} · "
                      f"GSF={est['GSF']:.2f} ({est['metodo']}) · reparaciones={len(o.meta['reparacion'])}")
                episodios.append(dicc.ingerir(o.id, o.tradicion, patrones.descriptores_piezas(o.grafo)))
                emb[o.id] = patrones.embedding_obra(o.grafo)
                hibridos.append(o)

    mem = SALIDAS / "memoria"
    mem.mkdir(parents=True, exist_ok=True)
    dicc.guardar(mem / "diccionario.json", mem / "eventos.jsonl")
    repro = DiccionarioPatrones.reproducir(mem / "eventos.jsonl", umbral=UMBRAL, escalas=ESCALAS)
    reproducible = json.dumps(_red(repro.a_dict()), sort_keys=True) == json.dumps(_red(dicc.a_dict()), sort_keys=True)
    ids_obras = list(emb)
    M = np.array([[patrones.similitud(emb[a], emb[b]) for b in ids_obras] for a in ids_obras])
    transv = dicc.transversales()
    _json(mem / "resumen.json", {
        "episodios": episodios, "prototipos": len(dicc.prototipos), "piezas_ingeridas": dicc.n_items(),
        "retencion_memoria": dicc.verificar_memoria(), "reproducible_desde_eventos": reproducible,
        "patrones_transversales": [{"id": p["id"], "tipo": p["tipo"], "n": p["n"], "tradiciones": p["tradiciones"]}
                                   for p in transv],
        "similitud_obras": {"ids": ids_obras, "matriz": M.round(4).tolist()},
    })
    print(f"   {len(dicc.prototipos)} prototipos · {dicc.n_items()} piezas · retención={dicc.verificar_memoria():.3f} "
          f"· reproducible={reproducible} · transversales={len(transv)}")

    print("[6] Entregables OpenBIM e interoperabilidad")
    carpeta_ifc = SALIDAS / "ifc"
    ruta_ids = carpeta_ifc / "estm_lod400.ids"
    ids.escribir(ruta_ids)
    lotes = [("catalogo_historico", obras)]
    validos = [o for o in hibridos if o.analisis["estructura"]["admisible"]]
    if validos:
        lotes.append(("sintesis_hibridos", validos))
    validaciones = []
    for nombre, lote in lotes:
        ruta = LOCAL / f"{nombre}.ifc"
        ifc.exportar(lote, ruta, nombre_proyecto=f"ESTM · {nombre}")
        res = ifc.resumen(ruta)
        val = ids.validar(ruta_ids, ruta)
        ifc.comprimir(ruta).replace(carpeta_ifc / f"{nombre}.ifczip")
        validaciones.append({"lote": nombre, **res, "ids": val})
        print(f"   {nombre}: {res['piezas']} piezas · {res['juntas']} juntas · IDS cumple={val['cumple']}")
    _json(carpeta_ifc / "validacion.json", validaciones)
    destino_interop = SALIDAS / "interop"
    ejemplos = obras if args.interop_todo else [o for o in obras if o.id == "GO-CR4"]
    for o in ejemplos:
        speckle.escribir(o, destino_interop / f"{o.id}_speckle.json")
        grasshopper.escribir(o, destino_interop / f"{o.id}_gh.json")

    _json(SALIDAS / "resumen.json", {
        "obras": [{"id": o.id, "nombre": o.nombre, "tradicion": o.tradicion, **_fila(o)} for o in obras],
        "hibridos": [{"id": o.id, "t": o.meta["t"], "genoma": o.genoma, "reparacion": o.meta["reparacion"],
                      **_fila(o)} for o in hibridos],
        "memoria": {"prototipos": len(dicc.prototipos), "retencion": dicc.verificar_memoria(),
                    "transversales": len(transv), "reproducible": reproducible},
        "ifc": validaciones,
    })
    informe(obras, hibridos, dicc, validaciones, reproducible)
    print(f"Pipeline ESTM completado en {time.time() - t0:.0f} s")


def _fila(o):
    est, fab, g = o.analisis["estructura"], o.analisis["fabricacion"], o.analisis["grafo"]
    return {"piezas": g["piezas"], "juntas": g["aristas"], "masa_t": g["masa_total_kg"] / 1000,
            "admisible": est["admisible"], "GSF": est["GSF"], "metodo": est["metodo"],
            "metodos": {m["metodo"]: {"admisible": m.get("admisible"), "GSF": m.get("GSF")} for m in est["metodos"]},
            "cnc_ok": fab["piedra_cnc"]["fraccion_ok"], "tdcp_ok": fab["3dcp"]["fraccion_ok"],
            "fabricable": fab["fraccion_fabricable"]}


def informe(obras, hibridos, dicc, validaciones, reproducible):
    L = ["# Resultados ESTM (generado automáticamente)", "",
         "> Generado por `pipeline.py`. No editar a mano.", "",
         "## 1. Obras del catálogo", "",
         "| Obra | Piezas | Juntas | Masa (t) | Equilibrio (mejor método) | GSF | Métodos | CNC ok | 3DCP ok | Fabricable |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for o in obras + hibridos:
        if o is (hibridos[0] if hibridos else None):
            L += ["", "## 2. Síntesis cruzada (slerp)", "",
                  "| Híbrido | t | n | β | j | mocárabe | Piezas | Admisible | GSF | Métodos | Reparación | Fabricable |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        f = _fila(o)
        met = ", ".join(f"{k}: {'sí' if v['admisible'] else 'no'} ({(v['GSF'] or 0):.2f})" for k, v in f["metodos"].items())
        if o in hibridos:
            gm = o.genoma
            L.append(f"| {o.id} | {o.meta['t']:.2f} | {int(gm['orden_radial'])} | {gm['beta_superficie']:.2f} | "
                     f"{gm['inclinacion_junta']:.2f} | {gm['mocarabe_rel']:.2f} | {f['piezas']} | "
                     f"{'sí' if f['admisible'] else 'no'} | {f['GSF']:.2f} | {met} | "
                     f"{len(o.meta['reparacion'])} pasos | {f['fabricable']:.0%} |")
        else:
            L.append(f"| {o.id} {o.nombre} | {f['piezas']} | {f['juntas']} | {f['masa_t']:.1f} | "
                     f"{'admisible' if f['admisible'] else 'no encontrado'} ({f['metodo']}) | {f['GSF']:.2f} | {met} | "
                     f"{f['cnc_ok']:.0%} | {f['tdcp_ok']:.0%} | {f['fabricable']:.0%} |")
    L += ["", "## 3. Memoria episódica", "",
          f"- Prototipos: {len(dicc.prototipos)} · piezas ingeridas: {dicc.n_items()}",
          f"- Retención de la memoria (ejemplares que siguen en su prototipo): {dicc.verificar_memoria():.3f}",
          f"- Estado reproducible desde el registro de eventos: {reproducible}",
          f"- Patrones transversales (compartidos por ≥ 2 tradiciones): {len(dicc.transversales())}", "",
          "| Prototipo | Tipo de pieza | n | Tradiciones |", "|---|---|---|---|"]
    for p in sorted(dicc.transversales(), key=lambda p: -p["n"])[:12]:
        L.append(f"| {p['id']} | {p['tipo']} | {p['n']} | {', '.join(f'{k} ({v})' for k, v in p['tradiciones'].items())} |")
    L += ["", "## 4. Entregables OpenBIM", "", "| Lote | Piezas | Juntas (IfcRelConnectsElements) | Psets | IDS |",
          "|---|---|---|---|---|"]
    for v in validaciones:
        L.append(f"| {v['lote']} | {v['piezas']} | {v['juntas']} | {v['psets']} | "
                 f"{'cumple' if v['ids']['cumple'] else 'NO cumple'} "
                 f"({', '.join(str(s['aprobadas']) + '/' + str(s['aplicables']) for s in v['ids']['especificaciones'])}) |")
    (SALIDAS / "informe.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
