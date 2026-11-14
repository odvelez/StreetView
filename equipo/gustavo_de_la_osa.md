# Gustavo de la Ossa: diapositivas y programación de apoyo

**Tu turno: empiezas YA, aparte del relevo.** Karel, Lobo y Blanco trabajan uno después de otro en la rama `obras`; tú no esperas a nadie. Tu trabajo son las **diapositivas** y dos programas: uno que dibuja las figuras que vas a usar en ellas y las pruebas de la API. Todo es en archivos **nuevos** y tuyos, en tu rama `gustavo/apoyo`.
1. **G1:** el esqueleto de las diapositivas (primero).
2. **G2:** las figuras (el programa que dibuja para tus diapositivas). Se pueden hacer en cualquier momento.
3. **G3:** las pruebas de la API. **Espera a que Karel entregue** (la ruta `/api/plan` estará en la rama `obras`); entonces trae sus cambios con `git fetch` y `git merge origin/obras` y escribe las pruebas.
4. **G4:** las capturas de la app, al final, cuando Lobo y Oscar avisen que la pantalla está lista.
4. Cuando termines cada cosa: commit y push a `gustavo/apoyo` y avisa a Oscar.

Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo y reglas).

## Lo que te toca

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **G1** | `equipo/entregas/gustavo_diapositivas.md`: guion de 10 minutos para 5 expositores con qué mostrar en cada parte y de dónde sale cada cifra: el problema (obras que cierran calles), la idea de las etapas, del mapa al grafo, el plan de El Salao, comparación, demostración, límites. **No uses «240 pares sin camino»** como dato del problema | Cada parte tiene qué mostrar y su fuente |
| **G2** | `herramientas/figuras_plan.py`: lee `resultados/plan_etapas.json` (solo lee, no recalcula) y guarda PNG en `resultados/figuras/`: **(1)** un mapa general con el eje de la obra en un color por etapa, los pasos peatonales en naranja, los cambios de sentido en morado y las esquinas a controlar en rojo si no tienen semáforo registrado; **(2)** un gráfico de barras con el desvío a pie con la obra frente a con los pasos, por etapa. Opcional: un mapa por etapa. Colores Okabe-Ito, leyenda y «© colaboradores de OpenStreetMap». Modelo: `main.py`, función `dibujar` | Genera las figuras y se ven bien en una diapositiva |
| **G3** | **Pruebas de la API:** `tests/test_app.py` con `app.test_client()` de Flask, sin descargas reales (si hace falta, simula con `unittest.mock`): `GET /` responde 200; `GET /api/ejemplo` trae `lineas`; `POST /api/analizar` sin líneas da 400 y con una zona demasiado grande también; `POST /api/plan` con El Salao da 200 con `etapas`, `resumen` y `pasos`, con parámetros fuera de rango da 400, y con Overpass simulado como caído da 503 | `python -m unittest` pasa con tus pruebas y todas las demás |
| **G4** | Capturas de la app (ventana de 1600 × 900, zoom 100 %): inicio, municipio, obra dibujada, ejemplo cargado, un paso por cada pantalla del recorrido, error y celular (390 × 844). PNG en `equipo/entregas/capturas/`. Una tanda borrador el sábado y una final el domingo | 15 capturas |

**Las diapositivas** tratan del nuevo tema: cómo hacer obras viales de la mejor forma, con El Salao como ejemplo. Motivación con respeto (4 de noviembre: sin nombres de víctimas ni decir qué ruta debieron tomar). Cifras de El Salao (de `resultados/plan_etapas.txt`): 2.386 m en **3 etapas**, **5 pasos peatonales**, 3 cambios de sentido, 18 rutas alternas. Límites que se dicen: no hay datos de tránsito (no se mide congestión), no se diseñan carriles ni semáforos, hay que verificar en terreno y se supone que la obra cierra los puentes existentes.

## Reglas

- **Tus archivos:** `herramientas/figuras_plan.py`, `resultados/figuras/`, `tests/test_app.py` y `equipo/entregas/gustavo_*`. **No toques** `src/`, `web/`, `app.py` ni las otras pruebas. Si tus pruebas encuentran un fallo en `app.py`, anótalo y avisa; no lo arregles.
- **No inventes datos:** ninguna cifra, fecha ni noticia sin fuente; si falta, «pendiente de fuente». No cambies cifras de los resultados.
- Si corres algo del proyecto: `git checkout -- proyecto_arroyos/resultados` (salvo `resultados/figuras`, que sí se sube).
- Rama `gustavo/apoyo`. Commits pequeños, uno por tarea, mensaje en español. **Commit y push al terminar cada tarea.**

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto.

```
Eres el Claude que ayuda a Gustavo de la Ossa en el proyecto final de Matemáticas Discretas (MAT 4021,
Uninorte). Lee primero: equipo/cambio_a_obras.md, proyecto_arroyos/README.md, resultados/plan_etapas.txt,
resultados/plan_etapas.json y main.py (función dibujar).

CONTEXTO: el proyecto pasa de "arroyos" a "hacer obras viales de la mejor forma" (una obra cierra calles; se
divide en etapas y se proponen medidas temporales). El Salao es el ejemplo principal. El trabajo de Gustavo
son las DIAPOSITIVAS, un programa de figuras y las pruebas de la API, en archivos NUEVOS y suyos: herramientas/figuras_plan.py, tests/test_app.py,
resultados/figuras/ y equipo/entregas/gustavo_*. NO toques src/, web/, app.py ni las otras pruebas.

TAREAS, en orden. Al terminar cada una: python -m unittest (deben pasar todas), commit con mensaje en español
y push a la rama gustavo/apoyo (créala con git checkout -b gustavo/apoyo). Si algo falla, DETENTE y dime qué
pasó.
  G1  equipo/entregas/gustavo_diapositivas.md: guion de 10 minutos para 5 expositores, con qué mostrar en
      cada parte y la fuente (archivo) de cada cifra. Cifras solo de resultados/plan_etapas.txt y
      resumen.txt. No uses "240 pares sin camino" como dato del problema. Motivación (4 de noviembre) con
      respeto, sin nombres de víctimas ni decir qué ruta debieron tomar; las fuentes del evento quedan
      "pendiente de fuente".
  G2  herramientas/figuras_plan.py: lee resultados/plan_etapas.json (solo lee) y guarda PNG en
      resultados/figuras/: (1) mapa general (eje por etapa en colores Okabe-Ito, pasos peatonales naranja,
      cambios de sentido morado, esquinas a controlar en rojo si semaforo es false); (2) gráfico de barras
      (desvío a pie con la obra vs con los pasos, por etapa). Opcional: un mapa por etapa. Leyenda y "©
      colaboradores de OpenStreetMap". Si un campo falta, sáltalo sin fallar. Usa main.py, función dibujar,
      como modelo.
  G3  Solo cuando yo te diga que Karel ya entregó (la ruta POST /api/plan estará en la rama obras): trae sus
      cambios con git fetch y git merge origin/obras, y escribe tests/test_app.py con app.test_client() de
      Flask, sin descargas reales (usa unittest.mock si hace falta): GET / da 200; GET /api/ejemplo trae
      lineas; POST /api/analizar sin líneas da 400 y con una zona demasiado grande también; POST /api/plan
      con El Salao da 200 con etapas, resumen y pasos, con parámetros fuera de rango da 400, y con
      osm.descargar simulado como caído da 503. Si una prueba descubre un fallo en app.py, NO lo arregles:
      anótalo en equipo/entregas/gustavo_hallazgos.md con qué hiciste, qué esperabas y qué pasó.
  G4  Solo si yo te lo pido: capturas de la app (ventana 1600x900) en equipo/entregas/capturas/.

REGLAS: no inventes datos ni cambies cifras. Después de correr cualquier programa del proyecto ejecuta
git checkout -- proyecto_arroyos/resultados (salvo resultados/figuras, que sí se sube). Al final de cada
tarea resume en 3 líneas qué hiciste y qué probaste.
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 48 pruebas
git checkout -b gustavo/apoyo
```
