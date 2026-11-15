"""Demanda de gravedad y voraz ponderado.  python -m unittest tests.test_demanda"""
import math
import unittest

from src.analisis import medir, tablas
from src.demanda import (EvaluadorPonderado, evaluar, fuerza_bruta_ponderada, objetivo, pesos_gravedad,
                         voraz_ponderado)
from src.grafo import Grafo
from src.supuestos import ESTADOS, SUPUESTOS, como_lista
from tests.test_proyecto import barrio_de_prueba


class Supuestos(unittest.TestCase):
    def test_cada_supuesto_esta_completo_y_su_valor_en_su_rango(self):
        for s in SUPUESTOS.values():
            with self.subTest(supuesto=s.nombre):
                self.assertTrue(s.justificacion and s.fuente and s.unidad is not None)
                self.assertIn(s.estado, ESTADOS)
                if isinstance(s.rango, tuple):
                    self.assertLessEqual(s.rango[0], s.valor)
                    self.assertLessEqual(s.valor, s.rango[1])

    def test_la_lista_para_el_json_usa_el_valor_pedido(self):
        lista = {d["nombre"]: d for d in como_lista({"d0_m": 250})}
        self.assertEqual(lista["d0_m"]["valor"], 250)
        self.assertEqual(lista["d0_m"]["rango"], [200, 1000])
        self.assertEqual(set(lista["d0_m"]), {"nombre", "valor", "unidad", "rango", "justificacion", "fuente", "estado"})


class Gravedad(unittest.TestCase):
    def test_dos_pares_hecho_a_mano(self):
        # Par 1: 100 m sin obra y 50 m de desvío. Par 2: 200 m sin obra y 10 m de desvío. d0 = 100 m.
        # Pesos: e^-1 y e^-2, normalizados: 1 / (1 + e^-1) = 0,731059 y 0,268941.
        # Desvío ponderado = 0,731059 * 50 + 0,268941 * 10 = 39,2424 m (la media simple sería 30 m).
        base = {"a": {"b": 100.0}, "c": {"d": 200.0}}
        F = {"a": {"b": 150.0}, "c": {"d": 210.0}}
        pares = [("a", "b"), ("c", "d")]
        pesos = pesos_gravedad(pares, base, d0_m=100)
        self.assertAlmostEqual(pesos[("a", "b")], 1 / (1 + math.exp(-1)), places=9)
        self.assertAlmostEqual(sum(pesos.values()), 1.0, places=12)
        self.assertAlmostEqual(evaluar(F, F, base, pares, pesos)["desvio_ponderado_m"], 39.2424, places=3)

    def test_con_d0_muy_grande_es_el_desvio_medio_de_siempre(self):
        red, _ = barrio_de_prueba()
        carrera1 = [t.id for t in red.tramos if t.via == "Carrera 1"]
        seco, obra = red.grafo_peatones(), red.grafo_peatones(excluir=carrera1)
        origenes = sorted(seco.adj)
        base, F = tablas(seco, origenes), tablas(obra, origenes)
        pares = [(a, b) for a in origenes for b in origenes if a < b]
        siempre = medir(F, F, base, pares).desvio_medio_m
        for d0 in (None, 1e12):
            pesos = pesos_gravedad(pares, base, d0_m=d0)
            self.assertAlmostEqual(evaluar(F, F, base, pares, pesos)["desvio_ponderado_m"], siempre, places=6)

    def test_desvio_relativo(self):
        # 100 m -> 160 m es un 60 % más largo: con tolerancia 0,5 cuenta; 200 -> 210 (5 %) no.
        base = {"a": {"b": 100.0}, "c": {"d": 200.0}}
        F = {"a": {"b": 160.0}, "c": {"d": 210.0}}
        pares = [("a", "b"), ("c", "d")]
        m = evaluar(F, F, base, pares, {("a", "b"): 0.25, ("c", "d"): 0.75}, tolerancia=0.5)
        self.assertAlmostEqual(m["demanda_desvio_relativo_pct"], 25.0)


def escalera(n=5, paso=100.0, rodeo=300.0):
    """Dos filas de n esquinas (lado norte N0..N4 y lado sur S0..S4), cada fila es una calle con cuadras
    de 100 m. Sin obra, cada i tiene un cruce Ni-Si de 30 m. Con la obra no queda ninguno: solo un rodeo
    de 300 m por el extremo (N4-S4). Los candidatos a paso peatonal son los cruces Ni-Si (30 m)."""
    seco, obra = Grafo(), Grafo()
    for g in (seco, obra):
        for i in range(n - 1):
            g.agregar_arista(f"N{i}", f"N{i+1}", paso)
            g.agregar_arista(f"S{i}", f"S{i+1}", paso)
        g.agregar_arista(f"N{n-1}", f"S{n-1}", rodeo)
    for i in range(n):
        seco.agregar_arista(f"N{i}", f"S{i}", 30.0)
    candidatos = [(dict(i=i, pos_m=i * paso), [(f"N{i}", f"S{i}", 30.0), (f"S{i}", f"N{i}", 30.0)]) for i in range(n)]
    norte, sur = [f"N{i}" for i in range(n)], [f"S{i}" for i in range(n)]
    return seco, obra, candidatos, norte, sur


class VorazPonderado(unittest.TestCase):
    def _caso(self, peso=None, d0=100):
        seco, obra, cand, norte, sur = escalera()
        origenes = norte + sur
        base = tablas(seco, origenes)
        pares = [(a, b) for a in norte for b in sur]
        pesos = pesos_gravedad(pares, base, d0_m=d0, peso=peso)
        F = tablas(obra, origenes)
        return obra, origenes, base, pares, pesos, cand, F

    def test_evaluador_coincide_con_evaluar(self):
        obra, origenes, base, pares, pesos, cand, F = self._caso()
        ev = EvaluadorPonderado(F, F, base, pares, pesos)
        for _, arcos in cand:
            self.assertEqual(ev.objetivo(arcos), objetivo(evaluar(F, F, base, pares, pesos, arcos)))

    def test_la_demanda_en_un_extremo_pone_el_paso_en_ese_extremo(self):
        # Las esquinas N0 y S0 pesan 20 veces más (por ejemplo, un colegio): el primer paso va en i = 0,
        # aunque el rodeo esté en el otro extremo (i = 4).
        obra, origenes, base, pares, pesos, cand, F = self._caso(peso=lambda n: 20.0 if n in ("N0", "S0") else 1.0)
        elegidos, _ = voraz_ponderado(obra, origenes, base, pares, pesos, cand, 1, F=F, R=F, mejora_min=0.02)
        self.assertEqual(elegidos[0][0]["i"], 0)

    def test_con_un_paso_el_voraz_es_optimo(self):
        # Con un solo paso el voraz prueba todos los candidatos: es la fuerza bruta.
        # Demanda pareja (sin d0): un paso en i = 0, 1, 2, 3, 4 deja 176,8 / 96,4 / 74,8 / 120 / 240 m.
        for peso in (None, lambda n: 20.0 if n in ("N0", "S0") else 1.0):
            obra, origenes, base, pares, pesos, cand, F = self._caso(peso=peso)
            elegidos, g = voraz_ponderado(obra, origenes, base, pares, pesos, cand, 1, F=F, R=F, mejora_min=0.0)
            Fg = tablas(g, origenes)
            optimo, _ = fuerza_bruta_ponderada(obra, origenes, base, pares, pesos, cand, 1)
            self.assertEqual(objetivo(evaluar(Fg, Fg, base, pares, pesos)), optimo)

    def test_con_dos_pasos_el_voraz_no_es_optimo_hecho_a_mano(self):
        # Contraejemplo del voraz, demanda pareja (sin d0), 25 pares Ni-Sj; sin obra d = 100|i-j| + 30.
        # Óptimo: pasos en 1 y 3. Un par tiene desvío 0 si un cruce (1, 3 o el rodeo en 4) queda entre i y j;
        # solo (0,0), (2,2) y (4,4) se desvían 200 m: 600 / 25 = 24,0 m.
        # Voraz: primero i = 2 (74,8 m, el mejor solo) y luego i = 0. Se desvían (1,1), (3,3), (3,4) y (4,3)
        # 200 m cada uno y (4,4) 270 m (rodeo de 300 m contra 30 m): 1070 / 25 = 42,8 m.
        # Con 3 pasos los dos coinciden (16,0 m). Por eso la salida dice que los pasos salen de un voraz.
        obra, origenes, base, pares, pesos, cand, F = self._caso(d0=None)
        elegidos, g = voraz_ponderado(obra, origenes, base, pares, pesos, cand, 2, F=F, R=F, mejora_min=0.0)
        self.assertEqual([e[0]["i"] for e in elegidos], [2, 0])
        Fg = tablas(g, origenes)
        self.assertEqual(objetivo(evaluar(Fg, Fg, base, pares, pesos)), (0, 42.8))
        self.assertEqual(fuerza_bruta_ponderada(obra, origenes, base, pares, pesos, cand, 2), ((0, 24.0), (1, 3)))
        elegidos, g = voraz_ponderado(obra, origenes, base, pares, pesos, cand, 3, F=F, R=F, mejora_min=0.0)
        Fg = tablas(g, origenes)
        self.assertEqual(objetivo(evaluar(Fg, Fg, base, pares, pesos)),
                         fuerza_bruta_ponderada(obra, origenes, base, pares, pesos, cand, 3)[0])

    def test_el_numero_de_pasos_sale_del_calculo(self):
        # Con k_max = 5 el voraz se detiene cuando el siguiente paso ya no baja el desvío al menos 2 %:
        # agrega algunos, pero no necesariamente los 5.
        obra, origenes, base, pares, pesos, cand, F = self._caso()
        elegidos, _ = voraz_ponderado(obra, origenes, base, pares, pesos, cand, 5, F=F, R=F, mejora_min=0.02)
        self.assertGreaterEqual(len(elegidos), 1)
        desvios = [m["desvio_ponderado_m"] for *_, m in elegidos]
        self.assertEqual(desvios, sorted(desvios, reverse=True))      # cada paso baja el desvío


if __name__ == "__main__":
    unittest.main()
