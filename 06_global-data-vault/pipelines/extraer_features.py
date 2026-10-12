"""Paso 3 — extrae features por sitio y por elemento y genera el dataset ML.

Salidas
  <caso>/data/features.json                 features del caso (regenerado)
  datasets/elementos_consolidados.csv        tabla larga de elementos (5 casos)
  datasets/features_sitios.csv|json          una fila por caso
  datasets/ml/X_features.csv                 matriz de features continuas
  datasets/ml/X_features_zscore.csv          matriz estandarizada
  datasets/ml/y_etiquetas.csv                etiquetas categóricas + multietiqueta
  datasets/ml/feature_metadata.json          unidades, normalización, descripción
  datasets/ml/aumentado_sintetico.csv        variantes por propagación de incertidumbre
"""

import numpy as np

from archimorph import features, io_utils, paths

N_SINTETICOS = 50
SEMILLA = 2026


def main():
    materials = features.load_materials()
    site_feats, elem_rows = [], []
    for sid in paths.SITES:
        elems, desc = features.load_site(sid)
        sf = features.site_features(sid, elems, desc, materials)
        io_utils.write_json(paths.features_path(sid), sf)
        site_feats.append(sf)
        elem_rows.extend(features.element_rows(sid, elems, materials))

    io_utils.write_csv(paths.DATASETS / "elementos_consolidados.csv", elem_rows)
    io_utils.write_json(paths.DATASETS / "features_sitios.json", site_feats)

    names = [n for n, _, _ in features.CONTINUAS]
    cats = [n for n, _ in features.CATEGORICAS]
    flat = []
    for sf in site_feats:
        row = {"sitio_id": sf["sitio_id"], **sf["features"], **sf["categoricas"]}
        flat.append(row)
    io_utils.write_csv(paths.DATASETS / "features_sitios.csv", flat, ["sitio_id"] + names + cats)

    X = np.array([[sf["features"][n] for n in names] for sf in site_feats])
    mu, sd = X.mean(axis=0), X.std(axis=0, ddof=1)
    sd_safe = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd_safe
    io_utils.write_csv(paths.ML / "X_features.csv",
                       [{"sitio_id": sf["sitio_id"], **dict(zip(names, x))} for sf, x in zip(site_feats, X)],
                       ["sitio_id"] + names)
    io_utils.write_csv(paths.ML / "X_features_zscore.csv",
                       [{"sitio_id": sf["sitio_id"], **dict(zip(names, z))} for sf, z in zip(site_feats, Z)],
                       ["sitio_id"] + names)

    all_tags = sorted({t for sf in site_feats for t in sf["etiquetas_morfologicas"]})
    y_rows = []
    for sf in site_feats:
        row = {"sitio_id": sf["sitio_id"], **sf["categoricas"]}
        row.update({f"tag_{t}": int(t in sf["etiquetas_morfologicas"]) for t in all_tags})
        y_rows.append(row)
    io_utils.write_csv(paths.ML / "y_etiquetas.csv", y_rows)

    meta = {
        "n_muestras_reales": len(site_feats),
        "features_continuas": [
            {"nombre": n, "unidad": u, "descripcion": d, "media": float(m_), "desv": float(s_),
             "min": float(X[:, i].min()), "max": float(X[:, i].max()), "constante": bool(s_ == 0)}
            for i, ((n, u, d), m_, s_) in enumerate(zip(features.CONTINUAS, mu, sd))
        ],
        "features_categoricas": [
            {"nombre": n, "descripcion": d,
             "valores": sorted({sf["categoricas"][n] for sf in site_feats})}
            for n, d in features.CATEGORICAS
        ],
        "etiquetas_multietiqueta": all_tags,
        "normalizacion": "z = (x - media) / desv  (desv muestral, ddof=1; constantes -> desv=1)",
        "aumentacion": {"n_por_sitio": N_SINTETICOS, "semilla": SEMILLA,
                        "metodo": "Perturbación log-normal de cada medida con su incertidumbre_rel declarada"},
    }
    io_utils.write_json(paths.ML / "feature_metadata.json", meta)

    rng = np.random.default_rng(SEMILLA)
    synth = []
    for sid in paths.SITES:
        elems, desc = features.load_site(sid)
        for i in range(N_SINTETICOS):
            pe, pd = features.perturb(elems, desc, rng)
            sf = features.site_features(sid, pe, pd, materials)
            synth.append({"sitio_id": sid, "variante": i, "sintetico": 1, **sf["features"],
                          **sf["categoricas"]})
    io_utils.write_csv(paths.ML / "aumentado_sintetico.csv", synth,
                       ["sitio_id", "variante", "sintetico"] + names + cats)
    print(f"  features: {len(site_feats)} sitios, {len(elem_rows)} elementos, "
          f"{len(synth)} variantes sintéticas")
    return site_feats


if __name__ == "__main__":
    main()
