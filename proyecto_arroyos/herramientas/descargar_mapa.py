"""Descarga de OpenStreetMap las calles y los arroyos del área metropolitana de Barranquilla.

Uso:  python herramientas/descargar_mapa.py

Escribe:
  datos/calles_area_metropolitana.json.gz   calles (vías para carros y peatones)
  datos/archivo_arroyos/arroyos_area_metropolitana.json   cauces con su nombre (archivo histórico;
                                                          el programa ya no lo usa)

Solo hace falta ejecutarlo para ACTUALIZAR el mapa: los archivos ya vienen en el
proyecto. Los servidores públicos de Overpass rechazan consultas grandes, así que
el área se descarga en cuadros de unos 4 km. Cada cuadro se guarda en
datos/cache/cuadros/; si el programa se interrumpe, al volver a correrlo
continúa donde iba.
"""
import datetime
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import osm  # noqa: E402
from src.osm import CUADROS, PASO, RECUADRO  # noqa: E402


def pedir(consulta, intentos=6):
    cuerpo = urllib.parse.urlencode({"data": consulta}).encode()
    for i in range(intentos):
        url = osm.SERVIDORES[i % len(osm.SERVIDORES)]
        try:
            pedido = urllib.request.Request(url, data=cuerpo, headers={"User-Agent": "proyecto-arroyos-uninorte/1.0"})
            with urllib.request.urlopen(pedido, timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as ex:
            espera = 10 * (i + 1)
            print(f"    {url.split('/')[2]} falló ({str(ex)[:60]}); reintento en {espera} s", flush=True)
            time.sleep(espera)
    return None


CENTRO = (10.93, -74.79)   # entre Barranquilla y Soledad: estos cuadros se descargan primero


def cuadros():
    """Todos los cuadros del recuadro, del más cercano al centro urbano al más lejano."""
    return sorted(_cuadros(), key=lambda c: ((c[0] + c[2]) / 2 - CENTRO[0]) ** 2 + ((c[1] + c[3]) / 2 - CENTRO[1]) ** 2)


def _cuadros():
    s, o, n, e = RECUADRO
    lat = s
    while lat < n - 1e-9:
        lon = o
        while lon < e - 1e-9:
            yield (round(lat, 4), round(lon, 4), round(min(lat + PASO, n), 4), round(min(lon + PASO, e), 4))
            lon += PASO
        lat += PASO


def main():
    CUADROS.mkdir(parents=True, exist_ok=True)
    lista = list(cuadros())
    pendientes = 0
    for i, c in enumerate(lista, 1):
        archivo = CUADROS / ("_".join(str(x) for x in c) + ".json")
        if archivo.exists():
            continue
        print(f"Cuadro {i}/{len(lista)} {c} ...", flush=True)
        t = time.time()
        datos = pedir(osm.consulta(c))
        if datos is None:
            print("    no se pudo; se intentará en la próxima ejecución", flush=True)
            pendientes += 1
            continue
        archivo.write_text(json.dumps(datos, separators=(",", ":")), encoding="utf-8")
        print(f"    listo: {len(datos['elements'])} elementos en {time.time() - t:.0f} s", flush=True)
    if pendientes:
        raise SystemExit(f"Faltan {pendientes} cuadros. Vuelva a ejecutar el programa para completarlos.")

    # Unir los cuadros: una vía que pasa por dos cuadros aparece en ambos con todos sus nodos.
    elementos = {}
    for archivo in sorted(CUADROS.glob("*.json")):
        for e in json.loads(archivo.read_text(encoding="utf-8"))["elements"]:
            elementos[(e["type"], e["id"])] = e
    hoy = datetime.date.today().isoformat()
    nn, nv = osm.guardar_local({"elements": list(elementos.values())}, RECUADRO, hoy)
    print(f"Calles: {nn} nodos, {nv} vías -> {osm.LOCAL}", flush=True)

    s, o, n, e = RECUADRO
    agua = pedir(f'[out:json][timeout:300];way["waterway"~"^(stream|river|canal|drain|ditch)$"]'
                 f"({s},{o},{n},{e});out tags geom;")
    if agua is None:
        print("No se pudieron actualizar los arroyos; se conserva el archivo anterior.")
        return
    arroyos = [dict(id=x["id"], nombre=x.get("tags", {}).get("name", ""), tipo=x["tags"].get("waterway"),
                    tunel=x["tags"].get("tunnel", "") or x["tags"].get("location", ""),
                    coords=[[round(p["lat"], 6), round(p["lon"], 6)] for p in x["geometry"]])
               for x in agua["elements"] if not x.get("tags", {}).get("name", "").startswith("Río Magdalena")]
    destino = osm.DATOS / "archivo_arroyos" / "arroyos_area_metropolitana.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(dict(fuente=f"OpenStreetMap (ODbL), descargado el {hoy}", recuadro=list(RECUADRO),
                                       arroyos=arroyos), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Arroyos: {len(arroyos)} tramos -> {destino}", flush=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):  # acentos bien en Windows con salida redirigida
        sys.stdout.reconfigure(encoding="utf-8")
    main()
