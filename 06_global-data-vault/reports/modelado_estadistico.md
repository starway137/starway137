# Formulación estadística — escala, esfuerzo y densidad

> Implementación: `pipelines/modelos_estadisticos.py` (+ `archimorph/stats.py`).
> Resultados numéricos: [`resultados_modelos.md`](resultados_modelos.md) y
> `../modelos/modelos_escala.json`.

## 1. Método común

- Regresión lineal por mínimos cuadrados sobre variables transformadas
  (log-log para leyes potenciales, log-lineal para exponenciales).
- Inferencia: error estándar, IC95 con t de Student (implementada sin scipy),
  p-valor bilateral; contraste de pendientes de referencia (isometría).
- Robustez: bootstrap no paramétrico de la pendiente (4000 remuestreos) y
  error de validación cruzada dejando-uno-fuera (LOO-RMSE).
- Con n entre 5 y 14 puntos, los IC son amplios: los modelos describen el
  corpus y alimentan el prior, no establecen leyes universales.

## 2. Modelos

### M1 — Alometría altura-base (masas centrales verticales)

$$\log_{10} H = \log_{10} a + b\,\log_{10} B,\qquad B = \sqrt{A_{planta}}$$

Solo se ajusta la familia *vertical central* (torres, vimana, prangs, chedi,
anda, templo-montaña). Plataformas y pilares exentos se excluyen y se
documentan aparte: mezclar familias produce un ajuste espurio (R² = 0.04).

Resultado: **H ≈ 7.97 · B^0.37**, R² = 0.33, n = 9; isometría (b = 1) rechazada
(p = 0.017). Alometría negativa: al crecer la base, la altura crece mucho
menos que proporcionalmente; las masas grandes son relativamente más bajas.
El IC95 de b incluye 0 (p = 0.11): la evidencia de crecimiento es débil y la
dispersión residual (0.25 en log10) se traslada al prior como incertidumbre.

### M2 — Tensión de peso propio frente a altura

$$\sigma_{base} = \rho\,g\,f\,H$$

donde f = V/(A·H) es el factor de volumen. La regresión empírica σ ~ H tiene
R² bajo (0.14) porque ρ y f varían entre elementos: la altura por sí sola no
predice la solicitación; la forma (f) sí. Todas las masas trabajan a
0.08–0.43 MPa con FS entre 5.9 (ciudadela de adobe) y 544 (plinto de
basalto). La altura usada respecto de la de aplastamiento no supera el 17 %.

### M3 — Anidamiento exponencial

$$L_k = L_0\,r^k \iff \ln L_k = \ln L_0 + k\ln r$$

Ajuste por sitio y agrupado sobre ln(L_k/L_0). r por sitio: 0.13–0.44; r
agrupado 0.29. Angkor muestra dos regímenes (r = 0.42 en el arquitectónico).
Es la **curva de escala exponencial** principal del vault: describe cómo
decrece la dimensión con la profundidad jerárquica.

### M4 — Volumen frente a huella

$$\log V = \log a + b\,\log A$$

b = 0.98 (IC95 0.89–1.06), R² = 0.98; isometría (b = 1.5) rechazada
(p ≈ 10⁻⁸). El volumen macizo crece casi linealmente con la huella: las
masas monumentales crecen en planta, no en altura (consistente con M1).

### M5 — Curva de crecimiento cronológico

$$H_{max}(t) = H_0\,e^{c\,t}$$

c = 3.7·10⁻⁴ /año (duplicación ≈ 1880 años), R² = 0.71, LOO-RMSE(ln) = 0.54.
Excluyendo Ayutthaya (posterior al máximo de Angkor): R² = 0.76. Curva
descriptiva con n = 5 y tradiciones diferentes. Más informativo es el
crecimiento intra-sitio de Sanchi: ×2.03 en diámetro (0.71 %/año) y ×8.4 en
volumen en ~100 años, por encapsulamiento.

### M6 — Densidad frente a escala

$$\text{ocupación} = a + b\,\log_{10} A$$

b = −0.05 por década de área (IC95 −0.35 a 0.25), R² = 0.07: **no hay
relación** entre escala y densidad en este corpus. Resultado nulo útil: la
densidad masa/vacío es una decisión tipológica, no una consecuencia de la
escala; en el prior se trata como variable independiente.

## 3. Relación entre los modelos

```
             escala (L_0)
                 │  M3: L_k = L_0 r^k
                 ▼
     base del núcleo (B = L_n) ──M1──► altura H ──M2──► σ_base ──► FS (material)
                 │                                      ▲
                 └──M4: V ∝ A^0.98 ─────────────────────┘ (factor de volumen f)
     densidad (M6): independiente de la escala
```

Esta cadena es exactamente la que recorre el generador de co-diseño
(`archimorph/prior.py::sample_design`).

## 4. Trabajo futuro

- Sustituir datos C por medidas A (LiDAR de Angkor, fotogrametría de Kailasa, ortofoto de Ayutthaya).
- Ampliar el corpus (p. ej. Borobudur, Bagan, Pattadakal, Harappa) para estimar efectos por tradición con modelos jerárquicos.
- Propagar la incertidumbre al ajuste con regresión con errores en las variables (Deming / bayesiana) usando `incertidumbre_rel`.
