"""Rutas del repositorio y registro de los cinco casos de estudio."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VAULT = ROOT / "06_global-data-vault"
SCHEMA = VAULT / "schema"
DATASETS = VAULT / "datasets"
ML = DATASETS / "ml"
MODELOS = VAULT / "modelos"
PRIORS = VAULT / "priors"
REPORTS = VAULT / "reports"
CODISENO = VAULT / "codiseno"

# Identificador corto -> carpeta del caso de estudio
SITES = {
    "AW": "01_angkor-wat",
    "KL": "02_templo-kailasa",
    "AY": "03_ciudad-antigua-sukhothai-ayutthaya",
    "MD": "04_mohenjo-daro",
    "SN": "05_estupa-sanchi",
}

SUBDIRS = ("docs", "analysis", "cad_parametric", "data")


def site_dir(sid):
    return ROOT / SITES[sid]


def elementos_path(sid):
    return site_dir(sid) / "data" / "elementos.csv"


def descriptores_path(sid):
    return site_dir(sid) / "data" / "descriptores.json"


def features_path(sid):
    return site_dir(sid) / "data" / "features.json"


def fuentes_path(sid):
    return site_dir(sid) / "docs" / "fuentes.md"


def cad_dir(sid):
    return site_dir(sid) / "cad_parametric"
