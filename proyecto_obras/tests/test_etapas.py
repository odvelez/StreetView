"""Pruebas del plan de canalización por etapas.  Ejecutar:  python -m unittest -v"""
import unittest

from src.analisis import tablas, voraz
from src.etapas import _de_ellos_puentes, cortes, numero_de_etapas, plan_por_etapas, plural, puentes_por_longitud
from src.geometria import Obra, Plano
from src.grafo import Grafo
from tests.test_proyecto import barrio_de_prueba


class ReglasDeLongitud(unittest.TestCase):
    def test_un_puente_cada_500_m_minimo_uno(self):
        # 1000 m -> 2 (el ejemplo del grupo); tramos cortos llevan 1; se redondea al más cercano.
        self.assertEqual(puentes_por_longitud(1000), 2)
        self.assertEqual(puentes_por_longitud(400), 1)
        self.assertEqual(puentes_por_longitud(250), 1)      # 0,5 redondea a 0 y el mínimo es 1
        self.assertEqual(puentes_por_longitud(1200), 2)      # 2,4 -> 2
        self.assertEqual(puentes_por_longitud(1300), 3)      # 2,6 -> 3
        self.assertEqual(puentes_por_longitud(1000, un_puente_cada_m=250), 4)

    def test_numero_de_etapas_depende_del_largo(self):
        self.assertEqual(numero_de_etapas(500, 1000), 1)
        self.assertEqual(numero_de_etapas(1000, 1000), 1)
        self.assertEqual(numero_de_etapas(1001, 1000), 2)
        self.assertEqual(numero_de_etapas(2386, 1000), 3)    # El Salao
        self.assertEqual(numero_de_etapas(2386, 700), 4)


class CortesDeEtapas(unittest.TestCase):
    def test_un_solo_tramo_si_cabe(self):
        self.assertEqual(cortes(800, [100, 400], 1000), [0.0, 800])

    def test_dos_etapas_exactas(self):
        # 2000 m con etapas de hasta 1000 m: el único corte posible es el 1000.
        self.assertEqual(cortes(2000, [300, 1700], 1000), [0, 1000, 2000])

    def test_reparte_los_cruces_parejo(self):
        # Un cruce cada 25 m a lo largo de 1500 m: el corte debe caer cerca de la mitad (750).
        posiciones = [25 * k for k in range(1, 60)]
        c = cortes(1500, posiciones, 1000)
        self.assertEqual(len(c), 3)
        self.assertTrue(700 <= c[1] <= 800, c)

    def test_ninguna_etapa_pasa_del_maximo_y_cubren_todo(self):
        c = cortes(2386, [10, 600, 900, 1500, 2000, 2300], 700)
        self.assertEqual((c[0], c[-1]), (0, 2386))
        self.assertEqual(len(c), 5)                          # 4 etapas
        self.assertTrue(all(0 < b - a <= 700 for a, b in zip(c, c[1:])), c)


class PosicionEnElEje(unittest.TestCase):
    def test_posicion_a_lo_largo_de_un_eje_recto(self):
        # Eje recto de oeste a este. Un punto sobre el 25 % de su largo queda en el 25 %.
        plano = Plano(10.0)
        lineas = [[(10.0, -74.000), (10.0, -73.990)]]
        obra = Obra(lineas, plano)
        largo = obra.longitud()
        p = plano.xy((10.0003, -74.000 + 0.0025))
        self.assertAlmostEqual(obra.posicion(p), 0.25 * largo, places=3)
        self.assertAlmostEqual(obra.posicion(plano.xy((10.0, -73.980))), largo, places=3)   # más allá del extremo

    def test_posicion_con_dos_segmentos(self):
        plano = Plano(10.0)
        obra = Obra([[(10.0, -74.000), (10.0, -73.999), (10.001, -73.999)]], plano)
        primero = plano.dist((10.0, -74.000), (10.0, -73.999))
        p = plano.xy((10.0005, -73.9992))              # junto al segundo tramo, a la mitad
        self.assertAlmostEqual(obra.posicion(p), primero + plano.dist((10.0, -73.999), (10.0005, -73.999)), places=2)


class SeparacionEntreElegidos(unittest.TestCase):
    def _caso(self):
        # Dos pares aislados: s1 -> t1 y s2 -> t2 (100 m cada uno). Candidatos: c0 y c1 acortan el primero
        # (a 10 m y a 12 m) y c2 acorta el segundo (a 50 m).
        g = Grafo(dirigido=True)
        g.agregar_arista("s1", "t1", 100)
        g.agregar_arista("s2", "t2", 100)
        origenes = ["s1", "s2", "t1", "t2"]
        cand = [({"id": 0}, [("s1", "t1", 10)]), ({"id": 1}, [("s1", "t1", 12)]), ({"id": 2}, [("s2", "t2", 50)])]
        base = tablas(g, origenes)
        return g, origenes, base, [("s1", "t1"), ("s2", "t2")], cand

    def test_sin_restriccion_elige_c0_y_c2(self):
        g, origenes, base, pares, cand = self._caso()
        elegidos, _ = voraz(g, origenes, base, pares, cand, 2)
        self.assertEqual([i["id"] for i, _ in elegidos], [0, 2])

    def test_con_incompatibles_se_salta_el_candidato_prohibido(self):
        # c2 queda prohibido tras elegir c0; c1 ya no mejora nada: solo se elige uno.
        g, origenes, base, pares, cand = self._caso()
        elegidos, _ = voraz(g, origenes, base, pares, cand, 2,
                            incompatibles=lambda elegido, c: elegido["id"] == 0 and c["id"] == 2)
        self.assertEqual([i["id"] for i, _ in elegidos], [0])


class PlanEnElBarrio(unittest.TestCase):
    """Barrio miniatura: obra de unos 438 m con la Carrera 1 (a nivel) y la Carrera 2 (puente)."""

    def test_una_etapa_cierra_los_dos_cruces_y_pone_un_puente(self):
        red, lineas = barrio_de_prueba()
        plan = plan_por_etapas(red, lineas)                 # etapa_max_m = 1000: una sola etapa
        self.assertEqual(len(plan["etapas"]), 1)
        e = plan["etapas"][0]
        self.assertEqual(e["cruces_cerrados"], 2)
        self.assertEqual(e["puentes_existentes_cerrados"], 1)     # la obra interviene el puente existente
        self.assertEqual(e["puentes_necesarios"], 1)               # 438 m -> 1 puente
        self.assertEqual(e["peatones"]["obra"]["sin_camino"], 9)   # 3 x 3 pares sin ningún camino
        self.assertEqual(len(e["peatones"]["puentes"]), 1)
        self.assertLess(e["peatones"]["con_puentes"]["sin_camino"], 9)
        self.assertEqual(e["vehiculos"]["medidas"], [])            # no hay calles de un solo sentido
        self.assertEqual(plan["resumen"]["puentes_peatonales"], 1)

    def test_si_el_puente_existente_se_mantiene_nadie_queda_aislado(self):
        # Con la Carrera 2 (puente) abierta, solo se cierra la Carrera 1: hay desvío pero ningún par sin camino.
        red, lineas = barrio_de_prueba()
        e = plan_por_etapas(red, lineas, cerrar_puentes=False)["etapas"][0]
        self.assertEqual(e["cruces_cerrados"], 1)
        self.assertEqual(e["puentes_existentes_cerrados"], 0)
        self.assertEqual(e["peatones"]["obra"]["sin_camino"], 0)
        self.assertGreater(e["peatones"]["obra"]["desvio_medio_m"], 0)

    def test_varias_etapas_cubren_toda_la_obra_sin_repetir_cierres(self):
        red, lineas = barrio_de_prueba()
        plan = plan_por_etapas(red, lineas, etapa_max_m=200)       # 438 m / 200 m -> 3 etapas
        et = plan["etapas"]
        self.assertEqual(len(et), 3)
        self.assertEqual(et[0]["inicio_m"], 0)
        for a, b in zip(et, et[1:]):
            self.assertEqual(a["fin_m"], b["inicio_m"])
        self.assertAlmostEqual(et[-1]["fin_m"], plan["obra"]["longitud_m"], delta=1)
        cerrados = [i for e in et for i in e["tramos_cerrados"]]
        self.assertEqual(len(cerrados), len(set(cerrados)))        # ningún tramo se cierra en dos etapas
        self.assertEqual(len(cerrados), 2)                          # y los dos cruces se cierran en alguna

    def test_pasos_para_mostrar_de_a_uno(self):
        red, lineas = barrio_de_prueba()
        plan = plan_por_etapas(red, lineas, etapa_max_m=200)
        ids = [p["id"] for p in plan["pasos"]]
        self.assertEqual(ids[0], "etapas")
        self.assertEqual(ids[-1], "limites")
        self.assertEqual([i for i in ids if i.startswith("etapa-")], ["etapa-1", "etapa-2", "etapa-3"])
        self.assertEqual(plan["pasos"][0]["cifra"], "3")
        for p in plan["pasos"]:
            self.assertTrue({"id", "titulo", "cifra", "unidad", "detalle", "capas", "foco"} <= set(p))
            self.assertEqual(len(p["foco"]), 2)


class Textos(unittest.TestCase):
    def test_plurales(self):
        self.assertEqual(plural(1, "etapa", "etapas"), "etapa")
        self.assertEqual(plural(3, "etapa", "etapas"), "etapas")
        self.assertEqual(plural(0, "paso", "pasos"), "pasos")
        self.assertEqual(_de_ellos_puentes(0), ".")
        self.assertEqual(_de_ellos_puentes(1), ", uno de ellos es un puente existente.")
        self.assertEqual(_de_ellos_puentes(3), ", 3 de ellos son puentes existentes.")

    def test_informe_sin_plurales_rotos(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "herramientas"))
        from plan_etapas import informe
        red, lineas = barrio_de_prueba()
        texto = informe("Prueba", plan_por_etapas(red, lineas, etapa_max_m=2000))
        self.assertIn(" en 1 etapa de hasta ", texto)
        self.assertNotIn("(s)", texto)
        self.assertNotIn("1 pasos", texto)
        self.assertNotIn("1 etapas", texto)


if __name__ == "__main__":
    unittest.main()
