"""Pruebas de la verificación ciega y de los productos.
    python3 -m unittest discover -s 07_sintesis-estereotomica/tests"""

import csv
import json
import struct
import sys
import tempfile
import unittest
import xml.dom.minidom
import zipfile
from pathlib import Path
from unittest import mock

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import pipeline  # noqa: E402
import verificacion  # noqa: E402
from estm import ingesta, productos, seleccion  # noqa: E402
from estm import interpretacion as it  # noqa: E402
from estm.generadores import controles  # noqa: E402
from estm.productos import dwg  # noqa: E402

CAT = json.loads((RAIZ / "obras" / "catalogo.json").read_text(encoding="utf-8"))
NUEVAS = json.loads((RAIZ / "obras" / "nuevas.json").read_text(encoding="utf-8"))
REF = {e["id"]: e for e in CAT["obras"]}
NV = {e["id"]: e for e in NUEVAS["obras"]}
_CACHE = {}


def ciega(e, semilla=11):
    """(obra verdadera, grafo ciego, verdad, tipos verdaderos) de una ficha."""
    if e["id"] not in _CACHE:
        o = pipeline.construir(e)
        cg, verdad, _ = ingesta.ciega(ingesta.piezas_de_grafo(o.grafo), semilla=semilla)
        g = ingesta.grafo_desde_mallas(e["id"], cg)
        tipos = {n: o.grafo.nodos[verdad[n]]["tipo"] for n in g.piezas()}
        _CACHE[e["id"]] = (o, g, verdad, tipos)
    return _CACHE[e["id"]]


class TestSeleccion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sel = seleccion.Selector()
        cls.sel.calibrar({rid: (ciega(REF[rid])[1], REF[rid]["genoma"], REF[rid]["tradicion"])
                          for rid in ("CA-NER", "NA-MOC")})

    def test_controles_negativos_rechazados(self):
        for cid, (_, f) in controles.CONTROLES.items():
            cg, _, _ = ingesta.ciega(f(), semilla=3)
            ev = self.sel.evaluar(ingesta.grafo_desde_mallas(cid, cg))
            self.assertFalse(ev["seleccionada"], cid)
            self.assertTrue(ev["condiciones_fallidas"], cid)

    def test_obra_nueva_seleccionada(self):
        ev = self.sel.evaluar(ciega(NV["NV-TOL"])[1])
        self.assertTrue(ev["seleccionada"])
        self.assertEqual(ev["indices"]["simetria"], 8)

    def test_curvatura_esfera_cilindro_plano(self):
        u, v = np.meshgrid(np.linspace(-1, 1, 15), np.linspace(-1, 1, 15))
        u, v = u.ravel(), v.ravel()
        esfera = seleccion.curvatura(np.column_stack([u, v, -(u ** 2 + v ** 2) / 2]))
        cilindro = seleccion.curvatura(np.column_stack([u, v, -u ** 2 / 2]))
        plano = seleccion.curvatura(np.column_stack([u, v, 0.1 * u]))
        self.assertGreater(esfera["razon"], 0.95)
        self.assertLess(cilindro["razon"], 0.05)
        self.assertLess(plano["relativa"], 1e-6)

    def test_afinidad_y_novedad(self):
        a = self.sel.afinidad(NV["NV-TOL"]["genoma"])
        self.assertEqual(a["mas_cercana"], "CA-NER")
        self.assertFalse(self.sel.afinidad(REF["CA-NER"]["genoma"])["novedad"])
        self.assertIn("orden_radial", self.sel.afinidad(NV["NV-HEX"]["genoma"])["genes_nuevos"])


class TestInterpretacion(unittest.TestCase):
    def test_genoma_de_obra_nueva_desde_mallas(self):
        o, g, _, tipos = ciega(NV["NV-TOL"])
        gen, diag = it.inferir_genoma(g, tipos)
        err = it.errores_genoma(gen, NV["NV-TOL"]["genoma"])
        self.assertEqual((err["orden_radial"], err["salto_estrella"], err["terceletes"]), (1, 1, 1))
        self.assertLessEqual(err["d_despiece"], 1)
        self.assertLess(err["err_rel_espesor"], 0.15)
        self.assertLess(abs(diag["luz_m"] - NV["NV-TOL"]["luz"]) / NV["NV-TOL"]["luz"], 0.03)

    def test_grafo_geometrico(self):
        o, g, verdad, _ = ciega(NV["NV-TOL"])
        m = verificacion.metricas_grafo(g, verdad, ingesta.piezas_de_grafo(o.grafo), o.grafo)
        self.assertGreaterEqual(m["precision"], 0.85)
        self.assertGreaterEqual(m["exhaustividad"], 0.7)

    def test_pseudo_etiquetas_sin_verdad(self):
        o, g, _, tipos = ciega(NV["NV-TOL"])
        mc = it.marco(g)
        gen, diag = it.inferir_genoma(g, tipos, mc)
        e_r = dict(NV["NV-TOL"], id="NV-TOL-R", genoma=gen, luz=diag["luz_m"])
        o_r = pipeline.construir(e_r)
        pseudo, fid = verificacion.pseudo_etiquetas(g, mc, diag, o_r)
        self.assertGreater(verificacion.acierto(pseudo, tipos), 0.95)
        self.assertLess(fid["fidelidad"], 0.03)

    def test_clasificador_aprende_sin_olvidar_y_detecta_novedad(self):
        _, g, _, tipos = ciega(REF["CA-NER"])
        clf = it.Clasificador()
        items = it.descriptores(g)
        clf.aprender("CA-NER", "califal", items, tipos)
        pred = clf.predecir(items)
        self.assertGreater(verificacion.acierto(pred, tipos), 0.95)
        raro = [("x", np.full(len(it.NOMBRES_GEO), 9.0))]
        self.assertEqual(clf.predecir(raro)["x"], "desconocido")
        _, g2, _, tipos2 = ciega(NV["NV-TOL"])
        clf.aprender("NV-TOL", "califal", it.descriptores(g2), tipos2)
        self.assertEqual(clf.dicc.verificar_memoria(), 1.0)


class TestProductos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.obra = pipeline.analizar(pipeline.construir(NV["NV-TOL"]))
        cls.carpeta = Path(cls.tmp.name) / "NV-TOL"
        cls.archivos = productos.exportar(cls.obra, cls.carpeta, ifc=False)
        cls.n = len(cls.obra.grafo.piezas())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_dxf_una_polyface_por_pieza_con_xdata(self):
        import ezdxf
        doc = ezdxf.readfile(str(self.carpeta / "modelo_3d.dxf"))
        pf = [e for e in doc.modelspace() if e.dxftype() == "POLYLINE"]
        self.assertEqual(len(pf), self.n)
        self.assertEqual(doc.units, ezdxf.units.M)
        self.assertTrue(pf[0].has_xdata("ESTM"))
        for nombre in ("planta_replanteo", "montea", "plantillas"):
            self.assertGreater(len(ezdxf.readfile(str(self.carpeta / f"{nombre}.dxf")).modelspace()), 10)

    def test_glb_dae_obj_stl(self):
        b = (self.carpeta / "modelo.glb").read_bytes()
        magia, version, total = struct.unpack("<4sII", b[:12])
        self.assertEqual((magia, version, total), (b"glTF", 2, len(b)))
        (lj,) = struct.unpack("<I", b[12:16])
        self.assertEqual(len(json.loads(b[20:20 + lj])["nodes"]), self.n)
        dom = xml.dom.minidom.parse(str(self.carpeta / "modelo.dae"))
        self.assertEqual(len(dom.getElementsByTagName("node")), self.n)
        obj = (self.carpeta / "modelo.obj").read_text(encoding="utf-8")
        self.assertEqual(obj.count("\ng "), self.n)
        with zipfile.ZipFile(self.carpeta / "piezas_stl.zip") as z:
            nombres = z.namelist()
            self.assertEqual(len(nombres), self.n)
            datos = z.read(nombres[0])
            (ntri,) = struct.unpack("<I", datos[80:84])
            self.assertEqual(len(datos), 84 + 50 * ntri)

    def test_tablas_visor_y_sketchup(self):
        with open(self.carpeta / "despiece.csv", encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), self.n)
        with open(self.carpeta / "replanteo.csv", encoding="utf-8") as f:
            ids = [r["id"] for r in csv.DictReader(f)]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(i.startswith("C") for i in ids) and any(i.startswith("K") for i in ids))
        html = (self.carpeta / "visor.html").read_text(encoding="utf-8")
        self.assertIn("cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js", html)
        self.assertNotIn("__DATOS__", html)
        rb = (self.carpeta / "importar_estm.rb").read_text(encoding="utf-8")
        self.assertIn("Sketchup.active_model", rb)
        datos = json.loads((self.carpeta / "piezas.json").read_text(encoding="utf-8"))
        self.assertEqual(len(datos["piezas"]), self.n)

    def test_dwg_sin_conversor_lo_dice(self):
        with mock.patch.object(dwg.shutil, "which", return_value=None):
            r = dwg.convertir(self.carpeta)
        self.assertFalse(r["convertido"])
        self.assertIn("modelo_3d.dxf", r["dxf"])


if __name__ == "__main__":
    unittest.main()
