"""Heurística voraz contra fuerza bruta (k = 2).

La fuerza bruta prueba TODAS las parejas de candidatos y se queda con la mejor según el
mismo criterio que el voraz: (pares sin camino, desvío medio). Así se mide cuánto se aleja
el voraz del óptimo para k = 2. No es una demostración: dice qué pasó en cada caso.

Para evaluar una pareja {i, j} sin repetir Dijkstra desde cada origen:
  1. se agrega el candidato i con `actualizar_tablas` (2 Dijkstra por arco),
  2. se evalúa el candidato j sobre esas tablas con la fórmula rápida.
Es exacto: la fórmula rápida es exacta para UN arco nuevo sobre unas tablas ya correctas,
y `actualizar_tablas` deja las tablas correctas para el grafo con el primer arco.
"""
from src.analisis import Evaluador, actualizar_tablas, extremos, voraz
from src.grafo import INF


def objetivo_inicial(F, R, base, pares):
    return Evaluador(F, R, base, pares).objetivo(())


def fuerza_bruta(g, origenes, base, pares, candidatos, F, R):
    """Mejor pareja de candidatos: (objetivo, i, j). Si ninguna mejora, devuelve None en i, j.

    `candidatos` es la lista de (info, arcos) que usa `voraz`; F y R, las tablas del grafo g.
    """
    objetivos = set(origenes) | extremos(candidatos)
    mejor = (objetivo_inicial(F, R, base, pares), None, None)
    n = len(candidatos)
    for i in range(n):
        F2, R2 = actualizar_tablas(g, F, R, candidatos[i][1], objetivos)
        ev = Evaluador(F2, R2, base, pares)
        for j in range(i + 1, n):
            obj = ev.objetivo(candidatos[j][1])
            if obj < mejor[0]:
                mejor = (obj, i, j)
    return mejor


def objetivo_de(g, origenes, base, pares, candidatos, indices, F, R):
    """Objetivo exacto al agregar los candidatos `indices` (en ese orden)."""
    objetivos = set(origenes) | extremos(candidatos)
    g = g.copia()
    for k, i in enumerate(indices):
        arcos = candidatos[i][1]
        if k < len(indices) - 1:
            F, R = actualizar_tablas(g, F, R, arcos, objetivos)
            for x, y, w in arcos:
                g.agregar_arista(x, y, w)
        else:
            return Evaluador(F, R, base, pares).objetivo(arcos)
    return objetivo_inicial(F, R, base, pares)


def comparar(g, origenes, base, pares, candidatos, F, R):
    """Resultado del voraz (k = 2) y de la fuerza bruta, con la diferencia entre los dos."""
    elegidos, _ = voraz(g, origenes, base, pares, candidatos, 2, F=F, R=R)
    infos = [c[0] for c in candidatos]
    indices = [next(i for i, inf in enumerate(infos) if inf is info) for info, _ in elegidos]
    obj_voraz = objetivo_de(g, origenes, base, pares, candidatos, indices, F, R) if indices \
        else objetivo_inicial(F, R, base, pares)
    obj_opt, i, j = fuerza_bruta(g, origenes, base, pares, candidatos, F, R)
    return dict(
        voraz=dict(indices=indices, objetivo=obj_voraz),
        optimo=dict(indices=[] if i is None else [i, j], objetivo=obj_opt),
        sin_camino_extra=obj_voraz[0] - obj_opt[0],
        desvio_extra_m=round(obj_voraz[1] - obj_opt[1], 3),
        coinciden=sorted(indices) == sorted([] if i is None else [i, j]) or obj_voraz == obj_opt,
        candidatos=len(candidatos),
    )
