"""Servidor web: mapa interactivo de arroyos de Barranquilla y su área metropolitana.

Uso:
  pip install flask
  python app.py
  Abrir http://localhost:5000 en el navegador.

Rutas:
  GET  /               la página (carpeta web/)
  GET  /api/arroyos    cauces de OpenStreetMap del área metropolitana
  GET  /api/ejemplo    el arroyo El Salao en Soledad, caso de estudio del documento
  POST /api/analizar   recibe el arroyo marcado y devuelve el análisis (src/analisis.py)
"""
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from src import fuente, osm
from src.analisis import analizar

RAIZ = Path(__file__).resolve().parent
WEB = RAIZ / "web"

app = Flask(__name__, static_folder=None)


@app.errorhandler(Exception)
def error_inesperado(ex):
    """Cualquier error del análisis vuelve como JSON, para que la página lo muestre."""
    if isinstance(ex, HTTPException):
        return ex
    app.logger.exception("Error al atender %s", request.path)
    return jsonify(error="Ocurrió un error inesperado al analizar este arroyo. "
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


if __name__ == "__main__":
    print("Abra http://localhost:5000 en el navegador. Ctrl+C para detener.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
