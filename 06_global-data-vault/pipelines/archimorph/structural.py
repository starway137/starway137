"""Estática de peso propio para masas de fábrica.

Para un sólido de huella A, altura H y volumen V = f·A·H, la tensión media de
compresión en la base debida al peso propio es

    sigma = rho · g · V / A = rho · g · f · H

donde f (factor_volumen) vale 1 para un prisma, 1/3 para pirámide o cono y
(3a² + h²) / (6a²) para un casquete esférico de radio basal a y flecha h.
Es una tensión media: las concentraciones locales (aristas, juntas, cimiento)
pueden multiplicarla, por lo que el factor de seguridad resultante describe
el régimen de trabajo, no la seguridad real del monumento (Heyman 1995).
"""

import math

G = 9.81


def footprint_area(forma, largo, ancho):
    if forma == "circulo":
        return math.pi / 4 * largo * ancho
    return largo * ancho


def equivalent_base(forma, largo, ancho):
    """Lado del cuadrado de igual área: medida de base comparable entre formas."""
    return math.sqrt(footprint_area(forma, largo, ancho))


def spherical_cap_factor(diameter, height):
    a = diameter / 2
    return (3 * a ** 2 + height ** 2) / (6 * a ** 2)


def stepped_factor(tiers):
    """Factor de volumen de una torre escalonada: tiers = [(lado_rel, alto_rel)]."""
    return sum(s ** 2 * h for s, h in tiers) / sum(h for _, h in tiers)


def base_stress_mpa(rho, height, factor):
    return rho * G * factor * height / 1e6


def safety_factor(fc_mpa, sigma_mpa):
    if sigma_mpa <= 0:
        return math.inf
    return fc_mpa / sigma_mpa


def max_height_for(rho, factor, fc_mpa, fs):
    """Altura máxima de una masa homotética para un factor de seguridad dado."""
    return fc_mpa * 1e6 / (fs * rho * G * factor)
