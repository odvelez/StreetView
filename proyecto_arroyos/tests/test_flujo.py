"""Flujo máximo y corte mínimo (Edmonds–Karp), con casos resueltos a mano.  python -m unittest tests.test_flujo"""
import itertools
import random
import unittest

from src.grafo import flujo_maximo


def corte_minimo_por_fuerza_bruta(capacidades, fuentes, sumideros):
    """Capacidad mínima entre todos los conjuntos X que contienen las fuentes y no los sumideros."""
    nodos = sorted({u for u, _ in capacidades} | {v for _, v in capacidades} | set(fuentes) | set(sumideros))
    libres = [n for n in nodos if n not in fuentes and n not in sumideros]
    mejor = None
    for r in range(len(libres) + 1):
        for extra in itertools.combinations(libres, r):
            X = set(fuentes) | set(extra)
            c = sum(cap for (u, v), cap in capacidades.items() if u in X and v not in X)
            mejor = c if mejor is None else min(mejor, c)
    return mejor


class CasosAMano(unittest.TestCase):
    def test_cuello_de_botella_interno(self):
        # s -> a (10), s -> b (10), a -> b (5), a -> t (1), b -> t (1).
        # A t solo llegan 1 + 1 = 2: el corte mínimo son los dos arcos que entran a t.
        caps = {("s", "a"): 10, ("s", "b"): 10, ("a", "b"): 5, ("a", "t"): 1, ("b", "t"): 1}
        r = flujo_maximo(caps, ["s"], ["t"])
        self.assertEqual(r["valor"], 2)
        self.assertEqual(r["corte"], [("a", "t", 1), ("b", "t", 1)])

    def test_invertir_un_arco_cambia_el_flujo(self):
        # Con a -> b: s->a->t (1) y s->a->b->t (1) = 2; el corte es s -> a (capacidad 2).
        # Con el arco al revés (b -> a), de a solo se sale a t: flujo 1, corte a -> t.
        caps = {("s", "a"): 2, ("a", "t"): 1, ("b", "t"): 1}
        r = flujo_maximo({**caps, ("a", "b"): 1}, ["s"], ["t"])
        self.assertEqual(r["valor"], 2)
        self.assertEqual(r["corte"], [("s", "a", 2)])
        r = flujo_maximo({**caps, ("b", "a"): 1}, ["s"], ["t"])
        self.assertEqual(r["valor"], 1)
        self.assertEqual(r["corte"], [("a", "t", 1)])

    def test_varias_fuentes_y_calle_de_doble_sentido(self):
        # Fuentes s1 y s2, sumidero t. s1 -> t (1), s2 -> t (2) y una calle de doble sentido s1 <-> s2 (5
        # en cada sentido) que no agrega nada porque las dos ya son fuentes: flujo 1 + 2 = 3.
        caps = {("s1", "t"): 1, ("s2", "t"): 2, ("s1", "s2"): 5, ("s2", "s1"): 5}
        r = flujo_maximo(caps, ["s1", "s2"], ["t"])
        self.assertEqual(r["valor"], 3)
        self.assertEqual(sum(c for *_, c in r["corte"]), 3)

    def test_sin_camino_da_cero(self):
        # s -> a y t -> a: desde s se llega a a, pero nunca a t. Flujo 0 y corte vacío.
        r = flujo_maximo({("s", "a"): 3, ("t", "a"): 3}, ["s"], ["t"])
        self.assertEqual((r["valor"], r["corte"]), (0, []))
        self.assertEqual(r["alcanzables"], {"s", "a"})

    def test_fuente_y_sumidero_a_la_vez_es_error(self):
        with self.assertRaises(ValueError):
            flujo_maximo({("a", "b"): 1}, ["a"], ["a", "b"])


class ContraFuerzaBruta(unittest.TestCase):
    def test_flujo_igual_al_corte_minimo_en_grafos_al_azar(self):
        # Teorema de flujo máximo y corte mínimo: el valor del flujo es la capacidad del corte mínimo,
        # calculado aquí probando todos los conjuntos posibles (grafos de 6 nodos, 60 casos).
        azar = random.Random(4021)
        for caso in range(60):
            nodos = list(range(6))
            caps = {}
            for u, v in itertools.permutations(nodos, 2):
                if azar.random() < 0.35:
                    caps[(u, v)] = azar.randint(1, 4)
            fuentes, sumideros = [0], [5] if caso % 2 else [4, 5]
            r = flujo_maximo(caps, fuentes, sumideros)
            with self.subTest(caso=caso):
                self.assertEqual(r["valor"], corte_minimo_por_fuerza_bruta(caps, fuentes, sumideros))
                self.assertEqual(r["valor"], sum(c for *_, c in r["corte"]))


if __name__ == "__main__":
    unittest.main()
