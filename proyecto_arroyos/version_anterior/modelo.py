"""Modelo del arroyo El Salao: carga los datos, arma escenarios y calcula métricas."""
import csv
import math
from dataclasses import dataclass
from pathlib import Path

from src.grafo import Grafo, INF, componentes_conexas, dijkstra

M_LAT, M_LON = 110600, 109300
DATOS = Path(__file__).resolve().parent.parent / "datos"


def distancia_m(a, b):
    return math.hypot((a[0] - b[0]) * M_LAT, (a[1] - b[1]) * M_LON)


def clave(u, v):
    return tuple(sorted((u, v)))


@dataclass
class Datos:
    nodos: dict
    aristas: list
    cruces: list
    arroyo: list


def leer_csv(nombre, carpeta=DATOS):
    with open(Path(carpeta) / nombre, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cargar(carpeta=DATOS):
    nodos = {r["id"]: {"pos": (float(r["lat"]), float(r["lon"])), "nombre": r["nombre"]}
             for r in leer_csv("nodos.csv", carpeta)}
    aristas = [(r["u"], r["v"], float(r["metros"]), r["via"])
               for r in leer_csv("aristas.csv", carpeta)]
    arroyo = [((float(r["lat1"]), float(r["lon1"])), (float(r["lat2"]), float(r["lon2"])))
              for r in leer_csv("arroyo.csv", carpeta)]
    return Datos(nodos, aristas, leer_csv("cruces.csv", carpeta), arroyo)


def construir_grafo(datos, excluir=frozenset()):
    g = Grafo()
    for u in datos.nodos:
        g.agregar_nodo(u)
    for u, v, metros, _ in datos.aristas:
        if u != v and clave(u, v) not in excluir:
            g.agregar_arista(u, v, metros)
    return g


def bloqueados_lluvia(datos):
    return {clave(c["u"], c["v"]) for c in datos.cruces if c["bloqueado_lluvia"] == "1"}


def puentes(datos):
    return [c for c in datos.cruces if c["tipo"] == "puente"]


def lados_del_arroyo(datos):
    """Separa la red en norte y sur quitando TODO tramo en contacto con el arroyo."""
    todos = {clave(c["u"], c["v"]) for c in datos.cruces}
    comp = componentes_conexas(construir_grafo(datos, todos))
    a, b = comp[0], comp[1]

    def lat_media(c):
        return sum(datos.nodos[x]["pos"][0] for x in c) / len(c)

    return (a, b) if lat_media(a) > lat_media(b) else (b, a)


def distancia_al_arroyo(p, arroyo):
    def seg(a, b):
        ax, ay = a[1] * M_LON, a[0] * M_LAT
        bx, by = b[1] * M_LON, b[0] * M_LAT
        px, py = p[1] * M_LON, p[0] * M_LAT
        vx, vy = bx - ax, by - ay
        l2 = vx * vx + vy * vy
        t = max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / l2)) if l2 else 0
        return math.hypot(px - ax - t * vx, py - ay - t * vy)

    return min(seg(a, b) for a, b in arroyo)


def zona_de_estudio(datos, radio):
    """Nodos de cada lado a menos de `radio` metros del arroyo."""
    norte, sur = lados_del_arroyo(datos)

    def cerca(c):
        return sorted(x for x in c if distancia_al_arroyo(datos.nodos[x]["pos"], datos.arroyo) <= radio)

    return cerca(norte), cerca(sur)


def tabla_distancias(g, origenes):
    return {o: dijkstra(g, o)[0] for o in origenes}


@dataclass
class Metricas:
    pares: int
    conectados: int
    media_m: float
    desvio_medio_m: float
    pct_mas_200m: float
    desvio_max_m: float


def medir(tabla, tabla_base, sur, norte):
    """Compara cada par sur-norte contra su distancia en el escenario base."""
    pares = conectados = 0
    suma = suma_desvio = maximo = mayores = 0.0
    for s in sur:
        d, base = tabla[s], tabla_base[s]
        for n in norte:
            if n not in base:
                continue
            pares += 1
            if n not in d:
                continue
            conectados += 1
            suma += d[n]
            desvio = d[n] - base[n]
            suma_desvio += desvio
            maximo = max(maximo, desvio)
            mayores += desvio > 200
    c = max(conectados, 1)
    return Metricas(pares, conectados, suma / c, suma_desvio / c,
                    100 * mayores / c, maximo)


def candidatos_puente(datos, g_lluvia, sur, norte, luz_max=90):
    """Posibles puentes nuevos: une un nodo sur con el nodo norte más cercano."""
    res = {}
    for s in sur:
        ps = datos.nodos[s]["pos"]
        if distancia_al_arroyo(ps, datos.arroyo) > luz_max:
            continue
        mejor, dmin = None, INF
        for n in norte:
            d = distancia_m(ps, datos.nodos[n]["pos"])
            if d < dmin:
                mejor, dmin = n, d
        if mejor is not None and dmin <= luz_max and clave(s, mejor) not in res:
            if mejor not in g_lluvia.adj[s]:
                res[clave(s, mejor)] = (s, mejor, round(dmin, 1))
    return list(res.values())


def desvio_con_puente(tabla, tabla_base, sur, norte, s_p, n_p, luz):
    """Desvío medio si se agrega un puente, sin repetir Dijkstra.

    Nuevo camino a->b = min(actual, a->s_p + luz + n_p->b, a->n_p + luz + s_p->b).
    Como el grafo es no dirigido, d(x, b) = d(b, x).
    """
    total = conectados = 0
    for a in sur:
        d, base = tabla[a], tabla_base[a]
        ds = d.get(s_p, INF)
        dn = d.get(n_p, INF)
        for b in norte:
            if b not in base:
                continue
            db = tabla[b]
            nuevo = min(d.get(b, INF), ds + luz + db.get(n_p, INF), dn + luz + db.get(s_p, INF))
            if nuevo < INF:
                conectados += 1
                total += nuevo - base[b]
    return total / max(conectados, 1)


def elegir_puentes(datos, g_lluvia, tabla_base, sur, norte, k):
    """Heurística voraz: en cada ronda agrega el puente que más reduce el desvío."""
    g = g_lluvia.copia()
    elegidos = []
    origenes = sorted(set(sur) | set(norte))
    for _ in range(k):
        tabla = tabla_distancias(g, origenes)
        mejor, mejor_valor = None, INF
        for s, n, luz in candidatos_puente(datos, g, sur, norte):
            v = desvio_con_puente(tabla, tabla_base, sur, norte, s, n, luz)
            if v < mejor_valor - 1e-9:
                mejor, mejor_valor = (s, n, luz), v
        if mejor is None:
            break
        g.agregar_arista(mejor[0], mejor[1], mejor[2])
        elegidos.append((*mejor, mejor_valor))
    return elegidos, g
