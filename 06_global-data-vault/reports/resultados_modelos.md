# Resultados de los modelos (generado automáticamente)

> Archivo generado por `pipelines/informe.py`. No editar a mano: ejecutar `make all`.

## 1. Features por caso de estudio

| Caso | Aspecto recinto | Canon cercano (desv.) | r anidamiento (R²) | Esbeltez masa | σ base (MPa) | log10 FS | Ocupación | Simetría |
|---|---|---|---|---|---|---|---|---|
| AW | 1.277 | 5:4 (+2.1 %) | 0.399 (0.98) | 0.32 | 0.161 | 2.09 | 0.06 | D2 |
| KL | 1.783 | raiz3 (+2.9 %) | 0.390 (0.97) | 1.67 | 0.341 | 2.47 | 0.44 | D1 |
| AY | 1.118 | 1:1 (+11.8 %) | 0.444 (0.99) | 2.33 | 0.247 | 1.31 | 0.35 | D2 |
| MD | 1.500 | 3:2 (+0.0 %) | 0.125 (0.96) | 0.04 | 0.170 | 0.77 | 0.70 | p2mm_traslacional |
| SN | 1.000 | 1:1 (+0.0 %) | 0.353 (0.92) | 0.51 | 0.205 | 1.17 | 0.69 | C4 |

**Control de azar en cánones:** con 11 cánones y tolerancia ±2 %, una razón aleatoria en [1, 3] cae cerca de algún canon con probabilidad 0.35. Ninguna coincidencia individual es evidencia de intención.

## 2. M1 — Alometría altura-base

H = 7.974 · B^b, n = 9, R² = 0.327, LOO-RMSE(log10) = 0.271

- b = 0.372 (IC95 [-0.105, 0.849], p = 0.108)
- Bootstrap b: [-0.303, 0.835]
- Contraste de isometría (b = 1): p = 0.017

![M1](../reports/figuras/m1_alometria.svg)

## 3. M2 — Tensión de peso propio y factor de seguridad

σ = k·H + c: k = 0.00254 (IC95 [-0.00149, 0.00657], p = 0.195) MPa/m, R² = 0.136

| Elemento | Altura (m) | σ base (MPa) | FS mínimo | Uso de la altura crítica |
|---|---|---|---|---|
| AW-E05 | 41.5 | 0.421 | 47 | 2.1 % |
| AW-M01 | 65.0 | 0.161 | 124 | 0.8 % |
| AW-M02 | 30.0 | 0.305 | 66 | 1.5 % |
| KL-E02 | 30.0 | 0.341 | 293 | 0.3 % |
| KL-M01 | 7.6 | 0.184 | 544 | 0.2 % |
| KL-M02 | 15.0 | 0.427 | 234 | 0.4 % |
| AY-E01 | 5.0 | 0.084 | 60 | 1.7 % |
| AY-E02 | 35.0 | 0.247 | 20 | 4.9 % |
| AY-M01 | 16.0 | 0.113 | 44 | 2.3 % |
| AY-M02 | 12.0 | 0.095 | 52 | 1.9 % |
| MD-E01 | 12.0 | 0.170 | 6 | 17.0 % |
| SN-E01 | 16.5 | 0.205 | 15 | 6.8 % |
| SN-F01 | 8.1 | 0.091 | 55 | 1.8 % |
| SN-M01 | 8.5 | 0.192 | 104 | 1.0 % |

FS mediano = 57; mínimo = 5.9 (MD-E01).

## 4. M3 — Anidamiento exponencial L_k = L_0 · r^k

| Caso | r | IC95 r | R² | n | Razones sucesivas |
|---|---|---|---|---|---|
| AW | 0.399 | [0.327, 0.486] | 0.977 | 6 | 0.68, 0.21, 0.53, 0.52, 0.25 |
| KL | 0.390 | [0.227, 0.670] | 0.966 | 4 | 0.61, 0.36, 0.28 |
| AY | 0.444 | [0.128, 1.540] | 0.986 | 3 | 0.53, 0.38 |
| MD | 0.125 | [0.058, 0.270] | 0.961 | 5 | 0.25, 0.14, 0.22, 0.02 |
| SN | 0.353 | [0.142, 0.876] | 0.924 | 4 | 0.83, 0.16, 0.42 |

r agrupado = 0.294; media geométrica de r = 0.314; Angkor solo régimen arquitectónico (niveles 2-5): r = 0.422, R² = 0.956.

![M3](../reports/figuras/m3_anidamiento.svg)

## 5. M4 — Volumen frente a huella

V = 10.2 · A^b, b = 0.977 (IC95 [0.892, 1.06], p = 9.99e-12), R² = 0.981; contraste b = 1.5: p = 1.42e-08

## 6. M5 — Curva de crecimiento cronológico

- Todos los casos: ln H = ln H0 + c·t, c = 3.69e-04 /año, R² = 0.711, tiempo de duplicación = 1 877 años, LOO-RMSE(ln) = 0.539
- Hasta 1200 (sin Ayutthaya): R² = 0.757, duplicación = 1 598 años
- Sanchi (intra-sitio): diámetro ×2.03 en 100 años (tasa 0.0071 /año); volumen ×8.4

![M5](../reports/figuras/m5_cronologia.svg)

## 7. M6 — Densidad frente a escala

ocupación = a + b·log10(A): b = -0.0461 (IC95 [-0.345, 0.253], p = 0.657), R² = 0.074, LOO-RMSE = 0.437

## 8. Contrastes de ingeniería inversa (cad_parametric)

- AW-H2: eje oeste = 1722 hat (hipótesis 1728; desv. -0.3 %)
- AW factor de volumen del templo-montaña = 0.107
- KL-H1: roca extraída = 215 423 t (citado 200 000 t; desv. +7.7 %)
- KL-H3: ritmo implícito = 11.3 m³/día durante 18 años
- AY-H1: escala lineal vs Angkor = 0.35; escala de altura = 0.54
- MD-H3: fracción cubierta generada = 0.60 (estimada 0.70)
- SN-H2: crecimiento de diámetro ×2.03, H/D = 0.450

