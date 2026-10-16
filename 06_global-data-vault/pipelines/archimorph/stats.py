"""Regresión lineal con inferencia clásica, bootstrap y validación cruzada.

Se implementa la distribución t de Student con la función beta incompleta
regularizada (fracción continua de Lentz) para no depender de scipy.
"""

import math

import numpy as np


# ---------------------------------------------------------------- t de Student
def _betacf(a, b, x, max_iter=300, eps=3e-14):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c if abs(1.0 + aa / c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1 - x))
    bt = math.exp(ln_bt)
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2, 0.5, x)
    return 1 - tail if t >= 0 else tail


def t_ppf(p, df):
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- OLS
def ols(x, y, alpha=0.05, names=("intercepto", "pendiente")):
    """Regresión simple y = b0 + b1·x con errores estándar, IC y p-valores."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    resid = y - yhat
    df = n - 2
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    out = {"n": n, "gl": df, "r2": r2, "coeficientes": {}}
    if df > 0:
        sigma2 = ss_res / df
        cov = sigma2 * np.linalg.inv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        tcrit = t_ppf(1 - alpha / 2, df)
        out["sigma_resid"] = math.sqrt(sigma2)
        out["r2_ajustado"] = 1 - (1 - r2) * (n - 1) / df if df > 0 else float("nan")
    else:
        se = np.full(2, float("nan"))
        tcrit = float("nan")
        out["sigma_resid"] = float("nan")
    for i, name in enumerate(names):
        b, s = float(beta[i]), float(se[i])
        coef = {"valor": b, "error_std": s}
        if df > 0 and s > 0:
            t = b / s
            coef.update({
                "t": t,
                "p_valor": 2 * (1 - t_cdf(abs(t), df)),
                "ic_inf": b - tcrit * s,
                "ic_sup": b + tcrit * s,
            })
        out["coeficientes"][name] = coef
    out["nivel_confianza"] = 1 - alpha
    return out


def test_slope(fit, value, name="pendiente"):
    """Contraste H0: pendiente = value (p-valor bilateral)."""
    c = fit["coeficientes"][name]
    if fit["gl"] <= 0 or not c.get("error_std"):
        return float("nan")
    t = (c["valor"] - value) / c["error_std"]
    return 2 * (1 - t_cdf(abs(t), fit["gl"]))


def bootstrap_slope(x, y, n_boot=4000, seed=0, alpha=0.05):
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    slopes = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if np.ptp(x[idx]) == 0:
            continue
        slopes.append(np.polyfit(x[idx], y[idx], 1)[0])
    slopes = np.asarray(slopes)
    return {
        "n_remuestreos": int(len(slopes)),
        "ic_inf": float(np.quantile(slopes, alpha / 2)),
        "ic_sup": float(np.quantile(slopes, 1 - alpha / 2)),
        "mediana": float(np.median(slopes)),
    }


def loo_rmse(x, y):
    """Error cuadrático medio de validación cruzada dejando-uno-fuera."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    errs = []
    for i in range(len(x)):
        mask = np.arange(len(x)) != i
        if np.ptp(x[mask]) == 0:
            continue
        b1, b0 = np.polyfit(x[mask], y[mask], 1)
        errs.append(y[i] - (b0 + b1 * x[i]))
    return float(np.sqrt(np.mean(np.square(errs)))) if errs else float("nan")


# ---------------------------------------------------------------- leyes de escala
def fit_power_law(x, y, **kw):
    """y = a · x^b  ->  log10 y = log10 a + b log10 x."""
    lx, ly = np.log10(x), np.log10(y)
    fit = ols(lx, ly, names=("log10_a", "b"), **kw)
    fit["a"] = 10 ** fit["coeficientes"]["log10_a"]["valor"]
    fit["b"] = fit["coeficientes"]["b"]["valor"]
    fit["loo_rmse_log10"] = loo_rmse(lx, ly)
    return fit


def fit_exponential(k, y, **kw):
    """y = y0 · r^k  ->  ln y = ln y0 + k ln r."""
    ly = np.log(y)
    fit = ols(k, ly, names=("ln_y0", "ln_r"), **kw)
    c = fit["coeficientes"]["ln_r"]
    fit["y0"] = math.exp(fit["coeficientes"]["ln_y0"]["valor"])
    fit["r"] = math.exp(c["valor"])
    if "ic_inf" in c:
        fit["r_ic"] = [math.exp(c["ic_inf"]), math.exp(c["ic_sup"])]
    return fit
