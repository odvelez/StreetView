# Preguntas de la sustentación

Grupo 7: Oscar Vélez, Gustavo de la Ossa, Sebastián Blanco, Karel Silva y Santiago Lobo.

La sustentación individual vale 40 % y **cada uno debe poder responder todo**, no solo su parte. Hay 5 minutos de preguntas, al grupo o a una persona. Respondan corto: la idea en una frase y después el dato o el archivo.

Cada uno empieza por el tema que expone y después estudia los demás:

| Integrante | Empieza por | Después |
|---|---|---|
| Oscar | 1. Problema y pregunta | todos |
| Karel | 2. Modelo y 3. Algoritmos | todos |
| Gustavo | 4. Resultados a pie y plan | todos |
| Sebastián | 4. Resultados en carro, 5. Límites y comprobaciones | todos |
| Santiago | 6. Datos, programa y demostración | todos |

Fuentes de las cifras: `resultados/plan_etapas.txt` (plan por etapas), `resultados/resumen.txt` (toda la obra a la vez), `resultados/informe_cambios.md` y `resultados/experimentos/`.

---

## 1. Problema y pregunta

**¿Cuál es la pregunta del proyecto?**
Al planificar una obra que cierra calles, ¿cómo se divide en etapas y qué medidas temporales reducen más el desvío de quienes la rodean?

**¿Por qué El Salao?**
Es el ejemplo principal: canalizarlo es una obra larga que cerraría las calles y los puentes que hoy lo cruzan. El 4 de noviembre es la motivación, no el tema. No damos nombres ni opinamos sobre qué ruta debieron tomar.

**¿El proyecto es sobre arroyos?**
No. Es sobre cómo planificar cualquier obra que cierra calles. El programa no está amarrado a El Salao: se puede dibujar otra obra (por ejemplo la de la calle 72, que es ilustrativa y no una obra real).

**¿Qué medidas temporales proponen?**
Cuatro: pasos peatonales provisionales (uno por cada 500 m de obra, mínimo uno por etapa), cambios de sentido (hasta 2 por etapa), rutas alternas señalizadas para cada cruce cerrado y control en las 5 esquinas por etapa con más recorridos desviados.

**¿Por qué no un puente vehicular?**
Costaría y tardaría casi lo mismo que la obra. Solo proponemos medidas temporales.

**¿Cuántas personas afecta?**
No hay cifra del sector de El Salao: el DANE no la publica desagregada. Solo podemos decir que Soledad tenía 535.984 habitantes en el censo de 2018.

---

## 2. Modelo

**¿Qué es un nodo y qué es una arista?**
Nodo = esquina. Arista = cuadra, con su largo en metros como peso.

**¿Por qué dos grafos?**
A pie se puede ir en contravía y en carro no: peatones en un grafo no dirigido y vehículos en uno dirigido. Además, cada medida sirve a uno solo: el paso peatonal solo a peatones y el cambio de sentido solo a vehículos.

**¿Cómo se representa la obra?**
Quitando las aristas de las cuadras que cruzan el eje o van sobre él, en una franja de 10 m a cada lado (20 m de borde a borde), incluidos los puentes existentes.

**¿Por qué quitar aristas y no subirles el peso?**
Un peso de penalización sería un número inventado. Quitar la arista representa exactamente que no se puede pasar.

**¿Cómo saben de qué lado está cada esquina?**
Por el signo del producto cruz con el segmento más cercano del eje. Lo comprobamos contra las componentes conexas: coinciden al 100 % en 1.229 esquinas.

**¿Qué es el desvío?**
Para dos esquinas en lados opuestos: Δ(a, b) = d_obra(a, b) − d(a, b). Es la distancia mínima con la obra menos la distancia mínima sin ella.

**¿Qué es un cambio de sentido en el grafo?**
Agregar el arco contrario a una calle de un solo sentido.

**¿Y un paso peatonal?**
Agregar una arista al grafo de peatones. Puede devolver un cruce que la obra cerró, o ser un paso nuevo de hasta 60 m en línea recta entre esquinas de lados opuestos.

---

## 3. Algoritmos

**¿Qué hace Dijkstra aquí?**
Da la distancia mínima en metros entre esquinas, sin obra y con obra. Está hecho a mano, con cola de prioridad, en `src/grafo.py`.

**¿Por qué Dijkstra y no BFS?**
Las aristas tienen pesos distintos (metros). BFS solo sirve si todas pesan lo mismo.

**¿Por qué pueden detener Dijkstra antes de terminar?**
Dijkstra cierra los nodos en orden de distancia: cuando ya cerró todas las esquinas que necesitamos, sus distancias son definitivas. Hay una prueba que lo comprueba.

**¿Qué es la fórmula de arco nuevo?**
Al agregar x→y con peso w: d'(a, b) = min(d(a, b), d(a, x) + w + d(y, b)). Un camino mínimo usa el arco nuevo a lo sumo una vez. Así evaluamos cada candidato sin repetir Dijkstra; el análisis bajó de unos 36 s a entre 6 y 8 s, con los mismos resultados.

**¿Cómo obtienen d(y, b) en el grafo dirigido?**
Con Dijkstra desde b en el grafo invertido.

**¿Qué hace el voraz?**
En cada ronda agrega el candidato que más mejora el objetivo: primero menos pares sin camino y después menor desvío medio. Solo lo acepta si mejora al menos un 2 %.

**¿El voraz da el óptimo?**
No está garantizado; da el mejor candidato de cada ronda. Con dos medidas lo comparamos con fuerza bruta: eligió la misma pareja entre 1.225 parejas de pasos peatonales y entre 11.325 de cambios de sentido. Hay una prueba con un caso construido en el que el voraz falla.

**¿Dónde está la programación dinámica?**
En los cortes entre etapas (`cortes` en `src/etapas.py`). Hay n = ⌈largo / 1.000 m⌉ etapas y los cortes posibles van cada 25 m. Para cada número de etapas s y cada punto j guardamos el mejor costo de dividir el eje hasta j. El costo es un par: primero el mayor número de cruces de una sola etapa y después la suma de los cuadrados. Así ninguna etapa concentra demasiados cruces.

**¿Por qué programación dinámica y no probar todas las divisiones?**
El problema tiene subestructura óptima: la mejor división hasta j con s etapas se arma con la mejor división hasta algún i con s − 1 etapas, más el tramo de i a j. Con la tabla se calcula una sola vez cada subproblema.

**¿Qué otros temas del curso usaron?**
BFS y componentes conexas (control del lado) e intermediación de Brandes (cruces críticos con toda la obra a la vez; describe el problema, no se usó para elegir medidas).

**Explique el caso resuelto a mano.**
Seis esquinas, A, B, C al norte y D, E, F al sur, con cuadras de 100 m y cruces A–D (80 m), B–E (50 m) y C–F (50 m). La etapa cierra A–D y B–E. El desvío medio de los 9 pares es 970 / 9 ≈ 107,8 m. Con un paso en B–E baja a 18,9 m y con uno en A–D a 28,9 m. El voraz elige B–E porque está en el centro y sirve a más pares. Está en el documento (sección 4) y en `tests/test_app.py`.

---

## 4. Resultados

**¿Cuál es el plan para El Salao?**
2.386 m en 3 etapas (975, 850 y 561 m): 5 pasos peatonales provisionales, 3 cambios de sentido, 18 rutas alternas y 15 esquinas a controlar, de las cuales 14 no tienen semáforo registrado en OpenStreetMap.

**¿Cuánto baja el desvío a pie?**
Etapa 1: de 387 a 48 m. Etapa 2: de 129 a 28 m. Etapa 3: de 219 a 56 m.

**¿Por qué la etapa 1 es la más difícil?**
Tiene el mayor desvío a pie con la obra (387 m): cierra 24 cruces, 3 de ellos puentes existentes.

**¿Y en carro?**
El desvío medio con la obra es de 332, 287 y 293 m, y con el cambio de sentido queda en 332, 279 y 293 m. Casi no baja. **Este es el hallazgo honesto: con medidas temporales el problema peatonal mejora mucho y el vehicular casi no.**

**¿Por qué la mejor medida vehicular no baja el desvío medio?**
Porque sobre todo devuelve el camino a pares que no tenían ninguno, y esos pares entran al promedio con recorridos largos. En la etapa 1, los pares sin camino pasan de 60 a 0: es una mejora real aunque el promedio no la muestre.

**¿Entonces qué recomiendan en carro?**
Señalizar las rutas alternas y controlar las esquinas de más carga. La calle elegida para cambiar de sentido cambia con otra muestra de esquinas, así que no es una recomendación firme.

**Den un ejemplo de ruta alterna.**
En la etapa 3, el cruce de la calle 61 pasa de 120 a 1.895 m en carro y de 120 a 1.107 m a pie.

**¿Qué es la "carga" de una esquina?**
Cuántos recorridos desviados de la muestra pasan por ella. No es congestión, porque no tenemos datos de tránsito. La de más carga es la calle 60 con carrera 18 (72,9 % de los recorridos desviados de la etapa 3).

**¿Qué pasa con toda la obra a la vez?**
Es el escenario de comparación. A pie, el desvío medio es 70 m, y con 3 pasos baja a 26 m (63 % menos); los pares con más de 200 m de desvío pasan de 10,9 % a 2,0 %. En carro, 138 m con la obra y 132 m con doble sentido en 2 calles.

**¿Los pasos nuevos pueden dejar a alguien mejor que sin obra?**
Sí. Algunos pasos nuevos son atajos, así que el desvío medio mezcla recorridos recuperados con atajos nuevos.

---

## 5. Límites y comprobaciones

**¿Qué no mide el modelo?**
- No hay datos de tránsito, así que no se mide congestión.
- Los pesos son metros, no tiempo.
- No se diseñan carriles ni semáforos.
- No se evalúan costo, suelos ni diseño hidráulico.
- La muestra de esquinas no se pondera por población.
- El voraz no garantiza el óptimo.
- Todo debe verificarse en terreno.

**¿Cuál es el supuesto que más pesa?**
Que cada etapa cierra también los puentes existentes de su tramo. Si se mantuvieran abiertos, el desvío a pie con la obra sería de 68, 56 y 36 m (`informe_cambios.md`, sección 7).

**¿Por qué una muestra de esquinas?**
Por tiempo de cómputo. Con toda la obra a la vez se usan 120 por lado (14.400 pares) y tarda segundos; en el plan por etapas, 60 por lado en cada etapa.

**¿La muestra cambia los resultados?**
A pie, poco: con otros tamaños de muestra el desvío con 3 pasos queda entre 22 y 28 m, y con todas las esquinas da 27,6 m. En carro, la medida recomendada sí cambia, y por eso no la presentamos como firme.

**¿Cómo saben que el programa calcula bien?**
Con las pruebas automáticas (`python -m unittest`):
- grafos y caminos resueltos a mano;
- una red miniatura con desvío conocido;
- la fórmula rápida comparada contra repetir Dijkstra;
- el plan por etapas y la API;
- el caso a mano del documento.

Y con los experimentos de `resultados/experimentos/`.

**¿Y si OpenStreetMap está mal?**
Es una limitación. Por eso cada cruce cerrado se debe verificar en Street View. Por ejemplo, la calle sin nombre de 6 m junto a la avenida Murillo puede ser un error del mapa.

---

## 6. Datos, programa y demostración

**¿De dónde salen los datos?**
De OpenStreetMap (© colaboradores, licencia ODbL), descargados con Overpass en noviembre de 2026. La red tiene 5.859 esquinas y 8.827 tramos. Están guardados en `datos/cache/`, así que no hace falta internet para El Salao.

**¿Cómo saben qué calles cierra la obra?**
Por geometría: la calle cruza el eje o va sobre él dentro de la franja. Después se verifica en Street View.

**¿Qué es la vía local "Arroyo El Salao" que aparece en las rutas?**
Es una calle de 102 m que en OpenStreetMap se llama así. La pantalla la muestra como «vía local junto al eje». Falta confirmar en Street View que sirva como ruta alterna.

**¿Cómo se corre?**
Desde `proyecto_obras/`: `python -m pip install -r requirements.txt`, `python -m unittest` y `python app.py`; después se abre `http://localhost:5000/?ejemplo`. El primer plan tarda entre 10 y 40 s y los siguientes salen del caché.

**¿Qué hace la pantalla?**
Elegir el municipio, dibujar la obra o cargar el ejemplo, y planificar. Después se recorre el plan paso a paso. Al hacer clic en un cruce cerrado se ve la ruta en carro y a pie, con enlace a Street View.

**¿Con qué está hecha?**
Servidor en Flask (Python) y mapa con Leaflet. Los algoritmos usan solo la biblioteca estándar de Python.

**¿Por qué no usar una librería de grafos o una red neuronal?**
Queríamos implementar los algoritmos del curso nosotros mismos. No hay datos etiquetados para una red neuronal, y el problema es de caminos en una red.

**¿La medida propuesta es construible?**
El modelo solo mide conectividad. Que una medida mejore el desvío no quiere decir que se pueda construir: eso requiere estudio técnico.
