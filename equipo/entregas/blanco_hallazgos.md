# Hallazgos de Blanco (B1)

Probado el sábado 14 de noviembre sobre `obras` en `5705862`, con Python 3.11 y Chrome sin ventana (1366×768).
Plan de pruebas: [blanco_plan_de_pruebas.md](blanco_plan_de_pruebas.md).

## Lista de comprobación

| Prueba | Resultado |
|---|---|
| `python -m unittest` | ✅ 63 en verde (unos 32 s) |
| `plan_etapas.py` contra `linea_base/plan_etapas.txt` | ✅ Mismos números. Solo cambian textos («arroyo» → «obra») y aparece el «10 m» del ancho de la franja |
| `POST /api/plan` con El Salao | ✅ 200, 3 etapas, 9 pasos; todos los números iguales a `linea_base/plan_etapas.json` (0 diferencias) |
| Planificar una obra dibujada | ✅ 3 clics en Soledad: 2 etapas, 8 pasos |
| Planificar con `--obra datos/ejemplos/obra_ilustrativa.json` | ✅ En la terminal: 1 etapa, 600 m. En la pantalla: 7 pasos y «Ejemplo ilustrativo, no es una obra real» en la tarjeta y en el panel |
| El recorrido muestra todos los pasos | ✅ 9 de 9 en El Salao, 7 de 7 en la calle 72 y 8 de 8 en la obra dibujada; al final queda la vista normal |
| Sin «arroyo», «cauce» ni «lluvia» en pantalla | ❌ Ver H1 |
| Error del servidor como mensaje claro | ✅ 500 JSON, 500 HTML («El servidor respondió con un error (500).»), 503, 400 y servidor apagado. Ver H5 sobre lo que llega **antes** de la pantalla |
| Consola sin errores rojos | ❌ Ver H2 |

## Fallos

| # | Qué se hizo | Qué se esperaba | Qué pasó | Dueño |
|---|---|---|---|---|
| **H1** | El Salao → selector de etapa «2» → lista «Rutas alternas para señalizar»; también al tocar esa ruta (recuadro de detalle) | Ninguna palabra «arroyo» en pantalla | Una ruta alterna se llama **«Arroyo El Salao»** (y lo mismo en la ventana del mapa). Es el nombre de la vía en OpenStreetMap (`rutas[].via`), no un texto del programa | **Oscar** decide (es un dato, no se inventa otro nombre). Si se cambia, en `src/etapas.py` (**Karel**) o en `web/app.js` (**Lobo**) |
| **H2** | Abrir `http://localhost:5000` con la consola (F12) | Consola sin errores rojos | `Failed to load resource: 404 (NOT FOUND) /favicon.ico` en cada carga | **Lobo** (`web/index.html`): basta con `<link rel="icon" href="data:,">` o un ícono en `web/` |
| **H3** | Recorrido de El Salao, pasos «Etapa 1 de 3» a «Etapa 3 de 3» | Plurales correctos | Dice «**1 cambio(s) de sentido**» (ya lo había visto Lobo) | **Karel** (`src/etapas.py`, `pasos_del_plan`) |
| **H4** | Recorrido de El Salao, paso «Etapa 2 de 3», y de la calle 72, «Etapa 1 de 1» | «1 de ellos es un puente existente» | Dice «Se cierran 24 cruces, **1 de ellos puentes existentes**» | **Karel** (`src/etapas.py`, `pasos_del_plan`) |
| **H5** | `POST /api/plan` con `NaN` en una coordenada | 400 con un mensaje claro | **500** «Ocurrió un error inesperado…» | **Lobo** (`app.py`), corregido en B3 con su permiso |
| **H6** | `POST /api/plan` con latitud 200 | 400 «coordenadas fuera de rango» | 400 «La zona es muy grande (112.8 km de lado)…»: el mensaje no dice qué pasó | **Lobo** (`app.py`), corregido en B3 |
| **H7** | `POST /api/analizar` con un cuerpo que no es JSON (y cualquier 404/405 bajo `/api/`) | Error en JSON | Página HTML «400 Bad Request» en inglés | **Lobo** (`app.py`), corregido en B3 |
| **H8** | Planificar El Salao dos veces seguidas | Unos 10 s (nota de Lobo) | 39 s la primera vez (54 s en la pantalla) y **18 s** la segunda, idéntica | `app.py` (**Lobo**): caché de B3 para la repetición. El primer cálculo es de `src/` (**Karel**) |
| **H9** | Commit `5705862` «aaaskks» de Lobo | `resultados/` sin cambios (regla 7: solo Oscar regenera) | Cambia `resultados/analisis.json` (decimales en la posición 11, ruido de redondeo) y reescribe `resultados/resumen.txt` con los textos nuevos | **Oscar** decide si se queda o se revierte; el mensaje del commit no dice qué hace |
| **H10** | `python herramientas/plan_etapas.py --obra … > salida.txt` en Windows | Acentos bien | «m�nimo», «desv�o»: con la salida redirigida, Python usa cp1252. Los archivos de `resultados/` sí salen bien en UTF-8 | **Karel** (`herramientas/plan_etapas.py`): `sys.stdout.reconfigure(encoding="utf-8")`. Menor |
| **H11** | Informe de la terminal de la calle 72 | «1 etapa», «1 paso peatonal provisional» | «en **1 etapas**», «**1 pasos peatonales** provisionales» (Karel ya lo anotó) | **Karel** (`herramientas/plan_etapas.py`). Menor |

Los textos con jerga o poco claros (por ejemplo «algoritmo de Dijkstra» en el panel) van en
[blanco_textos.md](blanco_textos.md) (B4).

## Qué no se pudo probar

- Un teléfono de verdad y un compañero que planifique sin explicación (pendiente de la nota de Lobo).
- Una descarga real de Overpass: se probó con `unittest.mock` (B3), sin internet.
