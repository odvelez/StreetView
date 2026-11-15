"""Genera un archivo de obra ilustrativa a lo largo de una calle.

Uso (desde proyecto_arroyos/):
    python herramientas/eje_de_calle.py --calle "Calle 72" --largo-m 600 \\
        --salida datos/ejemplos/obra_ilustrativa.json [--png resultados/obra_ilustrativa.png]

Toma los tramos con ese nombre de las calles ya descargadas de OpenStreetMap (por defecto, las de la
zona de El Salao), los une empezando por un extremo del tramo continuo más largo y sigue siempre lo más
recto posible hasta completar el largo pedido. Guarda el eje de la obra con el formato de
README.md (sección 2). **Es un ejemplo ilustrativo: no es una obra real**, y el archivo lo dice.
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src import fuente


def _componente_mas_largo(tramos):
    """El conjunto de tramos conectados entre sí con más metros."""
    por_nodo = defaultdict(list)
    for t in tramos:
        por_nodo[t.u].append(t)
        por_nodo[t.v].append(t)
    vistos, mejor = set(), []
    for t in tramos:
        if t.id in vistos:
            continue
        comp, pila = [], [t]
        while pila:
            x = pila.pop()
            if x.id in vistos:
                continue
            vistos.add(x.id)
            comp.append(x)
            for n in (x.u, x.v):
                pila += [y for y in por_nodo[n] if y.id not in vistos]
        if sum(x.metros for x in comp) > sum(x.metros for x in mejor):
            mejor = comp
    return mejor, por_nodo


def _direccion(plano, a, b):
    """Vector unitario (en metros) de a hacia b."""
    ax, ay = plano.xy(a)
    bx, by = plano.xy(b)
    d = math.hypot(bx - ax, by - ay) or 1.0
    return (bx - ax) / d, (by - ay) / d


def eje_de_calle(red, calle, largo_m):
    """Puntos (lat, lon) del eje de `calle` en `largo_m` metros, y el largo real que se logró.

    Solo usa tramos de vehículos con ese nombre (sin distinguir mayúsculas). Si la calle no llega al
    largo pedido, devuelve toda la que hay. Lanza ValueError si no hay ningún tramo con ese nombre.
    """
    nombre = calle.strip().lower()
    tramos = [t for t in red.tramos if t.vehicular and t.via.strip().lower() == nombre]
    if not tramos:
        parecidas = sorted({t.via for t in red.tramos if t.via and nombre in t.via.lower()})[:8]
        raise ValueError(f"No hay tramos de vehículos llamados «{calle}»." +
                         (f" Parecidos: {', '.join(parecidas)}." if parecidas else ""))
    comp, por_nodo = _componente_mas_largo(tramos)
    ids = {t.id for t in comp}
    grado = defaultdict(int)
    for t in comp:
        grado[t.u] += 1
        grado[t.v] += 1
    extremos = [n for n, g in grado.items() if g == 1] or list(grado)
    actual = min(extremos, key=lambda n: (red.pos[n][1], red.pos[n][0]))     # el extremo más al occidente

    puntos, recorrido, usados, ultimo = [red.pos[actual]], 0.0, set(), None
    while recorrido < largo_m:
        opciones = [t for t in por_nodo[actual] if t.id in ids and t.id not in usados]
        if not opciones:
            break

        def forma_desde(t):
            return t.forma if t.u == actual else t.forma[::-1]

        if ultimo is None:
            t = max(opciones, key=lambda t: t.metros)
        else:       # seguir lo más recto posible
            t = max(opciones, key=lambda t: sum(
                a * b for a, b in zip(ultimo, _direccion(red.plano, *forma_desde(t)[:2]))))
        usados.add(t.id)
        forma = forma_desde(t)
        for a, b in zip(forma, forma[1:]):
            paso = red.plano.dist(a, b)
            if recorrido + paso >= largo_m:
                f = (largo_m - recorrido) / paso if paso else 0.0
                puntos.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
                return [(round(p[0], 7), round(p[1], 7)) for p in puntos], float(largo_m)
            puntos.append(b)
            recorrido += paso
            ultimo = _direccion(red.plano, a, b)
        actual = t.v if t.u == actual else t.u
    return [(round(p[0], 7), round(p[1], 7)) for p in puntos], recorrido


def archivo_de_obra(calle, puntos):
    return {"nombre": f"Obra ilustrativa en la {calle}: no es una obra real", "ilustrativo": True,
            "lineas": [[list(p) for p in puntos]]}


def dibujar(red, puntos, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 6))
    for t in red.tramos:
        ys, xs = zip(*t.forma)
        ax.plot(xs, ys, color="#d0d0cc", lw=0.5)
    ys, xs = zip(*puntos)
    ax.plot(xs, ys, color="#D55E00", lw=3)
    ax.plot(xs[0], ys[0], "o", color="#0072B2", ms=8)
    ax.set_xlim(min(xs) - 0.004, max(xs) + 0.004)
    ax.set_ylim(min(ys) - 0.003, max(ys) + 0.003)
    ax.set_aspect(1 / 0.982)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Obra ilustrativa (no es una obra real)", loc="left", fontsize=10)
    ax.text(0.995, 0.008, "Datos del mapa: © colaboradores de OpenStreetMap (ODbL)", transform=ax.transAxes,
            ha="right", fontsize=7, color="#555")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Eje de obra ilustrativa a lo largo de una calle.")
    ap.add_argument("--calle", required=True, help='nombre exacto en OpenStreetMap, por ejemplo "Calle 72"')
    ap.add_argument("--largo-m", type=float, default=600, help="largo de la obra en metros (por defecto 600)")
    ap.add_argument("--salida", required=True, help="archivo JSON de salida")
    ap.add_argument("--png", help="opcional: dibuja el eje para comprobarlo")
    args = ap.parse_args()

    lineas = fuente.lineas_ejemplo()
    recuadro, _ = fuente.recuadro_de(lineas, 400)       # la zona de El Salao, ya descargada
    red, _ = fuente.red_para(recuadro)
    try:
        puntos, largo = eje_de_calle(red, args.calle, args.largo_m)
    except ValueError as ex:
        raise SystemExit(str(ex))
    if largo < args.largo_m - 1:
        print(f"AVISO: la calle solo da {largo:.0f} m de los {args.largo_m:.0f} pedidos.")
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    obra = archivo_de_obra(args.calle, puntos)
    # Una línea por punto, para que el archivo se lea y se compare fácil.
    lineas_de_puntos = ",\n   ".join(json.dumps(list(p)) for p in obra["lineas"][0])
    texto = ('{"nombre": ' + json.dumps(obra["nombre"], ensure_ascii=False) + ', "ilustrativo": true,\n'
             ' "lineas": [[' + lineas_de_puntos + ']]}\n')
    salida.write_text(texto, encoding="utf-8")
    print(f"{len(puntos)} puntos, {largo:.0f} m, de {puntos[0]} a {puntos[-1]} -> {salida}")
    if args.png:
        dibujar(red, puntos, Path(args.png))
        print(f"Dibujo en {args.png}")


if __name__ == "__main__":
    main()
