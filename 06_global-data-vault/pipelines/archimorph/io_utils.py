"""Lectura y escritura tipada de CSV / JSON."""

import csv
import json
from pathlib import Path

# Columnas numéricas conocidas en las tablas del vault
NUMERIC_COLUMNS = {
    "nivel_jerarquico", "es_masa_portante", "largo_m", "ancho_m", "alto_m",
    "factor_volumen", "fecha_aprox", "incertidumbre_rel",
    "densidad_kg_m3", "fc_min_MPa", "fc_max_MPa",
}


def to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    value = str(value).strip()
    if value == "":
        return None
    return float(value)


def read_csv(path, numeric=NUMERIC_COLUMNS):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        for key in list(row):
            if key in numeric:
                row[key] = to_float(row[key])
            elif row[key] is not None:
                row[key] = row[key].strip()
    return rows


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _fmt(row.get(k)) for k in fieldnames})


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return value


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(_round(obj), fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def _round(obj, digits=6):
    """Redondea floats para que los artefactos generados sean estables en git."""
    if isinstance(obj, float):
        return float(f"{obj:.{digits}g}")
    if isinstance(obj, dict):
        return {k: _round(v, digits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_round(v, digits) for v in obj]
    return obj
