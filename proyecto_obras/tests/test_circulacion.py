"""Propuestas calculadas: capacidad, pares viales y control temporal.  python -m unittest tests.test_circulacion

Todos los casos están resueltos a mano en los comentarios. Distancias a la latitud 10:
0,001 grados de longitud = 109,6 m y 0,001 grados de latitud = 110,6 m.
"""
import unittest

from src.circulacion import (calles_de_un_sentido, capacidad_entre_lados, detectar_pares, elegir_controles,
                             evaluar_par, vecinos_vehiculares)
from src.analisis import tablas
from src.demanda import pesos_gravedad
from src.geometria import Obra
from src.red import Red
from tests.test_proyecto import barrio_de_prueba


class CapacidadEnElBarrio(unittest.TestCase):
    """Barrio miniatura: Carrera 1 (a nivel) y Carrera 2 (puente), residenciales de doble sentido sin
    etiqueta lanes: 2 carriles en total (supuesto por clase), 1 por sentido."""

    def setUp(self):
        self.red, _ = barrio_de_prueba()
        self.sur, self.norte = ["s0", "s1", "s2"], ["n0", "n1", "n2"]
        self.c1 = [t.id for t in self.red.tramos if t.via == "Carrera 1"]
        self.c2 = [t.id for t in self.red.tramos if t.via == "Carrera 2"]

    def test_sin_obra_pasan_dos_carriles_en_cada_sentido(self):
        c = capacidad_entre_lados(self.red, self.sur, self.norte)
        self.assertEqual((c["a_b"], c["b_a"]), (2, 2))
        self.assertEqual(c["calles_a_b"], ["Carrera 1", "Carrera 2"])

    def test_con_la_obra_y_el_puente_abierto_queda_uno(self):
        c = capacidad_entre_lados(self.red, self.sur, self.norte, excluir=set(self.c1))
        self.assertEqual((c["a_b"], c["b_a"], c["calles_a_b"]), (1, 1, ["Carrera 2"]))

    def test_si_la_obra_cierra_tambien_el_puente_no_queda_ninguno(self):
        c = capacidad_entre_lados(self.red, self.sur, self.norte, excluir=set(self.c1 + self.c2))
        self.assertEqual((c["a_b"], c["b_a"]), (0, 0))

    def test_la_etiqueta_lanes_manda(self):
        # Con lanes=4 en la Carrera 2 (doble sentido): 2 carriles por sentido; total 1 + 2 = 3.
        red, _ = barrio_de_prueba()
        for t in red.tramos:
            if t.via == "Carrera 2":
                t.carriles_total, t.carriles_de_osm = 4, True
        c = capacidad_entre_lados(red, self.sur, self.norte)
        self.assertEqual((c["a_b"], c["b_a"]), (3, 3))


def barrio_de_dos_carreras():
    """Tres carreras de sur a norte, de 221,2 m (lat 10,000 a 10,002), separadas 109,6 m:

        a1 ------ b1 ------ c1      d1  e1    Calle Norte (doble sentido)
        ^         ^         |       ^   |
        A         B         C       Avenida Doble (dos calzadas a 22 m: d sube, e baja), aislada
        |         |         |       |   v
        a0 ------ b0 ------ c0      d0  e0    Calle Sur (doble sentido)

    Carrera A y Carrera B son de un solo sentido hacia el norte (residenciales, sin lanes: 2 carriles).
    Carrera C es de doble sentido (1 carril por sentido) y es la única que baja: la obra la cierra.
    La Avenida Doble no se conecta con las demás: solo sirve para comprobar que dos calzadas de una misma
    vía no se proponen como par vial.
    """
    lat = {0: 10.000, 1: 10.002}
    lon = {"a": -74.002, "b": -74.001, "c": -74.000, "d": -73.999, "e": -73.9988}
    nodos = {f"{k}{j}": (lat[j], x) for k, x in lon.items() for j in (0, 1)}
    res = {"highway": "residential"}
    vias = {
        "1": (["a0", "a1"], dict(res, name="Carrera A", oneway="yes")),
        "2": (["b0", "b1"], dict(res, name="Carrera B", oneway="yes")),
        "3": (["c0", "c1"], dict(res, name="Carrera C")),
        "4": (["a0", "b0", "c0"], dict(res, name="Calle Sur")),
        "5": (["a1", "b1", "c1"], dict(res, name="Calle Norte")),
        "6": (["d0", "d1"], dict(res, name="Avenida Doble", oneway="yes")),
        "7": (["e1", "e0"], dict(res, name="Avenida Doble", oneway="yes")),
    }
    red = Red(nodos, vias)
    # Eje corto de la obra que cruza la Carrera C a media altura.
    obra = Obra([[(10.001, -74.0005), (10.001, -73.9995)]], red.plano)
    return red, obra


class ParesViales(unittest.TestCase):
    def setUp(self):
        self.red, self.obra = barrio_de_dos_carreras()
        self.cerrada = {t.id for t in self.red.tramos if t.via == "Carrera C"}

    def test_detecta_el_par_y_excluye_las_dos_calzadas(self):
        usables, excluidas = calles_de_un_sentido(self.red, self.obra, 0, self.obra.longitud(), self.cerrada, radio=400)
        self.assertEqual([c["via"] for c in usables], ["Carrera A", "Carrera B"])
        self.assertEqual([e["via"] for e in excluidas], ["Avenida Doble"])
        self.assertIn("dos sentidos", excluidas[0]["motivo"])
        pares = detectar_pares(usables)
        self.assertEqual(len(pares), 1)
        self.assertEqual((pares[0]["relacion"], pares[0]["separacion_m"]), ("mismo sentido", 110))

    def test_evaluacion_de_todas_las_configuraciones_hecha_a_mano(self):
        # Lados: sur (a0, b0, c0) y norte (a1, b1, c1); 18 pares (9 de sur a norte y 9 de norte a sur).
        # Con la obra (sin la Carrera C) nadie puede bajar: 9 pares sin camino.
        # Capacidad (carriles del corte mínimo): sin obra, subir = A 2 + B 2 + C 1 = 5 y bajar = C 1.
        #   - sin cambio:          subir 4, bajar 0 (9 pares sin camino)
        #   - invertir A o B:      subir 2, bajar 2 (nadie sin camino)
        #   - las dos a doble:     subir 1 + 1 = 2, bajar 1 + 1 = 2, y todos los pares tienen su carrera
        #     directa: es la que menos alarga. Por ejemplo, de a1 a a0 sin obra hay que bajar por C:
        #     109,6 + 109,6 + 221,2 + 109,6 + 109,6 = 659,7 m; con A de doble sentido son 221,2 m.
        red = self.red
        sur, norte = ["a0", "b0", "c0"], ["a1", "b1", "c1"]
        origenes = sur + norte
        Vs = tablas(red.grafo_vehiculos(), origenes)
        pares_v = [(a, b) for a in sur for b in norte] + [(b, a) for a in sur for b in norte]
        pesos = pesos_gravedad(pares_v, Vs, None)
        self.assertAlmostEqual(Vs["a1"]["a0"], 659.7, delta=0.2)
        usables, _ = calles_de_un_sentido(red, self.obra, 0, self.obra.longitud(), self.cerrada, radio=400)
        par = detectar_pares(usables)[0]
        r = evaluar_par(red, par, self.cerrada, origenes, pares_v, pesos, Vs, sur, norte)
        alt = {a["configuracion"]: a for a in r["alternativas"]}
        self.assertEqual(alt["sin cambio"]["sin_camino"], 9)
        self.assertEqual((alt["sin cambio"]["capacidad_a_b"], alt["sin cambio"]["capacidad_b_a"]), (4, 0))
        for nombre in ("invertir Carrera A", "invertir Carrera B", "las dos a doble sentido"):
            self.assertEqual(alt[nombre]["sin_camino"], 0, nombre)
            self.assertEqual((alt[nombre]["capacidad_a_b"], alt[nombre]["capacidad_b_a"]), (2, 2), nombre)
        self.assertLess(alt["las dos a doble sentido"]["desvio_ponderado_m"], alt["invertir Carrera A"]["desvio_ponderado_m"])
        self.assertEqual(r["elegida"], "las dos a doble sentido")
        self.assertIn("devuelve el camino a 9 pares", r["motivo"])
        self.assertEqual({c["via"] for c in r["cambios"]}, {"Carrera A", "Carrera B"})

    def test_con_un_carril_no_se_propone_doble_sentido(self):
        for t in self.red.tramos:
            if t.via in ("Carrera A", "Carrera B"):
                t.carriles_total = 1
        usables, _ = calles_de_un_sentido(self.red, self.obra, 0, self.obra.longitud(), self.cerrada, radio=400)
        sur, norte = ["a0", "b0", "c0"], ["a1", "b1", "c1"]
        Vs = tablas(self.red.grafo_vehiculos(), sur + norte)
        pares_v = [(a, b) for a in sur for b in norte] + [(b, a) for a in sur for b in norte]
        r = evaluar_par(self.red, detectar_pares(usables)[0], self.cerrada, sur + norte, pares_v,
                        pesos_gravedad(pares_v, Vs, None), Vs, sur, norte)
        doble = next(a for a in r["alternativas"] if a["configuracion"] == "las dos a doble sentido")
        self.assertFalse(doble["evaluada"])
        self.assertTrue(r["elegida"].startswith("invertir"))     # invertir una sí devuelve el camino de bajada

    def test_sin_obra_no_se_propone_nada(self):
        # Sin la obra la Carrera C sigue abierta: invertir no devuelve caminos y alarga los de subida.
        sur, norte = ["a0", "b0", "c0"], ["a1", "b1", "c1"]
        Vs = tablas(self.red.grafo_vehiculos(), sur + norte)
        pares_v = [(a, b) for a in sur for b in norte] + [(b, a) for a in sur for b in norte]
        usables, _ = calles_de_un_sentido(self.red, self.obra, 0, self.obra.longitud(), set(), radio=400)
        r = evaluar_par(self.red, detectar_pares(usables)[0], set(), sur + norte, pares_v,
                        pesos_gravedad(pares_v, Vs, None), Vs, sur, norte)
        # Pasar las dos a doble sentido sí acorta (agrega caminos): se elige solo si baja el desvío 2 %.
        self.assertIn(r["elegida"], ("sin cambio", "las dos a doble sentido"))
        self.assertNotIn("invertir", r["elegida"])


def cruces_de_control():
    """Dos esquinas de 4 accesos, h y h2, a 109,6 m (calle Principal), cada una con una carrera que cruza:

              n            n2
              |            |
        w --- h ---------- h2 --- e2       Principal (secondary)
              |            |
              s            s2
    """
    nodos = {"h": (10.0, -74.001), "h2": (10.0, -74.000), "w": (10.0, -74.002), "e2": (10.0, -73.999),
             "n": (10.001, -74.001), "s": (9.999, -74.001), "n2": (10.001, -74.000), "s2": (9.999, -74.000)}
    vias = {"1": (["w", "h", "h2", "e2"], {"highway": "secondary", "name": "Principal"}),
            "2": (["s", "h", "n"], {"highway": "residential", "name": "Carrera 1"}),
            "3": (["s2", "h2", "n2"], {"highway": "residential", "name": "Carrera 2"})}
    return Red(nodos, vias)


class ControlTemporal(unittest.TestCase):
    def setUp(self):
        self.red = cruces_de_control()
        self.vecinos, self.clases = vecinos_vehiculares(self.red)
        # Carga ponderada (parte de la demanda desviada que pasa por cada esquina), total 1.
        self.carga = {"h": 0.6, "h2": 0.5, "w": 0.1, "e2": 0.1, "n": 0.1, "s": 0.1, "n2": 0.1, "s2": 0.1}

    def test_elige_la_mas_cargada_y_respeta_la_separacion(self):
        # Percentil 90 de 8 valores: el 8.º menor (ceil(0,9 * 8) = 8), o sea 0,6: solo h pasa el umbral.
        # (h2, con 0,5, tampoco podría: está a 109,6 m de h, menos que la separación de 150 m.)
        elegidas, con_sem = elegir_controles(self.red, self.carga, 1.0, self.vecinos, self.clases, {}, 40)
        self.assertEqual([e["esquina"] for e in elegidas], ["h"])
        self.assertEqual(elegidas[0]["accesos"], 4)
        self.assertTrue(elegidas[0]["cruza_via_mayor"])
        self.assertIs(elegidas[0]["semaforo_existente"], False)
        self.assertIn("verificar con conteos", elegidas[0]["motivo"])
        self.assertNotIn("requiere", elegidas[0]["motivo"])

    def test_una_esquina_con_semaforo_no_se_elige(self):
        carga = dict(self.carga, h2=0.6)        # empatan: las dos pasan el umbral
        elegidas, con_sem = elegir_controles(self.red, carga, 1.0, self.vecinos, self.clases,
                                             {"1": (10.0, -74.001)}, 40)    # semáforo justo en h
        self.assertEqual([e["esquina"] for e in elegidas], ["h2"])
        self.assertEqual(con_sem, 1)

    def test_un_codo_no_es_candidato(self):
        # w tiene un solo acceso: aunque sea la más cargada, no se elige.
        carga = dict(self.carga, w=0.9)
        elegidas, _ = elegir_controles(self.red, carga, 1.0, self.vecinos, self.clases, {}, 40)
        self.assertNotIn("w", [e["esquina"] for e in elegidas])

    def test_sin_datos_de_semaforos_lo_dice(self):
        elegidas, _ = elegir_controles(self.red, self.carga, 1.0, self.vecinos, self.clases, None, 40)
        self.assertIsNone(elegidas[0]["semaforo_existente"])
        self.assertIn("no se sabe si tiene semáforo", elegidas[0]["motivo"])


if __name__ == "__main__":
    unittest.main()
