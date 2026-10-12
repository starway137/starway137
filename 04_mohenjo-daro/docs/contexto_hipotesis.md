# Mohenjo-daro — contexto e hipótesis

## 1. Contexto

| Campo | Valor |
|---|---|
| Ubicación | Sindh, Pakistán (27.3292 N, 68.1389 E), llanura aluvial del Indo |
| Cronología | c. 2500–1900 a.C., fase harappana madura |
| Función | Ciudad planificada: ciudadela elevada (oeste) y Ciudad Baja residencial (este) |
| Materiales | Ladrillo cocido estandarizado (1:2:4), ladrillo crudo en plataformas, betún en el Gran Baño |
| Tipología | Ciudad en retícula ortogonal con drenaje urbano y pozos domésticos |

A diferencia de los otros cuatro casos, Mohenjo-daro no se organiza alrededor
de un centro sagrado: su regla es una norma repetible (ladrillo, calle,
manzana, pozo, desagüe) que produce orden urbano por agregación. Por eso es el
caso de control del dataset: un patrón reticular frente a cuatro patrones
centrales o axiales.

## 2. Preguntas de investigación

1. ¿Puede reproducirse la estructura urbana con un número pequeño de reglas?
2. ¿Se propaga la norma del ladrillo a escalas superiores (muro, lote, manzana)?
3. ¿Responde la ciudadela elevada a una restricción hidrológica?

## 3. Hipótesis

### MD-H1 — Retícula ortogonal con manzanas 3:2
- **Enunciado:** la Ciudad Baja se ordena por calles principales N-S y E-O que definen manzanas de proporción próxima a 3:2.
- **Predicción:** razón de la manzana tipo (366 / 244) dentro del ±5 % de 1.5.
- **Test:** `diagnosticos.canon_recinto_principal` en `data/features.json` (recinto principal = `MD-B01`).

### MD-H2 — Propagación del módulo del ladrillo
- **Enunciado:** las longitudes de muros y lotes son múltiplos del módulo del ladrillo (largo + junta).
- **Predicción:** los residuos de las longitudes medidas módulo 0.29 m no se distribuyen uniformemente (test de Rayleigh sobre la fase 2π·(L mod m)/m, p < 0.05).
- **Test:** pendiente de medidas de muros digitalizadas de [MD-01]/[MD-02]; el generador `cad_parametric/modelo_parametrico.py` impone la regla para explorar sus consecuencias, por lo que no puede usarse como prueba.

### MD-H3 — Densidad de la Ciudad Baja ≈ 0.6–0.7
- **Enunciado:** las reglas R1–R3 (calles, callejones, lotes con patio) bastan para reproducir la densidad observada.
- **Predicción:** fracción cubierta generada dentro del ±20 % de la estimación de 0.70.
- **Test:** `computos.test_MD_H3`.

### MD-H4 — La ciudadela como respuesta hidrológica
- **Enunciado:** la plataforma de ~12 m responde (también) a las crecidas del Indo, no solo a la jerarquía social.
- **Predicción:** cotas de la base de la plataforma por encima de los niveles de inundación reconstruidos para la fase madura; FS del relleno de adobe holgado.
- **Test:** estático en `M2_tension_peso_propio`; hidrológico pendiente de datos paleohidrológicos.

## 4. Restricciones de época deducidas

| Tipo | Restricción | Consecuencia formal |
|---|---|---|
| Material | Ladrillo estandarizado 1:2:4 | Aparejos regulares; medidas discretas de muros y vanos |
| Hidrología | Crecidas del Indo, freático alto | Plataformas elevadas, drenaje cubierto, pozos |
| Clima | Calor extremo | Casas introvertidas con patio, pocos vanos a la calle (porosidad baja) |
| Gobernanza | Norma compartida a escala regional | Repetición del módulo entre ciudades harappanas |
