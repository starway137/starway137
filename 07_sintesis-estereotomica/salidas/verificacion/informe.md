# Verificación ciega del algoritmo ESTM (generado automáticamente)

> Generado por `verificacion.py`. No editar a mano. Protocolo y lectura en `docs/protocolo_aplicabilidad.md`.

Las obras nuevas y los controles entran como **mallas de piezas sin semántica** (sin nombres, tipos ni juntas), giradas, trasladadas y con 1.5 mm de ruido gaussiano por vértice. El material y el relleno de senos son datos declarados del levantamiento; todo lo demás se deduce.

## 1. Selección: ¿comparte la obra las características del corpus?

Umbral de complejidad: **0.584** (0.8 × mínimo de las referencias). Condiciones mínimas: simetria ≥ 3, curvatura_razon ≥ 0.3, curvatura_rel ≥ 0.5, entropia_juntas ≥ 0.45, entropia_formas ≥ 0.3, piezas ≥ 60.

| Obra | Del corpus | C | Simetría | Curvatura (razón · rel.) | Entropía juntas | Entropía formas | Piezas | Resultado |
|---|---|---|---|---|---|---|---|---|
| GO-CR4 (referencia) | sí | 0.768 | 4 | 1.00 · 2.61 | 0.75 | 0.64 | 438 | calibración |
| GO-EST (referencia) | sí | 0.774 | 4 | 1.00 · 2.77 | 0.80 | 0.61 | 642 | calibración |
| CA-NER (referencia) | sí | 0.806 | 8 | 1.00 · 3.45 | 0.81 | 0.54 | 361 | calibración |
| NA-MOC (referencia) | sí | 0.731 | 8 | 1.00 · 4.07 | 0.55 | 0.55 | 569 | calibración |
| NV-OCT Bóveda gótica octogonal de ocho nervios al centro | sí | 0.679 | 8 | 1.00 · 0.97 | 0.85 | 0.59 | 402 | seleccionada ✔ |
| NV-CDT Bóveda estrellada octogonal de terceletes | sí | 0.837 | 8 | 1.00 · 2.05 | 0.89 | 0.56 | 770 | seleccionada ✔ |
| NV-TOL Cupulín nervado de dos cuadrados entrelazados {8/2} | sí | 0.791 | 8 | 1.00 · 4.23 | 0.75 | 0.55 | 249 | seleccionada ✔ |
| NV-SEL Cúpula de mocárabes de piedra (tipo selyúcida) | sí | 0.732 | 8 | 1.00 · 4.29 | 0.57 | 0.54 | 409 | seleccionada ✔ |
| NV-IRA Cúpula de mocárabes dodecagonal de ladrillo | sí | 0.719 | 12 | 1.00 · 4.35 | 0.56 | 0.51 | 625 | seleccionada ✔ |
| NV-MUD Cúpula mudéjar de nervios {8/3} con anillo de mocárabes | sí | 0.765 | 8 | 1.00 · 3.41 | 0.68 | 0.54 | 577 | seleccionada ✔ |
| NV-HEX Bóveda hexagonal de nervios cruzados {6/2} | sí | 0.798 | 6 | 1.00 · 3.42 | 0.79 | 0.62 | 313 | seleccionada ✔ |
| NC-MUR Muro de sillería a matajunta | no (control) | 0.092 | 1 | 0.54 · 0.00 | 0.16 | 0.15 | 85 | rechazada (simetria, curvatura_rel, entropia_juntas, entropia_formas) ✔ |
| NC-LOS Forjado de losas sobre vigas | no (control) | 0.326 | 4 | 0.32 · 0.34 | 0.26 | 0.61 | 21 | rechazada (curvatura_rel, entropia_juntas, piezas) ✔ |
| NC-CAN Bóveda de cañón corrido de medio punto | no (control) | 0.146 | 1 | 0.00 · 5.14 | 0.42 | 0.06 | 108 | rechazada (simetria, curvatura_razon, entropia_juntas, entropia_formas) ✔ |

## 2. Interpretación: ¿se ha extraído la información necesaria de cada obra?

Cada criterio compara lo deducido de la malla ciega con la ficha verdadera (que el algoritmo no ve).

| Criterio | Umbral | NV-OCT | NV-CDT | NV-TOL | NV-SEL | NV-IRA | NV-MUD | NV-HEX |
|---|---|---|---|---|---|---|---|---|
| grafo_precision (contactos detectados en la malla alterada que existen en la malla original) | >= 0.85 | 0.967 ✔ | 0.868 ✔ | 1.000 ✔ | 0.985 ✔ | 0.951 ✔ | 0.947 ✔ | 0.998 ✔ |
| grafo_exhaustividad (contactos de la malla original que se detectan tras la alteración) | >= 0.7 | 0.983 ✔ | 0.957 ✔ | 1.000 ✔ | 1.000 ✔ | 1.000 ✔ | 1.000 ✔ | 0.987 ✔ |
| acierto_tipos (piezas con tipo correcto tras la autocorrección (memoria previa a la obra)) | >= 0.9 | 0.983 ✔ | 0.888 ✘ | 1.000 ✔ | 0.961 ✔ | 1.000 ✔ | 0.986 ✔ | 1.000 ✔ |
| orden_radial (orden del polígono de planta) | == 1 | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ |
| salto_estrella (polígono estrellado de nervios {n/k}) | == 1 | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ |
| terceletes (presencia de terceletes y ligaduras) | == 1 | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ |
| d_apuntamiento (apuntamiento) | <= 0.15 | 0.025 ✔ | 0.000 ✔ | 0.025 ✔ | 0.000 ✔ | 0.100 ✔ | 0.150 ✔ | 0.050 ✔ |
| d_beta_superficie (arista (0) frente a cúpula (1)) | <= 0.15 | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.050 ✔ | 0.050 ✔ | 0.000 ✔ |
| d_inclinacion_junta (regla de juntas: lecho horizontal (0) o normal (1)) | <= 0.15 | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ |
| d_mocarabe_rel (extensión de la zona de mocárabes) | <= 0.1 | 0.000 ✔ | 0.000 ✔ | 0.000 ✔ | 0.158 ✘ | 0.000 ✔ | 0.001 ✔ | 0.000 ✔ |
| err_rel_espesor (espesor de la cáscara) | <= 0.15 | 0.055 ✔ | 0.025 ✔ | 0.021 ✔ | 0.060 ✔ | 0.056 ✔ | 0.070 ✔ | 0.001 ✔ |
| err_rel_canto (canto de los nervios) | <= 0.2 | 0.029 ✔ | 0.021 ✔ | 0.036 ✔ | 0.000 ✔ | 0.000 ✔ | 0.020 ✔ | 0.035 ✔ |
| d_despiece (hiladas por semiluz) | <= 2 | 1.000 ✔ | 0.000 ✔ | 0.000 ✔ | 1.000 ✔ | 0.000 ✔ | 0.000 ✔ | 1.000 ✔ |
| fidelidad_geometrica (mediana de la distancia entre piezas ciegas y reconstruidas / L) | <= 0.03 | 0.020 ✔ | 0.001 ✔ | 0.003 ✔ | 0.014 ✔ | 0.001 ✔ | 0.012 ✔ | 0.018 ✔ |
| veredicto_igual (admisible / no encontrado, igual en la obra verdadera y en la reconstruida) | == 1 | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ | 1 ✔ |
| err_rel_GSF (error relativo del factor geométrico de seguridad) | <= 0.2 | 0.003 ✔ | 0.000 ✔ | 0.071 ✔ | 0.019 ✔ | 0.000 ✔ | 0.081 ✔ | 0.031 ✔ |
| **criterios cumplidos** | | **16/16** | **15/16** | **16/16** | **15/16** | **16/16** | **16/16** | **16/16** |

Los tipos de pieza salen primero del clasificador (memoria episódica) y se autocorrigen con reglas físicas sobre la superficie ajustada: los nervios cuelgan bajo el intradós, los plementos quedan sobre él y los mocárabes forman anillos completos. Se vuelve a inferir hasta que los tipos no cambian; no se usa la verdad.

| Obra | Clasificador | Tras autocorrección (iteraciones) | Genoma inferido (n, k, terc., p, β, t/L, μ, j, K) | Piezas desconocidas | Equilibrio verdadera → reconstruida | Afín a | Genes nuevos frente al corpus |
|---|---|---|---|---|---|---|---|
| NV-OCT | 91.5% | 98.3% (2) | 8, 4, 0, 0.53, 0.00, 0.0283, 0.00, 1.00, 8 | 7 | admisible 2.46 (cortes) → admisible 2.46 (cortes) | GO-CR4 (d = 1.03) | estrella_{n/k} |
| NV-CDT | 78.6% | 88.8% (2) | 8, 3, 1, 0.40, 0.30, 0.0341, 0.00, 1.00, 10 | 86 | no encontrado 0.00 (ninguno) → no encontrado 0.00 (ninguno) | GO-EST (d = 1.33) | — |
| NV-TOL | 100.0% | 100.0% (1) | 8, 2, 0, 0.23, 1.00, 0.0587, 0.00, 1.00, 7 | 0 | admisible 1.55 (rebanada) → admisible 1.44 (rebanada) | CA-NER (d = 0.62) | estrella_{n/k}, despiece, canto_nervio_rel |
| NV-SEL | 96.1% | 96.1% (1) | 8, 0, 0, 0.30, 1.00, 0.0636, 0.76, 0.00, 6 | 0 | admisible 1.29 (rebanada) → admisible 1.32 (rebanada) | NA-MOC (d = 0.60) | espesor_rel, despiece |
| NV-IRA | 100.0% | 100.0% (1) | 12, 0, 0, 0.50, 0.95, 0.0528, 0.80, 0.00, 8 | 0 | no encontrado 0.00 (ninguno) → no encontrado 0.00 (ninguno) | NA-MOC (d = 1.06) | orden_radial, estrella_{n/k}, mocarabe_rel |
| NV-MUD | 98.6% | 98.6% (1) | 8, 3, 0, 0.40, 0.95, 0.0589, 0.35, 1.00, 8 | 1 | admisible 1.22 (rebanada) → admisible 1.12 (rebanada) | CA-NER (d = 0.93) | — |
| NV-HEX | 100.0% | 100.0% (1) | 6, 2, 0, 0.35, 0.70, 0.0501, 0.00, 1.00, 7 | 0 | admisible 1.41 (rebanada) → admisible 1.36 (rebanada) | CA-NER (d = 0.96) | orden_radial, estrella_{n/k} |

## 3. Autoaprendizaje sin olvido

- Prototipos del diccionario: 167 → 360 (las obras nuevas se ingieren con sus tipos autocorregidos, sin usar la verdad; cada obra aceptada pasa además a ser referencia del selector).
- Retención de la memoria (ejemplares que siguen en su prototipo): **1.000**.
- Segundo levantamiento (otro giro, otra traslación, otro ruido) de cada obra con la memoria ampliada:

| Obra | Clasificador antes | después | Tipos tras autocorrección antes | después | Criterios de genoma antes | después |
|---|---|---|---|---|---|---|
| NV-OCT | 91.5% | 100.0% | 98.3% | 100.0% | 10/10 | 10/10 |
| NV-CDT | 78.6% | 92.1% | 88.8% | 94.2% | 10/10 | 9/10 |
| NV-TOL | 100.0% | 100.0% | 100.0% | 100.0% | 10/10 | 10/10 |
| NV-SEL | 96.1% | 96.1% | 96.1% | 96.1% | 9/10 | 9/10 |
| NV-IRA | 100.0% | 100.0% | 100.0% | 100.0% | 10/10 | 10/10 |
| NV-MUD | 98.6% | 99.1% | 98.6% | 99.1% | 10/10 | 10/10 |
| NV-HEX | 100.0% | 100.0% | 100.0% | 100.0% | 10/10 | 10/10 |

## 4. Cruce con la referencia más afín y productos

| Obra nueva × referencia | Híbrido (t = 0.5, piedra CNC) | Admisible | GSF | Reparación | CNC ok | 3DCP ok | Productos |
|---|---|---|---|---|---|---|---|
| NV-OCT × GO-CR4 | HX-GO-CR4-NV-OCT-R-050 | sí | 1.77 (cortes) | 0 pasos | 52% | 42% | local/productos/HX-GO-CR4-NV-OCT-R-050/ (16 archivos) |
| NV-CDT × GO-EST | HX-GO-EST-NV-CDT-R-050 | sí | 1.60 (cortes) | 0 pasos | 64% | 52% | local/productos/HX-GO-EST-NV-CDT-R-050/ (16 archivos) |
| NV-TOL × CA-NER | HX-CA-NER-NV-TOL-R-050 | sí | 1.59 (rebanada) | 0 pasos | 72% | 61% | local/productos/HX-CA-NER-NV-TOL-R-050/ (16 archivos) |
| NV-SEL × NA-MOC | HX-NA-MOC-NV-SEL-R-050 | sí | 1.75 (rebanada) | 2 pasos | 84% | 42% | local/productos/HX-NA-MOC-NV-SEL-R-050/ (16 archivos) |
| NV-IRA × NA-MOC | HX-NA-MOC-NV-IRA-R-050 | sí | 1.72 (rebanada) | 3 pasos | 86% | 7% | local/productos/HX-NA-MOC-NV-IRA-R-050/ (16 archivos) |
| NV-MUD × CA-NER | HX-CA-NER-NV-MUD-R-050 | sí | 1.65 (rebanada) | 1 pasos | 80% | 33% | verificacion/productos/HX-CA-NER-NV-MUD-R-050/modelo_3d.dxf (+15) |
| NV-HEX × CA-NER | HX-CA-NER-NV-HEX-R-050 | sí | 1.84 (rebanada) | 1 pasos | 47% | 40% | local/productos/HX-CA-NER-NV-HEX-R-050/ (16 archivos) |
