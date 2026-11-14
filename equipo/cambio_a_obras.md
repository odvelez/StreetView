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
- Los algoritmos y las **48 pruebas**, que deben seguir en verde.

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

## 4. Reparto: un relevo, una sola vez cada quien

El trabajo de código se hace **como un relevo en una sola línea** (la rama `obras`): trabaja una persona a la vez, termina, sube y le pasa la posta a la siguiente. Así no hay que juntar ramas ni resolver choques. **Gustavo trabaja aparte** (sus archivos son nuevos y no chocan con nadie).

| Turno | Persona | Qué hace | Archivos |
|---|---|---|---|
| **1** | **Karel Silva** | **Refactorización** (de arroyo a obra, sin cambiar cifras) **y todo lo que hace falta para que la app responda con el plan**: la ruta `/api/plan` | `src/`, `main.py`, `herramientas/plan_etapas.py`, `herramientas/experimentos.py`, `tests/` y, en `app.py`, **solo** la ruta `/api/plan` |
| **2** | **Santiago Lobo** | **Mejora gráfica**: menú, recorrido paso a paso, resultados y pantalla pequeña | `web/` y, si hace falta, `app.py` |
| **3** | **Sebastián Blanco** | **Probar, corregir y asegurar** la app ya terminada | lo que haga falta, avisando al dueño |
| **0 y 4** | **Oscar Vélez** | **Antes de Karel:** crea el ejemplo de obra que no es un arroyo. **Al final:** recibe la posta, escribe las pruebas de la API, junta lo de Gustavo, limpia lo viejo y deja la app lista | `herramientas/eje_de_calle.py`, `datos/ejemplos/`, `tests/test_app.py`, `README.md`, `resultados/`, `documento/` y lo compartido |
| aparte | **Gustavo de la Ossa** | **Diapositivas** (guion y figuras) y un poco de programación: las figuras para las diapositivas | `herramientas/figuras_plan.py`, `equipo/entregas/gustavo_*` (rama `gustavo/apoyo`) |

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

1. **Una sola persona toca el código a la vez.** El que tiene el turno trabaja en la rama `obras`; los demás esperan su turno (mientras tanto pueden leer, correr la app y preparar). La excepción es Gustavo, que solo crea archivos nuevos en su rama.
2. **La posta se pasa así:** (a) `python -m unittest` en verde; (b) commit y push a `obras`; (c) escribes tu nota de entrega `equipo/entregas/<tu_nombre>_entrega.md` (qué cambió, cómo se corre, qué falta, qué te preocupa); (d) avisas a la siguiente persona **y a Oscar**: «tu turno». La siguiente persona empieza con `git pull` y comprobando que las pruebas pasan.
3. **El JSON solo se agranda: agrega campos, no los quites ni los renombres.** Karel puede **agregar** `eje` junto a `cauce`; el nombre viejo lo quita Oscar al final.
4. **No se borra nada** de `datos/` ni funciones que otro archivo todavía use (por ejemplo `fuente.arroyos_osm` o `/api/arroyos`). Oscar limpia al final.
5. **Las 48 pruebas deben pasar** antes de cada commit (`python -m unittest`).
6. **No se inventan datos.** Sin fuente, queda como pendiente.
7. `main.py` y `plan_etapas.py` **sobrescriben `resultados/`**. Después de correrlos, `git checkout -- proyecto_arroyos/resultados`, salvo que Oscar pida regenerarlos.
8. **Nadie sube a `main`:** solo Oscar, al final.

## 7. Parámetros nuevos (los agrega Karel; los usa la pantalla después)

| Parámetro | Valor por defecto | Para qué |
|---|---|---|
| `ancho_m` | 10 | Ancho de la franja de obra. Con 10 m el resultado es **idéntico** al de hoy |
| `medicion` | `"lados"` | Cómo se miden los recorridos. `"lados"` es como hoy. `"afectados"` es una mejora opcional |

## 8. Formato de un archivo de obra

Para obras fuera de El Salao (lo hace Oscar y lo lee Karel):

```json
{"nombre": "Obra ilustrativa en la calle 72", "ilustrativo": true,
 "lineas": [[[10.9187, -74.7981], [10.9190, -74.7975]]]}
```

`lineas` es una lista de líneas, cada una una lista de puntos `[lat, lon]`. Si `ilustrativo` es `true`, la pantalla muestra «Ejemplo ilustrativo, no es una obra real».

## 9. Orden de trabajo (el relevo)

| Paso | Cuándo (aproximado) | Quién | Qué | Pasa la posta cuando |
|---|---|---|---|---|
| **0** | Hecho | Oscar | Subió la base a `main` | — |
| **0b** | **Hecho** | Oscar | Creó el ejemplo de obra que no es un arroyo (`herramientas/eje_de_calle.py` y `datos/ejemplos/obra_ilustrativa.json`: 600 m de la calle 72) y lo subió a `main` | Archivo en `main` |
| **1** | Sábado, desde la mañana | **Karel** | Crea la rama `obras` desde `main` (ya con el ejemplo de obra). Hace R1 a R6 (refactor y `/api/plan`) | Pruebas en verde, push y nota de entrega |
| **2** | Sábado, después de Karel | **Lobo** | `git pull` de `obras`. Hace la parte gráfica (L1 a L5) | Pruebas en verde, push y nota de entrega |
| **3** | Sábado en la noche, después de Lobo | **Blanco** | `git pull` de `obras`. Prueba, devuelve fallos y corrige (B1 a B4) | Pruebas en verde, push y nota de entrega |
| **4** | Domingo, mañana | **Oscar** | Escribe `tests/test_app.py` (pruebas de la API, incluida `/api/plan`), junta la rama de Gustavo en `obras`, hace la limpieza final, regenera resultados, README y documento, y pasa `obras` a `main` | App lista antes de las 18:00 |
| aparte | Todo el tiempo | **Gustavo** | G1 (esqueleto de diapositivas) primero; luego G2 (figuras) y G3 (capturas, cuando la pantalla esté lista) | Sube a `gustavo/apoyo` y avisa a Oscar |

**La hora no manda, manda el relevo:** cada quien empieza cuando le toca, no antes. Mientras esperas puedes leer el proyecto, correr la app y preparar; **no edites archivos del proyecto hasta tu turno.**

**Mínimo para pasar la posta (si el tiempo aprieta):**
- **Karel** puede entregar con R1, R2 y R6 hechos (la app responde con el plan y el código ya habla de obras). Lo demás (R3 a R5 y las opcionales) pasa a Oscar. Debe entregar **antes de la hora límite que Oscar le diga**, aunque no haya terminado todo.
- **Lobo** puede entregar con el menú y el recorrido paso a paso (L1 y L2).
- **Blanco** corta B3 (robustez) primero.

**Por qué este orden:** Karel va primero porque cambia los nombres y el código que todos usan, y deja el servidor listo. Lobo va después porque su pantalla necesita ese servidor ya terminado. Blanco va al final porque prueba lo que los otros ya terminaron. Oscar cierra porque quitar lo viejo mientras otros lo leen rompería su trabajo.

**Costo de este orden:** es más lento que trabajar en paralelo, porque Lobo y Blanco esperan. Los archivos de cada uno son distintos, así que si el tiempo se acaba se puede dejar que Lobo empiece antes (su pantalla no depende del código de Karel si usa `resultados/plan_etapas.json`). Esa decisión es de Oscar.

### Oscar: lo que tienes que hacer

1. **Paso 0b (hecho):** el ejemplo de obra ya está en `main`.
2. Avisar el orden al equipo y decirle a Karel su hora límite.
3. Estar atento a cada «tu turno» y confirmar que las pruebas pasan antes de que siga el siguiente.
4. **Paso 4:** escribir `tests/test_app.py`, juntar a Gustavo, limpiar y dejar la app lista.

Metaprompt para tu Claude (pégalo en Claude Code, dentro de la carpeta del proyecto):

```
Eres el Claude que ayuda a Oscar Vélez, integrador del proyecto final de Matemáticas Discretas
(MAT 4021, Uninorte). Lee primero equipo/cambio_a_obras.md (secciones 5, 6 y 9) y los cuatro archivos
personales de equipo/.

El trabajo de código es un RELEVO en la rama obras: Karel -> Lobo -> Blanco, uno a la vez. Gustavo trabaja
aparte en gustavo/apoyo (diapositivas y figuras). Tu trabajo es: (A) crear el ejemplo de obra antes del turno
de Karel, (B) VERIFICAR cada entrega y (C) cerrar.

(A) YA HECHO (el ejemplo de obra está en main). Solo repítelo si yo te lo pido:
  - Crea herramientas/eje_de_calle.py: dado --calle "Calle 72" --largo-m 600 --salida <archivo>, genera un
    archivo JSON {"nombre", "ilustrativo": true, "lineas": [[[lat, lon], ...]]} uniendo los tramos de esa
    calle (usa fuente.red_para(recuadro) y red.tramos: cada Tramo tiene via y forma) hasta el largo pedido.
  - Crea datos/ejemplos/obra_ilustrativa.json con el nombre "Obra ilustrativa en la calle 72: no es una obra
    real". Dibújalo con matplotlib para comprobarlo.
  - Corre python -m unittest, haz commit y, SOLO si yo lo confirmo, push a main.

Cuando yo te diga "entregó <persona>":
  1. git fetch y git checkout obras; git pull.
  2. python -m unittest (dentro de proyecto_arroyos/): deben pasar todas.
  3. python herramientas/plan_etapas.py y compara con resultados/linea_base/plan_etapas.txt: las cifras de
     El Salao NO deben cambiar. Luego git checkout -- proyecto_arroyos/resultados.
  4. python app.py y comprueba que POST /api/plan con El Salao responde 200 con 3 etapas y 9 pasos.
  5. Lee equipo/entregas/<persona>_entrega.md y dime qué cambió, qué falta y qué riesgos ves.
  Si algo falla, DETENTE: dime qué falló, de quién es el archivo y qué se le debe pedir. No lo arregles tú si
  es un archivo ajeno.

Cuando yo te diga "cierra" (paso 4): primero escribe tests/test_app.py con app.test_client() de Flask, sin
descargas reales (usa unittest.mock si hace falta): GET / da 200; GET /api/ejemplo trae lineas; POST
/api/analizar sin líneas da 400; POST /api/plan con El Salao da 200 con etapas, resumen y pasos, y con
parámetros fuera de rango da 400. Luego junta gustavo/apoyo en obras (archivos nuevos, no deberían chocar);
quita lo que ya no se use (fuente.arroyos_osm, lineas_por_nombre, las rutas /api/arroyos, la clave cauce, el
alias Arroyo, --arroyo y --listar); mueve datos/arroyos_area_metropolitana.json a datos/archivo_arroyos/;
regenera resultados/ (main.py y herramientas/plan_etapas.py); actualiza README.md; y dime qué secciones de
documento/main.tex cambian de tema (no edites main.tex: es de otra persona). Pasa obras a main SOLO si yo lo
confirmo.

Reglas: no hagas push a main sin mi confirmación; si hay conflicto, muéstramelo antes de resolverlo; no
borres datos; no inventes cifras ni fuentes. Al terminar, resume qué verificaste, qué falló y qué falta.
```

## 10. Decisiones ya tomadas y lo que queda como está

- El Salao sigue como ejemplo principal.
- Por ahora los recorridos se miden **igual que hoy**. Cambiarlo es una mejora opcional de Karel (`medicion="afectados"`).
- La obra **cierra los puentes existentes** por defecto, como hoy. El parámetro `cerrar_puentes` permite cambiarlo, y la decisión final queda para después.
- Las esquinas a controlar y las esquinas aisladas junto a la avenida Murillo quedan **como están** y se revisan en la segunda ronda.
- **El documento y las diapositivas cambian de tema.** Las cifras de la simulación con lluvia siguen siendo válidas como «toda la obra a la vez», pero el centro del proyecto pasa a ser el plan por etapas.
