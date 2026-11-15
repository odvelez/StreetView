"""Plan de obra por etapas: cómo hacer una obra que cierra calles sin parar la movilidad.

Idea: una obra larga no se hace de una vez. Se divide en etapas a lo largo del eje de la obra y,
mientras se trabaja en una etapa, solo se cierran los cruces de ese tramo; el resto de la
ciudad sigue abierta. Para cada etapa el programa calcula:

  - el desvío que causa el cierre (peatones: grafo no dirigido; vehículos: grafo dirigido),
  - los pasos peatonales provisionales: uno por cada `un_puente_cada_m` metros de obra
    (mínimo uno), repartidos a lo largo del tramo,
  - las calles a pasar a doble sentido mientras dure la etapa,
  - las rutas alternas que hay que señalizar en cada cruce cerrado,
  - las esquinas que reciben más recorridos desviados (la carga), que son las candidatas
    a control de tráfico (semáforo o agente), con la información de si ya tienen semáforo.

Cuántas etapas hay depende de lo largo de la obra: n = ceil(longitud / etapa_max_m). Los cortes
se eligen con programación dinámica para que ninguna etapa concentre demasiados cruces y
ninguna pase de `etapa_max_m`.

Qué NO hace (y debe decirse): no hay datos de volumen de tránsito, así que la «carga» no es
congestión: es cuántos recorridos desviados pasan por la esquina. Tampoco diseña carriles ni
tiempos de semáforo. Es el mismo modelo de conectividad del resto del proyecto.

Diferencia con `analisis.analizar` (toda la obra a la vez, sin etapas): aquí, en cada etapa, se
cierran todos los tramos que tocan la franja de obra dentro del tramo en obra, incluidos los
puentes existentes (calles que la obra podría mantener abiertas), porque la obra los intervendría.
Con `cerrar_puentes=False` los puentes existentes se mantienen abiertos.

Nombres heredados del JSON (no se quitan para no romper la pantalla): la clave `arroyo` del plan
(ahora también está como `obra`), `cauce` en cada etapa (ahora también `eje`) y `lluvia_m` en
las rutas (el recorrido con la obra).
"""
import bisect
import math
from dataclasses import asdict

from src import osm
from src.analisis import (MEJORA_MIN, MAX_POR_LADO, LUZ_MAX_M, TOLERANCIA_M, candidatos_doble_sentido,
                          candidatos_puente_peatonal, clasificar, cruces_cerrados, extremos,
                          medir, rutas_alternas, tablas, voraz, zona)
from src.geometria import Obra, orientar
from src.grafo import INF, dijkstra

ETAPA_MAX_M = 1000         # largo máximo de una etapa de obra
UN_PUENTE_CADA_M = 500     # un paso peatonal provisional por cada tanto de obra (mínimo uno)
VENTANA_M = 250            # esquinas a esta distancia, a lo largo del eje, de la etapa, cuentan
MAX_POR_LADO_ETAPA = 60    # muestra de esquinas por lado en cada etapa
MAX_SENTIDOS = 2           # calles a pasar a doble sentido en cada etapa, como máximo
TOP_CARGA = 5              # esquinas con más recorridos desviados que se listan por etapa
MAX_RUTAS_ETAPA = 6
PASO_CORTE_M = 25          # los cortes entre etapas se buscan cada tanto
RADIO_SEMAFORO_M = 40      # un semáforo a menos de esto de la esquina cuenta como suyo
SEPARACION_SENTIDOS_M = 150
# Formas de medir los recorridos. "lados": pares de esquinas de un lado al otro de la obra (como
# siempre). "afectados" (R7, opcional) aún no está hecho.
MEDICIONES = ("lados",)


# ------------------------------------------------------------ longitud y cortes
def puentes_por_longitud(longitud_m, un_puente_cada_m=UN_PUENTE_CADA_M):
    """Pasos peatonales provisionales para una etapa: uno por cada `un_puente_cada_m`, mínimo uno."""
    return max(1, round(longitud_m / un_puente_cada_m))


def numero_de_etapas(longitud_m, etapa_max_m=ETAPA_MAX_M):
    return max(1, math.ceil(longitud_m / etapa_max_m - 1e-9))


def cortes(longitud_m, posiciones, etapa_max_m=ETAPA_MAX_M, paso_m=PASO_CORTE_M):
    """Posiciones (m desde el inicio del eje) donde empieza cada etapa, más el final.

    Se eligen n = ceil(longitud / etapa_max_m) etapas. Programación dinámica sobre una malla de
    posibles cortes: ninguna etapa pasa de etapa_max_m ni queda muy corta, y se minimiza primero
    el mayor número de cruces en una sola etapa y después la suma de cuadrados (reparto parejo).
    `posiciones` son las posiciones, a lo largo del eje, de los cruces que se cerrarían.
    """
    etapa_max_m = max(paso_m, int(etapa_max_m // paso_m) * paso_m)
    n = numero_de_etapas(longitud_m, etapa_max_m)
    if n == 1:
        return [0.0, longitud_m]
    malla = [k * paso_m for k in range(int(longitud_m // paso_m) + 1) if k * paso_m < longitud_m] + [longitud_m]
    pos = sorted(posiciones)
    minimo = min(0.4 * etapa_max_m, longitud_m / n)

    def cuenta(i, j):
        return bisect.bisect_left(pos, malla[j]) - bisect.bisect_left(pos, malla[i])

    mejor = [{0: ((0, 0), None)}]          # mejor[s][j] = (costo, índice previo) con s etapas hasta malla[j]
    for s in range(1, n + 1):
        actual = {}
        for j in range(1, len(malla)):
            for i, (costo_prev, _) in mejor[s - 1].items():
                largo = malla[j] - malla[i]
                if largo > etapa_max_m + 1e-9 or largo < minimo - 1e-9:
                    continue
                c = cuenta(i, j)
                costo = (max(costo_prev[0], c), costo_prev[1] + c * c)
                if j not in actual or costo < actual[j][0]:
                    actual[j] = (costo, i)
        mejor.append(actual)
    j, resultado = len(malla) - 1, []
    if j not in mejor[n]:      # no debería pasar; por si acaso, etapas iguales
        return [longitud_m * k / n for k in range(n + 1)]
    for s in range(n, 0, -1):
        resultado.append(malla[j])
        j = mejor[s][j][1]
    resultado.append(malla[0])
    return resultado[::-1]


def muestrear(lista, n):
    lista = sorted(lista)
    if len(lista) <= n:
        return lista
    paso = len(lista) / n
    return [lista[int(i * paso)] for i in range(n)]


def recorte_del_eje(lineas, obra, p0, p1):
    """Puntos (lat, lon) del eje de la obra entre las posiciones p0 y p1 (metros desde el inicio)."""
    pares = [(l[i], l[i + 1]) for l in lineas if len(l) >= 2 for i in range(len(l) - 1)]
    puntos = []
    for (a, b), ((ax, ay), (bx, by)), inicio in zip(pares, obra.segmentos, obra.inicio_segmento):
        largo = math.hypot(bx - ax, by - ay)
        fin = inicio + largo
        if fin < p0 or inicio > p1 or largo == 0:
            continue
        t0, t1 = max(0.0, (p0 - inicio) / largo), min(1.0, (p1 - inicio) / largo)
        for t in (t0, t1):
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if not puntos or puntos[-1] != p:
                puntos.append(p)
    return [list(p) for p in puntos]


recorte_del_cauce = recorte_del_eje   # nombre anterior


# ----------------------------------------------------------------- una etapa
def _punto_medio(forma):
    return forma[len(forma) // 2]


def _formato_propuestas(elegidos):
    return [dict(orden=i + 1, **info, desvio_medio_m=round(m.desvio_medio_m, 1),
                 desvio_fijo_m=round(m.desvio_fijo_m, 1), sin_camino=m.sin_camino)
            for i, (info, m) in enumerate(elegidos)]


def carga_de_desvios(g_obra, tablas_seco, tablas_obra, pares):
    """Cuántos recorridos desviados pasan por cada esquina (sin contar origen ni destino).

    Un par está desviado si con la obra su camino mide más de 1 m que en seco. Se recorre el camino
    mínimo con la obra de cada par desviado y se suma 1 a cada esquina intermedia.
    """
    desviados = {}
    for a, b in pares:
        d = tablas_obra[a].get(b, INF)
        if d < INF and d - tablas_seco[a][b] > 1.0:
            desviados.setdefault(a, set()).add(b)
    carga, total = {}, 0
    for a, destinos in desviados.items():
        dist, pred = dijkstra(g_obra, a, objetivos=destinos)
        for b in destinos:
            if b not in pred:
                continue
            total += 1
            n = pred[b]
            while n is not None and n != a:
                carga[n] = carga.get(n, 0) + 1
                n = pred[n]
    return carga, total


def evaluar_etapa(ctx, numero, p0, p1, cerrados_ids, luz_max, un_puente_cada_m, radio):
    """Todo el análisis de una etapa: desvío, pasos peatonales, doble sentido, rutas y carga."""
    red, obra = ctx["red"], ctx["obra"]
    xy = red.plano.xy
    contacto_e = {i: ("bloqueado", ctx["contacto"][i][1]) for i in cerrados_ids}
    longitud = p1 - p0
    estructurales = [i for i in cerrados_ids if ctx["contacto"][i][1] in ("cruza", "sobre")]
    eje = recorte_del_eje(ctx["lineas"], obra, p0, p1)
    resultado = dict(
        numero=numero, inicio_m=round(p0), fin_m=round(p1), longitud_m=round(longitud),
        cauce=eje, eje=eje,            # `cauce` es el nombre heredado; se conserva hasta la limpieza final
        tramos_cerrados=sorted(cerrados_ids), cruces_cerrados=len(estructurales),
        puentes_existentes_cerrados=sum(1 for i in cerrados_ids if red.tramos[i].puente),
        puentes_necesarios=puentes_por_longitud(longitud, un_puente_cada_m),
        avisos=[], peatones=None, vehiculos=None, rutas=[], carga=[])

    lo, hi = p0 - VENTANA_M, p1 + VENTANA_M
    lados_w = {s: [n for n in ctx["lados_todos"][s] if lo <= ctx["pos_nodo"][n] <= hi] for s in (1, -1)}
    muestra = {s: muestrear(lados_w[s], MAX_POR_LADO_ETAPA) for s in (1, -1)}
    if len(muestra[1]) < 3 or len(muestra[-1]) < 3:
        resultado["avisos"].append("Hay muy pocas esquinas cerca de esta etapa para medir el desvío.")
        return resultado
    origenes = sorted(set(muestra[1]) | set(muestra[-1]))

    # Grafos de la obra: la red sin los tramos cerrados (armados desde la red para respetar
    # tramos paralelos entre las mismas esquinas).
    pea_obra, veh_obra = red.grafo_peatones(set(cerrados_ids)), red.grafo_vehiculos(set(cerrados_ids))

    def en_etapa(info):
        return p0 - 100 <= info["pos_m"] <= p1 + 100

    cruces_p = cruces_cerrados(red, obra, contacto_e, ctx["inundadas"], pea_obra, vehicular=False)
    cruces_v = cruces_cerrados(red, obra, contacto_e, ctx["inundadas"], veh_obra, vehicular=True)

    # ---- peatones
    Fs = tablas(ctx["pea_seco"], muestra[1], objetivos=set(muestra[-1]))
    pares_p = [(a, b) for a in muestra[1] for b in muestra[-1] if b in Fs[a]]
    cand_p = candidatos_puente_peatonal(red, obra, cruces_p, lados_w, pea_obra, luz_max)
    for info, _ in cand_p:
        info["pos_m"] = round(obra.posicion(xy(_punto_medio(info["forma"]))))
    cand_p = [c for c in cand_p if en_etapa(c[0])]
    Fl = tablas(pea_obra, origenes, objetivos=set(origenes) | extremos(cand_p))
    sep = un_puente_cada_m / 2
    elegidos_p, _ = voraz(pea_obra, origenes, Fs, pares_p, cand_p, resultado["puentes_necesarios"], F=Fl, R=Fl,
                          mejora_min=0.0, incompatibles=lambda a, b: abs(a["pos_m"] - b["pos_m"]) < sep)
    obra_p = medir(Fl, Fl, Fs, pares_p)
    final_p = elegidos_p[-1][1] if elegidos_p else obra_p
    resultado["peatones"] = dict(
        pares=len(pares_p), obra=asdict(obra_p), con_puentes=asdict(final_p), candidatos=len(cand_p),
        puentes=_formato_propuestas(elegidos_p))
    if len(elegidos_p) < resultado["puentes_necesarios"]:
        resultado["avisos"].append(
            f"Por el largo de la etapa corresponden {resultado['puentes_necesarios']} "
            f"{plural(resultado['puentes_necesarios'], 'paso peatonal', 'pasos peatonales')}, pero solo "
            f"{len(elegidos_p)} {plural(len(elegidos_p), 'reduce', 'reducen')} el desvío.")

    # ---- vehículos
    pares_v = [(a, b) for a in muestra[1] for b in muestra[-1]] + [(b, a) for a in muestra[1] for b in muestra[-1]]
    Vs = tablas(ctx["veh_seco"], origenes, objetivos=set(origenes))
    pares_v = [(a, b) for a, b in pares_v if b in Vs[a]]
    cand_v = candidatos_doble_sentido(red, obra, contacto_e, ctx["inundadas"], radio)
    for info, _ in cand_v:
        info["pos_m"] = round(obra.posicion(xy(_punto_medio(info["forma"]))))
    cand_v = [c for c in cand_v if en_etapa(c[0])]
    objetivos_v = set(origenes) | extremos(cand_v)
    Vl = tablas(veh_obra, origenes, objetivos_v)
    Rl = tablas(veh_obra.invertido(), origenes, objetivos_v)
    elegidos_v, _ = voraz(veh_obra, origenes, Vs, pares_v, cand_v, MAX_SENTIDOS, F=Vl, R=Rl,
                          incompatibles=lambda a, b: abs(a["pos_m"] - b["pos_m"]) < SEPARACION_SENTIDOS_M)
    obra_v = medir(Vl, Rl, Vs, pares_v)
    final_v = elegidos_v[-1][1] if elegidos_v else obra_v
    resultado["vehiculos"] = dict(
        pares=len(pares_v), obra=asdict(obra_v), con_medidas=asdict(final_v), candidatos=len(cand_v),
        recuperados=obra_v.sin_camino - final_v.sin_camino, medidas=_formato_propuestas(elegidos_v))

    # ---- rutas alternas y carga de desvíos
    resultado["rutas"] = rutas_alternas(red, cruces_v, cruces_p, veh_obra, pea_obra)[:MAX_RUTAS_ETAPA]
    carga, total = carga_de_desvios(veh_obra, Vs, Vl, pares_v)
    senales = ctx["semaforos"]
    top, nombres = [], set()
    for n, c in sorted(carga.items(), key=lambda x: -x[1]):      # una esquina por nombre de calle
        if red.nombre(n) not in nombres:
            nombres.add(red.nombre(n))
            top.append((n, c))
        if len(top) == TOP_CARGA:
            break
    for n, c in top:
        con = None
        if senales is not None:
            con = any(red.plano.dist(red.pos[n], p) <= RADIO_SEMAFORO_M for p in senales.values())
        resultado["carga"].append(dict(
            esquina=n, nombre=red.nombre(n), posicion=list(red.pos[n]), recorridos=c,
            porcentaje=round(100 * c / max(total, 1), 1), semaforo=con))
    resultado["recorridos_desviados"] = total
    return resultado


# ---------------------------------------------------------------- el plan
def plan_por_etapas(red, lineas, radio=400, luz_max=LUZ_MAX_M, etapa_max_m=ETAPA_MAX_M,
                    un_puente_cada_m=UN_PUENTE_CADA_M, abiertos=(), cerrados=(), recuadro=None,
                    cerrar_puentes=True, ancho_m=TOLERANCIA_M, medicion="lados"):
    """Plan de obra por etapas para la obra `lineas` (su eje). Devuelve un dict listo para JSON.

    `abiertos` y `cerrados` son ids de tramos que el usuario corrigió (como en `analizar`).
    `recuadro` (sur, oeste, norte, este) permite saber qué esquinas ya tienen semáforo.
    `cerrar_puentes`: si la obra también cierra los puentes que ya existen en el tramo (por defecto sí,
    porque hay que intervenirlos). Con False solo se cierran los cruces a nivel.
    `ancho_m`: ancho de la franja de obra, medido desde el eje (ver `analisis.clasificar`). Con el
    valor por defecto (10 m) el resultado es el de siempre.
    `medicion`: cómo se miden los recorridos. Por ahora solo "lados" (pares de esquinas de un lado
    al otro de la obra); cualquier otro valor es un error.
    """
    if medicion not in MEDICIONES:
        raise ValueError(f"medicion={medicion!r} no existe. Use una de: {', '.join(MEDICIONES)}.")
    lineas = orientar(lineas)
    obra = Obra(lineas, red.plano)
    contacto, inundadas = clasificar(red, obra, set(abiertos), set(cerrados), ancho_m)
    xy = red.plano.xy
    pea_seco, veh_seco = red.grafo_peatones(), red.grafo_vehiculos()
    lados_todos, _, _ = zona(red, obra, radio, pea_seco, veh_seco, inundadas, ancho_m)
    pos_nodo = {n: obra.posicion(xy(red.pos[n])) for s in (1, -1) for n in lados_todos[s]}
    longitud = obra.longitud()

    # tramos que la obra cerraría, con su posición a lo largo del eje
    cerrables = {i: obra.posicion(xy(_punto_medio(red.tramos[i].forma)))
                 for i, (estado, _) in contacto.items()
                 if estado == "bloqueado" or (cerrar_puentes and estado == "puente")}
    posiciones_cruces = [p for i, p in cerrables.items() if contacto[i][1] in ("cruza", "sobre")]
    # (los puentes que no se cierran tampoco cuentan para repartir las etapas)
    limites = cortes(longitud, posiciones_cruces, etapa_max_m)

    ctx = dict(red=red, obra=obra, lineas=lineas, contacto=contacto, inundadas=inundadas,
               lados_todos=lados_todos, pos_nodo=pos_nodo, pea_seco=pea_seco, veh_seco=veh_seco,
               semaforos=osm.semaforos(recuadro) if recuadro else None)
    etapas = []
    for k in range(len(limites) - 1):
        p0, p1 = limites[k], limites[k + 1]
        ultimo = k == len(limites) - 2
        ids = [i for i, p in cerrables.items() if p0 <= p < p1 or (ultimo and p >= p1)]
        etapas.append(evaluar_etapa(ctx, k + 1, p0, p1, ids, luz_max, un_puente_cada_m, radio))

    datos_obra = dict(longitud_m=round(longitud), lineas=[[list(p) for p in l] for l in lineas])
    plan = dict(
        arroyo=datos_obra, obra=datos_obra,      # `arroyo` es el nombre heredado
        parametros=dict(radio_m=radio, luz_max_m=luz_max, etapa_max_m=etapa_max_m, un_puente_cada_m=un_puente_cada_m,
                        cerrar_puentes=cerrar_puentes, ancho_m=ancho_m, medicion=medicion),
        etapas=etapas, semaforos_conocidos=None if ctx["semaforos"] is None else len(ctx["semaforos"]))
    plan["resumen"] = resumen_del_plan(plan)
    plan["pasos"] = pasos_del_plan(plan)
    return plan


def resumen_del_plan(plan):
    e = plan["etapas"]
    puentes = sum(len((x["peatones"] or {}).get("puentes", [])) for x in e)
    sentidos = sum(len((x["vehiculos"] or {}).get("medidas", [])) for x in e)
    rutas = sum(len(x["rutas"]) for x in e)
    esquinas = sum(len(x["carga"]) for x in e)
    sin_semaforo = sum(1 for x in e for c in x["carga"] if c["semaforo"] is False)
    peor = max(e, key=lambda x: (x["peatones"] or {}).get("obra", {}).get("desvio_medio_m", 0), default=None)
    return dict(etapas=len(e), longitud_m=plan["obra"]["longitud_m"], puentes_peatonales=puentes,
                cambios_de_sentido=sentidos, rutas_alternas=rutas, esquinas_de_control=esquinas,
                esquinas_sin_semaforo=sin_semaforo, etapa_mas_dificil=peor["numero"] if peor else None)


# ------------------------------------------------------------ paso a paso
def _limites(puntos, margen=0.0015):
    lats, lons = [p[0] for p in puntos], [p[1] for p in puntos]
    return [[min(lats) - margen, min(lons) - margen], [max(lats) + margen, max(lons) + margen]]


def plural(n, uno, varios):
    """«1 paso peatonal», «2 pasos peatonales»: elige la forma según n."""
    return uno if n == 1 else varios


_plural = plural


def _de_ellos_puentes(n):
    """Final de la frase de cruces cerrados: cuántos son puentes existentes."""
    if not n:
        return "."
    if n == 1:
        return ", uno de ellos es un puente existente."
    return f", {n} de ellos son puentes existentes."


def pasos_del_plan(plan):
    """Lista de pasos para mostrar el plan de a uno: título, cifra grande, detalle y qué resaltar.

    Cada paso: id, titulo, cifra (texto grande), unidad, detalle (lista de frases), etapa (o None),
    capas (qué dibujar con foco: "etapas", "puentes", "sentidos", "rutas", "carga", "cauce"),
    donde "puentes" son los pasos peatonales provisionales y "cauce" es el eje de la obra.
    foco ([[lat, lon], [lat, lon]] del recuadro al que acercar el mapa).
    """
    r, e = plan["resumen"], plan["etapas"]
    todo = [p for l in plan["obra"]["lineas"] for p in l]
    foco_total = _limites(todo)
    pasos = [dict(
        id="etapas", titulo="Etapas de obra", cifra=str(r["etapas"]), etapa=None, capas=["etapas"], foco=foco_total,
        unidad=_plural(r["etapas"], "etapa de obra", "etapas de obra"),
        detalle=[f"La obra mide {r['longitud_m']:,} m a lo largo de su eje y se hace por tramos de hasta "
                 f"{plan['parametros']['etapa_max_m']} m.".replace(",", "."),
                 "En cada etapa solo se cierran los cruces de ese tramo; el resto sigue abierto.",
                 "Los cortes se eligen para que ninguna etapa concentre demasiados cruces."])]
    por_etapa = ", ".join(f"etapa {x['numero']}: {len((x['peatones'] or {}).get('puentes', []))}" for x in e)
    pasos.append(dict(
        id="puentes", titulo="Pasos peatonales provisionales", cifra=str(r["puentes_peatonales"]), etapa=None,
        capas=["puentes"], foco=foco_total,
        unidad=_plural(r["puentes_peatonales"], "paso peatonal", "pasos peatonales"),
        detalle=[f"Uno por cada {plan['parametros']['un_puente_cada_m']} m de obra, repartidos a lo largo del tramo.",
                 por_etapa + "."]))
    pasos.append(dict(
        id="sentidos", titulo="Cambios de sentido", cifra=str(r["cambios_de_sentido"]), etapa=None,
        capas=["sentidos"], foco=foco_total,
        unidad=_plural(r["cambios_de_sentido"], "calle a doble sentido", "calles a doble sentido"),
        detalle=["Calles de un solo sentido que pasan a doble sentido mientras dura cada etapa.",
                 "Solo se proponen si reducen el desvío o devuelven el camino a alguien."]))
    pasos.append(dict(
        id="rutas", titulo="Rutas alternas para señalizar", cifra=str(r["rutas_alternas"]), etapa=None,
        capas=["rutas"], foco=foco_total, unidad=_plural(r["rutas_alternas"], "ruta alterna", "rutas alternas"),
        detalle=["Para cada cruce cerrado: el camino más corto que queda abierto, en carro y a pie."]))
    sem = plan["semaforos_conocidos"]
    pasos.append(dict(
        id="control", titulo="Esquinas que reciben más recorridos desviados", cifra=str(r["esquinas_de_control"]),
        etapa=None, capas=["carga"], foco=foco_total,
        unidad=_plural(r["esquinas_de_control"], "esquina para controlar", "esquinas para controlar"),
        detalle=[f"{r['esquinas_sin_semaforo']} de ellas no tienen semáforo registrado en OpenStreetMap: son las "
                 "primeras candidatas a un semáforo temporal o un agente de tránsito." if sem is not None
                 else "No se sabe si tienen semáforo: faltan datos.",
                 "No es congestión medida: no hay datos de volumen de tránsito. Es cuántos recorridos desviados "
                 "pasan por la esquina."]))
    for x in e:
        p, v = x["peatones"], x["vehiculos"]
        detalle = [f"Tramo del metro {x['inicio_m']} al {x['fin_m']} ({x['longitud_m']} m). "
                   f"Se cierran {x['cruces_cerrados']} {_plural(x['cruces_cerrados'], 'cruce', 'cruces')}"
                   + _de_ellos_puentes(x["puentes_existentes_cerrados"])]
        if p:
            detalle.append(f"A pie: el desvío medio pasa de {p['obra']['desvio_medio_m']:.0f} m a "
                           f"{p['con_puentes']['desvio_medio_m']:.0f} m con {len(p['puentes'])} "
                           f"{_plural(len(p['puentes']), 'paso peatonal', 'pasos peatonales')}.")
        if v:
            detalle.append(f"En carro: desvío medio de {v['obra']['desvio_medio_m']:.0f} m"
                           + (f"; {v['obra']['sin_camino']} pares sin camino" if v['obra']['sin_camino'] else "")
                           + (f"; {len(v['medidas'])} {plural(len(v['medidas']), 'cambio', 'cambios')} de sentido."
                              if v["medidas"] else "."))
        detalle += x["avisos"]
        puntos = x["eje"] or todo
        pasos.append(dict(
            id=f"etapa-{x['numero']}", titulo=f"Etapa {x['numero']} de {r['etapas']}", etapa=x["numero"],
            cifra=str(len((p or {}).get("puentes", []))), unidad=_plural(len((p or {}).get("puentes", [])),
                                                                          "paso peatonal", "pasos peatonales"),
            detalle=detalle, capas=["etapas", "puentes", "sentidos", "rutas", "carga"], foco=_limites(puntos)))
    pasos.append(dict(
        id="limites", titulo="Qué no mide este plan", cifra="!", unidad="límites", etapa=None, capas=[], foco=foco_total,
        detalle=["No hay datos de volumen de tránsito: no se mide congestión, solo desvíos en metros.",
                 "No se diseñan carriles ni tiempos de semáforo.",
                 "Los pasos peatonales y cambios de sentido deben verificarse en terreno antes de proponerlos."]))
    return pasos
