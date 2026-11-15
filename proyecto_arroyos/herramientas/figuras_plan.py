"""Figuras del plan por etapas, para el documento y las diapositivas.

Uso (desde proyecto_arroyos/):
    python herramientas/figuras_plan.py

Lee resultados/plan_etapas.json (no recalcula el plan) y guarda en resultados/figuras/:
    plan_mapa.png     eje de la obra por etapa, pasos peatonales provisionales, cambios de sentido,
                      tramos cerrados y esquinas a controlar
    desvio_a_pie.png  desvío medio a pie por etapa: con la obra y con los pasos peatonales

Colores Okabe-Ito (se distinguen con daltonismo). Las calles de fondo salen de las descargas
guardadas en datos/cache/ (no se descarga nada si la zona ya está guardada).
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from src import fuente

PLAN = RAIZ / "resultados" / "plan_etapas.json"
SALIDA = RAIZ / "resultados" / "figuras"

# Okabe-Ito. Las etapas usan azul, verde azulado y celeste; las medidas, naranja y morado;
# las esquinas sin semáforo registrado, bermellón.
ETAPAS = ["#0072B2", "#009E73", "#56B4E9", "#000000", "#F0E442"]
NARANJA, MORADO, BERMELLON = "#E69F00", "#CC79A7", "#D55E00"
CALLE, CERRADA, TINTA, TENUE = "#d4d4d0", "#555555", "#1F2933", "#5f6b76"
CREDITO = "© colaboradores de OpenStreetMap (ODbL)"


def color_etapa(n):
    return ETAPAS[(n - 1) % len(ETAPAS)]


def lonlat(puntos):
    ys, xs = zip(*puntos)
    return xs, ys


def tramos_continuos(puntos, salto_m=250):
    """Parte una polilínea donde dos puntos seguidos están a más de salto_m (piezas separadas del eje)."""
    piezas, actual = [], [puntos[0]]
    for a, b in zip(puntos, puntos[1:]):
        dy = (b[0] - a[0]) * 110600
        dx = (b[1] - a[1]) * 110600 * 0.982
        if (dx * dx + dy * dy) ** 0.5 > salto_m:
            piezas.append(actual)
            actual = []
        actual.append(b)
    piezas.append(actual)
    return [p for p in piezas if len(p) >= 2]


def mapa(plan, ruta, radio=400):
    lineas = plan["obra"]["lineas"]
    recuadro, _ = fuente.recuadro_de([[tuple(p) for p in l] for l in lineas], radio)
    red, _ = fuente.red_para(recuadro)

    fig, ax = plt.subplots(figsize=(10, 7.5))
    for t in red.tramos:
        ax.plot(*lonlat(t.forma), color=CALLE, lw=0.6 if t.vehicular else 0.4, zorder=1)

    for e in plan["etapas"]:
        c = color_etapa(e["numero"])
        for i in e["tramos_cerrados"]:
            ax.plot(*lonlat(red.tramos[i].forma), color=CERRADA, lw=1.2, zorder=2)
        eje = e.get("eje") or e.get("cauce") or []
        if len(eje) >= 2:
            piezas = tramos_continuos(eje)
            for pieza in piezas:
                ax.plot(*lonlat(pieza), color=c, lw=5, solid_capstyle="round", zorder=3)
            mayor = max(piezas, key=len)
            my, mx = mayor[len(mayor) // 2]
            ax.annotate(f"Etapa {e['numero']}", (mx, my), xytext=(0, 14), textcoords="offset points",
                        ha="center", fontsize=9, fontweight="bold", color=TINTA, zorder=9,
                        bbox=dict(fc="white", ec=c, lw=1.5, boxstyle="round,pad=0.25"))
        for q in (e.get("vehiculos") or {}).get("medidas", []):
            ax.plot(*lonlat(q["forma"]), color=MORADO, lw=4, solid_capstyle="round", zorder=4)
        for q in (e.get("peatones") or {}).get("puentes", []):
            ax.plot(*lonlat(q["forma"]), color=NARANJA, lw=3, zorder=5)
            my, mx = q["forma"][len(q["forma"]) // 2]
            ax.plot(mx, my, "o", color=NARANJA, ms=12, mec="white", mew=2, zorder=6)
        for c_ in e.get("carga", []):
            la, lo = c_["posicion"]
            if c_["semaforo"] is False:
                ax.plot(lo, la, "o", color=BERMELLON, ms=8, mec="white", mew=1.5, zorder=7)
            else:
                ax.plot(lo, la, "o", mfc="white", mec=TENUE, ms=8, mew=1.8, zorder=7)

    todos = [p for l in lineas for p in l]
    m = radio / 110600
    ax.set_ylim(min(p[0] for p in todos) - m, max(p[0] for p in todos) + m)
    ax.set_xlim(min(p[1] for p in todos) - m, max(p[1] for p in todos) + m)
    ax.set_aspect(1 / 0.982)
    ax.set_xticks([])
    ax.set_yticks([])
    for lado in ax.spines.values():
        lado.set_color(CALLE)
    etapas = [Line2D([], [], color=color_etapa(e["numero"]), lw=5,
                     label=f"Etapa {e['numero']}: metro {e['inicio_m']} al {e['fin_m']}") for e in plan["etapas"]]
    ax.legend(handles=etapas + [
        Line2D([], [], color=CERRADA, lw=1.2, label="Tramo cerrado durante su etapa"),
        Line2D([], [], color=NARANJA, lw=3, marker="o", ms=9, mec="white", label="Paso peatonal provisional"),
        Line2D([], [], color=MORADO, lw=4, label="Cambio de sentido (doble sentido)"),
        Line2D([], [], ls="", marker="o", color=BERMELLON, ms=8, mec="white", label="Esquina a controlar, sin semáforo registrado"),
        Line2D([], [], ls="", marker="o", mfc="white", mec=TENUE, ms=8, mew=1.8, label="Esquina a controlar, con semáforo"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, frameon=False, fontsize=8.5)
    ax.text(0.995, 0.008, f"Datos del mapa: {CREDITO}", transform=ax.transAxes, ha="right", fontsize=7,
            color=TENUE, bbox=dict(fc="white", ec="none", pad=2, alpha=0.9), zorder=10)
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)


def barras(plan, ruta):
    etapas = [e for e in plan["etapas"] if e.get("peatones")]
    obra = [e["peatones"]["obra"]["desvio_medio_m"] for e in etapas]
    pasos = [e["peatones"]["con_puentes"]["desvio_medio_m"] for e in etapas]
    n_pasos = [len(e["peatones"]["puentes"]) for e in etapas]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = range(len(etapas))
    ancho = 0.36
    b1 = ax.bar([i - ancho / 2 - 0.01 for i in x], obra, ancho, color=TENUE, label="Con la obra", zorder=3)
    b2 = ax.bar([i + ancho / 2 + 0.01 for i in x], pasos, ancho, color=NARANJA,
                label="Con los pasos peatonales provisionales", zorder=3)
    for barras_, valores in ((b1, obra), (b2, pasos)):
        for b, v in zip(barras_, valores):
            ax.text(b.get_x() + b.get_width() / 2, v + max(obra) * 0.015, f"{v:.0f} m", ha="center",
                    va="bottom", fontsize=9, color=TINTA)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Etapa {e['numero']}\n({e['longitud_m']} m, {k} {'paso' if k == 1 else 'pasos'})"
                        for e, k in zip(etapas, n_pasos)], fontsize=9, color=TINTA)
    ax.set_ylabel("Desvío medio a pie (m)", color=TINTA)
    ax.set_ylim(0, max(obra) * 1.15)
    ax.grid(axis="y", color="#e6e6e3", lw=0.8, zorder=0)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#bdbdb8")
    ax.tick_params(colors=TENUE)
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    ax.set_title("Desvío medio a pie por etapa (El Salao)", fontsize=11, color=TINTA, loc="left")
    fig.text(0.99, 0.01, f"Fuente: resultados/plan_etapas.json. Datos: {CREDITO}", ha="right",
             fontsize=6.5, color=TENUE)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ruta, dpi=200)
    plt.close(fig)


def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    SALIDA.mkdir(parents=True, exist_ok=True)
    mapa(plan, SALIDA / "plan_mapa.png", radio=plan.get("parametros", {}).get("radio_m", 400))
    barras(plan, SALIDA / "desvio_a_pie.png")
    print(f"Figuras guardadas en {SALIDA.relative_to(RAIZ)}: plan_mapa.png, desvio_a_pie.png")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
