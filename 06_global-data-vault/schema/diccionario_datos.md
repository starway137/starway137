# Diccionario de datos

## 1. Convenciones

- Unidades SI (m, m², m³, kg/m³, MPa). Años: enteros, negativos = a.C.
- `largo_m` = dimensión mayor en planta y `ancho_m` = menor; en `circulo` y `cuadrado`, `largo_m = ancho_m` (diámetro o lado). La orientación del lado largo se documenta en `parametros.json`.
- Ejes de los modelos paramétricos: x = Este, y = Norte, z = altura (el OBJ exporta con Y vertical).
- Identificadores: `<SITIO>-<CLASE><NN>`. Clases: `E` cadena de inclusión, `M` masa, `B` bloque/manzana, `C` ciudad/territorio, `F` fase anterior, `N` otro elemento, `U` módulo métrico.

## 2. Calidad del dato

| Nivel | Significado | Incertidumbre relativa típica |
|---|---|---|
| **A** | Medida publicada en fuente primaria o de referencia | 0.01–0.05 |
| **B** | Derivada por cálculo de medidas A (o literatura secundaria consistente) | 0.05–0.15 |
| **C** | Estimación del proyecto (lectura de plano/fotografía) o hipótesis de reconstrucción | 0.10–0.30 |

Cada fila declara su `incertidumbre_rel`; la aumentación sintética la usa para
propagar el error. Ningún resultado basado mayoritariamente en datos C debe
presentarse como hallazgo: es una hipótesis con su protocolo de verificación.

## 3. `data/elementos.csv` (uno por caso)

| Columna | Tipo | Descripción |
|---|---|---|
| `element_id` | str | Identificador único con prefijo del sitio |
| `nombre` | str | Nombre descriptivo |
| `tipo` | str | Tipo morfológico (`foso`, `recinto`, `galeria`, `torre`, `templo_montana`, `vimana`, `prang`, `chedi`, `anda`, `pilar`, `plataforma`, `plinto`, `ciudadela`, `modulo`…) |
| `nivel_jerarquico` | int / vacío | Posición k en la cadena de inclusión (0 = exterior); vacío si no pertenece |
| `es_masa_portante` | 0/1 | 1 si entra en los modelos estructurales y alométricos |
| `forma_planta` | enum | `rect`, `cuadrado`, `circulo` |
| `largo_m`, `ancho_m` | float | Dimensiones en planta (> 0) |
| `alto_m` | float / vacío | Altura (masas), altura de muro, profundidad (excavaciones) |
| `factor_volumen` | float (0, 1] | V / (A_planta · H). Prisma 1, pirámide 1/3, casquete (3a²+h²)/(6a²) |
| `material` | str | `material_id` de `schema/materiales.csv` o `na` |
| `fase` | str | Fase constructiva |
| `fecha_aprox` | int | Año aproximado |
| `calidad_dato` | A/B/C | Ver §2 |
| `incertidumbre_rel` | float (0, 1) | Desviación relativa (1σ, log-normal) |
| `fuente_id` | str | Referencia en `docs/fuentes.md` |
| `notas` | str | Método, supuestos |

## 4. `data/descriptores.json`

Metadatos y etiquetas cualitativas del caso. Claves obligatorias (validadas
por `pipelines/archimorph/validation.py`): `sitio_id`, `nombre`, `pais`,
`coordenadas`, `cronologia{inicio, fin}`, `tipologia`, `cosmograma`,
`patron_compositivo`, `proceso_constructivo`, `sistema_estructural`,
`material_principal`, `modulo_metrico{nombre, valor_m}`,
`eje_principal{azimut_frente_deg, tipo}`, `simetria{grupo, orden_rotacional,
reflexion}`, `recinto_principal_id`, `masa_principal_id`,
`estimaciones{fraccion_ocupacion, porosidad_vanos}`, `etiquetas_morfologicas`,
`hipotesis_ids`, `licencia_datos`. Esquema formal: `descriptores.schema.json`.

## 5. Features normalizadas (`data/features.json`, `datasets/features_sitios.*`)

| Feature | Unidad | Definición |
|---|---|---|
| `relacion_aspecto_recinto` | adim | max(L, A) / min(L, A) del recinto principal |
| `desviacion_canon_abs` | adim | \|r − c\| / c respecto del canon más próximo |
| `razon_anidamiento_r` | adim | exp(pendiente) de ln L_k frente a k |
| `r2_anidamiento` | adim | R² de ese ajuste |
| `niveles_jerarquicos` | conteo | Longitud de la cadena de inclusión |
| `log10_escala_sitio_m` | log10 m | Dimensión mayor del nivel 0 |
| `log10_area_sitio_m2` | log10 m² | Área del nivel 0 |
| `log10_escala_en_modulos` | log10 | Nivel 0 expresado en el módulo métrico local |
| `log10_altura_max_m` | log10 m | Masa portante más alta |
| `esbeltez_masa_principal` | adim | H / √A de la masa principal |
| `factor_volumen_masa_principal` | adim | V / (A · H) |
| `tension_base_MPa` | MPa | ρ · g · f · H |
| `log10_factor_seguridad` | log10 | log10(f_c,min / σ) |
| `fraccion_ocupacion` | adim | Huella construida / área del recinto principal (masa/vacío) |
| `porosidad_vanos` | adim | Vano / superficie de alzado |
| `orden_simetria_rotacional` | conteo | n de C_n / D_n (retícula: 2) |
| `simetria_reflexion` | 0/1 | Presencia de ejes de reflexión |
| `eje_cos_n`, `eje_sin_n` | adim | cos(nθ), sin(nθ) con θ = azimut del frente: **vector axial invariante a la simetría** (un eje no dirigido con n = 2 no distingue 0° de 180°) |
| `fecha_media` | año | Punto medio de la cronología |

Categóricas: `tipologia`, `patron_compositivo`, `proceso_constructivo`,
`sistema_estructural`, `cosmograma`, `grupo_simetria`, `canon_cercano`.
Multietiqueta: `etiquetas_morfologicas` → columnas `tag_*` en `y_etiquetas.csv`.

## 6. Materiales (`schema/materiales.csv`)

Densidad y rango de resistencia a compresión (f_c,min – f_c,max) por material.
Los valores históricos son rangos de ingeniería típicos (calidad C), no
ensayos en sitio; se usan para órdenes de magnitud.
