# Gran Estupa de Sanchi — patrones, simetrías y proporciones

> Cifras generadas por el pipeline (`data/features.json`,
> `cad_parametric/salida/sanchi_geometria.json`).

## 1. Patrón compositivo: radial concéntrico alrededor de un eje vertical

| Nivel k | Elemento | Diámetro / lado (m) | Razón L_k / L_(k-1) |
|---|---|---|---|
| 0 | Vedika de suelo | 44 (C) | — |
| 1 | Anda | 36.6 (A) | 0.83 |
| 2 | Harmika | 6 (C) | 0.16 |
| 3 | Chhatra (disco mayor) | 2.5 (C) | 0.42 |

Ajuste: **r = 0.35**, R² = 0.92 (el más bajo del dataset). La cadena tiene
dos regímenes: un anillo de circunvalación muy próximo a la masa (0.83) y una
caída brusca hacia el remate (0.16). La arquitectura se concentra en el
**borde** (recorrido) y en el **eje** (remate), no en recintos intermedios.

## 2. Perfil del anda (SN-H1)

| Magnitud | Valor |
|---|---|
| H / D | **0.450** (hemisferio = 0.5) |
| Factor de volumen del casquete (3a² + h²)/(6a²) | 0.635 |
| Volumen del anda | ~10 990 m³ |
| D / H | 2.224 (√5 = 2.236, −0.6 %) |

El anda es un casquete algo más bajo que un hemisferio. La coincidencia D/H ≈
√5 tiene una probabilidad de azar de 0.18 con ±1 % de tolerancia: no se usa
como argumento.

## 3. Crecimiento por encapsulamiento (SN-H2)

| Fase | Diámetro (m) | Fecha aprox. |
|---|---|---|
| Ashokana (núcleo de ladrillo) | ~18 (C) | c. 250 a.C. |
| Shunga (revestimiento de piedra) | 36.6 (A) | c. 150 a.C. |

Factor lineal ×2.03 → factor de volumen homotético ×8.4. La cáscara añadida
(~9 690 m³) es el 88 % del volumen final: el monumento visible es casi todo
ampliación. Tasa media de crecimiento del diámetro: 0.71 % anual.

## 4. Simetría (SN-H3)

- Grupo **C4**: rotación de orden 4 **sin** reflexiones. Los retornos acodados de la vedika en cada torana se desplazan en sentido horario y forman un molinete (svastika en planta).
- Es el único grupo quiral del dataset: la planta codifica un sentido de recorrido (pradakshina horaria).
- Vector axial invariante (n = 4, frente sur): cos 4θ = 1, sin 4θ = 0.

## 5. Proporciones del mandala (SN-H4)

| Razón | Valor | Canon más próximo | Desviación |
|---|---|---|---|
| Vedika / anda 44 / 36.6 | 1.202 | 5:4 | −3.8 % |
| Harmika / anda 6 / 36.6 | 0.164 | — | — |

Sin canon dentro de ±2 %, y con la vedika en calidad C: SN-H4 no concluyente.

## 6. Masa, vacío y esfuerzos

- Fracción de ocupación dentro de la vedika: 0.69 (B). Porosidad de la masa: 0.02.
- Anda (mampostería mixta): σ_base = 0.21 MPa, **FS ≈ 15**.
- Pilares de torana (esbeltez 12): FS ≈ 104 (sin contar arquitrabes).

## 7. Recorridos

Pradakshina de suelo ≈ 126 m (279 hasta hipotéticos); deambulatorio del medhi ≈ 121 m.
