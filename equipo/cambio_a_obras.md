# Cambio de proyecto: de arroyos a obras viales

**Léelo primero. Aplica a las cinco personas.** Última actualización: viernes 13 de noviembre, noche.
**Entrega final:** domingo 15 de noviembre, 11:59 p. m.

## 1. El nuevo objetivo

El proyecto **ya no trata de arroyos**. Trata de **cómo hacer obras de la mejor forma vial**: dada una obra que cierra calles, dividirla en etapas y proponer medidas temporales para que la movilidad no se pare.

> **Pregunta nueva:** al planificar una obra que cierra calles, ¿cómo se divide en etapas y qué medidas temporales (pasos peatonales provisionales, cambios de sentido, rutas alternas, control en esquinas) reducen más el desvío de quienes la rodean?

**El Salao sigue como ejemplo principal:** la canalización de El Salao es una obra que cierra calles. El 4 de noviembre es la motivación; ya no es el tema.

## 2. Qué se mantiene

- La **solución por etapas** (`src/etapas.py`): número de etapas según el largo, cortes con programación dinámica, un paso peatonal por cada 500 m de obra, cambios de sentido, rutas alternas, esquinas con más recorridos desviados y semáforos conocidos.
- El **menú de inicio**, el **recorrido paso a paso** (cifra grande, resto desenfocado, botón «Siguiente») y la lista de etapas.
- El contrato `POST /api/plan` y los `pasos[]` (ver sección 5).
- Los algoritmos y las **44 pruebas**, que deben seguir en verde.

## 3. Mapa de términos

| Antes | Ahora |
|---|---|
| arroyo, cauce | **obra**, **eje de la obra** (la línea) y **franja de obra** (el eje con un ancho) |
| clase `Arroyo` | clase `Obra` |
| lluvia | **toda la obra a la vez, sin etapas** (escenario de comparación) |
| tramos bloqueados con lluvia | tramos **cerrados por la obra** |
| puente peatonal temporal | **paso peatonal provisional** |
| puentes existentes | calles que la obra puede **mantener abiertas** (`cerrar_puentes`) |
| capa azul de arroyos, «Marque el arroyo», `--arroyo`, `--listar` | se quitan de la pantalla y de la línea de comandos |

## 4. Reparto nuevo

| Persona | Qué hace | Archivos propios | Rama |
|---|---|---|---|
| **Karel Silva** | **Refactorización** del proyecto: de arroyo a obra, sin cambiar las cifras | `src/`, `main.py`, `herramientas/plan_etapas.py`, `herramientas/experimentos.py`, `tests/` | `karel/refactor-obras` |
| **Santiago Lobo** | **Mejora gráfica**: menú, resultados y recorrido paso a paso, más la ruta `/api/plan` mínima | `web/`, `app.py` | `lobo/grafico` |
| **Gustavo de la Ossa** | Exposición (diapositivas y guion) y programación de apoyo en archivos **nuevos** | `herramientas/figuras_plan.py`, `herramientas/eje_de_calle.py`, `datos/ejemplos/`, `tests/test_app.py`, `equipo/entregas/gustavo_*` | `gustavo/apoyo` |
| **Sebastián Blanco** | **Segunda ronda**: integra y corrige cuando Karel y Lobo hayan subido | lo que haga falta, **después** de ellos | `blanco/ajustes` |
| **Oscar Vélez** | Integrador: revisa, resuelve conflictos, limpia al final y deja la app lista | `README.md`, `resultados/`, `documento/` y archivos compartidos | `main` |

## 5. Contrato `POST /api/plan` (no lo rompas)

Pedido: `{lineas, radio, luz_max, etapa_max_m, un_puente_cada_m, cerrar_puentes, abiertos, cerrados}`. Respuesta:

```
arroyo {longitud_m, lineas}      parametros {radio_m, luz_max_m, etapa_max_m, un_puente_cada_m, cerrar_puentes}
semaforos_conocidos (número o null)      resumen {etapas, longitud_m, puentes_peatonales, cambios_de_sentido,
                                                  rutas_alternas, esquinas_de_control, esquinas_sin_semaforo, etapa_mas_dificil}
etapas[] {numero, inicio_m, fin_m, longitud_m, cauce[[lat,lon]...], tramos_cerrados[ids], cruces_cerrados,
          puentes_existentes_cerrados, puentes_necesarios, recorridos_desviados, avisos[textos],
          peatones   null | {pares, candidatos, obra{métricas}, con_puentes{métricas}, puentes[]},
          vehiculos  null | {pares, candidatos, recuperados, obra{métricas}, con_medidas{métricas}, medidas[]},
          rutas[]  {via, carro{seco_m, lluvia_m, desde, hasta, cerrado, forma}, pie{...}},
          carga[]  {esquina, nombre, posicion[lat,lon], recorridos, porcentaje, semaforo: true|false|null}}
pasos[]  {id, titulo, cifra, unidad, detalle[textos], etapa (número o null), capas[], foco[[lat,lon],[lat,lon]]}
métricas {pares, sin_camino, distancia_media_m, desvio_medio_m, pct_mayor_200m, desvio_max_m, desvio_fijo_m}
```

Cada puente (`puentes[]`): `orden`, `tipo`, `via`, `desde`, `hasta`, `recorrido_m`, `forma`, `pos_m`. Cada cambio de sentido (`medidas[]`): `orden`, `via`, `desde`, `hasta`, `metros`, `forma`, `pos_m`. En `rutas`, `lluvia_m` es el recorrido **con la obra** (nombre heredado). Ejemplo real completo: `proyecto_arroyos/resultados/plan_etapas.json`.

## 6. Reglas para no chocar (importantes)

1. **Cada archivo tiene un solo dueño** (tabla de la sección 4). Si necesitas cambiar un archivo ajeno, no lo toques: escribe la petición en tu archivo `.md` y avisa a Oscar.
2. **El JSON solo se agranda: agrega campos, no los quites ni los renombres.** Así la pantalla de Lobo no se rompe mientras Karel refactoriza. Karel puede **agregar** `eje` junto a `cauce`; el nombre viejo se quita al final, y lo hace Oscar.
3. **No se borra nada** de `datos/` ni funciones que otro archivo todavía use (por ejemplo `fuente.arroyos_osm` o `/api/arroyos`). Oscar limpia al final.
4. **Cada quien trabaja en su rama** y hace commits pequeños con mensajes claros en español. Antes de empezar: `git pull`. Nadie sube directo a `main`.
5. **Las 44 pruebas deben pasar** antes de cada commit (`python -m unittest`).
6. **No se inventan datos.** Sin fuente, queda como pendiente.
7. `main.py` y `plan_etapas.py` **sobrescriben `resultados/`**. Después de correrlos, `git checkout -- proyecto_arroyos/resultados`, salvo que Oscar pida regenerarlos.

## 7. Parámetros nuevos (los agrega Karel; los usa la pantalla después)

| Parámetro | Valor por defecto | Para qué |
|---|---|---|
| `ancho_m` | 10 | Ancho de la franja de obra. Con 10 m el resultado es **idéntico** al de hoy |
| `medicion` | `"lados"` | Cómo se miden los recorridos. `"lados"` es como hoy. `"afectados"` es una mejora opcional |

## 8. Formato de un archivo de obra

Para obras fuera de El Salao (lo hace Gustavo y lo lee Karel):

```json
{"nombre": "Obra ilustrativa en la calle 72", "ilustrativo": true,
 "lineas": [[[10.9187, -74.7981], [10.9190, -74.7975]]]}
```

`lineas` es una lista de líneas, cada una una lista de puntos `[lat, lon]`. Si `ilustrativo` es `true`, la pantalla muestra «Ejemplo ilustrativo, no es una obra real».

## 9. Orden de trabajo (para que la app funcione y no haya choques)

**Principio:** cada quien toca solo sus archivos y **nadie sube a `main`**. Oscar junta las ramas **en este orden** y, después de cada unión, corre `python -m unittest` y abre la app. Si algo falla, se devuelve a su dueño antes de seguir.

| Paso | Cuándo | Quién | Qué | Para pasar al siguiente |
|---|---|---|---|---|
| **0** | Ya | Oscar | Sube la base (commit y push). Todos descargan el proyecto | Todos lo tienen |
| **1** | Sábado, hasta mediodía | Karel, Lobo y Gustavo, **a la vez** (tocan archivos distintos) | Karel: R1 y R2. Lobo: L1 (`/api/plan`). Gustavo: G2 (ejemplo de obra) y G1 (esqueleto de diapositivas) | Cada uno hace push de su rama y avisa a Oscar |
| **2** | Sábado, mediodía | Oscar | Junta en `main`, **en este orden**: Karel (R1+R2), Lobo (L1), Gustavo (G2). Corre las pruebas y prueba `/api/plan` con El Salao | Pruebas en verde y `/api/plan` responde 3 etapas |
| **3** | Sábado, tarde | Karel, Lobo y Gustavo | Todos hacen `git pull` de `main` y siguen: Karel R3 a R5; Lobo L2 a L6; Gustavo G3 y G4 | Karel y Lobo hacen push y avisan |
| **4** | Sábado, fin del día | Oscar | Junta: Karel (R3 a R5), Lobo (L2 a L6), Gustavo (G3 y G4). Corre pruebas y abre la app | La app funciona con El Salao y con el ejemplo de Gustavo |
| **5** | Sábado noche y domingo temprano | Blanco | Prueba la app integrada y devuelve cada fallo a su dueño (B1 a B4) | Fallos corregidos |
| **6** | Domingo, mañana | Oscar | Limpieza final (quitar lo de arroyo, el campo `cauce`, el alias `Arroyo` y los datos de arroyos), regenerar resultados, README y documento. Gustavo toma las capturas finales | App lista antes de las 18:00 |

**Por qué este orden**
- Karel va antes que Lobo porque la ruta de Lobo llama al código de Karel.
- Gustavo entrega el ejemplo de obra antes de que Karel lo necesite (R3).
- Blanco va al final porque prueba lo que los otros ya terminaron.
- Oscar limpia al final porque quitar lo viejo mientras otros todavía lo leen rompería su trabajo.

**Si alguien se atrasa:** no se espera. Oscar junta lo que esté listo, en el mismo orden; lo que falte pasa a la ronda siguiente. Lo **opcional se corta primero**: R6 y R7 (Karel), B3 (Blanco), G3 (Gustavo).
**Si dos ramas tocan el mismo archivo** (no debería pasar): lo resuelve Oscar y avisa a los dos.

### Oscar: lo que tienes que hacer

1. **Paso 0:** commit y push de la base.
2. **Pasos 2 y 4:** juntar las ramas en el orden de la tabla, con las pruebas y la app después de cada unión.
3. **Paso 6:** limpieza, resultados, README y documento.

Metaprompt para tu Claude (pégalo en Claude Code, dentro de la carpeta del proyecto):

```
Eres el Claude que ayuda a Oscar Vélez, integrador del proyecto final de Matemáticas Discretas
(MAT 4021, Uninorte). Lee primero equipo/cambio_a_obras.md (sobre todo las secciones 5, 6 y 9) y los
cuatro archivos personales de equipo/.

Tu trabajo es JUNTAR las ramas del equipo en main, en este orden, y comprobar que la app funciona:
  Paso 2: karel/refactor-obras (solo R1 y R2) -> lobo/grafico (solo L1) -> gustavo/apoyo (solo G2).
  Paso 4: karel/refactor-obras (R3 a R5) -> lobo/grafico (L2 a L6) -> gustavo/apoyo (G3 y G4).
  Paso 6: limpieza final.

Después de CADA unión:
  1. Corre python -m unittest (dentro de proyecto_arroyos/). Deben pasar todas.
  2. Corre python herramientas/plan_etapas.py y compara con resultados/linea_base/plan_etapas.txt:
     las cifras de El Salao NO deben cambiar. Luego git checkout -- proyecto_arroyos/resultados.
  3. Arranca python app.py y comprueba que POST /api/plan con El Salao responde 200 con 3 etapas y 9 pasos.
  Si algo falla, DETENTE: no sigas con la siguiente rama. Dime qué falló, de quién es el archivo y qué
  se le debe pedir a esa persona. No lo arregles tú si es un archivo ajeno.

Reglas: no hagas push a main sin que yo lo confirme; si hay conflicto, muéstramelo antes de resolverlo;
no borres datos; no inventes cifras ni fuentes.

Paso 6 (limpieza), solo cuando yo te lo pida: quitar lo que ya no se use (fuente.arroyos_osm,
lineas_por_nombre, las rutas /api/arroyos, la clave cauce, el alias Arroyo, --arroyo y --listar), mover
datos/arroyos_area_metropolitana.json a datos/archivo_arroyos/, regenerar resultados/ (main.py y
herramientas/plan_etapas.py), actualizar README.md y avisar qué secciones de documento/main.tex cambian de
tema. No edites main.tex: es de otra persona. Al terminar, resume qué se juntó, qué falló y qué falta.
```

## 10. Decisiones ya tomadas y lo que queda como está

- El Salao sigue como ejemplo principal.
- Por ahora los recorridos se miden **igual que hoy**. Cambiarlo es una mejora opcional de Karel (`medicion="afectados"`).
- La obra **cierra los puentes existentes** por defecto, como hoy. El parámetro `cerrar_puentes` permite cambiarlo, y la decisión final queda para después.
- Las esquinas a controlar y las esquinas aisladas junto a la avenida Murillo quedan **como están** y se revisan en la segunda ronda.
- **El documento y las diapositivas cambian de tema.** Las cifras de la simulación con lluvia siguen siendo válidas como «toda la obra a la vez», pero el centro del proyecto pasa a ser el plan por etapas.
