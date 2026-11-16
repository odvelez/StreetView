"""Demanda supuesta entre esquinas (modelo de gravedad) y desvío ponderado por esa demanda.

No hay conteos de tránsito ni de peatones. Para no tratar igual un par de esquinas vecinas y uno de
esquinas a 2 km, cada par (a, b) recibe un peso de gravedad:

    T_ab = w_a * w_b * exp(-d_sin_obra(a, b) / d0)          y luego se normaliza para que sumen 1.

w_a es el «peso» de la esquina (uniforme: no hay población por manzana) y d0 la distancia
característica (src/supuestos.py). Con d0 muy grande todos los pares pesan igual y el desvío
ponderado es el desvío medio de siempre (hay una prueba que lo comprueba).

Este módulo también trae el voraz ponderado (la misma idea que `analisis.voraz`, con la misma fórmula
rápida d'(a, b) = min(d(a, b), d(a, x) + w + d(y, b)), pero con el objetivo pesado por la demanda) y su
fuerza bruta para compararlo en casos pequeños.
"""
import itertools
import math

from src.analisis import actualizar_tablas, extremos, tablas
from src.grafo import INF


def pesos_gravedad(pares, base, d0_m=None, peso=None):
    """{(a, b): peso} normalizado a suma 1. `base[a][b]` es la distancia sin obra.

    `d0_m` None o infinito: todos los pares pesan igual. `peso(esquina)`: peso de cada esquina (por
    defecto 1).
    """
    crudo = {}
    for a, b in pares:
        f = 1.0 if d0_m is None or math.isinf(d0_m) else math.exp(-base[a][b] / d0_m)
        crudo[(a, b)] = (peso(a) * peso(b) if peso else 1.0) * f
    total = sum(crudo.values())
    if total <= 0:
        n = max(len(crudo), 1)
        return {p: 1.0 / n for p in crudo}
    return {p: v / total for p, v in crudo.items()}


def evaluar(F, R, base, pares, pesos, arcos=(), tolerancia=None):
    """Desvío ponderado de los pares, opcionalmente agregando arcos nuevos (x, y, peso).

    Devuelve dict(desvio_ponderado_m, desvio_positivo_m, sin_camino, demanda_sin_camino_pct,
    demanda_desvio_relativo_pct):
      - desvio_ponderado_m: media de d_obra(a, b) - d_sin_obra(a, b) pesada por la demanda, sobre los
        pares que tienen camino. Puede ser negativa si una medida crea un atajo más corto que antes;
      - desvio_positivo_m: lo mismo contando solo el alargamiento, max(0, d_obra - d_sin_obra): un atajo
        nuevo no compensa el desvío de otro par. Es el que se usa para elegir pasos peatonales;
      - sin_camino: cuántos pares quedan sin camino; demanda_sin_camino_pct: qué parte de la demanda;
      - demanda_desvio_relativo_pct (si se da `tolerancia`): parte de la demanda cuyo recorrido se alarga
        más que esa fracción (por ejemplo 0,5 = un 50 % más largo).
    """
    suma_w = suma_wd = suma_wp = w_sin = w_rel = 0.0
    sin = 0
    for a, b in pares:
        w = pesos[(a, b)]
        Fa = F[a]
        d = Fa.get(b, INF)
        if arcos:
            Rb = R[b]
            for x, y, peso in arcos:
                c = Fa.get(x, INF) + peso + Rb.get(y, INF)
                if c < d:
                    d = c
        if d == INF:
            sin += 1
            w_sin += w
            continue
        seco = base[a][b]
        desvio = d - seco
        suma_w += w
        suma_wd += w * desvio
        suma_wp += w * max(0.0, desvio)
        if tolerancia is not None and seco > 0 and desvio / seco > tolerancia:
            w_rel += w
    return dict(desvio_ponderado_m=suma_wd / suma_w if suma_w else 0.0,
                desvio_positivo_m=suma_wp / suma_w if suma_w else 0.0, sin_camino=sin,
                demanda_sin_camino_pct=100 * w_sin, demanda_desvio_relativo_pct=100 * w_rel)


def objetivo(m, positivo=False):
    """Primero que nadie quede sin camino; después, el desvío ponderado (o solo el positivo)."""
    return (m["sin_camino"], round(m["desvio_positivo_m" if positivo else "desvio_ponderado_m"], 3))


class EvaluadorPonderado:
    """Lo mismo que `evaluar(...)[objetivo]` para un candidato, pero tocando solo los pares que mejoran.

    Es `analisis.Evaluador` con pesos: los pares se agrupan por origen y una cota descarta filas enteras
    (si d(a, x) + w + min_b d(y, b) no es menor que el par más largo de la fila, el arco no acorta nada).
    """

    def __init__(self, F, R, base, pares, pesos, positivo=False):
        self.F, self.R = F, R
        self.positivo = positivo
        alarga = (lambda x: max(0.0, x)) if positivo else (lambda x: x)
        self.alarga = alarga
        filas = {}
        for a, b in pares:
            filas.setdefault(a, []).append(b)
        self.columnas = sorted({b for _, b in pares}, key=str)
        self.filas = []
        self.sin = 0
        self.suma_w = self.suma_wd = 0.0
        for a, bs in filas.items():
            Fa = F[a]
            actual = [Fa.get(b, INF) for b in bs]
            seco = [base[a][b] for b in bs]
            w = [pesos[(a, b)] for b in bs]
            for d, s, p in zip(actual, seco, w):
                if d == INF:
                    self.sin += 1
                else:
                    self.suma_w += p
                    self.suma_wd += p * alarga(d - s)
            self.filas.append((a, bs, actual, seco, w, max(actual)))

    def actual(self):
        return (self.sin, round(self.suma_wd / self.suma_w if self.suma_w else 0.0, 3))

    def objetivo(self, arcos):
        alarga = self.alarga
        sin, suma_w, suma_wd = self.sin, self.suma_w, self.suma_wd
        hacia = []
        for x, y, peso in arcos:
            ry = {b: self.R[b].get(y, INF) for b in self.columnas}
            minimo = min(ry.values(), default=INF)
            if minimo < INF:
                hacia.append((x, peso, ry, minimo))
        if hacia:
            for a, bs, actual, seco, w, peor in self.filas:
                Fa = self.F[a]
                mejoras = None
                for x, peso, ry, minimo in hacia:
                    t = Fa.get(x, INF) + peso
                    if t + minimo >= peor:
                        continue
                    if mejoras is None:
                        mejoras = {}
                    for j, b in enumerate(bs):
                        c = t + ry[b]
                        if c < actual[j] and c < mejoras.get(j, INF):
                            mejoras[j] = c
                if mejoras:
                    for j, c in mejoras.items():
                        if actual[j] == INF:
                            sin -= 1
                            suma_w += w[j]
                            suma_wd += w[j] * alarga(c - seco[j])
                        else:
                            suma_wd -= w[j] * (alarga(actual[j] - seco[j]) - alarga(c - seco[j]))
        return (sin, round(suma_wd / suma_w if suma_w else 0.0, 3))


def agregar_arcos(g, F, R, arcos, objetivos):
    """Tablas exactas del grafo g con varios arcos nuevos: se agregan de a uno (como en el voraz), así un
    camino puede usar más de un arco nuevo. Devuelve (g con los arcos, F, R)."""
    g = g.copia()
    for arco in arcos:
        F, R = actualizar_tablas(g, F, R, [arco], objetivos)
        g.agregar_arista(*arco)
    return g, F, R


def voraz_ponderado(g, origenes, base, pares, pesos, candidatos, k_max, F, R, mejora_min,
                    incompatibles=None, tolerancia=None, positivo=False):
    """Voraz con el objetivo ponderado: en cada ronda agrega el candidato que más baja (sin camino,
    desvío ponderado), mientras baje al menos `mejora_min` del desvío (y 0,5 m) o devuelva el camino a
    alguien. Se detiene antes de `k_max` si ningún candidato mejora lo suficiente: así el NÚMERO de
    medidas sale del cálculo y no de una regla fija.

    `candidatos`: [(info, arcos)]. F y R: tablas de Dijkstra del grafo inicial con objetivos que incluyen
    los extremos de los candidatos. Devuelve ([(info, arcos, metricas)], grafo final); las métricas de
    cada elegido son exactas para el grafo con todos los elegidos hasta ese momento.
    Con `positivo=True` el objetivo solo cuenta el alargamiento (ver `evaluar`).
    """
    g = g.copia()
    objetivos = set(origenes) | extremos(candidatos)
    elegidos, usados = [], set()
    for ronda in range(k_max):
        ev = EvaluadorPonderado(F, R, base, pares, pesos, positivo)
        sin, desvio = ev.actual()
        umbral = (sin, desvio - (abs(desvio) * mejora_min + 0.5))
        mejor = None
        for i, (info, arcos) in enumerate(candidatos):
            if i in usados:
                continue
            if incompatibles and any(incompatibles(e, info) for e, _, _ in elegidos):
                continue
            obj = ev.objetivo(arcos)
            if obj < umbral and (mejor is None or obj < mejor[0]):
                mejor = (obj, i)
        if mejor is None:
            break
        i = mejor[1]
        info, arcos = candidatos[i]
        elegidos.append((info, arcos, evaluar(F, R, base, pares, pesos, arcos, tolerancia)))
        usados.add(i)
        if ronda < k_max - 1:
            F, R = actualizar_tablas(g, F, R, arcos, objetivos)
        for x, y, peso in arcos:
            g.agregar_arista(x, y, peso)
    return elegidos, g


def fuerza_bruta_ponderada(g, origenes, base, pares, pesos, candidatos, k, positivo=False):
    """Mejor combinación de exactamente k candidatos, recalculando Dijkstra desde cero para cada una.

    Solo para casos pequeños (pruebas): sirve para comparar con el voraz. Devuelve (objetivo, índices).
    """
    mejor = None
    for combo in itertools.combinations(range(len(candidatos)), k):
        h = g.copia()
        for i in combo:
            for x, y, peso in candidatos[i][1]:
                h.agregar_arista(x, y, peso)
        F = tablas(h, origenes)
        R = F if not h.dirigido else tablas(h.invertido(), origenes)
        obj = objetivo(evaluar(F, R, base, pares, pesos), positivo)
        if mejor is None or obj < mejor[0]:
            mejor = (obj, combo)
    return mejor
