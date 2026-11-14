# Karel Silva: refactorización (de arroyo a obra)

**Tu turno: empiezas YA**, en paralelo con Lobo y Gustavo (no se pisan: cada quien toca archivos distintos).
1. Haz **R1 y R2**, súbelos (commit y push a tu rama) y **avisa a Oscar**: él los junta en `main` antes de que sigas.
2. Cuando Oscar avise, haz `git pull` de `main` y sigue con **R3 a R5**.
3. R6 y R7 son opcionales: solo si lo demás está listo.

Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, reglas y orden de trabajo).

## Lo que te toca

El proyecto pasa de «arroyos» a «hacer obras viales de la mejor forma». Tú cambias el código para que hable de **obras** y **no cambias ni una cifra**: El Salao, tratado como obra, debe dar los mismos resultados que hoy.

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **R1** | La clase `Arroyo` pasa a `Obra` (deja el alias `Arroyo = Obra`). Agrega el parámetro `ancho_m` (por defecto 10) a `clasificar`, `analizar` y `plan_por_etapas`, al final y con valor por defecto | Con `ancho_m = 10` pasan todas las pruebas y los resultados son idénticos |
| **R2** | Cambia los textos de `pasos_del_plan`, `main.py` y `plan_etapas.py`: nada de «arroyo», «cauce» ni «lluvia»; usa «obra», «eje de la obra», «toda la obra a la vez». **No quites ni renombres campos del JSON**; puedes **agregar** `eje` junto a `cauce` | Buscar esas palabras en `src/` solo encuentra El Salao, el alias, `fuente.arroyos_osm` y la clave `cauce` |
| **R3** | `fuente.lineas_de_archivo(ruta)` y la opción `--obra <archivo>` en `main.py` y `plan_etapas.py`. El formato está en la sección 8 de `cambio_a_obras.md` | `plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json` funciona (el archivo lo hace Gustavo; mientras tanto haz uno propio y no lo subas) |
| **R4** | Parámetro `medicion="lados"` (igual que hoy) en `plan_por_etapas`; cualquier otro valor falla con mensaje claro | Hay prueba |
| **R5** | Adapta los nombres en las pruebas y agrega: regresión de El Salao (mismos números que `resultados/linea_base/`), `ancho_m`, obra a lo largo de una calle (calcula el resultado **a mano** y escríbelo en un comentario), alias, `lineas_de_archivo` y `medicion` inválida | `python -m unittest` pasa todo (44 más las tuyas) |
| R6 (opcional) | `medicion="afectados"`: medir el conjunto fijo de recorridos que quedan más largos o sin camino con la obra. Cambia las cifras: tabla antes y después en `equipo/entregas/karel_afectados.md`, apagado por defecto | Tabla hecha |
| R7 (opcional) | Que los pasos peatonales «nuevos» crucen la franja casi perpendicular y no corten calles; pruebas en `tests/test_puentes.py` | Tabla antes y después |

## Reglas

- **Tus archivos:** `src/`, `main.py`, `herramientas/plan_etapas.py`, `herramientas/experimentos.py`, `tests/`. **No toques** `web/`, `app.py`, `datos/`, `documento/`.
- **El JSON solo se agranda:** agrega campos, no quites ni renombres. No borres `fuente.arroyos_osm` ni mueves datos: Oscar limpia al final.
- Firmas de funciones: solo agrega parámetros **al final y con valor por defecto**.
- **44 pruebas en verde** antes de cada commit. No inventes datos.
- Rama `karel/refactor-obras`. Commits pequeños, uno por tarea, con mensaje en español. **Commit y push al terminar cada tarea.**
- Después de correr `main.py` o `plan_etapas.py`: `git checkout -- proyecto_arroyos/resultados`.

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto.

```
Eres el Claude que ayuda a Karel Silva en el proyecto final de Matemáticas Discretas (MAT 4021, Uninorte).
Lee primero: equipo/cambio_a_obras.md, proyecto_arroyos/src/geometria.py, src/analisis.py (clasificar y
analizar), src/etapas.py, src/fuente.py, main.py, herramientas/plan_etapas.py, tests/ y
resultados/linea_base/.

CONTEXTO: el proyecto pasa de "arroyos" a "hacer obras viales de la mejor forma" (una obra cierra calles;
se divide en etapas y se proponen medidas temporales). El Salao sigue como ejemplo principal. Tu tarea es
REFACTORIZAR el código Python para que hable de obras, SIN CAMBIAR NINGUNA CIFRA.

Mapa de términos: arroyo/cauce -> obra/eje de la obra; clase Arroyo -> Obra; lluvia -> toda la obra a la
vez; puente peatonal temporal -> paso peatonal provisional.

TAREAS, en orden. Al terminar cada una: python -m unittest (deben pasar todas), commit con mensaje claro
en español y push a la rama karel/refactor-obras. Si una prueba falla o una cifra cambia, DETENTE y dime qué
pasó. Después de R2 detente y espera a que yo te avise que Oscar juntó tu rama; luego sigue con R3.
  R1  Renombra la clase Arroyo a Obra (deja el alias Arroyo = Obra). Agrega el parámetro ancho_m (por
      defecto 10, el valor de TOLERANCIA_M) a clasificar, analizar y plan_por_etapas, AL FINAL y con valor
      por defecto. Con ancho_m=10 los resultados deben ser idénticos.
  R2  Cambia los textos (pasos_del_plan, main.py, herramientas/plan_etapas.py): nada de "arroyo", "cauce" ni
      "lluvia". NO quites ni renombres campos del JSON; puedes AGREGAR "eje" junto a "cauce".
  R3  fuente.lineas_de_archivo(ruta) (formato en la sección 8 de cambio_a_obras.md) y la opción --obra
      <archivo> en main.py y plan_etapas.py. No borres --arroyo ni --listar (quedan obsoletos).
  R4  Parámetro medicion="lados" (igual que hoy) en plan_por_etapas; otro valor falla con mensaje claro.
  R5  Adapta las pruebas y agrega: regresión de El Salao (mismos números que resultados/linea_base/),
      ancho_m (un ancho mayor cierra más o igual, nunca menos), obra a lo largo de una calle en el barrio
      miniatura (calcula el resultado esperado A MANO y escríbelo en un comentario), alias, lineas_de_archivo
      y medicion inválida.
  R6 y R7 son opcionales: solo si yo te lo pido.

REGLAS: solo editas src/, main.py, herramientas/plan_etapas.py, herramientas/experimentos.py y tests/.
NO toques web/, app.py, datos/ ni documento/. El JSON solo se agranda. No borres fuente.arroyos_osm ni
muevas datos. Firmas: solo parámetros nuevos al final y con valor por defecto. No inventes datos. Después de
correr main.py o plan_etapas.py ejecuta git checkout -- proyecto_arroyos/resultados.
Al final de cada tarea resume en 3 líneas qué hiciste y qué pruebas pasaron.
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 44 pruebas
git checkout -b karel/refactor-obras
```
