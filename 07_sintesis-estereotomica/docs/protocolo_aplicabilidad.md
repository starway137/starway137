# Protocolo de verificación y aplicabilidad

Este documento fija **cuándo y cómo** se pueden usar los procesos del módulo
ESTM sobre obras nuevas y en productos nuevos: diseños, materiales, detalles,
propuestas arquitectónicas, replanteo y patrimonio. Los resultados numéricos
están en [`salidas/verificacion/informe.md`](../salidas/verificacion/informe.md),
que regenera `verificacion.py`.

## 1. Qué se verifica

La pregunta es si el algoritmo, entrenado con las obras de referencia, puede
**recibir una obra que no ha visto**, decidir si pertenece al corpus de alta
complejidad, **extraer la información necesaria** para reconstruirla y
verificarla, **mejorar con ella** sin olvidar lo aprendido y **cruzarla** con
las referencias para producir entregables nuevos.

La prueba es ciega: cada obra nueva o control llega como **mallas de piezas sin
semántica** (sin nombres, tipos ni juntas), barajadas, giradas y trasladadas, y
con 1.5 mm de ruido por vértice, como llegaría un levantamiento segmentado o un
modelo de otro autor. El algoritmo nunca ve la ficha verdadera; solo se usa
después, para puntuar.

```
mallas ──► grafo de contactos ──► SELECCIÓN ──► tipos de pieza ──► genoma inverso
                                    │                                   │
                              (rechazo: fuera                    regeneración con
                               del corpus)                         la gramática
                                                                        │
            productos ◄── síntesis slerp ◄── memoria + referencias ◄── Heyman (verdadera
          (DXF, DAE, IFC…)  con la referencia     ampliadas            vs reconstruida)
                            más afín              (pseudo-etiquetas)
```

## 2. Puertas de decisión

Cada puerta tiene un criterio medible. Si no se supera, el proceso se detiene
en esa puerta y el informe dice por qué; no se genera ningún producto.

| Puerta | Pregunta | Criterio (umbral) | Si falla |
|---|---|---|---|
| G0 Entrada | ¿Las mallas son piezas cerradas en metros y Z vertical? | volumen > 0 por pieza; contactos detectados ≥ 1 por pieza | Pedir segmentación por piezas o reorientar el levantamiento |
| G1 Grafo | ¿Se reconstruyen las juntas pese al giro y al ruido? | precisión ≥ 0.85, exhaustividad ≥ 0.70 frente a los contactos de la malla sin alterar (en pruebas) | Ajustar `tol` al ruido del levantamiento (`detectar_contactos`) |
| G2 Selección | ¿Comparte la obra las características del corpus? | simetría rotacional ≥ 3, doble curvatura (razón ≥ 0.3, relativa ≥ 0.5), entropía de juntas ≥ 0.45, entropía de formas ≥ 0.30, ≥ 60 piezas e índice C ≥ 0.8 × mínimo de las referencias | Obra fuera del alcance: no se procesa (muros, forjados, cañones, arcos aislados) |
| G3 Interpretación | ¿Se ha extraído la información necesaria? | tipos ≥ 90 %; n, {n/k} y terceletes exactos; Δp, Δβ, Δj ≤ 0.15; Δμ ≤ 0.10; espesor ≤ 15 %; canto ≤ 20 %; despiece ± 2; fidelidad geométrica ≤ 3 % de la luz | Revisión humana de las piezas `desconocido` y del genoma; no usar como base de diseño |
| G4 Equilibrio | ¿La interpretación conserva lo que decide la seguridad? | mismo veredicto de Heyman en la obra verdadera y en la reconstruida; GSF ± 20 % | La reconstrucción no sirve para dictamen estructural |
| G5 Aprendizaje | ¿Mejora sin olvidar? | retención de la memoria = 1.000; el segundo levantamiento se interpreta igual o mejor | Revertir el episodio (el registro de eventos es reproducible) |
| G6 Producto | ¿El producto es construible? | admisible por Heyman con GSF ≥ 1.5 tras reparación mínima; fracción fabricable declarada por pieza | El producto se marca "no apto" y no se exporta |

En las pruebas (obras generadas desde una ficha) G1, G3 y G4 se miden contra
la verdad. En un caso real **no hay verdad**: se aplican los criterios
internos (fidelidad geométrica G3, piezas `desconocido`, novedad latente,
comprobación estructural G4 sobre la reconstrucción) y la revisión experta.

## 3. Aplicabilidad por tipo de producto

### 3.1 Diseños nuevos (síntesis entre tradiciones)

- **Entrada**: dos genomas (dos referencias, o una referencia y una obra
  nueva ya interpretada), un parámetro t ∈ [0, 1], una luz y un material.
- **Proceso**: `slerp` en el espacio latente normalizado → gramática →
  Heyman (arco, TNA, cortes, rebanada) → reparación mínima de espesor
  (×1.25, ≤ 5 pasos) hasta GSF ≥ 1.5 → DfAM.
- **Salida**: carpeta de productos completa (sección 4).
- **Condición**: solo se entrega un híbrido **admisible**. Que un método no
  encuentre una solución no prueba el colapso, pero tampoco autoriza el diseño.
- **Comando**: `python3 verificacion.py` (cruce automático con la referencia
  más afín) o `pipeline.hibrido(e_a, e_b, t, material, 0)` desde Python.

### 3.2 Materiales

| Cambio | Qué cambia en el cálculo | Qué hay que repetir |
|---|---|---|
| Piedra ↔ ladrillo ↔ hormigón (densidad uniforme) | Nada en el GSF: el equilibrio de Heyman es geométrico | DfAM (masa por pieza, envolvente de máquina), IFC |
| Relleno de senos distinto | Cargas y, con ellas, la línea de empujes | Heyman completo |
| Piedra CNC ↔ impresión 3D (3DCP) | Nada en el equilibrio | Restricciones de fabricación: voladizo ≤ 25°, espesor ≥ 0.08 m, diedro ≥ 20° (3DCP); planeidad de juntas ≤ 3 mm, diedro ≥ 35°, masa ≤ 6 t (CNC) |
| Fábrica con mortero de baja resistencia | Comprobación de tensión media (las hipótesis de Heyman exigen compresión suficiente) | Comprobar σ con la resistencia real del material |

Cada pieza del despiece lleva `metodo_recomendado` (`piedra_cnc`, `3dcp`,
`revisar`) y los motivos de fallo de cada ruta (`despiece.csv`).

### 3.3 Detalles constructivos

- **Plantillas de corte** (`plantillas.dxf`): cada cara de cada clase de piezas
  congruentes, desarrollada en su plano, con el número de unidades; sirve para
  cantería tradicional, corte por chorro de agua o como control dimensional.
- **Montea** (`montea.dxf`): secciones 1:1 por los ejes de simetría, con el
  intradós teórico; base para cimbras y para comprobar juntas.
- **Arranques, claves y nervios**: capas separadas en `modelo_3d.dxf`, XDATA con
  id, masa y orden de montaje.
- **Condición**: los detalles heredan las tolerancias de la gramática
  (planeidad de juntas declarada por pieza); no sustituyen el despiece de taller.

### 3.4 Propuestas arquitectónicas

- El IFC 4.3 (`modelo.ifczip`, Psets `ESTM_*`, IDS LOD 400) se vincula a Revit,
  ArchiCAD o BlenderBIM como ensamblaje de piezas con sus juntas
  (`IfcRelConnectsElements`).
- La obra se escala por su **luz**: el genoma es adimensional (espesor y canto
  relativos), pero el GSF **sí** depende de la proporción, no del tamaño; las
  restricciones de fabricación dependen del tamaño y se recalculan.
- Para bóvedas sobre pilares (β < 0.5) el análisis da el empuje horizontal por
  apoyo y un estribo de referencia (0.30 L × 0.15 L): el proyecto debe
  dimensionar sus propios estribos con esa reacción.

### 3.5 Replanteo de diseño

- `replanteo.csv` y `planta_replanteo.dxf` comparten los mismos puntos numerados:
  V (vértices de planta en la línea de impostas), A (asiento de arranques),
  C (claves), N (trazas de nervios con cota de intradós) y K (cimbras: intradós
  a lo largo del eje de cada sector en cada hilada).
- Origen en el centro de la planta y cota 0 en la línea de impostas: se lleva
  a coordenadas de obra con una traslación y un giro (dos puntos V conocidos).
- Uso con estación total: importar el CSV; comprobar la planta con los V y las
  cimbras con los K antes de asentar la primera hilada.
- **Replanteo inverso** (de lo construido al modelo): levantar las piezas, pasar
  por la verificación ciega y comparar el genoma inferido con el de proyecto; la
  fidelidad geométrica mide la desviación.

### 3.6 Patrimonio (levantamientos)

- Entrada: nube de puntos o malla **segmentada en piezas** (un grupo OBJ o un
  elemento IFC por pieza). Sin segmentación no hay grafo de juntas.
- Salida: tipos de pieza, genoma, reconstrucción, análisis de Heyman y novedad
  frente al corpus.
- **Límites**: el genoma describe la regla de traza, no las deformaciones,
  grietas ni asientos; una reconstrucción admisible no prueba que la obra real
  lo sea. Material y relleno deben venir de la inspección. Cualquier dictamen
  sobre un edificio real requiere un técnico competente.

## 4. Entregables

Cada producto se exporta con `estm.productos.exportar(obra, carpeta)`; la
tabla completa de formatos y programas está en
[`estm/productos/__init__.py`](../estm/productos/__init__.py) y en el `LEEME.md`
de cada carpeta. Resumen:

| Necesidad | Archivo |
|---|---|
| CAD 2D/3D (AutoCAD, BricsCAD, SketchUp Pro, Rhino) | `modelo_3d.dxf`, `planta_replanteo.dxf`, `montea.dxf`, `plantillas.dxf` |
| **.dwg** | `python3 -m estm.productos.dwg <carpeta>` con ODA File Converter o LibreDWG (DWG es propietario; los DXF R2018 abren sin conversión en los mismos programas) |
| **SketchUp (.skp)** | `importar_estm.rb` (Consola de Ruby → guardar como .skp) o importar `modelo.dae`; el producto escaparate se construyó también como `.skp` nativo con SketchUp (miniatura en su carpeta) |
| BIM | `modelo.ifczip` (IFC 4.3, IDS LOD 400) |
| Fabricación | `piezas_stl.zip` (un STL por pieza), `despiece.csv` |
| Obra | `replanteo.csv` |
| Revisión | `visor.html` (navegador: órbita, capas, secuencia de montaje, ficha de pieza), `modelo.glb` |
| Programación | `piezas.json`, `modelo.obj` |

## 5. Límites de la verificación

- Las obras nuevas de la prueba se **generan con la misma gramática** que las
  referencias, con genomas que no están en el entrenamiento (órdenes 6, 8 y 12,
  estrellas {8/2}, {8/3} y {8/4}, terceletes octogonales, mocárabes de piedra y
  de ladrillo, mezclas mudéjares). Por tanto se mide la **inversión** de la
  gramática y la selección, no la generalización a sistemas que la gramática no
  puede describir (bóvedas de horno, lunetos, trompas, cúpulas sobre pechinas);
  esas obras deben salir como `novedad` o como no interpretables, nunca con una
  reconstrucción confiada.
- El ruido de la prueba (1.5 mm) es el de un escáner terrestre; la fotogrametría
  de baja calidad necesita `tol` mayor en la detección de contactos.
- Las pseudo-etiquetas con las que el sistema se autoentrena provienen de su
  propia reconstrucción: si la reconstrucción es mala, el error se propaga. Por
  eso solo se ingieren obras que superan G3 por fidelidad geométrica y el
  registro de eventos permite revertir cualquier episodio.
- Heyman supone fábrica sin tracción, sin deslizamiento y con compresión
  suficiente; el GSF es un factor geométrico, no un coeficiente de seguridad de
  norma.

## 6. Comandos

```bash
make estm-test          # pruebas (incluye la verificación ciega reducida y los productos)
make estm               # pipeline de referencias, síntesis e IFC
make estm-verificacion  # verificación ciega completa + productos (~8 min)
python3 -m estm.productos.dwg salidas/verificacion/productos/<ID>   # DXF -> DWG
```
