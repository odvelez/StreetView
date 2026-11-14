# Gustavo de la Ossa: exposición y programación de apoyo

**Tu turno: empiezas YA**, en paralelo con Karel y Lobo (no se pisan: todo lo que programas son archivos **nuevos** y tuyos).
1. Haz primero **G2** (el ejemplo de obra), porque Karel lo necesita. Súbelo y **avisa a Oscar y a Karel**.
2. Después **G1** (esqueleto de diapositivas).
3. Cuando Oscar avise que juntó la ruta `/api/plan` de Lobo: **G4** (pruebas de la API). **G3** (figuras) puedes hacerla en cualquier momento.
4. **G5** (capturas) al final, cuando la pantalla de Lobo esté lista.

Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, formato del archivo de obra, reglas y orden de trabajo).

## Lo que te toca

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **G2** | `herramientas/eje_de_calle.py`: dado el nombre de una calle y un largo, genera un archivo de obra (formato de la sección 8 de `cambio_a_obras.md`). Úsalo para crear `datos/ejemplos/obra_ilustrativa.json` (por ejemplo 600 m de la calle 72). Lleva `"ilustrativo": true` y un nombre que diga que **no es una obra real** | El archivo existe y lo puedes dibujar |
| **G1** | `equipo/entregas/gustavo_diapositivas.md`: guion de 10 minutos con qué mostrar en cada parte y de dónde sale cada cifra (problema, la idea de las etapas, del mapa al grafo, el plan de El Salao, comparación, demostración, límites). **No uses «240 pares sin camino»** como dato del problema | Cada parte tiene qué mostrar y su fuente |
| **G4** | `tests/test_app.py` con `app.test_client()` de Flask, sin descargas reales: `/` responde 200; `/api/ejemplo` trae `lineas`; `/api/analizar` sin líneas da 400; cuando exista, `/api/plan` da 200 con `etapas`, `resumen` y `pasos` | `python -m unittest` pasa con tus pruebas y las 44 anteriores |
| **G3** | `herramientas/figuras_plan.py`: lee `resultados/plan_etapas.json` (solo lee) y guarda PNG en `resultados/figuras/`: mapa general (eje en color por etapa, pasos peatonales naranja, cambios de sentido morado, esquinas a controlar), un mapa por etapa y un gráfico de barras del desvío a pie con la obra frente a con los pasos. Colores Okabe-Ito, leyenda y «© colaboradores de OpenStreetMap». Modelo: `main.py`, función `dibujar` | Genera todas las figuras y se ven bien en una diapositiva |
| **G5** | Capturas de la app (ventana de 1600 × 900, zoom 100 %): inicio, municipio, obra dibujada, ejemplo cargado, un paso por cada pantalla del recorrido, error y celular (390 × 844). PNG en `equipo/entregas/capturas/`. Una tanda borrador el sábado y una final el domingo | 15 capturas |

**Las diapositivas** tratan del nuevo tema: cómo hacer obras viales de la mejor forma, con El Salao como ejemplo. Motivación con respeto (4 de noviembre: sin nombres de víctimas ni decir qué ruta debieron tomar). Cifras de El Salao: 2.386 m en **3 etapas**, **5 pasos peatonales**, 3 cambios de sentido, 18 rutas alternas (de `resultados/plan_etapas.txt`). Límites que se dicen: no hay datos de tránsito (no se mide congestión), no se diseñan carriles ni semáforos, hay que verificar en terreno y se supone que la obra cierra los puentes existentes.

## Reglas

- **Tus archivos:** `herramientas/figuras_plan.py`, `herramientas/eje_de_calle.py`, `datos/ejemplos/`, `tests/test_app.py` y `equipo/entregas/gustavo_*`. **No toques** `src/`, `web/`, `app.py` ni otras pruebas.
- **No inventes datos:** ninguna cifra, fecha ni noticia sin fuente; si falta, «pendiente de fuente». No cambies cifras de los resultados.
- **44 pruebas en verde** antes de cada commit.
- Rama `gustavo/apoyo`. Commits pequeños, uno por tarea, mensaje en español. **Commit y push al terminar cada tarea.**

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto.

```
Eres el Claude que ayuda a Gustavo de la Ossa en el proyecto final de Matemáticas Discretas (MAT 4021,
Uninorte). Lee primero: equipo/cambio_a_obras.md (sobre todo la sección 8, el formato del archivo de obra),
proyecto_arroyos/README.md, resultados/plan_etapas.txt, resultados/plan_etapas.json, main.py (función
dibujar) y src/fuente.py.

CONTEXTO: el proyecto pasa de "arroyos" a "hacer obras viales de la mejor forma" (una obra cierra calles; se
divide en etapas y se proponen medidas temporales). El Salao es el ejemplo principal. Tu trabajo son
archivos NUEVOS y tuyos: herramientas/figuras_plan.py, herramientas/eje_de_calle.py, datos/ejemplos/,
tests/test_app.py y equipo/entregas/gustavo_*. NO toques src/, web/, app.py ni otras pruebas.

TAREAS, en orden. Al terminar cada una: python -m unittest (deben pasar las 44 anteriores más las tuyas),
commit con mensaje en español y push a la rama gustavo/apoyo. Si algo falla, DETENTE y dime qué pasó.
  G2  herramientas/eje_de_calle.py: dado --calle "Calle 72" --largo-m 600 --salida <archivo>, genera un
      archivo JSON {"nombre", "ilustrativo": true, "lineas": [[[lat, lon], ...]]} uniendo los tramos de esa
      calle (usa fuente.red_para(recuadro) y red.tramos: cada Tramo tiene via y forma) hasta el largo pedido.
      Crea datos/ejemplos/obra_ilustrativa.json con el nombre "Obra ilustrativa en la calle 72: no es una
      obra real". Dibújalo con matplotlib para comprobarlo.
  G1  equipo/entregas/gustavo_diapositivas.md: guion de 10 minutos para 5 expositores, con qué mostrar en
      cada parte y la fuente (archivo) de cada cifra. Cifras solo de resultados/plan_etapas.txt y
      resumen.txt. No uses "240 pares sin camino" como dato del problema. Motivación (4 de noviembre) con
      respeto, sin nombres de víctimas ni decir qué ruta debieron tomar; las fuentes del evento quedan
      "pendiente de fuente".
  G4  tests/test_app.py con app.test_client() de Flask, sin descargas reales (usa unittest.mock si hace
      falta): GET / da 200; GET /api/ejemplo trae lineas; POST /api/analizar sin líneas da 400; y, cuando
      exista, POST /api/plan da 200 con etapas, resumen y pasos.
  G3  herramientas/figuras_plan.py: lee resultados/plan_etapas.json (solo lee) y guarda PNG en
      resultados/figuras/: mapa general (eje por etapa en colores Okabe-Ito, pasos peatonales naranja,
      cambios de sentido morado, esquinas a controlar en rojo si semaforo es false), un mapa por etapa y un
      gráfico de barras (desvío a pie con la obra vs con los pasos, por etapa). Leyenda y "© colaboradores de
      OpenStreetMap". Si un campo falta, sáltalo sin fallar.

REGLAS: no inventes datos ni cambies cifras. Después de correr cualquier programa del proyecto ejecuta
git checkout -- proyecto_arroyos/resultados (salvo resultados/figuras, que sí se sube). Al final de cada
tarea resume en 3 líneas qué hiciste y qué probaste.
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 44 pruebas
git checkout -b gustavo/apoyo
```
