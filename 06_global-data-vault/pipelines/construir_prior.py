"""Paso 5 — construye el prior generativo y el conjunto de restricciones."""

from archimorph import io_utils, paths, prior


def main():
    site_feats = io_utils.read_json(paths.DATASETS / "features_sitios.json")
    modelos = io_utils.read_json(paths.MODELOS / "modelos_escala.json")
    pr = prior.build_prior(site_feats, modelos)
    io_utils.write_json(paths.PRIORS / "prior_generativo.json", pr)
    print(f"  prior: {len(pr['continuas'])} distribuciones, {len(pr['restricciones'])} restricciones")
    return pr


if __name__ == "__main__":
    main()
