"""Grafo ponderado (no dirigido o dirigido), con los algoritmos del curso.

Todo está implementado a mano con la biblioteca estándar de Python.
"""
from collections import deque
import heapq

INF = float("inf")


class Grafo:
    """Lista de adyacencia: {nodo: {vecino: peso}}.

    Con dirigido=False cada arista se guarda en los dos sentidos (calles para
    peatones). Con dirigido=True solo se guarda u -> v (calles de un solo sentido).
    Si llegan dos aristas entre el mismo par de nodos, se conserva la más corta,
    porque es la única que puede formar parte de un camino mínimo.
    """

    def __init__(self, dirigido=False):
        self.adj = {}
        self.dirigido = dirigido

    def agregar_nodo(self, u):
        self.adj.setdefault(u, {})

    def agregar_arista(self, u, v, peso=1.0):
        if peso < 0:
            raise ValueError("Dijkstra exige pesos no negativos")
        self.agregar_nodo(u)
        self.agregar_nodo(v)
        if peso < self.adj[u].get(v, INF):
            self.adj[u][v] = peso
        if not self.dirigido and peso < self.adj[v].get(u, INF):
            self.adj[v][u] = peso

    def quitar_arista(self, u, v):
        self.adj.get(u, {}).pop(v, None)
        if not self.dirigido:
            self.adj.get(v, {}).pop(u, None)

    def nodos(self):
        return list(self.adj)

    def copia(self):
        g = Grafo(self.dirigido)
        g.adj = {u: dict(vec) for u, vec in self.adj.items()}
        return g

    def invertido(self):
        """Mismo grafo con todos los arcos al revés.

        Dijkstra sobre el grafo invertido desde b da d(x, b) para todo x:
        la distancia de cada nodo HACIA b en el grafo original.
        """
        g = Grafo(self.dirigido)
        for u in self.adj:
            g.agregar_nodo(u)
        for u, vec in self.adj.items():
            for v, peso in vec.items():
                g.adj[v][u] = peso
        return g

    def num_aristas(self):
        total = sum(len(v) for v in self.adj.values())
        return total if self.dirigido else total // 2


def bfs(g, origen):
    """Número mínimo de aristas desde `origen` a cada nodo alcanzable."""
    niveles = {origen: 0}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for v in g.adj[u]:
            if v not in niveles:
                niveles[v] = niveles[u] + 1
                cola.append(v)
    return niveles


def componentes_conexas(g):
    """Componentes conexas, de la más grande a la más pequeña (usa BFS)."""
    vistos, resultado = set(), []
    for s in g.adj:
        if s not in vistos:
            comp = set(bfs(g, s))
            vistos |= comp
            resultado.append(comp)
    return sorted(resultado, key=len, reverse=True)


def dijkstra(g, fuentes, objetivos=None, limite=INF):
    """Dijkstra desde una o varias fuentes.

    Devuelve (dist, pred). `dist` solo trae distancias definitivas (nodos cerrados).
    `pred` guarda el padre de cada nodo: con una fuente es un árbol de caminos
    mínimos; con varias es un bosque, con un árbol por fuente.

    Parada temprana (opcional), sin cambiar ninguna distancia que se devuelve:
      - objetivos: se detiene cuando ya cerró todos esos nodos. Dijkstra cierra los
        nodos en orden de distancia, así que lo que falta por explorar no puede
        acortar el camino a un nodo ya cerrado.
      - limite: no cierra nodos a más de esa distancia.

    Una fuente que no está en el grafo (por ejemplo, una esquina que con la obra
    perdió todas sus calles) queda aislada: solo se alcanza a sí misma.
    """
    if not isinstance(fuentes, (list, set, tuple, frozenset)):
        fuentes = [fuentes]
    adj = g.adj
    vacio = {}
    tentativa = {s: 0.0 for s in fuentes}
    pred = {s: None for s in fuentes}
    dist = {}
    heap = [(0.0, s) for s in fuentes]
    heapq.heapify(heap)
    faltan = set(objetivos) if objetivos is not None else None
    sacar, meter = heapq.heappop, heapq.heappush
    while heap:
        d, u = sacar(heap)
        if u in dist:
            continue          # entrada vieja: u ya se cerró con una distancia menor
        if d > limite:
            break
        dist[u] = d
        if faltan is not None:
            faltan.discard(u)
            if not faltan:
                break
        for v, peso in adj.get(u, vacio).items():
            nueva = d + peso
            if nueva < tentativa.get(v, INF):
                tentativa[v] = nueva
                pred[v] = u
                meter(heap, (nueva, v))
    if heap:
        # Se paró antes de tiempo: los nodos sin cerrar no tienen camino definitivo.
        pred = {n: pred[n] for n in dist}
    return dist, pred


def reconstruir_camino(pred, destino):
    """Camino desde la fuente hasta `destino`; lista vacía si no se alcanzó."""
    if destino not in pred:
        return []
    camino = [destino]
    while pred[camino[-1]] is not None:
        camino.append(pred[camino[-1]])
    return camino[::-1]


def centralidad_grado(g):
    """Grado de cada nodo dividido entre n-1."""
    n = len(g.adj)
    if n < 2:
        return {u: 0.0 for u in g.adj}
    return {u: len(v) / (n - 1) for u, v in g.adj.items()}


def centralidad_cercania(g):
    """Cercanía (n_alcanzables - 1) / suma de distancias, dentro de cada componente.

    Se multiplica por la fracción de nodos alcanzables para no premiar a los nodos
    de componentes pequeñas (corrección de Wasserman y Faust).
    """
    n = len(g.adj)
    res = {}
    for u in g.adj:
        dist, _ = dijkstra(g, u)
        total = sum(dist.values())
        alc = len(dist) - 1
        res[u] = (alc / total) * (alc / (n - 1)) if total > 0 and n > 1 else 0.0
    return res


def intermediacion(g):
    """Intermediación ponderada con el algoritmo de Brandes, normalizada a [0, 1]."""
    cb = {u: 0.0 for u in g.adj}
    for s in g.adj:
        pila = []
        predecesores = {u: [] for u in g.adj}
        sigma = {u: 0.0 for u in g.adj}
        sigma[s] = 1.0
        dist = {s: 0.0}
        heap = [(0.0, str(s), s)]
        cerrados = set()
        while heap:
            d, _, u = heapq.heappop(heap)
            if u in cerrados:
                continue
            cerrados.add(u)
            pila.append(u)
            for v, peso in g.adj[u].items():
                nueva = d + peso
                if nueva < dist.get(v, INF) - 1e-9:
                    dist[v] = nueva
                    sigma[v] = sigma[u]
                    predecesores[v] = [u]
                    heapq.heappush(heap, (nueva, str(v), v))
                elif abs(nueva - dist.get(v, INF)) <= 1e-9 and v not in cerrados:
                    sigma[v] += sigma[u]
                    predecesores[v].append(u)
        delta = {u: 0.0 for u in g.adj}
        while pila:
            w = pila.pop()
            for u in predecesores[w]:
                delta[u] += sigma[u] / sigma[w] * (1 + delta[w])
            if w != s:
                cb[w] += delta[w]
    n = len(g.adj)
    # Cada par se cuenta dos veces en un grafo no dirigido.
    escala = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 0.0
    return {u: v * escala for u, v in cb.items()}


# ------------------------------------------------------------ flujo máximo y corte mínimo
_FUENTE, _SUMIDERO = ("fuente virtual",), ("sumidero virtual",)


def flujo_maximo(capacidades, fuentes, sumideros):
    """Flujo máximo de un conjunto de fuentes a un conjunto de sumideros (Edmonds–Karp).

    `capacidades`: {(u, v): c} con c entero >= 0, dirigido (para una calle de doble sentido van los dos
    arcos). Se agrega una fuente virtual unida a cada fuente y un sumidero virtual unido desde cada
    sumidero, con capacidad «infinita» (más que la suma de todas). Cada ronda busca con BFS el camino de
    aumento con menos arcos en la red residual y empuja por él su cuello de botella (Edmonds y Karp, 1972).

    Devuelve dict(valor, corte, alcanzables):
      - valor: el flujo máximo;
      - corte: [(u, v, c)] arcos que van de lo alcanzable desde la fuente en la red residual final hacia lo
        demás. Por el teorema de flujo máximo y corte mínimo (Ford y Fulkerson, 1956), la suma de sus
        capacidades es igual a `valor` y es el corte de capacidad mínima;
      - alcanzables: nodos de ese lado del corte (sin la fuente virtual).
    """
    fuentes, sumideros = set(fuentes), set(sumideros)
    if fuentes & sumideros:
        raise ValueError("Un nodo no puede ser fuente y sumidero a la vez: el flujo sería infinito")
    infinito = sum(max(0, c) for c in capacidades.values()) + 1
    residual = {}

    def arco(u, v, c):
        residual.setdefault(u, {})
        residual.setdefault(v, {})
        residual[u][v] = residual[u].get(v, 0) + c
        residual[v].setdefault(u, 0)

    for (u, v), c in capacidades.items():
        if c > 0 and u != v:
            arco(u, v, c)
    for f in fuentes:
        arco(_FUENTE, f, infinito)
    for t in sumideros:
        arco(t, _SUMIDERO, infinito)

    def bfs_residual():
        padre = {_FUENTE: None}
        cola = deque([_FUENTE])
        while cola:
            u = cola.popleft()
            for v, c in residual.get(u, {}).items():
                if c > 0 and v not in padre:
                    padre[v] = u
                    if v == _SUMIDERO:
                        return padre
                    cola.append(v)
        return padre

    valor = 0
    while True:
        padre = bfs_residual()
        if _SUMIDERO not in padre:
            break
        camino, v = [], _SUMIDERO
        while padre[v] is not None:
            camino.append((padre[v], v))
            v = padre[v]
        empuje = min(residual[u][v] for u, v in camino)
        for u, v in camino:
            residual[u][v] -= empuje
            residual[v][u] += empuje
        valor += empuje

    alcanzables = set(padre) - {_FUENTE}
    corte = sorted(((u, v, c) for (u, v), c in capacidades.items()
                    if c > 0 and u in alcanzables and v not in alcanzables), key=lambda x: (str(x[0]), str(x[1])))
    return dict(valor=valor, corte=corte, alcanzables=alcanzables)
