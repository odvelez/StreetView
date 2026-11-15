"""Supuestos de las propuestas calculadas: un solo lugar para todos.

No hay datos de tránsito (ni conteos, ni población por manzana, ni tiempos de semáforo). Todo lo que
las propuestas calculadas suponen está aquí, con su valor por defecto, su unidad, el rango en que se
probó su sensibilidad, por qué se eligió, de dónde sale y qué tan seguro es:

  - "confirmado":           se vio en la fuente original o en una norma publicada.
  - "reportado":            lo dicen fuentes secundarias o resúmenes; no se leyó la fuente original.
  - "no verificado":        apareció en una sola fuente débil.
  - "supuesto del equipo":  no hay fuente; es una decisión del equipo para poder calcular.

Ningún valor de este archivo es un dato medido en Soledad.
"""
from dataclasses import asdict, dataclass

ESTADOS = ("confirmado", "reportado", "no verificado", "supuesto del equipo")


@dataclass(frozen=True)
class Supuesto:
    nombre: str
    valor: object
    unidad: str
    rango: object          # (mínimo, máximo) para los números; texto para los demás
    justificacion: str
    fuente: str
    estado: str


_LISTA = [
    Supuesto(
        "d0_m", 400, "m", (200, 1000),
        "Distancia característica de la demanda: el peso de un par de esquinas a distancia d (sin obra) es "
        "exp(-d / d0). Con d0 = 400 m un par a 400 m pesa 0,37 frente a uno a 0 m.",
        "Forma del modelo de gravedad: Princeton ORF 467, Trip Distribution. Gao, Wang, Gao y Liu (2013), "
        "Environment and Planning B 40(1):135-153: con el decaimiento por distancia el modelo predice mejor el "
        "tráfico que la intermediación sola. El valor 400 m no tiene fuente.",
        "supuesto del equipo"),
    Supuesto(
        "peso_esquina", "uniforme", "", "uniforme",
        "Cada esquina genera y atrae lo mismo. No hay población ni comercios por manzana.",
        "Sin fuente: no hay datos por manzana en el proyecto.",
        "supuesto del equipo"),
    Supuesto(
        "veh_h_carril", 950, "veh/h por carril", (600, 1900),
        "Capacidad de un carril en una calle con intersecciones: 1900 vehículos por hora de verde (base del "
        "HCM) por una fracción de verde g/C = 0,5. Si es igual en todas las calles no cambia el orden de las "
        "alternativas: solo multiplica la capacidad en carriles.",
        "1900 por hora de verde y por carril: Highway Capacity Manual, citado por FHWA (HPMS, apéndice N) y "
        "otros. g/C = 0,5 no tiene fuente (no hay tiempos de semáforo).",
        "reportado"),
    Supuesto(
        "carriles_por_clase",
        {"trunk": 4, "primary": 4, "secondary": 2, "tertiary": 2, "unclassified": 2, "residential": 2,
         "living_street": 1, "service": 1, "road": 2},
        "carriles (total de la vía)", "±1 carril",
        "Carriles cuando OpenStreetMap no trae la etiqueta lanes (la trae cerca del 20 % de las vías de la "
        "zona de El Salao). En una vía de doble sentido se reparten por mitades.",
        "Sin fuente: valores típicos elegidos por el equipo.",
        "supuesto del equipo"),
    Supuesto(
        "dist_par_max_m", 200, "m", (80, 300),
        "Dos calles paralelas forman un posible par vial si sus centros están a menos de esto (unas dos cuadras).",
        "Sin fuente.", "supuesto del equipo"),
    Supuesto(
        "largo_min_par_m", 100, "m", (50, 300),
        "Una calle cuenta para un par vial si tiene al menos este largo de un solo sentido cerca de la etapa.",
        "Sin fuente.", "supuesto del equipo"),
    Supuesto(
        "sep_calzadas_m", 40, "m", (20, 60),
        "Dos tramos de un solo sentido con el mismo nombre, sentidos opuestos y a menos de esto son las dos "
        "calzadas de una misma avenida: no se proponen como par vial.",
        "Sin fuente.", "supuesto del equipo"),
    Supuesto(
        "carriles_min_doble", 2, "carriles", (1, 3),
        "Una calle de un solo sentido solo puede pasar a doble sentido si tiene al menos estos carriles.",
        "Sin fuente: con un solo carril no caben dos sentidos.", "supuesto del equipo"),
    Supuesto(
        "clases_invertibles", ("residential", "tertiary", "unclassified", "living_street"), "clases de OSM",
        "residential, tertiary, unclassified, living_street",
        "Solo se propone invertir calles locales. Las avenidas (trunk, primary, secondary) quedan fuera.",
        "Sin fuente.", "supuesto del equipo"),
    Supuesto(
        "max_pares_etapa", 3, "pares", (1, 6),
        "Pares de calles que se evalúan por etapa (los más cercanos a la obra). Limita el tiempo de cálculo.",
        "Sin fuente: límite de cálculo.", "supuesto del equipo"),
    Supuesto(
        "sep_min_pasos_m", 80, "m", (50, 150),
        "Separación mínima, a lo largo del eje, entre dos pasos peatonales provisionales elegidos por demanda.",
        "Global Street Design Guide (GDCI): cruces a nivel cada 80 a 100 m en zonas urbanas. Es una guía "
        "internacional, no la norma colombiana.",
        "reportado"),
    Supuesto(
        "brecha_max_m", 200, "m", (100, 400),
        "Tramo de obra sin ningún cruce abierto que se marca como demasiado largo.",
        "Global Street Design Guide (GDCI): distancias de más de 200 m entre cruces deben evitarse.",
        "reportado"),
    Supuesto(
        "max_pasos_etapa", 8, "pasos", (2, 12),
        "Máximo de pasos peatonales por demanda en una etapa. Limita el cálculo; normalmente el voraz se "
        "detiene antes porque el siguiente paso ya no mejora lo suficiente.",
        "Sin fuente: límite de cálculo.", "supuesto del equipo"),
    Supuesto(
        "mejora_min", 0.02, "fracción", (0.0, 0.1),
        "Un paso peatonal más se agrega solo si baja el desvío ponderado al menos este 2 % (y 0,5 m).",
        "Sin fuente: el mismo umbral que usa el voraz del proyecto (analisis.MEJORA_MIN).",
        "supuesto del equipo"),
    Supuesto(
        "tolerancia_desvio_relativo", 0.5, "fracción", (0.25, 1.0),
        "Un par con un recorrido a pie más de un 50 % más largo que sin obra se cuenta como «probable que "
        "cruce por donde no debe».",
        "Moore y Older (1965), citados en un artículo de la WCTR 2019 (Mumbai, n.º 992): casi nadie usa un "
        "puente peatonal que tarda un 50 % más que cruzar a nivel. No se leyó el estudio original.",
        "reportado"),
    Supuesto(
        "percentil_carga", 90, "percentil", (75, 95),
        "Una esquina es candidata a control temporal si los recorridos desviados que pasan por ella están en "
        "este percentil o más de la etapa.",
        "Sin fuente. NO es un criterio de justificación de semáforos (MUTCD, capítulo 4C): esos criterios "
        "exigen conteos de vehículos y peatones.",
        "supuesto del equipo"),
    Supuesto(
        "accesos_min", 3, "accesos", (3, 4),
        "Una esquina candidata a control debe tener al menos 3 calles vehiculares (no es un simple codo).",
        "Sin fuente.", "supuesto del equipo"),
    Supuesto(
        "sep_control_m", 150, "m", (80, 300),
        "Separación mínima entre dos esquinas elegidas para control temporal.",
        "Sin fuente: la misma separación que usa el proyecto entre cambios de sentido.", "supuesto del equipo"),
    Supuesto(
        "max_controles_etapa", 3, "esquinas", (1, 5),
        "Máximo de esquinas propuestas para control temporal por etapa.",
        "Sin fuente.", "supuesto del equipo"),
]

SUPUESTOS = {s.nombre: s for s in _LISTA}


def valor(nombre):
    return SUPUESTOS[nombre].valor


def como_lista(valores=None):
    """Lista de dicts para el JSON, con el valor que de verdad se usó (los de `valores` reemplazan)."""
    valores = valores or {}
    res = []
    for s in _LISTA:
        d = asdict(s)
        v = valores.get(s.nombre, s.valor)
        d["valor"] = list(v) if isinstance(v, tuple) else v
        d["rango"] = list(s.rango) if isinstance(s.rango, tuple) else s.rango
        res.append(d)
    return res
