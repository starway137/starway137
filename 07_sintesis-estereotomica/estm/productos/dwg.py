"""DWG a partir de los DXF de producto.

El formato DWG es propietario: no hay escritor libre fiable en Python. Los
DXF que genera ESTM son R2018 (AC1032) y se abren sin conversión en
AutoCAD, BricsCAD, DraftSight, ZWCAD, SketchUp Pro y Revit. Para entregar
.dwg se convierten sin pérdida con un conversor externo, si está instalado:

    ODA File Converter (gratuito, Open Design Alliance)   ODAFileConverter
    LibreDWG (GPL)                                       dxf2dwg

Uso:  python3 -m estm.productos.dwg <carpeta_de_producto> [ACAD2018]
"""

import shutil
import subprocess
import sys
from pathlib import Path


def conversor():
    for exe in ("ODAFileConverter", "dxf2dwg"):
        if shutil.which(exe):
            return exe
    return None


def convertir(carpeta, version="ACAD2018"):
    carpeta = Path(carpeta)
    exe = conversor()
    if exe is None:
        return {"convertido": False, "motivo": "no hay ODAFileConverter ni dxf2dwg en el PATH",
                "dxf": sorted(p.name for p in carpeta.glob("*.dxf"))}
    if exe == "ODAFileConverter":
        destino = carpeta / "dwg"
        destino.mkdir(exist_ok=True)
        subprocess.run([exe, str(carpeta), str(destino), version, "DWG", "0", "1", "*.dxf"], check=True)
        hechos = sorted(p.name for p in destino.glob("*.dwg"))
    else:
        hechos = []
        for dxf in sorted(carpeta.glob("*.dxf")):
            subprocess.run([exe, "-y", "-o", str(dxf.with_suffix(".dwg")), str(dxf)], check=True)
            hechos.append(dxf.with_suffix(".dwg").name)
    return {"convertido": True, "conversor": exe, "dwg": hechos}


if __name__ == "__main__":
    print(convertir(sys.argv[1], *sys.argv[2:3]))
