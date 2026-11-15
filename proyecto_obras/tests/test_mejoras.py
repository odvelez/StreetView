"""Pruebas de las mejoras matemáticas: desvío fijo, voraz contra fuerza bruta y control de lados.

Los casos pequeños están resueltos a mano en los comentarios.  Ejecutar:  python -m unittest -v
"""
import unittest

from src.analisis import analizar, medir, tablas, voraz
from src.comparacion import comparar, fuerza_bruta
from src.control import control_de_lados, lados_de_zona
from src.grafo import Grafo, INF
from tests.test_proyecto import barrio_de_prueba


def escenario_dirigido():
    """Barrio miniatura con la Calle Norte en un solo sentido y la Carrera 1 bloqueada."""
    red, _ = barrio_de_prueba(norte_un_sentido=True)
    carrera1 = [t.id for t in red.tramos if t.via == "Carrera 1"]
    seco, g = red.grafo_vehiculos(), red.grafo_vehiculos(excluir=carrera1)
    origenes = sorted(g.adj)
    base = tablas(seco, origenes)
    pares = [(a, b) for a in origenes for b in origenes if a != b and b in base[a]]
    return g, origenes, base, pares


class DesvioFijo(unittest.TestCase):
    def test_sin_referencia_es_igual_al_desvio_medio(self):
        g, origenes, base, pares = escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        m = medir(F, R, base, pares)
        self.assertEqual(m.desvio_fijo_m, m.desvio_medio_m)

    def test_con_referencia_nunca_sube_al_agregar_una_medida(self):
        # Un conjunto fijo de pares solo puede mejorar cuando se agrega un arco.
        g, origenes, base, pares = escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        ref = {(a, b) for a, b in pares if F[a].get(b, INF) < INF}
        antes = medir(F, R, base, pares, (), ref)
        despues = medir(F, R, base, pares, [("n2", "n1", 109.6)], ref)
        self.assertLess(despues.sin_camino, antes.sin_camino)       # devuelve el camino a algunos pares
        self.assertLessEqual(despues.desvio_fijo_m, antes.desvio_fijo_m)

    def test_recuperados_en_el_informe(self):
        red, obra = barrio_de_prueba(norte_un_sentido=True)
        v = analizar(red, obra)["vehiculos"]
        self.assertEqual(v["recuperados"], v["lluvia"]["sin_camino"] - v["con_medida"]["sin_camino"])
        self.assertGreater(v["recuperados"], 0)


def grafo_complementario():
    """Dos arcos que solo sirven juntos.

        s -> a      b -> t         (con la obra no hay camino de s a t)

    Candidatos:  c0 = a -> m (1 m),  c1 = m -> b (1 m),  c2 = t -> s (1 m, no ayuda a s -> t).
    Solo la pareja {c0, c1} conecta s con t: s -> a -> m -> b -> t = 1 + 1 + 1 + 1 = 4 m.
    Ninguno de los dos mejora nada por separado, así que el voraz no elige ninguno.
    """
    g = Grafo(dirigido=True)
    g.agregar_arista("s", "a", 1)
    g.agregar_arista("b", "t", 1)
    seco = g.copia()
    seco.agregar_arista("a", "m", 1)
    seco.agregar_arista("m", "b", 1)
    origenes = ["s", "t"]
    candidatos = [({"id": 0}, [("a", "m", 1)]), ({"id": 1}, [("m", "b", 1)]), ({"id": 2}, [("t", "s", 1)])]
    objetivos = set(origenes) | {"a", "m", "b"}
    base = tablas(seco, origenes, objetivos)
    F = tablas(g, origenes, objetivos)
    R = tablas(g.invertido(), origenes, objetivos)
    return g, origenes, base, [("s", "t")], candidatos, F, R


class VorazContraFuerzaBruta(unittest.TestCase):
    def test_arcos_complementarios_el_voraz_no_llega_al_optimo(self):
        g, origenes, base, pares, cand, F, R = grafo_complementario()
        obj, i, j = fuerza_bruta(g, origenes, base, pares, cand, F, R)
        self.assertEqual((i, j), (0, 1))
        self.assertEqual(obj, (0, 0.0))          # s -> t mide 4 m, igual que en seco: desvío 0
        elegidos, _ = voraz(g, origenes, base, pares, cand, 2, F=F, R=R)
        self.assertEqual(elegidos, [])           # ninguno mejora por sí solo
        r = comparar(g, origenes, base, pares, cand, F, R)
        self.assertEqual(r["sin_camino_extra"], 1)
        self.assertFalse(r["coinciden"])

    def test_en_el_barrio_el_voraz_coincide_con_el_optimo(self):
        g, origenes, base, pares = escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        cand = [({"id": 0}, [("n2", "n1", 109.6)]), ({"id": 1}, [("n1", "n0", 109.6)]),
                ({"id": 2}, [("n1", "s1", 110.6)]), ({"id": 3}, [("s2", "s1", 109.6)])]
        r = comparar(g, origenes, base, pares, cand, F, R)
        self.assertLessEqual(r["optimo"]["objetivo"], r["voraz"]["objetivo"])   # el óptimo nunca pierde
        self.assertEqual(r["voraz"]["objetivo"], r["optimo"]["objetivo"])

    def test_fuerza_bruta_coincide_con_dijkstra_desde_cero(self):
        # El objetivo de la mejor pareja, calculado con tablas nuevas, da lo mismo.
        g, origenes, base, pares = escenario_dirigido()
        F, R = tablas(g, origenes), tablas(g.invertido(), origenes)
        cand = [({"id": 0}, [("n2", "n1", 109.6)]), ({"id": 1}, [("n1", "n0", 109.6)]),
                ({"id": 2}, [("n1", "s1", 110.6)])]
        obj, i, j = fuerza_bruta(g, origenes, base, pares, cand, F, R)
        g2 = g.copia()
        for k in (i, j):
            for x, y, w in cand[k][1]:
                g2.agregar_arista(x, y, w)
        exacto = medir(tablas(g2, origenes), tablas(g2.invertido(), origenes), base, pares).objetivo()
        self.assertEqual(obj, exacto)


class ControlDeLados(unittest.TestCase):
    def _barrio(self):
        red, obra = barrio_de_prueba()
        contexto = {}
        analizar(red, obra, contexto=contexto)
        return red, contexto

    def test_barrera_total_separa_los_dos_lados(self):
        # Sin la Carrera 1 ni el puente (Carrera 2), el norte y el sur quedan en componentes distintas.
        red, c = self._barrio()
        r = control_de_lados(red, c["contacto"], lados_de_zona(c["lados_todos"]), "barrera_total")
        self.assertEqual(r["esquinas"], 6)
        self.assertEqual(r["componentes"], 2)
        self.assertEqual(r["acuerdo_pct"], 100.0)

    def test_con_el_puente_abierto_los_lados_se_mezclan(self):
        # Con la obra hecha toda a la vez el puente sigue abierto: una sola componente con 3 esquinas de cada lado.
        red, c = self._barrio()
        r = control_de_lados(red, c["contacto"], lados_de_zona(c["lados_todos"]), "lluvia")
        self.assertEqual(r["componentes"], 1)
        self.assertEqual(r["componentes_mezcladas"], 1)
        self.assertEqual(r["acuerdo_pct"], 50.0)
        self.assertEqual(r["desacuerdos"], 3)


if __name__ == "__main__":
    unittest.main()
