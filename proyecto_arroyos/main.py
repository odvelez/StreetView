"""Arroyos y desvíos: análisis por línea de comandos (la web está en app.py).

Ejemplos:
  python main.py                               # caso de estudio: arroyo El Salao (Soledad)
  python main.py --arroyo "Arroyo Don Juan"    # cualquier arroyo con nombre en OpenStreetMap
  python main.py --listar                      # nombres de los arroyos disponibles
  python main.py --radio 500 --k 3 --luz 80    # otros ajustes

Entrada: datos/ (calles y arroyos de OpenStreetMap).
Salida: resumen en pantalla y archivos en resultados/ (resumen.txt, analisis.json, mapa.png).
"""
import argparse
import json
import time
from collections import Counter
from pathlib import Path

from src import fuente
from src.analisis import analizar

SALIDA = Path(__file__).resolve().parent / "resultados"


def linea(nombre, m):
    sin = f"{m['sin_camino']:>10}" if m["sin_camino"] else f"{'-':>10}"
    return (f"  {nombre:<26}{m['distancia_media_m']:>9.0f}{m['desvio_medio_m']:>9.0f}"
            f"{m['pct_mayor_200m']:>10.1f}{m['desvio_max_m']:>9.0f}{sin}")


def informe(nombre, r):
    p = []
    p.append(f"ARROYO: {nombre}")
    p.append(f"Longitud del cauce analizado: {r['arroyo']['longitud_m']} m")
    p.append(f"Red vial: {r['red']['esquinas']} esquinas, {r['red']['tramos']} tramos ({r['fuente']})")
    p.append(f"Tramos bloqueados con lluvia: {r['red']['bloqueados']}   Puentes: {r['red']['puentes']}   "
             f"Esquinas dentro del cauce: {r['red']['esquinas_inundadas']}")
    lados = ", ".join(f"{v} en el {k}" for k, v in r["zona"]["lados"].items())
    muestra = ", ".join(f"{v}" for v in r["zona"]["muestra"].values())
    p.append(f"Zona de estudio (a {r['zona']['radio_m']:.0f} m del cauce): {lados}; muestra de {muestra} por lado")
    for a in r["avisos"]:
        p.append(f"AVISO: {a}")
    cab = f"  {'Escenario':<26}{'Media m':>9}{'Desvío':>9}{'% >200 m':>10}{'Máx m':>9}{'Sin cam.':>10}"
    for clave, titulo, medida in (("peatones", "PEATONES (grafo no dirigido)", "puente peatonal"),
                                  ("vehiculos", "VEHÍCULOS (grafo dirigido, respeta sentidos viales)", "doble sentido")):
        x = r.get(clave)
        if not x:
            continue
        p.append(f"\n{titulo}")
        p.append(cab)
        p.append(linea("Seco", x["seco"]))
        p.append(linea("Lluvia", x["lluvia"]))
        p.append(linea(f"Lluvia + {medida}", x["con_medida"]))
        p.append(f"  Candidatos evaluados: {x['candidatos']}")
        ll, cm = x["lluvia"], x["con_medida"]
        p.append(f"  Pares sin camino: {ll['sin_camino']} con lluvia -> {cm['sin_camino']} con medida "
                 f"({x['recuperados']} recuperados)")
        p.append(f"  Desvío medio sobre los mismos {ll['pares'] - ll['sin_camino']} pares que tenían camino con lluvia: "
                 f"{ll['desvio_fijo_m']:.1f} m -> {cm['desvio_fijo_m']:.1f} m")
        if not x["propuestas"]:
            p.append(f"  Ningún {medida} reduce el desvío medio al menos 2 %.")
        for q in x["propuestas"]:
            if clave == "peatones":
                donde = f"cruce de la {q['via']}" if q["tipo"] == "cruce" else "paso nuevo"
                p.append(f"  {q['orden']}. {q['desde']}  <->  {q['hasta']}  ({donde}, {q['recorrido_m']} m)"
                         f"  -> desvío {q['desvio_medio_m']:.0f} m")
            else:
                p.append(f"  {q['orden']}. {q['via']}: {q['desde']} -> {q['hasta']} ({q['metros']} m)"
                         f"  -> desvío {q['desvio_medio_m']:.0f} m")
    if r["rutas"]:
        p.append("\nRUTAS ALTERNAS (cruces que la lluvia cierra; metros en seco -> con lluvia)")
        for x in r["rutas"]:
            partes = []
            for quien, k in (("carro", "carro"), ("a pie", "pie")):
                if k in x:
                    v = x[k]
                    partes.append(f"{quien} {v['seco_m']} -> {v['lluvia_m'] if v['lluvia_m'] is not None else 'sin ruta'}")
            p.append(f"  {x['via']:<22} " + "   ".join(partes))
    return "\n".join(p)


def dibujar(r, ruta):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
    except ImportError:
        print("\nmatplotlib no está instalado: se omite el mapa (pip install matplotlib).")
        return
    red, _ = fuente.red_para(tuple(r["recuadro"]))
    AZUL, ROJO, VERDE, NARANJA, MORADO = "#2a78b5", "#c4362f", "#1b8a5a", "#d9730d", "#7b3fb0"
    fig, ax = plt.subplots(figsize=(10, 7.5))
    for t in red.tramos:
        ys, xs = zip(*t.forma)
        ax.plot(xs, ys, color="#d0d0cc", lw=0.6 if t.vehicular else 0.4, zorder=1)
    for l in r["arroyo"]["lineas"]:
        ys, xs = zip(*l)
        ax.plot(xs, ys, color=AZUL, lw=3.5, alpha=0.7, solid_capstyle="round", zorder=2)
    for t in r["contacto"]:
        ys, xs = zip(*t["forma"])
        ax.plot(xs, ys, color=ROJO if t["estado"] == "bloqueado" else VERDE, lw=2.2 if t["estado"] == "bloqueado" else 4, zorder=3)
    for q in (r.get("vehiculos") or {}).get("propuestas", []):
        ys, xs = zip(*q["forma"])
        ax.plot(xs, ys, color=MORADO, lw=3.5, zorder=4)
    for q in (r.get("peatones") or {}).get("propuestas", []):
        ys, xs = zip(*q["forma"])
        ax.plot(xs, ys, color=NARANJA, lw=3, ls=(0, (1, 1)), zorder=5)
        my, mx = q["forma"][len(q["forma"]) // 2]
        ax.plot(mx, my, "o", color=NARANJA, ms=14, mec="white", zorder=6)
        ax.text(mx, my, str(q["orden"]), color="white", ha="center", va="center", fontsize=9, fontweight="bold", zorder=7)
    lat = [p[0] for l in r["arroyo"]["lineas"] for p in l]
    lon = [p[1] for l in r["arroyo"]["lineas"] for p in l]
    m = r["zona"]["radio_m"] / 110600
    ax.set_ylim(min(lat) - m, max(lat) + m)
    ax.set_xlim(min(lon) - m, max(lon) + m)
    ax.set_aspect(1 / 0.982)
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_color("#d0d0cc")
    ax.legend(handles=[
        Line2D([], [], color=AZUL, lw=3.5, alpha=0.7, label="Arroyo"),
        Line2D([], [], color=ROJO, lw=2.2, label="Tramo bloqueado con lluvia"),
        Line2D([], [], color=VERDE, lw=4, label="Puente existente"),
        Line2D([], [], marker="o", ls=(0, (1, 1)), color=NARANJA, ms=9, label="Puente peatonal propuesto"),
        Line2D([], [], color=MORADO, lw=3.5, label="Calle propuesta a doble sentido"),
    ], loc="lower left", framealpha=0.95, edgecolor="#d0d0cc", fontsize=9)
    ax.text(0.995, 0.008, "Datos del mapa: © colaboradores de OpenStreetMap (ODbL)", transform=ax.transAxes,
            ha="right", fontsize=7, color="#555", bbox=dict(fc="white", ec="none", pad=2, alpha=0.9), zorder=9)
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nMapa guardado en {ruta.relative_to(SALIDA.parent)}")


def main():
    ap = argparse.ArgumentParser(description="Desvíos por arroyos y medidas temporales mientras se canalizan.")
    ap.add_argument("--arroyo", help='nombre del arroyo en OpenStreetMap (por defecto, el ejemplo El Salao)')
    ap.add_argument("--listar", action="store_true", help="lista los arroyos con nombre disponibles")
    ap.add_argument("--radio", type=float, default=400, help="metros a cada lado del cauce (por defecto 400)")
    ap.add_argument("--luz", type=float, default=60, help="largo máximo de un puente peatonal nuevo (por defecto 60)")
    ap.add_argument("--k", type=int, default=3, help="medidas a proponer de cada tipo (por defecto 3)")
    ap.add_argument("--sin-mapa", action="store_true", help="no genera resultados/mapa.png")
    args = ap.parse_args()

    if args.listar:
        conteo = Counter(a["nombre"] for a in fuente.arroyos_osm() if a["nombre"])
        for nombre, n in sorted(conteo.items()):
            print(f"{nombre}  ({n} tramos)")
        return
    if not (100 <= args.radio <= 800) or not (1 <= args.k <= 3) or not (10 <= args.luz <= 150):
        ap.error("--radio entre 100 y 800, --k entre 1 y 3, --luz entre 10 y 150")

    if args.arroyo:
        nombre, lineas = args.arroyo, fuente.lineas_por_nombre(args.arroyo)
        if not lineas:
            raise SystemExit(f"No hay ningún arroyo llamado «{args.arroyo}». Use --listar para ver los nombres.")
    else:
        nombre, lineas = "Arroyo El Salao, Soledad (caso de estudio)", fuente.lineas_ejemplo()

    recuadro, lado = fuente.recuadro_de(lineas, args.radio)
    if lado > fuente.MAX_LADO_M:
        raise SystemExit(f"El arroyo ocupa una zona de {lado / 1000:.1f} km: es demasiado grande. "
                         "Use la web para marcar solo un tramo.")
    t = time.time()
    red, origen = fuente.red_para(recuadro)
    r = analizar(red, lineas, radio=args.radio, luz_max=args.luz, k=args.k)
    r["fuente"], r["recuadro"] = origen, recuadro
    texto = informe(nombre, r)
    print(texto)
    print(f"\nTiempo: {time.time() - t:.1f} s")

    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "resumen.txt").write_text(texto + "\n", encoding="utf-8")
    (SALIDA / "analisis.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    if not args.sin_mapa:
        dibujar(r, SALIDA / "mapa.png")


if __name__ == "__main__":
    main()
