"""Análisis de un arroyo cualquiera y de las medidas temporales mientras se canaliza.

Pasos:
  1. Clasificar los tramos que tocan el arroyo: bloqueados con lluvia o puentes.
  2. Escenario seco (red completa) y escenario de lluvia (sin los tramos bloqueados).
  3. Zona de estudio: esquinas a cada lado del arroyo, a menos de `radio` metros.
  4. Desvío de cada par (a, b) de lados opuestos:  d_lluvia(a, b) - d_seco(a, b).
  5. Cruces cerrados: pares de esquinas secas, en lados opuestos, que en seco se
     unían por tramos que la lluvia bloquea.
  6. Tres medidas, cada una para quien la usa:
       - Puente peatonal  -> grafo de peatones (no dirigido).
       - Doble sentido    -> grafo de vehículos (dirigido): una calle de un solo
                             sentido pasa a doble sentido mientras dure la obra.
       - Ruta alterna     -> camino mínimo con lluvia para cada cruce cerrado.
     Las dos primeras se eligen con una heurística voraz: en cada ronda se prueba
     cada candidato y se queda el que más reduce el desvío medio.
"""
import math
from dataclasses import asdict, dataclass

from src.geometria import Arroyo, orientar, proyectar, se_cruzan
from src.grafo import INF, Grafo, dijkstra, reconstruir_camino

TOLERANCIA_M = 10      # una calle a menos de esto del cauce se considera dentro de él
FRACCION_SOBRE = 0.6   # fracción de la calle que debe ir por el cauce para decir "va sobre él"
UMBRAL_M = 200         # desvío que consideramos "grande"
LUZ_MAX_M = 60         # longitud máxima de un puente peatonal nuevo (donde no hay calle)
MAX_POR_LADO = 120     # esquinas de muestra por lado, para que el cálculo tarde segundos
MAX_RUTAS = 15
MEJORA_MIN = 0.02     # una medida se recomienda solo si baja el desvío medio al menos 2 %


# ---------------------------------------------------------------- 1. contacto
def clasificar(red, arroyo, abiertos=(), cerrados=()):
    """Devuelve {id_tramo: (estado, motivo)} para todo tramo en contacto con el arroyo.

    estado: "bloqueado" o "puente".  motivo: "cruza", "sobre" o "esquina".
    Una esquina a menos de TOLERANCIA_M del cauce se considera inundada: todos
    sus tramos se bloquean, salvo que sea el extremo de un puente.
    """
    xy = red.plano.xy
    contacto = {}
    for t in red.tramos:
        pts = [xy(p) for p in t.forma]
        segs = set()
        for a, b in zip(pts, pts[1:]):
            segs |= arroyo.cercanos(a, b, TOLERANCIA_M)
        if not segs:
            continue
        segs = [arroyo.segmentos[i] for i in segs]
        cruza = any(se_cruzan(a, b, c, d) for a, b in zip(pts, pts[1:]) for c, d in segs)
        muestras = []
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 5))
            muestras += [(a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n) for j in range(n + 1)]
        cerca = sum(min(proyectar(q, c, d)[0] for c, d in segs) < TOLERANCIA_M for q in muestras)
        sobre = cerca / len(muestras) > FRACCION_SOBRE
        if cruza or sobre:
            contacto[t.id] = ("puente" if t.puente else "bloqueado", "cruza" if cruza else "sobre")

    extremos_puente = {n for t in red.tramos if t.puente and t.id in contacto for n in (t.u, t.v)}
    inundadas = {n for n, p in red.pos.items()
                 if n not in extremos_puente and arroyo.cercanos(xy(p), xy(p), TOLERANCIA_M)
                 and arroyo.ubicar(xy(p))[0] < TOLERANCIA_M}
    for t in red.tramos:
        if t.id not in contacto and (t.u in inundadas or t.v in inundadas) and not t.puente:
            contacto[t.id] = ("bloqueado", "esquina")

    for i in abiertos:
        if i in contacto:
            contacto[i] = ("abierto", contacto[i][1])
    for i in cerrados:
        if i in contacto:
            contacto[i] = ("bloqueado", contacto[i][1])
    return contacto, inundadas


# ------------------------------------------------------------------ 3. zona
def zona(red, arroyo, radio, g_pea, g_veh, inundadas):
    """Esquinas de cada lado del arroyo (todas y una muestra pareja de cada lado)."""
    lados = {1: [], -1: []}
    info = {}
    for n, p in red.pos.items():
        if n in inundadas or n not in g_veh.adj or n not in g_pea.adj or not g_veh.adj[n]:
            continue
        d, lado, extremo = arroyo.ubicar(red.plano.xy(p))
        if TOLERANCIA_M <= d <= radio and not extremo:
            lados[lado].append(n)
            info[n] = (d, lado)

    def muestra(lista):
        lista = sorted(lista)
        if len(lista) <= MAX_POR_LADO:
            return lista
        paso = len(lista) / MAX_POR_LADO
        return [lista[int(i * paso)] for i in range(MAX_POR_LADO)]

    return lados, {k: muestra(v) for k, v in lados.items()}, info


def nombre_lado(red, nodos):
    if not nodos:
        return "sin esquinas"
    lat = sum(red.pos[n][0] for n in nodos) / len(nodos)
    lon = sum(red.pos[n][1] for n in nodos) / len(nodos)
    return lat, lon


def nombres_de_lados(red, lados):
    """'norte'/'sur' u 'oriente'/'occidente', según cómo quedan los dos lados."""
    if not lados[1] or not lados[-1]:
        return {1: "lado A", -1: "lado B"}
    a, b = nombre_lado(red, lados[1]), nombre_lado(red, lados[-1])
    dlat = (a[0] - b[0]) * 110600
    dlon = (a[1] - b[1]) * red.plano.k
    if abs(dlat) >= abs(dlon):
        return {1: "lado norte", -1: "lado sur"} if dlat > 0 else {1: "lado sur", -1: "lado norte"}
    return {1: "lado oriente", -1: "lado occidente"} if dlon > 0 else {1: "lado occidente", -1: "lado oriente"}


# ---------------------------------------------------------------- 4. métricas
@dataclass
class Metricas:
    pares: int              # pares con camino en seco
    sin_camino: int         # pares que con lluvia quedan sin ningún camino
    distancia_media_m: float
    desvio_medio_m: float
    pct_mayor_200m: float
    desvio_max_m: float

    def objetivo(self):
        """Primero importa que nadie quede sin camino; después, el desvío medio."""
        return (self.sin_camino, round(self.desvio_medio_m, 3))


def tablas(g, origenes, objetivos=None):
    """Dijkstra desde cada origen: {origen: {nodo: distancia}}.

    Con `objetivos`, cada Dijkstra se detiene al cerrar todos esos nodos: las
    distancias hacia ellos son exactas y no se explora el resto de la ciudad.
    """
    return {o: dijkstra(g, o, objetivos)[0] for o in origenes}


def medir(F, R, base, pares, arcos=()):
    """Métricas de los pares, opcionalmente agregando arcos nuevos (x, y, peso).

    Con un arco nuevo x -> y, el camino a -> b puede ser a ~> x -> y ~> b, así que
        d_nuevo(a, b) = min(d(a, b), d(a, x) + peso + d(y, b))
    y no hace falta repetir Dijkstra: d(a, x) sale de la tabla F (desde a) y
    d(y, b) de la tabla R (Dijkstra desde b en el grafo invertido).
    """
    n = sin = mayores = 0
    suma = suma_desvio = maximo = 0.0
    for a, b in pares:
        Fa = F[a]
        d = Fa.get(b, INF)
        if arcos:
            Rb = R[b]
            for x, y, w in arcos:
                c = Fa.get(x, INF) + w + Rb.get(y, INF)
                if c < d:
                    d = c
        if d == INF:
            sin += 1
            continue
        n += 1
        desvio = d - base[a][b]
        suma += d
        suma_desvio += desvio
        mayores += desvio > UMBRAL_M
        maximo = max(maximo, desvio)
    c = max(n, 1)
    return Metricas(len(pares), sin, suma / c, suma_desvio / c, 100 * mayores / c, maximo)


class Evaluador:
    """Objetivo (pares sin camino, desvío medio) al agregar arcos, sin recorrer todos los pares.

    Usa la misma fórmula que `medir`, d_nuevo(a, b) = min(d(a, b), d(a, x) + w + d(y, b)),
    pero solo toca los pares que de verdad mejoran:
      - Los pares se agrupan por origen a. Para un arco x -> y, d(a, x) + w se calcula
        una vez por fila, no una vez por par.
      - Cota para descartar filas enteras: si d(a, x) + w + min_b d(y, b) no es menor
        que el par más largo de la fila, el arco no acorta ningún par de esa fila.
      - El desvío medio se actualiza restando lo que se ahorra cada par que mejora.
    El resultado es el mismo que el de `medir`; solo cambia cuánto trabajo se hace.
    """

    def __init__(self, F, R, base, pares):
        self.F, self.R = F, R
        filas = {}
        for a, b in pares:
            filas.setdefault(a, []).append(b)
        self.columnas = sorted({b for _, b in pares})
        self.filas = []
        self.sin = self.n = 0
        self.suma = 0.0
        for a, bs in filas.items():
            Fa = F[a]
            actual = [Fa.get(b, INF) for b in bs]
            seco = [base[a][b] for b in bs]
            for d, s in zip(actual, seco):
                if d == INF:
                    self.sin += 1
                else:
                    self.n += 1
                    self.suma += d - s
            self.filas.append((a, bs, actual, seco, max(actual)))

    def objetivo(self, arcos):
        sin, n, suma = self.sin, self.n, self.suma
        hacia = []
        for x, y, w in arcos:
            ry = {b: self.R[b].get(y, INF) for b in self.columnas}
            minimo = min(ry.values(), default=INF)
            if minimo < INF:
                hacia.append((x, w, ry, minimo))
        if hacia:
            F = self.F
            for a, bs, actual, seco, peor in self.filas:
                Fa = F[a]
                mejoras = None
                for x, w, ry, minimo in hacia:
                    t = Fa.get(x, INF) + w
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
                            n += 1
                            suma += c - seco[j]
                        else:
                            suma -= actual[j] - c
        return (sin, round(suma / max(n, 1), 3))


def extremos(candidatos):
    """Nodos donde empiezan o terminan los arcos candidatos."""
    return {z for _, arcos in candidatos for x, y, _ in arcos for z in (x, y)}


def actualizar_tablas(g, F, R, arcos, objetivos):
    """Tablas F y R del grafo g + arcos, sin repetir Dijkstra desde cada origen.

    Un camino mínimo usa cada arco nuevo x -> y a lo sumo una vez, y lo que va
    antes y después de ese arco es un camino del grafo viejo. Por eso:
        d'(a, v) = min(d(a, v), d(a, x) + w + d(y, v))
        d'(u, b) = min(d(u, b), d(u, x) + w + d(y, b))
    d(y, v) sale de un Dijkstra desde y; d(u, x), de un Dijkstra desde x en el grafo
    invertido. Son 2 Dijkstra por arco en vez de uno por cada origen.
    Las tablas nuevas solo guardan los `objetivos`, que es lo que se consulta.
    """
    desde, hacia = {}, {}
    inv = g.invertido() if g.dirigido else g
    for x, y, _ in arcos:
        if y not in desde:
            desde[y] = dijkstra(g, y, objetivos)[0]
        if g.dirigido and x not in hacia:
            hacia[x] = dijkstra(inv, x, objetivos)[0]

    def nueva_fila(fila, pasos):
        """pasos: [(costo hasta entrar al arco nuevo, distancias desde su salida)]."""
        res = {v: fila[v] for v in objetivos if v in fila}
        for t, salida in pasos:
            if t == INF:
                continue
            for v in objetivos:
                c = t + salida.get(v, INF)
                if c < res.get(v, INF):
                    res[v] = c
        return res

    F2 = {a: nueva_fila(Fa, [(Fa.get(x, INF) + w, desde[y]) for x, y, w in arcos]) for a, Fa in F.items()}
    if not g.dirigido:
        return F2, F2
    R2 = {b: nueva_fila(Rb, [(Rb.get(y, INF) + w, hacia[x]) for x, y, w in arcos]) for b, Rb in R.items()}
    return F2, R2


def voraz(g, origenes, base, pares, candidatos, k, F=None, R=None):
    """Heurística voraz: k rondas; en cada una se agrega el candidato que más mejora.

    `candidatos` es una lista de (info, arcos). F y R son las tablas de Dijkstra del
    grafo inicial (si ya se calcularon, no se repiten). Devuelve [(info, metricas)]:
    las métricas de cada elegido son exactas para el grafo con todos los elegidos
    hasta ese momento, así que las del último son las del escenario final.
    """
    g = g.copia()
    objetivos = set(origenes) | extremos(candidatos)
    elegidos, usados = [], set()
    for _ in range(k):
        if F is None:
            F = tablas(g, origenes, objetivos)
            R = F if not g.dirigido else tablas(g.invertido(), origenes, objetivos)
        ev = Evaluador(F, R, base, pares)
        desvio = ev.suma / max(ev.n, 1)
        # Para recomendar algo debe devolver el camino a alguien o bajar el desvío al menos 2 %.
        umbral = (ev.sin, desvio * (1 - MEJORA_MIN) - 0.5)
        mejor = None
        for i, (info, arcos) in enumerate(candidatos):
            if i in usados:
                continue
            obj = ev.objetivo(arcos)
            if obj < umbral and (mejor is None or obj < mejor[0]):
                mejor = (obj, i, info, arcos)
        if mejor is None:
            break
        _, i, info, arcos = mejor
        # Métricas completas (máximo, % > 200 m) solo para el elegido.
        elegidos.append((info, medir(F, R, base, pares, arcos)))
        usados.add(i)
        if len(elegidos) < k:
            F, R = actualizar_tablas(g, F, R, arcos, objetivos)
        for x, y, w in arcos:
            g.agregar_arista(x, y, w)
    return elegidos, g


# ------------------------------------------------------------- 5. candidatos
def cruces_cerrados(red, arroyo, contacto, inundadas, g_lluvia, vehicular, max_m=200):
    """Cruces que la lluvia cierra: pares (x, y) de esquinas secas en lados opuestos
    que en seco se unían por tramos que ahora están bloqueados.

    Se arma el grafo H solo con los tramos bloqueados. Desde cada esquina seca x
    que toca H se busca, dentro de H, la esquina seca y más cercana del otro lado.
    Devuelve [dict(via, x, y, metros, forma)].
    """
    xy = red.plano.xy
    H = Grafo(dirigido=vehicular)
    tramo_de = {}
    for t in red.tramos:
        if contacto.get(t.id, ("",))[0] != "bloqueado" or not (t.vehicular if vehicular else t.peatonal):
            continue
        if vehicular:
            if t.sentido >= 0:
                H.agregar_arista(t.u, t.v, t.metros)
            if t.sentido <= 0:
                H.agregar_arista(t.v, t.u, t.metros)
        else:
            H.agregar_arista(t.u, t.v, t.metros)
        for a, b in ((t.u, t.v), (t.v, t.u)):
            if (a, b) not in tramo_de or t.metros < tramo_de[(a, b)].metros:
                tramo_de[(a, b)] = t
    secas = [n for n in H.adj if n not in inundadas and g_lluvia.adj.get(n)]
    lado = {n: arroyo.ubicar(xy(red.pos[n]))[1] for n in secas}
    res, vistos = [], set()
    for x in secas:
        dist, pred = dijkstra(H, x, limite=max_m)
        opuestas = [(d, y) for y, d in dist.items() if y in lado and lado[y] != lado[x] and d <= max_m]
        if not opuestas:
            continue
        d, y = min(opuestas)
        clave = (x, y) if vehicular else tuple(sorted((x, y)))
        if clave in vistos:
            continue
        vistos.add(clave)
        camino = reconstruir_camino(pred, y)
        forma = []
        for a, b in zip(camino, camino[1:]):
            t = tramo_de[(a, b)]
            trozo = t.forma if t.u == a else t.forma[::-1]
            forma += trozo if not forma else trozo[1:]
        vias = [tramo_de[(a, b)].via for a, b in zip(camino, camino[1:]) if tramo_de[(a, b)].via]
        res.append(dict(via=vias[0] if vias else red.nombre(x), x=x, y=y, metros=round(d, 1), forma=forma))
    return res


def candidatos_puente_peatonal(red, arroyo, cruces, lados_todos, g_lluvia, luz_max):
    """Lugares posibles para un puente peatonal, de dos tipos:

    - "cruce": un cruce que la lluvia cierra (calle que pasa por el arroyo o esquina
      inundada). El puente devuelve a los peatones ese mismo paso.
    - "nuevo": dos esquinas de lados opuestos a menos de `luz_max` metros en línea
      recta, donde hoy no hay ninguna calle que cruce.
    """
    xy = red.plano.xy
    cand, vistos = [], set()

    def agregar(tipo, via, x, y, peso, forma):
        par = tuple(sorted((x, y)))
        if par in vistos or x == y:
            return
        vistos.add(par)
        info = dict(tipo=tipo, via=via, desde=red.nombre(x), hasta=red.nombre(y),
                    recorrido_m=round(peso), forma=[list(p) for p in forma])
        cand.append((info, [(x, y, peso), (y, x, peso)]))

    for c in cruces:
        agregar("cruce", c["via"], c["x"], c["y"], c["metros"], c["forma"])

    cerca = {s: [n for n in lados_todos[s] if arroyo.ubicar(xy(red.pos[n]))[0] <= luz_max] for s in (1, -1)}
    for x in cerca[1]:
        mejor, dmin = None, INF
        for y in cerca[-1]:
            d = red.plano.dist(red.pos[x], red.pos[y])
            if d < dmin:
                mejor, dmin = y, d
        if mejor is not None and dmin <= luz_max and mejor not in g_lluvia.adj.get(x, {}) \
                and arroyo.corta(xy(red.pos[x]), xy(red.pos[mejor])):
            agregar("nuevo", "", x, mejor, dmin, [red.pos[x], red.pos[mejor]])
    return cand


def candidatos_doble_sentido(red, arroyo, contacto, inundadas, radio):
    """Calles de un solo sentido, cerca del arroyo, que podrían habilitarse en doble sentido."""
    xy = red.plano.xy
    cand = []
    for t in red.tramos:
        if not t.vehicular or t.sentido == 0 or t.id in contacto:
            continue
        if t.u in inundadas or t.v in inundadas:
            continue
        medio = t.forma[len(t.forma) // 2]
        if arroyo.ubicar(xy(medio))[0] > radio:
            continue
        # Arco que hoy NO existe: el sentido contrario al permitido.
        x, y = (t.v, t.u) if t.sentido == 1 else (t.u, t.v)
        hoy = t.forma if t.sentido == 1 else t.forma[::-1]
        info = dict(via=t.via or "calle sin nombre", desde=red.nombre(t.u if t.sentido == 1 else t.v),
                    hasta=red.nombre(t.v if t.sentido == 1 else t.u), metros=round(t.metros),
                    forma=[list(p) for p in hoy])
        cand.append((info, [(x, y, t.metros)]))
    return cand


# -------------------------------------------------------------- ruta alterna
def rutas_alternas(red, cruces_v, cruces_p, g_veh_lluvia, g_pea_lluvia):
    """Para cada cruce cerrado, el camino mínimo con lluvia (lo que habría que señalizar)."""
    rutas = {}
    for cruces, g, clave, vehicular in ((cruces_v, g_veh_lluvia, "carro", True),
                                        (cruces_p, g_pea_lluvia, "pie", False)):
        for c in cruces:
            y = c["y"]
            dist, pred = dijkstra(g, c["x"], objetivos={y})
            if y in dist:
                camino = reconstruir_camino(pred, y)
                dibujo = []
                for a, b in zip(camino, camino[1:]):
                    trozo = red.forma_arco(a, b, solo_vehicular=vehicular)
                    dibujo += trozo if not dibujo else trozo[1:]
                dato = dict(seco_m=round(c["metros"]), lluvia_m=round(dist[y]),
                            desde=red.nombre(c["x"]), hasta=red.nombre(y),
                            cerrado=[list(p) for p in c["forma"]], forma=[list(p) for p in dibujo])
            else:
                dato = dict(seco_m=round(c["metros"]), lluvia_m=None, desde=red.nombre(c["x"]),
                            hasta=red.nombre(y), cerrado=[list(p) for p in c["forma"]], forma=[])
            r = rutas.setdefault(c["via"], dict(via=c["via"]))
            # Por cada calle cerrada se muestra el cruce con el mayor desvío.
            if clave not in r or extra(dato) > extra(r[clave]):
                r[clave] = dato
    lista = sorted(rutas.values(), key=lambda r: -max(extra(r.get("carro")), extra(r.get("pie"))))
    return lista[:MAX_RUTAS]


def extra(dato):
    if dato is None:
        return -1
    if dato["lluvia_m"] is None:
        return -0.5  # sin ruta posible: casi siempre una calle ciega; va al final
    return dato["lluvia_m"] - dato["seco_m"]


# ------------------------------------------------------------------ principal
def analizar(red, lineas, radio=400, luz_max=LUZ_MAX_M, k=1, abiertos=(), cerrados=()):
    lineas = orientar(lineas)
    arroyo = Arroyo(lineas, red.plano)
    contacto, inundadas = clasificar(red, arroyo, set(abiertos), set(cerrados))
    excluir = {i for i, (estado, _) in contacto.items() if estado == "bloqueado"}

    pea_seco, pea_lluvia = red.grafo_peatones(), red.grafo_peatones(excluir)
    veh_seco, veh_lluvia = red.grafo_vehiculos(), red.grafo_vehiculos(excluir)

    lados_todos, lados, _ = zona(red, arroyo, radio, pea_seco, veh_seco, inundadas)
    nombres = nombres_de_lados(red, lados_todos)
    avisos = []
    if len(lados[1]) < 3 or len(lados[-1]) < 3:
        avisos.append("Hay muy pocas esquinas a uno de los lados del arroyo. Dibuje un tramo "
                      "más largo o aumente el radio.")

    origenes = sorted(set(lados[1]) | set(lados[-1]))
    resultado = dict(
        arroyo=dict(longitud_m=round(arroyo.longitud()), lineas=[[list(p) for p in l] for l in lineas]),
        red=dict(esquinas=len(red.pos), tramos=len(red.tramos),
                 bloqueados=len(excluir), puentes=sum(1 for e, _ in contacto.values() if e == "puente"),
                 esquinas_inundadas=len(inundadas)),
        zona=dict(radio_m=radio, lados={nombres[s]: len(lados_todos[s]) for s in (1, -1)},
                  muestra={nombres[s]: len(lados[s]) for s in (1, -1)}),
        contacto=[dict(id=i, via=red.tramos[i].via or "calle sin nombre", estado=e, motivo=m,
                       forma=[list(p) for p in red.tramos[i].forma])
                  for i, (e, m) in sorted(contacto.items())],
        avisos=avisos,
    )
    if not origenes or avisos:
        resultado.update(peatones=None, vehiculos=None, rutas=[])
        return resultado

    def propuestas(elegidos):
        return [dict(orden=i + 1, **info, desvio_medio_m=round(m.desvio_medio_m, 1), sin_camino=m.sin_camino)
                for i, (info, m) in enumerate(elegidos)]

    # Cada tabla de Dijkstra se calcula una sola vez y se para al llegar a los nodos
    # que se necesitan: las esquinas de la muestra y los extremos de los candidatos.

    # ---- Peatones: no dirigido, pares de un lado al otro.
    # En seco solo hace falta d(a, b) con a del primer lado: Dijkstra desde ese lado.
    Fs = tablas(pea_seco, lados[1], objetivos=set(lados[-1]))
    pares_p = [(a, b) for a in lados[1] for b in lados[-1] if b in Fs[a]]
    cruces_p = cruces_cerrados(red, arroyo, contacto, inundadas, pea_lluvia, vehicular=False)
    cruces_v = cruces_cerrados(red, arroyo, contacto, inundadas, veh_lluvia, vehicular=True)
    cand_p = candidatos_puente_peatonal(red, arroyo, cruces_p, lados_todos, pea_lluvia, luz_max)
    # Con lluvia hacen falta los dos lados: d(y, b) sale de la tabla de b (no dirigido: R = F).
    Fl = tablas(pea_lluvia, origenes, objetivos=set(origenes) | extremos(cand_p))
    elegidos_p, _ = voraz(pea_lluvia, origenes, Fs, pares_p, cand_p, k, F=Fl, R=Fl)
    lluvia_p = medir(Fl, Fl, Fs, pares_p)
    resultado["peatones"] = dict(
        seco=asdict(medir(Fs, Fs, Fs, pares_p)), lluvia=asdict(lluvia_p),
        con_medida=asdict(elegidos_p[-1][1] if elegidos_p else lluvia_p), candidatos=len(cand_p),
        propuestas=propuestas(elegidos_p))

    # ---- Vehículos: dirigido, pares en los dos sentidos.
    pares_v = [(a, b) for a in lados[1] for b in lados[-1]] + [(b, a) for a in lados[1] for b in lados[-1]]
    Vs = tablas(veh_seco, origenes, objetivos=set(origenes))
    pares_v = [(a, b) for a, b in pares_v if b in Vs[a]]
    cand_v = candidatos_doble_sentido(red, arroyo, contacto, inundadas, radio)
    objetivos_v = set(origenes) | extremos(cand_v)
    Vl = tablas(veh_lluvia, origenes, objetivos_v)
    Rl = tablas(veh_lluvia.invertido(), origenes, objetivos_v)
    elegidos_v, _ = voraz(veh_lluvia, origenes, Vs, pares_v, cand_v, k, F=Vl, R=Rl)
    lluvia_v = medir(Vl, Rl, Vs, pares_v)
    resultado["vehiculos"] = dict(
        seco=asdict(medir(Vs, Vs, Vs, pares_v)), lluvia=asdict(lluvia_v),
        con_medida=asdict(elegidos_v[-1][1] if elegidos_v else lluvia_v), candidatos=len(cand_v),
        propuestas=propuestas(elegidos_v))
    if not cand_v:
        avisos.append("En OpenStreetMap no hay calles de un solo sentido registradas cerca de este "
                      "arroyo, así que no se puede proponer un cambio de sentido.")

    resultado["rutas"] = rutas_alternas(red, cruces_v, cruces_p, veh_lluvia, pea_lluvia)
    return resultado
