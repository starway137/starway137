"""Pruebas del módulo ESTM.   python3 -m unittest discover -s 07_sintesis-estereotomica/tests"""

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from estm import fabricacion, latente, patrones, tna  # noqa: E402
from estm.generadores import arco_dovelas, boveda_poligonal  # noqa: E402
from estm.generadores.arco import seccion_arco  # noqa: E402
from estm.geometria import hexaedro, prisma_entre  # noqa: E402
from estm.grafo import GrafoAtribuido  # noqa: E402
from estm.memoria import DiccionarioPatrones  # noqa: E402

CAT = json.loads((RAIZ / "obras" / "catalogo.json").read_text(encoding="utf-8"))
POR_ID = {e["id"]: e for e in CAT["obras"]}


def _boveda(oid, luz=None):
    e = POR_ID[oid]
    return boveda_poligonal(e["id"], e["nombre"], e["tradicion"], e["genoma"], luz or e["luz"], e["material"])


class TestHeyman(unittest.TestCase):
    def test_espesor_minimo_medio_punto(self):
        """Milankovitch (1907) / Heyman (1969): t/R = 0.1075 con juntas radiales."""
        R = 5.0
        r = tna.espesor_minimo(seccion_arco(R, 0.0, 30, 1.0, 1.0, 2400), 1.0, t_bajo=0.05)
        t = r["t_min_m"]
        self.assertAlmostEqual(t / (R + t / 2), 0.1075, delta=0.004)

    def test_seguridad_es_independiente_de_la_densidad(self):
        a = tna.espesor_minimo(seccion_arco(5.0, 0.5, 20, 1.0, 1.0, 1800), 0.6)
        b = tna.espesor_minimo(seccion_arco(5.0, 0.5, 20, 1.0, 1.0, 2600), 0.6)
        self.assertAlmostEqual(a["GSF"], b["GSF"], places=6)

    def test_carga_horizontal_nula_no_cambia_resultado(self):
        juntas, piezas = seccion_arco(5.0, 0.0, 20, 1.0, 1.0, 2400)(0.8)
        con = np.column_stack([piezas, np.zeros(len(piezas))])
        r1, r2 = tna.linea_empujes(juntas, piezas), tna.linea_empujes(juntas, con)
        self.assertEqual(r1["H_min_N"], r2["H_min_N"])

    def test_arco_demasiado_delgado_sin_solucion(self):
        juntas, piezas = seccion_arco(5.0, 0.0, 30, 1.0, 1.0, 2400)(0.3)
        self.assertFalse(tna.linea_empujes(juntas, piezas)["admisible"])


class TestTNA(unittest.TestCase):
    def test_equilibrio_horizontal_diagramas(self):
        for n in (4, 8):
            for dg in (tna.diagrama_arista(n, 5.0, 8), tna.diagrama_cupula(n, 5.0, 8)):
                q = dg["densidades"](dg["semillas"][0])
                self.assertTrue((q > 0).all())
                _, res = tna.fdm(dg["xy"], dg["aristas"], q, dg["apoyos"], np.ones(len(dg["xy"])))
                self.assertLess(res, 1e-9)

    def test_escala_de_la_red(self):
        dg = tna.diagrama_cupula(8, 5.0, 6)
        q = dg["densidades"](dg["semillas"][3])
        u1, _ = tna.fdm(dg["xy"], dg["aristas"], q, dg["apoyos"], np.ones(len(dg["xy"])))
        u2, _ = tna.fdm(dg["xy"], dg["aristas"], 2 * q, dg["apoyos"], np.ones(len(dg["xy"])))
        np.testing.assert_allclose(u2, u1 / 2)          # doble empuje -> red a la mitad de altura


class TestGeometriaGrafo(unittest.TestCase):
    def test_volumen_arco_analitico(self):
        o = arco_dovelas("t", "t", "t", 10.0, 0.0, 0.75, 15, profundidad=0.6)
        vol = sum(d["volumen_m3"] for d in o.grafo.nodos.values() if "volumen_m3" in d)
        exacto = math.pi / 2 * ((5.75) ** 2 - 5.0 ** 2) * 0.6
        self.assertAlmostEqual(vol / exacto, 1.0, delta=0.005)

    def test_contacto_junta_radial(self):
        o = arco_dovelas("t", "t", "t", 10.0, 0.0, 0.75, 15, profundidad=0.6)
        areas = [d["area_m2"] for d in o.grafo.aristas.values() if d["tipo"] == "junta_radial"]
        self.assertTrue(areas)
        for a in areas:
            self.assertAlmostEqual(a, 0.75 * 0.6, delta=1e-6)

    def test_hexaedro_orientado(self):
        q0 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], float)
        h = hexaedro(q0, q0 + [0, 0, 2])
        self.assertAlmostEqual(h.volumen_centroide()[0], 2.0)
        self.assertAlmostEqual(h.diedro_minimo(), 90.0, places=6)

    def test_tipologias_conexas_y_coherentes(self):
        g = _boveda("GO-CR4").grafo.resumen()
        self.assertEqual(g["componentes_conexas"], 1)
        self.assertEqual(g["por_tipo_nodo"]["jarja"], 4)
        e = _boveda("GO-EST").grafo.resumen()
        self.assertGreater(e["por_tipo_nodo"]["clave"], g["por_tipo_nodo"]["clave"])   # claves secundarias
        c = _boveda("CA-NER").grafo.resumen()
        self.assertGreaterEqual(c["por_tipo_nodo"]["clave"], 9)                          # cruces de la estrella {8/3}
        m = _boveda("NA-MOC").grafo.resumen()
        self.assertGreater(m["por_tipo_arista"].get("voladizo", 0), 0)
        self.assertNotIn("dovela_nervio", m["por_tipo_nodo"])

    def test_serializacion_grafo(self):
        o = arco_dovelas("t", "t", "t", 8.0, 0.5, 0.5, 9)
        g2 = GrafoAtribuido.de_dict(json.loads(json.dumps(o.grafo.a_dict())))
        self.assertEqual(g2.resumen(), o.grafo.resumen())


class TestMemoria(unittest.TestCase):
    def setUp(self):
        self.obras = [_boveda(i, luz=6.0) for i in ("GO-CR4", "CA-NER", "NA-MOC")]
        self.escalas = [0.5, 0.3, 0.25, 0.25, 0.25] + [0.35] * 8

    def test_sin_olvido_y_sin_perdida(self):
        d = DiccionarioPatrones(umbral=1.0, escalas=self.escalas)
        total = 0
        for o in self.obras:
            items = patrones.descriptores_piezas(o.grafo)
            total += len(items)
            r = d.ingerir(o.id, o.tradicion, items)
            self.assertEqual(r["retencion_memoria"], 1.0)
        self.assertEqual(d.n_items(), total)               # ninguna pieza se pierde
        self.assertEqual(d.verificar_memoria(), 1.0)

    def test_reproducible_desde_eventos(self):
        d = DiccionarioPatrones(umbral=1.0, escalas=self.escalas)
        for o in self.obras:
            d.ingerir(o.id, o.tradicion, patrones.descriptores_piezas(o.grafo))
        with tempfile.TemporaryDirectory() as tmp:
            d.guardar(Path(tmp) / "e.json", Path(tmp) / "ev.jsonl")
            r = DiccionarioPatrones.reproducir(Path(tmp) / "ev.jsonl", umbral=1.0, escalas=self.escalas)
        self.assertEqual(json.dumps(r.a_dict(), sort_keys=True), json.dumps(d.a_dict(), sort_keys=True))

    def test_tradicion_nueva_amplia_el_diccionario(self):
        d = DiccionarioPatrones(umbral=1.0, escalas=self.escalas)
        d.ingerir("GO", "gotica", patrones.descriptores_piezas(self.obras[0].grafo))
        antes = len(d.prototipos)
        d.ingerir("NA", "nazari", patrones.descriptores_piezas(self.obras[2].grafo))
        self.assertGreater(len(d.prototipos), antes)
        self.assertTrue(any(p["tipo"] == "celda_mocarabe" for p in d.prototipos))


class TestLatente(unittest.TestCase):
    def test_ida_y_vuelta(self):
        for e in CAT["obras"]:
            if e["tipo"] == "boveda":
                g = latente.decodificar(latente.codificar(e["genoma"]))
                for k, v in e["genoma"].items():
                    self.assertAlmostEqual(g[k], v, places=6, msg=f"{e['id']}.{k}")

    def test_slerp_extremos_y_norma(self):
        a, b = latente.codificar(POR_ID["GO-CR4"]["genoma"]), latente.codificar(POR_ID["NA-MOC"]["genoma"])
        np.testing.assert_allclose(latente.slerp(a, b, 0.0), a)
        np.testing.assert_allclose(latente.slerp(a, b, 1.0), b, atol=1e-12)
        m = latente.slerp(a, b, 0.5)
        self.assertAlmostEqual(np.linalg.norm(m), 0.5 * (np.linalg.norm(a) + np.linalg.norm(b)))
        self.assertGreater(np.linalg.norm(m), np.linalg.norm(0.5 * (a + b)))   # no colapsa al centro

    def test_hibridos_validos(self):
        for _, g in latente.serie(POR_ID["CA-NER"]["genoma"], POR_ID["GO-EST"]["genoma"], [0.3, 0.6]):
            self.assertEqual(int(g["orden_radial"]) % 2, 0)
            self.assertLessEqual(g["salto_estrella_rel"] * g["orden_radial"], g["orden_radial"] / 2)
            o = boveda_poligonal("h", "h", "h", g, 6.0)
            self.assertEqual(o.grafo.resumen()["componentes_conexas"], 1)


class TestFabricacion(unittest.TestCase):
    def test_sillar_cubico_cnc(self):
        q0 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], float)
        r = fabricacion.cnc(hexaedro(q0, q0 + [0, 0, 1]), 2400, "plemento")
        self.assertTrue(r["ok"], r)

    def test_cuna_aguda_falla(self):
        inf = np.array([[0, 0, 0], [2, 0, 0], [2, 0.6, 0]], float)
        sup = inf + [0, 0, 0.5]
        r = fabricacion.cnc(prisma_entre(inf, sup), 500, "clave")
        self.assertIn("diedro_agudo", r["fallos"])

    def test_losa_volada_3dcp_reorienta(self):
        q0 = np.array([[0, 0, 0], [1.2, 0, 0], [1.2, 1.2, 0], [0, 1.2, 0]], float)
        r = fabricacion.impresion_3d(hexaedro(q0, q0 + [0, 0, 0.15]))
        self.assertTrue(r["ok"], r)                            # se imprime apoyada en una cara
        self.assertLess(r["voladizo_deg"], 1.0)


class TestInteroperabilidad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obra = arco_dovelas("AR-T", "Arco de prueba", "prueba", 6.0, 0.5, 0.45, 9)
        cls.obra.analisis["estructura"] = {"admisible": True, "GSF": 1.5, "metodo": "arco"}
        fabricacion.evaluar_obra(cls.obra.grafo)
        fabricacion.secuencia_montaje(cls.obra.grafo)

    def test_ifc_ids_y_determinismo(self):
        try:
            import ifcopenshell
            import ifcopenshell.util.unit
            from estm.interop import ids, ifc
        except ImportError:
            self.skipTest("ifcopenshell / ifctester no instalados")
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a" / "x.ifc", Path(tmp) / "b" / "x.ifc"
            ifc.exportar([self.obra], a)
            ifc.exportar([self.obra], b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            f = ifcopenshell.open(str(a))
            self.assertEqual(f.schema_identifier, "IFC4X3_ADD2")
            self.assertEqual(ifcopenshell.util.unit.calculate_unit_scale(f), 1.0)
            self.assertEqual(len(f.by_type("IfcBuildingElementPart")), self.obra.grafo.resumen()["piezas"])
            ids.escribir(Path(tmp) / "r.ids")
            self.assertTrue(ids.validar(Path(tmp) / "r.ids", a)["cumple"])

    def test_carga_grasshopper_legible(self):
        from estm.interop import grasshopper
        sys.path.insert(0, str(RAIZ / "grasshopper"))
        import importar_estm
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "gh.json"
            grasshopper.escribir(self.obra, ruta)
            datos, piezas = importar_estm.leer(ruta, "dovela")
        self.assertEqual(len(piezas), self.obra.grafo.resumen()["por_tipo_nodo"]["dovela"])
        self.assertTrue(all(len(c) >= 3 for p in piezas for c in p["caras"]))

    def test_speckle_malla(self):
        from estm.interop import speckle
        obj = speckle.objeto_obra(self.obra)
        m = obj["@piezas"][0]
        self.assertEqual(m["speckle_type"], "Objects.Geometry.Mesh")
        self.assertEqual(len(m["vertices"]) % 3, 0)
        i, caras = 0, 0
        while i < len(m["faces"]):
            i += m["faces"][i] + 1
            caras += 1
        self.assertEqual(i, len(m["faces"]))


if __name__ == "__main__":
    unittest.main()
