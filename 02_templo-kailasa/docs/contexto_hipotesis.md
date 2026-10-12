# Templo de Kailasa — contexto e hipótesis

## 1. Contexto

| Campo | Valor |
|---|---|
| Ubicación | Ellora, Maharashtra, India (20.0237 N, 75.179 E), escarpe basáltico orientado a poniente |
| Cronología | c. 756–773, dinastía Rashtrakuta (atribuido a Krishna I); trabajos de detalle posteriores |
| Función | Templo shivaíta que materializa el monte Kailasa, morada de Shiva |
| Material | Basalto de los Traps del Decán, sin juntas ni mortero |
| Tipología | Templo monolítico excavado ("arquitectura en negativo") de tipo dravida |

Kailasa no se construyó: se excavó. Se abrieron dos zanjas paralelas y una
transversal en la ladera hasta aislar un bloque de roca, que se talló de
arriba abajo con plinto, mandapas, vimana, puentes, pilares-estandarte y
elefantes exentos. El patio resultante mide ~82 × 46 m y su pared posterior
alcanza ~33 m.

## 2. Preguntas de investigación

1. ¿Puede formalizarse el proyecto como un balance sustractivo (volumen retenido / extraído)?
2. ¿Qué reglas de proyecto impone un proceso irreversible, sin posibilidad de añadir material?
3. ¿Se rigen las proporciones por un canon de tratado (Vastu) o por la geometría del escarpe?

## 3. Hipótesis

### KL-H1 — Balance sustractivo consistente con ~200 000 t
- **Enunciado:** el volumen de roca extraído se deduce de la envolvente del patio (terreno en pendiente) menos el volumen retenido del templo.
- **Predicción:** masa extraída dentro de ±25 % de 200 000 t.
- **Test:** `cad_parametric/modelo_parametrico.py` → `computos.test_KL_H1`.
- **Falsación:** desviación > 25 % con medidas fotogramétricas de calidad A.

### KL-H2 — Composición axial bilateral sin canon proporcional fuerte
- **Enunciado:** la planta es una secuencia lineal (gopura → Nandi mandapa → mandapa → vimana) con simetría bilateral; sus razones de planta no prueban por sí solas un canon.
- **Predicción:** la razón del patio (82/46) y del templo (50/33) caen cerca de algún canon, pero con probabilidad de azar alta (≥ 0.3 con tolerancia ±2 %).
- **Test:** `diagnosticos.canon_recinto_principal` en `data/features.json`.

### KL-H3 — Viabilidad del ritmo de extracción
- **Enunciado:** la duración atribuida (~18 años, un reinado) implica un ritmo de extracción alcanzable con una cuadrilla de tamaño moderado.
- **Predicción:** ritmo del orden de 10 m³/día; con una productividad supuesta de 0.05–0.1 m³/operario·día en basalto con herramientas de hierro, requeriría del orden de 100–200 canteros simultáneos (supuesto C, a contrastar con arqueología experimental).
- **Test:** `computos.test_KL_H3`.

### KL-H4 — La irreversibilidad, no la resistencia, gobierna la forma
- **Enunciado:** las tensiones de peso propio son despreciables frente a la resistencia del basalto; la restricción de proyecto es la imposibilidad de corregir errores (talla de arriba abajo y de fuera adentro).
- **Predicción:** FS > 100 en vimana y plinto; incluso el dhvajastambha, el elemento más esbelto, queda lejos del aplastamiento.
- **Test:** `M2_tension_peso_propio`.

## 4. Restricciones de época deducidas

| Tipo | Restricción | Consecuencia formal |
|---|---|---|
| Proceso | Sustracción irreversible | Diseño completo antes de excavar; talla descendente; márgenes de seguridad en los muros |
| Material | Basalto masivo con diaclasas | Orientación del bloque según discontinuidades; elementos exentos solo donde la roca es sana |
| Topografía | Ladera con pendiente hacia poniente | Profundidad variable (frente bajo, fondo alto); acceso desde el valle |
| Logística | Evacuación del escombro por el frente | Secuencia de excavación de fondo a frente; el frente se cierra al final con la gopura |
