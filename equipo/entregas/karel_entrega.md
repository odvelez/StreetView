# Entrega de Karel (turno 1): refactor a obras y ruta `/api/plan`

**Estado:** R1, R2, R3, R4, R5 y R6 hechas. R7 y R8 (opcionales) no se hicieron.
**Pruebas:** `python -m unittest` → **63 en verde** (las 48 de antes y 15 nuevas en `tests/test_obras.py`).
**Cifras de El Salao:** idénticas a `resultados/linea_base/` (lo comprueba una prueba automática; solo cambian los textos).

## Qué cambié

| Tarea | Qué se hizo | Archivos |
|---|---|---|
| R1 | La clase `Arroyo` pasa a `Obra` (queda el alias `Arroyo = Obra`). Parámetro nuevo `ancho_m` (por defecto 10 = `TOLERANCIA_M`), al final y con valor por defecto, en `clasificar`, `zona`, `analizar` y `plan_por_etapas`. | `src/geometria.py`, `src/analisis.py`, `src/etapas.py` |
| R2 | Textos y nombres internos de «arroyo/cauce/lluvia» pasan a «obra/eje de la obra/toda la obra a la vez»; «puente peatonal temporal» pasa a «paso peatonal provisional». **No se quitó ni renombró ningún campo del JSON.** Se **agregaron** `obra` (igual a `arroyo`) en el plan y `eje` (igual a `cauce`) en cada etapa. | `src/*.py`, `main.py`, `herramientas/plan_etapas.py` |
| R3 | `fuente.leer_obra(ruta)` → `{nombre, ilustrativo, lineas}` y `fuente.lineas_de_archivo(ruta)` → líneas (formato de la sección 8). Si el archivo está mal, lanza `ValueError` con un mensaje claro. Opción `--obra <archivo>` en `main.py` y en `plan_etapas.py`. `--arroyo` y `--listar` siguen ahí, marcadas como obsoletas. | `src/fuente.py`, `main.py`, `herramientas/plan_etapas.py` |
| R4 | `plan_por_etapas(..., medicion="lados")`. Cualquier otro valor da `ValueError: medicion='afectados' no existe. Use una de: lados.` También está la opción `--medicion` en `plan_etapas.py`. | `src/etapas.py` |
| R5 | Las pruebas usan los nombres nuevos (`Obra`, `obra`). Pruebas nuevas: regresión de El Salao (plan y análisis contra `linea_base/`), `ancho_m` (más ancho cierra lo mismo o más; umbral de 55/56 m calculado a mano), obra a lo largo de la Carrera 1 del barrio miniatura (calculada a mano en el comentario), alias, `lineas_de_archivo` (bueno, ejemplo de la calle 72 y 6 archivos malos), textos sin «arroyo» y `medicion` inválida. | `tests/` |
| R6 | `POST /api/plan` (lo único nuevo en `app.py`). Campos nuevos: `etapa_max_m` (300–2000, 1000), `un_puente_cada_m` (200–1000, 500), `cerrar_puentes` (booleano, `true`), `ancho_m` (10–60, 10) y, opcional, `medicion` (`"lados"`). Errores en JSON: 400 (pedido inválido o zona muy grande) y 503 (no se pudo descargar el mapa). Devuelve el plan más `tiempos`, `recuadro` y `fuente`. | `app.py` |

Además, en `herramientas/experimentos.py` solo se cambió `ctx["arroyo"]` por `ctx["obra"]`; el experimento de control da lo mismo que antes.

## Cómo se corre

Todo desde `proyecto_arroyos/`. El primer comando corre las pruebas (tarda unos 16 s por la regresión de El Salao):

```bash
python -m unittest
```

```bash
python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json
```

```bash
python app.py
```

Con la app corriendo, `POST http://localhost:5000/api/plan` con `{"lineas": <El Salao>}` responde **200, 3 etapas y 9 pasos**, y la respuesta es igual a `resultados/linea_base/plan_etapas.json` (solo cambian los textos de los pasos y se agregan campos).

Después de correr `main.py` o `plan_etapas.py`: `git checkout -- proyecto_arroyos/resultados`.

## Para Lobo (pantalla)

- La pantalla puede pedir `POST /api/plan`. El contrato es el de la sección 5, sin cambios. Además llegan `obra`, `etapas[].eje` y `parametros.ancho_m` / `parametros.medicion`.
- Un archivo de obra con `"ilustrativo": true` lo lee `fuente.leer_obra`. La pantalla debe mostrar «Ejemplo ilustrativo, no es una obra real». Todavía no hay una ruta `GET` para el ejemplo de la calle 72 (no la pedía R6).

## Qué falta

- R7 (`medicion="afectados"`) y R8 (pasos peatonales casi perpendiculares): opcionales, no hechas.
- La limpieza final (es de Oscar): `fuente.arroyos_osm`, `lineas_por_nombre`, `/api/arroyos`, la clave `cauce`, el alias `Arroyo`, el alias `recorte_del_cauce`, `--arroyo` y `--listar`.

## Qué me preocupa

1. **Qué significa `ancho_m`.** Hice lo que pide la tabla: `ancho_m` reemplaza a `TOLERANCIA_M`, así que con 10 da lo mismo que hoy. Pero se mide **desde el eje hacia cada lado**: con `ancho_m = 10`, la franja real mide 20 m de borde a borde. Si el equipo entiende «ancho» como el total, hay que decidirlo antes de que la pantalla lo muestre.
2. **Palabras que siguen en `src/`.** Quedan «arroyo», «cauce» y «lluvia», pero solo como claves del JSON (`arroyo`, `cauce`, `lluvia`, `lluvia_m`), claves de `contexto` que usan los experimentos y las pruebas, los alias, el modo `"lluvia"` de `control_de_lados`, `arroyos_osm`/`lineas_por_nombre`, el archivo `arroyo_el_salao.csv` y el `User-Agent` de `osm.py`. Quitarlas rompería el contrato; es parte de la limpieza.
3. **`resultados/linea_base/analisis.json` es anterior a las «mejoras matemáticas»:** no tiene `desvio_fijo_m` ni `recuperados`. La prueba compara solo los campos que sí tiene (todos iguales).
4. **Las pruebas ahora tardan unos 16 s** (antes 0,02 s) y usan la red real de `datos/cache/`. Si eso molesta, se puede separar la regresión.
5. **Ejemplo de la calle 72:** entre las rutas alternas aparecen «Calle 47» y «Carrera 18 Sur». Puede ser cómo están los nombres en OpenStreetMap; conviene que Oscar lo mire antes de mostrarlo.
6. Cambiaron los **textos** de `pasos[]` y de los informes. Si Gustavo compara textos en `tests/test_app.py`, debe usar los nuevos.
7. En el informe de `plan_etapas.py` sigue apareciendo «1 etapas» y «1 pasos peatonales»: ya pasaba antes con «1 puentes». No lo cambié.
