"""Verificación ciega: ¿procesa el algoritmo obras NUEVAS de alta complejidad?

Protocolo (cada paso tiene un criterio de aceptación explícito, CRITERIOS):

  0. Referencias  las bóvedas del catálogo se convierten en mallas sin
                  semántica; el clasificador de piezas aprende sus tipos y el
                  selector calibra su umbral de complejidad.
  1. Entrada      obras nuevas (obras/nuevas.json) y controles negativos
                  llegan como mallas: nombres neutros, orden barajado, giro y
                  traslación arbitrarios, ruido de levantamiento de 1.5 mm.
  2. Grafo        contactos detectados geométricamente (precisión/exhaustividad
                  frente al grafo del generador).
  3. Selección    índice de complejidad + condiciones mínimas: las obras del
                  corpus deben entrar, los controles deben quedar fuera.
  4. Interpretación  tipos de pieza (memoria episódica, con detección de
                  novedad) y genoma por ingeniería inversa.
  5. Regeneración el genoma inferido reconstruye la obra con la gramática;
                  fidelidad geométrica pieza a pieza.
  6. Equilibrio   Heyman sobre la obra verdadera y sobre la reconstruida:
                  el veredicto y el GSF deben coincidir (la interpretación
                  conserva lo que decide la seguridad).
  7. Autoaprendizaje  los tipos autocorregidos (nervios bajo el intradós,
                  plementos sobre él, mocárabes en anillos completos; SIN usar
                  la verdad) se ingieren en la memoria y la obra pasa a ser
                  referencia. Se comprueba que no se
                  olvida nada (retención = 1) y que un segundo levantamiento de
                  la misma obra se interpreta igual o mejor.
  8. Cruce        cada obra nueva se cruza (slerp) con su referencia más
                  afín; el híbrido se verifica, se repara y se exporta como
                  productos (DXF, DAE/GLB/OBJ/STL, CSV de replanteo, IFC,
                  visor HTML, script de SketchUp).

Uso:  python3 verificacion.py                 (todo, ~6 min)
      python3 verificacion.py --sin-productos (pasos 0-7)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

import pipeline  # noqa: E402
from estm import ingesta, productos, seleccion  # noqa: E402
from estm import interpretacion as it  # noqa: E402
from estm.generadores import controles  # noqa: E402

SALIDA = pipeline.SALIDAS / "verificacion"
LOCAL = pipeline.LOCAL / "productos"
SEMILLA = 20261016

CRITERIOS = {
    "grafo_precision": (">=", 0.85, "contactos detectados en la malla alterada que existen en la malla original"),
    "grafo_exhaustividad": (">=", 0.70, "contactos de la malla original que se detectan tras la alteración"),
    "acierto_tipos": (">=", 0.90, "piezas con tipo correcto tras la autocorrección (memoria previa a la obra)"),
    "orden_radial": ("==", 1, "orden del polígono de planta"),
    "salto_estrella": ("==", 1, "polígono estrellado de nervios {n/k}"),
    "terceletes": ("==", 1, "presencia de terceletes y ligaduras"),
    "d_apuntamiento": ("<=", 0.15, "apuntamiento"),
    "d_beta_superficie": ("<=", 0.15, "arista (0) frente a cúpula (1)"),
    "d_inclinacion_junta": ("<=", 0.15, "regla de juntas: lecho horizontal (0) o normal (1)"),
    "d_mocarabe_rel": ("<=", 0.10, "extensión de la zona de mocárabes"),
    "err_rel_espesor": ("<=", 0.15, "espesor de la cáscara"),
    "err_rel_canto": ("<=", 0.20, "canto de los nervios"),
    "d_despiece": ("<=", 2, "hiladas por semiluz"),
    "fidelidad_geometrica": ("<=", 0.03, "mediana de la distancia entre piezas ciegas y reconstruidas / L"),
    "veredicto_igual": ("==", 1, "admisible / no encontrado, igual en la obra verdadera y en la reconstruida"),
    "err_rel_GSF": ("<=", 0.20, "error relativo del factor geométrico de seguridad"),
}


def _cumple(op, umbral, valor, eps=1e-9):
    return {"==": abs(valor - umbral) <= eps, ">=": valor >= umbral - eps, "<=": valor <= umbral + eps}[op]


# ------------------------------------------------------------------ medidas
def metricas_grafo(g_ciego, verdad, piezas_orig, g_orig, area_min=2e-3):
    """Robustez de la detección de contactos al giro, la traslación y el ruido:
    precisión y exhaustividad frente a los contactos geométricos de las mallas
    SIN alterar (misma regla y misma tolerancia). Se informa además qué parte
    de las juntas físicas del generador se recupera."""
    det = {tuple(sorted((verdad[a], verdad[b]))) for a, b in g_ciego.aristas}
    ref = {tuple(sorted((a, b))) for a, b, _ in ingesta.detectar_contactos(piezas_orig)}
    fisicas = {tuple(sorted(k)) for k, d in g_orig.aristas.items() if d.get("area_m2", 0) >= area_min}
    return {"detectadas": len(det), "referencia_geometrica": len(ref),
            "precision": len(det & ref) / max(len(det), 1), "exhaustividad": len(det & ref) / max(len(ref), 1),
            "juntas_generador_recuperadas": len(det & fisicas) / max(len(fisicas), 1)}


def _centroides(g):
    ids = g.piezas()
    return ids, np.array([g.nodos[n]["centroide"] for n in ids])


def pseudo_etiquetas(g, mc, diag, o_reg):
    """Lleva las piezas ciegas al marco de la gramática y toma el tipo de la
    pieza reconstruida más cercana. No usa la verdad."""
    ids_b, Cb = _centroides(g)
    ids_r, Cr = _centroides(o_reg.grafo)
    z_r = min(geo.V[:, 2].min() for geo in o_reg.grafo.geometrias.values())
    P = np.column_stack([it._rot(Cb[:, :2] - mc["centro"], -diag["giro_rad"]), Cb[:, 2] - mc["z0"] + z_r])
    d = np.sqrt(((P[:, None, :] - Cr[None, :, :]) ** 2).sum(-1))
    cerca = d.argmin(axis=1)
    L = mc["L"]
    etiquetas = {n: o_reg.grafo.nodos[ids_r[i]]["tipo"] for n, i in zip(ids_b, cerca)}
    ida = float(np.median(d.min(axis=1)) / L)
    vuelta = float(np.median(d.min(axis=0)) / L)
    return etiquetas, {"ciega_a_reconstruida": ida, "reconstruida_a_ciega": vuelta,
                       "fidelidad": max(ida, vuelta), "piezas_ciegas": len(ids_b), "piezas_reconstruidas": len(ids_r)}


def acierto(pred, verdad_tipos):
    return float(np.mean([pred[n] == verdad_tipos[n] for n in pred]))


def comparar_equilibrio(o_v, o_r):
    ev, er = o_v.analisis["estructura"], o_r.analisis["estructura"]
    igual = int(ev["admisible"] == er["admisible"])
    if ev["admisible"] and er["admisible"]:
        err = abs(er["GSF"] - ev["GSF"]) / ev["GSF"]
    else:
        err = 0.0 if igual else 1.0
    return {"verdadera": {"admisible": ev["admisible"], "GSF": ev["GSF"], "metodo": ev["metodo"]},
            "reconstruida": {"admisible": er["admisible"], "GSF": er["GSF"], "metodo": er["metodo"]},
            "veredicto_igual": igual, "err_rel_GSF": err}


# ------------------------------------------------------------------ pasos
def referencias(cat, semilla):
    clf, refs = it.Clasificador(), {}
    for k, e in enumerate(x for x in cat["obras"] if x["tipo"] == "boveda"):
        o = pipeline.construir(e)
        cg, verdad, _ = ingesta.ciega(ingesta.piezas_de_grafo(o.grafo), semilla=semilla + k)
        g = ingesta.grafo_desde_mallas(e["id"], cg)
        etq = {n: o.grafo.nodos[verdad[n]]["tipo"] for n in g.piezas()}
        clf.aprender(e["id"], e["tradicion"], it.descriptores(g), etq)
        refs[e["id"]] = (g, e["genoma"], e["tradicion"])
    sel = seleccion.Selector()
    sel.calibrar(refs)
    return clf, sel, refs


def ficha_reconstruida(e, gen, diag):
    """Ficha para la gramática a partir del genoma inferido. Material y relleno de
    senos son datos declarados del levantamiento (no se deducen de las mallas)."""
    return {"id": f"{e['id']}-R", "tipo": "boveda", "nombre": f"{e['nombre']} (reconstruida)",
            "tradicion": e["tradicion"], "luz": round(diag["luz_m"], 3),
            "material": e["material"], "relleno_rel": e.get("relleno_rel", 0.0),
            "genoma": gen, "fuente": f"interpretación ciega de {e['id']}", "calidad": "reconstruida"}


def autocorregir(e, g, mc, tipos, max_iter=4):
    """Interpretación con autocorrección física (sin usar la verdad):
    tipos -> genoma -> superficie ajustada -> nervios bajo el intradós / plementos sobre él,
    celdas de mocárabe en anillos completos -> tipos corregidos ... hasta que no cambian.
    La obra se reconstruye con el genoma final y sus piezas dan las pseudo-etiquetas."""
    hist = []
    for i in range(max_iter):
        gen, diag = it.inferir_genoma(g, {n: t for n, t in tipos.items() if t != "desconocido"}, mc)
        if gen is None:
            return None, diag, hist
        nuevos, cambios = it.corregir_por_superficie(g, tipos, gen, diag, mc)
        hist.append({"iteracion": i, "cambios_de_tipo": cambios, "_tipos": tipos})
        if cambios == 0:
            break
        tipos = nuevos
    e_r = ficha_reconstruida(e, gen, diag)
    o_r = pipeline.construir(e_r)
    pseudo, fid = pseudo_etiquetas(g, mc, diag, o_r)
    return (fid, gen, diag, e_r, o_r, tipos, pseudo), None, hist


def interpretar(e, g, verdad, o_v, clf, sel):
    """Pasos 4-6 sobre una obra seleccionada. Devuelve (resultado, ficha_reconstruida, obra_reconstruida)."""
    mc = it.marco(g)
    items = it.descriptores(g, mc)
    pred, dist = clf.predecir(items, con_distancia=True)
    tipos_v = {n: o_v.grafo.nodos[verdad[n]]["tipo"] for n in g.piezas()}
    mejor, motivo, hist = autocorregir(e, g, mc, pred)
    if mejor is None:
        return {"interpretable": False, "motivo": motivo["motivo"]}, None, None
    fid, gen, diag, e_r, o_r, tipos, pseudo = mejor
    pipeline.analizar(o_r)
    errores = it.errores_genoma(gen, e["genoma"])
    eq = comparar_equilibrio(o_v, o_r)
    medidas = {"acierto_tipos": acierto(tipos, tipos_v), **errores,
               "fidelidad_geometrica": fid["fidelidad"], "veredicto_igual": eq["veredicto_igual"],
               "err_rel_GSF": eq["err_rel_GSF"], "err_rel_luz": abs(diag["luz_m"] - e["luz"]) / e["luz"]}
    res = {"interpretable": True, "medidas": medidas, "genoma_inferido": gen, "diagnostico": diag,
           "acierto_clasificador": acierto(pred, tipos_v),
           "autocorreccion": [{"iteracion": h["iteracion"], "cambios_de_tipo": h["cambios_de_tipo"],
                               "acierto_tipos": acierto(h["_tipos"], tipos_v)} for h in hist],
           "piezas_desconocidas": sum(t == "desconocido" for t in pred.values()),
           "distancia_media_prototipo": float(np.mean(list(dist.values()))),
           "acierto_pseudo_etiquetas": acierto(pseudo, tipos_v), "fidelidad": fid, "equilibrio": eq,
           "afinidad": sel.afinidad(gen)}
    res["_pseudo"], res["_items"] = tipos, items          # se aprenden los tipos autocorregidos
    return res, e_r, o_r


def evaluar_criterios(medidas):
    out = {}
    for k, (op, umbral, _) in CRITERIOS.items():
        if k in medidas:
            out[k] = bool(_cumple(op, umbral, medidas[k]))
    return out


def candidatos(nuevas):
    for e in nuevas["obras"]:
        o = pipeline.construir(e)
        yield e["id"], e["nombre"], True, e, o, ingesta.piezas_de_grafo(o.grafo)
    for cid in nuevas["controles"]:
        nombre, f = controles.CONTROLES[cid]
        yield cid, nombre, False, None, None, f()


# ------------------------------------------------------------------ principal
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-productos", action="store_true")
    args = ap.parse_args(argv)
    t0 = time.time()
    cat = json.loads((RAIZ / "obras" / "catalogo.json").read_text(encoding="utf-8"))
    nuevas = json.loads((RAIZ / "obras" / "nuevas.json").read_text(encoding="utf-8"))

    print("[0] Referencias: mallas sin semántica, clasificador y umbral de complejidad")
    clf, sel, refs = referencias(cat, SEMILLA)
    prot_ini = len(clf.dicc.prototipos)
    print(f"   {len(refs)} referencias · {prot_ini} prototipos · umbral de complejidad {sel.umbral:.3f}")
    ref_cx = {rid: {"complejidad": r["complejidad"], **r["indices"]} for rid, r in sel.referencias.items()}

    print("[1-7] Obras nuevas y controles (prueba ciega, en orden de llegada)")
    filas, interpretadas = [], []
    for k, (cid, nombre, esperada, e, o_v, piezas) in enumerate(candidatos(nuevas)):
        cg, verdad, info = ingesta.ciega(piezas, semilla=SEMILLA + 100 + k)
        g = ingesta.grafo_desde_mallas(cid, cg)
        ev = sel.evaluar(g)
        fila = {"id": cid, "nombre": nombre, "del_corpus": esperada, "alteracion": info,
                "seleccion": {"seleccionada": ev["seleccionada"], "complejidad": ev["complejidad"],
                              "condiciones_fallidas": ev["condiciones_fallidas"], **ev["indices"]},
                "seleccion_correcta": ev["seleccionada"] == esperada}
        if esperada:
            fila["grafo"] = metricas_grafo(g, verdad, piezas, o_v.grafo)
        if ev["seleccionada"] and esperada:
            pipeline.analizar(o_v)
            res, e_r, o_r = interpretar(e, g, verdad, o_v, clf, sel)
            if res["interpretable"]:
                res["medidas"]["grafo_precision"] = fila["grafo"]["precision"]
                res["medidas"]["grafo_exhaustividad"] = fila["grafo"]["exhaustividad"]
                res["criterios"] = evaluar_criterios(res["medidas"])
                # 7. autoaprendizaje con pseudo-etiquetas (sin verdad) y ampliación de referencias
                tradicion = f"{e['tradicion']}"
                clf.aprender(cid, tradicion, res.pop("_items"), res.pop("_pseudo"))
                sel.incorporar(cid, g, res["genoma_inferido"], tradicion)
                res["prototipos_tras_aprender"] = len(clf.dicc.prototipos)
                interpretadas.append((e, e_r, o_v, o_r, k))
            fila["interpretacion"] = res
            if not res["interpretable"]:
                print(f"   {cid}: seleccionada (C={ev['complejidad']:.2f}) pero NO interpretable: {res['motivo']}",
                      flush=True)
                filas.append(fila)
                continue
            m = res.get("medidas", {})
            ok = sum(res.get("criterios", {}).values())
            print(f"   {cid}: seleccionada (C={ev['complejidad']:.2f}) · tipos {res.get('acierto_clasificador', 0):.1%}"
                  f" → {m.get('acierto_tipos', 0):.1%} ({len(res.get('autocorreccion', []))} it.) · "
                  f"criterios {ok}/{len(res.get('criterios', {}))} · GSF {res['equilibrio']['verdadera']['GSF']:.2f}"
                  f" → {res['equilibrio']['reconstruida']['GSF']:.2f} · afín a {res['afinidad']['mas_cercana']}"
                  f"{' · genes nuevos: ' + ', '.join(res['afinidad']['genes_nuevos']) if res['afinidad']['novedad'] else ''}",
                  flush=True)
        else:
            print(f"   {cid}: {'seleccionada' if ev['seleccionada'] else 'rechazada'} (C={ev['complejidad']:.2f}; "
                  f"falla {', '.join(ev['condiciones_fallidas']) or '-'}) · "
                  f"{'correcto' if fila['seleccion_correcta'] else 'ERROR'}", flush=True)
        filas.append(fila)

    print("[7b] Autoaprendizaje: segundo levantamiento de cada obra con la memoria ampliada")
    retencion = clf.dicc.verificar_memoria()
    mejora = []
    for e, _, o_v, _, k in interpretadas:
        cg, verdad, _ = ingesta.ciega(ingesta.piezas_de_grafo(o_v.grafo), semilla=SEMILLA + 500 + k)
        g = ingesta.grafo_desde_mallas(e["id"], cg)
        mc = it.marco(g)
        pred = clf.predecir(it.descriptores(g, mc))
        tipos_v = {n: o_v.grafo.nodos[verdad[n]]["tipo"] for n in g.piezas()}
        mejor, _, _ = autocorregir(e, g, mc, pred)
        gen, tipos_fin = mejor[1], mejor[5]
        crit = evaluar_criterios(it.errores_genoma(gen, e["genoma"]))
        fila = next(f for f in filas if f["id"] == e["id"])
        antes = fila["interpretacion"]
        crit_antes = {c: v for c, v in antes["criterios"].items() if c in crit}
        mejora.append({"id": e["id"], "acierto_antes": antes["acierto_clasificador"],
                       "acierto_despues": acierto(pred, tipos_v),
                       "acierto_final_antes": antes["medidas"]["acierto_tipos"],
                       "acierto_final_despues": acierto(tipos_fin, tipos_v),
                       "criterios_genoma_antes": sum(crit_antes.values()), "criterios_genoma_despues": sum(crit.values()),
                       "criterios_genoma": len(crit)})
        print(f"   {e['id']}: clasificador {mejora[-1]['acierto_antes']:.1%} → {mejora[-1]['acierto_despues']:.1%} · "
              f"tras autocorrección {mejora[-1]['acierto_final_antes']:.1%} → {mejora[-1]['acierto_final_despues']:.1%} · "
              f"genoma {mejora[-1]['criterios_genoma_antes']} → {mejora[-1]['criterios_genoma_despues']}/{len(crit)}")
    print(f"   prototipos {prot_ini} → {len(clf.dicc.prototipos)} · retención {retencion:.3f}")

    cruces = []
    if not args.sin_productos:
        print("[8] Cruce con la referencia más afín y productos")
        por_id = {x["id"]: x for x in cat["obras"]}
        for e, e_r, o_v, o_r, _ in interpretadas:
            af = next(f for f in filas if f["id"] == e["id"])["interpretacion"]["afinidad"]
            ref = min((r for r in af["distancias"] if r in por_id), key=af["distancias"].get)
            e_h, o_h = pipeline.hibrido(por_id[ref], e_r, 0.5, "piedra_cnc", 0)
            est = o_h.analisis["estructura"]
            destino = (SALIDA / "productos" if e["id"] in productos.ESCAPARATE else LOCAL)
            archivos = []
            if est["admisible"]:                         # solo un híbrido verificado se convierte en producto
                archivos = productos.exportar(o_h, destino / o_h.id)
            if o_r.analisis["estructura"]["admisible"]:  # la obra reconstruida: productos de levantamiento
                productos.exportar(o_r, LOCAL / o_r.id)
            cruces.append({"obra": e["id"], "referencia": ref, "hibrido": o_h.id, "genoma": o_h.genoma,
                           "admisible": est["admisible"], "GSF": est["GSF"], "metodo": est["metodo"],
                           "reparacion": o_h.meta["reparacion"],
                           "fabricable": o_h.analisis["fabricacion"]["fraccion_fabricable"],
                           "cnc_ok": o_h.analisis["fabricacion"]["piedra_cnc"]["fraccion_ok"],
                           "tdcp_ok": o_h.analisis["fabricacion"]["3dcp"]["fraccion_ok"],
                           "productos": [str(Path(a).relative_to(pipeline.SALIDAS)) for a in archivos]
                           if destino != LOCAL else [f"local/productos/{o_h.id}/ ({len(archivos)} archivos)"]})
            print(f"   {e['id']} × {ref} → {o_h.id}: GSF {est['GSF']:.2f} ({est['metodo']}) · "
                  f"reparaciones {len(o_h.meta['reparacion'])} · {len(archivos)} archivos", flush=True)

    resumen = {"semilla": SEMILLA, "criterios": {k: {"operador": v[0], "umbral": v[1], "descripcion": v[2]}
                                                 for k, v in CRITERIOS.items()},
               "referencias": ref_cx, "umbral_complejidad": sel.umbral, "candidatos": filas,
               "autoaprendizaje": {"prototipos_inicio": prot_ini, "prototipos_fin": len(clf.dicc.prototipos),
                                   "retencion": retencion, "segundo_levantamiento": mejora},
               "cruces": cruces}
    pipeline._json(SALIDA / "resultados.json", resumen)
    informe(resumen)
    total = sum(sum(f["interpretacion"]["criterios"].values()) for f in filas if "criterios" in f.get("interpretacion", {}))
    n_crit = sum(len(f["interpretacion"]["criterios"]) for f in filas if "criterios" in f.get("interpretacion", {}))
    print(f"Verificación completada en {time.time() - t0:.0f} s · selección "
          f"{sum(f['seleccion_correcta'] for f in filas)}/{len(filas)} · criterios {total}/{n_crit}")
    return resumen


# ------------------------------------------------------------------ informe
def _fmt(v):
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, (int, np.integer)):
        return str(v)
    return f"{v:.3f}"


def informe(r):
    L = ["# Verificación ciega del algoritmo ESTM (generado automáticamente)", "",
         "> Generado por `verificacion.py`. No editar a mano. Protocolo y lectura en "
         "`docs/protocolo_aplicabilidad.md`.", "",
         "Las obras nuevas y los controles entran como **mallas de piezas sin semántica** (sin nombres, tipos ni "
         "juntas), giradas, trasladadas y con 1.5 mm de ruido gaussiano por vértice. El material y el relleno de "
         "senos son datos declarados del levantamiento; todo lo demás se deduce.", "",
         "## 1. Selección: ¿comparte la obra las características del corpus?", "",
         f"Umbral de complejidad: **{r['umbral_complejidad']:.3f}** (0.8 × mínimo de las referencias). "
         "Condiciones mínimas: " + ", ".join(f"{k} ≥ {v}" for k, v in seleccion.MINIMOS.items()) + ".", "",
         "| Obra | Del corpus | C | Simetría | Curvatura (razón · rel.) | Entropía juntas | Entropía formas | Piezas "
         "| Resultado |", "|---|---|---|---|---|---|---|---|---|"]
    for rid, x in r["referencias"].items():
        L.append(f"| {rid} (referencia) | sí | {x['complejidad']:.3f} | {x['simetria']} | {x['curvatura_razon']:.2f} · "
                 f"{x['curvatura_rel']:.2f} | {x['entropia_juntas']:.2f} | {x['entropia_formas']:.2f} | {x['piezas']} "
                 "| calibración |")
    for f in r["candidatos"]:
        s = f["seleccion"]
        res = "seleccionada" if s["seleccionada"] else f"rechazada ({', '.join(s['condiciones_fallidas']) or 'C < umbral'})"
        L.append(f"| {f['id']} {f['nombre']} | {'sí' if f['del_corpus'] else 'no (control)'} | {s['complejidad']:.3f} | "
                 f"{s['simetria']} | {s['curvatura_razon']:.2f} · {s['curvatura_rel']:.2f} | {s['entropia_juntas']:.2f} | "
                 f"{s['entropia_formas']:.2f} | {s['piezas']} | {res} {'✔' if f['seleccion_correcta'] else '✘'} |")
    interp = [f for f in r["candidatos"] if "criterios" in f.get("interpretacion", {})]
    L += ["", "## 2. Interpretación: ¿se ha extraído la información necesaria de cada obra?", "",
          "Cada criterio compara lo deducido de la malla ciega con la ficha verdadera (que el algoritmo no ve).", "",
          "| Criterio | Umbral | " + " | ".join(f["id"] for f in interp) + " |",
          "|---|---|" + "---|" * len(interp)]
    for k, (op, u, desc) in CRITERIOS.items():
        celdas = []
        for f in interp:
            m, c = f["interpretacion"]["medidas"], f["interpretacion"]["criterios"]
            celdas.append(f"{_fmt(m[k])} {'✔' if c[k] else '✘'}" if k in m else "—")
        L.append(f"| {k} ({desc}) | {op} {u} | " + " | ".join(celdas) + " |")
    L.append("| **criterios cumplidos** | | " + " | ".join(
        f"**{sum(f['interpretacion']['criterios'].values())}/{len(f['interpretacion']['criterios'])}**" for f in interp) + " |")
    L += ["", "Los tipos de pieza salen primero del clasificador (memoria episódica) y se autocorrigen con reglas "
          "físicas sobre la superficie ajustada: los nervios cuelgan bajo el intradós, los plementos quedan sobre "
          "él y los mocárabes forman anillos completos. Se vuelve a inferir hasta que los tipos no cambian; no se "
          "usa la verdad.", "",
          "| Obra | Clasificador | Tras autocorrección (iteraciones) | Genoma inferido (n, k, terc., p, β, t/L, μ, j, K) "
          "| Piezas desconocidas | Equilibrio verdadera → reconstruida | Afín a | Genes nuevos frente al corpus |",
          "|---|---|---|---|---|---|---|---|"]
    for f in interp:
        x = f["interpretacion"]
        gn = x["genoma_inferido"]
        eq = x["equilibrio"]
        L.append(f"| {f['id']} | {x['acierto_clasificador']:.1%} | {x['medidas']['acierto_tipos']:.1%} "
                 f"({len(x['autocorreccion'])}) | {int(gn['orden_radial'])}, "
                 f"{round(gn['salto_estrella_rel'] * gn['orden_radial'])}, "
                 f"{int(gn['terceletes'])}, {gn['apuntamiento']:.2f}, {gn['beta_superficie']:.2f}, "
                 f"{gn['espesor_rel']:.4f}, {gn['mocarabe_rel']:.2f}, {gn['inclinacion_junta']:.2f}, "
                 f"{int(gn['despiece'])} | {x['piezas_desconocidas']} | "
                 f"{'admisible' if eq['verdadera']['admisible'] else 'no encontrado'} {eq['verdadera']['GSF']:.2f} "
                 f"({eq['verdadera']['metodo']}) → {'admisible' if eq['reconstruida']['admisible'] else 'no encontrado'} "
                 f"{eq['reconstruida']['GSF']:.2f} ({eq['reconstruida']['metodo']}) | {x['afinidad']['mas_cercana']} "
                 f"(d = {x['afinidad']['distancia_min']:.2f}) | {', '.join(x['afinidad']['genes_nuevos']) or '—'} |")
    a = r["autoaprendizaje"]
    L += ["", "## 3. Autoaprendizaje sin olvido", "",
          f"- Prototipos del diccionario: {a['prototipos_inicio']} → {a['prototipos_fin']} "
          "(las obras nuevas se ingieren con sus tipos autocorregidos, sin usar la verdad; cada obra aceptada "
          "pasa además a ser referencia del selector).",
          f"- Retención de la memoria (ejemplares que siguen en su prototipo): **{a['retencion']:.3f}**.",
          "- Segundo levantamiento (otro giro, otra traslación, otro ruido) de cada obra con la memoria ampliada:", "",
          "| Obra | Clasificador antes | después | Tipos tras autocorrección antes | después "
          "| Criterios de genoma antes | después |", "|---|---|---|---|---|---|---|"]
    for m in a["segundo_levantamiento"]:
        L.append(f"| {m['id']} | {m['acierto_antes']:.1%} | {m['acierto_despues']:.1%} | "
                 f"{m['acierto_final_antes']:.1%} | {m['acierto_final_despues']:.1%} | "
                 f"{m['criterios_genoma_antes']}/{m['criterios_genoma']} | {m['criterios_genoma_despues']}/{m['criterios_genoma']} |")
    if r["cruces"]:
        L += ["", "## 4. Cruce con la referencia más afín y productos", "",
              "| Obra nueva × referencia | Híbrido (t = 0.5, piedra CNC) | Admisible | GSF | Reparación | CNC ok | 3DCP ok "
              "| Productos |", "|---|---|---|---|---|---|---|---|"]
        for c in r["cruces"]:
            prod = c["productos"]
            texto = (prod[0] + (f" (+{len(prod) - 1})" if len(prod) > 1 else "")) if prod else "—"
            L.append(f"| {c['obra']} × {c['referencia']} | {c['hibrido']} | {'sí' if c['admisible'] else 'no'} | "
                     f"{c['GSF']:.2f} ({c['metodo']}) | {len(c['reparacion'])} pasos | {c['cnc_ok']:.0%} | "
                     f"{c['tdcp_ok']:.0%} | {texto} |")
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "informe.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
