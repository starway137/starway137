"""Pruebas unitarias y de integración del vault.  python3 -m unittest discover -s 06_global-data-vault/tests"""

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from archimorph import canons, features, geometry, paths, prior, stats, structural, validation  # noqa: E402
import construir_cad  # noqa: E402


class TestStats(unittest.TestCase):
    def test_t_distribution(self):
        self.assertAlmostEqual(stats.t_cdf(0, 7), 0.5, places=9)
        self.assertAlmostEqual(stats.t_ppf(0.975, 10), 2.228, places=3)
        self.assertAlmostEqual(stats.t_ppf(0.975, 1), 12.706, places=2)

    def test_ols_exact_line(self):
        fit = stats.ols([0, 1, 2, 3], [1, 3, 5, 7])
        self.assertAlmostEqual(fit["coeficientes"]["pendiente"]["valor"], 2.0)
        self.assertAlmostEqual(fit["r2"], 1.0)

    def test_power_law_recovers_exponent(self):
        rng = np.random.default_rng(0)
        x = np.logspace(0, 2, 30)
        y = 3 * x ** 0.6 * np.exp(rng.normal(0, 0.01, 30))
        fit = stats.fit_power_law(x, y)
        self.assertAlmostEqual(fit["b"], 0.6, places=2)
        self.assertLess(stats.test_slope(fit, 0.6, "b"), 1.0)

    def test_exponential_recovers_ratio(self):
        fit = stats.fit_exponential([0, 1, 2, 3], [100, 50, 25, 12.5])
        self.assertAlmostEqual(fit["r"], 0.5)


class TestCanonsStructural(unittest.TestCase):
    def test_nearest_canon(self):
        self.assertEqual(canons.nearest_canon(1.618)[0], "aurea")
        self.assertEqual(canons.nearest_canon(1 / 1.5)[0], "3:2")

    def test_chance_probability_monotone(self):
        p1, p2, p5 = (canons.chance_probability(t) for t in (0.01, 0.02, 0.05))
        self.assertTrue(0 < p1 < p2 < p5 < 1)

    def test_shape_factors(self):
        self.assertAlmostEqual(structural.spherical_cap_factor(2, 1), 2 / 3)
        self.assertAlmostEqual(structural.stepped_factor([(1, 1)]), 1.0)
        sigma = structural.base_stress_mpa(2000, 10, 1.0)
        self.assertAlmostEqual(structural.max_height_for(2000, 1.0, sigma, 1.0), 10)


class TestGeometry(unittest.TestCase):
    def test_volumes_and_export(self):
        m = geometry.Model("t", "T")
        p = m.prisma("p", 0, 0, 2, 3, h=4)
        c = m.casquete("c", 0, 0, 2, 1)
        self.assertAlmostEqual(p["volumen_m3"], 24)
        self.assertAlmostEqual(c["volumen_m3"], 2 / 3 * math.pi)
        m.marco("f", 0, 0, 10, 10, 1, h=2)
        m.torre_escalonada("s", 0, 0, 4, 8, niveles=4)
        with tempfile.TemporaryDirectory() as d:
            m.export(d, stem="t")
            for ext in ("planta.svg", "volumetria.obj", "geometria.json"):
                self.assertTrue((Path(d) / f"t_{ext}").stat().st_size > 0)


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = features.load_materials()

    def test_structure_and_schema(self):
        self.assertEqual(validation.validate_all(self.materials), [])

    def test_validation_detects_unknown_material(self):
        mats = copy.deepcopy(self.materials)
        del mats["arenisca_khmer"]
        errors = validation.validate_site("AW", mats)
        self.assertTrue(any("material desconocido" in e for e in errors))

    def test_features_complete_and_finite(self):
        for sid in paths.SITES:
            elems, desc = features.load_site(sid)
            sf = features.site_features(sid, elems, desc, self.materials)
            for name, _, _ in features.CONTINUAS:
                self.assertTrue(math.isfinite(sf["features"][name]), f"{sid}.{name}")
            self.assertGreater(sf["features"]["r2_anidamiento"], 0.9)

    def test_perturbation_reproducible(self):
        elems, desc = features.load_site("SN")
        a = features.perturb(elems, desc, np.random.default_rng(5))
        b = features.perturb(elems, desc, np.random.default_rng(5))
        self.assertEqual(a, b)


class TestReverseEngineering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = {}
        for sid in ("AW", "KL"):
            mod = construir_cad.load_model_module(sid)
            P = json.loads((paths.cad_dir(sid) / "parametros.json").read_text("utf-8"))
            cls.models[sid] = mod.build(P)

    def test_kailasa_subtractive_balance(self):
        c = self.models["KL"].computos
        self.assertLess(abs(c["test_KL_H1"]["desviacion_rel"]), 0.25)

    def test_angkor_volume_factor_matches_dataset(self):
        elems, _ = features.load_site("AW")
        f_csv = next(e["factor_volumen"] for e in elems if e["element_id"] == "AW-M01")
        f_cad = self.models["AW"].computos["factor_volumen_templo_montana"]
        self.assertLess(abs(f_cad - f_csv) / f_csv, 0.15)


class TestCoDesign(unittest.TestCase):
    def setUp(self):
        self.materials = features.load_materials()
        site_feats = []
        for sid in paths.SITES:
            elems, desc = features.load_site(sid)
            site_feats.append(features.site_features(sid, elems, desc, self.materials))
        allo = {"ajuste": {"coeficientes": {"log10_a": {"valor": 0.9}}, "b": 0.37, "sigma_resid": 0.25}}
        self.site_feats = site_feats
        self.prior = prior.build_prior(site_feats, {"M1_alometria_altura_base": allo})

    def test_samples_satisfy_hard_constraints(self):
        for seed in range(20):
            for mat in ("hormigon_c30", "tierra_compactada"):
                w = prior.parse_weights("AW=0.5,MD=0.5" if seed % 2 else "SN=1", self.prior["sitios"])
                d = prior.sample_design(self.prior, 20000, mat, self.materials, w, fs=3, tau=1.0, seed=seed)
                self.assertGreaterEqual(d["verificacion"]["factor_seguridad_resultante"], 3 - 1e-9)
                L = [lv["largo_m"] for lv in d["parametros"]["niveles"]]
                self.assertTrue(all(b < a for a, b in zip(L, L[1:])))
                self.assertGreaterEqual(d["parametros"]["masa_central"]["base_m"], 8 - 1e-9)

    def test_evaluation_affinity_sums_to_one(self):
        spec = json.loads(
            (paths.CODISENO / "ejemplos" / "proyecto_centro_cultural.json").read_text("utf-8"))
        res = prior.evaluate_design(spec, self.prior, self.site_feats, self.materials)
        self.assertAlmostEqual(sum(res["afinidad_morfologica"].values()), 1.0)


if __name__ == "__main__":
    unittest.main()
