# Santiago Lobo: mejora gráfica (turno 2)

**Tu turno: eres el SEGUNDO**, después de Karel. Karel deja listo el código y la ruta `/api/plan`; tú haces la pantalla, tú solo.
1. **Mientras esperas** puedes leer el proyecto, correr la app y bocetar en papel. **No edites archivos del proyecto hasta que Karel y Oscar te avisen «tu turno».**
2. Cuando te avisen: `git fetch`, `git checkout obras`, `git pull`, y `python -m unittest` debe pasar.
3. Haz las tareas, con commit y push a `obras` al terminar cada una.
4. **Pasa la posta:** pruebas en verde, push, escribe `equipo/entregas/lobo_entrega.md` (qué cambiaste, cómo se corre, qué falta, qué te preocupa) y avisa a **Blanco y a Oscar**: «tu turno».

**Mínimo para pasar la posta si el tiempo aprieta:** el menú y el recorrido paso a paso (L1 y L2).
Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, contrato del JSON, reglas, relevo).

## Lo que te toca

La app **planifica obras por etapas**. Tú haces que se vea y se use bien. Lo más importante es el **recorrido paso a paso**. La ruta `POST /api/plan` ya la hizo Karel; mientras no llegue tu turno, tienes una respuesta real en `resultados/plan_etapas.json`.

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **L1** | **Recorrido paso a paso.** Al pulsar «Planificar obra»: la página se desenfoca y oscurece; en el centro una tarjeta con la **cifra en grande** (`paso.cifra`, 96 px o más), su unidad, el título y el detalle; botones Anterior, Siguiente y Saltar (y teclas ← → Esc); «Paso 3 de 9»; el mapa se acerca a `paso.foco` y resalta solo las capas de `paso.capas`. Los pasos vienen en `plan.pasos`: no los inventes ni los reordenes | Ves los 9 pasos de El Salao en orden, con teclado y en 390 × 844 |
| **L2** | Menú de inicio en 3 pasos (elegir municipio, definir la obra, planificar). Quita la capa azul de arroyos y todo texto de «arroyo», «cauce» o «lluvia»: usa «obra», «Dibujar la obra», «Cargar ejemplo: obra de canalización de El Salao». Ajustes plegables: largo máximo de etapa, un paso peatonal cada tanto, y si la obra cierra los puentes existentes | Un compañero planifica una obra sin que le expliques |
| **L3** | Pantalla de resultados clara: cruce cerrado, ruta en carro y ruta a pie distinguibles; cifras principales juntas; enlace a Street View; mostrar `avisos` | Se entiende de un vistazo |
| **L4** | Escritorio y pantalla pequeña (panel inferior en 700 px o menos, botones de 48 px, sin desplazamiento horizontal) | Se ve bien en 1920×1080, 1366×768 y 390×844 |
| **L5** | Lista de comprobación en `equipo/entregas/lobo_checklist.md` (los 9 pasos, teclado, cambio de etapas, error del servidor, consola sin errores rojos) | Llena |

**Qué dibuja cada capa de un paso:** `etapas` el eje en tramos de colores (`etapas[].cauce`, o `eje` si existe); `puentes` marcadores naranja (`peatones.puentes[].forma`); `sentidos` calle morada (`vehiculos.medidas[].forma`); `rutas` carro amarilla y a pie verde punteada (`rutas[]`); `carga` círculos en `carga[].posicion`, rojo si `semaforo` es `false`, verde si `true`, gris si `null`. Colores de etapas aptos para daltonismo (Okabe-Ito: `#0072B2`, `#E69F00`, `#009E73`, `#CC79A7`, `#56B4E9`, `#D55E00`).

## Reglas

- **Tus archivos:** `web/` y, si hace falta un ajuste, `app.py` (avisa a Oscar). **No toques** `src/`, `tests/`, `datos/`, `resultados/`.
- **No uses** `/api/arroyos` ni `lineas_por_nombre`: la ruta queda en `app.py` hasta que Oscar la quite.
- Lo que recibes del servidor puede cambiar solo agregando campos: si falta uno, no te rompas. `peatones` o `vehiculos` pueden ser `null`.
- **48 pruebas de Python en verde** antes de cada commit. No inventes datos. Cargas externas solo con versión exacta (Leaflet 1.9.4).
- Rama `obras`. Commits pequeños, uno por tarea, mensaje en español. **Commit y push al terminar cada tarea.** No cambies los `id` ni la estructura de pantallas después del sábado: Gustavo toma capturas.

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto, **solo cuando Karel y Oscar te hayan avisado «tu turno»**.

```
Eres el Claude que ayuda a Santiago Lobo en el proyecto final de Matemáticas Discretas (MAT 4021, Uninorte).
Lee primero: equipo/cambio_a_obras.md (sobre todo la sección 5, el contrato, y la 6), equipo/entregas/
karel_entrega.md (lo que dejó Karel), proyecto_arroyos/app.py (la ruta /api/plan ya existe), web/index.html,
web/app.js, web/estilos.css, src/etapas.py (solo lectura) y resultados/plan_etapas.json (una respuesta real
de El Salao: 3 etapas, 9 pasos).

CONTEXTO: la app pasa de "arroyos" a "planificar obras viales por etapas". Eres el SEGUNDO de un relevo en la
rama obras (Karel ya terminó; después seguirá Blanco). Tu trabajo es la parte GRÁFICA. Eres dueño de web/. No
toques src/, tests/, datos/ ni resultados/. Antes de empezar: git checkout obras, git pull y python -m
unittest (deben pasar todas).

TAREAS, en orden. Al terminar cada una: python -m unittest, commit con mensaje en español y push a obras. Si
algo falla, DETENTE y dime qué pasó.
  L1  RECORRIDO PASO A PASO (lo más importante). Al pulsar "Planificar obra" la página llama a POST /api/plan
      y muestra el resultado de a un paso: desenfoca y oscurece el resto de la página (filter: blur(3px)
      opacity(.45)); en el centro una tarjeta con la cifra en grande (paso.cifra, 96 px o más), paso.unidad,
      paso.titulo y paso.detalle; botones Anterior, Siguiente y Saltar recorrido, teclas flechas y Esc,
      indicador "Paso 3 de 9"; el mapa se acerca a paso.foco (fitBounds) y resalta SOLO las capas de
      paso.capas (lo demás con opacidad 0.2). Al terminar queda la vista normal con la lista de etapas y un
      botón para repetir. Usa plan.pasos tal cual: no los inventes ni reordenes. Capas: etapas = eje en
      tramos de colores (etapas[].cauce, o eje si existe); puentes = marcadores naranja
      (peatones.puentes[].forma); sentidos = calle morada (vehiculos.medidas[].forma); rutas = carro amarilla
      y a pie verde punteada (rutas[]); carga = círculos en carga[].posicion (rojo si semaforo es false, verde
      si true, gris si null). Colores Okabe-Ito para etapas. Maneja peatones o vehiculos en null (muestra
      etapas[].avisos).
  L2  Menú de inicio en 3 pasos (municipio, definir la obra, planificar). Quita la capa azul de arroyos y todo
      texto de "arroyo", "cauce" o "lluvia" (usa "obra", "Dibujar la obra", "Cargar ejemplo: obra de
      canalización de El Salao"). Ajustes plegables: largo máximo de etapa (500, 700, 1000, 1500; por defecto
      1000), un paso peatonal cada (250, 500, 750; por defecto 500), y si la obra cierra los puentes existentes.
      NO uses /api/arroyos ni lineas_por_nombre.
  L3  Pantalla de resultados clara, con enlace a Street View y avisos.
  L4  Escritorio y pantalla pequeña (390x844), botones de 48 px, sin scroll horizontal.
  L5  equipo/entregas/lobo_checklist.md con la lista de comprobación y su resultado.

REGLAS: el JSON puede cambiar solo agregando campos: si falta uno, no te rompas. No inventes datos. Cargas
externas solo con versión exacta. AL TERMINAR (o si el tiempo aprieta, con L1 y L2 hechos): escribe
equipo/entregas/lobo_entrega.md (qué cambiaste, cómo se corre, qué falta, qué te preocupa), haz commit y push,
y dime "listo para pasar la posta a Blanco". Al final de cada tarea resume en 3 líneas qué hiciste y probaste.
```

## Cómo empezar (cuando sea tu turno)

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
git checkout obras
git pull
python -m unittest          # deben pasar todas
python app.py               # http://localhost:5000
```
