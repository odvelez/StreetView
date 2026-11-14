"""De dónde salen los datos: el ejemplo El Salao, obras guardadas en archivo, arroyos con nombre
(heredado) y la red vial de una zona."""
import csv
import json
import math
from pathlib import Path

from src import osm
from src.geometria import M_LAT, m_lon, orientar
from src.red import Red

MARGEN_M = 600          # calles adicionales alrededor de la zona de estudio, para no cortar desvíos
MAX_LADO_M = 6000       # tamaño máximo del recuadro, para que el cálculo termine en segundos
GRILLA = 0.002          # el recuadro se redondea a esta grilla (~220 m) para reutilizar redes ya armadas

_redes = {}
_local = None


def recuadro_de(lineas, radio):
    """Recuadro (sur, oeste, norte, este) alrededor de la obra y su lado más largo en metros."""
    lats = [p[0] for l in lineas for p in l]
    lons = [p[1] for l in lineas for p in l]
    lat0 = sum(lats) / len(lats)
    dlat = (radio + MARGEN_M) / M_LAT
    dlon = (radio + MARGEN_M) / m_lon(lat0)
    s, n = min(lats) - dlat, max(lats) + dlat
    o, e = min(lons) - dlon, max(lons) + dlon
    s, o = math.floor(s / GRILLA) * GRILLA, math.floor(o / GRILLA) * GRILLA
    n, e = math.ceil(n / GRILLA) * GRILLA, math.ceil(e / GRILLA) * GRILLA
    alto, ancho = (n - s) * M_LAT, (e - o) * m_lon(lat0)
    return (round(s, 4), round(o, 4), round(n, 4), round(e, 4)), max(alto, ancho)


def mapa_local():
    global _local
    if _local is None and osm.LOCAL.exists():
        _local = osm.MapaLocal()
    return _local


def red_para(recuadro):
    """(Red, descripción de la fuente) del recuadro: copia local si lo cubre; si no, Overpass."""
    if recuadro not in _redes:
        local = mapa_local()
        cuadros = osm.cuadros_que_cubren(recuadro)
        if local and local.contiene(recuadro):
            nodos, vias = local.recortar(recuadro)
            fuente = f"OpenStreetMap, copia local del {local.fecha}"
        elif cuadros:
            nodos, vias = osm.leer_cuadros(cuadros, recuadro)
            fuente = "OpenStreetMap, copia local (cuadros descargados)"
        else:
            nodos, vias = osm.descargar(recuadro)
            fuente = "OpenStreetMap, descargado con Overpass"
        _redes[recuadro] = (Red(nodos, vias), fuente)
        if len(_redes) > 8:
            _redes.pop(next(iter(_redes)))
    return _redes[recuadro]


def lineas_ejemplo():
    """Eje de la obra de canalización del arroyo El Salao en Soledad (caso de estudio del documento)."""
    with open(osm.DATOS / "arroyo_el_salao.csv", newline="", encoding="utf-8") as f:
        segs = [[(float(r["lat1"]), float(r["lon1"])), (float(r["lat2"]), float(r["lon2"]))]
                for r in csv.DictReader(f)]
    return orientar(segs)


def leer_obra(ruta):
    """Lee un archivo de obra (formato de equipo/cambio_a_obras.md, sección 8):

        {"nombre": "...", "ilustrativo": true, "lineas": [[[lat, lon], [lat, lon], ...], ...]}

    Devuelve dict(nombre, ilustrativo, lineas) con las líneas ya orientadas. `nombre` e
    `ilustrativo` son opcionales (por defecto, el nombre del archivo y False).
    Lanza ValueError con un mensaje claro si el archivo no tiene ese formato.
    """
    ruta = Path(ruta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise ValueError(f"{ruta.name} no es un JSON válido: {ex}") from None
    if not isinstance(datos, dict) or not isinstance(datos.get("lineas"), list):
        raise ValueError(f'{ruta.name} debe tener la forma {{"nombre": ..., "lineas": [[[lat, lon], ...]]}}.')
    lineas = []
    for k, linea in enumerate(datos["lineas"], 1):
        try:
            puntos = [(float(p[0]), float(p[1])) for p in linea if len(p) == 2]
        except (TypeError, ValueError):
            raise ValueError(f"{ruta.name}: la línea {k} tiene puntos que no son [lat, lon].") from None
        if len(puntos) != len(linea):
            raise ValueError(f"{ruta.name}: la línea {k} tiene puntos que no son [lat, lon].")
        if any(not (-90 <= la <= 90 and -180 <= lo <= 180) for la, lo in puntos):
            raise ValueError(f"{ruta.name}: la línea {k} tiene coordenadas fuera de rango (¿lat y lon al revés?).")
        if len(puntos) >= 2:
            lineas.append(puntos)
    if not lineas:
        raise ValueError(f"{ruta.name} no tiene ninguna línea con al menos dos puntos.")
    return dict(nombre=str(datos.get("nombre") or ruta.stem), ilustrativo=bool(datos.get("ilustrativo", False)),
                lineas=orientar(lineas))


def lineas_de_archivo(ruta):
    """Líneas [(lat, lon), ...] del eje de la obra guardada en `ruta` (ver `leer_obra`)."""
    return leer_obra(ruta)["lineas"]


def arroyos_osm():
    return json.loads((osm.DATOS / "arroyos_area_metropolitana.json").read_text(encoding="utf-8"))["arroyos"]


def lineas_por_nombre(nombre):
    """Todos los tramos de OpenStreetMap con ese nombre (sin distinguir mayúsculas)."""
    n = nombre.strip().lower()
    return orientar([a["coords"] for a in arroyos_osm() if a["nombre"].lower() == n])
