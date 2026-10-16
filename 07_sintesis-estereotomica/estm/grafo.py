"""Grafo atribuido relacional G = (V, E) de una obra de fábrica.

V: piezas (dovela, clave, jarja, plemento, celda de mocárabe…) y apoyos.
   Atributos: tipo, tradición, material, volumen, masa, centroide, caja
   orientada, nivel/hilada, datos de fabricación y de equilibrio.
E: relaciones con semántica constructiva (junta radial, lecho horizontal,
   junta lateral, apoyo en nervio, encuentro en clave, apoyo en estribo).
   Atributos: área de contacto, normal, inclinación de la junta.

La geometría de cada pieza se guarda aparte (Poliedro) para que el grafo sea
serializable y comparable sin depender de la malla.
"""

import numpy as np

from .geometria import Poliedro, contacto

TIPOS_ARISTA = {
    "junta_radial": "Junta normal al intradós (estereotomía de dovelas)",
    "lecho": "Junta de lecho entre hiladas sucesivas",
    "junta_lateral": "Junta entre piezas de la misma hilada",
    "apoyo_nervio": "Plemento o celda que descansa sobre un nervio",
    "encuentro_clave": "Nervio que acomete a una clave",
    "arranque": "Pieza que acomete a una jarja o arranque",
    "apoyo": "Pieza que descarga en un apoyo (muro, pilar, estribo)",
    "voladizo": "Celda de mocárabe que vuela sobre la hilada inferior",
    "contacto": "Contacto detectado geométricamente (obra ingerida sin semántica)",
}


class GrafoAtribuido:
    def __init__(self, nombre, **atributos):
        self.nombre = nombre
        self.atributos = atributos
        self.nodos = {}
        self.geometrias = {}
        self.aristas = {}

    # ------------------------------------------------------------ construcción
    def add_nodo(self, nid, tipo, geom=None, densidad=None, **attrs):
        if nid in self.nodos:
            raise KeyError(f"Nodo duplicado: {nid}")
        d = {"tipo": tipo, **attrs}
        if geom is not None:
            vol, cen = geom.volumen_centroide()
            ext, _ = geom.caja_orientada()
            d.update({"volumen_m3": float(vol), "centroide": [float(x) for x in np.round(cen, 4)],
                      "extensiones_m": [float(x) for x in np.round(ext, 4)]})
            if densidad:
                d["masa_kg"] = float(vol * densidad)
            self.geometrias[nid] = geom
        self.nodos[nid] = d
        return d

    def add_arista(self, u, v, tipo, calcular_contacto=True, **attrs):
        if tipo not in TIPOS_ARISTA:
            raise ValueError(f"Tipo de arista desconocido: {tipo}")
        if u not in self.nodos or v not in self.nodos:
            raise KeyError(f"Arista con nodo inexistente: {u}-{v}")
        clave = (u, v) if u < v else (v, u)
        d = {"tipo": tipo, **attrs}
        if calcular_contacto and u in self.geometrias and v in self.geometrias:
            c = contacto(self.geometrias[u], self.geometrias[v])
            if c:
                d.update(c)
        self.aristas[clave] = d
        return d

    # ------------------------------------------------------------ consultas
    def vecinos(self, u):
        return [b if a == u else a for (a, b) in self.aristas if u in (a, b)]

    def lista_adyacencia(self):
        ady = {n: [] for n in self.nodos}
        for (a, b), d in self.aristas.items():
            ady[a].append((b, d["tipo"]))
            ady[b].append((a, d["tipo"]))
        return ady

    def orden(self):
        return sorted(self.nodos)

    def laplaciano_normalizado(self):
        ids = self.orden()
        idx = {n: i for i, n in enumerate(ids)}
        A = np.zeros((len(ids), len(ids)))
        for a, b in self.aristas:
            A[idx[a], idx[b]] = A[idx[b], idx[a]] = 1.0
        g = A.sum(axis=1)
        dinv = np.where(g > 0, 1 / np.sqrt(np.maximum(g, 1e-12)), 0)
        return np.eye(len(ids)) - dinv[:, None] * A * dinv[None, :]

    def componentes_conexas(self):
        ady = self.lista_adyacencia()
        vistos, comps = set(), []
        for n in self.orden():
            if n in vistos:
                continue
            pila, comp = [n], []
            vistos.add(n)
            while pila:
                u = pila.pop()
                comp.append(u)
                for v, _ in ady[u]:
                    if v not in vistos:
                        vistos.add(v)
                        pila.append(v)
            comps.append(comp)
        return comps

    def piezas(self):
        return [n for n in self.orden() if n in self.geometrias]

    def resumen(self):
        tn, ta = {}, {}
        for d in self.nodos.values():
            tn[d["tipo"]] = tn.get(d["tipo"], 0) + 1
        for d in self.aristas.values():
            ta[d["tipo"]] = ta.get(d["tipo"], 0) + 1
        masa = sum(d.get("masa_kg", 0.0) for d in self.nodos.values())
        return {"nodos": len(self.nodos), "aristas": len(self.aristas),
                "piezas": len(self.geometrias), "por_tipo_nodo": dict(sorted(tn.items())),
                "por_tipo_arista": dict(sorted(ta.items())), "masa_total_kg": masa,
                "componentes_conexas": len(self.componentes_conexas())}

    # ------------------------------------------------------------ serialización
    def a_dict(self, con_geometria=True):
        d = {"nombre": self.nombre, "atributos": self.atributos,
             "nodos": [{"id": n, **self.nodos[n]} for n in self.orden()],
             "aristas": [{"u": a, "v": b, **d} for (a, b), d in sorted(self.aristas.items())]}
        if con_geometria:
            d["geometrias"] = {n: g.a_dict() for n, g in sorted(self.geometrias.items())}
        return d

    @staticmethod
    def de_dict(d):
        g = GrafoAtribuido(d["nombre"], **d.get("atributos", {}))
        geoms = d.get("geometrias", {})
        for nd in d["nodos"]:
            nd = dict(nd)
            nid = nd.pop("id")
            g.nodos[nid] = nd
            if nid in geoms:
                g.geometrias[nid] = Poliedro.de_dict(geoms[nid])
        for ad in d["aristas"]:
            ad = dict(ad)
            u, v = ad.pop("u"), ad.pop("v")
            g.aristas[(u, v)] = ad
        return g
