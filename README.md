# Obras viales por etapas (MAT 4021, Matemáticas Discretas, Uninorte)

Equipo: Oscar Vélez, Gustavo de la Ossa, Sebastián Blanco, Karel Silva y Santiago Lobo.
**Entrega:** domingo 15 de noviembre de 2026, 11:59 p. m., por Brightspace: PDF en LaTeX y diapositivas (10 minutos, 5 expositores, demo en vivo). La sustentación individual vale **40 %**: cada integrante debe poder explicar todo el proyecto.

Este es el único README del repositorio. Todo el código está en `proyecto_arroyos/`.

## 1. Qué es

**Pregunta:** al planificar una obra que cierra calles, ¿cómo se divide en etapas y qué medidas temporales (pasos peatonales provisionales, cambios de sentido, rutas alternas, control en esquinas) reducen más el desvío de quienes la rodean?

**Ejemplo principal:** la canalización de El Salao, en Soledad (2.386 m). El 4 de noviembre es la motivación del proyecto, no su tema. Tratarlo con respeto: sin nombres de víctimas y sin decir qué ruta debieron tomar.

**Modelo:** las esquinas son nodos y las cuadras son aristas con peso en metros. Hay un grafo **no dirigido** para peatones y uno **dirigido** para vehículos (respeta los sentidos viales). La obra quita las aristas que toca. Dijkstra mide el desvío, programación dinámica decide los cortes de las etapas, una heurística voraz elige las medidas y para cada cruce cerrado se calcula una ruta alterna.

## 2. Cómo se usa

Requisitos: Python 3.10 o superior y `pip install -r requirements.txt` (Flask para la web; matplotlib solo para `mapa.png`). Los algoritmos usan solo la biblioteca estándar. Todo desde `proyecto_arroyos/`.

```bash
python app.py                      # pantalla en http://localhost:5000 (use /?ejemplo para cargar El Salao)
python main.py                     # análisis de toda la obra a la vez: resultados/resumen.txt, analisis.json, mapa.png
python herramientas/plan_etapas.py # plan por etapas: resultados/plan_etapas.txt y .json
python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json   # otra obra
python -m unittest                 # 81 pruebas (tardan unos 35 s)
```

En la pantalla: elegir municipio, dibujar la obra (o cargar el ejemplo), pulsar **Planificar** y seguir el recorrido paso a paso. El primer plan de El Salao tarda entre 15 y 40 s; la segunda vez sale del caché (unos 5 ms). Para la presentación, abra `/?ejemplo` una vez antes de empezar. Si cambia algo en `src/`, reinicie `python app.py` por el caché. Desde Python en Windows use `http://127.0.0.1:5000`, no `localhost` (2 s más por pedido).

`main.py` y `plan_etapas.py` **sobrescriben `resultados/`**; úselos solo para regenerar los resultados a propósito.

Formato de un archivo de obra (`datos/ejemplos/obra_ilustrativa.json` es un ejemplo de 600 m de la calle 72; si `ilustrativo` es `true`, la pantalla avisa «Ejemplo ilustrativo, no es una obra real»):

```json
{"nombre": "Obra ilustrativa en la calle 72", "ilustrativo": true,
 "lineas": [[[10.9187, -74.7981], [10.9190, -74.7975]]]}
```

## 3. Cómo funciona (todos deben poder explicarlo)

1. **Mapa a grafo.** Esquinas = nodos, cuadras = aristas con la longitud en metros (OpenStreetMap, vía Overpass).
2. **Dos grafos.** Peatones, no dirigido. Vehículos, dirigido. El paso peatonal solo sirve a peatones y el cambio de sentido solo a vehículos.
3. **Obra.** Se borran las aristas que cruzan el eje de la obra o van sobre él (franja de `ancho_m` = 10 m a cada lado del eje), incluidos los puentes existentes (parámetro `cerrar_puentes`). Quitar la arista representa «no se puede pasar»; un peso de penalización sería un número inventado.
4. **Lados.** Cada esquina queda a un lado de la obra según el signo del producto cruz con el segmento más cercano.
5. **Desvío.** Para cada par de esquinas en lados opuestos, Dijkstra da el camino mínimo sin obra y con obra; el desvío es la diferencia.
6. **Etapas.** El número de etapas sale del largo (hasta 1.000 m cada una) y los cortes se eligen con programación dinámica. Hay un paso peatonal provisional por cada 500 m de obra.
7. **Medidas (voraz).** Se elige en cada ronda el candidato que más baja el desvío medio. Fórmula rápida: al agregar x→y con peso w, `d'(a,b) = min(d(a,b), d(a,x) + w + d(y,b))`, sin repetir Dijkstra por candidato; con parada temprana y grafo invertido para el caso dirigido. Pasó de unos 36 s a 6–8 s con los mismos resultados (hay pruebas que lo comparan).
8. **Rutas alternas y esquinas.** Para cada cruce cerrado se calcula el camino mínimo que queda. Se marcan las esquinas con más recorridos desviados y si tienen semáforo registrado.

## 4. Resultados de El Salao

De `resultados/plan_etapas.txt` y `resumen.txt`: obra de **2.386 m en 3 etapas**, **5 pasos peatonales provisionales**, 3 cambios de sentido, 18 rutas alternas y 15 esquinas a controlar (14 sin semáforo registrado). Toda la obra a la vez, sin etapas, es el escenario de comparación.

A pie, toda la obra a la vez: desvío medio 70 m, 10,9 % de pares con más de 200 m, máximo 763 m; con 3 pasos peatonales: 26 m, 2,0 % y 440 m. En vehículos las medidas ayudan poco: la «mejor» medida (doble sentido en una calle de 6 m, junto a la Av. Murillo) devuelve el camino a 120 pares pero no baja el desvío medio, porque esos pares entran al promedio con recorridos largos. **Las conclusiones deben decirlo con honestidad:** con medidas temporales el problema peatonal mejora mucho y el vehicular casi no.

Hipótesis sin verificar: los 240 pares vehiculares sin camino (2 × 120) serían **una sola esquina aislada** de la muestra, cerca de 10,9195 N, −74,7993 O. No use «240 pares sin camino» como dato del problema hasta confirmarlo.

Nota sobre un nombre: en OpenStreetMap hay una calle residencial de 4 m llamada «Arroyo El Salao» (vía 898051045). El programa la muestra como «Vía local junto al eje (en OSM: Arroyo El Salao)» para que la pantalla no hable de arroyos. Es un dato de OSM; **falta confirmar en Street View** que esa calle de 102 m sirva como ruta alterna.

Otros experimentos (betweenness, sensibilidad, control de lados, histograma, voraz contra fuerza bruta) están en `resultados/experimentos/`; el informe de cambios, en `resultados/informe_cambios.md`.

## 5. Organización

```
proyecto_arroyos/
  app.py               servidor Flask: GET /, GET /api/ejemplo, POST /api/analizar, POST /api/plan
  main.py              análisis de toda la obra a la vez, por terminal
  web/                 pantalla (Leaflet): menú, recorrido paso a paso, resultados
  src/grafo.py         grafo dirigido y no dirigido, BFS, componentes, Dijkstra, centralidades
  src/red.py           de calles de OpenStreetMap a tramos y grafos
  src/geometria.py     clase Obra, cruces calle–obra, distancia, lado
  src/analisis.py      escenarios, desvíos, candidatos y selección voraz
  src/etapas.py        plan por etapas y pasos para la pantalla
  src/fuente.py        de dónde salen las calles; lectura de archivos de obra
  src/osm.py           lectura y descarga de OpenStreetMap
  src/comparacion.py   voraz contra fuerza bruta (k = 2)
  src/control.py       control del lado por componentes conexas
  herramientas/        plan_etapas.py, eje_de_calle.py, experimentos.py, diagnostico_sin_camino.py, descargar_mapa.py
  datos/               ejemplos/, cache/, arroyo_el_salao.csv, arroyos_area_metropolitana.json
  resultados/          salidas generadas; linea_base/ son las cifras de referencia de El Salao
  tests/               81 pruebas (regresión contra linea_base, API, robustez, etapas, obras)
  documento/main.tex   documento en LaTeX
```

**Contrato `POST /api/plan`** (no romperlo: el JSON solo se agranda). Pedido: `{lineas, radio, luz_max, etapa_max_m (300–2000, 1000), un_puente_cada_m (200–1000, 500), cerrar_puentes (true), ancho_m (10–60, 10), medicion ("lados"), abiertos, cerrados}`. Respuesta: `obra`, `parametros`, `semaforos_conocidos`, `resumen`, `etapas[]` (con `eje`, `tramos_cerrados`, `peatones`, `vehiculos`, `rutas[]`, `carga[]`), `pasos[]`, `tiempos`, `recuadro`, `fuente`, `aviso_zona` y `en_cache`. Errores en JSON: 400 (pedido inválido o zona demasiado grande) y 503 (no se pudo descargar el mapa). Ejemplo real: `resultados/plan_etapas.json`.

**Datos:** calles y arroyos © colaboradores de OpenStreetMap (ODbL), descargados el 10 de noviembre de 2026 para el recuadro 10,84–11,12 N y 74,96–74,73 O (Barranquilla, Soledad, Malambo, Puerto Colombia y Galapa). Si la obra queda fuera de lo guardado, se descargan las calles de Overpass a `datos/cache/` (puede tardar minutos).

## 6. Estado del equipo

| Persona | Parte | Estado |
|---|---|---|
| Oscar | Ejemplo de obra (calle 72), integración, esta documentación | Hecho; falta la limpieza final (sección 7) |
| Karel | Refactor de arroyo a obra y `/api/plan` | Hecho (R1 a R6). Opcionales sin hacer: `medicion="afectados"` y pasos peatonales casi perpendiculares |
| Lobo | Pantalla: menú, recorrido, resultados, pantalla pequeña | Hecho |
| Blanco | Pruebas, robustez de `app.py`, revisión de textos | Hecho |
| Gustavo | Diapositivas, `herramientas/figuras_plan.py`, `tests/test_app.py` | **Diapositivas entregadas** (por WhatsApp, no están en el repositorio). Sin entregar: figuras y pruebas de la API; ver sección 7 |

## 7. Lo que falta (en orden)

**Bloquea la entrega**
1. **Documento.** `documento/main.tex` sigue hablando de arroyos y lluvia y tiene **8 `\completar{}`**. El centro del documento pasa a ser el plan por etapas; las cifras de la simulación con lluvia siguen siendo válidas como «toda la obra a la vez». Completar: cifra de habitantes del sector con fuente (DANE o Alcaldía de Soledad), noticias del 4 de noviembre y canalización anunciada (fecha y costo) y emergencias anteriores, cómo se confirmó cada cruce, el caso de prueba hecho a mano y las conclusiones propias. Sin fuente, dejar «pendiente de verificar»; no inventar datos.
2. **Diapositivas:** entregadas por Gustavo por WhatsApp. Falta revisar que usen las cifras de la sección 4 y el tema de obras (no de arroyos), y repartir quién expone qué (problema 1:30; mapa a grafo 2:00; Dijkstra, voraz y pruebas 2:00; resultados con el hallazgo honesto 2:00; demo en vivo 2:00; límites y cierre 0:30).
3. **Figuras** (opcional si las diapositivas ya traen las suyas; `herramientas/figuras_plan.py`): leer `resultados/plan_etapas.json` y guardar PNG en `resultados/figuras/`: mapa con el eje por etapa (colores Okabe-Ito), pasos peatonales en naranja, cambios de sentido en morado y esquinas sin semáforo en rojo; y barras del desvío a pie con la obra frente a con los pasos, por etapa. Con leyenda y «© colaboradores de OpenStreetMap».
4. **Pruebas de la API** (opcional, ya hay 18 en `test_app_robustez.py`; `tests/test_app.py`, con `app.test_client()` y sin descargas reales): `GET /` da 200; `/api/ejemplo` trae `lineas`; `/api/analizar` sin líneas da 400; `/api/plan` con El Salao da 200 con `etapas`, `resumen` y `pasos`, con parámetros fuera de rango da 400 y con Overpass caído da 503. Ya existen `tests/test_app_robustez.py` con 18 pruebas parecidas; pueden completarse o reutilizarse.
5. **Capturas** de la app (1600 × 900; celular 390 × 844) para las diapositivas. Los `id` de la pantalla son `#menu`, `#paso-municipio`, `#paso-obra`, `#paso-planificar`, `#ajustes`, `#btn-planificar`, `#recorrido`, `#resultados`, `#cifras`, `#selector-etapa`, `#detalle-etapa`.
6. **Ensayo cronometrado** de los 10 minutos y preparar las preguntas de la sustentación (sección 8).

**Limpieza del código (solo Oscar, al final)**
- Quitar `fuente.arroyos_osm`, `lineas_por_nombre`, la ruta `/api/arroyos`, la clave `cauce` (queda `eje`), el alias `Arroyo`, el alias `recorte_del_cauce`, `--arroyo` y `--listar`; mover `datos/arroyos_area_metropolitana.json` a `datos/archivo_arroyos/`. Quedan palabras viejas en claves del JSON (`arroyo`, `cauce`, `lluvia`, `lluvia_m`) y en el `User-Agent` de `osm.py`; quitarlas rompe el contrato, así que hay que cambiar a la vez pantalla, pruebas y `resultados/linea_base/`.
- Regenerar `resultados/` solo si cambia algo y actualizar el `.tex` en el mismo momento.

**Pequeños arreglos pendientes**
- Pantalla (`web/`): mostrar `aviso_zona` (llega pero no se ve) y agregar favicon (`<link rel="icon" href="data:,">`; hoy da 404 en la consola). Tampoco se pueden corregir a mano tramos abiertos o cerrados, y `radio`, `luz_max` y `ancho_m` no están en la pantalla.
- `src/etapas.py`: plurales («1 cambio(s) de sentido», «1 de ellos puentes existentes») y «1 etapas», «1 pasos peatonales» en `plan_etapas.py`; con salida redirigida en Windows los acentos salen mal (`sys.stdout.reconfigure(encoding="utf-8")`).
- Textos con jerga (por ejemplo «algoritmo de Dijkstra» en el panel) que conviene aclarar.
- `ancho_m` se mide **desde el eje hacia cada lado**: con 10, la franja real mide 20 m de borde a borde. Decidir cuál es la definición y escribirla igual en pantalla y documento.
- En el ejemplo de la calle 72 aparecen «Calle 47» y «Carrera 18 Sur» entre las rutas alternas; puede ser cómo están nombradas en OSM, conviene mirarlo antes de mostrarlo.
- El commit «aaaskks» de Lobo cambió `resultados/` por ruido de redondeo; esa carpeta ya se regeneró, así que no hay nada más que hacer.
- Probar en un teléfono real y con alguien que planifique una obra sin explicación.
- Revisar en Street View los cruces cerrados de El Salao (por ejemplo Calle 61, Carrera 22D, Calle 59A, Calle 60, Calle 67A, Calle 75 y la vía local junto al eje) y confirmar la calle de 6 m de la Av. Murillo; si es un error de OSM, va como limitación.

**Límites que deben quedar escritos**
No hay datos de tránsito (no se mide congestión); los pesos son metros, no tiempo; no se diseñan carriles ni semáforos; no se evalúan costo, suelos ni diseño hidráulico; se usa una muestra de 120 esquinas por lado sin ponderar por población; la heurística voraz no garantiza el óptimo; se supone que la obra cierra los puentes existentes; la calidad de OSM depende de quien lo edita y hay que verificar en terreno.

## 8. Preguntas que pueden hacer en la sustentación

- **¿Por qué quitar aristas y no aumentar el peso?** Un peso de penalización sería un número inventado; quitar la arista representa que no se puede pasar.
- **¿Por qué dos grafos?** Un peatón puede caminar en contravía y un carro no; además cada medida solo sirve a quien la usa.
- **¿Por qué no un puente vehicular?** Costaría y tardaría casi lo que la obra. Solo se proponen medidas temporales.
- **¿El voraz da el óptimo?** No está garantizado; sí da el mejor candidato de cada ronda. Hay una comparación contra fuerza bruta con k = 2 en `resultados/experimentos/`.
- **¿Cómo saben qué calles cierra la obra?** Por geometría: la calle cruza el eje o va sobre él. Después se verifica en Street View.
- **¿Y si OpenStreetMap está mal?** Es una limitación; por eso se verifica en Street View.
- **¿Por qué una muestra de esquinas?** Con todas tardaría minutos; con 120 por lado son 14.400 pares y tarda segundos.
- **¿Por qué la mejor medida vehicular no baja el desvío medio?** Devuelve el camino a pares que antes no tenían ninguno y esos entran al promedio con recorridos largos.
- **¿Por qué no una red neuronal?** No hay datos etiquetados y el problema es de caminos en una red.
- **¿La medida es construible?** El modelo solo mide conectividad.

## 9. Reglas del equipo

1. No inventar datos: población, noticias, costos, fechas y fuentes verificables y con enlace; si no, «pendiente de verificar».
2. Las 81 pruebas deben pasar antes de cada commit (`python -m unittest`).
3. Si cambia una cifra, se actualiza el `.tex` en el mismo momento.
4. Después de correr `main.py` o `plan_etapas.py` sin querer regenerar, `git checkout -- proyecto_arroyos/resultados`.
5. Commits pequeños, con mensaje en español.
