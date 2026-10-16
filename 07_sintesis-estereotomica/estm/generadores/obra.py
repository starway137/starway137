"""Contenedor de una obra: grafo, genoma, metadatos y secciones de análisis."""

from dataclasses import dataclass, field


@dataclass
class Obra:
    id: str
    nombre: str
    tradicion: str
    genoma: dict
    grafo: object
    meta: dict = field(default_factory=dict)
    # constructor(t) -> (juntas, piezas) para el análisis de líneas de empujes
    seccion: object = None
    espesor: float = 0.0
    superficie: object = None
    analisis: dict = field(default_factory=dict)
    z_trasdos: object = None
