# Obras viales por etapas

Proyecto final de Matemáticas Discretas (MAT 4021), Universidad del Norte.
Equipo: Oscar Vélez, Gustavo de la Ossa, Sebastián Blanco, Karel Silva y Santiago Lobo.
Repositorio: https://github.com/odvelez/StreetView

## 1. Qué es

Cuando una obra cierra calles, la gente que vive alrededor tiene que dar vueltas. Este programa recibe el eje de una obra dibujado sobre el mapa, la divide en etapas y propone medidas temporales para que el desvío sea menor: pasos peatonales provisionales, cambios de sentido, rutas alternas y esquinas a controlar.

Lo probamos con la canalización del arroyo El Salao, en Soledad (2.386 m). La emergencia del 4 de noviembre de 2026 en ese arroyo es lo que nos llevó al tema, pero el trabajo no analiza la emergencia: analiza cómo planificar una obra así.

Pregunta del proyecto: al planificar una obra que cierra calles, ¿cómo se divide en etapas y qué medidas temporales reducen más el desvío de quienes la rodean?

## 2. Cómo ejecutarlo

Hace falta Python 3.10 o superior. Flask se usa para la pantalla y matplotlib para las figuras; los algoritmos usan solo la biblioteca estándar. Para El Salao no se necesita internet: las calles ya están guardadas en `datos/cache/`.

```bash
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_obras
python -m pip install -r requirements.txt
python -m unittest                  # 144 pruebas, tardan alrededor de un minuto
python app.py                       # pantalla en http://localhost:5000/?ejemplo
```

Otros comandos (siempre desde `proyecto_obras/`):

```bash
python herramientas/plan_etapas.py                      # plan por etapas de El Salao, solo imprime
python herramientas/plan_etapas.py --guardar            # además escribe resultados/plan_etapas.txt y .json
python herramientas/plan_etapas.py --sin-calculadas     # sin las propuestas calculadas (sección 3)
python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json    # otra obra
python main.py                                          # toda la obra a la vez: resultados/resumen.txt, analisis.json, mapa.png
python herramientas/experimentos.py                     # comprobaciones del modelo, tarda varios minutos
```

`main.py` y `plan_etapas.py --guardar` sobrescriben `resultados/`. Si se ejecutan sin querer, `git checkout -- proyecto_obras/resultados` deja todo como estaba.

En la pantalla se elige el municipio, se dibuja la obra (o se carga el ejemplo), se pulsa «Planificar» y se sigue el recorrido paso a paso. El primer plan de El Salao tarda entre 10 y 40 segundos según el computador; después sale del caché. Si algo se ve raro, hay que revisar que no haya otro `python app.py` abierto: en Windows dos servidores pueden ocupar el puerto 5000 y el navegador puede estar hablando con el viejo.

Una obra es un archivo JSON con su nombre y una o más líneas de puntos `[latitud, longitud]`:

```json
{"nombre": "Obra ilustrativa en la calle 72", "ilustrativo": true,
 "lineas": [[[10.9187, -74.7981], [10.9190, -74.7975]]]}
```

## 3. Qué calcula

1. Las esquinas son nodos y las cuadras son aristas con su largo en metros (OpenStreetMap). Hay un grafo no dirigido para peatones y uno dirigido para vehículos.
2. La obra quita las aristas que toca: las cuadras que cruzan el eje o van sobre él, en una franja de 10 m a cada lado, incluidos los puentes existentes. Quitar la arista representa que no se puede pasar; subirle el peso habría sido un número inventado.
3. Para cada par de esquinas en lados opuestos, Dijkstra da el camino más corto sin la obra y con ella. El desvío es la diferencia.
4. El número de etapas sale del largo de la obra (hasta 1.000 m cada una) y los cortes se eligen con programación dinámica para que ninguna etapa concentre demasiados cruces cerrados.
5. Las medidas se eligen con una heurística voraz: en cada ronda se agrega la que más baja el desvío medio. Para no repetir Dijkstra con cada candidato se usa `d'(a,b) = min(d(a,b), d(a,x) + w + d(y,b))` al agregar un arco x→y de peso w.
6. Para cada cruce cerrado se calcula la ruta alterna. A pie pasa por el paso provisional más cercano. Se marcan las esquinas por las que pasan más recorridos desviados y si OpenStreetMap registra un semáforo ahí.

Además, el programa calcula cinco propuestas más. Vienen activas por defecto en la pantalla, la API y los scripts, y se apagan con `--sin-calculadas` o con `"propuestas_calculadas": false` en `POST /api/plan`. Todas usan una demanda supuesta, no medida; los supuestos están en `src/supuestos.py`, cada uno con su valor, su rango y su estado.

- Demanda supuesta (modelo de gravedad): cada par de esquinas pesa `exp(-distancia / d0)`, con d0 = 400 m.
- Capacidad para cruzar la obra: flujo máximo (Edmonds–Karp) de un lado al otro; el corte mínimo dice cuántos carriles quedan y por qué calles.
- Pares viales: calles locales paralelas de un solo sentido, para dejar una en cada sentido.
- Pasos peatonales por demanda: un voraz ponderado decide cuántos y dónde, y se informa el mayor tramo sin cruce.
- Control temporal: esquinas con más demanda desviada. Es una priorización, no un criterio para instalar semáforos.

## 4. Resultados de El Salao

De `python herramientas/plan_etapas.py`:

- 3 etapas (975, 850 y 561 m).
- 5 pasos peatonales con la regla de uno cada 500 m, y 16 si se eligen por demanda.
- 3 cambios de sentido, 18 rutas alternas y 15 esquinas a controlar (14 sin semáforo registrado).
- 9 esquinas candidatas a control temporal. No salió ningún par vial: en OpenStreetMap casi no hay calles locales de un solo sentido en paralelo cerca de la obra.

Desvío medio a pie, con la obra y con los pasos provisionales: etapa 1, de 387 a 48 m; etapa 2, de 129 a 28 m; etapa 3, de 219 a 56 m. En carro el desvío medio es de 332, 287 y 293 m, y los cambios de sentido casi no lo bajan. Con medidas temporales el problema peatonal mejora mucho y el vehicular casi no.

Con la obra completa a la vez, sin etapas, el desvío medio a pie es de 70 m y baja a 26 m con tres pasos. Si los puentes existentes se mantienen abiertos (`--mantener-puentes`), el desvío a pie con la obra baja a 68, 56 y 36 m; es el supuesto que más pesa en las cifras.

Los archivos están en `resultados/`. Las comprobaciones (voraz contra fuerza bruta, sensibilidad, control del lado, histograma) están en `resultados/experimentos/` y se explican en `resultados/informe_cambios.md`.

## 5. Estructura de carpetas

```
proyecto_obras/
  app.py            servidor Flask: GET /, GET /api/ejemplo, GET /api/ejemplo_obra, POST /api/analizar, POST /api/plan
  main.py           análisis de toda la obra a la vez, por terminal
  web/              pantalla (Leaflet): menú, recorrido paso a paso y resultados
  src/              grafo.py (grafos, BFS, Dijkstra, flujo máximo), red.py, geometria.py, analisis.py, etapas.py,
                    demanda.py, circulacion.py, supuestos.py, control.py, comparacion.py, fuente.py, osm.py
  herramientas/     plan_etapas.py, experimentos.py, figuras_plan.py, eje_de_calle.py, descargar_mapa.py,
                    diagnostico_sin_camino.py
  datos/            ejemplos/, cache/ (calles guardadas) y arroyo_el_salao.csv (eje del ejemplo)
  resultados/       salidas del programa; linea_base/ guarda las cifras de referencia que usan las pruebas
  tests/            144 pruebas
```

`POST /api/plan` recibe `lineas` y parámetros opcionales (`etapa_max_m`, `un_puente_cada_m`, `cerrar_puentes`, `ancho_m`, `d0_m`, entre otros) y devuelve el plan con `resumen`, `etapas[]` y `pasos[]`. Un ejemplo completo está en `resultados/plan_etapas.json`.

## 6. Datos y límites

Las calles son de OpenStreetMap (© colaboradores, licencia ODbL), descargadas en noviembre de 2026 para el recuadro 10,84–11,12 N y 74,96–74,73 O (Barranquilla, Soledad, Malambo, Puerto Colombia y Galapa). Si una obra queda fuera de lo guardado, el programa descarga las calles con Overpass a `datos/cache/`.

Lo que hay que tener presente al leer los resultados:

- No tenemos datos de tránsito. Medimos desvíos en metros, no congestión.
- La demanda y los carriles de las propuestas calculadas son supuestos nuestros. Sirven para ordenar medidas, no para medir.
- Los datos de noticias, de la obra de canalización y de la población de Soledad (535.984 habitantes, censo 2018) son aproximados y no los hemos contrastado uno por uno con sus fuentes. No sabemos el número de habitantes del sector ni el costo de la obra.
- Suponemos que la obra cierra también los puentes existentes de su tramo.
- OpenStreetMap puede tener errores. Falta confirmar en Street View que los cruces que el modelo cierra existen de verdad (por ejemplo calle 61, carrera 22D, calle 59A y calle 75). Todo debe verificarse en terreno.
- No diseñamos carriles ni tiempos de semáforo, y no evaluamos costos, suelos ni diseño hidráulico. La heurística voraz no garantiza el óptimo.

## 7. Equipo

| Persona | Parte |
|---|---|
| Oscar Vélez | Integración, ejemplo de la calle 72 y documentación |
| Karel Silva | Paso de arroyos a obras, `/api/plan` y propuestas calculadas |
| Santiago Lobo | Pantalla: menú, recorrido paso a paso y resultados |
| Sebastián Blanco | Pruebas, robustez de `app.py` y revisión de textos |
| Gustavo de la Ossa | Figuras del plan y presentación |
