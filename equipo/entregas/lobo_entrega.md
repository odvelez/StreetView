# Entrega de Lobo (turno 2): la pantalla

**Estado:** L1, L2, L3, L4 y L5 hechas, un commit por tarea, todas subidas a `obras`.
**Pruebas de Python:** `python -m unittest` → **63 en verde** antes de cada commit.
**Pruebas de la pantalla:** 129 comprobaciones automáticas en Chromium (Playwright), todas bien. Detalle en [lobo_checklist.md](lobo_checklist.md).

## Qué cambié

| Tarea | Qué se hizo | Archivos |
|---|---|---|
| **L2** | **Menú de inicio en 3 pasos:** (1) elegir el municipio, (2) definir la obra con «Dibujar la obra», «Deshacer», «Borrar» o uno de los ejemplos, (3) planificar. Cada paso se marca con ✓ cuando ya se cumplió. **Ajustes plegables:** largo máximo de etapa (500, 700, **1000**, 1500), un paso peatonal cada (250, **500**, 750) y «La obra cierra también los puentes existentes» (marcado). Se quitaron la capa azul de arroyos, el pedido a `/api/arroyos` y todo texto de «arroyo», «cauce» o «lluvia». | `web/index.html`, `web/app.js`, `web/estilos.css`, `app.py` |
| **L1** | **Recorrido paso a paso.** Al planificar: `POST /api/plan`; el panel y los controles del mapa se desenfocan y oscurecen; en el centro una tarjeta con `paso.cifra` (104 px; 96 px en el teléfono), `unidad`, `titulo`, `detalle` y los `avisos` de la etapa. Anterior / Siguiente / Saltar, teclas ← → Esc y «Paso 3 de 9» con puntitos. El mapa vuela a `paso.foco` **dentro de la zona que la tarjeta no tapa** y resalta solo `paso.capas` (en los pasos de etapa, solo esa etapa); lo demás queda al 20 %. Los pasos salen tal cual de `plan.pasos`. Al terminar queda la vista normal y el botón «Repetir el recorrido». | `web/` |
| **L3** | **Resultados.** Seis cifras juntas; selector «Todas · 1 · 2 · 3»; por etapa: desvío medio a pie y en carro (con la obra y con las medidas), avisos, pasos peatonales, calles a doble sentido, rutas alternas y esquinas a controlar. Al tocar una ruta: cruce cerrado en rojo, carro en amarillo y a pie en verde punteado, con un recuadro y enlace a Street View. Los pasos peatonales y las esquinas también abren una ventana con Street View. Leyenda del mapa. | `web/` |
| **L4** | En 700 px o menos: mapa arriba y panel abajo; todo lo tocable mide 48 px o más (también el zoom del mapa); recuadro de detalle compacto. Sin desplazamiento horizontal en 1920×1080, 1366×768 y 390×844. Respeta «reducir movimiento» del sistema. | `web/estilos.css`, `web/app.js` |
| **L5** | Lista de comprobación con los resultados. | `equipo/entregas/lobo_checklist.md` |

**Capas del mapa** (como pide la tarea):

| Capa | Cómo se dibuja | De dónde sale |
|---|---|---|
| Etapas | El eje en tramos Okabe-Ito | `etapas[].eje`, o `cauce` si no está |
| Pasos peatonales | Marcadores naranja | `peatones.puentes[].forma` |
| Sentidos | Calle morada | `vehiculos.medidas[].forma` |
| Rutas | En carro amarilla y a pie verde punteada; el cruce cerrado en rojo | `rutas[]` |
| Carga | Círculos rojo, verde o gris según `semaforo` | `carga[].posicion` |

### En `app.py` (aviso para Oscar)

Solo dos cambios pequeños, sin tocar `/api/plan`:

1. Ruta nueva **`GET /api/ejemplo_obra`**: devuelve `{nombre, ilustrativo, lineas}` de `datos/ejemplos/obra_ilustrativa.json` con `fuente.leer_obra`. Es el botón «Cargar ejemplo ilustrativo: 600 m de la calle 72»; la pantalla muestra «Ejemplo ilustrativo, no es una obra real».
2. El mensaje del error 500 genérico decía «al analizar este arroyo»; ahora dice «al planificar esta obra».

## Cómo se corre

Desde `proyecto_arroyos/`. Primero las pruebas (unos 20 s):

```bash
python -m unittest
```

Luego la app:

```bash
python app.py
```

Abra `http://localhost:5000`, o `http://localhost:5000/?ejemplo` para que se planifique El Salao solo (útil en la presentación). El primer plan tarda unos 10 s.

## Qué falta

- **Que un compañero planifique una obra sin explicación** (criterio de L2). No se puede medir con una máquina: Blanco, pruébalo con alguien.
- Probar en un teléfono de verdad (aquí se emuló 390×844 táctil) y ver las animaciones del mapa en un navegador visible.
- La pantalla no deja **corregir a mano** tramos abiertos o cerrados (la vieja sí, con `abiertos`/`cerrados`). El plan solo devuelve los `id` de `tramos_cerrados`, sin su forma, así que no hay qué dibujar para tocarlos. Se mandan `abiertos: []` y `cerrados: []`.
- Los ajustes `radio`, `luz_max` y `ancho_m` no están en la pantalla: no los pedía la tarea y el servidor usa sus valores por defecto.

## Qué me preocupa

1. **Capturas de Gustavo:** los `id` de la pantalla ya son estos (`#menu`, `#paso-municipio`, `#paso-obra`, `#paso-planificar`, `#ajustes`, `#btn-planificar`, `#recorrido`, `#rec-*`, `#resultados`, `#cifras`, `#selector-etapa`, `#detalle-etapa`). Si alguien los cambia después del sábado, sus capturas se desactualizan. Truco para las capturas: `/?ejemplo`.
2. **El mapa no se desenfoca, se oscurece.** La tarea pide desenfocar «el resto de la página». Desenfoqué el panel y los controles (`blur(3px) opacity(.45)`), pero el fondo del mapa solo se oscurece: si se desenfoca, no se leen las calles del paso que se está mostrando.
3. **La tarjeta va en el centro y tapa parte del mapa.** Por eso el mapa encuadra `paso.foco` en la zona libre (a la derecha de la tarjeta en escritorio, arriba en el teléfono). En 1366×768 esa zona mide unos 460 px de ancho y la obra se ve chica. Si molesta, se puede poner la tarjeta sobre el panel.
4. **El verde de la etapa 3 (`#009E73`) se parece al verde de la ruta a pie.** Los dos colores los fija la tarea. Para distinguirlos, el eje es grueso y continuo, la ruta a pie es punteada, y al ver una ruta todo el plan se atenúa.
5. Los textos de la tarjeta (`pasos[].detalle`) vienen tal cual del servidor, y ahí todavía dice «1 cambio(s) de sentido». No lo cambié porque es de `src/`; si se arregla allá, la tarjeta lo toma sola. Las cifras del panel de resultados sí usan bien el singular y el plural («1 etapa de obra»).
6. `resultados/plan_etapas.json` todavía tiene los textos viejos («El arroyo mide…», «puentes peatonales temporales»). La pantalla no lo usa (pide el plan en vivo), pero Oscar lo regenera al final.
