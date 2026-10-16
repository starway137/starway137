"""Análisis de equilibrio por el teorema del límite inferior (Heyman, 1966).

Hipótesis de Heyman para fábricas: (1) resistencia a compresión ilimitada,
(2) resistencia a tracción nula, (3) no hay deslizamiento entre piezas.
Teorema de la seguridad: si existe UNA distribución de esfuerzos en
equilibrio con las cargas y contenida dentro de la fábrica, la estructura es
segura. Por tanto basta encontrar una solución admisible; las que no se
encuentran no prueban el colapso (el resultado es conservador).

Herramientas:
  linea_empujes       arcos y rebanadas 2D con juntas de cualquier orientación
                      (radiales -> dovelas; horizontales -> voladizos/mocárabes)
  espesor_minimo      bisección del espesor -> coeficiente geométrico de
                      seguridad GSF = t / t_min
  red_empujes_*       Thrust Network Analysis (Block 2009) con diagrama de
                      forma en equilibrio horizontal y equilibrio vertical por
                      densidades de fuerza (Schek 1974)
  estribo             vuelco y posición de la resultante en el estribo
"""

import numpy as np

G = 9.81


# ======================================================================== 2D
def linea_empujes(juntas, piezas, n_H=600, n_s=201, mu=None):
    """Busca líneas de empujes admisibles en un semiarco (o rebanada).

    juntas : (n+1, 2, 2) — juntas ordenadas desde la clave (0) hasta el
             arranque (n); [i, 0] = punto de intradós, [i, 1] = trasdós (x, z).
    piezas : (n, 3) o (n, 4) — peso w_k [N], punto de aplicación (x_k, z_k)
             de la pieza situada entre la junta k y la k+1 y, opcionalmente,
             una carga horizontal f_k [N] (positiva hacia el arranque), p. ej.
             el empuje que los plementos transmiten a un nervio.
    La clave recibe un empuje horizontal H (simetría) aplicado en un punto de
    la junta 0 a la fracción s0 de su longitud. Se recorre una malla (H, s0)
    y se calcula, en cada junta, la fracción s_i donde la corta la resultante;
    la solución es admisible si 0 <= s_i <= 1 en todas las juntas.
    mu : coeficiente de rozamiento opcional (comprueba el no-deslizamiento).
    """
    J = np.asarray(juntas, float)
    P = np.asarray(piezas, float)
    a, d = J[:, 0], J[:, 1] - J[:, 0]
    w, cx, cz = P[:, 0], P[:, 1], P[:, 2]
    fx = P[:, 3] if P.shape[1] > 3 else np.zeros(len(P))
    Wtot = w.sum()
    W = np.concatenate([[0.0], np.cumsum(w)])
    FX = np.concatenate([[0.0], np.cumsum(fx)])
    S = np.concatenate([[0.0], np.cumsum(w * cx + fx * cz)])

    Hs = np.concatenate([[0.0], Wtot * np.logspace(-3, 1.5, n_H - 1)])
    s0 = np.linspace(0, 1, n_s)
    H = Hs[:, None, None]
    p0z = (a[0, 1] + s0 * d[0, 1])[None, :, None]
    M = -p0z * H - S[None, None, :]
    Fx, Fz = H + FX[None, None, :], -W[None, None, :]
    cross_a = a[:, 0] * Fz - a[:, 1] * Fx
    cross_d = d[:, 0] * Fz - d[:, 1] * Fx
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (M - cross_a) / cross_d
    s = s[:, :, 1:]                                   # la junta 0 es s0 por construcción
    ok = np.isfinite(s) & (s >= -1e-9) & (s <= 1 + 1e-9)
    if mu is not None:
        n_j = np.stack([-d[1:, 1], d[1:, 0]], axis=-1)
        n_j /= np.linalg.norm(n_j, axis=-1, keepdims=True)
        t_j = d[1:] / np.linalg.norm(d[1:], axis=-1, keepdims=True)
        Fn = np.abs(Fx[..., 1:] * n_j[:, 0] + Fz[..., 1:] * n_j[:, 1])
        Ft = np.abs(Fx[..., 1:] * t_j[:, 0] + Fz[..., 1:] * t_j[:, 1])
        ok &= Ft <= mu * Fn + 1e-9
    factible = ok.all(axis=2)
    if not factible.any():
        return {"admisible": False, "W_total_N": float(Wtot)}

    margen = np.where(ok, np.minimum(s, 1 - s), -np.inf).min(axis=2)
    margen = np.where(factible, margen, -np.inf)
    iH, iS = np.unravel_index(np.argmax(margen), margen.shape)
    filas = np.where(factible.any(axis=1))[0]
    iHmin = filas[0]
    iSmin = int(np.argmax(np.where(factible[iHmin], margen[iHmin], -np.inf)))

    def estado(i_h, i_s):
        si = np.concatenate([[s0[i_s]], s[i_h, i_s]])
        pts = a + si[:, None] * d
        return {"H_N": float(Hs[i_h]), "s0": float(s0[i_s]),
                "fracciones": si.round(4).tolist(), "puntos": pts.round(4).tolist(),
                "margen_min": float(np.minimum(si, 1 - si).min())}

    return {
        "admisible": True,
        "W_total_N": float(Wtot),
        "H_min_N": float(Hs[filas[0]]),
        "H_max_N": float(Hs[filas[-1]]),
        "empuje_minimo": estado(iHmin, iSmin),
        "maximo_margen": estado(iH, iS),
    }


def espesor_minimo(constructor, t_actual, t_bajo=None, iter_=16, **kw):
    """Bisección del espesor mínimo con línea de empujes admisible.

    constructor(t) -> (juntas, piezas). Devuelve t_min y GSF = t_actual / t_min.
    """
    t_bajo = t_bajo or t_actual * 0.02
    alto = t_actual
    if not linea_empujes(*constructor(alto), **kw)["admisible"]:
        for _ in range(6):
            alto *= 1.6
            if linea_empujes(*constructor(alto), **kw)["admisible"]:
                break
        else:
            return {"t_min_m": None, "GSF": 0.0, "nota": "sin solución admisible hasta 16x el espesor"}
    bajo = t_bajo
    for _ in range(iter_):
        medio = 0.5 * (bajo + alto)
        if linea_empujes(*constructor(medio), **kw)["admisible"]:
            alto = medio
        else:
            bajo = medio
    return {"t_min_m": alto, "GSF": t_actual / alto}


# ======================================================================== TNA 3D
def matriz_incidencia(n_nodos, aristas):
    C = np.zeros((len(aristas), n_nodos))
    for k, (i, j) in enumerate(aristas):
        C[k, i], C[k, j] = 1.0, -1.0
    return C


def fdm(xy, aristas, q, fijos, cargas, z_fijos=None):
    """Equilibrio vertical por densidades de fuerza: D_ff z_f = P_f - D_fs z_s.

    Convención de compresión: un nodo más alto que sus vecinos transmite su
    carga P (positiva hacia abajo) por compresión de sus aristas.
    Devuelve z y el residuo del equilibrio horizontal en los nodos libres.
    """
    n = len(xy)
    C = matriz_incidencia(n, aristas)
    D = C.T @ (q[:, None] * C)
    libres = ~fijos
    zs = np.zeros(fijos.sum()) if z_fijos is None else z_fijos
    z = np.zeros(n)
    z[fijos] = zs
    z[libres] = np.linalg.solve(D[np.ix_(libres, libres)], cargas[libres] - D[np.ix_(libres, fijos)] @ zs)
    res = D[libres] @ xy
    return z, float(np.abs(res).max()) if len(res) else 0.0


def diagrama_arista(n, R, anillos):
    """Diagrama de forma para bóveda de arista/crucería sobre polígono regular.

    Líneas de plemento paralelas a cada lado (los arcos de la plementería)
    acometen a los nervios diagonales, que llevan la carga a los vértices.
    Devuelve nodos (x, y), aristas, familia de cada arista, apoyos y nodos
    diagonales; la densidad de los nervios se obtiene imponiendo el
    equilibrio horizontal en cada nodo diagonal.
    """
    A = R * np.cos(np.pi / n)
    tan = np.tan(np.pi / n)
    h = A / anillos
    nodos = [(0.0, 0.0)]
    diag = {}
    for v in range(n):
        th = 2 * np.pi * v / n + np.pi / n
        e = np.array([np.cos(th), np.sin(th)])
        for k in range(1, anillos + 1):
            diag[(v, k)] = len(nodos)
            nodos.append(tuple(e * R * k / anillos))
    aristas, familia = [], []
    for v in range(n):
        prev = 0
        for k in range(1, anillos + 1):
            aristas.append((prev, diag[(v, k)]))
            familia.append(("diagonal", v, k))
            prev = diag[(v, k)]
    for s in range(n):
        ns = np.array([np.cos(2 * np.pi * s / n), np.sin(2 * np.pi * s / n)])
        ts = np.array([-ns[1], ns[0]])
        v_izq, v_der = (s - 1) % n, s
        for k in range(1, anillos):
            qv = A * k / anillos
            m = max(0, int(round(2 * qv * tan / h)) - 1)
            cadena = [diag[(v_izq, k)]]
            for i in range(1, m + 1):
                vv = -qv * tan + 2 * qv * tan * i / (m + 1)
                cadena.append(len(nodos))
                nodos.append(tuple(qv * ns + vv * ts))
            cadena.append(diag[(v_der, k)])
            for a, b in zip(cadena, cadena[1:]):
                aristas.append((a, b))
                familia.append(("plemento", s, k))
    xy = np.array(nodos)
    apoyos = np.zeros(len(xy), bool)
    for v in range(n):
        apoyos[diag[(v, anillos)]] = True
    dg = {"xy": xy, "aristas": aristas, "familia": familia, "apoyos": apoyos,
          "diag": diag, "n": n, "anillos": anillos, "R": R, "n_par": anillos}
    dg["densidades"] = lambda x: densidades_arista(dg, np.exp(x[:-1]), np.exp(x[-1]))
    dg["semillas"] = [np.append(pend * np.linspace(0, 1, anillos - 1), lg)
                      for pend in (-4.0, -2.5, -1.0, 0.0, 1.0) for lg in (-3.0, -1.0, 1.0, 3.0)]
    return dg


def diagrama_cupula(n, R, anillos):
    """Diagrama de forma meridianos + anillos para cúpulas sobre polígono regular.

    2n meridianos por los ejes de simetría (centros de lado y vértices) y
    anillos semejantes al polígono. Al estar cada nodo sobre un eje de
    simetría, los dos tramos de anillo que concurren dan una resultante
    radial, equilibrada por la diferencia de empuje del meridiano. Los anillos
    sólo pueden comprimirse (q >= 0): sin tracciones, hipótesis de Heyman.
    Apoyo continuo en el perímetro (muro o tambor).
    """
    A = R * np.cos(np.pi / n)
    nodos = [(0.0, 0.0)]
    idx = {}
    for m in range(2 * n):
        th = m * np.pi / n
        borde = A if m % 2 == 0 else R
        e = np.array([np.cos(th), np.sin(th)])
        for k in range(1, anillos + 1):
            idx[(m, k)] = len(nodos)
            nodos.append(tuple(e * borde * k / anillos))
    aristas, familia = [], []
    for m in range(2 * n):
        prev = 0
        for k in range(1, anillos + 1):
            aristas.append((prev, idx[(m, k)]))
            familia.append(("meridiano", m, k))
            prev = idx[(m, k)]
    for k in range(1, anillos):
        for m in range(2 * n):
            aristas.append((idx[(m, k)], idx[((m + 1) % (2 * n), k)]))
            familia.append(("anillo", m, k))
    xy = np.array(nodos)
    apoyos = np.zeros(len(xy), bool)
    for m in range(2 * n):
        apoyos[idx[(m, anillos)]] = True

    def densidades(x):
        """x = [log q de cada anillo (anillos-1), log γ_lado, log γ_vértice]."""
        q = np.zeros(len(aristas))
        qa = np.exp(x[:anillos - 1])
        idx_m = {}
        for e, f in enumerate(familia):
            if f[0] == "anillo":
                q[e] = qa[f[2] - 1]
            else:
                idx_m[(f[1], f[2])] = e
        incid = {}
        for e, (i, j) in enumerate(aristas):
            incid.setdefault(i, []).append(e)
            incid.setdefault(j, []).append(e)
        for m in range(2 * n):
            q[idx_m[(m, 1)]] = np.exp(x[anillos - 1 + (m % 2)])
            for k in range(1, anillos):
                nodo = idx[(m, k)]
                e_out = idx_m[(m, k + 1)]
                fuerza = np.zeros(2)
                for e in incid[nodo]:
                    if e == e_out:
                        continue
                    i, j = aristas[e]
                    fuerza += q[e] * (xy[j if i == nodo else i] - xy[nodo])
                d = xy[idx[(m, k + 1)]] - xy[nodo]
                q[e_out] = -np.dot(fuerza, d) / np.dot(d, d)
        return q

    return {"xy": xy, "aristas": aristas, "familia": familia, "apoyos": apoyos, "n": n,
            "anillos": anillos, "R": R, "densidades": densidades, "n_par": anillos + 1,
            "semillas": [np.concatenate([np.full(anillos - 1, la), [lg, lg]])
                         for la in (-3.0, -1.0, 0.5) for lg in (-1.0, 1.0, 3.0)]}


def densidades_arista(dg, q_lineas, gamma):
    """Densidades de fuerza: q de cada línea de plemento (constante a lo largo
    de la línea, condición de equilibrio en sus nodos interiores) y q de los
    nervios diagonales obtenida imponiendo el equilibrio horizontal en cada
    nodo diagonal, desde la clave hacia los apoyos.

    q_lineas: escalar, o array de longitud anillos-1 (una por anillo).
    """
    xy, ar, fam = dg["xy"], dg["aristas"], dg["familia"]
    q_lineas = np.broadcast_to(np.asarray(q_lineas, float), (dg["anillos"] - 1,))
    q = np.zeros(len(ar))
    idx_diag = {}
    for e, f in enumerate(fam):
        if f[0] == "plemento":
            q[e] = q_lineas[f[2] - 1]
        else:
            idx_diag[(f[1], f[2])] = e
    incid = {}
    for e, (i, j) in enumerate(ar):
        incid.setdefault(i, []).append(e)
        incid.setdefault(j, []).append(e)
    for v in range(dg["n"]):
        q[idx_diag[(v, 1)]] = gamma
        for k in range(1, dg["anillos"]):
            nodo = dg["diag"][(v, k)]
            e_out = idx_diag[(v, k + 1)]
            fuerza = np.zeros(2)
            for e in incid[nodo]:
                if e == e_out:
                    continue
                i, j = ar[e]
                otro = j if i == nodo else i
                fuerza += q[e] * (xy[otro] - xy[nodo])
            dir_out = xy[dg["diag"][(v, k + 1)]] - xy[nodo]
            q[e_out] = -np.dot(fuerza, dir_out) / np.dot(dir_out, dir_out)
    return q


def cargas_por_raster(xy, puntos, pesos):
    """Asigna cada carga puntual (p. ej. celdas de un ráster de la planta) al
    nodo más cercano del diagrama de forma."""
    cargas = np.zeros(len(xy))
    for i0 in range(0, len(puntos), 4000):
        bloque = puntos[i0:i0 + 4000]
        d2 = ((bloque[:, None, :] - xy[None, :, :]) ** 2).sum(-1)
        np.add.at(cargas, d2.argmin(axis=1), pesos[i0:i0 + 4000])
    return cargas


def ajuste_envolvente(u, z_inf, z_sup, libres):
    """Intervalo de escala λ (z = u/λ) con la red dentro de [z_inf, z_sup].

    λ es proporcional al empuje horizontal: λ_min -> empuje mínimo.
    """
    u, zi, zs = u[libres], z_inf[libres], z_sup[libres]
    if (u <= 0).any():
        return None
    lam_lo = (u / zs).max()
    mask = zi > 1e-9
    lam_hi = (u[mask] / zi[mask]).min() if mask.any() else np.inf
    return (lam_lo, lam_hi) if lam_lo <= lam_hi else None


def _holgura(u, z_inf, z_sup, libres):
    """log(λ_hi / λ_lo): > 0 si la red cabe en la fábrica (medida continua)."""
    u, zi, zs = u[libres], z_inf[libres], z_sup[libres]
    if (u <= 0).any():
        return -np.inf
    lo = (u / zs).max()
    m = zi > 1e-9
    hi = (u[m] / zi[m]).min() if m.any() else np.inf
    return float(np.log(hi / lo))


def _gsf(u, z_inf, z_sup, libres):
    z_mid, semi = 0.5 * (z_inf + z_sup), 0.5 * (z_sup - z_inf)
    lo, hi = 0.0, 4.0
    if ajuste_envolvente(u, z_mid - hi * semi, z_mid + hi * semi, libres) is None:
        return 0.0
    for _ in range(30):
        m = 0.5 * (lo + hi)
        if ajuste_envolvente(u, z_mid - m * semi, z_mid + m * semi, libres):
            hi = m
        else:
            lo = m
    return 1.0 / hi


def _holgura_suave(u, z_inf, z_sup, libres, p=30.0):
    """Holgura con máximo/mínimo suavizados (log-sum-exp) para optimizar."""
    u, zi, zs = u[libres], z_inf[libres], z_sup[libres]
    if (u <= 0).any():
        return -np.inf
    a = np.log(u / zs)
    m = zi > 1e-9
    b = np.log(u[m] / zi[m])
    lo = a.max() + np.log(np.exp(p * (a - a.max())).sum()) / p
    hi = b.min() - np.log(np.exp(-p * (b - b.min())).sum()) / p
    return float(hi - lo)


def _nelder_mead(f, x0, paso=0.8, iters=400, tol=1e-6):
    n = len(x0)
    S = [np.array(x0, float)] + [np.array(x0, float) + paso * np.eye(n)[i] for i in range(n)]
    F = [f(x) for x in S]
    for _ in range(iters):
        orden = np.argsort(F)[::-1]                       # maximización
        S, F = [S[i] for i in orden], [F[i] for i in orden]
        if abs(F[0] - F[-1]) < tol and np.isfinite(F[0]):
            break
        c = np.mean(S[:-1], axis=0)
        xr = c + (c - S[-1])
        fr = f(xr)
        if fr > F[0]:
            xe = c + 2 * (c - S[-1])
            fe = f(xe)
            S[-1], F[-1] = (xe, fe) if fe > fr else (xr, fr)
        elif fr > F[-2]:
            S[-1], F[-1] = xr, fr
        else:
            xc = c + 0.5 * (S[-1] - c)
            fc = f(xc)
            if fc > F[-1]:
                S[-1], F[-1] = xc, fc
            else:
                S = [S[0]] + [S[0] + 0.5 * (x - S[0]) for x in S[1:]]
                F = [F[0]] + [f(x) for x in S[1:]]
    i = int(np.argmax(F))
    return S[i], F[i]


def red_empujes(dg, cargas, z_inf, z_sup):
    """TNA: optimiza el diagrama de fuerzas (log q de cada línea de plemento y
    del arranque de los nervios) maximizando la holgura de la red dentro de la
    fábrica (Nelder-Mead sobre una holgura suavizada, varias semillas).
    Devuelve la mejor red, el rango de empujes compatible y el GSF."""
    libres = ~dg["apoyos"]
    cache = {}

    def red(x):
        k = tuple(np.round(x, 9))
        if k not in cache:
            q = dg["densidades"](x)
            if (q <= 0).any():
                cache[k] = (None, None)
            else:
                u, res = fdm(dg["xy"], dg["aristas"], q, dg["apoyos"], cargas)
                ok = res <= 1e-6 * max(1.0, np.abs(q).max() * dg["R"])
                cache[k] = (q, u) if ok else (None, None)
        return cache[k]

    def objetivo(x):
        q, u = red(x)
        return -np.inf if q is None else _holgura_suave(u, z_inf, z_sup, libres)

    semillas = sorted(dg["semillas"], key=objetivo, reverse=True)
    mejor_x, mejor_f = None, -np.inf
    for x0 in semillas[:3]:
        x, fx = _nelder_mead(objetivo, x0)
        if fx > mejor_f:
            mejor_x, mejor_f = x, fx
    if mejor_x is None:
        return {"admisible": False, "GSF": 0.0}
    q, u = red(mejor_x)
    if q is None:
        return {"admisible": False, "GSF": 0.0}
    hol = _holgura(u, z_inf, z_sup, libres)
    gsf = _gsf(u, z_inf, z_sup, libres)
    rango = ajuste_envolvente(u, z_inf, z_sup, libres)
    salida = {"admisible": rango is not None, "GSF": gsf, "holgura": hol,
              "parametros_log_q": np.round(mejor_x, 5).tolist(),
              "n_nodos": int(len(u)), "n_aristas": len(dg["aristas"])}
    if rango is None:
        return salida
    lam_min, lam_max = rango
    C = matriz_incidencia(len(u), dg["aristas"])
    fuerzas_planta = (q / lam_min)[:, None] * (C @ dg["xy"])
    reacciones = []
    for nodo in np.where(dg["apoyos"])[0]:
        h = np.zeros(2)
        for e, (i, j) in enumerate(dg["aristas"]):
            if nodo in (i, j):
                h += fuerzas_planta[e] * (1 if i == nodo else -1)
        reacciones.append(float(np.linalg.norm(h)))
    salida.update({
        "lambda_min": float(lam_min), "lambda_max": float(lam_max),
        "relacion_empuje_max_min": float(lam_max / lam_min),
        "empuje_horizontal_min_por_apoyo_N": float(np.mean(reacciones)),
        "reaccion_vertical_por_apoyo_N": float(cargas.sum() / dg["apoyos"].sum()),
        "z_red": (u / lam_min).round(4).tolist(),
    })
    return salida


# ======================================================================== estribo
def estribo(H, V, h_arranque, ancho, fondo, alto, densidad):
    """Vuelco del estribo y posición de la resultante en su base (límite inferior)."""
    Wb = densidad * G * ancho * fondo * alto
    M_estab = Wb * ancho / 2 + V * ancho
    M_vuelco = H * h_arranque
    x_res = (M_estab - M_vuelco) / (Wb + V)
    return {"peso_estribo_N": Wb, "FS_vuelco": M_estab / M_vuelco if M_vuelco > 0 else np.inf,
            "resultante_desde_borde_exterior_m": x_res, "en_nucleo_central": ancho / 3 <= x_res <= 2 * ancho / 3,
            "admisible": 0 <= x_res <= ancho}
