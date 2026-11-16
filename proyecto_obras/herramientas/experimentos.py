"""Experimentos de la prioridad 2 para el caso de estudio (El Salao).

Uso (desde proyecto_obras/):
    python herramientas/experimentos.py                 # todos
    python herramientas/experimentos.py voraz control   # solo algunos

Experimentos:
    voraz         heurística voraz contra fuerza bruta (k = 2), con todos los candidatos
    criticos      intermediación (Brandes) en el grafo vehicular, en seco y con lluvia
    sensibilidad  luz máxima del puente y tamaño y posición de la muestra de esquinas
    control       lado por producto cruz contra componentes conexas
    histograma    distribución del desvío por par, antes y después de las medidas
    calculadas    sensibilidad de las propuestas calculadas (d0, carriles y capacidad por carril)

Cada uno guarda un .json y un .md (tabla lista para el informe) en resultados/experimentos/.
Los resultados oficiales de resultados/analisis.json no se tocan.
Excepción: «calculadas» solo imprime; con --salida <carpeta> guarda su .json y .md en esa carpeta
(nunca en resultados/):  python herramientas/experimentos.py calculadas --salida /tmp/sensibilidad
"""
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src import analisis, fuente
from src.analisis import analizar, medir, tablas
from src.comparacion import comparar
from src.control import control_de_lados, lados_de_zona, lados_por_distancia
from src.grafo import INF, intermediacion

SALIDA = RAIZ / "resultados" / "experimentos"
RADIO = 400


def sin_forma(info):
    return {k: v for k, v in info.items() if k != "forma"}


def guardar(nombre, datos, md):
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / f"{nombre}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    (SALIDA / f"{nombre}.md").write_text(md, encoding="utf-8")
    print(f"  -> resultados/experimentos/{nombre}.json y .md")


def caso(k=3, luz=analisis.LUZ_MAX_M):
    """Red, líneas del cauce, resultado oficial y contexto interno de El Salao."""
    lineas = fuente.lineas_ejemplo()
    recuadro, _ = fuente.recuadro_de(lineas, RADIO)
    red, _ = fuente.red_para(recuadro)
    contexto = {}
    r = analizar(red, lineas, radio=RADIO, luz_max=luz, k=k, contexto=contexto)
    return red, lineas, r, contexto


def tabla(cabecera, filas):
    out = ["| " + " | ".join(cabecera) + " |", "|" + "|".join("---" for _ in cabecera) + "|"]
    out += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------ voraz vs óptimo
def exp_voraz():
    print("Voraz contra fuerza bruta (k = 2)")
    red, lineas, r, ctx = caso(k=2)
    datos, filas = {}, []
    for clave, titulo in (("peatones", "Puentes peatonales"), ("vehiculos", "Doble sentido")):
        c = ctx[clave]
        t = time.time()
        res = comparar(c["lluvia"], ctx["origenes"], c["F_seco"], c["pares"], c["candidatos"],
                       c["F_lluvia"], c.get("R_lluvia", c["F_lluvia"]))
        seg = time.time() - t
        # Verificación independiente del óptimo: Dijkstra desde cero sobre el grafo con la pareja.
        g2 = c["lluvia"].copia()
        for i in res["optimo"]["indices"]:
            for x, y, w in c["candidatos"][i][1]:
                g2.agregar_arista(x, y, w)
        F2 = tablas(g2, ctx["origenes"], set(ctx["origenes"]))
        R2 = F2 if not g2.dirigido else tablas(g2.invertido(), ctx["origenes"], set(ctx["origenes"]))
        exacto = medir(F2, R2, c["F_seco"], c["pares"]).objetivo()
        n = len(c["candidatos"])
        res.update(
            parejas_probadas=n * (n - 1) // 2, segundos=round(seg, 1),
            objetivo_optimo_desde_cero=list(exacto),
            verificado=list(exacto) == list(res["optimo"]["objetivo"]),
            elegidos_voraz=[sin_forma(c["candidatos"][i][0]) for i in res["voraz"]["indices"]],
            elegidos_optimo=[sin_forma(c["candidatos"][i][0]) for i in res["optimo"]["indices"]])
        datos[clave] = res
        filas.append([titulo, n, res["parejas_probadas"], tuple(res["voraz"]["objetivo"]),
                      tuple(res["optimo"]["objetivo"]), res["sin_camino_extra"], res["desvio_extra_m"],
                      "sí" if res["coinciden"] else "no", "sí" if res["verificado"] else "NO"])
        print(f"  {titulo}: voraz {res['voraz']['objetivo']} / óptimo {res['optimo']['objetivo']} ({seg:.0f} s)")
    md = ("Objetivo = (pares sin camino, desvío medio en m). Menor es mejor.\n\n"
          + tabla(["Medida", "Candidatos", "Parejas probadas", "Voraz", "Óptimo (fuerza bruta)",
                   "Pares sin camino de más", "Desvío de más (m)", "Misma pareja", "Óptimo verificado desde cero"], filas))
    guardar("voraz_vs_fuerza_bruta", datos, md)


# --------------------------------------------------------------- criticos
def exp_criticos(top=10):
    print("Intermediación en el grafo vehicular (tarda unos 2 minutos)")
    red, lineas, r, ctx = caso(k=1)
    obra, v = ctx["obra"], ctx["vehiculos"]
    t = time.time()
    bs, bl = intermediacion(v["seco"]), intermediacion(v["lluvia"])
    print(f"  calculado en {time.time() - t:.0f} s")
    en_zona = set(ctx["lados_todos"][1]) | set(ctx["lados_todos"][-1])

    def fila(n, valor, otro=None):
        d = obra.ubicar(red.plano.xy(red.pos[n]))[0]
        return dict(esquina=n, nombre=red.nombre(n), valor=round(valor, 6), distancia_cauce_m=round(d),
                    en_zona=n in en_zona, posicion=list(red.pos[n]),
                    osm=f"https://www.openstreetmap.org/node/{n}")

    def mejores(d, claves=None):
        orden = sorted(claves if claves is not None else d, key=lambda n: -d[n])[:top]
        return [fila(n, d[n]) for n in orden]

    delta = {n: bl[n] - bs.get(n, 0.0) for n in bl}
    datos = dict(
        top_seco=mejores(bs), top_lluvia=mejores(bl),
        mayor_aumento=[dict(**fila(n, delta[n]), seco=round(bs.get(n, 0.0), 6), lluvia=round(bl[n], 6))
                       for n in sorted(delta, key=lambda n: -delta[n])[:top]],
        mayor_aumento_en_zona=[dict(**fila(n, delta[n]), seco=round(bs.get(n, 0.0), 6), lluvia=round(bl[n], 6))
                               for n in sorted(en_zona & set(delta), key=lambda n: -delta[n])[:top]],
        esquinas=len(bs), en_comun_top=len({f["esquina"] for f in mejores(bs)} & {f["esquina"] for f in mejores(bl)}),
        suma_seco=round(sum(bs.values()), 4), suma_lluvia=round(sum(bl.values()), 4),
    )
    md = f"Grafo vehicular: {len(bs)} esquinas. Valores normalizados a [0, 1] (Brandes con pesos).\n\n"
    for titulo, clave in (("Mayor intermediación en seco", "top_seco"), ("Mayor intermediación con lluvia", "top_lluvia"),
                          ("Mayor aumento con lluvia (toda la red)", "mayor_aumento"),
                          ("Mayor aumento con lluvia (zona de estudio)", "mayor_aumento_en_zona")):
        md += f"**{titulo}**\n\n"
        extra = clave.startswith("mayor")
        cab = ["#", "Esquina", "Valor", "Distancia al cauce (m)"] + (["Seco", "Lluvia"] if extra else []) + ["OSM"]
        filas = [[i + 1, f["nombre"], f"{f['valor']:.5f}", f["distancia_cauce_m"]]
                 + ([f"{f['seco']:.5f}", f"{f['lluvia']:.5f}"] if extra else []) + [f["osm"].rsplit("/", 1)[1]]
                 for i, f in enumerate(datos[clave])]
        md += tabla(cab, filas) + "\n"
    md += f"Esquinas en común entre los {top} primeros en seco y con lluvia: {datos['en_comun_top']}.\n"
    guardar("criticos_betweenness", datos, md)


# ------------------------------------------------------------ sensibilidad
def resumen_corrida(r):
    p, v = r["peatones"], r["vehiculos"]
    return dict(
        lados=r["zona"]["muestra"], candidatos_p=p["candidatos"], candidatos_v=v["candidatos"],
        pea_lluvia=round(p["lluvia"]["desvio_medio_m"], 1), pea_final=round(p["con_medida"]["desvio_medio_m"], 1),
        pea_pct200=round(p["lluvia"]["pct_mayor_200m"], 1), pea_puentes=[
            f"{q['desde']} <-> {q['hasta']} ({q['recorrido_m']} m)" for q in p["propuestas"]],
        veh_lluvia=round(v["lluvia"]["desvio_medio_m"], 1), veh_fijo=round(v["lluvia"]["desvio_fijo_m"], 1),
        veh_final_fijo=round(v["con_medida"]["desvio_fijo_m"], 1), veh_pares=v["lluvia"]["pares"],
        veh_sin=v["lluvia"]["sin_camino"], veh_sin_final=v["con_medida"]["sin_camino"],
        veh_pct200=round(v["lluvia"]["pct_mayor_200m"], 1),
        veh_medidas=[f"{q['desde']} -> {q['hasta']} ({q['metros']} m)" for q in v["propuestas"]])


def exp_sensibilidad():
    print("Sensibilidad a la luz del puente y a la muestra")
    lineas = fuente.lineas_ejemplo()
    recuadro, _ = fuente.recuadro_de(lineas, RADIO)
    red, _ = fuente.red_para(recuadro)
    datos = dict(luz=[], muestra=[])
    for luz in (20, 40, 60, 80, 100, 150):
        t = time.time()
        r = resumen_corrida(analizar(red, lineas, radio=RADIO, luz_max=luz, k=3))
        r["luz_m"] = luz
        datos["luz"].append(r)
        print(f"  luz {luz} m: peatones {r['pea_lluvia']} -> {r['pea_final']} m ({time.time() - t:.0f} s)")

    original = analisis.MAX_POR_LADO, analisis.DESFASE_MUESTRA
    try:
        for tam, desfases in ((30, range(5)), (60, range(5)), (120, range(5)), (240, range(2)), (10 ** 6, [0])):
            for d in desfases:
                analisis.MAX_POR_LADO, analisis.DESFASE_MUESTRA = tam, d
                t = time.time()
                r = resumen_corrida(analizar(red, lineas, radio=RADIO, k=3))
                r["tam"], r["desfase"] = tam, d
                datos["muestra"].append(r)
                print(f"  muestra {min(tam, 999)} (desfase {d}): vehículos sin camino {r['veh_sin']} "
                      f"de {r['veh_pares']} ({time.time() - t:.0f} s)")
    finally:
        analisis.MAX_POR_LADO, analisis.DESFASE_MUESTRA = original

    md = "**Luz máxima del puente peatonal** (muestra oficial de 120 por lado, 3 puentes)\n\n"
    md += tabla(["Luz (m)", "Candidatos", "Desvío con lluvia (m)", "Desvío con 3 puentes (m)", "Primer puente"],
                [[d["luz_m"], d["candidatos_p"], d["pea_lluvia"], d["pea_final"],
                  d["pea_puentes"][0] if d["pea_puentes"] else "-"] for d in datos["luz"]])

    def rango(xs):
        xs = list(xs)
        return f"{sum(xs) / len(xs):.1f} ({min(xs):.1f}–{max(xs):.1f})"

    md += "\n**Tamaño de la muestra** (media y rango entre posiciones de la muestra; 'todas' = sin muestrear)\n\n"
    filas = []
    for tam in (30, 60, 120, 240, 10 ** 6):
        g = [d for d in datos["muestra"] if d["tam"] == tam]
        if not g:
            continue
        pares = g[0]["veh_pares"]
        filas.append([("todas" if tam == 10 ** 6 else tam), len(g), pares,
                      rango(d["pea_lluvia"] for d in g), rango(d["pea_final"] for d in g),
                      rango(d["veh_fijo"] for d in g), rango(d["veh_final_fijo"] for d in g),
                      rango(100 * d["veh_sin"] / d["veh_pares"] for d in g),
                      rango(d["veh_sin_final"] and 100 * d["veh_sin_final"] / d["veh_pares"] for d in g)])
    md += tabla(["Esquinas por lado", "Muestras", "Pares veh.", "Peatones lluvia (m)", "Peatones 3 puentes (m)",
                 "Vehículos lluvia (m)", "Vehículos con medidas (m)", "% pares sin camino", "% sin camino con medidas"], filas)
    guardar("sensibilidad", datos, md)


# ------------------------------------------------------------------ control
def exp_control():
    print("Control del lado: producto cruz contra componentes conexas")
    red, lineas, r, ctx = caso(k=1)
    conjuntos = {"zona (sin la orilla)": lados_de_zona(ctx["lados_todos"]),
                 "todas a menos de 400 m (con la orilla)": lados_por_distancia(red, ctx["obra"], RADIO)}
    datos = {}
    for nombre, lado in conjuntos.items():
        for modo in ("barrera_total", "lluvia"):
            datos[f"{nombre} / {modo}"] = control_de_lados(red, ctx["contacto"], lado, modo)
    filas = [[k, d["esquinas"], d["componentes"], d["componentes_mezcladas"],
              ", ".join(f"{c['esquinas']}" for c in d["mayores"]), f"{d['acuerdo_pct']:.1f} %", d["desacuerdos"]]
             for k, d in datos.items()]
    md = tabla(["Esquinas / grafo", "Esquinas", "Componentes", "Componentes con los dos lados", "Tamaño de las 5 mayores",
                "Acuerdo", "Esquinas en desacuerdo"], filas)
    for k, d in datos.items():
        print(f"  {k}: acuerdo {d['acuerdo_pct']} % ({d['desacuerdos']} en desacuerdo); mayores {d['mayores'][:3]}")
        for e in d["ejemplos"][:5]:
            print(f"      desacuerdo: {e['nombre']} {e['posicion']} lado {e['lado_producto_cruz']}")
    guardar("control_lados", datos, md)


# --------------------------------------------------------------- histograma
def desvios(F, base, pares):
    """Desvío de cada par con camino: d(a, b) - d_seco(a, b)."""
    return [F[a][b] - base[a][b] for a, b in pares if b in F[a]]


def percentil(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))]


def exp_histograma():
    print("Histograma de desvíos por par")
    red, lineas, r, ctx = caso(k=3)
    origenes = set(ctx["origenes"])
    datos = {}
    for clave in ("peatones", "vehiculos"):
        c = ctx[clave]
        Ff = tablas(c["final"], ctx["origenes"], origenes)
        datos[clave] = dict(
            lluvia=desvios(c["F_lluvia"], c["F_seco"], c["pares"]),
            medidas=desvios(Ff, c["F_seco"], c["pares"]),
            pares=len(c["pares"]))
    resumen, filas = {}, []
    for clave, titulo in (("peatones", "Peatones"), ("vehiculos", "Vehículos")):
        for esc, nombre in (("lluvia", "Lluvia"), ("medidas", "Lluvia + medidas")):
            xs = datos[clave][esc]
            res = dict(pares_con_camino=len(xs), sin_camino=datos[clave]["pares"] - len(xs),
                       media=round(sum(xs) / len(xs), 1), mediana=round(percentil(xs, 50), 1),
                       p90=round(percentil(xs, 90), 1), p99=round(percentil(xs, 99), 1), maximo=round(max(xs), 1),
                       mejor_que_seco_pct=round(100 * sum(x < -1 for x in xs) / len(xs), 1),
                       sin_desvio_pct=round(100 * sum(abs(x) < 1 for x in xs) / len(xs), 1),
                       mayor_200_pct=round(100 * sum(x > analisis.UMBRAL_M for x in xs) / len(xs), 1))
            resumen.setdefault(clave, {})[esc] = res
            filas.append([titulo, nombre, res["pares_con_camino"], res["sin_camino"], res["mejor_que_seco_pct"],
                          res["sin_desvio_pct"], res["mediana"], res["p90"], res["p99"], res["maximo"], res["mayor_200_pct"]])
    md = ("Desvío = distancia con el escenario − distancia en seco, en metros, por par con camino. "
          "Es negativo cuando una medida crea un atajo más corto que cualquier camino de la red seca.\n\n"
          + tabla(["Modo", "Escenario", "Pares con camino", "Sin camino", "% mejor que en seco (< -1 m)", "% sin desvío (±1 m)", "Mediana",
                   "P90", "P99", "Máximo", "% > 200 m"], filas))
    guardar("histograma", dict(resumen=resumen), md)
    dibujar_histograma(datos, SALIDA.parent / "histograma_desvios.png")


def dibujar_histograma(datos, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Colores de la paleta de referencia (ranuras 1 y 2), validados para modo claro.
    SUPERFICIE, TINTA, TINTA2, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
    AZUL, NARANJA = "#2a78d6", "#eb6834"
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.3), facecolor=SUPERFICIE)
    for ax, clave, titulo, ancho, tope in ((ejes[0], "peatones", "Peatones", 50, 800),
                                          (ejes[1], "vehiculos", "Vehículos", 100, 1600)):
        ax.set_facecolor(SUPERFICIE)
        bordes = list(range(-ancho, tope + ancho, ancho))   # la primera barra reúne los desvíos negativos
        for k, (esc, color, etiqueta) in enumerate((("lluvia", AZUL, "Con lluvia"),
                                                    ("medidas", NARANJA, "Con lluvia + medidas"))):
            xs = datos[clave][esc]
            cuentas = [0] * (len(bordes) - 1)
            for x in xs:
                cuentas[min(max(int((x + ancho) // ancho), 0), len(cuentas) - 1)] += 1
            xpos = [b + ancho * (0.05 + 0.45 * k) for b in bordes[:-1]]
            ax.bar(xpos, [max(c, 0.0) for c in cuentas], width=ancho * 0.43, align="edge", color=color,
                   edgecolor=SUPERFICIE, linewidth=1, label=etiqueta, bottom=0)
        ax.set_yscale("log")
        ax.set_ylim(0.8, None)
        ax.set_xlim(-ancho, tope)
        ax.text(-ancho / 2, 0.9, "< 0", ha="center", va="top", fontsize=7, color=TINTA2)
        ax.set_title(f"{titulo}: desvío por par de esquinas", loc="left", fontsize=11, color=TINTA)
        ax.set_xlabel("Desvío respecto al escenario seco (m)", color=TINTA2, fontsize=9)
        ax.set_ylabel("Pares de esquinas (escala logarítmica)", color=TINTA2, fontsize=9)
        ax.grid(axis="y", color=REJILLA, linewidth=0.8)
        ax.set_axisbelow(True)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(REJILLA)
        ax.tick_params(colors=TINTA2, labelsize=8)
        ax.legend(frameon=False, fontsize=9, labelcolor=TINTA2, loc="upper right")
    fig.text(0.01, 0.01, "La primera barra (< 0) son pares que mejoran respecto al escenario seco gracias a un atajo nuevo. "
             "Los pares sin camino no se grafican. Muestra de 120 esquinas por lado.", fontsize=7, color=TINTA2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    plt.close(fig)
    print(f"  -> {ruta.relative_to(RAIZ)}")


# --------------------------------------------------- sensibilidad de las propuestas calculadas
def _resumen_calculadas(plan):
    """Lo que se compara entre variantes: pasos (posiciones), controles, pares y capacidad, por etapa."""
    res = []
    for e in plan["etapas"]:
        pd, c = e["pasos_por_demanda"], e["circulacion"]
        res.append(dict(
            pasos=sorted(q["pos_m"] for q in (pd or {}).get("pasos", [])),
            controles=sorted(q["nombre"] for q in e["control_temporal"]["esquinas"]),
            pares=[(tuple(p["calles"]), p["elegida"]) for p in e["pares_viales"]["pares"]],
            capacidad=None if not c else (c["capacidad"]["obra"]["a_b"], c["capacidad"]["obra"]["b_a"]),
            demanda_mejor_que_regla=None if not c else (
                c["peatones"]["con_pasos_por_demanda"]["desvio_positivo_m"]
                <= c["peatones"]["con_pasos_regla_500m"]["desvio_positivo_m"])))
    return res


def exp_calculadas(salida=None):
    """Recalcula las propuestas de El Salao cambiando un supuesto a la vez y dice qué cambia.

    - d0_m: 200, 400 (base) y 1000 m.
    - carriles: ±1 en las calles SIN etiqueta lanes de OSM (las que usan el supuesto por clase).
    - veh_h_carril: 600, 950 y 1900. No hace falta recalcular: es el mismo número en todas las calles, así
      que solo multiplica la capacidad (el corte mínimo en carriles y el orden de las alternativas no cambian).
    """
    from src.etapas import plan_por_etapas
    from src.supuestos import SUPUESTOS
    print("Sensibilidad de las propuestas calculadas (El Salao): unos 50 s")
    lineas = fuente.lineas_ejemplo()
    recuadro, _ = fuente.recuadro_de(lineas, RADIO)
    red, _ = fuente.red_para(recuadro)
    base_d0 = SUPUESTOS["d0_m"].valor

    def plan(d0):
        return _resumen_calculadas(plan_por_etapas(red, lineas, radio=RADIO, recuadro=recuadro,
                                                   propuestas_calculadas=True, d0_m=d0))

    variantes = {f"d0 = {base_d0} m (base)": plan(base_d0)}
    for d0 in (200, 1000):
        variantes[f"d0 = {d0} m"] = plan(d0)
    originales = {t.id: t.carriles_total for t in red.tramos if not t.carriles_de_osm}
    try:
        for delta in (-1, +1):
            for t in red.tramos:
                if t.id in originales:
                    t.carriles_total = max(1, originales[t.id] + delta)
            variantes[f"carriles {delta:+d} (sin lanes en OSM)"] = plan(base_d0)
    finally:
        for t in red.tramos:
            if t.id in originales:
                t.carriles_total = originales[t.id]
    base = variantes[f"d0 = {base_d0} m (base)"]
    filas, datos = [], {}
    for nombre, v in variantes.items():
        for k, (e, b) in enumerate(zip(v, base)):
            cambios = [clave for clave in ("pasos", "controles", "pares", "capacidad", "demanda_mejor_que_regla")
                       if e[clave] != b[clave]]
            filas.append([nombre, k + 1, len(e["pasos"]), ", ".join(e["controles"]) or "-",
                          "-" if e["capacidad"] is None else f"{e['capacidad'][0]} / {e['capacidad'][1]}",
                          "sí" if e["demanda_mejor_que_regla"] else "no",
                          "igual a la base" if not cambios else "cambia: " + ", ".join(cambios)])
        datos[nombre] = v
    md = ("Cada fila cambia un solo supuesto. «Cambia» lista qué propuestas son distintas a las de la base "
          "(si no cambia ninguna con ese supuesto, la propuesta es robusta frente a él).\n"
          "veh_h_carril (600, 950, 1900) no se recalcula: multiplica igual a todas las calles y no cambia el orden.\n\n"
          + tabla(["Variante", "Etapa", "Pasos por demanda", "Control temporal", "Carriles con obra (A->B / B->A)",
                   "Demanda mejor que la regla de 500 m", "Comparado con la base"], filas))
    print(md)
    for clave in ("pasos", "controles", "capacidad", "demanda_mejor_que_regla"):
        robusta = all(v[k][clave] == base[k][clave] for v in variantes.values() for k in range(len(base)))
        print(f"  {clave}: {'robusta' if robusta else 'depende de los supuestos'}")
    if salida:
        carpeta = Path(salida)
        if (RAIZ / "resultados") in [carpeta.resolve(), *carpeta.resolve().parents]:
            raise SystemExit("--salida no puede estar dentro de resultados/")
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / "sensibilidad_calculadas.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        (carpeta / "sensibilidad_calculadas.md").write_text(md, encoding="utf-8")
        print(f"  -> {carpeta}/sensibilidad_calculadas.json y .md")


EXPERIMENTOS = dict(voraz=exp_voraz, criticos=exp_criticos, sensibilidad=exp_sensibilidad,
                    control=exp_control, histograma=exp_histograma)
# Solo cuando se pide por nombre (no está en «todos»): no escribe en resultados/.
A_PEDIDO = dict(calculadas=exp_calculadas)

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):  # acentos bien en Windows con salida redirigida
        sys.stdout.reconfigure(encoding="utf-8")
    argumentos, salida = sys.argv[1:], None
    if "--salida" in argumentos:
        i = argumentos.index("--salida")
        if i + 1 >= len(argumentos):
            raise SystemExit("Falta la carpeta después de --salida")
        salida = argumentos[i + 1]
        argumentos = argumentos[:i] + argumentos[i + 2:]
    pedidos = argumentos or list(EXPERIMENTOS)
    todos = {**EXPERIMENTOS, **A_PEDIDO}
    desconocidos = [p for p in pedidos if p not in todos]
    if desconocidos:
        raise SystemExit(f"Experimento desconocido: {desconocidos}. Opciones: {', '.join(todos)}")
    for nombre in pedidos:
        t = time.time()
        todos[nombre](salida) if nombre in A_PEDIDO else todos[nombre]()
        print(f"  ({time.time() - t:.0f} s)\n")
