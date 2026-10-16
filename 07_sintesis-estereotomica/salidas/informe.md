# Resultados ESTM (generado automáticamente)

> Generado por `pipeline.py`. No editar a mano.

## 1. Obras del catálogo

| Obra | Piezas | Juntas | Masa (t) | Equilibrio (mejor método) | GSF | Métodos | CNC ok | 3DCP ok | Fabricable |
|---|---|---|---|---|---|---|---|---|---|
| AR-MP Arco de medio punto de dovelas | 29 | 30 | 18.2 | admisible (arco) | 1.31 | arco: sí (1.31) | 100% | 100% | 100% |
| AR-AP Arco apuntado equilátero de dovelas | 29 | 30 | 15.7 | admisible (arco) | 1.23 | arco: sí (1.23) | 100% | 100% | 100% |
| GO-CR4 Bóveda de crucería cuatripartita | 438 | 1202 | 199.2 | admisible (cortes) | 1.09 | tna: no (0.27), cortes: sí (1.09) | 51% | 45% | 68% |
| GO-EST Bóveda estrellada de terceletes y ligaduras | 642 | 1894 | 235.5 | no encontrado (ninguno) | 0.00 | tna: no (0.36), cortes: no (0.98) | 64% | 54% | 81% |
| CA-NER Cúpula nervada califal de nervios cruzados | 361 | 1072 | 108.6 | admisible (rebanada) | 1.66 | tna: no (0.46), tna_anillos: no (0.59), rebanada: sí (1.66) | 69% | 62% | 69% |
| NA-MOC Cúpula de mocárabes sobre planta octogonal (versión en fábrica) | 569 | 1632 | 147.8 | no encontrado (ninguno) | 0.00 | tna: no (0.49), tna_anillos: no (0.71), rebanada: no (0.94) | 85% | 31% | 85% |

## 2. Síntesis cruzada (slerp)

| Híbrido | t | n | β | j | mocárabe | Piezas | Admisible | GSF | Métodos | Reparación | Fabricable |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HX-GO-CR4-NA-MOC-025 | 0.25 | 4 | 0.23 | 0.77 | 0.13 | 510 | sí | 1.30 | tna: no (0.49), cortes: sí (1.30) | 5 pasos | 30% |
| HX-GO-CR4-NA-MOC-050 | 0.50 | 4 | 0.52 | 0.48 | 0.33 | 393 | sí | 1.77 | tna: no (0.32), tna_anillos: no (0.27), rebanada: sí (1.77) | 3 pasos | 25% |
| HX-GO-CR4-NA-MOC-075 | 0.75 | 6 | 0.80 | 0.20 | 0.55 | 421 | sí | 1.57 | tna: no (0.45), tna_anillos: no (0.65), rebanada: sí (1.57) | 3 pasos | 26% |
| HX-CA-NER-GO-EST-025 | 0.25 | 6 | 0.79 | 1.00 | 0.00 | 272 | sí | 1.50 | tna: no (0.39), tna_anillos: no (0.59), rebanada: sí (1.50) | 0 pasos | 45% |
| HX-CA-NER-GO-EST-050 | 0.50 | 6 | 0.53 | 1.00 | 0.00 | 338 | sí | 1.86 | tna: no (0.36), tna_anillos: no (0.53), rebanada: sí (1.86) | 1 pasos | 49% |
| HX-CA-NER-GO-EST-075 | 0.75 | 4 | 0.26 | 1.00 | 0.00 | 542 | sí | 1.64 | tna: no (0.58), cortes: sí (1.64) | 4 pasos | 61% |

## 3. Memoria episódica

- Prototipos: 125 · piezas ingeridas: 4544
- Retención de la memoria (ejemplares que siguen en su prototipo): 1.000
- Estado reproducible desde el registro de eventos: True
- Patrones transversales (compartidos por ≥ 2 tradiciones): 48

| Prototipo | Tipo de pieza | n | Tradiciones |
|---|---|---|---|
| P0021 | plemento | 236 | gotica (64), gotica_tardia_hispana (160), hibrido:califal+gotica_tardia_hispana (12) |
| P0059 | celda_mocarabe | 188 | nazari (152), hibrido:gotica+nazari (36) |
| P0022 | plemento | 180 | gotica (124), gotica_tardia_hispana (56) |
| P0016 | dovela_nervio | 150 | gotica (32), gotica_tardia_hispana (56), hibrido:califal+gotica_tardia_hispana (62) |
| P0024 | plemento | 140 | gotica (64), gotica_tardia_hispana (40), hibrido:gotica+nazari (20), hibrido:califal+gotica_tardia_hispana (16) |
| P0054 | celda_mocarabe | 140 | nazari (80), hibrido:gotica+nazari (60) |
| P0084 | plemento | 100 | hibrido:gotica+nazari (56), hibrido:califal+gotica_tardia_hispana (44) |
| P0086 | plemento | 100 | hibrido:gotica+nazari (36), hibrido:califal+gotica_tardia_hispana (64) |
| P0014 | dovela_nervio | 96 | gotica (20), gotica_tardia_hispana (32), hibrido:califal+gotica_tardia_hispana (44) |
| P0047 | plemento | 96 | califal (24), hibrido:califal+gotica_tardia_hispana (72) |
| P0050 | plemento | 84 | califal (48), hibrido:califal+gotica_tardia_hispana (36) |
| P0051 | plemento | 78 | califal (24), hibrido:califal+gotica_tardia_hispana (54) |

## 4. Entregables OpenBIM

| Lote | Piezas | Juntas (IfcRelConnectsElements) | Psets | IDS |
|---|---|---|---|---|
| catalogo_historico | 2068 | 5860 | 10346 | cumple (2068/2068, 2068/2068, 6/6) |
| sintesis_hibridos | 2476 | 7532 | 12386 | cumple (2476/2476, 2476/2476, 6/6) |
