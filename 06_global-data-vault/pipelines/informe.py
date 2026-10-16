"""Paso 6 — informe automático de resultados (Markdown) y gráficos SVG.

El informe se regenera en cada ejecución; los informes redactados a mano en
reports/ citan este archivo como fuente de las cifras.
"""

import math

import numpy as np

from archimorph import canons, io_utils, paths

CSS = """<style>
.viz{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--s1:#2a78d6;--s2:#eb6834;
--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--fit:#52514e}
@media (prefers-color-scheme:dark){.viz{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#34332f;
--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--fit:#c3c2b7}}
.bg{fill:var(--surface)}.t{fill:var(--ink);font:600 15px sans-serif}.l{fill:var(--ink2);font:12px sans-serif}
.a{fill:var(--ink2);font:11px sans-serif}.g{stroke:var(--grid);stroke-width:1}.ax{stroke:var(--ink2);stroke-width:1}
.fit{stroke:var(--fit);stroke-width:2;fill:none}.ref{stroke:var(--fit);stroke-width:1.5;stroke-dasharray:5 4;fill:none}
.pt{stroke:var(--surface);stroke-width:2}
</style>"""
SERIES = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)", "var(--s5)"]


class Chart:
    """Gráfico de dispersión/líneas mínimo con ejes lineales o logarítmicos."""

    def __init__(self, title, xlabel, ylabel, xr, yr, logx=False, logy=False, w=640, h=420):
        self.title, self.xlabel, self.ylabel = title, xlabel, ylabel
        self.logx, self.logy, self.w, self.h = logx, logy, w, h
        self.m = dict(l=64, r=110, t=60, b=52)
        self.xr = [self._tx(v, logx) for v in xr]
        self.yr = [self._tx(v, logy) for v in yr]
        self.body = []
        self.boxes = []
        self.legend = []

    def _label(self, x, y, text, cls="a"):
        """Coloca una etiqueta evitando solapes con las ya colocadas (búsqueda voraz)."""
        if not text:
            return
        w, h = 6.3 * len(text), 12
        for dx, dy in ((8, 4), (8, 16), (8, -8), (-8 - w, 4), (8, 28), (8, -20), (-8 - w, 16), (-8 - w, -8)):
            box = (x + dx, y + dy - h + 2, w, h)
            if all(box[0] + box[2] < b[0] or b[0] + b[2] < box[0] or box[1] + box[3] < b[1]
                   or b[1] + b[3] < box[1] for b in self.boxes):
                break
        self.boxes.append(box)
        self.body.append(f'<text class="{cls}" x="{box[0]:.1f}" y="{box[1] + h - 2:.1f}">{text}</text>')

    def add_legend(self, label, color, dashed=False):
        self.legend.append((label, color, dashed))

    @staticmethod
    def _tx(v, log):
        return math.log10(v) if log else v

    def X(self, v):
        a, b = self.xr
        return self.m["l"] + (self._tx(v, self.logx) - a) / (b - a) * (self.w - self.m["l"] - self.m["r"])

    def Y(self, v):
        a, b = self.yr
        return self.h - self.m["b"] - (self._tx(v, self.logy) - a) / (b - a) * (self.h - self.m["t"] - self.m["b"])

    def _ticks(self, rng, log):
        a, b = rng
        if log:
            return [10 ** k for k in range(math.ceil(a), math.floor(b) + 1)]
        step = 10 ** math.floor(math.log10((b - a) / 4))
        for mult in (1, 2, 5, 10):
            if (b - a) / (step * mult) <= 6:
                step *= mult
                break
        return [k * step for k in range(math.ceil(a / step), math.floor(b / step) + 1)]

    def points(self, xs, ys, labels, color=SERIES[0], tips=None):
        for i, (x, y, lab) in enumerate(zip(xs, ys, labels)):
            tip = tips[i] if tips else lab
            self.body.append(f'<circle class="pt" cx="{self.X(x):.1f}" cy="{self.Y(y):.1f}" r="5" '
                             f'fill="{color}"><title>{tip}</title></circle>')
            self.boxes.append((self.X(x) - 5, self.Y(y) - 5, 10, 10))
        for x, y, lab in zip(xs, ys, labels):
            self._label(self.X(x), self.Y(y), lab)

    def line(self, xs, ys, cls="fit", color=None, label=None):
        d = " ".join(f"{'M' if i == 0 else 'L'}{self.X(x):.1f},{self.Y(y):.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
        style = f' style="stroke:{color}"' if color else ""
        self.body.append(f'<path class="{cls}" d="{d}"{style}/>')
        if label:
            self._label(self.X(xs[-1]), self.Y(ys[-1]), label, cls="l")

    def svg(self):
        fmt = lambda v: f"{v:g}" if abs(v) < 1e4 else f"{v:.0e}"  # noqa: E731
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" class="viz" '
               f'role="img" aria-label="{self.title}">', CSS,
               f'<rect class="bg" width="{self.w}" height="{self.h}"/>',
               f'<text class="t" x="{self.m["l"]}" y="26">{self.title}</text>']
        x0, x1 = self.m["l"], self.w - self.m["r"]
        y0, y1 = self.h - self.m["b"], self.m["t"]
        for v in self._ticks(self.yr, self.logy):
            yy = self.Y(v)
            out.append(f'<line class="g" x1="{x0}" x2="{x1}" y1="{yy:.1f}" y2="{yy:.1f}"/>')
            out.append(f'<text class="a" x="{x0 - 8}" y="{yy + 4:.1f}" text-anchor="end">{fmt(v)}</text>')
        for v in self._ticks(self.xr, self.logx):
            xx = self.X(v)
            out.append(f'<text class="a" x="{xx:.1f}" y="{y0 + 18}" text-anchor="middle">{fmt(v)}</text>')
        out.append(f'<line class="ax" x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}"/>')
        out.append(f'<text class="l" x="{(x0 + x1) / 2:.0f}" y="{self.h - 12}" text-anchor="middle">{self.xlabel}</text>')
        out.append(f'<text class="l" transform="translate(16 {(y0 + y1) / 2:.0f}) rotate(-90)" '
                   f'text-anchor="middle">{self.ylabel}</text>')
        out.extend(self.body)
        lx = self.m["l"]
        for label, color, dashed in self.legend:
            if dashed:
                out.append(f'<line class="ref" x1="{lx}" x2="{lx + 18}" y1="38" y2="38"/>')
            else:
                out.append(f'<circle cx="{lx + 6}" cy="38" r="5" fill="{color}"/>')
            out.append(f'<text class="l" x="{lx + 24}" y="42">{label}</text>')
            lx += 34 + 6.8 * len(label)
        out.append("</svg>")
        return "\n".join(out) + "\n"


def chart_alometria(mod, rows):
    m1 = mod["M1_alometria_altura_base"]
    fit = m1["ajuste"]
    vert = set(m1["elementos"])
    c = Chart(f"M1 · Alometría altura-base, masas centrales verticales (b = {fit['b']:.2f}, R² = {fit['r2']:.2f})",
              "Base equivalente B (m, log)", "Altura H (m, log)", (0.5, 400), (1, 200), True, True)
    gx = [0.5, 400]
    c.line(gx, [fit["a"] * x ** fit["b"] for x in gx], label="ajuste")
    # referencia isométrica que pasa por el ajuste en la media geométrica de B
    bm = 10 ** np.mean([math.log10(r["base_equivalente_m"]) for r in rows if r["element_id"] in vert])
    hm = fit["a"] * bm ** fit["b"]
    lo = 0.5
    c.line([lo, 200 * bm / hm], [hm / bm * lo, 200], cls="ref")
    for group, color in ((True, SERIES[0]), (False, SERIES[1])):
        sel = [r for r in rows if (r["element_id"] in vert) == group]
        c.points([r["base_equivalente_m"] for r in sel], [r["alto_m"] for r in sel],
                 [r["element_id"] for r in sel], color=color,
                 tips=[f"{r['element_id']} {r['nombre']}: B={r['base_equivalente_m']:.1f} m, H={r['alto_m']:.1f} m"
                       for r in sel])
    c.add_legend("vertical (ajustada)", SERIES[0])
    c.add_legend("plataforma o pilar (excluida)", SERIES[1])
    c.add_legend("isometría b = 1", None, dashed=True)
    return c.svg()


def chart_anidamiento(site_feats):
    c = Chart("M3 · Anidamiento de recintos: ln(L_k / L_0) por nivel", "Nivel jerárquico k",
              "ln(L_k / L_0)", (0, 5.5), (-11, 0.5))
    for i, sf in enumerate(site_feats):
        n = sf["diagnosticos"]["anidamiento"]
        L0 = n["dimension_mayor_m"][0]
        ys = [math.log(L / L0) for L in n["dimension_mayor_m"]]
        c.line(n["niveles"], ys, cls="fit", color=SERIES[i], label=f"{sf['sitio_id']} r={n['r']:.2f}")
        c.add_legend(sf["sitio_id"], SERIES[i])
        c.points(n["niveles"], ys, [""] * len(ys), color=SERIES[i],
                 tips=[f"{sf['sitio_id']} {e}: L={L:g} m" for e, L in zip(n["elementos"], n["dimension_mayor_m"])])
    return c.svg()


def chart_cronologia(mod):
    m5 = mod["M5_crecimiento_cronologico"]
    fit = m5["ajuste_todos"]
    d = m5["datos"]
    c = Chart("M5 · Altura máxima frente a fecha (curva descriptiva, n = 5)", "Año (negativo = a.C.)",
              "Altura máxima (m, log)", (-2700, 1800), (5, 100), False, True)
    ts = list(range(-2700, 1801, 100))
    c.line(ts, [fit["y0"] * fit["r"] ** t for t in ts], label="exp. ajustada")
    c.points([p["fecha"] for p in d], [p["altura_max_m"] for p in d], [p["sitio_id"] for p in d],
             tips=[f"{p['sitio_id']}: {p['altura_max_m']:.1f} m, año {p['fecha']:.0f}" for p in d])
    return c.svg()


def _f(v, nd=3):
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", " ")
    return f"{v:.{nd}g}"


def _coef(fit, name):
    c = fit["coeficientes"][name]
    ic = f"[{_f(c.get('ic_inf'))}, {_f(c.get('ic_sup'))}]" if "ic_inf" in c else "—"
    return f"{_f(c['valor'])} (IC95 {ic}, p = {_f(c.get('p_valor'))})"


def markdown(mod, site_feats, cad, rows):
    L = ["# Resultados de los modelos (generado automáticamente)", "",
         "> Archivo generado por `pipelines/informe.py`. No editar a mano: ejecutar `make all`.", "",
         "## 1. Features por caso de estudio", "",
         "| Caso | Aspecto recinto | Canon cercano (desv.) | r anidamiento (R²) | Esbeltez masa | σ base (MPa) | log10 FS | Ocupación | Simetría |",
         "|---|---|---|---|---|---|---|---|---|"]
    for sf in site_feats:
        f, d = sf["features"], sf["diagnosticos"]
        cr = d["canon_recinto_principal"]
        L.append(f"| {sf['sitio_id']} | {f['relacion_aspecto_recinto']:.3f} | {cr['canon_cercano']} "
                 f"({100 * cr['desviacion_rel']:+.1f} %) | {f['razon_anidamiento_r']:.3f} ({f['r2_anidamiento']:.2f}) | "
                 f"{f['esbeltez_masa_principal']:.2f} | {f['tension_base_MPa']:.3f} | {f['log10_factor_seguridad']:.2f} | "
                 f"{f['fraccion_ocupacion']:.2f} | {sf['categoricas']['grupo_simetria']} |")
    p = site_feats[0]["diagnosticos"]["canon_recinto_principal"]
    L += ["", f"**Control de azar en cánones:** con {len(canons.CANONES)} cánones "
          f"y tolerancia ±{100 * p['tolerancia']:.0f} %, una razón aleatoria en [1, 3] cae cerca de algún canon con "
          f"probabilidad {p['prob_coincidencia_azar']:.2f}. Ninguna coincidencia individual es evidencia de intención.", ""]

    m1 = mod["M1_alometria_altura_base"]
    L += ["## 2. M1 — Alometría altura-base", "",
          f"H = {m1['ajuste']['a']:.3f} · B^b, n = {m1['ajuste']['n']}, R² = {m1['ajuste']['r2']:.3f}, "
          f"LOO-RMSE(log10) = {m1['ajuste']['loo_rmse_log10']:.3f}", "",
          f"- b = {_coef(m1['ajuste'], 'b')}",
          f"- Bootstrap b: [{m1['bootstrap_b']['ic_inf']:.3f}, {m1['bootstrap_b']['ic_sup']:.3f}]",
          f"- Contraste de isometría (b = 1): p = {_f(m1['p_valor_isometria_b1'])}", "",
          "![M1](../reports/figuras/m1_alometria.svg)", ""]

    m2 = mod["M2_tension_peso_propio"]
    L += ["## 3. M2 — Tensión de peso propio y factor de seguridad", "",
          f"σ = k·H + c: k = {_coef(m2['ajuste'], 'k_MPa_por_m')} MPa/m, R² = {m2['ajuste']['r2']:.3f}", "",
          "| Elemento | Altura (m) | σ base (MPa) | FS mínimo | Uso de la altura crítica |", "|---|---|---|---|---|"]
    for r in rows:
        crit = m2["altura_critica"][r["element_id"]]
        L.append(f"| {r['element_id']} | {r['alto_m']:.1f} | {r['tension_base_MPa']:.3f} | "
                 f"{r['factor_seguridad_min']:.0f} | {100 * crit['uso_de_altura_critica']:.1f} % |")
    L += ["", f"FS mediano = {m2['fs_mediana']:.0f}; mínimo = {m2['fs_minimo']:.1f} ({m2['elemento_mas_solicitado']}).", ""]

    m3 = mod["M3_anidamiento_exponencial"]
    L += ["## 4. M3 — Anidamiento exponencial L_k = L_0 · r^k", "",
          "| Caso | r | IC95 r | R² | n | Razones sucesivas |", "|---|---|---|---|---|---|"]
    for sid, v in m3["por_sitio"].items():
        ic = f"[{v['r_ic95'][0]:.3f}, {v['r_ic95'][1]:.3f}]" if v["r_ic95"] else "—"
        L.append(f"| {sid} | {v['r']:.3f} | {ic} | {v['r2']:.3f} | {v['n']} | "
                 f"{', '.join(f'{x:.2f}' for x in v['razones_sucesivas'])} |")
    a = m3["angkor_regimen_arquitectonico"]
    L += ["", f"r agrupado = {m3['agrupado']['r']:.3f}; media geométrica de r = {m3['r_media_geometrica']:.3f}; "
          f"Angkor solo régimen arquitectónico (niveles 2-5): r = {a['r']:.3f}, R² = {a['r2']:.3f}.", "",
          "![M3](../reports/figuras/m3_anidamiento.svg)", ""]

    m4 = mod["M4_volumen_huella"]
    L += ["## 5. M4 — Volumen frente a huella", "",
          f"V = {m4['ajuste']['a']:.3g} · A^b, b = {_coef(m4['ajuste'], 'b')}, R² = {m4['ajuste']['r2']:.3f}; "
          f"contraste b = 1.5: p = {_f(m4['p_valor_isometria_b1_5'])}", ""]

    m5 = mod["M5_crecimiento_cronologico"]
    fa, fp, sn = m5["ajuste_todos"], m5["ajuste_hasta_1200"], m5["sanchi_crecimiento_por_encapsulamiento"]
    L += ["## 6. M5 — Curva de crecimiento cronológico", "",
          f"- Todos los casos: ln H = ln H0 + c·t, c = {fa['tasa_anual']:.2e} /año, R² = {fa['r2']:.3f}, "
          f"tiempo de duplicación = {_f(fa['tiempo_duplicacion_anios'])} años, LOO-RMSE(ln) = {fa['loo_rmse_ln']:.3f}",
          f"- Hasta 1200 (sin Ayutthaya): R² = {fp['r2']:.3f}, duplicación = {_f(fp['tiempo_duplicacion_anios'])} años",
          f"- Sanchi (intra-sitio): diámetro ×{sn['diametro_final_m'] / sn['diametro_inicial_m']:.2f} en "
          f"{sn['intervalo_anios']:.0f} años (tasa {sn['tasa_anual_diametro']:.4f} /año); volumen ×{sn['factor_volumen']:.1f}", "",
          "![M5](../reports/figuras/m5_cronologia.svg)", ""]

    m6 = mod["M6_densidad_escala"]
    L += ["## 7. M6 — Densidad frente a escala", "",
          f"ocupación = a + b·log10(A): b = {_coef(m6['ajuste'], 'pendiente_por_decada')}, R² = {m6['ajuste']['r2']:.3f}, "
          f"LOO-RMSE = {m6['ajuste']['loo_rmse']:.3f}", ""]

    L += ["## 8. Contrastes de ingeniería inversa (cad_parametric)", "",
          f"- AW-H2: eje oeste = {cad['AW']['computos']['test_AW_H2']['distancia_en_hat']:.0f} hat "
          f"(hipótesis 1728; desv. {100 * cad['AW']['computos']['test_AW_H2']['desviacion_rel']:+.1f} %)",
          f"- AW factor de volumen del templo-montaña = {cad['AW']['computos']['factor_volumen_templo_montana']:.3f}",
          f"- KL-H1: roca extraída = {_f(cad['KL']['computos']['masa_extraida_t'])} t "
          f"(citado 200 000 t; desv. {100 * cad['KL']['computos']['test_KL_H1']['desviacion_rel']:+.1f} %)",
          f"- KL-H3: ritmo implícito = {cad['KL']['computos']['test_KL_H3']['ritmo_m3_dia']:.1f} m³/día durante "
          f"{cad['KL']['computos']['test_KL_H3']['duracion_hipotetica_anios']} años",
          f"- AY-H1: escala lineal vs Angkor = {cad['AY']['computos']['test_AY_H1']['factor_escala_lineal_vs_angkor']:.2f}; "
          f"escala de altura = {cad['AY']['computos']['test_AY_H1']['factor_escala_altura_vs_angkor']:.2f}",
          f"- MD-H3: fracción cubierta generada = {cad['MD']['computos']['fraccion_cubierta']:.2f} "
          f"(estimada {cad['MD']['computos']['test_MD_H3']['fraccion_ocupacion_estimada']:.2f})",
          f"- SN-H2: crecimiento de diámetro ×{cad['SN']['computos']['test_SN_H2']['factor_crecimiento_diametro']:.2f}, "
          f"H/D = {cad['SN']['computos']['razon_altura_diametro']:.3f}", ""]
    return "\n".join(L) + "\n"


def main():
    mod = io_utils.read_json(paths.MODELOS / "modelos_escala.json")
    site_feats = io_utils.read_json(paths.DATASETS / "features_sitios.json")
    cad = io_utils.read_json(paths.DATASETS / "computos_cad.json")
    rows = [r for r in io_utils.read_csv(paths.DATASETS / "elementos_consolidados.csv",
                                         numeric=io_utils.NUMERIC_COLUMNS | {
                                             "base_equivalente_m", "tension_base_MPa", "factor_seguridad_min"})
            if r["es_masa_portante"] == 1 and r["tension_base_MPa"] is not None]
    fig = paths.REPORTS / "figuras"
    fig.mkdir(parents=True, exist_ok=True)
    (fig / "m1_alometria.svg").write_text(chart_alometria(mod, rows), encoding="utf-8")
    (fig / "m3_anidamiento.svg").write_text(chart_anidamiento(site_feats), encoding="utf-8")
    (fig / "m5_cronologia.svg").write_text(chart_cronologia(mod), encoding="utf-8")
    (paths.REPORTS / "resultados_modelos.md").write_text(markdown(mod, site_feats, cad, rows), encoding="utf-8")
    print("  informe: reports/resultados_modelos.md + 3 figuras")


if __name__ == "__main__":
    main()
