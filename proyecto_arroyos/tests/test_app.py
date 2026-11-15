"""Pruebas de la API (app.py) y del caso resuelto a mano del documento.

Ejecutar:  python -m unittest tests.test_app -v

Sin red: toda descarga de OpenStreetMap se reemplaza con unittest.mock. El plan de El Salao se
calcula con las calles guardadas en datos/cache/ (tarda unos 10 s, una sola vez para toda la clase).
"""
import json
import unittest
from unittest import mock

import app as servidor
from src import fuente, osm
from src.analisis import medir, tablas, voraz
from src.grafo import Grafo

CLAVES_PLAN = {"obra", "parametros", "semaforos_conocidos", "resumen", "etapas", "pasos", "tiempos",
               "recuadro", "fuente", "aviso_zona", "en_cache"}
CLAVES_ETAPA = {"eje", "tramos_cerrados", "peatones", "vehiculos", "rutas", "carga"}


def sin_red(*args, **kwargs):
    raise AssertionError("La prueba intentó descargar de OpenStreetMap")


def plan_minimo(*args, **kwargs):
    """Plan con la forma del contrato, para las pruebas que no necesitan el cálculo real."""
    return dict(arroyo=dict(longitud_m=1, lineas=[]), obra=dict(longitud_m=1, lineas=[]),
                parametros=dict(kwargs), semaforos_conocidos=None, resumen=dict(etapas=1), etapas=[], pasos=[])


class Base(unittest.TestCase):
    def setUp(self):
        servidor.limpiar_cache()
        self.cliente = servidor.app.test_client()
        self.sin_red = mock.patch.object(osm.urllib.request, "urlopen", side_effect=sin_red)
        self.sin_red.start()
        self.addCleanup(self.sin_red.stop)

    def post(self, ruta, cuerpo):
        return self.cliente.post(ruta, data=json.dumps(cuerpo), content_type="application/json")


class Paginas(Base):
    def test_inicio_da_200_con_html_y_favicon(self):
        r = self.cliente.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.content_type)
        self.assertIn(b'rel="icon"', r.data)

    def test_ejemplo_trae_lineas(self):
        d = self.cliente.get("/api/ejemplo").get_json()
        self.assertTrue(d["lineas"])
        self.assertTrue(all(len(l) >= 2 for l in d["lineas"]))

    def test_ejemplo_de_obra_es_ilustrativo(self):
        d = self.cliente.get("/api/ejemplo_obra").get_json()
        self.assertTrue(d["ilustrativo"])
        self.assertTrue(d["lineas"])


class Errores(Base):
    def test_analizar_sin_lineas_da_400(self):
        r = self.post("/api/analizar", {"lineas": []})
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.get_json())

    def test_plan_sin_lineas_da_400(self):
        r = self.post("/api/plan", {"lineas": [[[10.9, -74.8]]]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("eje de la obra", r.get_json()["error"])

    def test_parametros_invalidos_dan_400(self):
        lineas = fuente.lineas_ejemplo()
        for extra in ({"etapa_max_m": "mucho"}, {"ancho_m": None}, {"cerrar_puentes": "sí"},
                      {"medicion": "afectados"}, {"abiertos": ["x"]}):
            with self.subTest(extra=extra):
                r = self.post("/api/plan", dict(lineas=[[list(p) for p in l] for l in lineas], **extra))
                self.assertEqual(r.status_code, 400)
                self.assertIn("error", r.get_json())

    def test_parametros_fuera_de_rango_se_acotan(self):
        # Fuera de rango no es error: se lleva al límite más cercano (etapa 300–2000 m, ancho 10–60 m).
        lineas = [[list(p) for p in l] for l in fuente.lineas_ejemplo()]
        with mock.patch.object(fuente, "red_para", return_value=(object(), "prueba")), \
                mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_minimo) as plan:
            r = self.post("/api/plan", {"lineas": lineas, "etapa_max_m": 50, "un_puente_cada_m": 5000,
                                        "ancho_m": 1})
        self.assertEqual(r.status_code, 200)
        kw = plan.call_args.kwargs
        self.assertEqual((kw["etapa_max_m"], kw["un_puente_cada_m"], kw["ancho_m"]), (300, 1000, 10))

    def test_zona_demasiado_grande_da_400(self):
        r = self.post("/api/plan", {"lineas": [[[10.80, -74.95], [11.10, -74.70]]]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("muy grande", r.get_json()["error"])

    def test_overpass_caido_da_503(self):
        with mock.patch.object(fuente, "red_para", side_effect=osm.ErrorDescarga("No se pudieron descargar\nmás")):
            r = self.post("/api/plan", {"lineas": [[[4.6097, -74.0817], [4.6105, -74.0805]]]})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json()["error"], "No se pudieron descargar")


class PlanDeElSalao(unittest.TestCase):
    """El plan real de El Salao por la API, con las calles guardadas y sin red."""

    @classmethod
    def setUpClass(cls):
        servidor.limpiar_cache()
        cliente = servidor.app.test_client()
        lineas = [[list(p) for p in l] for l in fuente.lineas_ejemplo()]
        cuerpo = json.dumps({"lineas": lineas})
        with mock.patch.object(osm.urllib.request, "urlopen", side_effect=sin_red):
            cls.r = cliente.post("/api/plan", data=cuerpo, content_type="application/json")
            cls.r2 = cliente.post("/api/plan", data=cuerpo, content_type="application/json")
        cls.d = cls.r.get_json()

    def test_responde_200_con_el_contrato(self):
        self.assertEqual(self.r.status_code, 200)
        self.assertTrue(CLAVES_PLAN <= set(self.d), CLAVES_PLAN - set(self.d))
        for e in self.d["etapas"]:
            self.assertTrue(CLAVES_ETAPA <= set(e), CLAVES_ETAPA - set(e))

    def test_cifras_de_resultados(self):
        # Las mismas de resultados/plan_etapas.txt.
        r = self.d["resumen"]
        self.assertEqual((r["etapas"], r["longitud_m"], r["puentes_peatonales"], r["cambios_de_sentido"],
                          r["rutas_alternas"], r["esquinas_de_control"], r["esquinas_sin_semaforo"]),
                         (3, 2386, 5, 3, 18, 15, 14))
        self.assertTrue(self.d["pasos"])

    def test_zona_guardada_sin_aviso_y_segunda_vez_del_cache(self):
        self.assertIsNone(self.d["aviso_zona"])
        self.assertFalse(self.d["en_cache"])
        self.assertTrue(self.r2.get_json()["en_cache"])
        self.assertEqual(self.r2.get_json()["resumen"], self.d["resumen"])


class CasoResueltoAMano(unittest.TestCase):
    """El caso de la sección 4 del documento (documento/main.tex), calculado a mano.

    Seis esquinas: A, B, C al norte de la obra y D, E, F al sur. Cuadras de 100 m a lo largo de cada
    lado (A-B, B-C, D-E, E-F) y tres cruces: A-D (80 m), B-E (50 m) y C-F (50 m). Grafo no dirigido
    (peatones). La etapa cierra A-D y B-E; solo queda C-F.

    Distancias (m) para los 9 pares norte-sur:
        par    sin obra  con obra  desvío   con paso B-E  desvío
        A-D       80       450      370         250         170   (A-B-C-F-E-D; con B-E: A-B-E-D)
        A-E      150       350      200         150           0
        A-F      250       250        0         250           0
        B-D      150       350      200         150           0
        B-E       50       250      200          50           0
        B-F      150       150        0         150           0
        C-D      250       250        0         250           0
        C-E      150       150        0         150           0
        C-F       50        50        0          50           0
    Desvío medio con la obra: (370 + 200 + 200 + 200) / 9 = 970 / 9 = 107,78 m.
    Con el paso B-E (w = 50), por la fórmula d'(a,b) = min(d(a,b), d(a,B) + 50 + d(E,b)):
        d'(A,D) = min(450, 100 + 50 + 100) = 250  ->  desvío medio 170 / 9 = 18,89 m.
    Con el paso A-D (w = 80): d'(A,E) = min(350, 0 + 80 + 100) = 180 y d'(B,D) = 180 (30 m de desvío
    cada uno) y d'(B,E) = min(250, 100 + 80 + 100) = 250 (200 m)  ->  260 / 9 = 28,89 m.
    El voraz elige B-E.
    """

    @staticmethod
    def grafo(aristas):
        g = Grafo()
        for u, v, w in aristas:
            g.agregar_arista(u, v, w)
        return g

    def setUp(self):
        calles = [("A", "B", 100), ("B", "C", 100), ("D", "E", 100), ("E", "F", 100), ("C", "F", 50)]
        self.seco = self.grafo(calles + [("A", "D", 80), ("B", "E", 50)])
        self.obra = self.grafo(calles)
        self.norte, self.sur = ["A", "B", "C"], ["D", "E", "F"]
        self.pares = [(a, b) for a in self.norte for b in self.sur]
        self.base = tablas(self.seco, self.norte)
        self.candidatos = [("paso B-E", [("B", "E", 50), ("E", "B", 50)]),
                           ("paso A-D", [("A", "D", 80), ("D", "A", 80)])]

    def test_distancias_sin_obra_y_con_obra(self):
        F = tablas(self.obra, self.norte)
        self.assertEqual([self.base[a][b] for a, b in self.pares], [80, 150, 250, 150, 50, 150, 250, 150, 50])
        self.assertEqual([F[a][b] for a, b in self.pares], [450, 350, 250, 350, 250, 150, 250, 150, 50])

    def test_desvio_medio_con_la_obra(self):
        F = tablas(self.obra, self.norte + self.sur)
        m = medir(F, F, self.base, self.pares)
        self.assertAlmostEqual(m.desvio_medio_m, 970 / 9)
        self.assertEqual(m.desvio_max_m, 370)

    def test_cada_candidato_con_la_formula(self):
        F = tablas(self.obra, self.norte + self.sur)
        con_be = medir(F, F, self.base, self.pares, self.candidatos[0][1])
        con_ad = medir(F, F, self.base, self.pares, self.candidatos[1][1])
        self.assertAlmostEqual(con_be.desvio_medio_m, 170 / 9)
        self.assertAlmostEqual(con_ad.desvio_medio_m, 260 / 9)

    def test_el_voraz_elige_b_e(self):
        elegidos, _ = voraz(self.obra, self.norte + self.sur, self.base, self.pares, self.candidatos, k=1)
        self.assertEqual(elegidos[0][0], "paso B-E")
        self.assertAlmostEqual(elegidos[0][1].desvio_medio_m, 170 / 9)

    def test_con_los_dos_pasos_no_queda_desvio(self):
        elegidos, _ = voraz(self.obra, self.norte + self.sur, self.base, self.pares, self.candidatos, k=2)
        self.assertEqual([e[0] for e in elegidos], ["paso B-E", "paso A-D"])
        self.assertAlmostEqual(elegidos[-1][1].desvio_medio_m, 0)


if __name__ == "__main__":
    unittest.main()
