# Dataset card — ArchiMorph-5

Datasheet según Gebru et al. (2021).

## Motivación

Conjunto morfométrico de cinco obras arquitectónicas antiguas del sur y
sudeste de Asia, estructurado como features y etiquetas para condicionar,
regularizar y restringir modelos de diseño generativo contemporáneo.

## Composición

| Archivo | Filas | Contenido |
|---|---|---|
| `X_features.csv` | 5 | 20 features continuas por obra (valores físicos) |
| `X_features_zscore.csv` | 5 | Las mismas, estandarizadas (z-score, ddof = 1) |
| `y_etiquetas.csv` | 5 | 7 etiquetas categóricas + multietiqueta `tag_*` |
| `feature_metadata.json` | — | Unidad, descripción, media, desviación, rango, normalización |
| `aumentado_sintetico.csv` | 250 | 50 variantes por obra (propagación de incertidumbre), `sintetico = 1` |
| `../elementos_consolidados.csv` | 39 | Tabla larga de elementos medidos con calidad, incertidumbre y fuente |
| `../features_sitios.json` | 5 | Features + diagnósticos (ajustes, cánones, masa principal) |

Unidad de muestra: la obra (5) o el elemento arquitectónico (39).

## Proceso de obtención

1. Medidas de literatura (calidad A), derivadas (B) o estimadas sobre planos y fotografías (C), cada una con incertidumbre relativa y fuente.
2. Reconstrucción paramétrica (`<caso>/cad_parametric/`) para derivar volúmenes, factores de forma y contrastes.
3. Extracción automática de features (`pipelines/extraer_features.py`).

## Aumentación

Cada variante sintética perturba todas las medidas con un factor log-normal
de desviación igual a su `incertidumbre_rel`, y las estimaciones (ocupación,
porosidad) según su calidad (A 2 %, B 5 %, C 15 %). Las variantes representan
**incertidumbre de medida**, no obras nuevas: no deben usarse como test de
generalización a otras tradiciones. Partición recomendada: agrupar por
`sitio_id` (validación *leave-one-site-out*).

## Usos previstos

- Vector de condicionamiento para modelos generativos de plantas/masas.
- Prior y restricciones para optimización paramétrica (`../../priors/`).
- Métrica de afinidad morfológica para rediseño (`pipelines/codiseno.py evaluar`).

## Usos no previstos

- Inferir significado ritual o datación a partir de la geometría.
- Presentar como hallazgo arqueológico cualquier resultado basado en datos C.
- Entrenar clasificadores con las 5 obras como si fueran una muestra representativa.

## Sesgos y limitaciones

- n = 5 obras, cuatro tradiciones, sin casos fuera de Asia meridional y sudoriental.
- Parte importante de las medidas es de calidad C (ver `calidad` en cada `features.json`).
- `fraccion_ocupacion` y `porosidad_vanos` son estimaciones de lectura de planta.
- Varias features son constantes o casi constantes en algún subconjunto (ver `constante` en `feature_metadata.json`).

## Licencia y mantenimiento

Datos: CC-BY-4.0 (campo `licencia_datos` de cada descriptor). Se regenera
con `make all`; cualquier corrección se hace en `<caso>/data/` y se propaga.
