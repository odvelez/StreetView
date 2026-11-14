"""Servidor web: mapa interactivo de arroyos de Barranquilla y su área metropolitana.

Uso:
  pip install flask
  python app.py
  Abrir http://localhost:5000 en el navegador.

Rutas:
  GET  /               la página (carpeta web/)
  GET  /api/arroyos    cauces de OpenStreetMap del área metropolitana
  GET  /api/ejemplo    el arroyo El Salao en Soledad, caso de estudio del documento
  GET  /api/ejemplo_obra  obra ilustrativa en la calle 72 (datos/ejemplos/obra_ilustrativa.json)
  POST /api/analizar   recibe el arroyo marcado y devuelve el análisis (src/analisis.py)
  POST /api/plan       recibe el eje de una obra y devuelve el plan por etapas (src/etapas.py)
"""
import hashlib
import json
import math
import threading
import time
from collections import OrderedDict
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from src import fuente, osm
from src.analisis import TOLERANCIA_M, analizar
from src.etapas import ETAPA_MAX_M, MEDICIONES, UN_PUENTE_CADA_M, plan_por_etapas

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"
MAX_PUNTOS = 2000        # puntos del eje de la obra, sumando todas las líneas
MAX_CACHE = 16           # planes guardados en memoria (los últimos pedidos distintos)

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024   # 1 MB: 2.000 puntos ocupan unos 50 kB

# Errores HTTP de las rutas /api/: siempre en JSON y en español, para que la página los muestre.
MENSAJES_HTTP = {
    400: "El pedido no se pudo leer. Vuelva a cargar la página e inténtelo de nuevo.",
    404: "Esa dirección no existe en este programa. Vuelva a la página de inicio.",
    405: "Esa dirección no acepta este tipo de pedido.",
    413: "El pedido es demasiado grande. Dibuje la obra con menos puntos.",
}


@app.errorhandler(Exception)
def error_inesperado(ex):
    """Cualquier error del análisis vuelve como JSON, para que la página lo muestre."""
    if isinstance(ex, HTTPException):
        if request.path.startswith("/api/"):
            return jsonify(error=MENSAJES_HTTP.get(ex.code, f"Error {ex.code} al atender el pedido.")), ex.code
        return ex
    app.logger.exception("Error al atender %s", request.path)
    return jsonify(error="Ocurrió un error inesperado al planificar esta obra. "
                         "Pruebe con otro tramo o revise la consola donde corre app.py."), 500


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    return send_from_directory(WEB, archivo)


@app.get("/api/arroyos")
def arroyos():
    return send_from_directory(osm.DATOS, "arroyos_area_metropolitana.json")


@app.get("/api/ejemplo")
def ejemplo():
    return jsonify(nombre="Arroyo El Salao (Soledad)", lineas=fuente.lineas_ejemplo())


@app.get("/api/ejemplo_obra")
def ejemplo_obra():
    """Obra ilustrativa en la calle 72 (no es una obra real), para probar la pantalla fuera de El Salao."""
    obra = fuente.leer_obra(RAIZ / "datos" / "ejemplos" / "obra_ilustrativa.json")
    return jsonify(nombre=obra["nombre"], ilustrativo=obra["ilustrativo"],
                   lineas=[[list(p) for p in l] for l in obra["lineas"]])


class PedidoInvalido(ValueError):
    """Error del pedido con un mensaje para mostrar tal cual."""


def _lineas(pedido):
    """Líneas [(lat, lon), ...] del pedido, ya validadas; descarta las de menos de dos puntos.

    Lanza PedidoInvalido si hay coordenadas que no son números finitos, fuera de rango o demasiados puntos.
    Lanza TypeError, ValueError o IndexError si la forma no es [[[lat, lon], ...], ...].
    """
    crudas = pedido.get("lineas", [])
    if not isinstance(crudas, list) or not all(isinstance(l, list) for l in crudas):
        raise ValueError("lineas")
    if sum(len(l) for l in crudas) > MAX_PUNTOS:
        raise PedidoInvalido(f"La obra tiene demasiados puntos (más de {MAX_PUNTOS:,}). ".replace(",", ".")
                             + "Dibújela con menos clics o divídala en obras más cortas.")
    lineas = [[(float(p[0]), float(p[1])) for p in l] for l in crudas]
    for l in lineas:
        for la, lo in l:
            if not (math.isfinite(la) and math.isfinite(lo)):
                raise PedidoInvalido("Hay puntos de la obra sin coordenadas válidas. Borre la obra y vuelva a dibujarla.")
            if not (-90 <= la <= 90 and -180 <= lo <= 180):
                raise PedidoInvalido("Hay puntos de la obra con coordenadas fuera de rango (la latitud va de -90 a 90 "
                                     "y la longitud de -180 a 180; ¿están al revés?). Revise los puntos y vuelva a intentarlo.")
    return [l for l in lineas if len(l) >= 2]


def aviso_de_zona(recuadro):
    """Aviso (no bloquea) si la zona no está en el mapa guardado y hay que descargarla, o None."""
    S, O, N, E = osm.RECUADRO
    s, o, n, e = recuadro
    if not (S <= s and O <= o and n <= N and e <= E):
        return ("La obra está fuera del área metropolitana guardada. Sus calles se descargan de OpenStreetMap: "
                "el plan puede tardar más y necesita internet.")
    local = fuente.mapa_local()
    descarga = osm.CACHE / f"calles_{hashlib.sha1(osm.consulta(recuadro).encode()).hexdigest()[:16]}.json"
    guardada = (recuadro in fuente._redes or (local is not None and local.contiene(recuadro))
                or osm.cuadros_que_cubren(recuadro) is not None or descarga.exists())
    if not guardada:
        return ("Esta zona no está completa en el mapa guardado. Sus calles se descargan de OpenStreetMap: "
                "el plan puede tardar más y necesita internet.")
    return None


# Caché de los últimos MAX_CACHE planes. La clave incluye todos los parámetros que cambian el plan.
_cache_planes = OrderedDict()
_cache_lock = threading.Lock()


def limpiar_cache():
    with _cache_lock:
        _cache_planes.clear()


@app.post("/api/analizar")
def api_analizar():
    pedido = request.get_json(force=True, silent=True)
    if not isinstance(pedido, dict):
        return jsonify(error="El pedido debe ser un objeto JSON."), 400
    try:
        lineas = _lineas(pedido)
        radio = min(max(float(pedido.get("radio", 400)), 100), 800)
        luz = min(max(float(pedido.get("luz_max", 60)), 10), 150)
        k = min(max(int(pedido.get("k", 1)), 1), 3)
        abiertos = [int(i) for i in pedido.get("abiertos", [])]
        cerrados = [int(i) for i in pedido.get("cerrados", [])]
    except PedidoInvalido as ex:
        return jsonify(error=str(ex)), 400
    except (TypeError, ValueError, IndexError, KeyError):
        return jsonify(error="Datos del pedido inválidos."), 400
    if not lineas:
        return jsonify(error="Marque el arroyo con al menos dos puntos."), 400

    recuadro, lado = fuente.recuadro_de(lineas, radio)
    if lado > fuente.MAX_LADO_M:
        return jsonify(error=f"La zona es muy grande ({lado / 1000:.1f} km de lado). Marque un tramo de "
                             f"arroyo más corto, de unos 4 km como máximo."), 400
    t0 = time.time()
    try:
        red, origen = fuente.red_para(recuadro)
    except osm.ErrorDescarga as ex:
        return jsonify(error=str(ex).split("\n")[0]), 503
    t1 = time.time()
    resultado = analizar(red, lineas, radio=radio, luz_max=luz, k=k, abiertos=abiertos, cerrados=cerrados)
    resultado["tiempos"] = dict(red_s=round(t1 - t0, 1), analisis_s=round(time.time() - t1, 1))
    resultado["recuadro"] = recuadro
    resultado["fuente"] = origen
    return jsonify(resultado)


def _numero(pedido, clave, defecto, minimo, maximo):
    """Valor numérico del pedido, acotado a [minimo, maximo] como en /api/analizar.

    Si es un número entero se devuelve como int, para que los textos digan «1000 m» y no «1000.0 m».
    """
    v = float(pedido.get(clave, defecto))
    if not math.isfinite(v):
        raise ValueError(clave)
    v = min(max(v, minimo), maximo)
    return int(v) if v.is_integer() else v


@app.post("/api/plan")
def api_plan():
    """Plan de obra por etapas. Pedido y respuesta: equipo/cambio_a_obras.md, sección 5."""
    pedido = request.get_json(force=True, silent=True)
    if not isinstance(pedido, dict):
        return jsonify(error="El pedido debe ser un objeto JSON."), 400
    try:
        lineas = _lineas(pedido)
        radio = _numero(pedido, "radio", 400, 100, 800)
        luz = _numero(pedido, "luz_max", 60, 10, 150)
        etapa_max = _numero(pedido, "etapa_max_m", ETAPA_MAX_M, 300, 2000)
        un_puente_cada = _numero(pedido, "un_puente_cada_m", UN_PUENTE_CADA_M, 200, 1000)
        ancho = _numero(pedido, "ancho_m", TOLERANCIA_M, 10, 60)
        abiertos = [int(i) for i in pedido.get("abiertos", [])]
        cerrados = [int(i) for i in pedido.get("cerrados", [])]
        cerrar_puentes = pedido.get("cerrar_puentes", True)
        medicion = pedido.get("medicion", "lados")
    except PedidoInvalido as ex:
        return jsonify(error=str(ex)), 400
    except (TypeError, ValueError, IndexError, KeyError):
        return jsonify(error="Datos del pedido inválidos."), 400
    if not isinstance(cerrar_puentes, bool):
        return jsonify(error="cerrar_puentes debe ser true o false."), 400
    if medicion not in MEDICIONES:
        return jsonify(error=f"medicion debe ser una de: {', '.join(MEDICIONES)}."), 400
    if not lineas:
        return jsonify(error="Marque el eje de la obra con al menos dos puntos."), 400

    recuadro, lado = fuente.recuadro_de(lineas, radio)
    if lado > fuente.MAX_LADO_M:
        return jsonify(error=f"La zona es muy grande ({lado / 1000:.1f} km de lado). Marque una obra "
                             f"más corta, de unos 4 km como máximo."), 400

    # Todos los parámetros que cambian el plan van en la clave del caché.
    clave = json.dumps([lineas, radio, luz, etapa_max, un_puente_cada, ancho, abiertos, cerrados,
                        cerrar_puentes, medicion])
    t0 = time.time()
    with _cache_lock:
        guardado = _cache_planes.get(clave)
        if guardado is not None:
            _cache_planes.move_to_end(clave)
    if guardado is not None:
        return jsonify(dict(guardado, aviso_zona=None, en_cache=True,
                            tiempos=dict(red_s=0.0, plan_s=round(time.time() - t0, 1))))

    aviso = aviso_de_zona(recuadro)
    try:
        red, origen = fuente.red_para(recuadro)
    except osm.ErrorDescarga as ex:
        return jsonify(error=str(ex).split("\n")[0]), 503
    t1 = time.time()
    plan = plan_por_etapas(red, lineas, radio=radio, luz_max=luz, etapa_max_m=etapa_max,
                           un_puente_cada_m=un_puente_cada, abiertos=abiertos, cerrados=cerrados,
                           recuadro=recuadro, cerrar_puentes=cerrar_puentes, ancho_m=ancho, medicion=medicion)
    plan["recuadro"] = recuadro
    plan["fuente"] = origen
    with _cache_lock:
        _cache_planes[clave] = plan
        _cache_planes.move_to_end(clave)
        while len(_cache_planes) > MAX_CACHE:
            _cache_planes.popitem(last=False)
    # Campos agregados (el JSON solo se agranda): aviso_zona (texto o null) y en_cache (true o false).
    return jsonify(dict(plan, aviso_zona=aviso, en_cache=False,
                        tiempos=dict(red_s=round(t1 - t0, 1), plan_s=round(time.time() - t1, 1))))


if __name__ == "__main__":
    print("Abra http://localhost:5000 en el navegador. Ctrl+C para detener.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
