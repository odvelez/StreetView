"""Pruebas del cambio de arroyos a obras viales (tareas R1 a R5).  Ejecutar:  python -m unittest -v

- Regresión: El Salao da los mismos números que resultados/linea_base/.
- `ancho_m`: una franja más ancha cierra lo mismo o más, nunca menos.
- Obra a lo largo de una calle del barrio miniatura, resuelta a mano.
- Ya no existe el alias `Arroyo`; `fuente.lineas_de_archivo` y `medicion` inválida.
"""
import json
import math
import tempfile
import unittest
from pathlib import Path

from src import fuente
from src.analisis import TOLERANCIA_M, analizar
from src.etapas import plan_por_etapas
from src import geometria
from src.geometria import Obra, Plano
from tests.test_proyecto import barrio_de_prueba

RAIZ = Path(__file__).resolve().parent.parent
LINEA_BASE = RAIZ / "resultados" / "linea_base"
EJEMPLO = RAIZ / "datos" / "ejemplos" / "obra_ilustrativa.json"

# Claves que la respuesta agregó después de la línea base (el JSON solo se agranda).
NUEVAS = {"obra", "eje", "ancho_m", "medicion", "fuente", "recuadro", "tiempos"}
# Textos de los pasos: se reescribieron de «arroyo» a «obra»; las cifras no cambian.
TEXTOS_DE_PASOS = {"titulo", "unidad", "detalle"}


def diferencias(antes, ahora, ruta="", sobras=False):
    """Lista de diferencias entre la línea base y el resultado de hoy (tolerancia 1e-6 en decimales).

    Con `sobras=True` se aceptan claves que la línea base no tenía (la de analisis.json es anterior
    a `desvio_fijo_m` y `recuperados`); los valores que sí tenía deben ser iguales.
    """
    if isinstance(antes, dict):
        res = []
        for k, v in antes.items():
            if k in NUEVAS:
                continue
            if k not in ahora:
                res.append(f"falta {ruta}/{k}")
            elif not (ruta.startswith("/pasos") and k in TEXTOS_DE_PASOS):
                res += diferencias(v, ahora[k], f"{ruta}/{k}", sobras)
        if not sobras:
            res += [f"sobra {ruta}/{k}" for k in ahora if k not in antes and k not in NUEVAS]
        return res
    if isinstance(antes, list):
        if not isinstance(ahora, list) or len(antes) != len(ahora):
            return [f"{ruta}: largo {len(antes)} -> {len(ahora) if isinstance(ahora, list) else ahora!r}"]
        return [d for i, (a, b) in enumerate(zip(antes, ahora)) for d in diferencias(a, b, f"{ruta}[{i}]", sobras)]
    if isinstance(antes, float) or isinstance(ahora, float):
        return [] if math.isclose(antes, ahora, rel_tol=0, abs_tol=1e-6) else [f"{ruta}: {antes} -> {ahora}"]
    return [] if antes == ahora else [f"{ruta}: {antes!r} -> {ahora!r}"]


class RegresionElSalao(unittest.TestCase):
    """El refactor no cambia ninguna cifra de El Salao. Tarda unos 15 s (usa la red real de datos/cache/)."""

    @classmethod
    def setUpClass(cls):
        cls.lineas = fuente.lineas_ejemplo()
        cls.recuadro, _ = fuente.recuadro_de(cls.lineas, 400)
        cls.red, _ = fuente.red_para(cls.recuadro)

    def test_plan_por_etapas_igual_a_la_linea_base(self):
        base = json.loads((LINEA_BASE / "plan_etapas.json").read_text(encoding="utf-8"))
        plan = json.loads(json.dumps(plan_por_etapas(self.red, self.lineas, recuadro=self.recuadro, propuestas_calculadas=False)))
        self.assertEqual(diferencias(base, plan), [])
        self.assertEqual(plan["resumen"]["etapas"], 3)
        self.assertEqual(len(plan["pasos"]), 9)
        self.assertEqual(plan["parametros"]["ancho_m"], TOLERANCIA_M)

    def test_analisis_de_toda_la_obra_igual_a_la_linea_base(self):
        base = json.loads((LINEA_BASE / "analisis.json").read_text(encoding="utf-8"))
        r = json.loads(json.dumps(analizar(self.red, self.lineas, radio=400, luz_max=60, k=3)))
        self.assertEqual(diferencias(base, r, sobras=True), [])


class AnchoDeLaFranja(unittest.TestCase):
    def test_un_ancho_mayor_cierra_lo_mismo_o_mas(self):
        red, eje = barrio_de_prueba()
        anterior_cerrados, anterior_contacto = set(), set()
        for ancho in (10, 20, 40, 55, 56, 60):
            r = analizar(red, eje, ancho_m=ancho)
            contacto = {c["id"] for c in r["contacto"]}
            cerrados = {c["id"] for c in r["contacto"] if c["estado"] == "bloqueado"}
            self.assertTrue(anterior_contacto <= contacto, ancho)
            self.assertTrue(anterior_cerrados <= cerrados, ancho)
            anterior_cerrados, anterior_contacto = cerrados, contacto

    def test_umbral_hecho_a_mano(self):
        # El eje va por la latitud 10.0005; la Calle Sur (10.0000) y la Calle Norte (10.0010) quedan a
        # 0.0005 * 110600 = 55.3 m. Con ancho 55 siguen fuera: solo se cierra la Carrera 1 (cruza).
        # Con ancho 56 quedan dentro de la franja ("sobre") y se cierran sus cuatro tramos; las
        # esquinas s0, s1, n0 y n1 quedan dentro de la franja (s2 y n2 no, porque son extremos del puente).
        red, eje = barrio_de_prueba()
        r55 = analizar(red, eje, ancho_m=55)
        self.assertEqual(r55["red"]["bloqueados"], 1)
        self.assertEqual(r55["red"]["esquinas_inundadas"], 0)
        r56 = analizar(red, eje, ancho_m=56)
        self.assertEqual(r56["red"]["bloqueados"], 5)
        self.assertEqual(r56["red"]["esquinas_inundadas"], 4)
        self.assertEqual({c["via"] for c in r56["contacto"] if c["motivo"] == "sobre"}, {"Calle Sur", "Calle Norte"})

    def test_plan_guarda_el_ancho_en_los_parametros(self):
        red, eje = barrio_de_prueba()
        self.assertEqual(plan_por_etapas(red, eje, ancho_m=20)["parametros"]["ancho_m"], 20)


class ObraALoLargoDeUnaCalle(unittest.TestCase):
    """Obra sobre la Carrera 1 del barrio miniatura (de s1 a n1), alargada 55 m hacia cada lado.

        n0 ---- n1 ---- n2
               |#       |
               |#       |        # = eje de la obra (lon -74.001, de lat 9.9995 a 10.0015)
               |#       |
        s0 ---- s1 ---- s2

    Resuelto a mano:
      - Largo del eje: 0.002 grados de latitud * 110600 = 221.2 m -> 221 m; una etapa (cabe en 1000 m)
        y un paso peatonal (221 / 500 = 0.44 redondea a 0, y el mínimo es 1).
      - La Carrera 1 va sobre el eje: "sobre". Los cuatro tramos de la Calle Sur y la Calle Norte tocan el
        eje en s1 o en n1: "cruza". La Carrera 2 (puente) queda a 109.6 m: no se toca.
        Se cierran 5 tramos, todos cruces (ninguno es puente existente).
      - s1 y n1 están sobre el eje (distancia 0 < 10 m): quedan dentro de la franja.
      - A cada lado quedan solo 2 esquinas (s0, n0 al occidente; s2, n2 al oriente), menos de las 3 que
        hacen falta para medir el desvío: el plan lo avisa y no da métricas.
    """

    EJE = [[(9.9995, -74.001), (10.0015, -74.001)]]

    def test_plan_hecho_a_mano(self):
        red, _ = barrio_de_prueba()
        plan = plan_por_etapas(red, self.EJE)
        self.assertEqual(plan["obra"]["longitud_m"], 221)
        self.assertEqual(len(plan["etapas"]), 1)
        e = plan["etapas"][0]
        carrera2 = next(t.id for t in red.tramos if t.via == "Carrera 2")
        self.assertEqual(len(e["tramos_cerrados"]), 5)
        self.assertNotIn(carrera2, e["tramos_cerrados"])
        self.assertEqual(e["cruces_cerrados"], 5)
        self.assertEqual(e["puentes_existentes_cerrados"], 0)
        self.assertEqual(e["puentes_necesarios"], 1)
        self.assertIsNone(e["peatones"])
        self.assertEqual(len(e["avisos"]), 1)
        self.assertEqual(e["eje"], e["cauce"])

    def test_analisis_hecho_a_mano(self):
        red, _ = barrio_de_prueba()
        r = analizar(red, self.EJE)
        motivos = sorted((c["via"], c["motivo"]) for c in r["contacto"])
        self.assertEqual(motivos, [("Calle Norte", "cruza"), ("Calle Norte", "cruza"), ("Calle Sur", "cruza"),
                                   ("Calle Sur", "cruza"), ("Carrera 1", "sobre")])
        self.assertEqual(r["red"]["esquinas_inundadas"], 2)
        self.assertEqual(sorted(r["zona"]["lados"].values()), [2, 2])
        self.assertIsNone(r["peatones"])


class NombresNuevos(unittest.TestCase):
    def test_sin_alias_viejo_arroyo(self):
        # El alias `Arroyo = Obra` se quitó en la limpieza final; la clase es Obra.
        self.assertFalse(hasattr(geometria, "Arroyo"))
        plano = Plano(10.0)
        self.assertAlmostEqual(Obra([[(10.0, -74.0), (10.001, -74.0)]], plano).longitud(), 110.6, places=6)

    def test_plan_tiene_los_nombres_nuevos_y_los_viejos(self):
        red, eje = barrio_de_prueba()
        plan = plan_por_etapas(red, eje)
        self.assertEqual(plan["obra"], plan["arroyo"])
        for e in plan["etapas"]:
            self.assertEqual(e["eje"], e["cauce"])

    def test_textos_de_los_pasos_ya_no_hablan_de_arroyos(self):
        red, eje = barrio_de_prueba()
        texto = json.dumps(plan_por_etapas(red, eje, etapa_max_m=200)["pasos"], ensure_ascii=False).lower()
        for palabra in ("arroyo", "cauce", "lluvia", "canaliz"):
            self.assertNotIn(palabra, texto)


class ObraEnArchivo(unittest.TestCase):
    def _archivo(self, contenido):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        ruta = Path(d.name) / "obra.json"
        ruta.write_text(contenido if isinstance(contenido, str) else json.dumps(contenido), encoding="utf-8")
        return ruta

    def test_lee_lineas_y_las_orienta(self):
        # Dos tramos dibujados en sentidos opuestos que se tocan: quedan como una sola línea.
        ruta = self._archivo({"nombre": "Prueba", "lineas": [[[10.0, -74.0], [10.0, -73.999]],
                                                             [[10.0, -73.998], [10.0, -73.999]]]})
        self.assertEqual(fuente.lineas_de_archivo(ruta), [[(10.0, -74.0), (10.0, -73.999), (10.0, -73.998)]])
        datos = fuente.leer_obra(ruta)
        self.assertEqual((datos["nombre"], datos["ilustrativo"]), ("Prueba", False))

    def test_ejemplo_de_la_calle_72(self):
        datos = fuente.leer_obra(EJEMPLO)
        self.assertTrue(datos["ilustrativo"])
        self.assertTrue(datos["lineas"] and all(len(l) >= 2 for l in datos["lineas"]))
        largo = Obra(datos["lineas"], Plano(datos["lineas"][0][0][0])).longitud()
        self.assertAlmostEqual(largo, 600, delta=30)

    def test_archivos_malos_dan_un_error_claro(self):
        for contenido in ("no es json", [1, 2], {"nombre": "x"}, {"lineas": [[[10.0, -74.0]]]},
                          {"lineas": [[["a", "b"], [10.0, -74.0]]]}, {"lineas": [[[100.0, -74.0], [10.0, -74.0]]]}):
            with self.assertRaises(ValueError, msg=contenido):
                fuente.lineas_de_archivo(self._archivo(contenido))


class Medicion(unittest.TestCase):
    def test_lados_es_lo_de_siempre(self):
        red, eje = barrio_de_prueba()
        a, b = plan_por_etapas(red, eje), plan_por_etapas(red, eje, medicion="lados")
        self.assertEqual(a, b)
        self.assertEqual(a["parametros"]["medicion"], "lados")

    def test_medicion_invalida_falla_con_mensaje_claro(self):
        red, eje = barrio_de_prueba()
        with self.assertRaisesRegex(ValueError, "medicion='afectados'.*lados"):
            plan_por_etapas(red, eje, medicion="afectados")


if __name__ == "__main__":
    unittest.main()
