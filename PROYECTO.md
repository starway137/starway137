# ArchiMorph-5 — arqueología computacional para diseño generativo

Análisis morfométrico, paramétrico y contextual de cinco obras arquitectónicas
antiguas, transformadas en datos estructurados (CSV/JSON) para condicionar y
restringir modelos de diseño generativo contemporáneo.

> El `README.md` de la raíz es el README de perfil de GitHub y se mantiene
> intacto; este archivo es el índice del proyecto.

## 1. Estructura

```
.
├── 01_angkor-wat/                          Templo Angkor Wat (Camboya)
├── 02_templo-kailasa/                      Templo de Kailasa, Ellora (Maharashtra, India)
├── 03_ciudad-antigua-sukhothai-ayutthaya/  Ayutthaya (Wat Chaiwatthanaram) + Sukhothai (Tailandia)
├── 04_mohenjo-daro/                        Mohenjo-daro, Valle del Indo (Pakistán)
├── 05_estupa-sanchi/                       Gran Estupa de Sanchi (Madhya Pradesh, India)
│   ├── docs/            contexto_hipotesis.md · fuentes.md
│   ├── analysis/        patrones_proporciones.md
│   ├── cad_parametric/  parametros.json · modelo_parametrico.py · ingenieria_inversa.md · salida/{svg,obj,json}
│   └── data/            elementos.csv · descriptores.json · features.json (generado)
├── 06_global-data-vault/                   Consolidación, modelos, prior generativo, co-diseño
├── 07_sintesis-estereotomica/              Grafos de piezas, Heyman/TNA, DfAM, memoria episódica,
│                                           slerp entre tradiciones, IFC 4.3 + IDS, Speckle, Grasshopper
├── Makefile · requirements.txt · .github/workflows/pipeline.yml
```

Cada caso de estudio es autónomo (sus datos, su modelo, sus hipótesis) y
comparte un mismo esquema; el vault solo lee de ellos.

## 2. Metodología por obra (carpetas 01–05)

1. **Contexto e hipótesis** (`docs/`): cronología, función, materiales;
   cuatro hipótesis por obra con enunciado, predicción falsable, test en el
   repositorio y criterio de falsación.
2. **Composición y proporción** (`analysis/`): cadena de inclusión y razón de
   anidamiento, simetría (grupo en planta), cánones **con probabilidad de
   coincidencia por azar**, modulación en la unidad métrica local, masa/vacío.
3. **Ingeniería inversa** (`cad_parametric/`): la regla generativa
   reconstruida como código; produce planta SVG, volumetría OBJ y un JSON con
   volúmenes y contrastes de hipótesis (p. ej. balance sustractivo de Kailasa).
4. **Datos** (`data/`): cada medida con calidad (A/B/C), incertidumbre y fuente.

## 3. Consolidación (06)

- **Síntesis cruzada** de patrones comunes y divergencias.
- **Modelos estadísticos M1–M6**: alometría altura-base, tensión de peso
  propio, anidamiento exponencial, volumen-huella, curva de crecimiento
  cronológico y densidad-escala, con IC, bootstrap y LOO.
- **Dataset ML** normalizado, con metadatos, etiquetas multietiqueta,
  aumentación por propagación de incertidumbre y *dataset card*.
- **Prior generativo + restricciones** y CLI de co-diseño (`generar` / `evaluar`).

## 4. Resultados principales

| Hallazgo | Evidencia |
|---|---|
| Los cinco casos son cadenas de inclusión geométricas (R² ≥ 0.92); en los cuatro con centro sagrado, cada recinto mide 0.35–0.44 veces el que lo contiene | M3 |
| Ninguna masa trabaja por encima de 0.43 MPa de tensión media (FS 6–544): la forma no la limita la resistencia sino la estabilidad, el proceso y el terreno | M2 |
| Las masas centrales verticales muestran alometría negativa (H ∝ B^0.37; isometría rechazada, p = 0.017) | M1 |
| El balance sustractivo de Kailasa da ~215 000 t extraídas (+8 % sobre la cifra citada) | KL-H1 |
| Wat Chaiwatthanaram transfiere la regla jemer verticalizándola (escala de altura 0.54 frente a escala lineal 0.35 respecto de Angkor) | AY-H1 |
| No hay evidencia de proporción áurea: con 11 cánones y ±2 %, el azar acierta el 35 % de las veces | `canons.py` |

## 5. Módulo 07 · Síntesis estereotómica

Pipeline independiente para obras de alta complejidad estructural:
arcos de dovelas, crucería gótica y estrellada, nervadas califales y
mocárabes. Las obras se representan como grafos atribuidos relacionales de
piezas y juntas y se verifican por el límite inferior de Heyman (líneas de
empujes, método de los cortes, rebanadas y Thrust Network Analysis). Cada
pieza se evalúa para piedra CNC e impresión 3D de hormigón. Los patrones se
aprenden de forma continua con memoria episódica, sin olvido, y las
tradiciones se cruzan por interpolación esférica. Los entregables son IFC 4.3
con Psets `ESTM_*`, validados con IDS a nivel LOD 400. Detalle en
[`07_sintesis-estereotomica/README.md`](07_sintesis-estereotomica/README.md).

```bash
make estm-test    # 23 pruebas (incluye el benchmark de Heyman t/R = 0.1075)
make estm         # pipeline completo (~7 min)
```

## 6. Reproducir

```bash
pip install -r requirements.txt   # solo numpy
make all                          # validación → CAD → features → modelos → prior → informe → co-diseño
make test                         # 16 pruebas unitarias y de integración
make codiseno AREA=15000 MEZCLA="KL=0.5,SN=0.5" NOMBRE=mi_propuesta
```

El pipeline es determinista (semillas fijas); la CI comprueba que los
artefactos versionados coinciden con los regenerados.

## 7. Calidad de los datos — leer antes de usar

Una parte sustancial de las medidas es de **calidad C** (estimaciones del
proyecto sobre plantas y fotografías publicadas), señalada fila a fila. Los
resultados que dependen de ellas son hipótesis con protocolo de verificación
(LiDAR, fotogrametría, ortofoto), no hallazgos. Las referencias de
`docs/fuentes.md` deben verificarse (edición y página) antes de publicar.
