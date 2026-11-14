# Sebastián Blanco: segunda ronda (probar, corregir y asegurar)

**Tu turno: eres el TERCERO.** Karel va primero, Lobo después, y tú al final, tú solo. **Lobo y Oscar te avisan «tu turno»** (sábado en la noche).
1. **Mientras esperas** solo te preparas: lee el proyecto, corre la app y escribe tu plan de pruebas en `equipo/entregas/blanco_plan_de_pruebas.md`. **No edites archivos del proyecto hasta tu turno.**
2. Cuando te avisen: `git fetch`, `git checkout obras`, `git pull`, y `python -m unittest` debe pasar.
3. Haz las tareas, con commit y push a `obras` al terminar cada una.
4. **Pasa la posta:** pruebas en verde, push, escribe `equipo/entregas/blanco_entrega.md` (qué probaste, qué corregiste, qué falta, qué te preocupa) y avisa a **Oscar**: «tu turno».

Lee antes, 5 minutos: [cambio_a_obras.md](cambio_a_obras.md) (objetivo, reglas y orden de trabajo).

## Lo que te toca (cuando sea tu turno)

| Tarea | Qué haces | Terminado cuando |
|---|---|---|
| **B1** | **Probar la app integrada** con esta lista: todas las pruebas pasan; El Salao da el mismo plan que `resultados/linea_base/plan_etapas.txt`; planificar una obra dibujada; planificar con `--obra` (el ejemplo de obra de Oscar); el recorrido muestra todos los pasos; ninguna palabra de arroyo, cauce o lluvia en pantalla; un error del servidor se ve como mensaje claro; la consola (F12) sin errores rojos. Anota cada fallo en `equipo/entregas/blanco_hallazgos.md`: qué hiciste, qué esperabas, qué pasó y de quién es el archivo | Lista llena y cada fallo con dueño |
| **B2** | **Corregir.** Arregla lo tuyo o lo que Oscar te asigne. Lo de Karel o de Lobo, devuélveselo con el hallazgo. No cambies cifras ni el formato del JSON | Fallos corregidos |
| **B3** (opcional) | **Robustez de `app.py`**, con permiso de Lobo: validar coordenadas fuera de rango, `NaN`, más de 2.000 puntos y cuerpo que no es JSON (hoy da una página HTML, no JSON); aviso (sin bloquear) para zonas fuera del área guardada; mensaje claro si falla Overpass (probar con `unittest.mock`); caché de los últimos 16 análisis, cuya clave incluya **todos** los parámetros | Hay pruebas y una segunda llamada idéntica es 10 veces más rápida |
| **B4** | **Revisión de textos** en español: usted, sin jerga («grafo», «Dijkstra»), cada error dice qué pasó y qué hacer, mismas palabras para lo mismo («obra», «etapa», «paso peatonal provisional»). Tabla `archivo | texto actual | texto propuesto` en `equipo/entregas/blanco_textos.md` para el dueño de cada archivo | Tabla entregada |

## Reglas

- **No toques archivos ajenos sin avisar al dueño.** Antes de que Oscar te avise, no edites nada.
- **44 pruebas en verde** antes de cada commit. No inventes datos ni cambies cifras.
- Rama `obras` (la misma de Karel y Lobo; ya terminaron). Commits pequeños, mensaje en español. **Commit y push al terminar cada tarea.**
- **Si el tiempo aprieta,** corta B3 (robustez) primero.

## Metaprompt para tu Claude

Pégalo en Claude Code, dentro de la carpeta del proyecto, **solo cuando Lobo y Oscar te hayan avisado «tu turno»**.

```
Eres el Claude que ayuda a Sebastián Blanco en el proyecto final de Matemáticas Discretas (MAT 4021,
Uninorte). Lee primero: equipo/cambio_a_obras.md, equipo/karel_silva.md y equipo/santiago_lobo.md (para saber
qué hicieron), proyecto_arroyos/app.py, src/etapas.py (solo lectura) y resultados/linea_base/plan_etapas.txt.

CONTEXTO: el proyecto pasó de "arroyos" a "hacer obras viales de la mejor forma" (una obra cierra calles; se
divide en etapas y se proponen medidas temporales). Eres el TERCERO de un relevo en la rama obras (Karel y
Lobo ya terminaron). Tu papel: probar la app terminada, anotar fallos y corregir lo que sea tuyo. No edites
archivos ajenos sin avisar al dueño: src/ y tests/ son de Karel; web/ y app.py son de Lobo; datos/,
resultados/ y documento/ son de Oscar. Antes de empezar: git checkout obras, git pull y python -m unittest
(deben pasar todas). Lee también equipo/entregas/karel_entrega.md y lobo_entrega.md.

TAREAS, en orden. Al terminar cada una: python -m unittest (deben pasar todas), commit con mensaje en español
y push a la rama obras. Si algo falla, DETENTE y dime qué pasó.
  B1  Prueba la app integrada con python app.py y esta lista: python -m unittest pasa todo; python
      herramientas/plan_etapas.py da lo mismo que resultados/linea_base/plan_etapas.txt (luego git checkout --
      proyecto_arroyos/resultados); planificar una obra dibujada; planificar con --obra
      datos/ejemplos/obra_ilustrativa.json; el recorrido muestra todos los pasos; no hay palabras "arroyo",
      "cauce" ni "lluvia" en pantalla; un error del servidor sale como mensaje claro; la consola (F12) sin
      errores rojos. Escribe cada fallo en equipo/entregas/blanco_hallazgos.md: qué se hizo, qué se esperaba,
      qué pasó y de quién es el archivo.
  B2  Corrige solo lo que sea tuyo o lo que yo te asigne; lo demás devuélvelo a su dueño con el hallazgo. No
      cambies cifras ni el formato del JSON.
  B3  (opcional, solo si yo te lo pido y Lobo lo permite) Robustez de app.py: validar coordenadas fuera de
      rango, NaN, más de 2000 puntos y cuerpo que no es JSON (hoy get_json(force=True) da una página HTML);
      aviso sin bloquear para zonas fuera del área guardada; mensaje claro si falla Overpass (prueba con
      unittest.mock, sin descargas reales); caché de los últimos 16 análisis con una clave que incluya todos
      los parámetros. Cada cosa con prueba.
  B4  Revisa los textos en español: usted, sin jerga, cada error dice qué pasó y qué hacer, mismas palabras
      para lo mismo ("obra", "etapa", "paso peatonal provisional"). Entrega una tabla archivo | texto actual |
      texto propuesto en equipo/entregas/blanco_textos.md.

REGLAS: no inventes datos ni cambies cifras. Al final de cada tarea resume en 3 líneas qué hiciste y qué
probaste. Si el tiempo aprieta, corta B3 primero. AL TERMINAR: escribe equipo/entregas/blanco_entrega.md (qué
probaste, qué corregiste, qué falta, qué te preocupa), haz commit y push, y dime "listo para pasar la posta a
Oscar".
```

## Cómo empezar

```
git clone https://github.com/odvelez/StreetView.git
cd StreetView/proyecto_arroyos
pip install -r requirements.txt
python -m unittest          # deben pasar 44 pruebas
python app.py               # http://localhost:5000
```
