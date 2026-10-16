"""IDS 1.0 (buildingSMART Information Delivery Specification) para LOD 400.

Define los requisitos de información que debe cumplir cada entrega y los
valida con ifctester contra el IFC generado: la verificación no es una
afirmación del pipeline sino un contraste con un estándar abierto.
"""

from pathlib import Path


def construir():
    from ifctester import ids
    doc = ids.Ids(title="ESTM - Piezas de fábrica LOD 400", author="starway137@users.noreply.github.com",
                  version="1.0", description="Requisitos de información para piezas estereotómicas de fabricación",
                  purpose="Fabricación digital (CNC / 3DCP) y montaje", milestone="LOD 400")

    s1 = ids.Specification(name="Pieza de fábrica con identidad, tipo y material", ifcVersion=["IFC4X3_ADD2"],
                           identifier="ESTM-01", minOccurs=1)
    s1.applicability.append(ids.Entity(name="IFCBUILDINGELEMENTPART"))
    s1.requirements += [
        ids.Attribute(name="Name"),
        ids.Attribute(name="ObjectType"),
        ids.Material(),
        ids.Classification(system="ESTM-Piezas"),
        ids.Property(propertySet="ESTM_Pieza", baseName="Identificador", dataType="IFCLABEL"),
        ids.Property(propertySet="ESTM_Pieza", baseName="Masa_kg", dataType="IFCREAL"),
        ids.Property(propertySet="ESTM_Pieza", baseName="Volumen_m3", dataType="IFCREAL"),
    ]
    s2 = ids.Specification(name="Datos de fabricación y montaje", ifcVersion=["IFC4X3_ADD2"],
                           identifier="ESTM-02", minOccurs=1)
    s2.applicability.append(ids.Entity(name="IFCBUILDINGELEMENTPART"))
    s2.requirements += [
        ids.Property(propertySet="ESTM_Fabricacion", baseName="MetodoRecomendado", dataType="IFCLABEL"),
        ids.Property(propertySet="ESTM_Fabricacion", baseName="OrdenMontaje", dataType="IFCINTEGER"),
        ids.Property(propertySet="ESTM_Fabricacion", baseName="RequiereCimbra", dataType="IFCBOOLEAN"),
        ids.Property(propertySet="ESTM_LOD", baseName="NivelLOD", value="400", dataType="IFCINTEGER"),
        ids.Property(propertySet="ESTM_LOD", baseName="ToleranciaFabricacion_mm", dataType="IFCREAL"),
    ]
    s3 = ids.Specification(name="Obra con verificación de equilibrio", ifcVersion=["IFC4X3_ADD2"],
                           identifier="ESTM-03", minOccurs=1)
    s3.applicability.append(ids.Entity(name="IFCELEMENTASSEMBLY"))
    s3.requirements += [
        ids.Property(propertySet="ESTM_Obra", baseName="Admisible_LimiteInferior", dataType="IFCBOOLEAN"),
        ids.Property(propertySet="ESTM_Obra", baseName="FactorSeguridadGeometrico", dataType="IFCREAL"),
        ids.Property(propertySet="ESTM_Obra", baseName="Tradicion", dataType="IFCLABEL"),
    ]
    doc.specifications += [s1, s2, s3]
    return doc


def escribir(ruta):
    doc = construir()
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    doc.to_xml(str(ruta))
    return doc


def validar(ruta_ids, ruta_ifc):
    import ifcopenshell
    from ifctester import ids, reporter
    doc = ids.open(str(ruta_ids))
    doc.validate(ifcopenshell.open(str(ruta_ifc)))
    rep = reporter.Json(doc)
    rep.report()
    datos = rep.results
    return {
        "ids": Path(ruta_ids).name, "ifc": Path(ruta_ifc).name,
        "cumple": bool(datos["status"]),
        "especificaciones": [
            {"id": s.get("identifier") or s.get("id"), "nombre": s["name"], "cumple": bool(s["status"]),
             "aplicables": s.get("total_applicable"), "aprobadas": s.get("total_applicable_pass")}
            for s in datos["specifications"]
        ],
    }
