"""Verificación estructural de una obra por el límite inferior.

Métodos (basta UNO admisible para declarar la obra segura, teorema de Heyman):
    arco      línea de empujes del semiarco + espesor mínimo (GSF)
    tna       red de empujes 3D sobre diagrama de arista/crucería (Block 2009)
    rebanada  gajo por la bisectriz de un sector (Heyman, cúpulas por gajos):
              ignora los esfuerzos de anillo, luego es conservador

Para cada obra se registran todos los métodos aplicables y se toma el mayor
GSF admisible. Que un método no encuentre solución no prueba el colapso.
"""

import numpy as np

from . import tna
from .generadores.arco import semiarco
from .superficie import centro_radio

G = 9.81
MU = 0.7                 # rozamiento piedra-piedra (comprobación de no deslizamiento)
RHO_RELLENO = 1800.0     # relleno de senos (cascote y mortero)


def _arco(obra):
    t = obra.espesor
    em = tna.espesor_minimo(obra.seccion, t, t_bajo=0.05 * t)
    juntas, piezas = obra.seccion(t)
    sin = tna.linea_empujes(juntas, piezas)
    con = tna.linea_empujes(juntas, piezas, mu=MU)
    luz = obra.grafo.atributos["luz_m"]
    p = obra.genoma["apuntamiento"]
    _, polis = semiarco(luz / 2, p, t, len(piezas), obra.genoma["inclinacion_junta"])
    obra.meta["_seccion_dibujo"] = (juntas, polis, sin.get("maximo_margen", {}).get("puntos"))
    Rm = centro_radio(luz / 2, p)[1] + (em["t_min_m"] or 0) / 2
    return {"metodo": "arco", "admisible": sin["admisible"], "GSF": em["GSF"],
            "t_min_m": em["t_min_m"], "t_min_sobre_R": (em["t_min_m"] / Rm) if em["t_min_m"] else None,
            "con_rozamiento": con["admisible"],
            "H_min_kN": sin.get("H_min_N", 0) / 1e3 if sin["admisible"] else None,
            "H_max_kN": sin.get("H_max_N", 0) / 1e3 if sin["admisible"] else None}


def _tna(obra, anillos=10, diagrama="arista"):
    m = obra.meta
    sup = obra.superficie
    n = sup.n
    dg = (tna.diagrama_arista if diagrama == "arista" else tna.diagrama_cupula)(n, sup.R, anillos)
    rho = m["densidad_kg_m3"]
    paso = sup.A / 45
    X, Y = sup.raster(paso)
    gx, gy = sup.gradiente(X, Y)
    _, q, _ = sup.locales(X, Y)
    t_eff = np.where(q > m["q_mocarabe_m"], m["espesor_mocarabe_m"], m["espesor_m"])
    pesos = rho * G * t_eff * np.sqrt(1 + gx ** 2 + gy ** 2) * paso ** 2
    puntos = np.column_stack([X, Y])
    segs = [(np.array(a), np.array(b)) for _, a, b in m["nervios_planta"]]
    h_r, b_r = m["canto_nervio_m"], m["ancho_nervio_m"]
    if segs and h_r > 0:
        extra_p, extra_w = [], []
        for a, b in segs:
            L = np.linalg.norm(b - a)
            k = max(2, int(L / paso))
            s = (np.arange(k) + 0.5) / k
            extra_p.append(a[None] + s[:, None] * (b - a)[None])
            extra_w.append(np.full(k, rho * G * h_r * b_r * L / k))
        puntos = np.vstack([puntos] + extra_p)
        pesos = np.concatenate([pesos] + extra_w)
    # relleno de senos hasta la cota z_f = relleno_rel · flecha (Heyman; Huerta 2004)
    z_f = m.get("relleno_rel", 0.0) * sup.flecha()
    if z_f > 0:
        Zi = sup.z(X, Y)
        Nz = 1 / np.sqrt(1 + gx ** 2 + gy ** 2)
        z_ext = Zi + t_eff / Nz
        h_rell = np.clip(z_f - z_ext, 0, None)
        puntos = np.vstack([puntos, np.column_stack([X, Y])])
        pesos = np.concatenate([pesos, RHO_RELLENO * G * h_rell * paso ** 2])
    cargas = tna.cargas_por_raster(dg["xy"], puntos, pesos)
    xy = dg["xy"] * 0.999
    zi = sup.z(xy[:, 0], xy[:, 1])
    N = sup.normal(xy[:, 0], xy[:, 1])
    _, qn, _ = sup.locales(xy[:, 0], xy[:, 1])
    t_n = np.where(qn > m["q_mocarabe_m"], m["espesor_mocarabe_m"], m["espesor_m"])
    if obra.z_trasdos is not None:
        z_sup = np.maximum(obra.z_trasdos(xy), zi + t_n)        # trasdós exacto según la regla de juntas
    else:
        z_sup = zi + np.minimum(t_n / np.maximum(N[:, 2], 1e-3), 3 * t_n)
    if z_f > 0:
        z_sup = np.maximum(z_sup, z_f)                       # la red puede pasar por el relleno
    z_inf = zi.copy()
    if segs and h_r > 0:
        cerca = np.zeros(len(xy), bool)
        for a, b in segs:
            ab = b - a
            tt = np.clip(((xy - a) @ ab) / (ab @ ab), 0, 1)
            cerca |= np.linalg.norm(xy - (a + tt[:, None] * ab), axis=1) < b_r / 2 + 1e-6
        z_inf = np.where(cerca, zi - h_r, zi)
    r = tna.red_empujes(dg, cargas, z_inf, z_sup)
    r["metodo"] = "tna" if diagrama == "arista" else "tna_anillos"
    r["carga_total_kN"] = float(cargas.sum() / 1e3)
    if r.get("admisible"):
        r["empuje_min_por_apoyo_kN"] = r["empuje_horizontal_min_por_apoyo_N"] / 1e3
        r["reaccion_vertical_por_apoyo_kN"] = r["reaccion_vertical_por_apoyo_N"] / 1e3
        obra.meta["_red"] = (dg, np.array(r["z_red"]))
    r.pop("z_red", None)
    return r


def _seccion_perfil(P2, sup, t_arriba, t_abajo, ancho, rho, fx=None, w_extra=None):
    """Sección 2D a lo largo de una directriz en planta P2 (desde la clave).

    Coordenadas locales (s, z): s = distancia en planta desde la clave. Juntas
    normales a la directriz; la fábrica va de t_abajo bajo el intradós a
    t_arriba sobre él. Devuelve juntas, piezas (w, x, z, fx) y polígonos.
    """
    s_ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P2, axis=0), axis=1))])
    z = sup.z(P2[:, 0] * 0.999, P2[:, 1] * 0.999)
    dz = np.gradient(z, s_)
    dz[0] = 0.0                                              # clave simétrica: tangente horizontal
    N = np.column_stack([-dz, np.ones_like(dz)])
    N /= np.linalg.norm(N, axis=1, keepdims=True)
    C = np.column_stack([s_, z])
    a, b = C - t_abajo * N, C + t_arriba * N
    juntas = np.stack([a, b], axis=1)
    piezas, polis = [], []
    for i in range(len(C) - 1):
        poli = np.array([a[i], a[i + 1], b[i + 1], b[i]])
        x, y = poli[:, 0], poli[:, 1]
        cr = x * np.roll(y, -1) - np.roll(x, -1) * y
        A = cr.sum() / 2
        cx = ((x + np.roll(x, -1)) * cr).sum() / (6 * A)
        cz = ((y + np.roll(y, -1)) * cr).sum() / (6 * A)
        w = abs(A) * ancho * rho * G + (0.0 if w_extra is None else w_extra[i])
        piezas.append((w, cx, cz, 0.0 if fx is None else fx[i]))
        polis.append(poli)
    return juntas, np.array(piezas), polis


def _cortes(obra, franjas=10):
    """Método de los cortes (Heyman) para bóvedas de arista y crucería.

    La plementería se corta en franjas paralelas a cada lado; cada franja es un
    arco entre nervios diagonales con su propia línea de empujes. Los nervios
    diagonales son arcos cargados con las reacciones de los plementos (peso y
    empuje horizontal proyectado). Si todos son admisibles existe un campo de
    esfuerzos estáticamente admisible: límite inferior.
    """
    m, sup = obra.meta, obra.superficie
    n, A, R = sup.n, sup.A, sup.R
    rho = m["densidad_kg_m3"]
    hay_diagonales = m.get("salto_estrella") == n // 2 and m["canto_nervio_m"] > 0
    ancho_n = m["ancho_nervio_m"] if hay_diagonales else 4 * m["espesor_m"]
    n0 = np.array([1.0, 0.0])
    t0 = np.array([0.0, 1.0])
    e = np.array([np.cos(np.pi / n), np.sin(np.pi / n)])
    tan = np.tan(np.pi / n)
    dq = A / franjas
    qs = (np.arange(franjas) + 0.5) * dq

    def evaluar(esc):
        t = m["espesor_m"] * esc
        h_r = (m["canto_nervio_m"] if hay_diagonales else 0.0) * esc
        cargas_v, cargas_h, rho_k = [], [], []
        for q in qs:
            v_fin = q * tan
            k = max(4, int(np.ceil(v_fin / 0.2)))
            v = np.linspace(0, v_fin, k + 1)
            P2 = q * n0[None] + v[:, None] * t0[None]
            jj, pz, _ = _seccion_perfil(P2, sup, t, 0.0, dq, rho)
            r = tna.linea_empujes(jj, pz, n_H=300, n_s=81)
            if not r["admisible"]:
                return None
            cargas_v.append(2 * r["W_total_N"])
            cargas_h.append(2 * r["H_min_N"] * np.sin(np.pi / n))
            rho_k.append(q / np.cos(np.pi / n))
        rr = np.linspace(0, R, 2 * franjas + 1)
        P2 = rr[:, None] * e[None]
        w_extra = np.zeros(len(rr) - 1)
        fx = np.zeros(len(rr) - 1)
        mid = 0.5 * (rr[1:] + rr[:-1])
        for V, Hh, rk in zip(cargas_v, cargas_h, rho_k):
            i = int(np.argmin(np.abs(mid - rk)))
            w_extra[i] += V
            fx[i] += Hh
        jj, pz, polis = _seccion_perfil(P2, sup, t, h_r, ancho_n, rho, fx=fx, w_extra=w_extra)
        r = tna.linea_empujes(jj, pz)
        if not r["admisible"]:
            return None
        return r, (jj, polis)

    base = evaluar(1.0)
    lo, hi = 0.05, 1.0
    if base is None:
        hi = 1.0
        while hi < 4.0 and evaluar(hi) is None:
            hi *= 1.4
        if hi >= 4.0:
            return {"metodo": "cortes", "admisible": False, "GSF": 0.0}
        lo = hi / 1.4
    for _ in range(12):
        mid_ = 0.5 * (lo + hi)
        if evaluar(mid_) is None:
            lo = mid_
        else:
            hi = mid_
    salida = {"metodo": "cortes", "admisible": base is not None, "GSF": 1.0 / hi, "franjas": franjas,
              "diagonales": "nervio" if hay_diagonales else "arista"}
    if base is not None:
        r, (jj, polis) = base
        salida.update({"empuje_nervio_clave_kN": r["empuje_minimo"]["H_N"] / 1e3,
                       "empuje_horizontal_min_por_apoyo_N": r["empuje_minimo"]["H_N"] + 0.0,
                       "reaccion_vertical_por_apoyo_N": r["W_total_N"]})
        obra.meta["_seccion_dibujo"] = (jj, polis, r["maximo_margen"]["puntos"])
    return salida


def _rebanada(obra):
    em = tna.espesor_minimo(obra.seccion, 1.0, t_bajo=0.03)
    juntas, piezas = obra.seccion(1.0)
    sin = tna.linea_empujes(juntas, piezas)
    con = tna.linea_empujes(juntas, piezas, mu=MU)
    return {"metodo": "rebanada", "admisible": sin["admisible"], "GSF": em["GSF"],
            "con_rozamiento": con["admisible"],
            "H_clave_kN": sin.get("empuje_minimo", {}).get("H_N", 0) / 1e3 if sin["admisible"] else None}


def estructura(obra):
    if obra.grafo.atributos.get("tipologia") == "arco":
        metodos = [_arco(obra)]
    else:
        metodos = [_tna(obra)]
        if obra.seccion is not None:
            metodos.append(_tna(obra, diagrama="cupula"))
            metodos.append(_rebanada(obra))
        if obra.superficie.beta < 0.5:
            metodos.append(_cortes(obra))
    adm = [m for m in metodos if m.get("admisible")]
    mejor = max(adm, key=lambda m: m["GSF"]) if adm else max(metodos, key=lambda m: m.get("GSF", 0))
    salida = {"admisible": bool(adm), "GSF": float(mejor.get("GSF", 0.0)) if adm else 0.0,
              "metodo": mejor["metodo"] if adm else "ninguno", "metodos": metodos}
    if obra.grafo.atributos.get("tipologia") != "arco" and not obra.meta.get("apoyo_perimetral"):
        t_ = next((m for m in metodos if m["metodo"] in ("tna", "cortes") and m.get("admisible")), None)
        if t_:
            luz = obra.meta["luz_m"]
            salida["estribo_referencia"] = tna.estribo(
                H=t_["empuje_horizontal_min_por_apoyo_N"], V=t_["reaccion_vertical_por_apoyo_N"],
                h_arranque=1.2 * luz, ancho=0.3 * luz, fondo=0.15 * luz, alto=1.2 * luz,
                densidad=obra.meta["densidad_kg_m3"])
            salida["estribo_referencia"]["dimensiones"] = "ancho 0.30 L, fondo 0.15 L, arranque a 1.2 L"
    return salida
