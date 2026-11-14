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
import math
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from src import fuente, osm
from src.analisis import TOLERANCIA_M, analizar
from src.etapas import ETAPA_MAX_M, MEDICIONES, UN_PUENTE_CADA_M, plan_por_etapas

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"

app = Flask(__name__, static_folder=None)


@app.errorhandler(Exception)
def error_inesperado(ex):
    """Cualquier error del análisis vuelve como JSON, para que la página lo muestre."""
    if isinstance(ex, HTTPException):
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


@app.post("/api/analizar")
def api_analizar():
    pedido = request.get_json(force=True)
    try:
        lineas = [[(float(p[0]), float(p[1])) for p in l] for l in pedido.get("lineas", [])]
        lineas = [l for l in lineas if len(l) >= 2]
        radio = min(max(float(pedido.get("radio", 400)), 100), 800)
        luz = min(max(float(pedido.get("luz_max", 60)), 10), 150)
        k = min(max(int(pedido.get("k", 1)), 1), 3)
        abiertos = [int(i) for i in pedido.get("abiertos", [])]
        cerrados = [int(i) for i in pedido.get("cerrados", [])]
    except (TypeError, ValueError):
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
        lineas = [[(float(p[0]), float(p[1])) for p in l] for l in pedido.get("lineas", [])]
        lineas = [l for l in lineas if len(l) >= 2]
        radio = _numero(pedido, "radio", 400, 100, 800)
        luz = _numero(pedido, "luz_max", 60, 10, 150)
        etapa_max = _numero(pedido, "etapa_max_m", ETAPA_MAX_M, 300, 2000)
        un_puente_cada = _numero(pedido, "un_puente_cada_m", UN_PUENTE_CADA_M, 200, 1000)
        ancho = _numero(pedido, "ancho_m", TOLERANCIA_M, 10, 60)
        abiertos = [int(i) for i in pedido.get("abiertos", [])]
        cerrados = [int(i) for i in pedido.get("cerrados", [])]
        cerrar_puentes = pedido.get("cerrar_puentes", True)
        medicion = pedido.get("medicion", "lados")
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
    t0 = time.time()
    try:
        red, origen = fuente.red_para(recuadro)
    except osm.ErrorDescarga as ex:
        return jsonify(error=str(ex).split("\n")[0]), 503
    t1 = time.time()
    plan = plan_por_etapas(red, lineas, radio=radio, luz_max=luz, etapa_max_m=etapa_max,
                           un_puente_cada_m=un_puente_cada, abiertos=abiertos, cerrados=cerrados,
                           recuadro=recuadro, cerrar_puentes=cerrar_puentes, ancho_m=ancho, medicion=medicion)
    plan["tiempos"] = dict(red_s=round(t1 - t0, 1), plan_s=round(time.time() - t1, 1))
    plan["recuadro"] = recuadro
    plan["fuente"] = origen
    return jsonify(plan)


if __name__ == "__main__":
    print("Abra http://localhost:5000 en el navegador. Ctrl+C para detener.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
