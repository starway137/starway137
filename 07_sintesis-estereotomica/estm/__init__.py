"""estm — síntesis estereotómica computacional.

Pipeline para analizar, extraer y sintetizar patrones de obras históricas de
fábrica (estereotomía, bóvedas góticas, mocárabes) representadas como grafos
atribuidos relacionales G = (V, E):

    geometria     poliedros de pieza (volumen, centroide, caras de contacto)
    grafo         grafo atribuido relacional: piezas (V) y juntas (E)
    superficie    familias de perfil (medio punto -> apuntado) y superficies
                  de bóveda sobre planta poligonal (arista <-> cúpula)
    generadores   gramática paramétrica unificada (arcos, crucería, nervadas
                  califales, mocárabes e híbridos)
    tna           límite inferior de Heyman: líneas de empujes en arcos y
                  rebanadas, y Thrust Network Analysis por densidades de fuerza
    fabricacion   restricciones DfAM para piedra CNC y hormigón impreso (3DCP)
    patrones      firmas Weisfeiler-Lehman, espectro y descriptores de pieza
    memoria       diccionario de patrones con memoria episódica (aprendizaje
                  continuo sin olvido)
    latente       genoma de diseño e interpolación esférica (slerp)
    interop       IFC 4.3 + IDS, Speckle y Grasshopper (LOD 400)
"""

__version__ = "1.0.0"
