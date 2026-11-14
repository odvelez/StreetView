# Karel Silva: refactorización y servidor del plan (turno 1)

**Tu turno: eres el PRIMERO.** Empiezas el sábado desde la mañana y trabajas **tú solo** en el código: Lobo y Blanco esperan a que termines.
1. Crea la rama compartida: `git checkout -b obras` y `git push -u origin obras`.
2. Haz todas las tareas, con commit y push al terminar cada una.
3. **Pasa la posta:** pruebas en verde, push, escribe `equipo/entregas/karel_entrega.md` (qué cambiaste, cómo se corre, qué falta, qué te preocupa) y avisa a **Lobo y a Oscar**: «tu turno».

**Hora límite:** Oscar te dirá una. Si llegas a ella sin haber terminado todo, **entrega con R1, R2 y R6 hechos** y con las pruebas en verde; lo demás pasa a Oscar.
Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, reglas, relevo).

## Lo que te toca

Dos cosas: (1) cambiar el código de «arroyo» a «obra» **sin cambiar ni una cifra**, y (2) dejar el servidor listo para que Lobo solo tenga que hacer la pantalla.

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **R1** | La clase `Arroyo` pasa a `Obra` (deja el alias `Arroyo = Obra`). Agrega el parámetro `ancho_m` (por defecto 10) a `clasificar`, `analizar` y `plan_por_etapas`, al final y con valor por defecto | Con `ancho_m = 10` pasan todas las pruebas y los resultados son idénticos |
| **R2** | Cambia los textos de `pasos_del_plan`, `main.py` y `plan_etapas.py`: nada de «arroyo», «cauce» ni «lluvia»; usa «obra», «eje de la obra», «toda la obra a la vez». **No quites ni renombres campos del JSON**; puedes **agregar** `eje` junto a `cauce` | Buscar esas palabras en `src/` solo encuentra El Salao, el alias, `fuente.arroyos_osm` y la clave `cauce` |
| **R6** | **Ruta `POST /api/plan` en `app.py`** (es lo único que tocas de ese archivo). Pedido y respuesta: sección 5 de `cambio_a_obras.md`. Mismas validaciones y errores (JSON, 400 y 503) que `/api/analizar`. Campos nuevos: `etapa_max_m` (300 a 2000, por defecto 1000), `un_puente_cada_m` (200 a 1000, por defecto 500), `cerrar_puentes` (booleano, por defecto `true`), `ancho_m` (10 a 60, por defecto 10). Llama a `plan_por_etapas(...)` y devuelve el diccionario más `tiempos`, `recuadro` y `fuente` | Con la app corriendo, El Salao devuelve 200 con 3 etapas y 9 pasos |
| **R3** | `fuente.lineas_de_archivo(ruta)` y la opción `--obra <archivo>` en `main.py` y `plan_etapas.py` (formato en la sección 8 de `cambio_a_obras.md`) | `plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json` funciona. El archivo lo crea Oscar y ya viene en `main` cuando creas la rama `obras`. Si por algo no está, haz uno propio de prueba y no lo subas |
| **R4** | Parámetro `medicion="lados"` (igual que hoy) en `plan_por_etapas`; otro valor falla con mensaje claro | Hay prueba |
| **R5** | Adapta los nombres en las pruebas y agrega: regresión de El Salao (mismos números que `resultados/linea_base/`), `ancho_m`, obra a lo largo de una calle (calcula el resultado **a mano** y escríbelo en un comentario), alias, `lineas_de_archivo` y `medicion` inválida | `python -m unittest` pasa todo (44 más las tuyas) |
| R7 (opcional) | `medicion="afectados"`: medir el conjunto fijo de recorridos que quedan más largos o sin camino con la obra. Cambia las cifras: tabla antes y después en `equipo/entregas/karel_afectados.md`, apagado por defecto | Tabla hecha |
| R8 (opcional) | Que los pasos peatonales «nuevos» crucen la franja casi perpendicular y no corten calles; pruebas en `tests/test_puentes.py` | Tabla antes y después |

**Orden recomendado:** R1, R2, R6 (el mínimo para pasar la posta), luego R3, R4, R5 y, si sobra tiempo, R7 y R8.

## Reglas

- **Tus archivos:** `src/`, `main.py`, `herramientas/plan_etapas.py`, `herramientas/experimentos.py`, `tests/` y, en `app.py`, solo la ruta `/api/plan`. **No toques** `web/`, `datos/`, `documento/`.
- **El JSON solo se agranda:** agrega campos, no quites ni renombres. No borres `fuente.arroyos_osm` ni mueves datos: Oscar limpia al final.
- Firmas de funciones: solo agrega parámetros **al final y con valor por defecto**.
- **44 pruebas en verde** antes de cada commit. No inventes datos.
- Rama `obras`. Commits pequeños, uno por tarea, con mensaje en español. **Commit y push al terminar cada tarea.**
- Después de correr `main.py` o `plan_etapas.py`: `git checkout -- proyecto_arroyos/resultados`.

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto.

```
Eres el Claude que ayuda a Karel Silva en el proyecto final de Matemáticas Discretas (MAT 4021, Uninorte).
Lee primero: equipo/cambio_a_obras.md (sobre todo secciones 5, 6, 8 y 9), proyecto_arroyos/src/geometria.py,
src/analisis.py (clasificar y analizar), src/etapas.py, src/fuente.py, app.py, main.py,
herramientas/plan_etapas.py, tests/ y resultados/linea_base/.

CONTEXTO: el proyecto pasa de "arroyos" a "hacer obras viales de la mejor forma" (una obra cierra calles; se
divide en etapas y se proponen medidas temporales). El Salao sigue como ejemplo principal. Eres el PRIMERO de
un relevo en la rama obras: tú trabajas solo en el código; después seguirán Lobo (pantalla) y Blanco
(pruebas). Tu tarea: (1) REFACTORIZAR el código para que hable de obras SIN CAMBIAR NINGUNA CIFRA y
(2) dejar listo el servidor (ruta /api/plan).

Antes de empezar: git checkout -b obras y git push -u origin obras.
Mapa de términos: arroyo/cauce -> obra/eje de la obra; clase Arroyo -> Obra; lluvia -> toda la obra a la vez;
puente peatonal temporal -> paso peatonal provisional.

TAREAS. Al terminar cada una: python -m unittest (deben pasar todas), commit con mensaje en español y push a
obras. Si una prueba falla o una cifra cambia, DETENTE y dime qué pasó. Orden: R1, R2, R6, R3, R4, R5.
  R1  Renombra la clase Arroyo a Obra (deja el alias Arroyo = Obra). Agrega ancho_m (por defecto 10, el valor
      de TOLERANCIA_M) a clasificar, analizar y plan_por_etapas, AL FINAL y con valor por defecto. Con
      ancho_m=10 los resultados deben ser idénticos.
  R2  Cambia los textos (pasos_del_plan, main.py, herramientas/plan_etapas.py): nada de "arroyo", "cauce" ni
      "lluvia". NO quites ni renombres campos del JSON; puedes AGREGAR "eje" junto a "cauce".
  R6  En app.py agrega POST /api/plan (es lo único que tocas de app.py), con las mismas validaciones y errores
      JSON (400, 503) que /api/analizar. Campos nuevos: etapa_max_m (300-2000, por defecto 1000),
      un_puente_cada_m (200-1000, por defecto 500), cerrar_puentes (booleano, por defecto true), ancho_m
      (10-60, por defecto 10). Llama a src.etapas.plan_por_etapas(red, lineas, radio=, luz_max=, etapa_max_m=,
      un_puente_cada_m=, abiertos=, cerrados=, recuadro=, cerrar_puentes=, ancho_m=) y devuelve el diccionario
      más tiempos, recuadro y fuente. Pruébalo con app.test_client() o arrancando python app.py: El Salao
      debe dar 200, 3 etapas y 9 pasos.
  R3  fuente.lineas_de_archivo(ruta) (formato en la sección 8 de cambio_a_obras.md) y la opción --obra
      <archivo> en main.py y plan_etapas.py. No borres --arroyo ni --listar (quedan obsoletos). El archivo de
      ejemplo (datos/ejemplos/obra_ilustrativa.json) lo crea Oscar y ya viene en main. Si por algo no está,
      haz uno propio de prueba y no lo subas.
  R4  Parámetro medicion="lados" (igual que hoy) en plan_por_etapas; otro valor falla con mensaje claro.
  R5  Adapta las pruebas y agrega: regresión de El Salao (mismos números que resultados/linea_base/),
      ancho_m (un ancho mayor cierra más o igual, nunca menos), obra a lo largo de una calle en el barrio
      miniatura (calcula el resultado esperado A MANO y escríbelo en un comentario), alias, lineas_de_archivo
      y medicion inválida.
  R7 y R8 son opcionales: solo si yo te lo pido.

REGLAS: solo editas src/, main.py, herramientas/plan_etapas.py, herramientas/experimentos.py, tests/ y, en
app.py, únicamente la ruta /api/plan. NO toques web/, datos/ ni documento/. El JSON solo se agranda. No
borres fuente.arroyos_osm ni muevas datos. Firmas: solo parámetros nuevos al final y con valor por defecto.
No inventes datos. Después de correr main.py o plan_etapas.py ejecuta git checkout --
proyecto_arroyos/resultados.
AL TERMINAR TODO (o si llega la hora límite con R1, R2 y R6 hechos): escribe equipo/entregas/karel_entrega.md
(qué cambiaste, cómo se corre, qué falta, qué te preocupa), haz commit y push, y dime "listo para pasar la
posta a Lobo". Al final de cada tarea resume en 3 líneas qué hiciste y qué pruebas pasaron.
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 44 pruebas
git checkout -b obras
git push -u origin obras
```
