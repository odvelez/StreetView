"""Lectura de calles de OpenStreetMap.

Todas las fuentes dan el mismo resultado, (nodos, vias):
  nodos = {id: (lat, lon)}
  vias  = {id: (lista_de_ids_de_nodo, etiquetas)}

- MapaLocal: todas las calles del área metropolitana, descargadas una vez y
  guardadas en datos/calles_area_metropolitana.json.gz. Funciona sin internet.
- descargar(recuadro): consulta el servicio Overpass (para zonas fuera del
  área guardada) y guarda la respuesta en datos/cache/.
- leer_xml(ruta): un archivo .osm exportado desde openstreetmap.org.
"""
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATOS = Path(__file__).resolve().parent.parent / "datos"
CACHE = DATOS / "cache"
LOCAL = DATOS / "calles_area_metropolitana.json.gz"
CUADROS = CACHE / "cuadros"

# Área metropolitana (sur, oeste, norte, este) y tamaño de los cuadros de descarga.
RECUADRO = (10.84, -74.96, 11.12, -74.73)
PASO = 0.035

# Etiquetas de OpenStreetMap que usa el modelo; las demás se descartan al guardar.
ETIQUETAS = ("highway", "name", "oneway", "junction", "bridge", "man_made", "access",
             "motor_vehicle", "vehicle", "foot", "area")

# Servidores públicos de Overpass. Si uno está saturado se prueba el siguiente.
SERVIDORES = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

TIPOS_VIA = ("motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|"
             "secondary_link|tertiary|tertiary_link|unclassified|residential|living_street|"
             "service|road|footway|pedestrian|path|steps|track|cycleway")


class ErrorDescarga(Exception):
    pass


def leer_xml(ruta):
    nodos, vias = {}, {}
    for e in ET.parse(ruta).getroot():
        if e.tag == "node":
            nodos[e.get("id")] = (float(e.get("lat")), float(e.get("lon")))
        elif e.tag == "way":
            tags = {t.get("k"): t.get("v") for t in e.findall("tag")}
            refs = [n.get("ref") for n in e.findall("nd")]
            vias[e.get("id")] = (refs, tags)
    return _limpiar(nodos, vias)


def leer_json(datos):
    nodos, vias = {}, {}
    for e in datos["elements"]:
        if e["type"] == "node":
            nodos[str(e["id"])] = (e["lat"], e["lon"])
        elif e["type"] == "way":
            vias[str(e["id"])] = ([str(n) for n in e["nodes"]], e.get("tags", {}))
    return _limpiar(nodos, vias)


def _limpiar(nodos, vias):
    """Quita de cada vía los nodos que quedaron fuera del recuadro descargado."""
    limpias = {}
    for w, (refs, tags) in vias.items():
        refs = [r for r in refs if r in nodos]
        if len(refs) >= 2:
            limpias[w] = (refs, tags)
    return nodos, limpias


def consulta(recuadro):
    s, o, n, e = recuadro
    return (f'[out:json][timeout:120];way["highway"~"^({TIPOS_VIA})$"]'
            f"({s:.5f},{o:.5f},{n:.5f},{e:.5f});(._;>;);out body qt;")


def descargar(recuadro, intentos_por_servidor=2):
    """Descarga las calles del recuadro (sur, oeste, norte, este) o las lee del caché."""
    q = consulta(recuadro)
    CACHE.mkdir(parents=True, exist_ok=True)
    archivo = CACHE / f"calles_{hashlib.sha1(q.encode()).hexdigest()[:16]}.json"
    if archivo.exists():
        return leer_json(json.loads(archivo.read_text(encoding="utf-8")))

    cuerpo = urllib.parse.urlencode({"data": q}).encode()
    errores = []
    for url in SERVIDORES:
        for intento in range(intentos_por_servidor):
            try:
                pedido = urllib.request.Request(
                    url, data=cuerpo, headers={"User-Agent": "proyecto-arroyos-uninorte/1.0"})
                with urllib.request.urlopen(pedido, timeout=150) as r:
                    texto = r.read().decode("utf-8")
                datos = json.loads(texto)
                archivo.write_text(texto, encoding="utf-8")
                return leer_json(datos)
            except Exception as ex:  # servidor saturado, sin internet, respuesta inválida...
                errores.append(f"{url}: {ex}")
                time.sleep(2 * (intento + 1))
    raise ErrorDescarga("No se pudieron descargar las calles de OpenStreetMap. "
                        "Revise la conexión a internet o intente en unos minutos.\n" + "\n".join(errores))


class MapaLocal:
    """Calles del área metropolitana guardadas en un archivo comprimido."""

    def __init__(self, ruta=LOCAL):
        with gzip.open(ruta, "rt", encoding="utf-8") as f:
            datos = json.load(f)
        self.recuadro = tuple(datos["recuadro"])
        self.fecha = datos["fecha"]
        self.nodos = {k: tuple(v) for k, v in datos["nodos"].items()}
        self.vias = datos["vias"]

    def contiene(self, recuadro):
        s, o, n, e = recuadro
        S, O, N, E = self.recuadro
        return S <= s and O <= o and n <= N and e <= E

    def recortar(self, recuadro):
        """Calles dentro del recuadro. Si una vía sale y vuelve a entrar, se parte en pedazos."""
        s, o, n, e = recuadro
        dentro = {k for k, (la, lo) in self.nodos.items() if s <= la <= n and o <= lo <= e}
        nodos, vias = {}, {}
        for w, refs, tags in self.vias:
            pedazo, parte = [], 0
            for r in refs + [None]:
                if r is not None and r in dentro:
                    pedazo.append(r)
                    continue
                if len(pedazo) >= 2:
                    vias[f"{w}.{parte}"] = (pedazo, tags)
                    for x in pedazo:
                        nodos[x] = self.nodos[x]
                    parte += 1
                pedazo = []
        return nodos, vias


def guardar_local(datos_overpass, recuadro, fecha, ruta=LOCAL):
    """Convierte una respuesta de Overpass en el archivo comprimido de MapaLocal."""
    nodos, vias = leer_json(datos_overpass)
    usados = {r for refs, _ in vias.values() for r in refs}
    compacto = dict(
        fuente="© colaboradores de OpenStreetMap, licencia ODbL", fecha=fecha, recuadro=list(recuadro),
        nodos={k: [round(v[0], 7), round(v[1], 7)] for k, v in nodos.items() if k in usados},
        vias=[[w, refs, {k: t[k] for k in ETIQUETAS if k in t}] for w, (refs, t) in vias.items()])
    with gzip.open(ruta, "wt", encoding="utf-8") as f:
        json.dump(compacto, f, ensure_ascii=False, separators=(",", ":"))
    return len(compacto["nodos"]), len(compacto["vias"])


def cuadros_que_cubren(recuadro):
    """Archivos de cuadros ya descargados que cubren el recuadro, o None si falta alguno."""
    s, o, n, e = recuadro
    S, O, N, E = RECUADRO
    if not (S <= s and O <= o and n <= N and e <= E):
        return None
    archivos = []
    i = 0
    while S + i * PASO < N - 1e-9:
        j = 0
        while O + j * PASO < E - 1e-9:
            c = (round(S + i * PASO, 4), round(O + j * PASO, 4),
                 round(min(S + (i + 1) * PASO, N), 4), round(min(O + (j + 1) * PASO, E), 4))
            if c[0] < n and s < c[2] and c[1] < e and o < c[3]:
                archivo = CUADROS / ("_".join(str(x) for x in c) + ".json")
                if not archivo.exists():
                    return None
                archivos.append(archivo)
            j += 1
        i += 1
    return archivos


def leer_cuadros(archivos, recuadro):
    """Une los cuadros y recorta el recuadro (partiendo las vías que salen de él)."""
    elementos = {}
    for a in archivos:
        for e in json.loads(a.read_text(encoding="utf-8"))["elements"]:
            elementos[(e["type"], e["id"])] = e
    nodos, vias = leer_json({"elements": list(elementos.values())})
    s, o, n, e = recuadro
    dentro = {k for k, (la, lo) in nodos.items() if s <= la <= n and o <= lo <= e}
    nodos_r, vias_r = {}, {}
    for w, (refs, tags) in vias.items():
        pedazo, parte = [], 0
        for r in refs + [None]:
            if r is not None and r in dentro:
                pedazo.append(r)
                continue
            if len(pedazo) >= 2:
                vias_r[f"{w}.{parte}"] = (pedazo, tags)
                for x in pedazo:
                    nodos_r[x] = nodos[x]
                parte += 1
            pedazo = []
    return nodos_r, vias_r
