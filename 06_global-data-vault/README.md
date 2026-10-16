# 06 · Global Data Vault

Contenedor central de datos, consolidación, modelado y co-diseño. Lee los
datos de los cinco casos (`01_…` a `05_…`), los valida, ejecuta sus modelos
paramétricos, extrae features, ajusta los modelos de escala y construye el
prior generativo.

```
06_global-data-vault/
├── pipelines/                 Código (solo numpy + biblioteca estándar)
│   ├── archimorph/            Librería: geometría, estadística, features, prior
│   ├── validar.py             1. Esquema e integridad referencial
│   ├── construir_cad.py       2. Ejecuta <caso>/cad_parametric/modelo_parametrico.py
│   ├── extraer_features.py    3. Features por caso y dataset ML
│   ├── modelos_estadisticos.py 4. M1–M6 (regresión, leyes de escala)
│   ├── construir_prior.py     5. Prior generativo + restricciones
│   ├── informe.py             6. Informe automático y figuras
│   ├── codiseno.py            CLI de co-diseño (generar / evaluar)
│   └── run_all.py             Pipeline completo
├── schema/                    Diccionario de datos, JSON Schemas, materiales
├── datasets/                  Consolidado + ml/ (X, y, metadatos, aumentado, dataset card)
├── modelos/                   modelos_escala.json
├── priors/                    prior_generativo.json
├── reports/                   Síntesis cruzada, modelado, co-diseño, resultados (generado), figuras
├── codiseno/                  ejemplos/ (entradas) y salidas/ (propuestas generadas)
└── tests/                     Pruebas unitarias y de integración (unittest)
```

## Flujo

```
<caso>/data/elementos.csv ─┐
<caso>/data/descriptores.json ─┼─► validar ─► construir_cad ─► extraer_features ─► modelos ─► prior ─► co-diseño
<caso>/cad_parametric/ ─────┘                    │                  │               │
                                         salida/*.svg|obj|json   datasets/ml/   reports/
```

## Uso

```bash
make all          # desde la raíz del repositorio
make test
python3 pipelines/codiseno.py generar --area 12000 --mezcla "AW=0.6,SN=0.4" --nombre mi_propuesta
python3 pipelines/codiseno.py evaluar --diseno codiseno/ejemplos/proyecto_centro_cultural.json
```

## Documentos

| Documento | Contenido |
|---|---|
| [`reports/sintesis_cruzada.md`](reports/sintesis_cruzada.md) | Patrones comunes y divergencias entre los 5 casos |
| [`reports/modelado_estadistico.md`](reports/modelado_estadistico.md) | Formulación de M1–M6 e interpretación |
| [`reports/co_diseno.md`](reports/co_diseno.md) | El dataset como prior generativo y conjunto de restricciones |
| [`reports/resultados_modelos.md`](reports/resultados_modelos.md) | Cifras generadas automáticamente |
| [`schema/diccionario_datos.md`](schema/diccionario_datos.md) | Definición de columnas, features y niveles de calidad |
| [`datasets/ml/dataset_card.md`](datasets/ml/dataset_card.md) | Datasheet del dataset ML |
