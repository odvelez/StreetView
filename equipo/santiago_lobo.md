# Santiago Lobo: mejora gráfica

**Tu turno: empiezas YA**, en paralelo con Karel y Gustavo (no se pisan: tú tocas `web/` y `app.py`).
1. Haz **L1** (la ruta `/api/plan`), súbela (commit y push a tu rama) y **avisa a Oscar**: él la junta en `main` antes de que sigas.
2. Mientras tanto puedes avanzar L2 y L3 con el archivo `resultados/plan_etapas.json`, que es una respuesta real de El Salao.
3. Cuando Oscar avise, `git pull` de `main` y sigue con **L2 a L6**.

Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, contrato del JSON, reglas y orden de trabajo).

## Lo que te toca

La app ahora **planifica obras por etapas**. Tú haces que se vea y se use bien. Lo más importante es el **recorrido paso a paso**.

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **L1** | En `app.py`, la ruta `POST /api/plan` (pedido y respuesta en la sección 5 de `cambio_a_obras.md`). Mismas validaciones y errores que `/api/analizar`; campos nuevos `etapa_max_m` (300 a 2000, por defecto 1000), `un_puente_cada_m` (200 a 1000, por defecto 500) y `cerrar_puentes` (por defecto `true`). Llama a `plan_por_etapas(...)` de `src.etapas` y devuelve el diccionario más `tiempos`, `recuadro` y `fuente` | Con la app corriendo, El Salao devuelve 200 con 3 etapas y 9 pasos |
| **L2** | **Recorrido paso a paso.** Al pulsar «Planificar obra»: la página se desenfoca y oscurece; en el centro una tarjeta con la **cifra en grande** (`paso.cifra`, 96 px o más), su unidad, el título y el detalle; botones Anterior, Siguiente y Saltar (y teclas ← → Esc); «Paso 3 de 9»; el mapa se acerca a `paso.foco` y resalta solo las capas de `paso.capas`. Los pasos vienen en `plan.pasos`: no los inventes | Ves los 9 pasos de El Salao en orden, con teclado y en 390 × 844 |
| **L3** | Menú de inicio en 3 pasos (elegir municipio, definir la obra, planificar). Quita la capa azul de arroyos y todo texto de «arroyo», «cauce» o «lluvia»: usa «obra», «Dibujar la obra», «Cargar ejemplo: obra de canalización de El Salao». Ajustes plegables: largo máximo de etapa, un paso peatonal cada tanto, y si la obra cierra los puentes existentes | Un compañero planifica una obra sin que le expliques |
| **L4** | Pantalla de resultados clara: cruce cerrado, ruta en carro y ruta a pie distinguibles; cifras principales juntas; enlace a Street View; mostrar `avisos` | Se entiende de un vistazo |
| **L5** | Escritorio y pantalla pequeña (panel inferior en 700 px o menos, botones de 44 px, sin desplazamiento horizontal) | Se ve bien en 1920×1080, 1366×768 y 390×844 |
| **L6** | Lista de comprobación en `equipo/entregas/lobo_checklist.md` (los 9 pasos, teclado, cambio de etapas, error del servidor, consola sin errores rojos) | Llena |

**Qué dibuja cada capa de un paso:** `etapas` el eje en tramos de colores (`etapas[].cauce`, o `eje` si existe); `puentes` marcadores naranja (`peatones.puentes[].forma`); `sentidos` calle morada (`vehiculos.medidas[].forma`); `rutas` carro amarilla y a pie verde punteada (`rutas[]`); `carga` círculos en `carga[].posicion`, rojo si `semaforo` es `false`, verde si `true`, gris si `null`. Colores de etapas aptos para daltonismo (Okabe-Ito: `#0072B2`, `#E69F00`, `#009E73`, `#CC79A7`, `#56B4E9`, `#D55E00`).

## Reglas

- **Tus archivos:** `web/` y `app.py`. **No toques** `src/`, `tests/`, `datos/`, `resultados/`.
- **No uses** `/api/arroyos` ni `lineas_por_nombre`: la ruta queda en `app.py` hasta que Oscar la quite.
- Lo que recibes del servidor puede cambiar solo agregando campos: si falta uno, no te rompas. `peatones` o `vehiculos` pueden ser `null`.
- **44 pruebas de Python en verde** antes de cada commit. No inventes datos. Cargas externas solo con versión exacta (Leaflet 1.9.4).
- Rama `lobo/grafico`. Commits pequeños, uno por tarea, mensaje en español. **Commit y push al terminar cada tarea.** No cambies los `id` ni la estructura de pantallas después del sábado: Gustavo toma capturas.

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto.

```
Eres el Claude que ayuda a Santiago Lobo en el proyecto final de Matemáticas Discretas (MAT 4021, Uninorte).
Lee primero: equipo/cambio_a_obras.md (sobre todo la sección 5, el contrato), proyecto_arroyos/app.py,
web/index.html, web/app.js, web/estilos.css, src/etapas.py (solo lectura) y resultados/plan_etapas.json
(una respuesta real de El Salao: 3 etapas, 9 pasos).

CONTEXTO: la app pasa de "arroyos" a "planificar obras viales por etapas". Tu trabajo es la parte GRÁFICA y la
ruta POST /api/plan. Eres dueño de web/ y app.py. No toques src/, tests/, datos/ ni resultados/.

TAREAS, en orden. Al terminar cada una: python -m unittest (deben pasar todas), commit con mensaje en español y
push a la rama lobo/grafico. Si algo falla, DETENTE y dime qué pasó. Después de L1 detente y avísame.
  L1  En app.py agrega POST /api/plan con las mismas validaciones y errores (JSON) que /api/analizar. Campos
      nuevos: etapa_max_m (300-2000, por defecto 1000), un_puente_cada_m (200-1000, por defecto 500),
      cerrar_puentes (booleano, por defecto true). Llama a src.etapas.plan_por_etapas(red, lineas, radio=,
      luz_max=, etapa_max_m=, un_puente_cada_m=, abiertos=, cerrados=, recuadro=, cerrar_puentes=) SIN
      modificarla y devuelve el diccionario más tiempos, recuadro y fuente. Prueba con El Salao: 200, 3 etapas.
  L2  RECORRIDO PASO A PASO (lo más importante). Al pulsar "Planificar obra": desenfoca y oscurece el resto de
      la página (filter: blur(3px) opacity(.45)); en el centro una tarjeta con la cifra en grande
      (paso.cifra, 96 px o más), paso.unidad, paso.titulo y paso.detalle; botones Anterior, Siguiente y Saltar
      recorrido, teclas flechas y Esc, indicador "Paso 3 de 9"; el mapa se acerca a paso.foco (fitBounds) y
      resalta SOLO las capas de paso.capas (lo demás con opacidad 0.2). Al terminar queda la vista normal con
      la lista de etapas y un botón para repetir. Usa plan.pasos tal cual: no los inventes ni reordenes.
      Capas: etapas = eje en tramos de colores (etapas[].cauce, o eje si existe); puentes = marcadores
      naranja (peatones.puentes[].forma); sentidos = calle morada (vehiculos.medidas[].forma); rutas = carro
      amarilla y a pie verde punteada (rutas[]); carga = círculos en carga[].posicion (rojo si semaforo es
      false, verde si true, gris si null). Colores Okabe-Ito para etapas. Maneja peatones o vehiculos en null
      (muestra etapas[].avisos).
  L3  Menú de inicio en 3 pasos (municipio, definir la obra, planificar). Quita la capa azul de arroyos y todo
      texto de "arroyo", "cauce" o "lluvia" (usa "obra", "Dibujar la obra", "Cargar ejemplo: obra de
      canalización de El Salao"). Ajustes plegables: largo máximo de etapa (500, 700, 1000, 1500; por defecto
      1000), un paso peatonal cada (250, 500, 750; por defecto 500), y si la obra cierra los puentes existentes.
      NO uses /api/arroyos ni lineas_por_nombre.
  L4  Pantalla de resultados clara, con enlace a Street View y avisos.
  L5  Escritorio y pantalla pequeña (390x844), botones de 44 px, sin scroll horizontal.
  L6  equipo/entregas/lobo_checklist.md con la lista de comprobación y su resultado.

REGLAS: el JSON puede cambiar solo agregando campos: si falta uno, no te rompas. No inventes datos. Cargas
externas solo con versión exacta. Al final de cada tarea resume en 3 líneas qué hiciste y qué probaste.
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 44 pruebas
python app.py               # http://localhost:5000
git checkout -b lobo/grafico
```
