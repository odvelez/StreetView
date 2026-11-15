"""Robustez de app.py (tarea B3 de Blanco).  Ejecutar:  python -m unittest tests.test_app_robustez -v

Sin descargas reales: el mapa y el plan se reemplazan con unittest.mock donde hace falta.
"""
import json
import time
import unittest
from unittest import mock

import app as servidor
from src import fuente, osm

# 600 m de la calle 72 (datos/ejemplos/obra_ilustrativa.json, recortado): zona guardada en datos/cache/cuadros.
EN_ZONA = [[[10.9187, -74.7981], [10.9190, -74.7975], [10.9195, -74.7965]]]
# Un punto en Bogotá: fuera del área metropolitana guardada.
FUERA = [[[4.6097, -74.0817], [4.6105, -74.0805]]]


def plan_falso(*args, **kwargs):
    """Plan mínimo con la forma del contrato; tarda 0,3 s para medir el caché."""
    time.sleep(0.3)
    return dict(arroyo=dict(longitud_m=1, lineas=[]), obra=dict(longitud_m=1, lineas=[]), parametros={},
                semaforos_conocidos=None, resumen=dict(etapas=1), etapas=[], pasos=[])


class Base(unittest.TestCase):
    def setUp(self):
        servidor.limpiar_cache()
        self.cliente = servidor.app.test_client()

    def post(self, cuerpo, ruta="/api/plan"):
        datos = cuerpo if isinstance(cuerpo, (bytes, str)) else json.dumps(cuerpo)
        return self.cliente.post(ruta, data=datos, content_type="application/json")

    def assertErrorJson(self, r, codigo, contiene=""):
        self.assertEqual(r.status_code, codigo, r.data[:200])
        self.assertTrue(r.is_json, f"no es JSON: {r.data[:120]!r}")
        self.assertIn("error", r.get_json())
        self.assertIn(contiene, r.get_json()["error"])
        self.assertNotIn("<", r.get_json()["error"])


class Validacion(Base):
    def test_cuerpo_que_no_es_json(self):
        for ruta in ("/api/plan", "/api/analizar"):
            for cuerpo in (b"hola", b"", b"[1, 2]", b'"texto"'):
                with self.subTest(ruta=ruta, cuerpo=cuerpo):
                    self.assertErrorJson(self.post(cuerpo, ruta), 400, "objeto JSON")

    def test_nan_e_infinito(self):
        for valor in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(valor=valor):
                r = self.post(f'{{"lineas": [[[{valor}, -74.8], [10.9, -74.8]]]}}')
                self.assertErrorJson(r, 400, "coordenadas válidas")
        r = self.post({"lineas": [[["nan", -74.8], [10.9, -74.8]]]})
        self.assertErrorJson(r, 400, "coordenadas válidas")

    def test_coordenadas_fuera_de_rango(self):
        for lineas in ([[[200, -74.8], [10.9, -74.8]]], [[[10.9, -274.8], [10.9, -74.8]]],
                       [[[10.9, -74.8], [-91, -74.8]]]):
            with self.subTest(lineas=lineas):
                self.assertErrorJson(self.post({"lineas": lineas}), 400, "fuera de rango")

    def test_lat_y_lon_al_reves_no_es_error_de_rango_pero_si_aviso(self):
        # [-74.8, 10.9] es una coordenada válida (en el océano Antártico): no se bloquea por rango,
        # pero la zona es otra y se avisa (aquí con el mapa simulado).
        with mock.patch.object(fuente, "red_para", return_value=(object(), "prueba")), \
                mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_falso):
            r = self.post({"lineas": [[[-74.8, 10.9], [-74.801, 10.9]]]})
        self.assertEqual(r.status_code, 200)
        self.assertIn("fuera del área metropolitana", r.get_json()["aviso_zona"])

    def test_mas_de_2000_puntos(self):
        linea = [[10.9 + i * 1e-6, -74.8] for i in range(2001)]
        self.assertErrorJson(self.post({"lineas": [linea]}), 400, "demasiados puntos")
        # Se suman todas las líneas.
        self.assertErrorJson(self.post({"lineas": [linea[:1000], linea[:1001]]}), 400, "demasiados puntos")

    def test_2000_puntos_si_se_aceptan(self):
        linea = [[10.9187 + i * 1e-7, -74.7981] for i in range(2000)]
        with mock.patch.object(fuente, "red_para", return_value=(object(), "prueba")), \
                mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_falso):
            self.assertEqual(self.post({"lineas": [linea]}).status_code, 200)

    def test_forma_mala(self):
        for lineas in ("abc", [1, 2], [[[10.9], [10.9, -74.8]]], [[["a", "b"], [10.9, -74.8]]]):
            with self.subTest(lineas=lineas):
                self.assertErrorJson(self.post({"lineas": lineas}), 400, "inválidos")

    def test_errores_http_de_la_api_en_json(self):
        # GET /api/plan cae en la ruta de archivos estáticos: 404, también en JSON.
        self.assertErrorJson(self.cliente.get("/api/plan"), 404)
        self.assertErrorJson(self.cliente.put("/api/plan"), 405)
        self.assertErrorJson(self.cliente.get("/api/no_existe"), 404)
        self.assertErrorJson(self.post(b"x" * (servidor.app.config["MAX_CONTENT_LENGTH"] + 1)), 413, "demasiado grande")
        # Fuera de /api/ se deja la página normal de Flask.
        r = self.cliente.get("/no_existe.html")
        self.assertEqual(r.status_code, 404)
        self.assertFalse(r.is_json)


class Zona(Base):
    def test_sin_aviso_en_zona_guardada(self):
        recuadro, _ = fuente.recuadro_de(EN_ZONA, 400)
        self.assertIsNone(servidor.aviso_de_zona(recuadro))

    def test_sin_aviso_en_el_salao(self):
        # El Salao está guardado como una descarga de Overpass (datos/cache/calles_*.json), no en cuadros.
        recuadro, _ = fuente.recuadro_de(fuente.lineas_ejemplo(), 400)
        with mock.patch.dict(fuente._redes, clear=True):
            self.assertIsNone(servidor.aviso_de_zona(recuadro))

    def test_aviso_fuera_del_area(self):
        recuadro, _ = fuente.recuadro_de(FUERA, 400)
        self.assertIn("fuera del área metropolitana", servidor.aviso_de_zona(recuadro))

    def test_aviso_dentro_del_area_sin_cuadros(self):
        recuadro, _ = fuente.recuadro_de(EN_ZONA, 400)
        with mock.patch.object(osm, "cuadros_que_cubren", return_value=None), \
                mock.patch.object(fuente, "mapa_local", return_value=None), \
                mock.patch.dict(fuente._redes, clear=True):
            self.assertIn("no está completa", servidor.aviso_de_zona(recuadro))

    def test_el_aviso_no_bloquea(self):
        with mock.patch.object(fuente, "red_para", return_value=(object(), "prueba")), \
                mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_falso):
            r = self.post({"lineas": FUERA})
        self.assertEqual(r.status_code, 200)
        self.assertIn("OpenStreetMap", r.get_json()["aviso_zona"])


class Overpass(Base):
    def test_falla_overpass_da_503_con_mensaje_claro(self):
        def sin_red(*a, **k):
            raise OSError("sin internet (simulado)")
        with mock.patch.dict(fuente._redes, clear=True), \
                mock.patch("urllib.request.urlopen", side_effect=sin_red), \
                mock.patch.object(osm.time, "sleep"), \
                mock.patch.object(osm, "CACHE", osm.CACHE / "_no_existe_prueba"):
            r = self.post({"lineas": FUERA})
        self.assertErrorJson(r, 503, "No se pudieron descargar las calles de OpenStreetMap")
        msg = r.get_json()["error"]
        self.assertIn("Revise la conexión", msg)
        self.assertNotIn("http", msg)           # sin direcciones ni detalles técnicos
        self.assertNotIn("simulado", msg)
        (osm.CACHE / "_no_existe_prueba").rmdir()


class Cache(Base):
    def setUp(self):
        super().setUp()
        self.red = mock.patch.object(fuente, "red_para", return_value=(object(), "prueba"))
        self.plan = mock.patch.object(servidor, "plan_por_etapas", side_effect=plan_falso)
        self.red.start()
        self.calc = self.plan.start()

    def tearDown(self):
        mock.patch.stopall()
        servidor.limpiar_cache()

    def test_segunda_llamada_identica_10_veces_mas_rapida(self):
        pedido = {"lineas": EN_ZONA, "etapa_max_m": 700}
        t = time.perf_counter()
        r1 = self.post(pedido)
        t1 = time.perf_counter() - t
        t = time.perf_counter()
        r2 = self.post(pedido)
        t2 = time.perf_counter() - t
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(self.calc.call_count, 1)
        self.assertFalse(r1.get_json()["en_cache"])
        self.assertTrue(r2.get_json()["en_cache"])
        self.assertLess(t2 * 10, t1, f"primera {t1:.3f} s, segunda {t2:.3f} s")
        a, b = r1.get_json(), r2.get_json()
        for k in ("tiempos", "en_cache", "aviso_zona"):
            a.pop(k), b.pop(k)
        self.assertEqual(a, b)

    def test_la_clave_incluye_todos_los_parametros(self):
        base = {"lineas": EN_ZONA, "radio": 400, "luz_max": 60, "etapa_max_m": 1000, "un_puente_cada_m": 500,
                "ancho_m": 10, "abiertos": [], "cerrados": [], "cerrar_puentes": True, "medicion": "lados"}
        cambios = {"lineas": [[[10.9187, -74.7981], [10.9190, -74.7976]]], "radio": 500, "luz_max": 80,
                   "etapa_max_m": 700, "un_puente_cada_m": 250, "ancho_m": 20, "abiertos": [1], "cerrados": [2],
                   "cerrar_puentes": False}
        self.post(base)
        self.assertEqual(self.calc.call_count, 1)
        for k, v in cambios.items():
            with self.subTest(parametro=k):
                antes = self.calc.call_count
                r = self.post(dict(base, **{k: v}))
                self.assertEqual(r.status_code, 200)
                self.assertEqual(self.calc.call_count, antes + 1, f"cambiar {k} no debe usar el caché")
        # Mismo pedido con valores por defecto implícitos = mismo plan.
        antes = self.calc.call_count
        self.post({"lineas": EN_ZONA})
        self.assertEqual(self.calc.call_count, antes)

    def test_guarda_solo_los_ultimos_16(self):
        pedidos = [{"lineas": [[[10.9187, -74.7981], [10.9190, -74.7975 + i * 1e-5]]]} for i in range(17)]
        for p in pedidos:
            self.post(p)
        self.assertEqual(len(servidor._cache_planes), servidor.MAX_CACHE)
        antes = self.calc.call_count
        self.post(pedidos[-1])                 # reciente: en caché
        self.assertEqual(self.calc.call_count, antes)
        self.post(pedidos[0])                  # el más viejo ya salió
        self.assertEqual(self.calc.call_count, antes + 1)

    def test_los_errores_no_se_guardan(self):
        self.post({"lineas": [[[200, 0], [10, 0]]]})
        self.assertEqual(len(servidor._cache_planes), 0)


if __name__ == "__main__":
    unittest.main()
