"""Diccionario de patrones con memoria episódica (aprendizaje continuo).

Cada obra ingerida es un episodio. Sus piezas (vectores de descriptores) se
asignan al prototipo más cercano del mismo tipo o abren un prototipo nuevo.
El diccionario crece sin pérdida de información previa por cuatro garantías:

  1. Los prototipos nunca se borran ni se fusionan. Su ancla (centro) se
     congela al crearlos: la regla de clasificación de lo aprendido no deriva.
  2. Cada prototipo guarda estadísticos suficientes exactos (n, media, M2;
     combinación de Chan et al. 1979) que sí se actualizan con cada episodio.
  3. Estabilidad por repaso (replay): antes de crear un ancla nueva se
     comprueba contra la memoria episódica; si cambiaría la clasificación de
     algún ejemplar recordado, no se crea y los elementos se asignan al
     prototipo existente más cercano (estabilidad > plasticidad).
  4. Registro de eventos sólo-añadir: el estado completo es reproducible
     reproduciendo el registro (event sourcing), y el registro conserva los
     vectores originales de todas las piezas ingeridas.

Es un aprendizaje incremental por prototipos (nearest-class-mean con
memoria de repaso), no una red neuronal: interpretable y verificable.
"""

import hashlib
import json

import numpy as np


class DiccionarioPatrones:
    def __init__(self, umbral=0.45, k_memoria=6, escalas=None):
        self.umbral = umbral
        self.k_memoria = k_memoria
        self.escalas = None if escalas is None else np.asarray(escalas, float)
        self.prototipos = []
        self.memoria = {}
        self.vistos = {}
        self.eventos = []

    # ------------------------------------------------------------ utilidades
    def _escala(self, v):
        v = np.asarray(v, float)
        return v / self.escalas if self.escalas is not None else v

    def _distancia(self, v, proto):
        return float(np.linalg.norm(self._escala(v) - self._escala(proto["centro"])))

    def _cercano(self, v, tipo, extra=None):
        cand = [p for p in self.prototipos if p["tipo"] == tipo] + (extra or [])
        if not cand:
            return None, np.inf
        d = [self._distancia(v, p) for p in cand]
        i = int(np.argmin(d))
        return cand[i], d[i]

    @staticmethod
    def _combinar(p, X):
        """Combina estadísticos exactos (n, media, M2) con un lote X (Chan et al. 1979)."""
        X = np.asarray(X, float)
        nb, mb = len(X), X.mean(axis=0)
        m2b = ((X - mb) ** 2).sum(axis=0)
        na, ma, m2a = p["n"], np.asarray(p["media"]), np.asarray(p["m2"])
        n = na + nb
        delta = mb - ma
        return n, ma + delta * nb / n, m2a + m2b + delta ** 2 * na * nb / n

    def _roba_memoria(self, tipo, centro):
        """¿Cambiaría el ancla candidata la clasificación de algún ejemplar recordado?"""
        candidato = {"id": "_cand", "tipo": tipo, "centro": list(centro)}
        for pid, buf in self.memoria.items():
            p = self._por_id(pid)
            if p["tipo"] != tipo:
                continue
            for e in buf:
                if self._cercano(e["vector"], tipo, [candidato])[0]["id"] == "_cand":
                    return True
        return False

    def _por_id(self, pid):
        return self.prototipos[int(pid[1:])]

    def _nuevo(self, tipo, centro):
        c = np.asarray(centro, float)
        p = {"id": f"P{len(self.prototipos):04d}", "tipo": tipo, "centro": c.tolist(), "n": 0,
             "media": c.tolist(), "m2": np.zeros_like(c).tolist(),
             "obras": {}, "tradiciones": {}, "wl": {}, "fuera_de_umbral": 0}
        self.prototipos.append(p)
        self.memoria[p["id"]] = []
        self.vistos[p["id"]] = 0
        return p

    def _contabilizar(self, p, obra, tradicion, wl, k, sumar_stats=True, X=None):
        if sumar_stats:
            n_, media, m2 = self._combinar(p, X)
            p["n"], p["media"], p["m2"] = int(n_), media.tolist(), m2.tolist()
        p["obras"][obra] = p["obras"].get(obra, 0) + k
        p["tradiciones"][tradicion] = p["tradiciones"].get(tradicion, 0) + k
        for w in wl:
            p["wl"][w] = p["wl"].get(w, 0) + 1

    def _recordar(self, pid, ejemplares, obra):
        """Muestreo de reservorio determinista (semilla = hash de obra y prototipo)."""
        buf = self.memoria[pid]
        rng = np.random.default_rng(int(hashlib.md5(f"{obra}:{pid}".encode()).hexdigest(), 16) % 2 ** 32)
        for e in ejemplares:
            self.vistos[pid] += 1
            if len(buf) < self.k_memoria:
                buf.append(e)
            else:
                r = int(rng.integers(0, self.vistos[pid]))
                if r < self.k_memoria:
                    buf[r] = e

    # ------------------------------------------------------------ episodio
    def ingerir(self, obra, tradicion, items, registrar=True):
        """items: [(nodo, tipo, etiqueta_wl, vector)]. Devuelve el resumen del episodio."""
        if registrar:
            self.eventos.append({"evento": "ingesta", "obra": obra, "tradicion": tradicion,
                                 "items": [[n, t, w, [float(x) for x in v]] for n, t, w, v in items]})
        # fase 1: anclas nuevas para las piezas lejanas a todo lo aprendido
        lejanos = {}
        for n, t, w, v in items:
            _, d = self._cercano(v, t)
            if d >= self.umbral:
                lejanos.setdefault(t, []).append(np.asarray(v, float))
        creados, rechazados = [], 0
        for t, lista in lejanos.items():
            grupos = []
            for v in lista:                                    # agrupación líder dentro del episodio
                for g in grupos:
                    if np.linalg.norm(self._escala(v) - self._escala(g[0])) < self.umbral:
                        g.append(v)
                        break
                else:
                    grupos.append([v])
            for g in grupos:
                centro = np.mean(g, axis=0)
                if any(p["tipo"] == t for p in self.prototipos) and self._roba_memoria(t, centro):
                    rechazados += 1                            # cambiaría recuerdos: no se crea
                    continue
                creados.append(self._nuevo(t, centro)["id"])
        # fase 2: cada pieza al ancla más cercana; estadísticos exactos y memoria
        asign = {}
        for n, t, w, v in items:
            p, d = self._cercano(v, t)
            asign.setdefault(p["id"], []).append((n, w, v, d))
        for pid, miembros in asign.items():
            p = self._por_id(pid)
            p["fuera_de_umbral"] += sum(1 for *_, d in miembros if d >= self.umbral)
            self._contabilizar(p, obra, tradicion, [w for _, w, _, _ in miembros], len(miembros),
                               X=[v for _, _, v, _ in miembros])
            self._recordar(pid, [{"obra": obra, "nodo": n, "vector": [float(x) for x in v]}
                                 for n, _, v, _ in miembros], obra)
        return {"obra": obra, "items": len(items), "prototipos_creados": len(creados),
                "prototipos_actualizados": len(set(asign) - set(creados)),
                "anclas_rechazadas_por_estabilidad": rechazados,
                "total_prototipos": len(self.prototipos), "retencion_memoria": self.verificar_memoria()}

    # ------------------------------------------------------------ consultas
    def clasificar(self, vector, tipo):
        p, d = self._cercano(vector, tipo)
        return (p["id"], d) if p else (None, np.inf)

    def verificar_memoria(self):
        """Fracción de ejemplares recordados que siguen en su prototipo (1.0 = sin olvido)."""
        total = ok = 0
        for pid, buf in self.memoria.items():
            tipo = self._por_id(pid)["tipo"]
            for e in buf:
                total += 1
                ok += self.clasificar(e["vector"], tipo)[0] == pid
        return ok / total if total else 1.0

    def transversales(self, minimo=2):
        """Prototipos compartidos por al menos `minimo` tradiciones constructivas."""
        return [p for p in self.prototipos if len(p["tradiciones"]) >= minimo]

    def n_items(self):
        return sum(p["n"] for p in self.prototipos)

    # ------------------------------------------------------------ persistencia
    def a_dict(self):
        return {"umbral": self.umbral, "k_memoria": self.k_memoria,
                "escalas": None if self.escalas is None else self.escalas.tolist(),
                "prototipos": self.prototipos, "memoria": self.memoria}

    def guardar(self, ruta_estado, ruta_eventos):
        with open(ruta_estado, "w", encoding="utf-8") as fh:
            json.dump(_red(self.a_dict()), fh, ensure_ascii=False, indent=1)
        with open(ruta_eventos, "w", encoding="utf-8") as fh:
            for ev in self.eventos:                         # precisión completa: registro sin pérdida
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

    @staticmethod
    def reproducir(ruta_eventos, **kw):
        d = DiccionarioPatrones(**kw)
        with open(ruta_eventos, encoding="utf-8") as fh:
            for linea in fh:
                ev = json.loads(linea)
                items = [(n, t, w, np.array(v)) for n, t, w, v in ev["items"]]
                d.eventos.append(ev)
                d.ingerir(ev["obra"], ev["tradicion"], items, registrar=False)
        return d


def _red(o):
    if isinstance(o, float):
        return float(f"{o:.6g}")
    if isinstance(o, dict):
        return {k: _red(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_red(v) for v in o]
    return o
