"""Integración de las propuestas calculadas: plan, API y El Salao.  python -m unittest tests.test_calculadas

Sin el parámetro propuestas_calculadas el plan tiene que ser idéntico al de siempre (y al de
resultados/linea_base/, ver tests/test_obras.py). Con el parámetro, el JSON solo se agranda.
"""
import json
import unittest
from unittest import mock

import app as servidor
from src import fuente, osm
from src.etapas import plan_por_etapas
from src.supuestos import SUPUESTOS
from tests.test_obras import LINEA_BASE, diferencias
from tests.test_proyecto import barrio_de_prueba

CLAVES_NUEVAS_ETAPA = {"circulacion", "pares_viales", "pasos_por_demanda", "control_temporal"}
PASOS_NUEVOS = ["reorganizacion", "pasos-demanda", "control-temporal"]


def sin_pasos(plan):
    return {k: v for k, v in plan.items() if k != "pasos"}


def a_json(x):
    return json.loads(json.dumps(x))


class EnElBarrio(unittest.TestCase):
    def test_apagadas_el_plan_es_el_de_siempre(self):
        red, eje = barrio_de_prueba()
        self.assertEqual(plan_por_etapas(red, eje, propuestas_calculadas=False),
                         plan_por_etapas(red, eje, propuestas_calculadas=False, d0_m=250))

    def test_por_defecto_estan_activas(self):
        red, eje = barrio_de_prueba()
        self.assertIn("calculadas", plan_por_etapas(red, eje)["parametros"])

    def test_con_el_parametro_el_json_solo_se_agranda(self):
        red, eje = barrio_de_prueba()
        antes = a_json(plan_por_etapas(red, eje, propuestas_calculadas=False))
        ahora = a_json(plan_por_etapas(red, eje, propuestas_calculadas=True))
        self.assertEqual(diferencias(sin_pasos(antes), sin_pasos(ahora), sobras=True), [])
        ids = [p["id"] for p in ahora["pasos"]]
        self.assertEqual(ids, [p["id"] for p in antes["pasos"]][:-1] + PASOS_NUEVOS + ["limites"])
        for viejo, nuevo in zip(antes["pasos"][:-1], ahora["pasos"]):
            self.assertEqual(viejo, nuevo)
        self.assertTrue(CLAVES_NUEVAS_ETAPA <= set(ahora["etapas"][0]))
        self.assertEqual({s["nombre"] for s in ahora["supuestos"]}, set(SUPUESTOS))
        self.assertEqual(ahora["parametros"]["calculadas"]["d0_m"], SUPUESTOS["d0_m"].valor)
        self.assertEqual(set(ahora["resumen"]["calculadas"]), {"pares_viales_evaluados", "pares_viales_propuestos",
                                                               "pasos_por_demanda", "controles_temporales", "brecha_max_m"})

    def test_la_demanda_pone_dos_pasos_donde_la_regla_pone_uno(self):
        # Obra de 438 m: la regla da 1 paso (Carrera 1). Con la obra cerrando las dos carreras, los pares de
        # la Carrera 2 quedan con 220 m más; un segundo paso en la Carrera 2 baja el alargamiento a 0.
        red, eje = barrio_de_prueba()
        e = plan_por_etapas(red, eje, propuestas_calculadas=True)["etapas"][0]
        pd = e["pasos_por_demanda"]
        self.assertEqual((pd["numero"], pd["comparacion_regla_500m"]["numero"]), (2, 1))
        self.assertEqual({q["via"] for q in pd["pasos"]}, {"Carrera 1", "Carrera 2"})
        self.assertEqual(e["circulacion"]["peatones"]["con_pasos_por_demanda"]["desvio_positivo_m"], 0.0)
        self.assertGreater(e["circulacion"]["peatones"]["con_pasos_regla_500m"]["desvio_positivo_m"], 0.0)

    def test_etapas_sin_esquinas_suficientes_traen_las_claves_con_motivo(self):
        red, eje = barrio_de_prueba()
        plan = plan_por_etapas(red, eje, etapa_max_m=200, propuestas_calculadas=True)
        for e in plan["etapas"]:
            self.assertTrue(CLAVES_NUEVAS_ETAPA <= set(e))
            if e["circulacion"] is None:
                self.assertTrue(e["pares_viales"]["motivo"])

    def test_d0_elegido_queda_en_parametros_y_supuestos(self):
        red, eje = barrio_de_prueba()
        plan = plan_por_etapas(red, eje, propuestas_calculadas=True, d0_m=250)
        self.assertEqual(plan["parametros"]["calculadas"]["d0_m"], 250)
        self.assertEqual(next(s for s in plan["supuestos"] if s["nombre"] == "d0_m")["valor"], 250)


def plan_falso(*args, **kwargs):
    return dict(arroyo=dict(longitud_m=1, lineas=[]), obra=dict(longitud_m=1, lineas=[]), parametros={},
                semaforos_conocidos=None, resumen=dict(etapas=1), etapas=[], pasos=[])


EN_ZONA = [[[10.9187, -74.7981], [10.9190, -74.7975]]]


class ApiConMock(unittest.TestCase):
    def setUp(self):
        servidor.limpiar_cache()
        self.cliente = servidor.app.test_client()
        mock.patch.object(fuente, "red_para", return_value=(object(), "prueba")).start()
        self.calc = mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_falso).start()
        self.addCleanup(mock.patch.stopall)
        self.addCleanup(servidor.limpiar_cache)

    def post(self, cuerpo):
        return self.cliente.post("/api/plan", data=json.dumps(cuerpo), content_type="application/json")

    def test_por_defecto_se_calculan(self):
        self.assertEqual(self.post({"lineas": EN_ZONA}).status_code, 200)
        self.assertIs(self.calc.call_args.kwargs["propuestas_calculadas"], True)
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": False})
        self.assertIs(self.calc.call_args.kwargs["propuestas_calculadas"], False)

    def test_propuestas_calculadas_debe_ser_booleano(self):
        for v in ("sí", 1, None):
            with self.subTest(valor=v):
                r = self.post({"lineas": EN_ZONA, "propuestas_calculadas": v})
                self.assertEqual(r.status_code, 400)
                self.assertIn("propuestas_calculadas", r.get_json()["error"])

    def test_d0_se_acota_y_lo_invalido_da_400(self):
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": True, "d0_m": 50})
        self.assertEqual(self.calc.call_args.kwargs["d0_m"], 200)
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": True, "d0_m": 5000})
        self.assertEqual(self.calc.call_args.kwargs["d0_m"], 1000)
        self.assertEqual(self.post({"lineas": EN_ZONA, "d0_m": "lejos"}).status_code, 400)

    def test_cache(self):
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": False})
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": False, "d0_m": 300})  # apagadas, d0 no cambia nada
        self.assertEqual(self.calc.call_count, 1)
        self.post({"lineas": EN_ZONA})
        self.post({"lineas": EN_ZONA, "d0_m": 300})
        self.assertEqual(self.calc.call_count, 3)
        self.post({"lineas": EN_ZONA, "propuestas_calculadas": True, "d0_m": 300})
        self.assertEqual(self.calc.call_count, 3)


def sin_red(*args, **kwargs):
    raise AssertionError("La prueba intentó descargar de OpenStreetMap")


class ElSalao(unittest.TestCase):
    """El Salao por la API real con las propuestas calculadas (unos 10 s, una sola vez)."""

    @classmethod
    def setUpClass(cls):
        servidor.limpiar_cache()
        lineas = [[list(p) for p in l] for l in fuente.lineas_ejemplo()]
        with mock.patch.object(osm.urllib.request, "urlopen", side_effect=sin_red):
            r = servidor.app.test_client().post("/api/plan", data=json.dumps(dict(lineas=lineas, propuestas_calculadas=True)),
                                                content_type="application/json")
        cls.status, cls.plan = r.status_code, r.get_json()
        servidor.limpiar_cache()

    def test_responde_200_con_12_pasos(self):
        self.assertEqual(self.status, 200)
        self.assertEqual(len(self.plan["pasos"]), 12)
        self.assertEqual([p["id"] for p in self.plan["pasos"]][-4:], PASOS_NUEVOS + ["limites"])

    def test_las_cifras_de_siempre_no_cambian(self):
        base = json.loads((LINEA_BASE / "plan_etapas.json").read_text(encoding="utf-8"))
        self.assertEqual(diferencias(sin_pasos(base), sin_pasos(self.plan), sobras=True), [])
        for viejo, nuevo in zip(base["pasos"][:-1], self.plan["pasos"]):
            self.assertEqual(viejo["cifra"], nuevo["cifra"])

    def test_cada_etapa_trae_las_cuatro_propuestas(self):
        for e in self.plan["etapas"]:
            with self.subTest(etapa=e["numero"]):
                self.assertTrue(CLAVES_NUEVAS_ETAPA <= set(e))
                pv = e["pares_viales"]
                self.assertTrue(pv["pares"] or pv["motivo"], "sin pares debe decir por qué")
                cap = e["circulacion"]["capacidad"]
                # Cerrar calles nunca aumenta el corte mínimo.
                self.assertLessEqual(cap["obra"]["a_b"], cap["seco"]["a_b"])
                self.assertLessEqual(cap["obra"]["b_a"], cap["seco"]["b_a"])
                self.assertGreaterEqual(e["pasos_por_demanda"]["numero"], 1)
                for q in e["control_temporal"]["esquinas"]:
                    self.assertGreaterEqual(q["accesos"], SUPUESTOS["accesos_min"].valor)
                    self.assertIsNot(q["semaforo_existente"], True)

    def test_en_el_salao_no_hay_pares_viales_y_lo_dice(self):
        # Medido en los datos: ninguna pareja de calles locales de un solo sentido paralelas cerca del eje.
        self.assertEqual(self.plan["resumen"]["calculadas"]["pares_viales_evaluados"], 0)
        excluidas = {x["via"] for e in self.plan["etapas"] for x in e["pares_viales"]["excluidas"]}
        self.assertIn("Avenida Murillo", excluidas)          # dos calzadas: no se invierte

    def test_los_supuestos_vienen_completos(self):
        for s in self.plan["supuestos"]:
            self.assertEqual(set(s), {"nombre", "valor", "unidad", "rango", "justificacion", "fuente", "estado"})


if __name__ == "__main__":
    unittest.main()
