"""Pruebas del generador de obra ilustrativa.  Ejecutar:  python -m unittest -v"""
import unittest

from herramientas.eje_de_calle import archivo_de_obra, eje_de_calle
from tests.test_proyecto import barrio_de_prueba


def largo(red, puntos):
    return sum(red.plano.dist(a, b) for a, b in zip(puntos, puntos[1:]))


class EjeDeCalle(unittest.TestCase):
    # La Calle Norte del barrio miniatura mide 2 x 109,6 = 219,2 m (n0 - n1 - n2).
    def test_corta_el_eje_en_el_largo_pedido_empezando_por_el_occidente(self):
        red, _ = barrio_de_prueba()
        puntos, logrado = eje_de_calle(red, "Calle Norte", 150)
        self.assertEqual(logrado, 150)
        self.assertAlmostEqual(largo(red, puntos), 150, delta=0.1)
        self.assertEqual(puntos[0], red.pos["n0"])               # n0 es el extremo más al occidente

    def test_si_la_calle_es_mas_corta_devuelve_toda(self):
        red, _ = barrio_de_prueba()
        puntos, logrado = eje_de_calle(red, "calle norte", 1000)   # sin distinguir mayúsculas
        self.assertAlmostEqual(logrado, 219.2, delta=0.3)
        self.assertEqual(puntos[-1], red.pos["n2"])

    def test_calle_inexistente_da_error_claro(self):
        red, _ = barrio_de_prueba()
        with self.assertRaises(ValueError) as e:
            eje_de_calle(red, "Calle Norte 9", 100)
        self.assertIn("Calle Norte 9", str(e.exception))

    def test_el_archivo_dice_que_no_es_una_obra_real(self):
        obra = archivo_de_obra("Calle 72", [(10.0, -74.0), (10.001, -74.0)])
        self.assertTrue(obra["ilustrativo"])
        self.assertIn("no es una obra real", obra["nombre"])
        self.assertEqual(obra["lineas"], [[[10.0, -74.0], [10.001, -74.0]]])


if __name__ == "__main__":
    unittest.main()
