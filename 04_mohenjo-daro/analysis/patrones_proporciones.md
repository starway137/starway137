# Mohenjo-daro — patrones, simetrías y proporciones

> Cifras generadas por el pipeline (`data/features.json`,
> `cad_parametric/salida/mohenjo_daro_geometria.json`).

## 1. Patrón compositivo: retícula ortogonal + jerarquía de escalas

Mohenjo-daro es el caso de control: su orden no es central sino
**traslacional**. Aun así existe una cadena de inclusión que va del territorio
al material:

| Nivel k | Elemento | Dimensión mayor (m) | Razón L_k / L_(k-1) |
|---|---|---|---|
| 0 | Área urbana | 1600 | — |
| 1 | Ciudadela | 400 | 0.25 |
| 2 | Edificio del Gran Baño | 55 | 0.14 |
| 3 | Gran Baño (estanque) | 11.88 | 0.22 |
| 4 | Ladrillo estándar | 0.28 | 0.02 |

Ajuste: **r = 0.125** (IC95 0.06–0.27), R² = 0.96. Es el gradiente más fuerte
del dataset porque la cadena llega hasta la pieza constructiva: la ciudad
abarca casi cuatro órdenes de magnitud (1600 m → 0.28 m) con una única norma.

## 2. Proporciones

| Razón | Valor | Canon más próximo | Desviación |
|---|---|---|---|
| Ladrillo grueso : ancho : largo | 1 : 2 : 4 | 2:1 por pares | 0 % (A) |
| Manzana 366 / 244 | 1.500 | 3:2 | 0 % (medida en pies redondeados, C) |
| Gran Baño 11.88 / 7.01 | 1.695 | 5:3 | +1.7 % |
| Ciudadela 400 / 200 (C) | 2.0 | 2:1 | 0 % (redondeada) |

El Gran Baño **no** es áureo: su razón (1.695) está más cerca de 5:3 que de
φ (+4.7 %). La manzana 3:2 procede de una medida redondeada (1200 × 800 pies):
la coincidencia es parcialmente circular y MD-H1 requiere digitalizar los
planos de Marshall y Mackay.

## 3. Simetría

- Grupo de traslación **p2mm** (retícula rectangular con dos familias de reflexión), sin centro.
- Eje no dirigido: la retícula se orienta aproximadamente a los puntos cardinales; vector axial con n = 2 (cos 2θ = 1, sin 2θ = 0).

## 4. Densidad (masa / vacío) — contraste MD-H3

El generador por reglas produce 1009 casas en 6 manzanas:

| Magnitud | Modelo | Estimación (C) |
|---|---|---|
| Fracción de huella de lotes | 0.86 | — |
| Fracción cubierta (lotes − patios) | **0.60** | 0.70 |
| Superficie media de lote | 458 m² | — |

Desviación −14 %, dentro del ±20 % de la predicción: MD-H3 es consistente.
La densidad cubierta de Mohenjo-daro es la más alta del dataset y su porosidad
de fachada la más baja (0.08): ciudad introvertida de casas-patio.

## 5. Esfuerzos

Ciudadela (adobe, factor 0.85): σ_base = 0.17 MPa, **FS ≈ 5.9**, el más bajo
del dataset y el único que usa el 17 % de su altura de aplastamiento. El
material más débil (ladrillo crudo) impone la plataforma ancha y baja
(esbeltez 0.04).

## 6. Modulación

- Módulo del ladrillo con junta: 0.29 m. Gran Baño ≈ 41 × 24 módulos.
- Unidad de longitud hipotética de 33.5 cm (50 divisiones de la escala de concha): el área urbana mide ~4770 unidades.
- MD-H2 (propagación del módulo) exige un test de Rayleigh sobre longitudes medidas: pendiente de datos.
