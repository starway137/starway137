"""Paso 2 — ejecuta los modelos paramétricos de cada caso y consolida sus cómputos."""

import importlib.util

from archimorph import io_utils, paths


def load_model_module(sid):
    path = paths.cad_dir(sid) / "modelo_parametrico.py"
    spec = importlib.util.spec_from_file_location(f"modelo_{sid}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    resumen = {}
    for sid in paths.SITES:
        model = load_model_module(sid).main()
        resumen[sid] = {
            "modelo": model.nombre,
            "n_primitivas": len(model.prims),
            "computos": model.computos,
        }
        print(f"  {sid}: {len(model.prims)} primitivas -> {paths.SITES[sid]}/cad_parametric/salida/")
    io_utils.write_json(paths.DATASETS / "computos_cad.json", resumen)


if __name__ == "__main__":
    main()
