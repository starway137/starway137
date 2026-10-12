"""Validación de estructura, esquema e integridad referencial de los casos."""

import re

from . import io_utils, paths

COLUMNAS = [
    "element_id", "nombre", "tipo", "nivel_jerarquico", "es_masa_portante",
    "forma_planta", "largo_m", "ancho_m", "alto_m", "factor_volumen", "material",
    "fase", "fecha_aprox", "calidad_dato", "incertidumbre_rel", "fuente_id", "notas",
]
FORMAS = {"rect", "cuadrado", "circulo"}
CALIDADES = {"A", "B", "C"}
CLAVES_DESCRIPTOR = [
    "sitio_id", "nombre", "pais", "coordenadas", "cronologia", "tipologia",
    "cosmograma", "patron_compositivo", "proceso_constructivo", "sistema_estructural",
    "material_principal", "modulo_metrico", "eje_principal", "simetria",
    "recinto_principal_id", "masa_principal_id", "estimaciones",
    "etiquetas_morfologicas", "hipotesis_ids", "licencia_datos",
]


def _source_ids(sid):
    text = paths.fuentes_path(sid).read_text(encoding="utf-8")
    return set(re.findall(r"\[([A-Z]{2}-\d{2})\]", text))


def validate_site(sid, materials):
    errors = []
    d = paths.site_dir(sid)
    for sub in paths.SUBDIRS:
        if not (d / sub).is_dir():
            errors.append(f"{sid}: falta la subcarpeta {sub}/")

    with open(paths.elementos_path(sid), encoding="utf-8") as fh:
        header = fh.readline().strip().split(",")
    if header != COLUMNAS:
        errors.append(f"{sid}: columnas de elementos.csv no coinciden con el esquema")

    elems = io_utils.read_csv(paths.elementos_path(sid))
    desc = io_utils.read_json(paths.descriptores_path(sid))
    sources = _source_ids(sid)
    ids = [e["element_id"] for e in elems]
    if len(ids) != len(set(ids)):
        errors.append(f"{sid}: element_id duplicados")

    for e in elems:
        eid = e["element_id"]
        if not eid.startswith(sid + "-"):
            errors.append(f"{eid}: el prefijo no coincide con el sitio {sid}")
        if e["forma_planta"] not in FORMAS:
            errors.append(f"{eid}: forma_planta inválida '{e['forma_planta']}'")
        if e["calidad_dato"] not in CALIDADES:
            errors.append(f"{eid}: calidad_dato inválida")
        if not e["largo_m"] or not e["ancho_m"] or e["largo_m"] <= 0 or e["ancho_m"] <= 0:
            errors.append(f"{eid}: largo/ancho deben ser > 0")
        elif e["forma_planta"] in ("cuadrado", "circulo") and e["largo_m"] != e["ancho_m"]:
            errors.append(f"{eid}: {e['forma_planta']} exige largo == ancho")
        if e["material"] != "na" and e["material"] not in materials:
            errors.append(f"{eid}: material desconocido '{e['material']}'")
        if e["fuente_id"] not in sources:
            errors.append(f"{eid}: fuente {e['fuente_id']} no figura en docs/fuentes.md")
        if e["incertidumbre_rel"] is None or not 0 < e["incertidumbre_rel"] < 1:
            errors.append(f"{eid}: incertidumbre_rel debe estar en (0, 1)")
        if e["es_masa_portante"] == 1:
            if not e["alto_m"]:
                errors.append(f"{eid}: masa portante sin alto_m")
            if not e["factor_volumen"] or not 0 < e["factor_volumen"] <= 1:
                errors.append(f"{eid}: masa portante con factor_volumen fuera de (0, 1]")
            if materials.get(e["material"], {}).get("fc_min_MPa") is None:
                errors.append(f"{eid}: masa portante con material sin resistencia")

    chain = sorted((e for e in elems if e["nivel_jerarquico"] is not None),
                   key=lambda e: e["nivel_jerarquico"])
    levels = [int(e["nivel_jerarquico"]) for e in chain]
    if levels != list(range(len(levels))):
        errors.append(f"{sid}: los niveles jerárquicos deben ser 0..n consecutivos")
    if len(chain) < 3:
        errors.append(f"{sid}: la cadena de inclusión necesita al menos 3 niveles")
    sizes = [max(e["largo_m"], e["ancho_m"]) for e in chain]
    if any(b >= a for a, b in zip(sizes, sizes[1:])):
        errors.append(f"{sid}: la cadena de inclusión no es estrictamente decreciente")

    for key in CLAVES_DESCRIPTOR:
        if key not in desc:
            errors.append(f"{sid}: descriptores.json sin la clave '{key}'")
    if desc.get("sitio_id") != sid:
        errors.append(f"{sid}: sitio_id del descriptor no coincide")
    by_id = {e["element_id"]: e for e in elems}
    for key in ("recinto_principal_id", "masa_principal_id"):
        if desc.get(key) not in by_id:
            errors.append(f"{sid}: {key} '{desc.get(key)}' no existe en elementos.csv")
    if by_id.get(desc.get("masa_principal_id"), {}).get("es_masa_portante") != 1:
        errors.append(f"{sid}: la masa principal debe ser un elemento portante")
    for name, est in desc.get("estimaciones", {}).items():
        if not 0 <= est["valor"] <= 1 or est["calidad"] not in CALIDADES:
            errors.append(f"{sid}: estimación '{name}' inválida")

    hyp_text = (d / "docs" / "contexto_hipotesis.md").read_text(encoding="utf-8")
    for hid in desc.get("hipotesis_ids", []):
        if hid not in hyp_text:
            errors.append(f"{sid}: la hipótesis {hid} no está documentada en docs/")
    return errors


def validate_all(materials):
    errors = []
    for sid in paths.SITES:
        errors.extend(validate_site(sid, materials))
    return errors
