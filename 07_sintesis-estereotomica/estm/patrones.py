"""Extracción de patrones del grafo atribuido.

- Etiquetado Weisfeiler-Lehman (WL): cada nodo se reetiqueta con su etiqueta
  y el multiconjunto de (tipo de junta, etiqueta del vecino). Las etiquetas de
  la iteración h describen subestructuras de radio h ("motivos": una dovela
  entre dos juntas radiales, una celda volada a matajunta sobre dos celdas…).
- Espectro del laplaciano normalizado: firma global de la conectividad.
- Descriptores de pieza: vector geométrico-constructivo por nodo, con
  escalas fijas (no dependen del corpus, para que el espacio sea estable
  durante el aprendizaje continuo).
"""

import hashlib
from collections import Counter

import numpy as np

TIPOS_JUNTA = ["junta_radial", "lecho", "junta_lateral", "apoyo_nervio", "encuentro_clave",
               "arranque", "apoyo", "voladizo"]
NOMBRES_DESCRIPTOR = ["log10_volumen", "log10_esbeltez", "inclinacion_junta", "grado",
                      "altura_relativa"] + [f"frac_{t}" for t in TIPOS_JUNTA]


def _h(texto):
    return hashlib.md5(texto.encode("utf-8")).hexdigest()[:10]


def etiquetas_wl(grafo, iteraciones=2):
    ady = grafo.lista_adyacencia()
    etq = {n: d["tipo"] for n, d in grafo.nodos.items()}
    historia = [dict(etq)]
    for _ in range(iteraciones):
        nueva = {}
        for n in grafo.orden():
            vecinos = sorted(f"{t}:{etq[v]}" for v, t in ady[n])
            nueva[n] = _h(etq[n] + "|" + ",".join(vecinos))
        etq = nueva
        historia.append(dict(etq))
    return historia


def histograma_wl(grafo, iteraciones=2):
    c = Counter()
    for h, etq in enumerate(etiquetas_wl(grafo, iteraciones)):
        c.update(f"{h}:{e}" for e in etq.values())
    return c


def vector_hash(contador, dim=64):
    v = np.zeros(dim)
    for k, cnt in contador.items():
        hsh = int(hashlib.md5(k.encode()).hexdigest(), 16)
        v[hsh % dim] += (1 if (hsh >> 7) & 1 else -1) * cnt
    return v


def espectro(grafo, k=12):
    lam = np.linalg.eigvalsh(grafo.laplaciano_normalizado())
    lam = np.sort(lam)
    out = np.zeros(k)
    out[:min(k, len(lam))] = lam[:k]
    return out


def embedding_obra(grafo, dim=64, k=12):
    """Vector unitario: histograma WL con hashing + espectro de baja frecuencia."""
    wl = vector_hash(histograma_wl(grafo), dim)
    wl = wl / (np.linalg.norm(wl) or 1)
    sp = espectro(grafo, k) / 2.0
    v = np.concatenate([wl, sp])
    return v / np.linalg.norm(v)


def descriptores_piezas(grafo):
    """(nodo, tipo, etiqueta_wl1, vector) para cada pieza con geometría."""
    ady = grafo.lista_adyacencia()
    wl1 = etiquetas_wl(grafo, 1)[1]
    zs = [d["centroide"][2] for d in grafo.nodos.values() if "centroide" in d]
    zmin, zmax = (min(zs), max(zs)) if zs else (0, 1)
    items = []
    for n in grafo.piezas():
        d = grafo.nodos[n]
        ext = d["extensiones_m"]
        incl = [grafo.aristas[(n, v) if n < v else (v, n)].get("inclinacion_deg") for v, _ in ady[n]]
        incl = [x for x in incl if x is not None]
        tipos = Counter(t for _, t in ady[n])
        grado = max(1, len(ady[n]))
        vec = [np.log10(max(d["volumen_m3"], 1e-6)), np.log10(ext[0] / max(ext[2], 1e-6)),
               (np.mean(incl) / 90.0) if incl else 0.5, len(ady[n]) / 8.0,
               (d["centroide"][2] - zmin) / max(zmax - zmin, 1e-6)]
        vec += [tipos.get(t, 0) / grado for t in TIPOS_JUNTA]
        items.append((n, d["tipo"], wl1[n], np.round(np.array(vec, float), 6)))
    return items


def similitud(e1, e2):
    return float(np.dot(e1, e2))
