# Protocolo de interoperabilidad técnica (OpenBIM · Grasshopper · Speckle · LOD 400)

## 1. Principios

1. **Una sola fuente de verdad:** el grafo atribuido. IFC, Speckle y
   Grasshopper son proyecciones del mismo grafo y comparten identificadores.
2. **Identidad estable:** `GlobalId = compress(uuid5(NS, "<obra>/<pieza>"))`.
   Reexportar una obra conserva la identidad de cada pieza, lo que hace posible
   el intercambio incremental (actualizar en lugar de duplicar). En Speckle,
   `applicationId = "<obra>/<pieza>"` y `properties.ifc_globalid = GlobalId`.
3. **Reproducibilidad:** misma entrada, mismos bytes. La cabecera tiene fecha
   fija, las relaciones se crean en orden estable y el ifcZIP lleva marca de
   tiempo fija. Lo verifican `tests/test_estm.py` y la CI.
4. **Unidades:** SI. Metros (IfcSIUnit LENGTHUNIT sin prefijo), m², m³, kg, N.
   Ejes: x, y en planta, z vertical. Speckle y Grasshopper usan las mismas
   coordenadas (`units = "m"`).

## 2. IFC 4.3 (IFC4X3_ADD2)

### Estructura espacial y de descomposición

```
IfcProject
└─ IfcSite ─ IfcBuilding ─ IfcBuildingStorey "Nivel de arranques"
             └─ contiene: IfcElementAssembly (una por obra) · IfcVirtualElement (apoyos)
                 └─ IfcRelAggregates → IfcBuildingElementPart (una por pieza)
```

| Grafo | IFC | Detalle |
|---|---|---|
| obra | `IfcElementAssembly` (USERDEFINED) | `ObjectType` = tipología (BOVEDA, ARCO) |
| pieza | `IfcBuildingElementPart` (USERDEFINED) | `ObjectType` = tipo (DOVELA_NERVIO, PLEMENTO…) · `IfcPolygonalFaceSet` en `Body` |
| apoyo | `IfcVirtualElement` | `Description` = pilar / muro o tambor |
| junta (arista) | `IfcRelConnectsElements` | `Name` = tipo de junta · `Description` = JSON {área, inclinación, normal} |
| tipo de pieza | `IfcClassificationReference` | clasificación `ESTM-Piezas` 1.0 |
| material | `IfcMaterial` + `IfcRelAssociatesMaterial` | por obra |

Las juntas del grafo viajan como **relaciones nativas IFC**: un visor o una
herramienta de cómputo puede reconstruir G = (V, E) sin el JSON.

### Psets propios (prefijo `ESTM_`)

El prefijo `Pset_` está reservado a buildingSMART. Las propiedades propias se
declaran con prefijo de organización.

| Pset | Propiedades |
|---|---|
| `ESTM_Obra` (ensamblaje) | Identificador · Tradicion · Genoma (JSON) · Admisible_LimiteInferior · FactorSeguridadGeometrico · MetodoEquilibrio · Fuente · CalidadDato |
| `ESTM_Pieza` | Identificador · Obra · TipoPieza · Tradicion · Hilada · Sector · Nivel · Masa_kg · Volumen_m3 · Centroide · Extensiones_m |
| `ESTM_Estereotomia` | InclinacionJunta · PlaneidadJuntas_mm · DiedroMinimo_deg · Matajunta |
| `ESTM_Equilibrio` | ObraAdmisible · GSF_Obra · MetodoEquilibrio |
| `ESTM_Fabricacion` | MetodoRecomendado · CNC_Viable · CNC_Fallos · CNC_Aprovechamiento · Impresion3D_Viable · Impresion3D_Fallos · Impresion3D_Orientacion · Impresion3D_Voladizo_deg · OrdenMontaje · RequiereCimbra |
| `ESTM_LOD` | NivelLOD = 400 · ToleranciaFabricacion_mm · EstadoInformacion |
| `Qto_ESTM_Pieza` | NetVolume · NetWeight |

### Validación con IDS 1.0

`salidas/ifc/estm_lod400.ids` (buildingSMART Information Delivery
Specification) define tres especificaciones:

- **ESTM-01:** cada pieza tiene nombre, tipo, material, clasificación, masa y
  volumen.
- **ESTM-02:** datos de fabricación y montaje, con `NivelLOD = 400`.
- **ESTM-03:** cada obra declara su verificación de equilibrio.

Los IFC generados se validan con `ifctester` en el propio pipeline, y el
resultado queda en `salidas/ifc/validacion.json`. La geometría se ha
contrastado triangulando con `ifcopenshell.geom`: el volumen coincide con el
del grafo.

## 3. Grasshopper (Rhino 8)

Hay dos caminos:

| Camino | Cuándo | Cómo |
|---|---|---|
| **Archivo** | sin servidor, revisión de diseño | `pipeline.py` escribe `<obra>_gh.json`; el componente *Script* (Python 3) con `grasshopper/importar_estm.py` devuelve mallas, GUIDs, tipos, masas, orden de montaje y el grafo como líneas entre centroides |
| **Speckle** | colaboración y versiones | el conector de Speckle para Grasshopper recibe el modelo por `applicationId`, conservando la identidad entre versiones |
| **IFC** | entrega formal | abrir el ifcZIP en Rhino 8 (importador IFC) o en Bonsai/BlenderBIM |

El script de Grasshopper no se ha ejecutado dentro de Rhino en este
repositorio, porque no hay Rhino en la CI. Su lectura del JSON sí se prueba
(`test_carga_grasshopper_legible`).

## 4. Speckle

`estm/interop/speckle.py` produce un objeto del modelo de Speckle 2:

```
Base (obra)  applicationId "obra/<ID>", genoma, equilibrio
├─ @piezas : Objects.Geometry.Mesh  vertices [x,y,z,…], faces [n, i0…in-1, …], units "m",
│            applicationId "<ID>/<pieza>", properties {tipo, masa_kg, metodo, orden_montaje, ifc_globalid…}
└─ @juntas : Base {origen, destino, tipo, area_m2, inclinacion_deg}
```

`speckle.enviar()` publica una versión con `specklepy` (requiere el servidor y
un token personal en `SPECKLE_TOKEN`). No se ejecuta en el pipeline, porque el
repositorio no guarda credenciales, y no se ha probado contra un servidor.

## 5. Qué significa LOD 400 aquí

LOD 400 (BIMForum: elemento con información de **fabricación, montaje e
instalación**) se cumple a nivel de pieza para:

- [x] Geometría individual de cada pieza (malla cerrada, volumen exacto) con identidad estable.
- [x] Material, masa y volumen por pieza (Qto).
- [x] Uniones (juntas) con área, normal e inclinación, como relaciones IFC.
- [x] Ruta de fabricación recomendada y verificaciones CNC/3DCP con sus motivos de fallo.
- [x] Orden de montaje y necesidad de cimbra.
- [x] Requisitos verificados con IDS.

Lo que **no** incluye y una entrega de taller real necesitaría:

- [ ] Trayectorias de herramienta (G-code) y trayectorias de impresión. Se entregan la orientación y las restricciones, no el CAM.
- [ ] Geometría de detalle de los mocárabes: las celdas son prismáticas, sin el alvéolo curvo de las celdas nazaríes reales.
- [ ] Tolerancias por cara y juntas de mortero (se fija una tolerancia global de 2 mm).
- [ ] Levantamiento real: las obras del catálogo son reconstrucciones tipológicas.

## 6. Flujo recomendado

```
catálogo / levantamiento ─► pipeline.py ─► grafo + verificación + DfAM
                                         ├─► IFC 4.3 (+ IDS) ─► coordinación BIM, fabricante
                                         ├─► Speckle ─► Grasshopper / Rhino / Revit (versiones)
                                         └─► GH JSON ─► Grasshopper (sin servidor)
cambios de diseño en Grasshopper ─► genoma ─► pipeline.py (re-verificación) ─► misma identidad de piezas
```
