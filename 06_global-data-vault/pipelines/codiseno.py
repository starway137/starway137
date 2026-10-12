"""Asistente de co-diseño: genera propuestas o evalúa proyectos con el prior.

Generar una propuesta a partir de una mezcla de lógicas históricas:
    python3 codiseno.py generar --area 12000 --material hormigon_c30 \
        --mezcla "AW=0.6,SN=0.4" --temperatura 0.3 --semilla 1 --nombre ejemplo

Evaluar (rediseño) un proyecto contemporáneo descrito en JSON:
    python3 codiseno.py evaluar --diseno ../codiseno/ejemplos/proyecto_centro_cultural.json

--temperatura 0 interpola de forma determinista entre los casos; 1 explora
con la dispersión completa observada en el corpus.
"""

import argparse
import json

from archimorph import features, io_utils, paths, prior


def generar(args):
    pr = io_utils.read_json(paths.PRIORS / "prior_generativo.json")
    materials = features.load_materials()
    w = prior.parse_weights(args.mezcla, pr["sitios"])
    design = prior.sample_design(pr, args.area, args.material, materials, w, fs=args.fs,
                                 tau=args.temperatura, seed=args.semilla, azimut=args.azimut,
                                 base_min=args.base_min)
    out = paths.CODISENO / "salidas"
    io_utils.write_json(out / f"{args.nombre}_diseno.json", design)
    prior.design_to_model(design, nombre=f"Propuesta {args.nombre}").export(out, stem=args.nombre)
    v = design["verificacion"]
    mc = design["parametros"]["masa_central"]
    print(f"  propuesta '{args.nombre}': dominante {design['sitio_dominante']}, "
          f"{len(design['parametros']['niveles'])} niveles, r={design['parametros']['razon_anidamiento_r']:.3f}, "
          f"masa {mc['forma']} H={mc['alto_m']:.1f} m, FS={v['factor_seguridad_resultante']:.1f}")
    for t in design["trazabilidad"]:
        print("    ·", t)
    return design


def evaluar(args):
    pr = io_utils.read_json(paths.PRIORS / "prior_generativo.json")
    site_feats = io_utils.read_json(paths.DATASETS / "features_sitios.json")
    with open(args.diseno, encoding="utf-8") as fh:
        spec = json.load(fh)
    res = prior.evaluate_design(spec, pr, site_feats, features.load_materials(), fs=args.fs)
    name = spec.get("nombre", "proyecto")
    io_utils.write_json(paths.CODISENO / "salidas" / f"evaluacion_{name}.json", res)
    afin = sorted(res["afinidad_morfologica"].items(), key=lambda kv: -kv[1])
    print(f"  evaluación '{name}': afinidad " + ", ".join(f"{k}={v:.2f}" for k, v in afin))
    for s in res["sugerencias"]:
        print("    ·", s)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generar")
    g.add_argument("--area", type=float, required=True, help="Área del recinto exterior (m²)")
    g.add_argument("--material", default="hormigon_c30")
    g.add_argument("--mezcla", default="", help='Pesos por sitio, p. ej. "AW=0.5,SN=0.5"')
    g.add_argument("--temperatura", type=float, default=0.3)
    g.add_argument("--semilla", type=int, default=0)
    g.add_argument("--fs", type=float, default=3.0, help="Factor de seguridad objetivo")
    g.add_argument("--azimut", type=float, default=None, help="Orientación del frente (°)")
    g.add_argument("--base-min", type=float, default=8.0, help="Lado mínimo del núcleo (m)")
    g.add_argument("--nombre", default="propuesta")
    e = sub.add_parser("evaluar")
    e.add_argument("--diseno", required=True)
    e.add_argument("--fs", type=float, default=3.0)
    args = ap.parse_args(argv)
    return generar(args) if args.cmd == "generar" else evaluar(args)


if __name__ == "__main__":
    main()
