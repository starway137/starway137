"""Materiales: densidad y resistencia a compresión orientativas.

Bajo las hipótesis de Heyman la resistencia no interviene en el equilibrio;
se usa solo para comprobar que la tensión media de trabajo es baja.
"""

MATERIALES = {
    "caliza": {"nombre": "Piedra caliza", "densidad_kg_m3": 2400, "fc_MPa": 40, "epoca": "historico"},
    "arenisca": {"nombre": "Arenisca", "densidad_kg_m3": 2300, "fc_MPa": 30, "epoca": "historico"},
    "ladrillo": {"nombre": "Fábrica de ladrillo", "densidad_kg_m3": 1800, "fc_MPa": 8, "epoca": "historico"},
    "yeso": {"nombre": "Yeso (mocárabe nazarí, no portante)", "densidad_kg_m3": 1200, "fc_MPa": 5,
             "epoca": "historico"},
    "piedra_cnc": {"nombre": "Piedra natural mecanizada CNC", "densidad_kg_m3": 2500, "fc_MPa": 60,
                   "epoca": "contemporaneo"},
    "hormigon_3dcp": {"nombre": "Hormigón impreso 3D (3DCP)", "densidad_kg_m3": 2250, "fc_MPa": 35,
                      "epoca": "contemporaneo"},
}


def densidad(material):
    return MATERIALES[material]["densidad_kg_m3"]
