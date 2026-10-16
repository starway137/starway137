"""Productos ejecutables de una obra (histórica reconstruida, híbrida o nueva).

    exportar(obra, carpeta)  ->  lista de archivos

| Archivo                 | Se abre / ejecuta en                                   | Uso                                  |
|-------------------------|--------------------------------------------------------|--------------------------------------|
| modelo_3d.dxf           | AutoCAD, BricsCAD, DraftSight, SketchUp Pro, Rhino     | modelo de piezas por capas + XDATA   |
| planta_replanteo.dxf    | cualquier CAD 2D                                       | replanteo en obra, cotas             |
| montea.dxf              | cualquier CAD 2D                                       | secciones 1:1 (cimbras, plantillas)  |
| plantillas.dxf          | CAD 2D, corte por chorro de agua / plotter             | plantillas de cada cara por clase    |
| modelo.dae              | SketchUp (Importar), Blender, 3ds Max, Rhino           | modelo despiezable con materiales    |
| modelo.glb              | visores web, Windows 3D Viewer, Blender, AR            | revisión y presentación              |
| modelo.obj / .mtl       | Rhino, Blender, MeshLab, Grasshopper                   | intercambio de mallas                |
| piezas_stl.zip          | CAM de 5 ejes, laminadores de impresión 3D             | fabricación pieza a pieza            |
| despiece.csv            | Excel, LibreOffice, ERP de cantería                    | lista de piezas, masas, fabricación  |
| replanteo.csv           | estación total, Excel                                  | coordenadas de puntos de replanteo   |
| piezas.json             | Grasshopper (estm/interop), scripts                    | fuente de datos única                |
| importar_estm.rb        | SketchUp (Consola de Ruby)                             | reconstrucción nativa -> .skp        |
| visor.html              | cualquier navegador                                    | visor 3D con secuencia de montaje    |
| modelo.ifczip           | Revit, ArchiCAD, BlenderBIM, Solibri, Navisworks       | BIM LOD 400 con Psets ESTM_*         |

.dwg: `python3 -m estm.productos.dwg <carpeta>` (necesita ODA File Converter o
LibreDWG). .skp: ejecutar importar_estm.rb en SketchUp y guardar.
"""

from pathlib import Path

from . import cad, datos, mallas, sketchup, visor
from .mallas import color

ESCAPARATE = ("NV-MUD",)          # obras nuevas cuyos productos se versionan en el repositorio


def exportar(obra, carpeta, ifc=True):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    clases = cad.clases_piezas(obra.grafo)
    puntos = datos.puntos_replanteo(obra)
    archivos = []
    archivos += cad.modelo_3d(obra, carpeta / "modelo_3d.dxf")
    archivos += cad.planta_replanteo(obra, carpeta / "planta_replanteo.dxf", puntos)
    archivos += cad.montea(obra, carpeta / "montea.dxf")
    archivos += cad.plantillas(obra, carpeta / "plantillas.dxf", clases)
    archivos += mallas.dae(obra, carpeta / "modelo.dae")
    archivos += mallas.glb(obra, carpeta / "modelo.glb")
    archivos += mallas.obj(obra, carpeta / "modelo.obj")
    archivos += mallas.stl(obra, carpeta / "piezas_stl.zip")
    archivos += datos.despiece(obra, carpeta / "despiece.csv", clases)
    archivos += datos.escribir_replanteo(puntos, carpeta / "replanteo.csv")
    archivos += datos.piezas_json(obra, carpeta / "piezas.json")
    archivos += sketchup.ruby(carpeta / "importar_estm.rb",
                              {t: color(t) for t in {d["tipo"] for d in obra.grafo.nodos.values()}})
    est = obra.analisis.get("estructura", {})
    archivos += visor.visor(obra, carpeta / "visor.html",
                            f"{obra.nombre} · GSF {est.get('GSF', 0):.2f} ({est.get('metodo', '—')}) · "
                            f"{len(obra.grafo.piezas())} piezas")
    if ifc:
        from ..interop import ifc as ifc_mod
        ruta = carpeta / "modelo.ifc"
        ifc_mod.exportar([obra], ruta, nombre_proyecto=f"ESTM · {obra.id}")
        destino = ifc_mod.comprimir(ruta)
        ruta.unlink()
        archivos.append(destino)
    archivos.append(_leeme(obra, carpeta, clases, puntos))
    return archivos


def _leeme(obra, carpeta, clases, puntos):
    est = obra.analisis.get("estructura", {})
    fab = obra.analisis.get("fabricacion", {})
    L = [f"# {obra.id} · {obra.nombre}", "",
         f"- Piezas: {len(obra.grafo.piezas())} en {len(clases)} clases de forma · puntos de replanteo: {len(puntos)}",
         f"- Equilibrio (Heyman): {'admisible' if est.get('admisible') else 'NO encontrado'} · "
         f"GSF {est.get('GSF', 0):.2f} ({est.get('metodo', '—')})",
         f"- Fabricación: piedra CNC {fab.get('piedra_cnc', {}).get('fraccion_ok', 0):.0%} · "
         f"3DCP {fab.get('3dcp', {}).get('fraccion_ok', 0):.0%} · fabricable {fab.get('fraccion_fabricable', 0):.0%}",
         f"- Genoma: {', '.join(f'{k}={v:.3g}' for k, v in obra.genoma.items())}", "",
         "Unidades: metros, Z vertical, origen en el centro de la planta a la cota de impostas.", "",
         "| Archivo | Abrir con | Para |", "|---|---|---|"]
    for fila in __doc__.split("\n"):
        if fila.startswith("| ") and not fila.startswith("| Archivo") and "---" not in fila:
            celdas = [c.strip() for c in fila.strip("|").split("|")]
            L.append(f"| `{celdas[0]}` | {celdas[1]} | {celdas[2]} |")
    if (carpeta / "modelo_skp_miniatura.png").exists():
        L += ["", "Este producto se construyó además como **.skp nativo** con SketchUp (481 grupos sólidos en 5 "
              "subconjuntos por tipo, una etiqueta y un material por tipo, escenas «Exterior», «Intradós (vista de "
              "gusano)» y «Planta»); `modelo_skp_miniatura.png` es su miniatura. El mismo .skp se obtiene en local "
              "ejecutando `importar_estm.rb`."]
    L += ["", "**.dwg**: `python3 -m estm.productos.dwg <esta carpeta>` (ODA File Converter o LibreDWG).",
          "**.skp**: en SketchUp, Ventana > Consola de Ruby > `load '<esta carpeta>/importar_estm.rb'` y guardar; "
          "o Archivo > Importar > `modelo.dae`."]
    ruta = carpeta / "LEEME.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    return ruta
