"""Diagnóstico: ¿por qué hay pares de vehículos sin camino con lluvia en El Salao?

Uso (desde proyecto_arroyos/):   python herramientas/diagnostico_sin_camino.py

Lista las esquinas a las que no se puede llegar en el grafo dirigido de lluvia y los
tramos que las rodean, para comprobar en OpenStreetMap y en Street View.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import fuente
from src.analisis import clasificar, tablas, zona
from src.geometria import Arroyo, orientar
from src.grafo import dijkstra


def main(radio=400):
    lineas = fuente.lineas_ejemplo()
    recuadro, _ = fuente.recuadro_de(lineas, radio)
    red, _ = fuente.red_para(recuadro)
    arroyo = Arroyo(orientar(lineas), red.plano)
    contacto, inundadas = clasificar(red, arroyo)
    excluir = {i for i, (e, _) in contacto.items() if e == "bloqueado"}
    seco, lluvia = red.grafo_vehiculos(), red.grafo_vehiculos(excluir)
    todos, lados, _ = zona(red, arroyo, radio, red.grafo_peatones(), seco, inundadas)
    origenes = sorted(set(lados[1]) | set(lados[-1]))
    pares = [(a, b) for a in lados[1] for b in lados[-1]] + [(b, a) for a in lados[1] for b in lados[-1]]
    Fs = tablas(seco, origenes, set(origenes))
    Fl = tablas(lluvia, origenes, set(origenes))
    pares = [(a, b) for a, b in pares if b in Fs[a]]
    sin = [(a, b) for a, b in pares if b not in Fl[a]]
    print(f"Pares con camino en seco: {len(pares)}.  Sin camino con lluvia: {len(sin)}")
    print("Destinos que no se alcanzan:", Counter(b for _, b in sin).most_common())

    # Para cada esquina de la zona: ¿cuántas esquinas del lado opuesto NO pueden llegar a ella?
    # (Dijkstra sobre el grafo invertido: alcanza a todas las que pueden llegar a n.)
    inv = lluvia.invertido()
    lado_de = {n: s for s in (1, -1) for n in todos[s]}
    incomunicadas = []
    for n, s in lado_de.items():
        otros = set(todos[-s])
        llegan = dijkstra(inv, n, objetivos=otros)[0] if n in inv.adj else {}
        faltan = len(otros - set(llegan))
        if faltan:
            incomunicadas.append((faltan, n))
    print(f"\nEn toda la zona ({len(lado_de)} esquinas) hay {len(incomunicadas)} esquinas a las que "
          "no llega alguna esquina del lado opuesto:")
    for faltan, n in sorted(incomunicadas, reverse=True)[:10]:
        print(f"\n  esquina {n}  {red.pos[n]}  {red.nombre(n)}  lado {lado_de[n]}  "
              f"({'en la muestra' if n in origenes else 'fuera de la muestra'}); "
              f"no le llegan {faltan} de {len(todos[-lado_de[n]])} esquinas del otro lado")
        print(f"    https://www.openstreetmap.org/node/{n}")
        for t in red.tramos:
            if n in (t.u, t.v):
                print(f"    tramo {t.id}: {t.u} -> {t.v}, {t.metros:.1f} m, clase {t.clase}, "
                      f"sentido {t.sentido}, {contacto.get(t.id, ('libre',))[0]}")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):  # acentos bien en Windows con salida redirigida
        sys.stdout.reconfigure(encoding="utf-8")
    main()
