# Asistencia de co-diseño — el dataset como prior y como restricción

> Implementación: `pipelines/archimorph/prior.py` y `pipelines/codiseno.py`.
> Prior serializado: `../priors/prior_generativo.json`.

## 1. Principio

El dataset no es un catálogo de formas que copiar. Se usa de tres maneras:

| Uso | Qué aporta | Dónde |
|---|---|---|
| **Prior generativo** | Distribuciones de proporción, anidamiento, esbeltez, densidad y simetría observadas | `prior_generativo.json → continuas, categoricas, alometria` |
| **Restricciones paramétricas** | Reglas duras (estática, inclusión, tamaño mínimo) y blandas (rangos históricos) | `prior_generativo.json → restricciones` |
| **Métrica de afinidad** | Distancia estandarizada de un proyecto a cada lógica histórica | `codiseno.py evaluar` |

## 2. Prior

- Variables continuas en espacio transformado (log para razones positivas,
  logit para fracciones), con media, desviación y valor por sitio.
- **Mezcla de lógicas:** el diseñador da pesos por sitio (p. ej.
  `AW=0.6,SN=0.4`). Cada variable se interpola en el espacio transformado
  (media geométrica ponderada) y se perturba con
  `temperatura · desviación del corpus`.
  - `temperatura = 0`: interpolación determinista entre casos.
  - `temperatura = 1`: exploración con toda la dispersión observada.
- La altura del núcleo se obtiene de la alometría M1 con su residuo.
- Las categóricas (simetría, patrón, tipología) y la orientación se heredan del sitio dominante, salvo que se fije `--azimut` por el contexto del proyecto.

## 3. Restricciones

| Id | Tipo | Regla | Origen |
|---|---|---|---|
| R1 | Dura | σ_base ≤ f_c,min / FS con el **material contemporáneo** elegido | M2 |
| R2 | Blanda | Esbeltez dentro del rango histórico ±20 % | Features |
| R3 | Blanda | r de anidamiento dentro del rango histórico | M3 |
| R4 | Blanda | Fracción de ocupación dentro del rango histórico | Features |
| R5 | Dura | Inclusión estricta de la cadena de recintos | Definición |
| R6 | Dura | El núcleo no baja de un tamaño constructivo mínimo (truncamiento) | Práctica |

Cuando una muestra viola una restricción, se **proyecta** sobre el conjunto
factible (se acota el valor) y la corrección queda registrada en
`trazabilidad`: el diseñador ve qué decidió el dato y qué decidió la regla.

## 4. Flujos de trabajo

### 4.1 Diseño (generar)

```bash
cd 06_global-data-vault/pipelines
python3 codiseno.py generar --area 12000 --material hormigon_c30 \
    --mezcla "AW=0.6,SN=0.4" --temperatura 0.3 --semilla 1 --nombre ejemplo_aw_sn
```

Resultado (en `codiseno/salidas/`): parámetros JSON, planta SVG, volumetría
OBJ e informe de verificación. Ejemplo incluido:

| Ejemplo | Dominante | Niveles | r | Núcleo | FS | Trazabilidad |
|---|---|---|---|---|---|---|
| `ejemplo_aw_sn` (12 000 m², hormigón) | AW | 4 | 0.43 | Torre 9.6 m de base, H = 16.9 m | 158 | R6 trunca 5→4 niveles; orientación 270° heredada |
| `ejemplo_md_kl` (40 000 m², tierra compactada) | MD | 2 | 0.13 | Torre 35 m de base, H = 23.8 m | 9.2 | R6 trunca 5→2 niveles; azimut 180° fijado por el proyecto |

### 4.2 Rediseño (evaluar)

```bash
python3 codiseno.py evaluar --diseno ../codiseno/ejemplos/proyecto_centro_cultural.json
```

Para el centro cultural de ejemplo (claustros 140 → 80 → 40 → 18 m, torre de
48 m de hormigón):

- Afinidad morfológica: **AY 0.62**, KL 0.35, AW 0.02 → la propuesta es, en la lógica del corpus, una "verticalización tipo Ayutthaya".
- R1 cumple (FS = 48). R3 no cumple: r = 0.50 > 0.44 (máximo histórico). Sugerencia: comprimir la cadena hacia r ≤ 0.44 (referente: Ayutthaya), o asumir conscientemente un gradiente de escala más suave que cualquier caso histórico.

## 5. Integración con modelos de diseño generativo

| Modelo | Cómo usar el vault |
|---|---|
| Optimización paramétrica (Grasshopper/Galapagos, pymoo) | R1–R6 como restricciones; distancia a un sitio objetivo como función de coste |
| Modelos de difusión / VAE de plantas | `prior_generativo.json` como prior condicional; features como vector de condicionamiento; `aumentado_sintetico.csv` para regularizar |
| Modelos de grafos (GNN) | Cadena de inclusión como árbol jerárquico (nodo = recinto, arista = contención, atributo = r) |
| LLM-asistentes de proyecto | `descriptores.json` + hipótesis como contexto recuperable; las restricciones como herramientas de verificación |

## 6. Límites éticos y de método

- Los patrones extraídos de arquitectura sagrada se usan como lógica
  geométrica y constructiva, no como apropiación de su significado ritual.
- Un prior de cinco obras es estrecho: debe ampliarse antes de usarlo como
  único criterio. La temperatura y la proyección de restricciones existen para
  que el diseñador mantenga el control.
