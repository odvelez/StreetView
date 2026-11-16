# Obras viales por etapas (MAT 4021, Matemáticas Discretas, Uninorte)

Equipo: Oscar Vélez, Gustavo de la Ossa, Sebastián Blanco, Karel Silva y Santiago Lobo.
**Entrega (Brightspace, martes 17 de noviembre de 2026):** el documento escrito (paper) en LaTeX, en PDF, y las diapositivas (que se preparan aparte y no están en este repositorio). Ambos deben incluir el **enlace al repositorio** (https://github.com/odvelez/StreetView). La sustentación individual vale **40 %**: cada integrante debe poder explicar todo el proyecto.

**Sustentación** (programación oficial del profesor): lunes 16 de noviembre (2:00 a 4:00 p. m.; grupos 1 a 7, citación desde las 2:05 y cada 17 min) o miércoles 18 (2:00 a 3:00 p. m.; grupos 8 a 10, citaciones 2:05, 2:22 y 2:39). **Somos el grupo 7: lunes 16 de noviembre, citación a las 3:47 p. m. (estar afuera del salón desde las 3:37).**
- Estar **afuera del salón 10 minutos antes** de la hora y dejar todo listo; al entrar se empieza enseguida (solo hay 2 minutos entre grupos).
- **10 minutos** de presentación con temporizador proyectado; al terminar se corta. Todos participan de forma equitativa.
- **5 minutos de preguntas**, al grupo o a una persona en particular.
- Probar antes el ejecutable y la proyección: si algo falla por falta de preparación, **no hay tiempo adicional** y baja la nota.
- El profesor debe poder **ejecutar y reproducir el proyecto desde este README** sin problemas: el repositorio debe tener todo el código y la documentación clara.

Este es el único README del repositorio. Todo el código está en `proyecto_obras/`.

## 1. Qué es

**Pregunta:** al planificar una obra que cierra calles, ¿cómo se divide en etapas y qué medidas temporales (pasos peatonales provisionales, cambios de sentido, rutas alternas, control en esquinas) reducen más el desvío de quienes la rodean?

**Ejemplo principal:** la canalización de El Salao, en Soledad (2.386 m). El 4 de noviembre es la motivación del proyecto, no su tema. Tratarlo con respeto: sin nombres de víctimas y sin decir qué ruta debieron tomar.

**Modelo:** las esquinas son nodos y las cuadras son aristas con peso en metros. Hay un grafo **no dirigido** para peatones y uno **dirigido** para vehículos (respeta los sentidos viales). La obra quita las aristas que toca. Dijkstra mide el desvío, programación dinámica decide los cortes de las etapas, una heurística voraz elige las medidas y para cada cruce cerrado se calcula una ruta alterna.

## 2. Cómo se usa

**Para quien califica** (probado en un clon limpio con un entorno virtual nuevo, Python 3.11, Windows):

```bash
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_obras
python -m pip install -r requirements.txt
python -m unittest                 # verificar: todas las pruebas deben dar OK
python app.py                      # abrir http://localhost:5000/?ejemplo
```

No se necesita internet para El Salao: las calles ya están guardadas en `datos/cache/`.

Requisitos: Python 3.10 o superior (Flask para la web; matplotlib para `mapa.png` y las figuras). Los algoritmos usan solo la biblioteca estándar. Todo desde `proyecto_obras/`.

```bash
python app.py                      # pantalla en http://localhost:5000 (use /?ejemplo para cargar El Salao)
python main.py                     # análisis de toda la obra a la vez: resultados/resumen.txt, analisis.json, mapa.png
python herramientas/plan_etapas.py # plan por etapas: resultados/plan_etapas.txt y .json
python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json   # otra obra
python -m unittest                 # 144 pruebas (tardan unos 45 s)
```

En la pantalla: elegir municipio, dibujar la obra (o cargar el ejemplo), pulsar **Planificar** y seguir el recorrido paso a paso. El primer plan de El Salao tarda entre 10 y 40 s según el computador; la segunda vez sale del caché (unos 5 ms). Para la presentación, abra `/?ejemplo` una vez antes de empezar. Si cambia algo en `src/`, reinicie `python app.py` por el caché. Desde Python en Windows use `http://127.0.0.1:5000`, no `localhost` (2 s más por pedido).

**Si algo se ve raro, revise que no haya otro `python app.py` abierto.** En Windows, dos servidores pueden ocupar el puerto 5000 a la vez sin dar error, y el navegador puede estar hablando con el viejo (con otro código o con planes en caché). Cierre todas las ventanas donde corra `app.py` y vuelva a abrir uno solo.

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
8. **Rutas alternas y esquinas.** Para cada cruce cerrado se calcula el camino mínimo que queda (a pie, ya con los pasos peatonales provisionales elegidos, así que pasa por el más cercano). Se marcan las esquinas con más recorridos desviados y si tienen semáforo registrado.

### 3b. Propuestas calculadas (activas por defecto)

Vienen activadas en la pantalla, la API y los scripts; con `"propuestas_calculadas": false` (o `--sin-calculadas`) el plan es el de antes, sin ellas. Agregan cinco propuestas calculadas, sin datos de tránsito y con todos sus supuestos explícitos en `src/supuestos.py` (valor, rango, justificación, fuente y estado: confirmado, reportado, no verificado o supuesto del equipo):

1. **Demanda supuesta (modelo de gravedad).** Cada par de esquinas pesa `exp(-distancia sin obra / d0)` (d0 = 400 m, rango 200–1000; supuesto del equipo). Con d0 muy grande da el desvío medio de siempre (hay prueba).
2. **Capacidad para cruzar la obra.** Flujo máximo (Edmonds–Karp) de un lado al otro en el grafo vehicular, con los carriles de OSM (`lanes`) o un supuesto por tipo de vía. El corte mínimo dice cuántos carriles quedan y por qué calles (teorema de Ford y Fulkerson).
3. **Pares viales.** Calles locales paralelas de un solo sentido: se prueban todas las configuraciones (sin cambio, invertir una, invertir la otra, las dos a doble sentido) con Dijkstra y con el corte mínimo. Se excluyen las dos calzadas de una avenida. En El Salao no hay ningún par (OSM tiene pocas calles con `oneway`) y la salida lo dice.
4. **Pasos peatonales por demanda.** Un voraz ponderado decide cuántos y dónde (agrega un paso solo si baja el alargamiento ponderado al menos 2 %, con 80 m de separación), y se informa el tramo más largo sin cruce (la guía GDCI recomienda no pasar de 200 m). En el caso de prueba con 2 pasos el voraz no es óptimo (42,8 m frente a 24,0 m), con 3 sí: está en `tests/test_demanda.py`.
5. **Control temporal.** Esquinas con más demanda desviada, al menos 3 accesos, sin semáforo registrado y separadas 150 m. Es una priorización, **no** un criterio para instalar semáforos (esos exigen conteos) y no se calculan tiempos de semáforo.

```bash
python herramientas/plan_etapas.py                          # informe con las propuestas (no escribe en resultados/ salvo --guardar)
python herramientas/plan_etapas.py --sin-calculadas         # el plan de antes, sin propuestas calculadas
python herramientas/experimentos.py calculadas              # sensibilidad a d0 y a los carriles (solo imprime)
```

En la API: `POST /api/plan` (activas por defecto; `"propuestas_calculadas": false` las apaga; opcional `"d0_m"`, 200–1000). Cada etapa agrega `circulacion`, `pares_viales`, `pasos_por_demanda` y `control_temporal`; el plan agrega `supuestos[]`, `parametros.calculadas`, `resumen.calculadas` y tres pasos antes de «Qué no mide este plan». La pantalla los dibuja: pares viales (azul), pasos por demanda (turquesa) y esquinas de control temporal (círculos punteados), con sus pasos en el recorrido.

Lo robusto y lo que depende de los supuestos (El Salao, `experimentos.py calculadas`): el número y la ubicación de los pasos por demanda no cambian con d0 ni con los carriles, y siempre bajan el alargamiento frente a la regla de 500 m. Las esquinas de control temporal sí cambian con d0, y la capacidad, con un carril más por calle.

## 4. Resultados de El Salao

De `resultados/plan_etapas.txt` y `resumen.txt`: obra de **2.386 m en 3 etapas**, **5 pasos peatonales provisionales**, 3 cambios de sentido, 18 rutas alternas y 15 esquinas a controlar (14 sin semáforo registrado). Toda la obra a la vez, sin etapas, es el escenario de comparación.

A pie, toda la obra a la vez: desvío medio 70 m, 10,9 % de pares con más de 200 m, máximo 763 m; con 3 pasos peatonales: 26 m, 2,0 % y 440 m. En vehículos las medidas ayudan poco: la «mejor» medida (doble sentido en una calle de 6 m, junto a la Av. Murillo) devuelve el camino a 120 pares pero no baja el desvío medio, porque esos pares entran al promedio con recorridos largos. **Las conclusiones deben decirlo con honestidad:** con medidas temporales el problema peatonal mejora mucho y el vehicular casi no.

Hipótesis sin verificar: los 240 pares vehiculares sin camino (2 × 120) serían **una sola esquina aislada** de la muestra, cerca de 10,9195 N, −74,7993 O. No use «240 pares sin camino» como dato del problema hasta confirmarlo.

Nota sobre un nombre: en OpenStreetMap hay una calle residencial de 4 m llamada «Arroyo El Salao» (vía 898051045). El programa la muestra como «Vía local junto al eje (en OSM: Arroyo El Salao)» para que la pantalla no hable de arroyos. Es un dato de OSM; **falta confirmar en Street View** que esa calle de 102 m sirva como ruta alterna.

Otros experimentos (betweenness, sensibilidad, control de lados, histograma, voraz contra fuerza bruta) están en `resultados/experimentos/`; el informe de cambios, en `resultados/informe_cambios.md`.

## 5. Organización

```
proyecto_obras/
  app.py               servidor Flask: GET /, GET /api/ejemplo, GET /api/ejemplo_obra, POST /api/analizar, POST /api/plan
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
  src/supuestos.py     todos los supuestos de las propuestas calculadas (valor, rango, fuente y estado)
  src/demanda.py       demanda supuesta (modelo de gravedad), desvío ponderado, voraz ponderado y su fuerza bruta
  src/circulacion.py   propuestas calculadas: capacidad (corte mínimo), pares viales, pasos por demanda, control temporal
  herramientas/        plan_etapas.py, figuras_plan.py, eje_de_calle.py, experimentos.py, diagnostico_sin_camino.py, descargar_mapa.py
  datos/               ejemplos/, cache/ (calles guardadas), arroyo_el_salao.csv (eje del ejemplo)
  resultados/          salidas generadas; figuras/ (mapa y barras del plan); linea_base/ son las cifras de referencia de El Salao
  tests/               144 pruebas (API sin red, caso resuelto a mano, regresión contra linea_base, robustez, etapas, obras,
                       flujo máximo, demanda, circulación y propuestas calculadas)
  documento/main.tex, main.pdf                  documento en LaTeX (entrega)
  documento/preguntas.md  preguntas y respuestas de la sustentación
```

**Contrato `POST /api/plan`** (no romperlo: el JSON solo se agranda). Pedido: `{lineas, radio, luz_max, etapa_max_m (300–2000, 1000), un_puente_cada_m (200–1000, 500), cerrar_puentes (true), ancho_m (10–60, 10), medicion ("lados"), abiertos, cerrados}`. Respuesta: `obra`, `parametros`, `semaforos_conocidos`, `resumen`, `etapas[]` (con `eje`, `tramos_cerrados`, `peatones`, `vehiculos`, `rutas[]`, `carga[]`), `pasos[]`, `tiempos`, `recuadro`, `fuente`, `aviso_zona` y `en_cache`. Errores en JSON: 400 (pedido inválido o zona demasiado grande) y 503 (no se pudo descargar el mapa). Ejemplo real: `resultados/plan_etapas.json`. Opcional (sección 3b): `propuestas_calculadas` (true; con false la respuesta es la de antes) y `d0_m` (200–1000, 400).

**Datos:** calles © colaboradores de OpenStreetMap (ODbL), descargadas en noviembre de 2026 para el recuadro 10,84–11,12 N y 74,96–74,73 O (Barranquilla, Soledad, Malambo, Puerto Colombia y Galapa). Si la obra queda fuera de lo guardado, se descargan las calles de Overpass a `datos/cache/` (puede tardar minutos).

## 6. Estado del equipo

| Persona | Parte | Estado |
|---|---|---|
| Oscar | Ejemplo de obra (calle 72), integración, documento, limpieza final, esta documentación | Hecho |
| Karel | Refactor de arroyo a obra y `/api/plan` | Hecho (R1 a R6). Opcionales sin hacer: `medicion="afectados"` y pasos peatonales casi perpendiculares |
| Lobo | Pantalla: menú, recorrido, resultados, pantalla pequeña | Hecho |
| Blanco | Pruebas, robustez de `app.py`, revisión de textos | Hecho |
| Gustavo | Diapositivas (aparte, fuera del repositorio) | Hecho. Las figuras (`herramientas/figuras_plan.py`) y `tests/test_app.py` quedaron integradas |

## 7. Lo que falta

**Entrega (Brightspace, martes 17 de noviembre):** subir `proyecto_obras/documento/main.pdf` (tiene el enlace al repositorio; se compila con `pdflatex main.tex` dos veces desde `documento/`) y las diapositivas, que se preparan aparte.

**Pendiente de verificar** (en `main.tex` ya están escritos como «pendiente de verificar», sin recuadros rojos):
1. Cruces cerrados de El Salao (calle 61, carrera 22D, calle 59A, calle 60, calle 67A, calle 75 y la vía local junto al eje, que en OSM se llama «Arroyo El Salao»): confirmar en Street View que cruzan el arroyo.
2. La calle sin nombre de 6 m de **largo** junto a la avenida Murillo: confirmar en Street View que existe; si es un error de OSM, queda como limitación.

**Fuentes del documento sin abrir todavía.** Los datos de la canalización (CRA, 2022 y 2023; El Heraldo, 12 de noviembre de 2026), del taxi arrastrado (El Heraldo, 18 de octubre de 2026) y de la población de Soledad (DANE, censo 2018, 535.984 habitantes) salieron de dos informes de IA. Antes de la sustentación hay que abrir los enlaces de la bibliografía y confirmar que dicen eso. No hay cifra de habitantes del sector ni costo de la obra con fuente.

**Antes de la sustentación (lunes 16, 3:47 p. m.)**
- Ensayo cronometrado de los 10 minutos y la demo en el mismo computador que se va a usar.
- Cerrar cualquier `python app.py` viejo, abrir uno solo y cargar `/?ejemplo` antes de entrar (sección 2).
- Estudiar `documento/preguntas.md`: cada integrante debe poder responder todo.
- Capturas de la app como respaldo por si falla la demo (opcional).

**Opcionales sin hacer** (no bloquean la entrega)
- Pantalla: no se pueden corregir a mano tramos abiertos o cerrados, y `radio`, `luz_max` y `ancho_m` no están en la pantalla.
- En el ejemplo de la calle 72 aparecen «Calle 47» y «Carrera 18 Sur» entre las rutas alternas; puede ser cómo están nombradas en OSM.
- Claves heredadas del JSON (`arroyo`, `cauce`, `lluvia_m`) y el `User-Agent` de `osm.py`: se dejaron para no romper el contrato de `/api/plan`.
- Probar en un teléfono real y con alguien que planifique una obra sin explicación.

**Hecho en la última revisión:** documento reescrito al tema de obras por etapas con el caso resuelto a mano; figuras; pruebas de la API (incluido un error 500 corregido en `app.py`); plurales, acentos en Windows, favicon, `aviso_zona` visible y textos sin jerga en la pantalla; limpieza del código de arroyos (`/api/arroyos`, `--arroyo`, `--listar` y alias) sin cambiar ninguna cifra; README probado en un clon limpio.

**Definición de `ancho_m`:** se mide desde el eje hacia cada lado. Con 10, la franja mide 20 m de borde a borde; así está escrito en el documento.

**Límites que deben quedar escritos** (están en el documento, sección 6)
No hay datos de tránsito (no se mide congestión); los pesos son metros, no tiempo; no se diseñan carriles ni semáforos; no se evalúan costo, suelos ni diseño hidráulico; se usa una muestra de esquinas sin ponderar por población; la heurística voraz no garantiza el óptimo; se supone que la obra cierra los puentes existentes; la calidad de OSM depende de quien lo edita y hay que verificar en terreno.

## 8. Preguntas que pueden hacer en la sustentación

Están, con respuestas y por tema, en `proyecto_obras/documento/preguntas.md`. Las más probables:

- **¿Por qué quitar aristas y no aumentar el peso?** Un peso de penalización sería un número inventado; quitar la arista representa que no se puede pasar.
- **¿Por qué dos grafos?** Un peatón puede caminar en contravía y un carro no; además cada medida solo sirve a quien la usa.
- **¿El voraz da el óptimo?** No está garantizado; sí da el mejor candidato de cada ronda. Contra fuerza bruta con k = 2 eligió la misma pareja (`resultados/experimentos/`).
- **¿Dónde está la programación dinámica?** En los cortes entre etapas (`cortes` en `src/etapas.py`).
- **¿Por qué la mejor medida vehicular no baja el desvío medio?** Devuelve el camino a pares que antes no tenían ninguno y esos entran al promedio con recorridos largos.

## 9. Reglas del equipo

1. No inventar datos: población, noticias, costos, fechas y fuentes verificables y con enlace; si no, «pendiente de verificar».
2. Todas las pruebas deben pasar antes de cada commit (`python -m unittest`).
3. Si cambia una cifra, se actualiza el `.tex` en el mismo momento.
4. Después de correr `main.py` o `plan_etapas.py` sin querer regenerar, `git checkout -- proyecto_obras/resultados`.
5. Commits pequeños, con mensaje en español.
