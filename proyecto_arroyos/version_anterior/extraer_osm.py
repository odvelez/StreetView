"""Convierte el mapa de OpenStreetMap en los CSV que usa el programa.

Uso:  python herramientas/extraer_osm.py

Lee  datos/sector_soledad.osm  y escribe:
  datos/nodos.csv    intersecciones (id, lat, lon, nombre)
  datos/aristas.csv  tramos de calle (u, v, metros, via, clase)
  datos/arroyo.csv   segmentos del cauce principal
  datos/cruces.csv   tramos en contacto con el arroyo y cómo se comportan con lluvia

Solo se usa para PREPARAR los datos. Si corrigen a mano datos/cruces.csv,
no vuelvan a ejecutar este script, porque sobrescribe ese archivo.
"""
import csv
import math
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
OSM = RAIZ / "datos" / "sector_soledad.osm"

# Vías por las que puede circular una moto o un carro.
CLASES = {"residential", "tertiary", "primary", "primary_link", "secondary",
          "trunk", "trunk_link", "unclassified", "service", "living_street"}

# Cauce principal: tramos con nombre "Arroyo El Salao" y su paso bajo la Murillo.
PASO_MURILLO = "177838918"

# Metros por grado cerca de la latitud 10.9 (aproximación local plana).
M_LAT, M_LON = 110600, 109300

# Distancia máxima al cauce (m) y fracción mínima para decir que una calle va SOBRE él.
DIST_CAUCE, FRAC_CAUCE = 6, 0.6


def xy(p):
    return p[1] * M_LON, p[0] * M_LAT


def dist(a, b):
    ax, ay, bx, by = *xy(a), *xy(b)
    return math.hypot(ax - bx, ay - by)


def se_cruzan(a, b, c, d):
    """True si el segmento a-b corta al segmento c-d."""
    ax, ay, bx, by, cx, cy, dx, dy = *xy(a), *xy(b), *xy(c), *xy(d)
    den = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
    if abs(den) < 1e-9:
        return False
    t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / den
    u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / den
    return -1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6


def dist_punto_segmento(p, a, b):
    px, py, ax, ay, bx, by = *xy(p), *xy(a), *xy(b)
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    t = max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / l2)) if l2 else 0
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


def leer_osm():
    nodos, vias = {}, {}
    for e in ET.parse(OSM).getroot():
        tags = {t.get("k"): t.get("v") for t in e.findall("tag")}
        if e.tag == "node":
            nodos[e.get("id")] = (float(e.get("lat")), float(e.get("lon")))
        elif e.tag == "way":
            refs = [n.get("ref") for n in e.findall("nd") if n.get("ref") in nodos]
            vias[e.get("id")] = (refs, tags)
    return nodos, vias


def main():
    nodos, vias = leer_osm()
    calles = {w: v for w, v in vias.items() if v[1].get("highway") in CLASES}

    cauce = []
    for w, (refs, t) in vias.items():
        if "waterway" in t and (t.get("name") == "Arroyo El Salao" or w == PASO_MURILLO):
            cauce += [(nodos[a], nodos[b], t) for a, b in zip(refs, refs[1:])]

    with open(RAIZ / "datos" / "arroyo.csv", "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f)
        c.writerow(["lat1", "lon1", "lat2", "lon2"])
        for a, b, _ in cauce:
            c.writerow([*a, *b])

    # Un nodo es intersección si lo usan dos calles o es extremo de una.
    usos = Counter()
    for refs, _ in calles.values():
        usos.update(refs)
        usos[refs[0]] += 1
        usos[refs[-1]] += 1

    aristas, nombres_nodo = [], {}
    for w, (refs, t) in calles.items():
        nombre = t.get("name", "")
        inicio = 0
        for i in range(1, len(refs)):
            if usos[refs[i]] <= 1 and i != len(refs) - 1:
                continue
            tramo = refs[inicio: i + 1]
            inicio = i
            metros = sum(dist(nodos[a], nodos[b]) for a, b in zip(tramo, tramo[1:]))
            corta, muestras = False, []
            for a, b in zip(tramo, tramo[1:]):
                pa, pb = nodos[a], nodos[b]
                corta = corta or any(se_cruzan(pa, pb, s[0], s[1]) for s in cauce)
                n = max(1, int(dist(pa, pb) // 5))
                for j in range(n + 1):
                    q = (pa[0] + (pb[0] - pa[0]) * j / n, pa[1] + (pb[1] - pa[1]) * j / n)
                    muestras.append(min(dist_punto_segmento(q, s[0], s[1]) for s in cauce))
            frac = sum(d < DIST_CAUCE for d in muestras) / len(muestras)
            aristas.append(dict(u=tramo[0], v=tramo[-1], metros=round(metros, 1), via=nombre,
                                clase=t["highway"], puente=t.get("bridge") == "yes",
                                corta=corta, sobre=frac > FRAC_CAUCE))
            for extremo in (tramo[0], tramo[-1]):
                if nombre:
                    nombres_nodo.setdefault(extremo, set()).add(nombre)

    ids = sorted({a["u"] for a in aristas} | {a["v"] for a in aristas})
    d = RAIZ / "datos"
    with open(d / "nodos.csv", "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f)
        c.writerow(["id", "lat", "lon", "nombre"])
        for i in ids:
            c.writerow([i, *nodos[i], " x ".join(sorted(nombres_nodo.get(i, [])))])
    with open(d / "aristas.csv", "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f)
        c.writerow(["u", "v", "metros", "via", "clase"])
        for a in aristas:
            c.writerow([a["u"], a["v"], a["metros"], a["via"], a["clase"]])
    with open(d / "cruces.csv", "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f)
        c.writerow(["u", "v", "via", "metros", "lat", "lon", "tipo", "bloqueado_lluvia",
                    "confirmado", "nota"])
        for a in aristas:
            if a["puente"] and (a["corta"] or a["sobre"]):
                tipo, bloqueado = "puente", 0
            elif a["corta"] or a["sobre"]:
                tipo, bloqueado = ("sobre_cauce" if a["sobre"] else "a_nivel"), 1
            else:
                continue
            la = (nodos[a["u"]][0] + nodos[a["v"]][0]) / 2
            lo = (nodos[a["u"]][1] + nodos[a["v"]][1]) / 2
            c.writerow([a["u"], a["v"], a["via"], a["metros"], round(la, 6), round(lo, 6),
                        tipo, bloqueado, "no", "Clasificado desde etiquetas de OpenStreetMap"])
    print(f"{len(ids)} nodos, {len(aristas)} aristas")


if __name__ == "__main__":
    main()
