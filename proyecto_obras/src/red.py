"""Red vial construida desde OpenStreetMap: tramos entre intersecciones.

Cada tramo une dos intersecciones y guarda:
  - su longitud en metros (el peso de la arista),
  - si lo pueden usar carros/motos y si lo pueden usar peatones,
  - su sentido: 0 doble sentido, 1 solo de u a v, -1 solo de v a u,
  - si OpenStreetMap lo marca como puente,
  - su forma (lista de puntos) para dibujarlo en el mapa.

Con los tramos se arman dos grafos:
  - peatones: no dirigido (a pie se camina en ambos sentidos).
  - vehículos: dirigido (se respetan las calles de un solo sentido).
"""
from collections import Counter
from dataclasses import dataclass, field

from src.geometria import Plano
from src.grafo import INF, Grafo

VEHICULARES = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
               "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
               "residential", "living_street", "service", "road"}
SOLO_PEATONES = {"footway", "pedestrian", "path", "steps", "track", "cycleway"}
SIN_PEATONES = {"motorway", "motorway_link"}
PRIVADO = {"private", "no"}


def _nombre_de_via(nombre):
    """Una calle de OSM llamada como el arroyo ("Arroyo El Salao") es una vía local junto
    al eje de la obra; con ese nombre la pantalla parecería hablar del arroyo."""
    if nombre.lower().startswith("arroyo "):
        return "Vía local junto al eje (en OSM: " + nombre + ")"
    return nombre


@dataclass
class Tramo:
    id: int
    u: str
    v: str
    metros: float
    via: str
    clase: str
    forma: list
    vehicular: bool
    peatonal: bool
    sentido: int = 0
    puente: bool = False
    extra: dict = field(default_factory=dict)


def sentido_de(tags):
    ow = tags.get("oneway", "")
    if ow in ("yes", "1", "true"):
        return 1
    if ow in ("-1", "reverse"):
        return -1
    if ow == "no":
        return 0
    if tags.get("junction") in ("roundabout", "circular") or tags.get("highway") in ("motorway", "motorway_link"):
        return 1
    return 0


def permisos(tags):
    """(vehicular, peatonal) según el tipo de vía y las restricciones de acceso."""
    clase = tags.get("highway", "")
    vehicular = clase in VEHICULARES
    peatonal = (clase in VEHICULARES and clase not in SIN_PEATONES) or clase in SOLO_PEATONES
    if tags.get("access") in PRIVADO:
        vehicular = vehicular and tags.get("motor_vehicle") == "yes"
        peatonal = peatonal and tags.get("foot") in ("yes", "designated")
    if tags.get("motor_vehicle") in PRIVADO or tags.get("vehicle") in PRIVADO:
        vehicular = False
    if tags.get("foot") in PRIVADO:
        peatonal = False
    if tags.get("area") == "yes":
        return False, False
    return vehicular, peatonal


class Red:
    def __init__(self, nodos_osm, vias_osm):
        lats = [p[0] for p in nodos_osm.values()] or [0.0]
        self.plano = Plano(sum(lats) / len(lats))
        self.pos = {}
        self.tramos = []
        self._construir(nodos_osm, vias_osm)
        self.nombres = self._nombrar()

    def _construir(self, nodos, vias):
        utiles = {}
        for w, (refs, tags) in vias.items():
            veh, pea = permisos(tags)
            if veh or pea:
                utiles[w] = (refs, tags, veh, pea)

        # Un nodo es intersección si lo usan dos vías o si es extremo de una.
        usos = Counter()
        for refs, *_ in utiles.values():
            usos.update(refs)
            usos[refs[0]] += 1
            usos[refs[-1]] += 1

        for w, (refs, tags, veh, pea) in sorted(utiles.items()):
            inicio = 0
            for i in range(1, len(refs)):
                if usos[refs[i]] <= 1 and i != len(refs) - 1:
                    continue
                parte = refs[inicio: i + 1]
                inicio = i
                if parte[0] == parte[-1]:
                    continue
                forma = [nodos[r] for r in parte]
                metros = sum(self.plano.dist(a, b) for a, b in zip(forma, forma[1:]))
                self.pos[parte[0]] = nodos[parte[0]]
                self.pos[parte[-1]] = nodos[parte[-1]]
                self.tramos.append(Tramo(
                    id=len(self.tramos), u=parte[0], v=parte[-1], metros=round(metros, 1),
                    via=_nombre_de_via(tags.get("name", "")), clase=tags.get("highway", ""), forma=forma,
                    vehicular=veh, peatonal=pea, sentido=sentido_de(tags) if veh else 0,
                    puente=tags.get("bridge", "no") not in ("no", "") or tags.get("man_made") == "bridge"))

    def _nombrar(self):
        nombres = {}
        for t in self.tramos:
            if t.via:
                for n in (t.u, t.v):
                    nombres.setdefault(n, set()).add(t.via)
        res = {n: " x ".join(sorted(v)[:2]) for n, v in nombres.items()}
        # Esquinas de callejones o vías sin nombre en OpenStreetMap: se nombran por la
        # esquina vecina con nombre más cercana ("esquina cerca de Calle 61 x Carrera 22").
        vecina = {}
        for t in self.tramos:
            for n, otro in ((t.u, t.v), (t.v, t.u)):
                if n not in res and otro in res and t.metros < vecina.get(n, (INF, ""))[0]:
                    vecina[n] = (t.metros, res[otro])
        res.update({n: f"esquina cerca de {nombre}" for n, (_, nombre) in vecina.items()})
        return res

    def nombre(self, n):
        return self.nombres.get(n) or "esquina sin nombre"

    def grafo_peatones(self, excluir=frozenset()):
        g = Grafo(dirigido=False)
        for t in self.tramos:
            if t.peatonal and t.id not in excluir:
                g.agregar_arista(t.u, t.v, t.metros)
        return g

    def grafo_vehiculos(self, excluir=frozenset()):
        g = Grafo(dirigido=True)
        for t in self.tramos:
            if t.vehicular and t.id not in excluir:
                if t.sentido >= 0:
                    g.agregar_arista(t.u, t.v, t.metros)
                if t.sentido <= 0:
                    g.agregar_arista(t.v, t.u, t.metros)
        return g

    def forma_arco(self, a, b, solo_vehicular=False):
        """Forma del tramo más corto que va de a hacia b (para dibujar rutas)."""
        mejor = None
        for t in self._por_par().get((a, b), []):
            if solo_vehicular and not t.vehicular:
                continue
            if mejor is None or t.metros < mejor.metros:
                mejor = t
        if mejor is None:
            return [self.pos[a], self.pos[b]]
        return mejor.forma if mejor.u == a else mejor.forma[::-1]

    def _por_par(self):
        if not hasattr(self, "_indice"):
            self._indice = {}
            for t in self.tramos:
                self._indice.setdefault((t.u, t.v), []).append(t)
                self._indice.setdefault((t.v, t.u), []).append(t)
        return self._indice
