"""Exportación OpenBIM: IFC 4.3 (IFC4X3_ADD2) a nivel de pieza (LOD 400).

Mapeo grafo -> IFC
    obra                    IfcElementAssembly (USERDEFINED, ObjectType = tipología)
    pieza (nodo con malla)  IfcBuildingElementPart (USERDEFINED, ObjectType = tipo de pieza)
                            geometría IfcPolygonalFaceSet en el contexto Body
    apoyo (nodo sin malla)  IfcVirtualElement
    junta (arista)          IfcRelConnectsElements (Name = tipo; Description = atributos JSON)
    descomposición          IfcRelAggregates (obra -> piezas)
    tipo de pieza           IfcClassificationReference (clasificación ESTM)
    material                IfcMaterial (por obra)

Psets propios (prefijo ESTM_, nunca Pset_, reservado a buildingSMART):
    ESTM_Obra            tradición, genoma, verificación de Heyman
    ESTM_Pieza           identificador, tipo, hilada, sector, masa, volumen
    ESTM_Estereotomia    inclinación de junta, caras de junta, planeidad
    ESTM_Equilibrio      estado del límite inferior de la obra a la que pertenece
    ESTM_Fabricacion     ruta recomendada, verificaciones CNC y 3DCP, montaje, cimbra
    ESTM_LOD             nivel 400, tolerancia, estado de la información
Cantidades: Qto_ESTM_Pieza (NetVolume, NetWeight).

Los GlobalId son deterministas (uuid5 sobre el identificador de obra y
pieza): reexportar la misma obra conserva la identidad de cada elemento,
requisito para el intercambio incremental con Grasshopper/Speckle.
"""

import json
import uuid
import zipfile
from pathlib import Path

import numpy as np

NS = uuid.UUID("6f1d8a52-6b5e-4f2b-9f9e-0d8b0b6a7e31")
FECHA_FIJA = "2026-10-16T00:00:00"


def _guid(texto):
    import ifcopenshell.guid
    return ifcopenshell.guid.compress(uuid.uuid5(NS, texto).hex)


def _valor(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return float(round(float(v), 6))
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _pset(api, f, producto, nombre, props):
    limpio = {k: _valor(v) for k, v in props.items() if v is not None}
    pset = api.pset.add_pset(f, product=producto, name=nombre)
    api.pset.edit_pset(f, pset=pset, properties=limpio)


def exportar(obras, ruta, nombre_proyecto="ESTM - Síntesis estereotómica", separacion=4.0):
    import ifcopenshell
    import ifcopenshell.api as api
    import ifcopenshell.api.aggregate  # noqa: F401
    import ifcopenshell.api.classification  # noqa: F401
    import ifcopenshell.api.context  # noqa: F401
    import ifcopenshell.api.geometry  # noqa: F401
    import ifcopenshell.api.material  # noqa: F401
    import ifcopenshell.api.project  # noqa: F401
    import ifcopenshell.api.pset  # noqa: F401
    import ifcopenshell.api.root  # noqa: F401
    import ifcopenshell.api.spatial  # noqa: F401
    import ifcopenshell.api.unit  # noqa: F401

    f = api.project.create_file(version="IFC4X3_ADD2")
    proyecto = api.root.create_entity(f, ifc_class="IfcProject", name=nombre_proyecto)
    api.unit.assign_unit(f, length={"is_metric": True, "raw": "METERS"})
    for ua in f.by_type("IfcUnitAssignment"):          # orden estable (assign_unit usa un conjunto)
        ua.Units = sorted(ua.Units, key=lambda u: u.id())
    modelo = api.context.add_context(f, context_type="Model")
    cuerpo = api.context.add_context(f, context_type="Model", context_identifier="Body",
                                     target_view="MODEL_VIEW", parent=modelo)
    sitio = api.root.create_entity(f, ifc_class="IfcSite", name="Emplazamiento de referencia")
    edificio = api.root.create_entity(f, ifc_class="IfcBuilding", name="Catálogo de obras")
    planta = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name="Nivel de arranques")
    # Las relaciones se crean directamente con el esquema (orden estable y
    # reproducible); la API de alto nivel usa conjuntos y reordena.
    origen = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)

    def colocar(producto, dx=0.0):
        eje = origen if dx == 0 else f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((dx, 0.0, 0.0)),
                                                                   None, None)
        producto.ObjectPlacement = f.createIfcLocalPlacement(None, eje)

    for padre, hijo in ((proyecto, sitio), (sitio, edificio), (edificio, planta)):
        f.createIfcRelAggregates(None, None, None, None, padre, [hijo])
        if hijo.is_a("IfcSpatialStructureElement"):
            colocar(hijo)
    clasif = f.createIfcClassification(None, "1.0", None, "ESTM-Piezas",
                                       "Tipos de pieza de fábrica del grafo atribuido ESTM", None, None)
    referencias, por_tipo = {}, {}
    materiales, por_material = {}, {}
    contenidos = []

    x0 = 0.0
    for obra in obras:
        g = obra.grafo
        semiancho = max((max(abs(v[0]) for v in geo.V) for geo in g.geometrias.values()), default=1.0)
        x0 += semiancho
        M = np.eye(4)
        M[0, 3] = x0
        x0 += semiancho + separacion
        ens = api.root.create_entity(f, ifc_class="IfcElementAssembly", name=obra.nombre,
                                     predefined_type="USERDEFINED")
        ens.GlobalId = _guid(f"obra/{obra.id}")
        ens.ObjectType = g.atributos.get("tipologia", "fabrica").upper()
        ens.Description = f"{obra.id} · {obra.tradicion}"
        contenidos.append(ens)
        colocar(ens, float(M[0, 3]))
        est = obra.analisis.get("estructura", {})
        _pset(api, f, ens, "ESTM_Obra", {
            "Identificador": obra.id, "Tradicion": obra.tradicion,
            "Genoma": obra.genoma, "Admisible_LimiteInferior": est.get("admisible"),
            "FactorSeguridadGeometrico": est.get("GSF"), "MetodoEquilibrio": est.get("metodo"),
            "Fuente": obra.meta.get("fuente"), "CalidadDato": obra.meta.get("calidad"),
        })
        mat_id = g.atributos.get("material", "caliza")
        if mat_id not in materiales:
            materiales[mat_id] = f.createIfcMaterial(mat_id, None, "concrete" if mat_id == "hormigon_3dcp" else "masonry")
            por_material[mat_id] = []
        nodos_ifc = {}
        partes = []
        for nid in g.orden():
            d = g.nodos[nid]
            if nid in g.geometrias:
                geo = g.geometrias[nid]
                parte = api.root.create_entity(f, ifc_class="IfcBuildingElementPart", name=nid,
                                               predefined_type="USERDEFINED")
                parte.GlobalId = _guid(f"{obra.id}/{nid}")
                parte.ObjectType = d["tipo"].upper()
                rep = api.geometry.add_mesh_representation(f, context=cuerpo, vertices=[geo.V.tolist()],
                                                           faces=[geo.F])
                parte.Representation = f.createIfcProductDefinitionShape(None, None, [rep])
                colocar(parte, float(M[0, 3]))
                fab_c, fab_3 = d.get("fab_cnc", {}), d.get("fab_3dcp", {})
                _pset(api, f, parte, "ESTM_Pieza", {
                    "Identificador": nid, "Obra": obra.id, "TipoPieza": d["tipo"], "Tradicion": obra.tradicion,
                    "Hilada": d.get("hilada"), "Sector": d.get("sector"), "Nivel": d.get("nivel"),
                    "Masa_kg": d.get("masa_kg"), "Volumen_m3": d.get("volumen_m3"),
                    "Centroide": d.get("centroide"), "Extensiones_m": d.get("extensiones_m"),
                })
                _pset(api, f, parte, "ESTM_Estereotomia", {
                    "InclinacionJunta": d.get("inclinacion_junta", d.get("inclinacion_junta_deg")),
                    "PlaneidadJuntas_mm": fab_c.get("planeidad_juntas_mm"),
                    "DiedroMinimo_deg": fab_c.get("diedro_min_deg"), "Matajunta": d.get("matajunta"),
                })
                _pset(api, f, parte, "ESTM_Equilibrio", {
                    "ObraAdmisible": est.get("admisible"), "GSF_Obra": est.get("GSF"),
                    "MetodoEquilibrio": est.get("metodo"),
                })
                _pset(api, f, parte, "ESTM_Fabricacion", {
                    "MetodoRecomendado": d.get("metodo_recomendado", "sin_evaluar"),
                    "CNC_Viable": fab_c.get("ok"), "CNC_Fallos": ",".join(fab_c.get("fallos", [])),
                    "CNC_Aprovechamiento": fab_c.get("aprovechamiento"),
                    "Impresion3D_Viable": fab_3.get("ok"), "Impresion3D_Fallos": ",".join(fab_3.get("fallos", [])),
                    "Impresion3D_Orientacion": fab_3.get("orientacion"),
                    "Impresion3D_Voladizo_deg": fab_3.get("voladizo_deg"),
                    "OrdenMontaje": d.get("orden_montaje"), "RequiereCimbra": d.get("requiere_cimbra"),
                })
                _pset(api, f, parte, "ESTM_LOD", {
                    "NivelLOD": 400, "ToleranciaFabricacion_mm": 2.0,
                    "EstadoInformacion": "geometria_de_fabricacion_por_pieza",
                })
                qto = api.pset.add_qto(f, product=parte, name="Qto_ESTM_Pieza")
                api.pset.edit_qto(f, qto=qto, properties={"NetVolume": float(d.get("volumen_m3", 0.0)),
                                                          "NetWeight": float(d.get("masa_kg", 0.0))})
                if d["tipo"] not in referencias:
                    referencias[d["tipo"]] = f.createIfcClassificationReference(
                        None, d["tipo"], d["tipo"].replace("_", " "), clasif, None, None)
                    por_tipo[d["tipo"]] = []
                por_tipo[d["tipo"]].append(parte)
                partes.append(parte)
                nodos_ifc[nid] = parte
            else:
                virt = api.root.create_entity(f, ifc_class="IfcVirtualElement", name=nid)
                virt.GlobalId = _guid(f"{obra.id}/{nid}")
                virt.Description = d.get("soporte", d["tipo"])
                colocar(virt, float(M[0, 3]))
                contenidos.append(virt)
                nodos_ifc[nid] = virt
        if partes:
            f.createIfcRelAggregates(None, None, None, None, ens, partes)
            por_material[mat_id] += partes
        for (a, b), d in sorted(g.aristas.items()):
            attrs = {k: d[k] for k in ("area_m2", "inclinacion_deg", "normal") if k in d}
            f.create_entity("IfcRelConnectsElements", GlobalId=_guid(f"{obra.id}/{a}/{b}"),
                            Name=d["tipo"], Description=json.dumps(attrs),
                            RelatingElement=nodos_ifc[a], RelatedElement=nodos_ifc[b])
    f.createIfcRelContainedInSpatialStructure(None, None, None, None, contenidos, planta)
    for tipo, prods in por_tipo.items():
        f.createIfcRelAssociatesClassification(None, None, None, None, prods, referencias[tipo])
    for mat_id, prods in por_material.items():
        if prods:
            f.createIfcRelAssociatesMaterial(None, None, None, None, prods, materiales[mat_id])
    # identidad determinista del resto de entidades (proyecto, relaciones, psets) por orden de creación
    con_id = ("IfcRelConnectsElements", "IfcBuildingElementPart", "IfcVirtualElement", "IfcElementAssembly")
    for i, ent in enumerate(f.by_type("IfcRoot")):
        if not any(ent.is_a(c) for c in con_id):
            ent.GlobalId = _guid(f"{ent.is_a()}/{i}")
    f.header.file_name.name = Path(ruta).name
    f.header.file_name.time_stamp = FECHA_FIJA
    f.header.file_name.author = ("ESTM pipeline",)
    f.header.file_name.organization = ("starway137",)
    f.header.file_description.description = ("ViewDefinition [ReferenceView]", "LOD 400 fabrication parts")
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    f.write(str(ruta))
    return f


def comprimir(ruta_ifc):
    """ifcZIP (zip con un único .ifc), con marca de tiempo fija para reproducibilidad."""
    ruta_ifc = Path(ruta_ifc)
    destino = ruta_ifc.with_suffix(".ifczip")
    info = zipfile.ZipInfo(ruta_ifc.name, date_time=(2026, 10, 16, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr(info, ruta_ifc.read_bytes())
    return destino


def resumen(ruta_ifc):
    import ifcopenshell
    f = ifcopenshell.open(str(ruta_ifc))
    return {"esquema": f.schema_identifier,
            "piezas": len(f.by_type("IfcBuildingElementPart")),
            "ensamblajes": len(f.by_type("IfcElementAssembly")),
            "juntas": len(f.by_type("IfcRelConnectsElements")),
            "psets": len(f.by_type("IfcPropertySet")),
            "caras_poligonales": len(f.by_type("IfcPolygonalFaceSet"))}
