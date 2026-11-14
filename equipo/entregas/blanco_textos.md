# Revisión de textos (B4)

Criterios: trato de **usted**, sin jerga («grafo», «Dijkstra», «pares», «nodos»), cada error dice **qué pasó y qué
hacer**, y las mismas palabras para lo mismo: **obra**, **etapa**, **paso peatonal provisional**, **calle a doble
sentido**, **esquina para controlar**.

Resultado general: no hay «tú» en la pantalla (todo está en usted). Los problemas son jerga, plurales y la misma
cosa dicha de tres formas («cambio de sentido» / «calle a doble sentido» / «doble sentido»).

Los cambios de `app.py` marcados con ✅ ya se hicieron en B3. Lo demás es una **propuesta** para el dueño: no lo
cambié.

## `src/etapas.py` (Karel): textos de `pasos[]` y `avisos`, que la pantalla muestra tal cual

| Texto actual | Texto propuesto | Por qué |
|---|---|---|
| «En carro: desvío medio de 332 m; 60 pares sin camino; 1 cambio(s) de sentido.» | «En carro: desvío medio de 332 m; 60 recorridos de la muestra se quedan sin camino; 1 calle pasa a doble sentido.» | «(s)» y «pares» (jerga); misma palabra que el panel |
| «Se cierran 24 cruces, 1 de ellos puentes existentes.» | «Se cierran 24 cruces; 1 de ellos es un puente existente.» (y «3 de ellos son puentes existentes») | Plural |
| «Por el largo de la etapa corresponden 2 pasos peatonales, pero solo 1 reduce el desvío.» | «Por el largo de la etapa corresponden 2 pasos peatonales provisionales, pero solo 1 reduce el desvío; no hace falta poner los demás.» (con «solo 2 reducen» en plural) | Plural del verbo y qué hacer |
| «Hay muy pocas esquinas cerca de esta etapa para medir el desvío.» | «Hay muy pocas esquinas cerca de esta etapa para medir el desvío. Revise en terreno cómo se rodea este tramo.» | Decir qué hacer |
| Título «Cambios de sentido» (unidad «calles a doble sentido») | «Calles a doble sentido» | La misma palabra que la cifra y el panel |
| «etapa 1: 2, etapa 2: 2, etapa 3: 1.» | «Por etapa: 2 en la primera, 2 en la segunda y 1 en la tercera.» | Empieza en minúscula y se lee como una lista técnica |
| «Uno por cada 500 m de obra, repartidos a lo largo del tramo.» | «Un paso peatonal provisional por cada 500 m de obra, repartidos a lo largo de la obra.» | Decir de qué se habla; «tramo» se usa para otra cosa |
| «…se hace por tramos de hasta 1000 m.» (y «La obra mide 2.386 m») | «…se hace por tramos de hasta 1.000 m.» | Mismo separador de miles en las dos cifras |
| «Solo se proponen si reducen el desvío o devuelven el camino a alguien.» | «Solo se proponen si reducen el desvío o si vuelven a dejar pasar a quien se había quedado sin camino.» | Más claro |
| «Los pasos peatonales y cambios de sentido deben verificarse en terreno antes de proponerlos.» | «Los pasos peatonales provisionales y las calles a doble sentido deben verificarse en terreno antes de proponerlos.» | Mismas palabras |
| «No se sabe si tienen semáforo: faltan datos.» | «No se sabe si tienen semáforo: esta zona no tiene ese dato en el mapa guardado. Revíselo en terreno.» | Qué hacer |

## `web/app.js` (Lobo)

| Texto actual | Texto propuesto | Por qué |
|---|---|---|
| «Cómo leer esto: para cada par de esquinas a lados opuestos de la obra se calcula el camino más corto antes y durante la obra (algoritmo de Dijkstra); el desvío es la diferencia.» | «Cómo leer esto: se toman esquinas a los dos lados de la obra y, para ir de una a otra, se compara el camino más corto antes y durante la obra; el desvío es cuánto más hay que recorrer.» | Jerga («Dijkstra», «par») |
| «Pares que se quedan sin camino: 60 → 0» | «Recorridos que se quedan sin camino: 60 → 0» | Jerga |
| «En carro o moto: desvío medio» (tarjeta de etapa) | «En carro: desvío medio» | En el resto de la pantalla dice «En carro» |
| «Con 1 cambio» / «Con 2 pasos» (barras de comparación) | «Con 1 calle a doble sentido» / «Con 2 pasos peatonales» | Mismas palabras |
| «Doble sentido: Calle X» (ventana del mapa) | «Calle a doble sentido: Calle X» | Mismas palabras |
| «Esquinas que reciben más recorridos desviados» (título de la lista) | «Esquinas para controlar» (con la explicación debajo) | La cifra y la leyenda dicen «esquinas para controlar» |
| «No hay conexión con el servidor. ¿Está corriendo python app.py?» | «No se pudo conectar con el programa. Compruebe que la ventana donde corre `python app.py` sigue abierta y vuelva a intentarlo.» | Qué hacer, sin pregunta |
| «El servidor respondió con un error (500).» / «Error del servidor (500).» | «El programa tuvo un problema al planificar la obra (error 500). Vuelva a intentarlo; si se repite, pruebe con otro tramo.» | Qué hacer |
| «No se pudo cargar el ejemplo (404).» | «No se pudo cargar el ejemplo (error 404). Recargue la página e inténtelo de nuevo.» | Qué hacer |
| «El ejemplo no trae el eje de la obra.» | «El archivo del ejemplo no tiene el eje de la obra. Avise al equipo; mientras tanto, dibuje la obra a mano.» | Qué hacer |
| «El servidor no envió pasos para el recorrido.» | «Este plan no trae el recorrido paso a paso. Los resultados de abajo sí están completos.» | Qué pasó, sin jerga |
| (no existe) | Mostrar `plan.aviso_zona` cuando no sea `null`, como un aviso amarillo debajo de «Listo». | Campo nuevo de B3 |

## `web/index.html` (Lobo)

| Texto actual | Texto propuesto | Por qué |
|---|---|---|
| «Marque sobre el mapa el eje de la obra: la línea de calles que se van a cerrar.» | Sin cambio. | Bien |
| «Un paso peatonal provisional cada … m» | Sin cambio. | Bien |
| «La obra cierra también los puentes existentes» | «La obra cierra también los puentes que ya existen en el tramo» | Más claro para quien no sabe qué «puente existente» es |

## `app.py` (Lobo; cambiado en B3 con su permiso donde dice ✅)

| Texto actual | Texto propuesto | Estado |
|---|---|---|
| 500 con NaN: «Ocurrió un error inesperado…» | «Hay puntos de la obra sin coordenadas válidas. Borre la obra y vuelva a dibujarla.» | ✅ |
| Latitud 200: «La zona es muy grande (112.8 km de lado)…» | «Hay puntos de la obra con coordenadas fuera de rango (…¿están al revés?). Revise los puntos y vuelva a intentarlo.» | ✅ |
| Más de 2.000 puntos: (no se controlaba) | «La obra tiene demasiados puntos (más de 2.000). Dibújela con menos clics o divídala en obras más cortas.» | ✅ |
| Cuerpo que no es JSON en `/api/analizar` y 404/405 bajo `/api/`: página HTML en inglés | Mensaje en español y en JSON | ✅ |
| «Datos del pedido inválidos.» | «Los datos de la obra no tienen el formato esperado. Borre la obra y vuelva a dibujarla.» | Propuesta |
| «cerrar_puentes debe ser true o false.» / «medicion debe ser una de: lados.» | Se dejan así: solo los ve quien llama a la API a mano, nunca la pantalla. | — |
| «La zona es muy grande (8.8 km de lado). Marque una obra más corta, de unos 4 km como máximo.» | «La obra es muy larga: la zona que hay que analizar mide 8,8 km de lado. Divídala en obras de unos 4 km como máximo y planifique cada una.» | Propuesta (coma decimal y qué hacer) |
| «Ocurrió un error inesperado al planificar esta obra. Pruebe con otro tramo o revise la consola donde corre app.py.» | Sin cambio. | Bien |
| «Marque el arroyo con al menos dos puntos.» (`/api/analizar`, ruta vieja) | Se quita con `/api/analizar` en la limpieza de Oscar. | — |

## `src/osm.py` (Karel)

| Texto actual | Texto propuesto | Por qué |
|---|---|---|
| «No se pudieron descargar las calles de OpenStreetMap. Revise la conexión a internet o intente en unos minutos.» | Sin cambio. | Dice qué pasó y qué hacer |

## Nombres que vienen de OpenStreetMap (Oscar decide)

| Dónde | Texto | Nota |
|---|---|---|
| Ruta alterna de la etapa 2 de El Salao | «Arroyo El Salao» | Es el nombre de la vía en OpenStreetMap, no un texto del programa. No se inventa otro; si se quiere ocultar, mostrarlo como «Cruce sobre la obra (Arroyo El Salao en OpenStreetMap)» |
| Calle 72: rutas alternas | «Calle 47», «Carrera 18 Sur» | Ya lo anotó Karel: revisar antes de mostrar |
| Esquinas | «Carrera22B» (sin espacio), «Calle 76A 1» | Así están en OpenStreetMap |
