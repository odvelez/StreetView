# Lista de comprobación de la pantalla (Lobo, L5)

**Fecha:** viernes 13 de noviembre de 2026. **Rama:** `obras`. **Servidor:** `python app.py` con la ruta real `POST /api/plan` (no la copia de `resultados/`).
**Cómo se probó:** Chromium sin cabeza (Playwright) que abre `http://127.0.0.1:5000/?ejemplo`, recorre la pantalla y mide cada cosa. En total, **129 comprobaciones automáticas, 129 bien**, más las pruebas sueltas de abajo. `python -m unittest`: **63 pruebas en verde** (antes de cada commit).

Leyenda: ✅ comprobado y bien · 👤 falta que lo pruebe una persona

## 1. Los 9 pasos de El Salao (L1)

Plan real del servidor: 3 etapas, 9 pasos. El orden en pantalla es exactamente el de `plan.pasos`.

| # | `id` | Cifra · unidad | Capas resaltadas (lo demás al 20 %) | 1920×1080 | 1366×768 | 390×844 |
|---|---|---|---|---|---|---|
| 1 | `etapas` | 3 · etapas de obra | eje de las 3 etapas | ✅ | ✅ | ✅ |
| 2 | `puentes` | 5 · pasos peatonales | pasos peatonales de las 3 etapas | ✅ | ✅ | ✅ |
| 3 | `sentidos` | 3 · calles a doble sentido | calles moradas de las 3 etapas | ✅ | ✅ | ✅ |
| 4 | `rutas` | 18 · rutas alternas | rutas en carro y a pie de las 3 etapas | ✅ | ✅ | ✅ |
| 5 | `control` | 15 · esquinas para controlar | esquinas (rojo, verde o gris) | ✅ | ✅ | ✅ |
| 6 | `etapa-1` | 2 · pasos peatonales | todas las capas, solo de la etapa 1 | ✅ | ✅ | ✅ |
| 7 | `etapa-2` | 2 · pasos peatonales | todas las capas, solo de la etapa 2 | ✅ | ✅ | ✅ |
| 8 | `etapa-3` | 1 · paso peatonal | todas las capas, solo de la etapa 3 | ✅ | ✅ | ✅ |
| 9 | `limites` | ! · límites | ninguna (todo atenuado) | ✅ | ✅ | ✅ |

En cada paso y cada pantalla se comprobó:

- ✅ Contador «Paso N de 9» correcto.
- ✅ Cifra de 104 px en escritorio y 96 px en el teléfono (se pide 96 o más).
- ✅ Tarjeta entera dentro de la pantalla.
- ✅ Panel desenfocado y oscurecido (`filter: blur(3px) opacity(.45)`).
- ✅ El mapa se acerca a `paso.foco`, que queda dentro del mapa y **sin que la tarjeta lo tape (0 %)**.
- ✅ Solo están encendidas las capas de `paso.capas`, y en los pasos de etapa, solo las de esa etapa.

## 2. Teclado y botones del recorrido

- ✅ → avanza, ← retrocede y Esc salta el recorrido.
- ✅ «Anterior» está desactivado en el paso 1.
- ✅ «Siguiente» avanza, y en el último paso dice «Terminar ✓».
- ✅ «Saltar recorrido» cierra el recorrido.
- ✅ Al terminar vuelve la vista normal: sin desenfoque, con la lista de etapas, y el foco del teclado queda en «Repetir el recorrido».
- ✅ «Repetir el recorrido» empieza otra vez en el paso 1.
- ✅ Mientras dura el recorrido, el panel queda `inert` (no se puede tocar ni enfocar) y las flechas no mueven el mapa.

## 3. Cambio de etapas (L3)

- ✅ El selector «Todas · 1 · 2 · 3» funciona: en las tres pantallas, la tarjeta del panel dice «Etapa N» y en el mapa solo queda encendida la etapa N.
- ✅ Al tocar una ruta alterna se ven el cruce cerrado (rojo, con ✕), la ruta en carro (amarilla, con borde oscuro) y la ruta a pie (verde punteada), cada una con su color. El recuadro trae un enlace a Street View y no tapa la ruta (0 de 86 puntos tapados en escritorio y 8 de 86 en el teléfono).
- ✅ Un paso peatonal o una esquina abre su ventana, con enlace a Street View.
- ✅ «Volver a la etapa» y «Ver toda la obra» funcionan.
- ✅ Las seis cifras principales están juntas: 3 etapas · 2.386 m · 5 pasos peatonales · 3 calles a doble sentido · 18 rutas alternas · 15 esquinas (14 sin semáforo).
- ✅ Los ajustes llegan al servidor. Con 500 m, 250 m y sin cerrar los puentes, el pedido lleva esos valores y la respuesta trae 5 etapas y 11 pasos, con 5 colores Okabe-Ito y 6 pestañas.

## 4. Error del servidor y datos incompletos

- ✅ **400 real** (obra de unos 11 km): «La zona es muy grande (11.1 km de lado)…». No se abre el recorrido.
- ✅ **503** (simulado): se muestra el mensaje del servidor.
- ✅ **500 sin JSON** (simulado): «El servidor respondió con un error (500).»
- ✅ **Servidor apagado** (simulado): «No hay conexión con el servidor. ¿Está corriendo python app.py?».
- ✅ `peatones: null` y `vehiculos: null`: la etapa avisa «no trae datos de…» y muestra `etapas[].avisos`.
- ✅ Datos incompletos sin errores de JavaScript: etapa sin `eje` ni `cauce`, rutas sin `carro`, etapa sin `carga`, `detalle` como texto suelto, paso sin `foco` y un campo nuevo desconocido.
- ✅ Plan vacío (`{resumen: {}}`): no se rompe, no abre el recorrido y avisa que el servidor no envió pasos.

## 5. Consola sin errores rojos

- ✅ No hay ningún error de JavaScript en la consola en ninguna prueba.
- Las únicas líneas rojas son «Failed to load resource» del propio navegador cuando se fuerza un 503, un 500 o una caída a propósito. Es lo esperado: la página las maneja.

## 6. Menú y textos (L2)

- ✅ El menú tiene 3 pasos, y cada uno se marca con ✓ cuando ya se cumplió.
- ✅ «Dibujar la obra» marca puntos con clics o toques, «Deshacer» quita uno, «Borrar» limpia todo y «Planificar obra» se habilita solo con una obra.
- ✅ «Cargar ejemplo: obra de canalización de El Salao» planifica directo, y `/?ejemplo` también.
- ✅ El ejemplo de la calle 72 muestra «Ejemplo ilustrativo, no es una obra real» en el menú, en la tarjeta del recorrido y en los resultados. Usa el singular: «1 etapa de obra».
- ✅ Ni «arroyo», ni «cauce», ni «lluvia» aparecen en lo que ve el usuario (texto y `title`). En `web/` solo quedan como claves del JSON del contrato (`cauce`, `lluvia_m`, `arroyo`).
- ✅ No se usa `/api/arroyos` ni `lineas_por_nombre`, y la capa azul de arroyos ya no está.
- ✅ La única carga externa es Leaflet 1.9.4, con versión exacta.

## 7. Escritorio y pantalla pequeña (L4)

| Comprobación | 1920×1080 | 1366×768 | 390×844 |
|---|---|---|---|
| Distribución | panel a la izquierda, 400 px | panel a la izquierda, 400 px | mapa arriba (380 px), panel abajo |
| Sin desplazamiento horizontal (menú, recorrido, resultados) | ✅ | ✅ | ✅ |
| Todo lo que se toca mide 48 px o más | — | — | ✅ (menú, recorrido, resultados, ruta) |

## 8. Lo que falta probar a mano

- 👤 **Que un compañero planifique una obra sin que le expliquen** (criterio de L2). Esto no se puede medir con una máquina: que lo pruebe Blanco.
- 👤 Ver la pantalla en un teléfono de verdad, con el dedo. Aquí se emuló un 390×844 táctil.
- 👤 Las animaciones (el vuelo del mapa entre pasos) en un navegador visible.
