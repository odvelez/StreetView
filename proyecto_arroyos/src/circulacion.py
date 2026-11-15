"""Propuestas calculadas para reorganizar la circulación alrededor de una etapa de obra.

Cuatro piezas, todas con supuestos explícitos (src/supuestos.py) y sin datos de tránsito:

  1. Capacidad entre los dos lados de la obra: flujo máximo (Edmonds–Karp) en el grafo vehicular,
     con la capacidad de cada calle en carriles. El corte mínimo dice cuántos carriles quedan para
     pasar de un lado al otro y por qué calles (teorema de flujo máximo y corte mínimo).
  2. Pares de calles paralelas de un solo sentido (pares viales): para cada par se prueban TODAS las
     configuraciones (sin cambio, invertir una, invertir la otra, las dos a doble sentido) y se mide
     cada una con Dijkstra (desvío ponderado por la demanda) y con el corte mínimo (capacidad).
  3. Pasos peatonales según la demanda: voraz ponderado (src/demanda.py) que decide cuántos y dónde,
     con separación mínima; se informa la brecha más larga sin cruce a lo largo de la obra.
  4. Control temporal en esquinas: las que reciben más recorridos desviados ponderados, con al menos
     3 accesos, sin semáforo registrado y separadas entre sí. Es una priorización, no un criterio de
     justificación de semáforos (esos exigen conteos).

Por qué hace falta la capacidad: midiendo solo distancias, invertir una calle quita un arco y agrega
otro, y pasarla a doble sentido solo agrega; así nunca ganaría invertir. Con capacidad sí puede ganar.
"""
import math

from src.analisis import tablas
from src.demanda import agregar_arcos, evaluar, pesos_gravedad, voraz_ponderado
from src.grafo import Grafo, flujo_maximo
from src.supuestos import valor as supuesto

CLASES_MAYORES = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
                  "tertiary", "tertiary_link"}
MAX_ANGULO_PAR = 25          # grados: dos calles con direcciones a menos de esto son paralelas


def _r(m):
    """Métricas de src.demanda.evaluar redondeadas para el JSON."""
    return dict(desvio_ponderado_m=round(m["desvio_ponderado_m"], 1), desvio_positivo_m=round(m["desvio_positivo_m"], 1),
                sin_camino=m["sin_camino"],
                demanda_sin_camino_pct=round(m["demanda_sin_camino_pct"], 1),
                demanda_desvio_relativo_pct=round(m["demanda_desvio_relativo_pct"], 1))


# ------------------------------------------------------------------ grafos con cambios de sentido
def sentido_con(t, sentidos):
    return sentidos.get(t.id, t.sentido) if sentidos else t.sentido


def grafo_vehiculos_con(red, excluir=frozenset(), sentidos=None):
    """Grafo vehicular sin los tramos `excluir` y con los sentidos cambiados {id_tramo: -1, 0 o 1}."""
    g = Grafo(dirigido=True)
    for t in red.tramos:
        if t.vehicular and t.id not in excluir:
            s = sentido_con(t, sentidos)
            if s >= 0:
                g.agregar_arista(t.u, t.v, t.metros)
            if s <= 0:
                g.agregar_arista(t.v, t.u, t.metros)
    return g


def capacidades_vehiculares(red, excluir=frozenset(), sentidos=None):
    """({(u, v): carriles}, {(u, v): {nombres de calle}}). Tramos paralelos suman sus carriles."""
    caps, nombres = {}, {}
    for t in red.tramos:
        if not t.vehicular or t.id in excluir:
            continue
        s = sentido_con(t, sentidos)
        c = t.carriles_en(s)
        arcos = ([(t.u, t.v)] if s >= 0 else []) + ([(t.v, t.u)] if s <= 0 else [])
        for a in arcos:
            caps[a] = caps.get(a, 0) + c
            nombres.setdefault(a, set()).add(t.via or "calle sin nombre")
    return caps, nombres


def capacidad_entre_lados(red, lado_a, lado_b, excluir=frozenset(), sentidos=None):
    """Carriles del corte mínimo de A hacia B y de B hacia A, con las calles de cada corte."""
    caps, nombres = capacidades_vehiculares(red, excluir, sentidos)
    res = {}
    for clave, fuentes, sumideros in (("a_b", lado_a, lado_b), ("b_a", lado_b, lado_a)):
        f = flujo_maximo(caps, set(fuentes), set(sumideros) - set(fuentes))
        res[clave] = f["valor"]
        res[f"calles_{clave}"] = sorted({n for u, v, _ in f["corte"] for n in nombres[(u, v)]})
    return res


def tramo_de_arco(red, x, y, metros):
    """Id del tramo de un solo sentido que une x e y con ese largo (para los candidatos a doble sentido)."""
    for t in red.tramos:
        if t.vehicular and t.sentido != 0 and {t.u, t.v} == {x, y} and abs(t.metros - metros) < 1e-6:
            return t.id
    return None


# ------------------------------------------------------------------ pares viales
def _direccion(t, plano):
    """Vector (en metros) del tramo en el sentido en que se puede circular."""
    a, b = (t.forma[0], t.forma[-1]) if t.sentido >= 0 else (t.forma[-1], t.forma[0])
    (ax, ay), (bx, by) = plano.xy(a), plano.xy(b)
    return bx - ax, by - ay


def calles_de_un_sentido(red, obra, p0, p1, excluir, radio, ventana_m=250):
    """Calles con nombre de un solo sentido cerca de la etapa: (usables, excluidas con su motivo).

    Cada calle usable: dict(via, tramos, largo_m, angulo, centro, clase). Se excluyen las de clases no
    invertibles, las cortas, las que tienen tramos en los dos sentidos (dos calzadas de una avenida o una
    calle que cambia de sentido) y las que no tienen nombre (no se pueden señalizar por nombre).
    """
    xy = red.plano.xy
    grupos = {}
    for t in red.tramos:
        if not t.vehicular or t.sentido == 0 or not t.via or t.id in excluir:
            continue
        medio = xy(t.forma[len(t.forma) // 2])
        if obra.ubicar(medio)[0] > radio:
            continue
        pos = obra.posicion(medio)
        if not (p0 - ventana_m <= pos <= p1 + ventana_m):
            continue
        grupos.setdefault(t.via, []).append(t)

    invertibles = set(supuesto("clases_invertibles"))
    usables, excluidas = [], []
    for via, ts in sorted(grupos.items()):
        largo = sum(t.metros for t in ts)
        vectores = [(_direccion(t, red.plano), t) for t in ts]
        # Eje principal de la calle sin importar el sentido (ángulo doble), y sentido de cada tramo.
        sx = sum(math.cos(2 * math.atan2(vy, vx)) * t.metros for (vx, vy), t in vectores)
        sy = sum(math.sin(2 * math.atan2(vy, vx)) * t.metros for (vx, vy), t in vectores)
        eje = math.atan2(sy, sx) / 2
        ux, uy = math.cos(eje), math.sin(eje)
        adelante = sum(t.metros for (vx, vy), t in vectores if vx * ux + vy * uy >= 0)
        atras = largo - adelante
        clase = max({t.clase for t in ts}, key=lambda c: sum(t.metros for t in ts if t.clase == c))
        if min(adelante, atras) > 0.3 * largo:
            excluidas.append(dict(via=via, motivo="tiene tramos en los dos sentidos (dos calzadas de una vía o "
                                                  "una calle que cambia de sentido)"))
            continue
        if clase not in invertibles:
            excluidas.append(dict(via=via, motivo=f"es una vía de clase {clase} (solo se proponen calles locales)"))
            continue
        if largo < supuesto("largo_min_par_m"):
            excluidas.append(dict(via=via, motivo=f"solo tiene {largo:.0f} m de un sentido cerca de la etapa"))
            continue
        if atras > adelante:
            ux, uy = -ux, -uy
        pts = [xy(p) for t in ts for p in (t.forma[0], t.forma[-1])]
        centro = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        usables.append(dict(via=via, tramos=sorted(t.id for t in ts), largo_m=round(largo), angulo=math.atan2(uy, ux),
                            centro=centro, clase=clase))
    return usables, excluidas


def detectar_pares(calles, maximo=None):
    """Pares de calles de un solo sentido paralelas y cercanas, de la más cercana a la más lejana.

    Paralelas: sus direcciones difieren menos de 25 grados (mismo sentido) o más de 155 (sentidos
    opuestos: ya son un par vial). Cercanas: entre sep_calzadas_m y dist_par_max_m de separación y
    superpuestas a lo largo de su dirección.
    """
    dmax, dmin = supuesto("dist_par_max_m"), supuesto("sep_calzadas_m")
    pares = []
    for i, a in enumerate(calles):
        for b in calles[i + 1:]:
            dif = abs((a["angulo"] - b["angulo"] + math.pi) % (2 * math.pi) - math.pi)
            if dif < math.radians(MAX_ANGULO_PAR):
                relacion = "mismo sentido"
            elif dif > math.pi - math.radians(MAX_ANGULO_PAR):
                relacion = "sentidos opuestos"
            else:
                continue
            ux, uy = math.cos(a["angulo"]), math.sin(a["angulo"])
            dx, dy = b["centro"][0] - a["centro"][0], b["centro"][1] - a["centro"][1]
            perp, largo = abs(-dx * uy + dy * ux), abs(dx * ux + dy * uy)
            if dmin < perp <= dmax and largo <= (a["largo_m"] + b["largo_m"]) / 2:
                pares.append(dict(a=a, b=b, relacion=relacion, separacion_m=round(perp)))
    pares.sort(key=lambda p: p["separacion_m"])
    return pares[:maximo] if maximo else pares


def configuraciones(red, par):
    """[(nombre, {id_tramo: nuevo sentido}, nota)] para un par de calles."""
    a, b = par["a"], par["b"]

    def invertir(calle):
        return {i: -red.tramos[i].sentido for i in calle["tramos"]}

    confs = [("sin cambio", {}, ""), (f"invertir {a['via']}", invertir(a), ""), (f"invertir {b['via']}", invertir(b), "")]
    minimo = supuesto("carriles_min_doble")
    ids = a["tramos"] + b["tramos"]
    if all(red.tramos[i].carriles_total >= minimo for i in ids):
        confs.append(("las dos a doble sentido", {i: 0 for i in ids}, ""))
    else:
        confs.append(("las dos a doble sentido", None,
                      f"no se evalúa: hay tramos con menos de {minimo} carriles"))
    return confs


def _mejora(nueva, base, cap_nueva, cap_base, mejora_min):
    """True si la alternativa mejora de verdad a la de base (sin cambio)."""
    if nueva["sin_camino"] != base["sin_camino"]:
        return nueva["sin_camino"] < base["sin_camino"]
    d0, d1 = base["desvio_ponderado_m"], nueva["desvio_ponderado_m"]
    if d1 <= d0 - (abs(d0) * mejora_min + 0.5):
        return True
    return d1 <= d0 + 0.5 and cap_nueva > cap_base     # mismo desvío y más capacidad


def evaluar_par(red, par, excluir, origenes, pares_v, pesos_v, base_v, lado_a, lado_b, base_sentidos=None):
    """Todas las configuraciones de un par, medidas con Dijkstra (desvío ponderado) y con el corte mínimo.

    Se recalcula Dijkstra para cada configuración: al quitar arcos ya no sirve la fórmula rápida.
    Devuelve el dict del par con `alternativas`, `elegida`, `motivo` y `cambios` (los sentidos a aplicar).
    """
    alternativas, medidas = [], {}
    for nombre, cambios, nota in configuraciones(red, par):
        if cambios is None:
            alternativas.append(dict(configuracion=nombre, evaluada=False, nota=nota))
            continue
        sentidos = {**(base_sentidos or {}), **cambios}
        g = grafo_vehiculos_con(red, excluir, sentidos)
        F = tablas(g, origenes, objetivos=set(origenes))
        m = evaluar(F, F, base_v, pares_v, pesos_v)
        cap = capacidad_entre_lados(red, lado_a, lado_b, excluir, sentidos)
        medidas[nombre] = (m, min(cap["a_b"], cap["b_a"]), cambios)
        alternativas.append(dict(configuracion=nombre, evaluada=True, **_r(m),
                                 capacidad_a_b=cap["a_b"], capacidad_b_a=cap["b_a"], nota=nota))
    base_m, base_cap, _ = medidas["sin cambio"]
    mejor = min(medidas.items(), key=lambda kv: (kv[1][0]["sin_camino"], round(kv[1][0]["desvio_ponderado_m"], 1), -kv[1][1]))
    nombre, (m, cap, cambios) = mejor
    if nombre != "sin cambio" and _mejora(m, base_m, cap, base_cap, supuesto("mejora_min")):
        elegida, motivo = nombre, _motivo(m, base_m, cap, base_cap)
    else:
        elegida, cambios = "sin cambio", {}
        motivo = "Ninguna configuración devuelve el camino a más pares, ni baja el desvío ponderado al menos un 2 %, ni da más capacidad sin alargar los recorridos."
    return dict(calles=[par["a"]["via"], par["b"]["via"]], relacion=par["relacion"], separacion_m=par["separacion_m"],
                alternativas=alternativas, elegida=elegida, motivo=motivo,
                cambios=[dict(id=i, via=red.tramos[i].via, sentido=s) for i, s in sorted(cambios.items())],
                forma=[[list(p) for p in red.tramos[i].forma] for i in sorted(cambios)])


def _motivo(m, base, cap, cap_base):
    partes = []
    if m["sin_camino"] < base["sin_camino"]:
        partes.append(f"devuelve el camino a {base['sin_camino'] - m['sin_camino']} pares")
    if m["desvio_ponderado_m"] < base["desvio_ponderado_m"]:
        partes.append(f"baja el desvío ponderado de {base['desvio_ponderado_m']:.0f} a {m['desvio_ponderado_m']:.0f} m")
    if cap != cap_base:
        partes.append(f"el sentido más estrecho pasa de {cap_base} a {cap} carriles")
    return "Elegida porque " + ", ".join(partes) + "." if partes else "Elegida."


# ------------------------------------------------------------------ pasos peatonales por demanda
def brechas(posiciones_abiertas, p0, p1, candidatos=()):
    """Mayor tramo de la etapa sin ningún cruce abierto y los tramos de más de brecha_max_m.

    Los extremos de la etapa cuentan como abiertos (fuera de la etapa los cruces siguen abiertos). Para
    cada tramo largo se dice cuántos candidatos a paso peatonal había dentro: si no hay ninguno, el
    tramo no tiene esquinas enfrentadas a menos de la luz máxima y hace falta estudiarlo en terreno.
    """
    puntos = sorted([p0, p1] + [p for p in posiciones_abiertas if p0 <= p <= p1])
    tramos = [(a, b) for a, b in zip(puntos, puntos[1:])]
    maximo = max((b - a for a, b in tramos), default=0.0)
    largos = [dict(inicio_m=round(a), fin_m=round(b), largo_m=round(b - a),
                   candidatos_dentro=sum(1 for c in candidatos if a < c < b)) for a, b in tramos
              if b - a > supuesto("brecha_max_m")]
    return round(maximo), largos


def _formato_pasos(elegidos):
    return [dict(orden=i + 1, **info, **_r(m)) for i, (info, _, m) in enumerate(elegidos)]


def pasos_por_demanda(d, pesos_p, tolerancia):
    """Voraz ponderado sobre los pasos peatonales candidatos de la etapa (ver `propuestas_de_etapa`)."""
    sep = supuesto("sep_min_pasos_m")
    elegidos, _ = voraz_ponderado(
        d["pea_obra"], d["origenes"], d["Fs"], d["pares_p"], pesos_p, d["cand_p"], supuesto("max_pasos_etapa"),
        F=d["Fl"], R=d["Fl"], mejora_min=supuesto("mejora_min"),
        incompatibles=lambda a, b: abs(a["pos_m"] - b["pos_m"]) < sep, tolerancia=tolerancia, positivo=True)
    return elegidos


# ------------------------------------------------------------------ control temporal
def vecinos_vehiculares(red, excluir=frozenset()):
    """({esquina: esquinas vecinas por calles vehiculares abiertas}, {esquina: clases de esas calles})."""
    vecinos, clases = {}, {}
    for t in red.tramos:
        if t.vehicular and t.id not in excluir:
            for a, b in ((t.u, t.v), (t.v, t.u)):
                vecinos.setdefault(a, set()).add(b)
                clases.setdefault(a, set()).add(t.clase)
    return vecinos, clases


def elegir_controles(red, carga, total, vecinos, clases, semaforos, radio_semaforo_m):
    """Esquinas candidatas a control temporal (semáforo provisional o agente), de mayor a menor carga.

    Candidata: al menos `accesos_min` calles, carga en el percentil `percentil_carga` o más de la etapa y
    sin semáforo registrado a menos de `radio_semaforo_m`. Se eligen de forma voraz con separación
    `sep_control_m`, hasta `max_controles_etapa`. Devuelve (elegidas, cuántas se descartaron por tener ya
    semáforo).
    """
    valores = sorted(c for c in carga.values() if c > 0)
    if not valores or total <= 0:
        return [], 0
    k = max(1, math.ceil(supuesto("percentil_carga") / 100 * len(valores)))
    umbral = valores[k - 1]
    sep, maximo, accesos_min = supuesto("sep_control_m"), supuesto("max_controles_etapa"), supuesto("accesos_min")
    elegidas, con_semaforo = [], 0
    for n, c in sorted(carga.items(), key=lambda x: (-x[1], str(x[0]))):
        if c < umbral or len(elegidas) == maximo:
            break
        accesos = len(vecinos.get(n, ()))
        if accesos < accesos_min:
            continue
        sem = None
        if semaforos is not None:
            if any(red.plano.dist(red.pos[n], p) <= radio_semaforo_m for p in semaforos.values()):
                con_semaforo += 1
                continue
            sem = False
        if any(red.plano.dist(red.pos[n], red.pos[e["esquina"]]) < sep for e in elegidas):
            continue
        mayor = bool(clases.get(n, set()) & CLASES_MAYORES)
        elegidas.append(dict(
            esquina=n, nombre=red.nombre(n), posicion=list(red.pos[n]), puntaje_pct=round(100 * c / total, 1),
            accesos=accesos, cruza_via_mayor=mayor, semaforo_existente=sem,
            motivo=(f"Pasa por aquí el {100 * c / total:.0f} % de la demanda desviada; {accesos} accesos"
                    + ("; cruza una vía principal" if mayor else "")
                    + ("; sin semáforo registrado en OpenStreetMap." if sem is False
                       else "; no se sabe si tiene semáforo (faltan datos).")
                    + " Candidata a control temporal (semáforo provisional o agente de tránsito); "
                      "verificar con conteos.")))
    return elegidas, con_semaforo


# ------------------------------------------------------------------ todo junto, por etapa
def propuestas_de_etapa(d, d0_m):
    """Las cuatro propuestas calculadas de una etapa. `d` trae lo que ya calculó `etapas.evaluar_etapa`:

    red, obra, p0, p1, cerrados (ids), contacto, lados_w {1, -1}, muestra {1, -1}, origenes, radio,
    semaforos, radio_semaforo_m; peatones: pea_obra, Fs, Fl, pares_p, cand_p, elegidos_regla [(info, arcos)];
    vehículos: Vs, Vl, Rl, veh_obra, pares_v, medidas_regla [(info, arcos)].
    """
    red, obra = d["red"], d["obra"]
    xy = red.plano.xy
    excluir = set(d["cerrados"])
    tol = supuesto("tolerancia_desvio_relativo")

    # ---- demanda supuesta
    pesos_p = pesos_gravedad(d["pares_p"], d["Fs"], d0_m)
    pesos_v = d["pesos_v"]

    # ---- peatones: regla de longitud contra pasos por demanda
    obra_p = evaluar(d["Fl"], d["Fl"], d["Fs"], d["pares_p"], pesos_p, tolerancia=tol)
    arcos_regla = [a for _, arcos in d["elegidos_regla"] for a in arcos]
    _, F_regla, _ = agregar_arcos(d["pea_obra"], d["Fl"], d["Fl"], arcos_regla,
                                  set(d["origenes"]) | {z for x, y, _ in arcos_regla for z in (x, y)})
    regla_p = evaluar(F_regla, F_regla, d["Fs"], d["pares_p"], pesos_p, tolerancia=tol)
    elegidos = pasos_por_demanda(d, pesos_p, tol)
    demanda_p = elegidos[-1][2] if elegidos else obra_p
    abiertos = [obra.posicion(xy(red.tramos[i].forma[len(red.tramos[i].forma) // 2]))
                for i, (estado, motivo) in d["contacto"].items()
                if motivo == "cruza" and i not in excluir and red.tramos[i].peatonal]
    pos_cand = [info["pos_m"] for info, _ in d["cand_p"]]
    brecha_regla = brechas(abiertos + [info["pos_m"] for info, _ in d["elegidos_regla"]], d["p0"], d["p1"], pos_cand)
    brecha_demanda = brechas(abiertos + [info["pos_m"] for info, _, _ in elegidos], d["p0"], d["p1"], pos_cand)
    pasos = dict(
        pasos=_formato_pasos(elegidos), numero=len(elegidos), candidatos=len(d["cand_p"]),
        limitado_por_maximo=len(elegidos) == supuesto("max_pasos_etapa"),
        brecha_max_m=brecha_demanda[0], tramos_sobre_brecha=brecha_demanda[1],
        comparacion_regla_500m=dict(numero=len(d["elegidos_regla"]), brecha_max_m=brecha_regla[0],
                                    tramos_sobre_brecha=brecha_regla[1], **_r(regla_p)),
        metodo="voraz ponderado por la demanda supuesta; con pocos candidatos se comparó contra fuerza bruta "
               "(tests/test_demanda.py): con 2 pasos el voraz puede no ser óptimo")

    # ---- vehículos: medidas de la regla de hoy (doble sentido) y pares viales
    sentidos_medidas, arcos_medidas = {}, []
    for _, arcos in d["medidas_regla"]:
        for x, y, w in arcos:
            arcos_medidas.append((x, y, w))
            i = tramo_de_arco(red, x, y, w)
            if i is not None:
                sentidos_medidas[i] = 0
    obra_v = evaluar(d["Vl"], d["Rl"], d["Vs"], d["pares_v"], pesos_v)

    def medir_v(sentidos):
        g = grafo_vehiculos_con(red, excluir, sentidos)
        F = tablas(g, d["origenes"], objetivos=set(d["origenes"]))
        return evaluar(F, F, d["Vs"], d["pares_v"], pesos_v)

    if arcos_medidas:      # exacto, agregando los arcos de a uno (2 Dijkstra por arco en vez de uno por esquina)
        _, F_med, _ = agregar_arcos(d["veh_obra"], d["Vl"], d["Rl"], arcos_medidas, d["objetivos_v"])
        medidas_v = evaluar(F_med, F_med, d["Vs"], d["pares_v"], pesos_v)
    else:
        medidas_v = obra_v
    lado_a, lado_b = d["lados_w"][1], d["lados_w"][-1]
    usables, excluidas = calles_de_un_sentido(red, obra, d["p0"], d["p1"], excluir, d["radio"])
    candidatos_pares = detectar_pares(usables, supuesto("max_pares_etapa"))
    pares = [evaluar_par(red, par, excluir, d["origenes"], d["pares_v"], pesos_v, d["Vs"], lado_a, lado_b,
                         base_sentidos=sentidos_medidas) for par in candidatos_pares]
    sentidos_final = dict(sentidos_medidas)
    for p in pares:
        sentidos_final.update({c["id"]: c["sentido"] for c in p["cambios"]})
    final_v = medir_v(sentidos_final) if len(sentidos_final) > len(sentidos_medidas) else medidas_v
    if candidatos_pares:
        motivo_pares = None
    elif usables:
        motivo_pares = ("Hay calles de un solo sentido cerca de esta etapa, pero ningún par es paralelo y está a "
                        f"menos de {supuesto('dist_par_max_m')} m.")
    else:
        motivo_pares = ("No se encontraron calles locales de un solo sentido, con nombre y de al menos "
                        f"{supuesto('largo_min_par_m')} m, cerca de esta etapa. En OpenStreetMap pocas calles traen "
                        "la etiqueta de sentido (oneway): verificar en terreno.")

    # ---- capacidad entre los dos lados
    seco = capacidad_entre_lados(red, lado_a, lado_b)
    con_obra = capacidad_entre_lados(red, lado_a, lado_b, excluir)
    con_todo = capacidad_entre_lados(red, lado_a, lado_b, excluir, sentidos_final)
    veh_h = supuesto("veh_h_carril")

    def conserva(c):
        return {k: (round(100 * c[k] / seco[k], 1) if seco[k] else None) for k in ("a_b", "b_a")}

    # ---- control temporal
    carga, total = d["carga_w"], d["total_w"]
    vecinos, clases = vecinos_vehiculares(red, excluir)
    controles, con_semaforo = elegir_controles(red, carga, total, vecinos, clases, d["semaforos"], d["radio_semaforo_m"])

    circulacion = dict(
        demanda=dict(modelo="gravedad: peso del par = exp(-distancia sin obra / d0), normalizado",
                     d0_m=d0_m, peso_esquina=supuesto("peso_esquina"),
                     pares_peatones=len(d["pares_p"]), pares_vehiculos=len(d["pares_v"])),
        peatones=dict(obra=_r(obra_p), con_pasos_regla_500m=_r(regla_p), con_pasos_por_demanda=_r(demanda_p)),
        vehiculos=dict(obra=_r(obra_v), con_cambios_de_sentido=_r(medidas_v), con_cambios_y_pares_viales=_r(final_v)),
        capacidad=dict(
            unidad="carriles del corte mínimo (sentido a_b: del lado A al lado B)", veh_h_carril=veh_h,
            seco=seco, obra=con_obra, con_medidas=con_todo, conserva_pct=conserva(con_obra),
            conserva_con_medidas_pct=conserva(con_todo),
            veh_h_aprox={k: {s: c[s] * veh_h for s in ("a_b", "b_a")} for k, c in
                         (("seco", seco), ("obra", con_obra), ("con_medidas", con_todo))}),
        esquina_mas_cargada_pct=round(100 * max(carga.values()) / total, 1) if carga and total else None)
    return dict(
        circulacion=circulacion,
        pares_viales=dict(pares=pares, evaluados=len(pares), propuestos=sum(1 for p in pares if p["elegida"] != "sin cambio"),
                          calles_un_sentido=[c["via"] for c in usables], excluidas=excluidas, motivo=motivo_pares),
        pasos_por_demanda=pasos,
        control_temporal=dict(esquinas=controles, descartadas_por_semaforo=con_semaforo,
                              semaforos_conocidos=d["semaforos"] is not None))


def propuestas_vacias(motivo):
    """Las mismas claves cuando la etapa no tiene esquinas suficientes para medir."""
    return dict(circulacion=None, pares_viales=dict(pares=[], evaluados=0, propuestos=0, calles_un_sentido=[],
                                                    excluidas=[], motivo=motivo),
                pasos_por_demanda=None, control_temporal=dict(esquinas=[], descartadas_por_semaforo=0,
                                                               semaforos_conocidos=None))
