# Proyecto final MAT 4021: plan de trabajo hasta la entrega

Matemáticas Discretas, Universidad del Norte. Equipo: Oscar Vélez, Gustavo de la Ossa, Sebastián Blanco, Karel Silva y Santiago Lobo.

> **ACTUALIZACIÓN (viernes 13, noche): el proyecto cambió de arroyos a «hacer obras viales de la mejor forma». El reparto y el plan vigentes están en [equipo/cambio_a_obras.md](equipo/cambio_a_obras.md). Lo que sigue (reparto de Persona 1, 2 y 3) quedó desactualizado.**

> Este archivo es el **plan del equipo**. Las instrucciones para instalar y ejecutar el programa siguen en [`proyecto_arroyos/README.md`](proyecto_arroyos/README.md).

**Entrega:** domingo 15 de noviembre de 2026, 11:59 p. m. (hora de Bogotá), por Brightspace.
**Se entrega:** el PDF en LaTeX y las diapositivas (10 minutos, 5 expositores, demo en vivo). Después viene la sustentación individual, que vale **40 %**: cada integrante debe poder explicar todo el proyecto, no solo su parte.

------

## 1. Resumen del proyecto

**Pregunta:** mientras se canaliza un arroyo, ¿qué medida temporal reduce más el desvío de quienes necesitan cruzarlo: un puente peatonal, cambiar el sentido de una calle o señalizar una ruta alterna?

**Caso de estudio:** el arroyo El Salao, en Soledad, donde hubo una emergencia el 4 de noviembre.

**Cómo se cumplen las cuatro condiciones de "problema de impacto":**

| Condición | Cómo se cumple | Estado |
|---|---|---|
| Afecta a alguien | Habitantes de los barrios junto al arroyo (Los Cedros, Las Moras y vecinos) | Falta la cifra con fuente |
| Hay evidencia | Emergencia del 4 de noviembre, canalización anunciada y emergencias anteriores | Faltan las fuentes |
| Se puede mejorar | Se mide el desvío en seco, con lluvia y con cada medida | Hecho |
| Se puede modelar | Grafos ponderados, BFS, Dijkstra, componentes y centralidades (unidades 3 y 4) | Hecho |

**El modelo en una línea:** las esquinas son nodos y las cuadras son aristas, con peso en metros. Hay un grafo no dirigido para peatones y uno dirigido para vehículos. La lluvia borra las aristas que cruzan el cauce. Dijkstra mide el desvío, una heurística voraz elige las medidas y para cada cruce cerrado se calcula una ruta alterna.

---

## 2. Estado actual

### Ya funciona (no rehacer)

- Código en Python, unas 2.100 líneas, en `proyecto_arroyos/`:
  - El grafo peatonal no dirigido y el vehicular dirigido, que respeta los sentidos viales, se arman con datos de OpenStreetMap (Overpass).
  - El escenario de lluvia se decide por geometría: se borra la calle que cruza el cauce o va sobre él, y se respetan los puentes.
  - El lado del arroyo de cada esquina se decide con el signo del producto cruz.
  - Se corre Dijkstra en seco y con lluvia sobre 14.400 pares por sentido (120 esquinas por lado, dentro de 400 m del cauce).
  - La heurística voraz actualiza las distancias con `min(d(a,b), d(a,x)+w+d(y,b))`, así que no hay que repetir Dijkstra para cada candidato.
  - Se calculan rutas alternas para cada cruce cerrado.
  - Hay una página web (Flask + Leaflet) y un `main.py` que genera `resumen.txt`, `analisis.json` y `mapa.png`.
- **22 pruebas unitarias en verde** (`python -m unittest -v`).
- `documento/main.tex` ya tiene las cifras de la versión actual, pero le quedan **7 `\completar{}`**.

### Resultados de El Salao (congelados)

No se cambian sin volver a correr todo y actualizar el `.tex`.

| Peatones (no dirigido) | Desvío medio | Pares > 200 m | Máximo |
|---|---|---|---|
| Lluvia | 70 m | 10,9 % | 763 m |
| Lluvia + 3 puentes peatonales | 26 m | 2,0 % | 440 m |

| Vehículos (dirigido) | Desvío medio | Pares > 200 m | Máximo | Sin camino |
|---|---|---|---|---|
| Lluvia | 138 m | 23,4 % | 1.580 m | 240 |
| + doble sentido en calle de 6 m (Av. Murillo) | 138 m | 23,4 % | 1.580 m | 120 |
| + doble sentido en calle de 112 m | 132 m | 23,4 % | 1.580 m | 120 |

### Hallazgo que la entrega debe reconocer

En vehículos la mejora es pequeña. La "mejor" medida (la calle de 6 m) **no mejora el desvío medio**: solo devuelve el camino a 120 pares y sube un poco la media, de 137,5 a 137,6 m, porque esos pares entran al promedio con recorridos largos. Las conclusiones deben decirlo con honestidad: con medidas temporales, el problema vehicular casi no se resuelve, y el peatonal sí.

**Hipótesis por verificar (Persona 1):** 240 = 2 × 120. Es probable que los 240 pares sin camino sean **una sola esquina** de la muestra que queda aislada (120 pares de ida y 120 de vuelta). La calle de 6 m le devolvería solo un sentido. Esa esquina estaría cerca de 10,9195 N, −74,7993 O, junto a la Av. Murillo. Si se confirma, hay que explicarlo así en el documento, porque cambia mucho la lectura de la cifra "240 pares".

---

## 3. Reglas de trabajo

1. **No inventar datos.** Población, noticias, costos, fechas y fuentes deben ser verificables, con enlace. Si no hay fuente, se deja `\completar{}` o "pendiente de verificar" con una nota.
2. **Pruebas en verde.** Todo cambio de código debe mantener las 22 pruebas (o más) pasando.
3. **Cifras sincronizadas.** Si cambia una cifra, se actualiza el `.tex` en el mismo momento.
4. **Congelamiento.** Hasta el **sábado 14 a las 23:00** se puede tocar código. El domingo solo se trabaja en el documento, las diapositivas y el ensayo. Los resultados se congelan antes de escribir las conclusiones.

---

## 4. Plan de mejoras por prioridad

### Prioridad 1: bloqueante para entregar

| # | Tarea | Responsable | Hecho |
|---|---|---|---|
| 1.1 | Completar los 7 `\completar{}` de `main.tex` (ver lista abajo) | P3, con insumos de P1 y P2 | [ ] |
| 1.2 | Caso de prueba a mano: grafo pequeño resuelto en papel y agregado a `tests/` con el resultado esperado | P1 | [ ] |
| 1.3 | Verificar la calle de 6 m contra OSM (identificador de la vía) y Street View. Si es un error de OSM, va como limitación, no como resultado | P2 | [ ] |
| 1.4 | Revisar en Street View los cruces bloqueados de El Salao y corregir en la web los que sí se puedan pasar. Luego volver a correr el análisis | P2 revisa, P1 vuelve a correr | [ ] |
| 1.5 | Escribir las limitaciones (ver lista abajo) | P3 | [ ] |
| 1.6 | Quitar de `proyecto_arroyos/README.md` la referencia al `.gz` que no existe, o terminar la descarga (van 55 de 56 celdas) | P2 | [ ] |
| 1.7 | Diapositivas, guion y demo en vivo | P3 | [ ] |

**Los 7 `\completar{}` de `main.tex`:**

1. Resumen: confirmar los cruces en Street View antes de cerrar las cifras (línea 32).
2. Habitantes de los barrios del sector, con cifra y fuente (DANE o Alcaldía de Soledad) (línea 38).
3. Noticias del 4 de noviembre, canalización anunciada (fecha y costo) y emergencias anteriores (línea 40).
4. Cómo se confirmó cada cruce en Street View (línea 56).
5. El caso de prueba hecho a mano por el grupo (línea 73).
6. Confirmación de la calle sin nombre de 6 m (línea 112).
7. Conclusiones propias del grupo (línea 119).

**Cruces que hay que revisar en Street View** (de `resultados/resumen.txt`; en metros, en seco → con lluvia):

| Cruce | Carro | A pie | ¿Se puede pasar? | Qué se vio |
|---|---|---|---|---|
| Calle 61 | 120 → 1.895 | 120 → 217 | | |
| Arroyo El Salao (vía) | 102 → 1.107 | 102 → 957 | | |
| Carrera 22D | 102 → 1.107 | 106 → 934 | | |
| Calle 59A | 177 → 1.155 | 46 → 576 | | |
| Carrera 22A | 173 → 1.092 | 173 → 725 | | |
| Calle 60 | 132 → 1.048 | 132 → 288 | | |
| Calle 67A | 153 → 1.035 | 153 → 1.022 | | |
| Calle 75B | — | 108 → 937 | | |
| Calle 75 | 118 → 869 | 83 → 903 | | |
| Calle 67 | 189 → 1.004 | 132 → 790 | | |
| Calle 75C | — | 101 → 835 | | |
| Calle 74A | — | 84 → 688 | | |
| Calle 74B | — | 118 → 721 | | |
| Calle 74 | 103 → 652 | 103 → 652 | | |
| Calle 58A | — | 50 → 529 | | |
| Calle sin nombre de 6 m (≈ 10,9195 N, −74,7993 O) | medida propuesta | — | | |

**Limitaciones que deben quedar escritas:**

- En OpenStreetMap, `drain` y `ditch` pueden ser canales de drenaje y no arroyos. Además, hay cauces sin nombre.
- Se usa una muestra de 120 esquinas por lado, sin ponderar por población.
- La heurística voraz no garantiza el óptimo.
- La lluvia es binaria: la calle está abierta o cerrada. No se modelan niveles, velocidad del agua ni pendiente.
- Los pesos están en metros y no en tiempo: no hay velocidades ni congestión.
- No se evalúan costo, suelos ni diseño hidráulico de las medidas.
- La calidad de OSM depende de quien lo edita, y por eso los cruces se verifican en Street View.

### Prioridad 2: mejora matemática (solo si la prioridad 1 avanza)

| # | Tarea | Para qué sirve | Hecho |
|---|---|---|---|
| a | **Función objetivo:** reportar por separado los pares sin camino y el desvío medio. Si se necesita un solo número, usar orden lexicográfico (primero los pares sin camino, luego el desvío medio) y justificarlo en el documento | Resuelve la confusión de la calle de 6 m | [ ] |
| b | **Betweenness** para encontrar los cruces críticos del grafo vehicular, con y sin lluvia | Usa centralidades, que son tema del curso | [ ] |
| c | **Voraz contra fuerza bruta** con k = 2 en un grafo pequeño, como cota empírica | Responde «¿el voraz da el óptimo?» con datos | [ ] |
| d | **Sensibilidad** a la luz máxima del puente y al tamaño de la muestra, con histograma de desvíos | Muestra que las conclusiones no dependen de un parámetro | [ ] |
| e | **Control del lado del arroyo:** comparar el producto cruz con una clasificación por componentes conexas del grafo con lluvia (como control, no como reemplazo) | Valida la clasificación de lados | [ ] |

Orden sugerido si no hay tiempo para todo: **a → c → b → d → e**.

### Prioridad 3: trabajo futuro (solo va en las limitaciones)

Niveles de lluvia, velocidad del agua, pendiente, pesos en tiempo, muestra ponderada por población o destinos (colegios, hospitales, paradas) y validación con datos reales.

---

## 5. Reparto

En el reparto trabajan tres personas. Los nombres de cada una están **por definir**.

| Rol | Persona | Tareas | Entrega |
|---|---|---|---|
| **Persona 1: modelo y código** | *por definir* | Prioridad 2 (a a e), caso de prueba a mano (1.2), pruebas en `tests/`, volver a correr el análisis tras la revisión en Street View (1.4) y reproducir las cifras con `main.py` | Código final con pruebas en verde y `analisis.json` actualizado |
| **Persona 2: datos y verificación** | *por definir* | Fuentes de población y evidencia, verificación de la calle de 6 m (1.3), revisión de cruces en Street View (1.4) y descarga o retiro del `.gz` (1.6) | Tabla de cruces verificados (la de arriba, completa), lista de fuentes con enlace y confirmación de la calle |
| **Persona 3: documento y presentación** | *por definir* | Completar el LaTeX (1.1), limitaciones (1.5), interpretación y conclusiones, diapositivas, guion, demo en vivo (1.7) y README final | PDF compilado y diapositivas con ensayo cronometrado |

**Dependencia:** Persona 3 no redacta los resultados finales hasta que Persona 1 y Persona 2 confirmen las cifras.

**Cadena crítica:** Persona 2 revisa Street View → Persona 1 vuelve a correr el análisis → Persona 3 escribe resultados y conclusiones. La revisión en Street View debe estar lista el **sábado a media tarde**, para que Persona 1 alcance a volver a correr antes del congelamiento de las 23:00.

---

## 6. Cronograma

| Cuándo | Qué |
|---|---|
| **Viernes 13, noche** | El equipo aprueba este README y asigna Persona 1, 2 y 3 |
| **Sábado 14** | P1: caso de prueba a mano y prioridad 2 (a y c). P2: fuentes y Street View (lista a media tarde). P3: redacta lo ya confirmado (modelo, algoritmos, limitaciones) y arma la estructura de las diapositivas |
| **Sábado 14, 23:00** | **Se congela el código.** P1 publica el `analisis.json` y el `resumen.txt` finales |
| **Domingo 15, mañana** | Integrar las cifras finales en el LaTeX, terminar las diapositivas y ensayar en 10 minutos |
| **Domingo 15, antes de las 18:00** | Compilar el PDF, revisar que no quede ningún `\completar` y entregar con margen antes de las 23:59 |

---

## 7. Preguntas abiertas para el equipo

- [ ] ¿Quién es Persona 1, quién Persona 2 y quién Persona 3?
- [ ] ¿Qué hacen los otros dos integrantes? Todos sustentan individualmente, así que todos deben estudiar el proyecto completo.
- [ ] ¿Se hace betweenness (prioridad 2b) o solo a y c?
- [ ] ¿Quién prepara las preguntas difíciles para la sustentación individual? Hay una lista inicial en la sección 10.

---

## 8. Cómo funciona, paso a paso

Todos deben poder explicar esto en la sustentación.

1. **Mapa a grafo.** Cada esquina es un nodo y cada cuadra es una arista. El peso de la arista es la longitud en metros. Los datos vienen de OpenStreetMap.
2. **Dos grafos.**
   - Peatones: grafo **no dirigido**, porque a pie se camina en ambos sentidos.
   - Vehículos: grafo **dirigido**, porque las calles de un solo sentido solo tienen el arco permitido.
3. **Lluvia.** Se borran las aristas que cruzan el cauce o van por encima de él, salvo los puentes. También se borran las de las esquinas que quedan dentro del cauce.
4. **Lados.** Cada esquina queda a la izquierda o a la derecha del cauce. Para saberlo se usa el signo del producto cruz con el segmento más cercano.
5. **Desvío.** Para cada par de esquinas en lados opuestos se calcula el camino mínimo con Dijkstra, en seco y con lluvia. El desvío es la diferencia entre los dos.
6. **Medidas.** Para cada medida candidata se calcula cuánto baja el desvío medio, y se elige la mejor. Esto es una heurística voraz.
   - **Fórmula rápida.** Al agregar un arco x→y con peso w, la nueva distancia de a a b es `min(d(a,b), d(a,x) + w + d(y,b))`. Así no hay que repetir Dijkstra para cada candidato.
   - **Grafo invertido.** En el grafo dirigido, `d(y,b)` se obtiene corriendo Dijkstra desde b en el grafo invertido.
   - **Parada temprana.** Dijkstra cierra los nodos en orden de distancia. Cuando ya cerró todas las esquinas que interesan, se detiene: lo que falta por explorar no puede acortar esos caminos.
   - **Solo los pares que mejoran.** Si `d(a,x) + w + min_b d(y,b)` no es menor que el par más largo de la fila de a, el candidato no ayuda a nadie de esa fila y se salta.
   - **Siguiente ronda sin repetir Dijkstra.** Las tablas nuevas salen de la misma fórmula: `d'(a,v) = min(d(a,v), d(a,x) + w + d(y,v))`. Bastan 2 Dijkstra por arco elegido.
   - Con esto, El Salao pasó de unos 36 s a 6–8 s con exactamente los mismos resultados (hay pruebas que lo comparan).
7. **Ruta alterna.** Para cada cruce cerrado se calcula el camino mínimo que queda con lluvia.

---

## 9. Guion de 10 minutos

Los expositores están por definir.

| Min. | Expositor | Contenido |
|---|---|---|
| 0–1:30 | 1 | El problema: el 4 de noviembre, a quién afecta y la evidencia |
| 1:30–3:30 | 2 | Del mapa al grafo; grafos de peatones y de vehículos; escenario de lluvia |
| 3:30–5:30 | 3 | Dijkstra, la fórmula rápida, la heurística voraz y las pruebas |
| 5:30–7:30 | 4 | Resultados de El Salao, incluido el hallazgo honesto sobre vehículos |
| 7:30–9:30 | 5 | Demostración en vivo: «Cargar el ejemplo», clic en una ruta alterna, corregir una calle y analizar otro arroyo de Barranquilla |
| 9:30–10 | Todos | Limitaciones y cierre |

Traten el caso del 4 de noviembre con respeto: no usen nombres de las víctimas ni afirmen qué ruta debieron tomar.

---

## 10. Preguntas que les pueden hacer en la sustentación

- **¿Por qué quitar aristas y no aumentarles el peso?** Un peso de penalización sería un número inventado. Quitar la arista representa que no se puede pasar.
- **¿Por qué dos grafos?** Un peatón puede caminar en contravía y un carro no. Además, el puente peatonal solo sirve a peatones y el cambio de sentido solo sirve a vehículos. Por eso cada medida se compara con el grafo de quien la usa.
- **¿Por qué no hay puente vehicular?** Costaría y tardaría casi lo mismo que la canalización. Solo se proponen medidas temporales.
- **¿La heurística voraz da el óptimo?** No está garantizado. Sí da el mejor candidato individual en cada ronda (ver prioridad 2c).
- **¿Cómo saben qué calles se inundan?** Por geometría: la calle cruza el cauce o va sobre él. Después se verifica en Street View y se corrige en la web.
- **¿Qué pasa si OpenStreetMap está mal?** Es una limitación. La web permite corregir cada cruce, y en El Salao se verificó con Street View.
- **¿Por qué una muestra de esquinas?** Con todas, el cálculo tardaría minutos. Con 120 por lado son 14.400 pares, y tarda segundos.
- **¿Por qué la mejor medida vehicular no baja el desvío medio?** Porque devuelve el camino a pares que antes no tenían ninguno, y esos entran al promedio con recorridos largos (ver sección 2).
- **¿Por qué no usaron una red neuronal?** No hay datos etiquetados para entrenarla, y el problema es de caminos en una red.
- **¿El puente propuesto es construible?** El modelo solo mide conectividad. No evalúa suelos, costos ni diseño hidráulico.
