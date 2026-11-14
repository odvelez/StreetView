# Entrega de Blanco (turno 3): probar, corregir y asegurar

**Estado:** B1, B2, B3 y B4 hechas, un commit por tarea en `obras`.
**Pruebas:** `python -m unittest` → **81 en verde** (las 63 que recibí y 18 nuevas en `tests/test_app_robustez.py`).
**Cifras:** El Salao da los mismos números que `resultados/linea_base/` (en la terminal y en la API). No cambié cifras.

## Qué probé (B1)

Detalle en [blanco_plan_de_pruebas.md](blanco_plan_de_pruebas.md) y [blanco_hallazgos.md](blanco_hallazgos.md).
Pruebas, línea base de El Salao, obra dibujada, `--obra` de la calle 72, recorrido completo (9, 7 y 8 pasos),
palabras viejas en todo el texto visible, errores del servidor (500, 503, 400 y servidor apagado) y la consola.
La pantalla se probó en Chrome sin ventana a 1366×768.

**Resultado:** la app funciona. Quedan dos fallos visibles: **«Arroyo El Salao»** aparece como nombre de una
ruta alterna (H1, es un dato de OpenStreetMap) y un **404 de `favicon.ico`** en la consola (H2).

## Qué corregí

| Tarea | Qué se hizo | Archivos |
|---|---|---|
| **B2** | Lo mío se corrigió en B3. Lo de Karel (plurales, «cambio(s)», acentos en la terminal) y lo de Lobo (favicon) quedó devuelto con el hallazgo y su dueño | `blanco_hallazgos.md` |
| **B3** | `app.py`: rechaza `NaN`/`Infinity`, coordenadas fuera de rango y más de 2.000 puntos con un mensaje claro (antes: error 500 o «zona muy grande, 112 km»). Cuerpo que no es JSON, 404, 405 y 413 bajo `/api/` responden en JSON y en español (antes: página HTML en inglés). Pedidos de más de 1 MB se rechazan. **Aviso sin bloquear** `aviso_zona` si la zona no está guardada y hay que descargarla. Si Overpass falla: 503 «No se pudieron descargar las calles de OpenStreetMap. Revise la conexión…» (probado con `unittest.mock`, sin internet). **Caché** de los últimos 16 planes con una clave que incluye todos los parámetros: El Salao pasa de 16 s a **5 ms** la segunda vez | `app.py`, `tests/test_app_robustez.py` |
| **B4** | Tabla de textos para cada dueño | `blanco_textos.md` |

**Campos agregados a la respuesta de `/api/plan`** (el JSON solo se agranda): `aviso_zona` (texto o `null`) y
`en_cache` (`true` o `false`). Cuando viene del caché, `tiempos` es el de esa respuesta (casi 0 s).

## Qué falta

- **Lobo:** mostrar `aviso_zona` en la pantalla (hoy llega pero no se ve) y agregar el favicon.
- **Karel:** los plurales de `pasos[].detalle` y los textos de `blanco_textos.md`.
- **Oscar:** decidir qué hacer con «Arroyo El Salao» como nombre de vía (H1) y con el commit `5705862` «aaaskks»,
  que cambió `resultados/` (H9).
- Probar en un teléfono de verdad y con un compañero que no conozca la app (no se puede hacer con una máquina).

## Qué me preocupa

1. **El primer plan de El Salao tarda entre 15 y 40 s** (Lobo anotó unos 10 s). El caché solo ayuda desde la
   segunda vez. Para la presentación, conviene abrir `/?ejemplo` una vez antes de empezar.
2. **Abrir `http://localhost:5000` desde Python en Windows tarda 2 s más por pedido** (intenta IPv6 primero y
   el servidor solo escucha en 127.0.0.1). El navegador no lo nota. Para scripts, usar `http://127.0.0.1:5000`.
3. **El caché vive en la memoria del servidor:** si se cambia algo en `src/`, hay que reiniciar `python app.py`
   para no ver planes viejos.
4. Las pruebas de Gustavo (`tests/test_app.py`) no deberían chocar con las mías: el archivo se llama distinto.
   Si alguna de las suyas espera una página HTML en un error de `/api/`, ahora recibe JSON.
5. **No hice push.** Los commits están solo en mi máquina hasta que se suban.
