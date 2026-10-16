# Ciudad Antigua (Ayutthaya / Sukhothai) — contexto e hipótesis

## 1. Contexto

| Campo | Valor |
|---|---|
| Ubicación | Ayutthaya, Tailandia; Wat Chaiwatthanaram (14.343 N, 100.5418 E) en la orilla oeste del Chao Phraya, fuera de la isla |
| Cronología | Ciudad: 1351–1767. Wat Chaiwatthanaram: fundado en 1630 por el rey Prasat Thong |
| Función | Monasterio real; conmemoración dinástica y reinterpretación del modelo jemer |
| Materiales | Ladrillo cocido revestido de estuco de cal; laterita puntual |
| Tipología | Wat real en quincunce: prang central + cuatro prangs de esquina sobre plataforma, galería con ocho meru thit, ubosot frente al río |

Ayutthaya ocupa una isla formada por la confluencia del Chao Phraya, el Pa
Sak y el Lopburi, con canales que la convierten en una ciudad-foso. Su
predecesora, Sukhothai, era una ciudad rectangular de triple muralla de
tierra. Wat Chaiwatthanaram se construyó tras campañas en Camboya y adopta la
lógica del templo-montaña jemer (quincunce, galería, eje) con materiales y
proporciones propios.

## 2. Preguntas de investigación

1. ¿Se transfiere la regla compositiva jemer por homotecia o con una deformación sistemática?
2. ¿Cómo cambia el límite urbano de una frontera construida (Sukhothai) a una topográfica (Ayutthaya)?
3. ¿Qué límite impone la fábrica de ladrillo a la altura de los prangs?

## 3. Hipótesis

### AY-H1 — Transferencia de la regla jemer con verticalización
- **Enunciado:** Wat Chaiwatthanaram reproduce la topología de Angkor Wat (quincunce en recinto rectangular, eje dirigido) pero no su métrica: la escala en altura es mayor que la escala en planta.
- **Predicción:** factor de escala de altura respecto de Angkor > factor de escala lineal.
- **Test:** `cad_parametric/modelo_parametrico.py` → `computos.test_AY_H1`.
- **Falsación:** factores iguales (homotecia) con medidas de calidad A.

### AY-H2 — La red fluvial como foso cosmológico y defensivo
- **Enunciado:** la isla de Ayutthaya ejerce a escala urbana la función que el foso ejerce en Angkor (límite, defensa, regulación hídrica).
- **Predicción:** el perímetro urbano coincide con cauces naturales y canales excavados en una proporción mayoritaria.
- **Test:** pendiente: digitalización SIG del perímetro (elemento `AY-C01`, calidad C).

### AY-H3 — Altura limitada por la fábrica de ladrillo y el estuco
- **Enunciado:** los prangs de ladrillo trabajan con márgenes estáticos menores que la piedra jemer y su esbeltez se acota por la estabilidad del revestimiento.
- **Predicción:** FS del prang central entre 5 y 50 (fábrica de ladrillo, f_c 5–20 MPa).
- **Test:** `M2_tension_peso_propio`.

### AY-H4 — De la muralla al río
- **Enunciado:** el paso de Sukhothai a Ayutthaya sustituye un límite construido rectangular por un límite topográfico irregular, con mayor superficie urbana.
- **Predicción:** área de Ayutthaya (isla) > área de Sukhothai (recinto amurallado).
- **Test:** comparación de `AY-C01` y `AY-C02` en `data/elementos.csv` (ambos C).

## 4. Restricciones de época deducidas

| Tipo | Restricción | Consecuencia formal |
|---|---|---|
| Material | Ladrillo + estuco, sin piedra de cantería | Prangs más esbeltos pero con revestimiento vulnerable; plataformas macizas |
| Hidrología | Inundación anual del Chao Phraya | Plataformas elevadas; frente fluvial como acceso principal (azimut 90°) |
| Política | Programa de prestigio tras campañas en Camboya | Cita explícita del modelo jemer |
| Rito | Theravada: ubosot, galería de budas, circunvalación | El ubosot se sitúa sobre el eje y rompe la simetría D2/D4 |
