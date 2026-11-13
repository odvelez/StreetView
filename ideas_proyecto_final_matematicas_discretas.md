# Ideas para el Proyecto Final: Matemáticas Discretas (MAT 4021)

Seis ideas de problemas de impacto en Barranquilla, el Atlántico y la región Caribe, modeladas solo con las Unidades 3 y 4 (grafos, BFS, Dijkstra, componentes, centralidades). No requieren álgebra booleana ni perceptrón.

**Avisos antes de decidir**

- El PDF y las diapositivas se entregan el **domingo 15 de noviembre, 11:59 pm**. Conviene escoger rápido y quedarse con la idea que tenga datos fáciles de conseguir.
- Las cifras vienen de las fuentes citadas, pero varían entre años y medios. Verifíquenlas antes de ponerlas en el documento.
- No se verificó la disponibilidad de los conjuntos de datos mencionados. Confírmenlos antes de comprometerse.

**Las cuatro condiciones de "problema de impacto"** (según el PDF del profesor): afecta a alguien, hay evidencia, se puede mejorar (medir antes y después) y se puede modelar. Cada idea responde a las cuatro.

---

## Resumen para decidir

| # | Idea | Dificultad | Evidencia | Datos |
|---|------|-----------|-----------|-------|
| 1 | Transmetro: estaciones críticas y rutas | Baja | Buena | Se arma a mano |
| 2 | Rutas seguras frente a los arroyos | Baja-media | Muy buena | Mapa de un sector |
| 3 | Siniestralidad vial (motociclistas) | Media | Muy buena | Datos abiertos (verificar) |
| 4 | Recolección de basuras en puntos críticos | Baja-media | Buena | Mapa de un barrio |
| 5 | Colaboración científica en el Caribe | Media | Moderada | Por conseguir |
| 6 | Cobertura de ambulancias y hospitales | Media | Débil | Estimados |

Recomendación: **1, 2 o 4** son las más seguras con el tiempo que queda. La 2 es la más fuerte para la condición de impacto.

---

## IDEA 1. Estaciones críticas y rutas del Transmetro (Barranquilla y Soledad)

**Problema.** Transmetro es un sistema tronco-alimentado y las rutas alimentadoras son las más propensas a retrasos, porque circulan por carriles mixtos en zonas de mayor congestión. Hay que saber qué estaciones, paraderos y transbordos sostienen la red y cuáles la dejan más expuesta.

**Quiénes son afectados.** Usuarios diarios (estudiantes y trabajadores), incluidos quienes vienen desde Soledad.

**Evidencia.**
- El sistema tiene 14 km de troncales (Murillo y Olaya Herrera), 198 km de rutas alimentadoras y 116 paradas señalizadas, con una matriz de transbordo [1].
- Los usuarios se quejan de retrasos constantes, sobre todo en las mañanas [2].
- En 2024 hubo una crisis de flota que obligó a usar 28 buses del transporte público colectivo para reforzar las alimentadoras en horas pico [3].

**Cómo se mide la mejora.** Antes y después de una propuesta (un nuevo transbordo o una ruta express): distancia promedio entre estaciones, diámetro de la red y cercanía promedio.

**Modelado.**
- **Nodos:** estaciones y paraderos (por ejemplo Joe Arroyo, La Arenosa, Joaquín Barrios Polo, Pedro Ramayá).
- **Aristas:** tramos directos entre dos paradas consecutivas de una ruta (B1, S1, S2, R1, A1-3, etc.).
- **Peso:** minutos de viaje, o 1 si se mide en número de paradas.
- **Dirección:** empiecen no dirigido; si hay tiempo, pasen a dirigido.
- **Tipo de red:** transporte (infraestructura).

**Temas del curso.** Lista de adyacencia, BFS (número de paradas), Dijkstra (tiempo), conexidad, componentes y las tres centralidades.

**Qué calcular.**
- Grado: qué estación concentra más conexiones.
- Cercanía: dónde ubicar un servicio.
- Intermediación: qué estación, si falla, aísla partes de la red.
- Dijkstra: ruta más corta entre barrios.
- Simulación de falla: quitar la estación de mayor intermediación y ver cuántos pares de nodos quedan desconectados (componentes).

**Datos.** Mapa y listado de rutas del sistema. Se puede construir a mano con unas 20 a 30 estaciones. Los tiempos pueden medirse ustedes mismos o ser una simulación justificada.

**Caso de prueba.** Un grafo estrella o camino, donde el resultado se conoce de antemano. En la estrella, el centro tiene centralidad de grado 1 e intermediación máxima.

**Dificultad.** Baja. Es la idea más segura.

**Fuentes.**
- [1] https://www.elheraldo.co/barranquilla/mas-de-409-millones-de-usuarios-movilizados-por-transmetro-en-14-anos-1109097
- [2] https://www.elheraldo.co/barranquilla/2022/08/12/quejas-por-retrasos-en-rutas-del-sistema-masivo-transmetro-929917/
- [3] https://www.infobae.com/colombia/2024/02/26/crisis-en-transmetro-de-barranquilla-buses-de-servicio-publico-reemplazaran-alimentadores/

---

## IDEA 2. Rutas seguras frente a los arroyos de Barranquilla y Soledad

**Problema.** Los arroyos siguen siendo un riesgo durante las lluvias. Se necesita una forma de elegir rutas que eviten cruces peligrosos y de identificar los cruces más críticos de un sector.

**Quiénes son afectados.** Peatones, motociclistas, conductores y familias de barrios inundables en Barranquilla y Soledad.

**Evidencia.**
- El observatorio ciudadano Proyecto Arroyos documentó al menos 117 muertes hasta octubre de 2025, la mayoría hombres menores de 40 años y peatones [1].
- Un experto señala que las lluvias intensas todavía generan corrientes superficiales en sectores como Don Juan, Salao y el occidente [1].
- En Soledad, el desbordamiento de los arroyos Platanal, Villegas y El Salao dejó al menos 1.260 familias damnificadas y más de 40 barrios afectados [2].
- Los episodios son recientes: durante las lluvias de esta semana, las autoridades reportaron el hallazgo sin vida de un adulto mayor arrastrado por un arroyo en Soledad, con búsqueda activa de una niña [3].

**Cómo se mide la mejora.** Porcentaje de rutas de un barrio a un punto seguro (hospital, colegio, estación) que cruzan arroyos, antes y después de aplicar el modelo. También el aumento de longitud de la ruta segura frente a la más corta.

**Modelado.**
- **Nodos:** intersecciones de un sector (30 a 50 bastan), más puntos de interés (hospital, colegio, estación).
- **Aristas:** tramos de calle.
- **Peso:** longitud más una penalización alta si el tramo cruza un arroyo (decisión de modelado que deben justificar).
- **Dirección:** no dirigido para las calles. Opcionalmente, un digrafo aparte para el flujo del agua (confluencias como nodos y tramos como arcos hacia el río).
- **Tipo de red:** infraestructura.

**Temas del curso.** Grafo ponderado, Dijkstra, BFS, conexidad (si se bloquean los cruces peligrosos, ¿el barrio queda aislado? Se ve con componentes), digrafo y grados de entrada y salida.

**Qué calcular.**
- Ruta más corta frente a ruta más segura.
- Intermediación de los cruces, para saber cuáles concentran más caminos.
- Componentes conexas al bloquear cruces.

**Datos.** Mapa del sector y puntos de cruce de arroyos, que pueden ubicar con noticias, el mapa de la ciudad y observación directa.

**Caso de prueba.** Un grafo pequeño de 6 nodos donde calculen a mano la ruta segura.

**Dificultad.** Baja a media. Lo más trabajoso es construir el grafo del sector.

**Fuentes.**
- [1] https://www.infobae.com/colombia/2026/07/20/asi-evolucionaron-los-famosos-y-peligrosos-arroyos-de-barranquilla-117-personas-fueron-arrastradas-en-el-ultimo-siglo/
- [2] https://www.elespectador.com/colombia/barranquilla/lluvias-dejaron-a-mas-de-1200-familias-damnificadas-en-soledad/
- [3] https://www.elespectador.com/colombia/mas-regiones/hallan-sin-vida-a-adulto-mayor-arrastrado-por-arroyo-en-soledad-buscan-a-su-nieta-de-5-anos/

---

## IDEA 3. Puntos críticos de siniestralidad vial (motociclistas)

**Problema.** Hay que priorizar dónde controlar y qué corredores intervenir. La pregunta es si los nodos más centrales de la red vial coinciden con los que más siniestros concentran.

**Quiénes son afectados.** Motociclistas, peatones y conductores. Las motos son las más afectadas.

**Evidencia.**
- En 2025, Barranquilla reportó 95 víctimas por siniestros, de las cuales 53 eran motociclistas (56%) [1].
- En las capitales del Caribe, los motociclistas son el 58% de las víctimas, y la región muestra siniestralidad creciente desde 2020, con un aumento de 47% en muertos en tres años [2].
- El Distrito ya aplica restricciones: el Decreto 0703 de 2025 prohíbe la circulación nocturna de motos entre las 11:00 p. m. y las 5:00 a. m., salvo excepciones [3].

**Cómo se mide la mejora.** Porcentaje de siniestros que caen dentro de los k nodos o corredores priorizados por el modelo (por ejemplo, los 5 con mayor intermediación). Esa es la cobertura de un plan de controles.

**Modelado.**
- **Nodos:** intersecciones o corredores principales (Circunvalar, Vía 40, Murillo, Olaya Herrera, La Cordialidad, etc.).
- **Aristas:** tramos viales que los unen.
- **Peso:** número de siniestros del tramo, o 1.
- **Dirección:** no dirigido (simplificación que deben justificar).
- **Tipo de red:** infraestructura.

**Temas del curso.** Grafo, grado, cercanía, intermediación, BFS y comparación de rankings.

**Qué calcular.** Las tres centralidades de cada nodo, y luego compararlas con el ranking de siniestros. Interpreten ambos resultados: si coinciden, la estructura de la red explica el riesgo; si no, hay otros factores (velocidad, tipo de vehículo).

**Datos.** Conjuntos de siniestros de Barranquilla en el portal Datos Abiertos Colombia (hay trabajos que mencionan haberlos usado; verifiquen cuál y qué columnas tiene).

**Caso de prueba.** Un grafo pequeño inventado con centralidades calculadas a mano.

**Dificultad.** Media. La limpieza de datos es lo más pesado, así que usen una muestra de corredores.

**Fuentes.**
- [1] https://www.eluniversal.com.co/regional/atlantico/2025/11/04/restriccion-de-motos-en-barranquilla-continuan-vigente-hasta-octubre-de-2026/
- [2] https://www.eltiempo.com/colombia/barranquilla/siniestralidad-en-el-caribe-prende-alarmas-cada-6-horas-muere-una-persona-en-las-vias-3326554
- [3] https://www.infobae.com/colombia/2025/11/13/ojo-si-pensaba-viajar-a-barranquilla-en-moto-y-no-cuenta-con-permiso-de-circulacion-distrito-extendio-restricciones-de-transito-hasta-2026/

---

## IDEA 4. Rutas de recolección de basuras en puntos críticos

**Problema.** Los basureros a cielo abierto reaparecen pocas horas después de limpiarlos, y buena parte de esos residuos termina en los arroyos. Se necesita una ruta eficiente de recorrido para limpiar los puntos críticos de un sector.

**Quiénes son afectados.** Vecinos de los sectores con basureros y quienes viven cerca de arroyos que se obstruyen con residuos.

**Evidencia.**
- Un informe distrital identificó 60 puntos críticos y más de 2.500 toneladas de residuos al mes en ellos. El servicio de limpieza de esos puntos cuesta cerca de $246.000.000 mensuales [1].
- Cada año se retiran más de 50.000 toneladas de residuos de los cuerpos de agua [2].
- En 2026 se retiraron 4.421 toneladas de la trampa del arroyo León, con 12 puntos críticos a lo largo de su cuenca [3].

El número de puntos críticos cambia según el año y el criterio (aparecen cifras de 23, 25, 35 y 60). Dejen constancia de eso en el documento.

**Cómo se mide la mejora.** Distancia total recorrida por el camión, o número de cuadras repetidas, con la ruta propuesta frente a una ruta ingenua.

**Modelado.**
- **Versión A (circuito de Euler):** el grafo de un barrio, con aristas = cuadras que el camión debe recorrer. Se cuentan los vértices de grado impar. Si hay 0, existe un circuito euleriano; si hay 2, un camino euleriano; si hay más, hay que repetir cuadras, y se determina cuáles con caminos mínimos entre pares de vértices impares. Elijan un sector pequeño para que sea manejable.
- **Versión B:** nodos = puntos críticos y el depósito, aristas = rutas entre ellos con tiempo como peso. Se usa Dijkstra y un árbol de expansión mínima para ver la red mínima de conexión.
- **Dirección:** no dirigido (o dirigido si hay calles de un solo sentido).
- **Peso:** metros o minutos. Opcionalmente, toneladas como peso del nodo.

**Temas del curso.** Teorema de Euler, grado, caminos mínimos, árbol de expansión mínima (Kruskal o Prim) y Dijkstra.

**Datos.** Mapa de un barrio con los puntos críticos identificados en prensa y en datos distritales.

**Caso de prueba.** El grafo de los puentes de Königsberg o el "moño" de la Unidad 3, cuyos resultados ya conocen.

**Dificultad.** Baja a media.

**Fuentes.**
- [1] https://www.elheraldo.co/barranquilla/2021/10/19/el-plan-para-erradicar-60-basureros-a-cielo-abierto-en-barranquilla-858603/
- [2] https://www.elheraldo.co/atlantico/2026/04/12/distrito-retira-anualmente-mas-de-50000-toneladas-de-residuos-de-los-cuerpos-de-agua/
- [3] https://www.elespectador.com/colombia/barranquilla/tras-las-lluvias-el-arroyo-leon-quedo-cubierto-de-basura-en-barranquilla/

---

## IDEA 5. Red de colaboración científica en el Caribe colombiano

**Problema.** Se quiere saber quiénes conectan a grupos de investigación que de otro modo estarían aislados, y si hay "islas" de investigadores sin colaboración entre universidades de la región. La evidencia de impacto aquí es más débil que en las ideas anteriores, así que tendrán que reforzarla.

**Quiénes son afectados.** Investigadores, semilleros y estudiantes de universidades de la región, y la región misma por su capacidad científica.

**Evidencia.**
- Un estudio sobre universidades públicas del Caribe (grupos 2013-2017) encontró que el porcentaje promedio de docentes investigadores con formación avanzada fue 27,9%, inferior al 30,7% nacional [1].
- Los rectores del Sistema Universitario Estatal sostienen que las universidades generan el 90% de la investigación científica en Colombia [2].
- La CUC reporta 43 grupos de investigación (16 en A1) y el primer lugar en producción científica en el Caribe [3]. Es un dato institucional autoinformado; tómenlo con cautela.

Falta evidencia directa sobre la desconexión entre grupos. Eso lo medirían ustedes con su propia red.

**Cómo se mide la mejora.** Número de componentes conexas de la red y nodos puente. Luego se plantea agregar k colaboraciones propuestas y se mide cuánto baja el número de componentes o el diámetro.

**Modelado.**
- **Red bipartita:** autores y artículos.
- **Proyección** sobre los autores: dos autores son adyacentes si comparten al menos un artículo. Esa es la red de colaboración.
- **Peso:** número de artículos en común (opcional).
- **Dirección:** no dirigido.

**Temas del curso.** Redes bipartitas y proyección (Unidad 4), componentes conexas, grado, intermediación y cercanía (si el grafo no es conexo, usen una de las dos opciones de la diapositiva).

**Qué calcular.**
- Componentes conexas.
- Autores con mayor intermediación (los puentes).
- Autores con mayor grado.
- Qué pasa al retirar un nodo puente.

**Datos.** Publicaciones públicas (bases abiertas de producción científica, CvLAC/GrupLAC de Minciencias). Con unas 100 a 300 publicaciones de unas pocas universidades alcanza.

**Caso de prueba.** El ejemplo de las diapositivas, con estudiantes P1 a P4 y cursos X, Y, Z.

**Dificultad.** Media. La obtención de datos es lo más lento.

**Fuentes.**
- [1] https://core.ac.uk/download/327121458.pdf
- [2] https://www.eluniversal.com.co/regional/minciencia-y-la-academia-fortaleceran-la-investigacion-en-el-caribe-DF7106371
- [3] https://www.cuc.edu.co/wp-content/uploads/2025/06/6.-INFORME-DE-GESTION-ANO-2024.pdf

---

## IDEA 6. Cobertura de ambulancias y hospitales en el Atlántico

**Problema.** Se quiere saber qué barrios o municipios están a más tiempo de un hospital y dónde conviene ubicar una ambulancia. La evidencia pública es más débil y los datos son más difíciles, así que es la última opción.

**Quiénes son afectados.** Pacientes en urgencias, sobre todo en municipios periféricos y zonas rurales.

**Evidencia.**
- Una entrega reciente de 20 ambulancias para 18 municipios y el Distrito de Barranquilla, con una inversión de más de $5.400 millones, muestra que el tema es prioridad pública. Solo tres de ellas son medicalizadas [1].
- Un preprint reciente analiza la capacidad instalada de salud en Barranquilla y habla de fragilidad estructural, concentración de la oferta y baja reserva [2]. Es un estudio estructural, no una medición de saturación en tiempo real, así que no lo sobrevendan.

**Cómo se mide la mejora.** Porcentaje de barrios que quedan a menos de X minutos de un hospital o ambulancia, antes y después de ubicar una unidad adicional.

**Modelado.**
- **Nodos:** barrios o municipios y hospitales.
- **Aristas:** vías que los unen.
- **Peso:** minutos de viaje.
- **Dirección:** no dirigido.

**Temas del curso.** Dijkstra, cercanía (la mejor ubicación es el nodo con mayor cercanía) y componentes.

**Datos.** Mapa de municipios y vías principales, y ubicación de hospitales. Los tiempos serían estimados y deben justificarlos.

**Caso de prueba.** Un grafo pequeño con una solución calculada a mano.

**Dificultad.** Media. Lo difícil es justificar los tiempos sin datos oficiales de respuesta.

**Fuentes.**
- [1] https://consultorsalud.com/entrega-de-20-ambulancias-atlantico-minsalud/
- [2] https://www.preprints.org/manuscript/202605.1254/v1

---

## Preguntas para definir en grupo

1. ¿Cuál idea nos interesa más y de cuál podemos conseguir datos esta semana?
2. ¿Qué sector o barrio acotamos para que el grafo sea manejable (20 a 50 nodos)?
3. ¿Qué lenguaje usamos y quién arma el grafo, quién el código y quién el documento en LaTeX?
4. ¿Cuál será nuestro caso de prueba de resultado conocido?
