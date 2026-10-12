"""Modelo paramétrico mínimo para ingeniería inversa de masas arquitectónicas.

Convenciones: unidades en metros; x = Este, y = Norte, z = altura.
Cada primitiva conserva su volumen analítico para poder hacer balances de
materia (p. ej. roca extraída en Kailasa) y exporta a:
    * SVG  — planta cenital con ejes, escala y norte
    * OBJ  — malla de volúmenes importable en Rhino / Blender / SketchUp
    * JSON — primitivas, parámetros y cómputos (trazable para ML)
"""

import math
from pathlib import Path

from . import io_utils

ESTILOS = {
    "agua": "fill:#cfe3f2;stroke:#5b8db8;stroke-width:0.8",
    "terreno": "fill:#efe9dc;stroke:#b3a88f;stroke-width:0.6",
    "vacio": "fill:none;stroke:#8c6d46;stroke-width:1;stroke-dasharray:6 4",
    "terraza": "fill:#e4e0d8;stroke:#7d776c;stroke-width:0.8",
    "muro": "fill:#6f6a62;stroke:#3c3934;stroke-width:0.6",
    "galeria": "fill:#c9c2b4;stroke:#4f4a42;stroke-width:0.8",
    "masa": "fill:#b8865b;stroke:#5a3c22;stroke-width:0.8",
    "masa_sec": "fill:#d3a77c;stroke:#6b4a2c;stroke-width:0.7",
    "puerta": "fill:#8f3b2c;stroke:#4d1e15;stroke-width:0.6",
    "modulo": "fill:none;stroke:#b9b4aa;stroke-width:0.4",
    "eje": "fill:none;stroke:#c0392b;stroke-width:0.8;stroke-dasharray:10 5",
    "fase": "fill:none;stroke:#2f6f5e;stroke-width:1.2;stroke-dasharray:3 3",
}


class Model:
    def __init__(self, nombre, sitio_id, parametros=None):
        self.nombre = nombre
        self.sitio_id = sitio_id
        self.parametros = parametros or {}
        self.prims = []
        self.lines = []
        self.computos = {}

    # ------------------------------------------------------------ primitivas
    def _add(self, prim):
        prim.setdefault("z0", 0.0)
        self.prims.append(prim)
        return prim

    def prisma(self, nombre, cx, cy, w, d, h=0.0, z0=0.0, capa="masa", rot=0.0):
        return self._add({"tipo": "prisma", "nombre": nombre, "cx": cx, "cy": cy,
                          "w": w, "d": d, "h": h, "z0": z0, "rot": rot, "capa": capa,
                          "huella_m2": w * d, "volumen_m3": w * d * h})

    def marco(self, nombre, cx, cy, w, d, espesor, h=0.0, z0=0.0, capa="muro"):
        area = w * d - max(w - 2 * espesor, 0) * max(d - 2 * espesor, 0)
        return self._add({"tipo": "marco", "nombre": nombre, "cx": cx, "cy": cy,
                          "w": w, "d": d, "espesor": espesor, "h": h, "z0": z0,
                          "capa": capa, "huella_m2": area, "volumen_m3": area * h})

    def torre_escalonada(self, nombre, cx, cy, base, h, niveles=5, ratio_cima=0.35,
                         z0=0.0, capa="masa", forma="cuadrado"):
        """Torre de niveles homotéticos: lado decrece linealmente hasta ratio_cima."""
        tiers = []
        dh = h / niveles
        for i in range(niveles):
            s = base * (1 - (1 - ratio_cima) * i / max(niveles - 1, 1))
            tiers.append({"lado": s, "z0": z0 + i * dh, "h": dh})
        if forma == "circulo":
            vol = sum(math.pi / 4 * t["lado"] ** 2 * t["h"] for t in tiers)
            huella = math.pi / 4 * base ** 2
        else:
            vol = sum(t["lado"] ** 2 * t["h"] for t in tiers)
            huella = base ** 2
        return self._add({"tipo": "torre_escalonada", "nombre": nombre, "cx": cx,
                          "cy": cy, "base": base, "h": h, "z0": z0, "forma": forma,
                          "niveles": tiers, "capa": capa, "huella_m2": huella,
                          "volumen_m3": vol, "factor_volumen": vol / (huella * h)})

    def casquete(self, nombre, cx, cy, diametro, h, z0=0.0, capa="masa"):
        a = diametro / 2
        vol = math.pi * h * (3 * a ** 2 + h ** 2) / 6
        huella = math.pi * a ** 2
        return self._add({"tipo": "casquete", "nombre": nombre, "cx": cx, "cy": cy,
                          "diametro": diametro, "h": h, "z0": z0, "capa": capa,
                          "huella_m2": huella, "volumen_m3": vol,
                          "factor_volumen": vol / (huella * h)})

    def cilindro(self, nombre, cx, cy, diametro, h=0.0, z0=0.0, capa="masa"):
        huella = math.pi * diametro ** 2 / 4
        return self._add({"tipo": "cilindro", "nombre": nombre, "cx": cx, "cy": cy,
                          "diametro": diametro, "h": h, "z0": z0, "capa": capa,
                          "huella_m2": huella, "volumen_m3": huella * h})

    def anillo(self, nombre, cx, cy, diametro, espesor, h=0.0, z0=0.0, capa="muro"):
        r1, r0 = diametro / 2, diametro / 2 - espesor
        huella = math.pi * (r1 ** 2 - r0 ** 2)
        return self._add({"tipo": "anillo", "nombre": nombre, "cx": cx, "cy": cy,
                          "diametro": diametro, "espesor": espesor, "h": h, "z0": z0,
                          "capa": capa, "huella_m2": huella, "volumen_m3": huella * h})

    def linea(self, x1, y1, x2, y2, capa="eje"):
        self.lines.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "capa": capa})

    # ------------------------------------------------------------ consultas
    def volumen(self, capas=None, prefijo=None):
        total = 0.0
        for p in self.prims:
            if capas and p["capa"] not in capas:
                continue
            if prefijo and not p["nombre"].startswith(prefijo):
                continue
            total += p["volumen_m3"]
        return total

    def bbox(self):
        xs, ys = [], []
        for p in self.prims:
            hw, hd = _half_extent(p)
            xs += [p["cx"] - hw, p["cx"] + hw]
            ys += [p["cy"] - hd, p["cy"] + hd]
        for ln in self.lines:
            xs += [ln["x1"], ln["x2"]]
            ys += [ln["y1"], ln["y2"]]
        return min(xs), min(ys), max(xs), max(ys)

    # ------------------------------------------------------------ exportación
    def export(self, out_dir, stem="modelo", svg_width=900):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self.to_svg(out_dir / f"{stem}_planta.svg", svg_width)
        self.to_obj(out_dir / f"{stem}_volumetria.obj")
        self.to_json(out_dir / f"{stem}_geometria.json")

    def to_json(self, path):
        por_capa = {}
        for p in self.prims:
            c = por_capa.setdefault(p["capa"], {"volumen_m3": 0.0, "huella_m2": 0.0, "n": 0})
            c["volumen_m3"] += p["volumen_m3"]
            c["huella_m2"] += p["huella_m2"]
            c["n"] += 1
        io_utils.write_json(path, {
            "modelo": self.nombre,
            "sitio_id": self.sitio_id,
            "unidades": "m",
            "convencion_ejes": "x=Este, y=Norte, z=altura",
            "parametros": self.parametros,
            "computos": self.computos,
            "resumen_por_capa": por_capa,
            "primitivas": self.prims,
        })

    def to_svg(self, path, width=900, margin=40):
        x0, y0, x1, y1 = self.bbox()
        span = max(x1 - x0, y1 - y0) or 1.0
        s = (width - 2 * margin) / span
        height = int((y1 - y0) * s + 2 * margin + 40)
        width_px = int((x1 - x0) * s + 2 * margin)

        def X(x):
            return margin + (x - x0) * s

        def Y(y):
            return margin + (y1 - y) * s

        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px} {height}" '
               f'width="{width_px}" height="{height}" font-family="sans-serif">',
               f"<title>{self.nombre} — planta paramétrica</title>",
               f'<rect width="{width_px}" height="{height}" fill="#fbfaf7"/>']
        for p in self.prims:
            out.extend(_svg_prim(p, X, Y, s))
        for ln in self.lines:
            out.append(f'<line x1="{X(ln["x1"]):.2f}" y1="{Y(ln["y1"]):.2f}" '
                       f'x2="{X(ln["x2"]):.2f}" y2="{Y(ln["y2"]):.2f}" '
                       f'style="{ESTILOS[ln["capa"]]}"/>')
        # barra de escala con longitud "redonda"
        target = span / 5
        mag = 10 ** math.floor(math.log10(target))
        bar = min((m * mag for m in (1, 2, 5, 10)), key=lambda v: abs(v - target))
        by = height - 22
        out.append(f'<line x1="{margin}" y1="{by}" x2="{margin + bar * s:.2f}" y2="{by}" '
                   'stroke="#222" stroke-width="3"/>')
        out.append(f'<text x="{margin}" y="{by - 6}" font-size="11" fill="#222">'
                   f'{bar:g} m</text>')
        nx = width_px - margin
        out.append(f'<path d="M{nx},{by - 24} l-6,16 l6,-4 l6,4 z" fill="#222"/>')
        out.append(f'<text x="{nx - 4}" y="{by + 8}" font-size="11" fill="#222">N</text>')
        out.append(f'<text x="{margin}" y="{height - 6}" font-size="10" fill="#555">'
                   f'{self.nombre} · {self.sitio_id} · generado por archimorph</text>')
        out.append("</svg>")
        Path(path).write_text("\n".join(out) + "\n", encoding="utf-8")

    def to_obj(self, path, segs=32):
        verts, lines = [], [f"# {self.nombre} — volumetría paramétrica (m, z arriba)"]

        def v(x, y, z):
            # OBJ con eje Y vertical: (x, z, -y)
            verts.append((x, z, -y))
            return len(verts)

        def box(cx, cy, w, d, z0, h, rot=0.0):
            if h <= 0:
                return []
            c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            corners = []
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                lx, ly = dx * w / 2, dy * d / 2
                corners.append((cx + lx * c - ly * sn, cy + lx * sn + ly * c))
            b = [v(x, y, z0) for x, y in corners]
            t = [v(x, y, z0 + h) for x, y in corners]
            faces = [b[::-1], t]
            for i in range(4):
                j = (i + 1) % 4
                faces.append([b[i], b[j], t[j], t[i]])
            return faces

        def ring_faces(cx, cy, radii_z, closed_top=True):
            """Superficie de revolución a partir de [(r, z)] ascendentes."""
            faces, rings = [], []
            for r, z in radii_z:
                rings.append([v(cx + r * math.cos(2 * math.pi * k / segs),
                                cy + r * math.sin(2 * math.pi * k / segs), z)
                              for k in range(segs)])
            faces.append(rings[0][::-1])
            for a, b in zip(rings, rings[1:]):
                for k in range(segs):
                    m = (k + 1) % segs
                    faces.append([a[k], a[m], b[m], b[k]])
            if closed_top:
                faces.append(rings[-1])
            return faces

        for p in self.prims:
            faces = []
            t = p["tipo"]
            if t == "prisma":
                faces = box(p["cx"], p["cy"], p["w"], p["d"], p["z0"], p["h"], p["rot"])
            elif t == "marco" and p["h"] > 0:
                e = p["espesor"]
                faces += box(p["cx"], p["cy"] + (p["d"] - e) / 2, p["w"], e, p["z0"], p["h"])
                faces += box(p["cx"], p["cy"] - (p["d"] - e) / 2, p["w"], e, p["z0"], p["h"])
                faces += box(p["cx"] + (p["w"] - e) / 2, p["cy"], e, p["d"] - 2 * e, p["z0"], p["h"])
                faces += box(p["cx"] - (p["w"] - e) / 2, p["cy"], e, p["d"] - 2 * e, p["z0"], p["h"])
            elif t == "torre_escalonada":
                for tier in p["niveles"]:
                    if p["forma"] == "circulo":
                        r = tier["lado"] / 2
                        faces += ring_faces(p["cx"], p["cy"], [(r, tier["z0"]),
                                                               (r, tier["z0"] + tier["h"])])
                    else:
                        faces += box(p["cx"], p["cy"], tier["lado"], tier["lado"],
                                     tier["z0"], tier["h"])
            elif t == "casquete" and p["h"] > 0:
                a, h = p["diametro"] / 2, p["h"]
                R = (a ** 2 + h ** 2) / (2 * h)
                zc = p["z0"] + h - R
                prof = []
                for i in range(12):
                    z = p["z0"] + h * i / 12
                    prof.append((math.sqrt(max(R ** 2 - (z - zc) ** 2, 0)), z))
                prof.append((a * 0.02, p["z0"] + h))
                faces = ring_faces(p["cx"], p["cy"], prof)
            elif t == "cilindro" and p["h"] > 0:
                r = p["diametro"] / 2
                faces = ring_faces(p["cx"], p["cy"], [(r, p["z0"]), (r, p["z0"] + p["h"])])
            elif t == "anillo" and p["h"] > 0:
                r = p["diametro"] / 2
                faces = ring_faces(p["cx"], p["cy"], [(r, p["z0"]), (r, p["z0"] + p["h"])],
                                   closed_top=False)[1:]
                faces += ring_faces(p["cx"], p["cy"], [(r - p["espesor"], p["z0"]),
                                                       (r - p["espesor"], p["z0"] + p["h"])],
                                    closed_top=False)[1:]
            if faces:
                lines.append(f"g {p['nombre'].replace(' ', '_')}")
                lines.extend("f " + " ".join(str(i) for i in f) for f in faces)
        body = [f"v {x:.3f} {y:.3f} {z:.3f}" for x, y, z in verts]
        Path(path).write_text("\n".join(lines[:1] + body + lines[1:]) + "\n", encoding="utf-8")


def _half_extent(p):
    t = p["tipo"]
    if t in ("prisma", "marco"):
        if p.get("rot"):
            r = math.radians(p["rot"])
            hw = abs(p["w"] / 2 * math.cos(r)) + abs(p["d"] / 2 * math.sin(r))
            hd = abs(p["w"] / 2 * math.sin(r)) + abs(p["d"] / 2 * math.cos(r))
            return hw, hd
        return p["w"] / 2, p["d"] / 2
    if t == "torre_escalonada":
        return p["base"] / 2, p["base"] / 2
    return p["diametro"] / 2, p["diametro"] / 2


def _svg_prim(p, X, Y, s):
    st = ESTILOS.get(p["capa"], ESTILOS["masa"])
    t = p["tipo"]
    title = f"<title>{p['nombre']}</title>"
    if t == "prisma":
        x, y = X(p["cx"] - p["w"] / 2), Y(p["cy"] + p["d"] / 2)
        tr = ""
        if p.get("rot"):
            tr = f' transform="rotate({-p["rot"]:.2f} {X(p["cx"]):.2f} {Y(p["cy"]):.2f})"'
        return [f'<rect x="{x:.2f}" y="{y:.2f}" width="{p["w"] * s:.2f}" '
                f'height="{p["d"] * s:.2f}" style="{st}"{tr}>{title}</rect>']
    if t == "marco":
        e = p["espesor"]
        ox, oy = X(p["cx"] - p["w"] / 2), Y(p["cy"] + p["d"] / 2)
        ix, iy = X(p["cx"] - p["w"] / 2 + e), Y(p["cy"] + p["d"] / 2 - e)
        iw, ih = max(p["w"] - 2 * e, 0) * s, max(p["d"] - 2 * e, 0) * s
        d = (f"M{ox:.2f},{oy:.2f} h{p['w'] * s:.2f} v{p['d'] * s:.2f} h{-p['w'] * s:.2f} z "
             f"M{ix:.2f},{iy:.2f} v{ih:.2f} h{iw:.2f} v{-ih:.2f} z")
        return [f'<path d="{d}" fill-rule="evenodd" style="{st}">{title}</path>']
    if t == "torre_escalonada":
        out = []
        for tier in p["niveles"]:
            if p["forma"] == "circulo":
                out.append(f'<circle cx="{X(p["cx"]):.2f}" cy="{Y(p["cy"]):.2f}" '
                           f'r="{tier["lado"] / 2 * s:.2f}" style="{st}">{title}</circle>')
            else:
                out.append(f'<rect x="{X(p["cx"] - tier["lado"] / 2):.2f}" '
                           f'y="{Y(p["cy"] + tier["lado"] / 2):.2f}" '
                           f'width="{tier["lado"] * s:.2f}" height="{tier["lado"] * s:.2f}" '
                           f'style="{st}">{title}</rect>')
        return out
    if t in ("casquete", "cilindro"):
        out = [f'<circle cx="{X(p["cx"]):.2f}" cy="{Y(p["cy"]):.2f}" '
               f'r="{p["diametro"] / 2 * s:.2f}" style="{st}">{title}</circle>']
        if t == "casquete":
            for k in (0.66, 0.33):
                out.append(f'<circle cx="{X(p["cx"]):.2f}" cy="{Y(p["cy"]):.2f}" '
                           f'r="{p["diametro"] / 2 * k * s:.2f}" style="{ESTILOS["modulo"]}"/>')
        return out
    if t == "anillo":
        r = p["diametro"] / 2 * s
        w = max(p["espesor"] * s, 0.8)
        return [f'<circle cx="{X(p["cx"]):.2f}" cy="{Y(p["cy"]):.2f}" r="{r - w / 2:.2f}" '
                f'fill="none" stroke="#3c3934" stroke-width="{w:.2f}">{title}</circle>']
    return []
