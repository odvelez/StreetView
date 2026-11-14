"""Casos de prueba de resultado conocido.  Ejecutar:  python -m unittest -v"""
import unittest

from src.analisis import Evaluador, actualizar_tablas, analizar, medir, tablas
from src.geometria import Obra, Plano, orientar, se_cruzan
from src.red import Red
from src.grafo import (Grafo, bfs, centralidad_cercania, centralidad_grado, componentes_conexas,
                       dijkstra, intermediacion, reconstruir_camino)


def grafo(aristas):
    g = Grafo()
    for u, v, *p in aristas:
        g.agregar_arista(u, v, p[0] if p else 1.0)
    return g


class Algoritmos(unittest.TestCase):
    def setUp(self):
        self.estrella = grafo([("c", x) for x in "abde"])
        self.camino = grafo([(1, 2), (2, 3), (3, 4), (4, 5)])
        # Resuelto a mano: el camino minimo A-C-B-D-E-F mide 2+1+5+2+3 = 13.
        self.ponderado = grafo([("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5),
                                ("C", "D", 8), ("C", "E", 10), ("D", "E", 2), ("D", "F", 6),
                                ("E", "F", 3)])

    def test_bfs_camino(self):
        self.assertEqual(bfs(self.camino, 1), {1: 0, 2: 1, 3: 2, 4: 3, 5: 4})

    def test_dijkstra_hecho_a_mano(self):
        dist, pred = dijkstra(self.ponderado, "A")
        self.assertEqual(dist, {"A": 0, "C": 2, "B": 3, "D": 8, "E": 10, "F": 13})
        self.assertEqual(reconstruir_camino(pred, "F"), ["A", "C", "B", "D", "E", "F"])

    def test_bosque_multifuente(self):
        dist, pred = dijkstra(self.camino, [1, 5])
        self.assertEqual(dist, {1: 0, 5: 0, 2: 1, 4: 1, 3: 2})
        self.assertIsNone(pred[1])
        self.assertIsNone(pred[5])

    def test_componentes_al_cortar_puente(self):
        g = grafo([("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "e"), ("e", "f"), ("f", "d")])
        self.assertEqual(len(componentes_conexas(g)), 1)
        g.quitar_arista("c", "d")
        self.assertEqual(sorted(map(sorted, componentes_conexas(g))), [["a", "b", "c"], ["d", "e", "f"]])

    def test_centralidades_estrella(self):
        grado = centralidad_grado(self.estrella)
        cb = intermediacion(self.estrella)
        cc = centralidad_cercania(self.estrella)
        self.assertEqual(grado["c"], 1.0)
        self.assertAlmostEqual(cb["c"], 1.0)
        self.assertEqual(cb["a"], 0.0)
        self.assertAlmostEqual(cc["c"], 1.0)
        self.assertAlmostEqual(cc["a"], 4 / 7)

    def test_intermediacion_camino(self):
        cb = intermediacion(self.camino)
        self.assertAlmostEqual(cb[3], 4 / 6)
        self.assertAlmostEqual(cb[2], 3 / 6)
        self.assertEqual(cb[1], 0.0)

    def test_intermediacion_caminos_empatados(self):
        # Cuadrado: los caminos de a a c pasan mitad por b y mitad por d.
        g = grafo([("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])
        self.assertAlmostEqual(intermediacion(g)["b"], (1 / 2) / 3)

    def test_peso_negativo_rechazado(self):
        with self.assertRaises(ValueError):
            Grafo().agregar_arista("a", "b", -1)


    def test_dirigido_respeta_sentido(self):
        g = Grafo(dirigido=True)
        g.agregar_arista("a", "b", 1)
        g.agregar_arista("b", "c", 1)
        self.assertEqual(dijkstra(g, "a")[0], {"a": 0, "b": 1, "c": 2})
        self.assertEqual(dijkstra(g, "c")[0], {"c": 0})
        # En el grafo invertido, Dijkstra desde c da la distancia de cada nodo HACIA c.
        self.assertEqual(dijkstra(g.invertido(), "c")[0], {"c": 0, "b": 1, "a": 2})

    def test_dijkstra_fuente_aislada(self):
        # Una esquina que con la obra pierde todas sus calles ya no está en el grafo:
        # Dijkstra no debe fallar, solo se alcanza a sí misma (antes daba KeyError).
        dist, pred = dijkstra(self.ponderado, "Z")
        self.assertEqual(dist, {"Z": 0})
        self.assertEqual(reconstruir_camino(pred, "Z"), ["Z"])

    def test_parada_temprana_no_cambia_distancias(self):
        completo, _ = dijkstra(self.ponderado, "A")
        dist, pred = dijkstra(self.ponderado, "A", objetivos={"B", "D"})
        self.assertEqual(dist["B"], completo["B"])
        self.assertEqual(dist["D"], completo["D"])
        self.assertNotIn("F", dist)            # F está más lejos que D: no hizo falta cerrarlo
        self.assertEqual(reconstruir_camino(pred, "D"), ["A", "C", "B", "D"])
        self.assertEqual(reconstruir_camino(pred, "F"), [])
        corto, _ = dijkstra(self.ponderado, "A", limite=3)
        self.assertEqual(corto, {"A": 0, "C": 2, "B": 3})


class Geometria(unittest.TestCase):
    def test_cruce_de_segmentos(self):
        self.assertTrue(se_cruzan((0, 0), (2, 2), (0, 2), (2, 0)))
        self.assertFalse(se_cruzan((0, 0), (1, 0), (0, 1), (1, 1)))

    def test_lado_de_la_obra(self):
        plano = Plano(10.0)
        obra = Obra([[(10.0, -74.01), (10.0, -73.99)]], plano)   # eje de oeste a este
        d_n, lado_n, ext_n = obra.ubicar(plano.xy((10.001, -74.0)))
        d_s, lado_s, _ = obra.ubicar(plano.xy((9.999, -74.0)))
        self.assertAlmostEqual(d_n, 110.6, places=1)
        self.assertNotEqual(lado_n, lado_s)
        self.assertFalse(ext_n)
        self.assertTrue(obra.ubicar(plano.xy((10.0, -73.98)))[2])   # frente a un extremo

    def test_orientar_une_tramos(self):
        # Dos tramos dibujados en sentidos opuestos que se tocan: quedan como una sola línea.
        lineas = orientar([[(0, 0), (0, 1)], [(0, 2), (0, 1)]])
        self.assertEqual(lineas, [[(0, 0), (0, 1), (0, 2)]])


def barrio_de_prueba(norte_un_sentido=False, esquina_aislada=False):
    """Barrio miniatura, resuelto a mano.

        n0 ---- n1 ---- n2      Calle Norte (lat 10.0010)
               |        |
    ~~~~~~~~~~ | ~~~~~~ | ~~~  eje de la obra (lat 10.0005)
               |        |
        s0 ---- s1 ---- s2      Calle Sur   (lat 10.0000)

    Carrera 1 (s1-n1) cruza la obra a nivel: la obra la cierra.
    Carrera 2 (s2-n2) es un puente: sigue abierta.
    Distancias: vertical 0.001 grados = 110.6 m; horizontal 0.001 grados = 109.6 m.
    De s1 a n1: sin obra 110.6 m; con la obra s1-s2-n2-n1 = 109.6 + 110.6 + 109.6 = 329.8 m.

    Con esquina_aislada se agrega la Carrera 0 (s3-n3), que solo cruza la obra:
    con la obra, s3 y n3 se quedan sin ninguna calle.
    """
    lon = {0: -74.002, 1: -74.001, 2: -74.000}
    nodos = {}
    for i, x in lon.items():
        nodos[f"s{i}"] = (10.0, x)
        nodos[f"n{i}"] = (10.001, x)
    norte = {"highway": "residential", "name": "Calle Norte"}
    if norte_un_sentido:
        norte["oneway"] = "yes"          # solo de n0 hacia n2
    vias = {
        "1": (["s0", "s1", "s2"], {"highway": "residential", "name": "Calle Sur"}),
        "2": (["n0", "n1", "n2"], norte),
        "3": (["s1", "n1"], {"highway": "residential", "name": "Carrera 1"}),
        "4": (["s2", "n2"], {"highway": "residential", "name": "Carrera 2", "bridge": "yes"}),
    }
    if esquina_aislada:
        nodos["s3"], nodos["n3"] = (10.0, -74.0025), (10.001, -74.0025)
        vias["5"] = (["s3", "n3"], {"highway": "residential", "name": "Carrera 0"})
    return Red(nodos, vias), [[(10.0005, -74.003), (10.0005, -73.999)]]


class ModeloMiniatura(unittest.TestCase):
    def test_clasifica_cruce_y_puente(self):
        red, obra = barrio_de_prueba()
        r = analizar(red, obra)
        estados = {c["via"]: c["estado"] for c in r["contacto"]}
        self.assertEqual(estados, {"Carrera 1": "bloqueado", "Carrera 2": "puente"})

    def test_desvio_conocido_en_ruta_alterna(self):
        red, obra = barrio_de_prueba()
        r = analizar(red, obra)
        ruta = next(x for x in r["rutas"] if x["via"] == "Carrera 1")
        self.assertEqual(ruta["pie"]["seco_m"], 111)       # 110.6 redondeado
        self.assertEqual(ruta["pie"]["lluvia_m"], 330)     # 329.8 redondeado

    def test_puente_peatonal_devuelve_el_cruce(self):
        red, obra = barrio_de_prueba()
        r = analizar(red, obra)
        p = r["peatones"]
        self.assertGreater(p["lluvia"]["desvio_medio_m"], 0)
        self.assertEqual(p["propuestas"][0]["via"], "Carrera 1")
        self.assertAlmostEqual(p["con_medida"]["desvio_medio_m"], 0, places=6)

    def test_doble_sentido_resuelve_calle_de_un_sentido(self):
        # Con la Calle Norte en un solo sentido (n0 -> n2) y la Carrera 1 bloqueada,
        # un carro que cruza por el puente llega a n2 pero no puede devolverse a n1 ni a n0.
        red, obra = barrio_de_prueba(norte_un_sentido=True)
        r = analizar(red, obra)
        v = r["vehiculos"]
        self.assertGreater(v["lluvia"]["sin_camino"], 0)
        self.assertEqual(v["propuestas"][0]["via"], "Calle Norte")
        self.assertEqual(v["con_medida"]["sin_camino"], 0)

    def test_formula_rapida_coincide_con_dijkstra(self):
        # Agregar un arco con la fórmula d(a,x)+w+d(y,b) da lo mismo que recalcular Dijkstra.
        red, _ = barrio_de_prueba(norte_un_sentido=True)
        carrera1 = [t.id for t in red.tramos if t.via == "Carrera 1"]
        seco, g = red.grafo_vehiculos(), red.grafo_vehiculos(excluir=carrera1)
        origenes = sorted(g.adj)
        base = tablas(seco, origenes)
        pares = [(a, b) for a in origenes for b in origenes if a != b and b in base[a]]
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        rapido = medir(F, R, base, pares, [("n2", "n1", 109.6)])
        g2 = g.copia()
        g2.agregar_arista("n2", "n1", 109.6)
        completo = medir(tablas(g2, origenes), tablas(g2.invertido(), origenes), base, pares)
        self.assertLess(rapido.sin_camino, medir(F, R, base, pares).sin_camino)
        self.assertEqual(rapido, completo)

    def test_esquina_aislada_no_rompe_el_analisis(self):
        # Caso del error 500 de la web: una esquina de la muestra pierde todas sus calles.
        red, obra = barrio_de_prueba(esquina_aislada=True)
        r = analizar(red, obra)
        self.assertGreater(r["peatones"]["lluvia"]["sin_camino"], 0)
        self.assertGreater(r["vehiculos"]["lluvia"]["sin_camino"], 0)

    def _escenario_dirigido(self):
        red, _ = barrio_de_prueba(norte_un_sentido=True)
        carrera1 = [t.id for t in red.tramos if t.via == "Carrera 1"]
        seco, g = red.grafo_vehiculos(), red.grafo_vehiculos(excluir=carrera1)
        origenes = sorted(g.adj)
        base = tablas(seco, origenes)
        pares = [(a, b) for a in origenes for b in origenes if a != b and b in base[a]]
        return g, origenes, base, pares

    def test_evaluador_coincide_con_medir(self):
        # La evaluación incremental de candidatos da el mismo objetivo que recorrer todos los pares.
        g, origenes, base, pares = self._escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        ev = Evaluador(F, R, base, pares)
        for arcos in ([], [("n2", "n1", 109.6)], [("n1", "s1", 110.6)],
                      [("n2", "n1", 109.6), ("n1", "n0", 109.6)]):
            self.assertEqual(ev.objetivo(arcos), medir(F, R, base, pares, arcos).objetivo())

    def test_actualizar_tablas_coincide_con_dijkstra(self):
        # Agregar un arco actualizando las tablas da lo mismo que repetir Dijkstra desde cada origen.
        g, origenes, _, _ = self._escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        arcos = [("n2", "n1", 109.6)]
        F2, R2 = actualizar_tablas(g, F, R, arcos, set(origenes))
        g2 = g.copia()
        g2.agregar_arista("n2", "n1", 109.6)
        self.assertEqual(F2, tablas(g2, origenes))
        self.assertEqual(R2, tablas(g2.invertido(), origenes))


if __name__ == "__main__":
    unittest.main()
