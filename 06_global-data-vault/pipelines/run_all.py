"""Ejecuta el pipeline completo de forma reproducible.

    validar -> construir_cad -> extraer_features -> modelos_estadisticos
            -> construir_prior -> informe -> ejemplos de co-diseño
"""

import construir_cad
import construir_prior
import codiseno
import extraer_features
import informe
import modelos_estadisticos
import validar
from archimorph import paths

EJEMPLOS = [
    ["generar", "--area", "12000", "--material", "hormigon_c30", "--mezcla", "AW=0.6,SN=0.4",
     "--temperatura", "0.3", "--semilla", "1", "--nombre", "ejemplo_aw_sn"],
    ["generar", "--area", "40000", "--material", "tierra_compactada", "--mezcla", "MD=0.7,KL=0.3",
     "--temperatura", "0.2", "--semilla", "3", "--azimut", "180", "--nombre", "ejemplo_md_kl"],
    ["evaluar", "--diseno", str(paths.CODISENO / "ejemplos" / "proyecto_centro_cultural.json")],
]


def main():
    print("[1/7] Validación");            validar.main()
    print("[2/7] Modelos paramétricos");  construir_cad.main()
    print("[3/7] Features");              extraer_features.main()
    print("[4/7] Modelos estadísticos");  modelos_estadisticos.main()
    print("[5/7] Prior generativo");      construir_prior.main()
    print("[6/7] Informe y gráficos");    informe.main()
    print("[7/7] Co-diseño (ejemplos)")
    for argv in EJEMPLOS:
        codiseno.main(argv)
    print("Pipeline completado.")


if __name__ == "__main__":
    main()
