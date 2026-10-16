# HX-CA-NER-NV-MUD-R-050 · Híbrido CA-NER→NV-MUD-R t=0.50

- Piezas: 481 en 29 clases de forma · puntos de replanteo: 113
- Equilibrio (Heyman): admisible · GSF 1.65 (rebanada)
- Fabricación: piedra CNC 80% · 3DCP 33% · fabricable 80%
- Genoma: orden_radial=8, salto_estrella_rel=0.375, terceletes=0, apuntamiento=0.28, beta_superficie=0.987, espesor_rel=0.0744, mocarabe_rel=0.182, inclinacion_junta=1, despiece=8, canto_nervio_rel=0.046

Unidades: metros, Z vertical, origen en el centro de la planta a la cota de impostas.

| Archivo | Abrir con | Para |
|---|---|---|
| `modelo_3d.dxf` | AutoCAD, BricsCAD, DraftSight, SketchUp Pro, Rhino | modelo de piezas por capas + XDATA |
| `planta_replanteo.dxf` | cualquier CAD 2D | replanteo en obra, cotas |
| `montea.dxf` | cualquier CAD 2D | secciones 1:1 (cimbras, plantillas) |
| `plantillas.dxf` | CAD 2D, corte por chorro de agua / plotter | plantillas de cada cara por clase |
| `modelo.dae` | SketchUp (Importar), Blender, 3ds Max, Rhino | modelo despiezable con materiales |
| `modelo.glb` | visores web, Windows 3D Viewer, Blender, AR | revisión y presentación |
| `modelo.obj / .mtl` | Rhino, Blender, MeshLab, Grasshopper | intercambio de mallas |
| `piezas_stl.zip` | CAM de 5 ejes, laminadores de impresión 3D | fabricación pieza a pieza |
| `despiece.csv` | Excel, LibreOffice, ERP de cantería | lista de piezas, masas, fabricación |
| `replanteo.csv` | estación total, Excel | coordenadas de puntos de replanteo |
| `piezas.json` | Grasshopper (estm/interop), scripts | fuente de datos única |
| `importar_estm.rb` | SketchUp (Consola de Ruby) | reconstrucción nativa -> .skp |
| `visor.html` | cualquier navegador | visor 3D con secuencia de montaje |
| `modelo.ifczip` | Revit, ArchiCAD, BlenderBIM, Solibri, Navisworks | BIM LOD 400 con Psets ESTM_* |

Este producto se construyó además como **.skp nativo** con SketchUp (481 grupos sólidos en 5 subconjuntos por tipo, una etiqueta y un material por tipo, escenas «Exterior», «Intradós (vista de gusano)» y «Planta»); `modelo_skp_miniatura.png` es su miniatura. El mismo .skp se obtiene en local ejecutando `importar_estm.rb`.

**.dwg**: `python3 -m estm.productos.dwg <esta carpeta>` (ODA File Converter o LibreDWG).
**.skp**: en SketchUp, Ventana > Consola de Ruby > `load '<esta carpeta>/importar_estm.rb'` y guardar; o Archivo > Importar > `modelo.dae`.
