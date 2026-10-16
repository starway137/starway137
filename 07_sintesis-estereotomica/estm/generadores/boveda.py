"""Gramática unificada de bóvedas sobre planta poligonal regular.

Un mismo genoma describe tradiciones distintas:
    crucería gótica       n = 4, nervios {4/2} (diagonales), β = 0 (arista), juntas radiales
    estrellada (terceletes) idem + terceletes y ligaduras
    nervada califal       n = 8, nervios {8/3} que no pasan por el centro, β = 1 (cúpula)
    cúpula de mocárabes   n = 8, sin nervios, zona de celdas voladas con lechos horizontales
y cualquier punto intermedio del espacio de parámetros (híbridos).

Piezas generadas (nodos del grafo):
    plemento        dovelas de la plementería / cáscara, por hiladas y sectores
    celda_mocarabe  celdas voladas por niveles, a matajunta entre niveles
    dovela_nervio   dovelas de nervios con juntas normales a su directriz
    clave           claves en los cruces de nervios y cierre central
    jarja           arranques de nervios en los vértices
    apoyo           pilares (vértices) o muros/tambor (lados)
"""

import numpy as np

from .. import materiales
from ..geometria import Poliedro, hexaedro, prisma_entre
from ..grafo import GrafoAtribuido
from ..superficie import SuperficiePoligonal
from .obra import Obra

G = 9.81


# ------------------------------------------------------------------ utilidades
def _cara(p0, p1, p2, p3):
    P = np.array([p0, p1, p2, p3])
    n = np.zeros(3)
    for a, b in zip(P, np.roll(P, -1, axis=0)):
        n += np.cross(a, b)
    area = np.linalg.norm(n) / 2
    n = n / (2 * area) if area > 0 else n
    return {"area_m2": float(area), "normal": [float(x) for x in np.round(n, 5)],
            "centro": [float(x) for x in np.round(P.mean(axis=0), 4)],
            "inclinacion_deg": float(np.degrees(np.arccos(min(1.0, abs(n[2])))))}


def _interseccion(p1, p2, p3, p4):
    d1, d2 = p2 - p1, p4 - p3
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12:
        return None
    r = p3 - p1
    t = (r[0] * d2[1] - r[1] * d2[0]) / den
    u = (r[0] * d1[1] - r[1] * d1[0]) / den
    if 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6:
        return t
    return None


def _dist_segmento(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


class _Envolvente:
    """Puntos de intradós/trasdós de la cáscara con la regla de juntas j."""

    def __init__(self, sup, j, t):
        self.sup, self.j, self.t = sup, j, t

    def intrados(self, P2):
        P2 = np.atleast_2d(P2)
        return np.column_stack([P2, self.sup.z(P2[:, 0], P2[:, 1])])

    def trasdos(self, P2, j=None, t=None):
        j = self.j if j is None else j
        t = self.t if t is None else t
        P2 = np.atleast_2d(P2)
        Pi = self.intrados(P2)
        N = self.sup.normal(P2[:, 0], P2[:, 1])
        r = np.linalg.norm(P2, axis=1, keepdims=True)
        rh = np.where(r > 1e-9, P2 / np.maximum(r, 1e-9), 0.0)
        horiz = np.column_stack([rh, np.zeros(len(P2))])
        d = (1 - j) * horiz + j * N
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        cos = np.clip((d * N).sum(axis=1), 0.25, 1.0)          # longitud de junta <= 4t
        return Pi + d * (t / cos)[:, None]


# ------------------------------------------------------------------ generador
def boveda_poligonal(id_, nombre, tradicion, genoma, luz, material="caliza", meta=None):
    """Genera piezas, grafo y secciones de análisis a partir del genoma.

    luz: distancia entre lados opuestos (2·apotema), en metros.
    """
    gm = dict(genoma)
    n = int(gm["orden_radial"])
    A = luz / 2
    R = A / np.cos(np.pi / n)
    p, beta, j = gm["apuntamiento"], gm["beta_superficie"], gm["inclinacion_junta"]
    t = gm["espesor_rel"] * luz
    K = int(round(gm["despiece"]))
    mu = gm["mocarabe_rel"]
    h_r = gm["canto_nervio_rel"] * luz
    b_r = max(0.12, 0.7 * h_r)
    k_est = int(round(gm["salto_estrella_rel"] * n))
    terceletes = int(round(gm["terceletes"]))
    rho = materiales.densidad(material)
    sup = SuperficiePoligonal(n, R, p, beta)
    env = _Envolvente(sup, j, t)
    tan = np.tan(np.pi / n)
    normales = sup.normales_lado()
    tang = np.column_stack([-normales[:, 1], normales[:, 0]])
    verts = sup.vertices()

    g = GrafoAtribuido(nombre, id=id_, tradicion=tradicion, tipologia="boveda", material=material,
                       luz_m=luz, orden_radial=n, beta=beta)
    perimetral = beta >= 0.5

    def plano(s, q, u):
        return q * normales[s] + u * q * tan * tang[s]

    # ---------------------------------------------------------------- niveles en q
    ell = A / max(K, 1)
    q_min = 0.6 * ell
    q_m = A * (1 - mu)
    n_cascara = max(1, int(round((q_m - q_min) / ell))) if q_m > q_min + 1e-6 else 0
    q_cas = np.linspace(q_min, q_m, n_cascara + 1) if n_cascara else np.array([q_min])
    T = max(1, int(round(mu * K * 1.5))) if mu > 1e-3 else 0
    q_moc = np.linspace(q_m, A, T + 1) if T else np.array([q_m])
    t_m = 1.5 * t

    # ---------------------------------------------------------------- cierre central
    cierre_pts = np.array([(q_min / np.cos(np.pi / n)) * np.array([np.cos(a), np.sin(a)])
                           for a in 2 * np.pi * np.arange(n) / n + np.pi / n])
    if n_cascara == 0 and T:
        q_min = q_m
    g.add_nodo("clave_cierre", "clave", prisma_entre(env.intrados(cierre_pts), env.trasdos(cierre_pts)),
               densidad=rho, hilada=0, sector=-1)

    # ---------------------------------------------------------------- cáscara (plementos)
    filas = {}                                   # (sector, hilada) -> [(id, u0, u1)]
    def piezas_hilada(q):
        return max(1, int(round(2 * q * tan / ell)))

    for s in range(n):
        for k in range(n_cascara):
            q0, q1 = q_cas[k], q_cas[k + 1]
            m = piezas_hilada(0.5 * (q0 + q1))
            us = np.linspace(-1, 1, m + 1)
            fila = []
            for i in range(m):
                u0, u1 = us[i], us[i + 1]
                P2 = np.array([plano(s, q0, u0), plano(s, q0, u1), plano(s, q1, u1), plano(s, q1, u0)])
                geo = hexaedro(env.intrados(P2), env.trasdos(P2))
                nid = f"plem_s{s}_h{k + 1:02d}_{i:02d}"
                g.add_nodo(nid, "plemento", geo, densidad=rho, sector=s, hilada=k + 1,
                           inclinacion_junta=j)
                fila.append((nid, u0, u1, q0, q1))
            filas[(s, k + 1)] = fila

    # ---------------------------------------------------------------- mocárabes
    for s in range(n):
        for k in range(T):
            q0, q1 = q_moc[k], q_moc[k + 1]
            c = max(2, int(round(2 * q1 * tan / (0.6 * ell))))
            us = np.linspace(-1, 1, c + 1)
            if k % 2:                                   # matajunta: desfase de media celda
                us = np.unique(np.clip(np.concatenate([[-1], us[:-1] + 1.0 / c, [1]]), -1, 1))
            fila = []
            for i in range(len(us) - 1):
                u0, u1 = us[i], us[i + 1]
                P2 = np.array([plano(s, q0, u0), plano(s, q0, u1), plano(s, q1, u1), plano(s, q1, u0)])
                geo = hexaedro(env.intrados(P2), env.trasdos(P2, j=0.0, t=t_m))
                nid = f"moc_s{s}_n{T - k:02d}_{i:02d}"
                g.add_nodo(nid, "celda_mocarabe", geo, densidad=rho, sector=s, nivel=T - k,
                           hilada=n_cascara + k + 1, matajunta=bool(k % 2), inclinacion_junta=0.0)
                fila.append((nid, u0, u1, q0, q1))
            filas[(s, n_cascara + k + 1)] = fila
    n_hiladas = n_cascara + T

    # ---------------------------------------------------------------- juntas de la cáscara
    def junta_lecho(s, q, u0, u1, j_, t_):
        P2 = np.array([plano(s, q, u0), plano(s, q, u1)])
        Pi, Pe = env.intrados(P2), env.trasdos(P2, j=j_, t=t_)
        return _cara(Pi[0], Pi[1], Pe[1], Pe[0])

    for s in range(n):
        for k in range(1, n_hiladas + 1):
            fila = filas.get((s, k), [])
            for (a, *_), (b, *_) in zip(fila, fila[1:]):
                g.add_arista(a, b, "junta_lateral")
            if k == 1:
                for nid, *_ in fila:
                    g.add_arista("clave_cierre", nid, "lecho" if j < 0.5 else "junta_radial",
                                 calcular_contacto=False)
            if k < n_hiladas:
                sup_fila = filas.get((s, k + 1), [])
                for a, ua0, ua1, _, qa1 in fila:
                    for b, ub0, ub1, *_ in sup_fila:
                        lo, hi = max(ua0, ub0), min(ua1, ub1)
                        if hi - lo > 1e-9:
                            moc_sup = k + 1 > n_cascara
                            tipo = "voladizo" if moc_sup else ("lecho" if j < 0.5 else "junta_radial")
                            j_ = 0.0 if moc_sup else j
                            t_ = t_m if moc_sup else t
                            g.add_arista(a, b, tipo, calcular_contacto=False,
                                         **junta_lecho(s, qa1, lo, hi, j_, t_))
            vecina = filas.get(((s + 1) % n, k), [])
            if fila and vecina:
                g.add_arista(fila[-1][0], vecina[0][0], "junta_lateral")

    # ---------------------------------------------------------------- nervios
    segmentos = []
    if 1 <= k_est <= n // 2:
        vistos = set()
        for i in range(n):
            par = frozenset((i, (i + k_est) % n))
            if par in vistos:
                continue
            vistos.add(par)
            segmentos.append(("cruceria", verts[i], verts[(i + k_est) % n]))
    if terceletes:
        for s in range(n):
            ligadura = 0.55 * A * normales[s]
            for v in (s, (s - 1) % n):
                segmentos.append(("tercelete", verts[v], ligadura))
            segmentos.append(("ligadura", ligadura, np.zeros(2)))
    if beta < 0.5 and h_r > 0:
        for s in range(n):
            segmentos.append(("formero", verts[(s - 1) % n], verts[s]))
    if h_r <= 0:
        segmentos = []

    # cortes de nervios en sus cruces -> claves
    cortes = [[0.0, 1.0] for _ in segmentos]
    claves = {}
    for a in range(len(segmentos)):
        for b in range(a + 1, len(segmentos)):
            ta = _interseccion(segmentos[a][1], segmentos[a][2], segmentos[b][1], segmentos[b][2])
            if ta is None:
                continue
            P = segmentos[a][1] + ta * (segmentos[a][2] - segmentos[a][1])
            d = segmentos[b][2] - segmentos[b][1]
            tb = float(np.dot(P - segmentos[b][1], d) / np.dot(d, d))
            cortes[a].append(ta)
            cortes[b].append(tb)
            claves.setdefault(tuple(np.round(P, 3)), set()).update({a, b})
    # extremos compartidos por varios nervios fuera de los vértices -> claves secundarias
    extremos = {}
    for i_s, (_, pa, pb) in enumerate(segmentos):
        for extremo in (pa, pb):
            if min(np.linalg.norm(verts - extremo, axis=1)) > 1e-6:
                extremos.setdefault(tuple(np.round(extremo, 3)), set()).add(i_s)
    for kc, segs in extremos.items():
        if len(segs) >= 2 or kc in claves or np.linalg.norm(kc) < 1e-6:
            claves.setdefault(kc, set()).update(segs)
    clave_ids = {}
    for i, (P, _) in enumerate(sorted(claves.items())):
        P = np.array(P)
        z0 = float(sup.z(P[0], P[1]))
        anillo_inf = np.column_stack([P + 0.9 * b_r * np.array([[np.cos(a), np.sin(a)] for a in
                                     np.linspace(0, 2 * np.pi, 9)[:-1]]), np.full(8, z0 - h_r)])
        anillo_sup = anillo_inf + np.array([0, 0, h_r])
        nid = f"clave_n{i:02d}"
        g.add_nodo(nid, "clave", prisma_entre(anillo_inf, anillo_sup), densidad=rho)
        clave_ids[tuple(np.round(P, 3))] = nid

    jarjas = {}
    if segmentos:
        for v, Pv in enumerate(verts):
            z0 = float(sup.z(Pv[0] * 0.999, Pv[1] * 0.999))
            base = np.column_stack([Pv + b_r * np.array([[1, 1], [-1, 1], [-1, -1], [1, -1]]) * 0.6,
                                    np.full(4, z0 - h_r)])
            nid = f"jarja_v{v}"
            g.add_nodo(nid, "jarja", prisma_entre(base, base + [0, 0, h_r + t]), densidad=rho, vertice=v)
            jarjas[v] = nid

    nervio_trazas = []
    for i_s, (familia, pa, pb) in enumerate(segmentos):
        ts = sorted(set(np.round(cortes[i_s], 9)))
        L = np.linalg.norm(pb - pa)
        params = []
        for t0, t1 in zip(ts, ts[1:]):
            m = max(1, int(round((t1 - t0) * L / ell)))
            params.extend(np.linspace(t0, t1, m + 1)[:-1])
        params.append(ts[-1])
        params = np.array(params)
        P2 = pa[None] + params[:, None] * (pb - pa)[None]
        if familia == "formero":
            P2 = P2 * 0.999
        P3 = env.intrados(P2)
        Tg = np.gradient(P3, axis=0)
        Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
        B = np.cross(Tg, [0, 0, 1])
        B /= np.linalg.norm(B, axis=1, keepdims=True)
        U = np.cross(B, Tg)
        U /= np.linalg.norm(U, axis=1, keepdims=True)
        sec = lambda i: np.array([P3[i] - b_r / 2 * B[i] - h_r * U[i], P3[i] + b_r / 2 * B[i] - h_r * U[i],  # noqa: E731
                                  P3[i] + b_r / 2 * B[i], P3[i] - b_r / 2 * B[i]])
        prev = None
        nervio_trazas.append((familia, pa, pb))
        for i in range(len(P2) - 1):
            Q0, Q1 = sec(i), sec(i + 1)
            geo = Poliedro(np.vstack([Q0, Q1]), [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2],
                                                  [2, 6, 7, 3], [3, 7, 4, 0]])
            nid = f"nerv_{i_s:02d}_{i:02d}"
            g.add_nodo(nid, "dovela_nervio", geo, densidad=rho, familia=familia, nervio=i_s)
            if prev:
                g.add_arista(prev, nid, "junta_radial")
            for extremo in (P2[i], P2[i + 1]):
                kc = tuple(np.round(extremo, 3))
                if kc in clave_ids:
                    g.add_arista(clave_ids[kc], nid, "encuentro_clave", calcular_contacto=False)
                for v, Pv in enumerate(verts):
                    if np.linalg.norm(extremo / (0.999 if familia == "formero" else 1) - Pv) < 1e-3 * R + 1e-6:
                        if v in jarjas:
                            g.add_arista(jarjas[v], nid, "arranque", calcular_contacto=False)
            prev = nid

    # plementos y celdas que apoyan en nervios
    if segmentos:
        ids = [nid for nid, d in g.nodos.items() if d["tipo"] in ("plemento", "celda_mocarabe")]
        C2 = np.array([g.nodos[nid]["centroide"][:2] for nid in ids])
        tam = np.array([g.nodos[nid]["extensiones_m"][0] for nid in ids])
        nervio_por_seg = {}
        for nid, d in g.nodos.items():
            if d["tipo"] == "dovela_nervio":
                nervio_por_seg.setdefault(d["nervio"], []).append(nid)
        for i_s, (_, pa, pb) in enumerate(segmentos):
            dist = _dist_segmento(C2, pa, pb)
            cerca = np.where(dist < 0.5 * tam + b_r / 2)[0]
            nervios = nervio_por_seg.get(i_s, [])
            if not nervios:
                continue
            NC = np.array([g.nodos[x]["centroide"][:2] for x in nervios])
            for i in cerca:
                mas_cerca = nervios[int(np.argmin(np.linalg.norm(NC - C2[i], axis=1)))]
                g.add_arista(ids[i], mas_cerca, "apoyo_nervio", calcular_contacto=False)

    # ---------------------------------------------------------------- apoyos
    if perimetral:
        for s in range(n):
            g.add_nodo(f"apoyo_lado{s}", "apoyo", soporte="muro_o_tambor")
            for nid, *_ in filas.get((s, n_hiladas), []):
                g.add_arista(nid, f"apoyo_lado{s}", "apoyo", calcular_contacto=False)
    for v in range(n):
        g.add_nodo(f"apoyo_v{v}", "apoyo", soporte="pilar")
        if v in jarjas:
            g.add_arista(jarjas[v], f"apoyo_v{v}", "apoyo", calcular_contacto=False)
        else:
            s_vecinos = (v, (v + 1) % n)
            for s in s_vecinos:
                fila = filas.get((s, n_hiladas), [])
                if fila:
                    extremo = fila[-1][0] if s == v else fila[0][0]
                    g.add_arista(extremo, f"apoyo_v{v}", "apoyo", calcular_contacto=False)

    # ---------------------------------------------------------------- sección (rebanada) para Heyman
    def constructor(escala):
        """Rebanada por la bisectriz de un sector (análisis por gajos de Heyman).

        escala multiplica todos los espesores (para el espesor mínimo)."""
        def puntos(q, j_, t_):
            P2 = np.array([[q, 0.0]])
            Pi = env.intrados(P2)[0]
            Pe = env.trasdos(P2, j=j_, t=t_ * escala)[0]
            return np.array([Pi[0], Pi[2]]), np.array([Pe[0], Pe[2]])
        qs = [(0.0, None)] + [(q, "c") for q in q_cas] + [(q, "m") for q in q_moc[1:]]
        juntas = []
        for q, zona in qs:
            if zona is None:
                zi = float(sup.z(0.0, 0.0))
                juntas.append((np.array([0.0, zi]), np.array([0.0, zi + t * escala])))
            else:
                j_, t_ = (j, t) if zona == "c" else (0.0, t_m)
                juntas.append(puntos(q, j_, t_))
        juntas = np.array(juntas)
        piezas = []
        for i in range(len(juntas) - 1):
            (a0, b0), (a1, b1) = juntas[i], juntas[i + 1]
            qq = np.linspace(a0[0], a1[0], 6)
            intr = np.column_stack([qq, sup.z(qq, 0 * qq)])
            zona_m = i >= len(q_cas)
            j_, t_ = (0.0, t_m) if zona_m else (j, t)
            ext = np.array([puntos(q, j_, t_)[1] for q in qq[1:-1]])[::-1]
            poli = np.vstack([intr, b1[None], ext, b0[None]]) if len(ext) else np.vstack([intr, b1, b0])
            x, z = poli[:, 0], poli[:, 1]
            cr = x * np.roll(z, -1) - np.roll(x, -1) * z
            area = cr.sum() / 2
            cx = ((x + np.roll(x, -1)) * cr).sum() / (6 * area)
            cz = ((z + np.roll(z, -1)) * cr).sum() / (6 * area)
            ancho = 2 * max(cx, 1e-6) * tan                        # anchura del gajo a esa distancia
            piezas.append((abs(area) * ancho * rho * G, cx, cz))
        return juntas, np.array(piezas)

    def z_trasdos(P2, iteraciones=8):
        """Cota del trasdós sobre cada punto de planta (inversión de la regla de juntas)."""
        P2 = np.atleast_2d(np.asarray(P2, float))
        P0 = P2.copy()
        E = None
        with np.errstate(invalid="ignore", divide="ignore"):
            for _ in range(iteraciones):
                _, q0, _ = sup.locales(P0[:, 0], P0[:, 1])
                moc = q0 > q_m
                E = np.where(moc[:, None], env.trasdos(P0, j=0.0, t=t_m), env.trasdos(P0))
                P0 = P0 + 0.7 * (P2 - E[:, :2])
                r = np.linalg.norm(P0, axis=1)
                P0 = np.where((r < 1e-6)[:, None], P2, P0)
            err = np.linalg.norm(E[:, :2] - P2, axis=1)
        z = E[:, 2]
        aprox = sup.z(P2[:, 0], P2[:, 1]) + t / np.clip(sup.normal(P2[:, 0], P2[:, 1])[:, 2], 0.3, 1)
        return np.where(np.isfinite(z) & (err < 0.02 * max(t, 1e-3) + 1e-4), z, aprox)

    genoma_norm = dict(gm)
    obra = Obra(id_, nombre, tradicion, genoma_norm, g, meta or {}, superficie=sup, espesor=t,
                seccion=constructor if perimetral else None)
    obra.z_trasdos = z_trasdos
    obra.meta.update({
        "luz_m": luz, "R_m": float(R), "apotema_m": float(A), "espesor_m": float(t),
        "espesor_mocarabe_m": float(t_m), "canto_nervio_m": float(h_r), "ancho_nervio_m": float(b_r),
        "q_mocarabe_m": float(q_m), "hiladas_cascara": int(n_cascara), "niveles_mocarabe": int(T),
        "salto_estrella": k_est, "apoyo_perimetral": perimetral, "densidad_kg_m3": rho,
        "nervios_planta": [(f, np.asarray(a).tolist(), np.asarray(b).tolist()) for f, a, b in nervio_trazas],
        "flecha_m": sup.flecha(),
    })
    return obra
