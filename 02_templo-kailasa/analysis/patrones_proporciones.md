# Templo de Kailasa — patrones, simetrías y proporciones

> Cifras generadas por el pipeline (`data/features.json`,
> `cad_parametric/salida/kailasa_geometria.json`).

## 1. Patrón compositivo: secuencia axial dentro de un vacío

La planta no es concéntrica sino **lineal**: gopura (frente oeste) → Nandi
mandapa → puente → mandapa de 16 pilares → vimana, alineados sobre el eje E-O
y envueltos por el patio. Aun así existe una cadena de inclusión:

| Nivel k | Elemento | Dimensión mayor (m) | Razón L_k / L_(k-1) |
|---|---|---|---|
| 0 | Patio excavado | 82 | — |
| 1 | Templo exento (plinto) | 50 | 0.61 |
| 2 | Vimana (base) | 18 | 0.36 |
| 3 | Garbhagriha | 5 | 0.28 |

Ajuste exponencial: **r = 0.39** (IC95 0.23–0.67), R² = 0.97. Las razones
decrecen hacia el centro: el santuario se comprime más que los recintos.

## 2. Proporciones y cánones (con control de azar)

| Razón | Valor | Canon más próximo | Desviación |
|---|---|---|---|
| Patio 82 / 46 | 1.783 | √3 | +2.9 % |
| Templo 50 / 33 | 1.515 | 3:2 | +1.0 % |
| Patio / templo (largo) 82 / 50 | 1.64 | φ | +1.4 % |
| Vimana: altura / base 30 / 18 | 1.67 | 5:3 | 0.0 % |

Hay varias coincidencias "bonitas", y eso es justamente lo que se espera por
azar: con ±2 % de tolerancia, la probabilidad de caer junto a algún canon es
0.35, y aquí se han ensayado cuatro razones. La hipótesis KL-H2 (sin canon
fuerte demostrable) se mantiene. Un test serio requiere medir en hasta y
comprobar múltiplos enteros del Vastu-purusha-mandala (8 × 8 o 9 × 9 padas).

## 3. Simetría

- Grupo **D1**: un único eje de reflexión (E-O). Frente dirigido a 270°.
- Los dos dhvajastambha y los dos elefantes son pares simétricos respecto del eje.
- Vector axial invariante (n = 1): cos θ = 0, sin θ = −1.

## 4. Masa y vacío: el balance sustractivo

| Magnitud | Valor |
|---|---|
| Envolvente del patio (terreno en pendiente 15→33 m) | 90 528 m³ |
| Volumen retenido (templo y exentos) | 16 244 m³ |
| Volumen extraído | 74 284 m³ |
| Masa extraída (basalto 2.9 t/m³) | **215 423 t** (+7.7 % vs 200 000 t citadas) |
| Razón retenido / extraído | 0.22 |

Por cada m³ que queda se retiraron ~4.6 m³: el diseño es fundamentalmente un
diseño de vacíos. La fracción de ocupación del patio es 0.44 (B).

## 5. Esfuerzos

- Vimana: σ_base = 0.34 MPa, FS ≈ 293 (basalto, f_c ≥ 100 MPa).
- Dhvajastambha (esbeltez 10, el elemento más esbelto del dataset): σ = 0.43 MPa, FS ≈ 234.
- El material permite formas muy esbeltas; la limitación es de proceso (KL-H4), no de resistencia.

## 6. Modulación

Con un hasta hipotético de 0.45 m: patio 182 × 102 hasta, templo 111 × 73
hasta. Ninguno es un múltiplo limpio de 8 o 9 padas con estas medidas de
calidad A aproximada; queda pendiente de fotogrametría.
