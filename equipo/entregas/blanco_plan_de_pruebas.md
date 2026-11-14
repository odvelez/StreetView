# Plan de pruebas de Blanco (turno 3)

Todo se corre desde `proyecto_arroyos/`.

| # | Qué se prueba | Cómo | Se espera |
|---|---|---|---|
| 1 | Pruebas automáticas | `python -m unittest` | Todas en verde (63 al recibir la posta) |
| 2 | Cifras de El Salao | `python herramientas/plan_etapas.py` y comparar con `resultados/linea_base/plan_etapas.txt`, solo los números; luego `git checkout -- proyecto_arroyos/resultados` | Mismos números (los textos sí cambiaron de «arroyo» a «obra») |
| 3 | La API con El Salao | `POST /api/plan` con `GET /api/ejemplo` | 200, 3 etapas, 9 pasos, mismos números que `linea_base/plan_etapas.json` |
| 4 | Obra con `--obra` | `python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json` y botón «Cargar ejemplo ilustrativo» | Plan de 1 etapa; la pantalla dice «Ejemplo ilustrativo, no es una obra real» |
| 5 | Obra dibujada | En Chrome: municipio Soledad, «Dibujar la obra», 3 clics, «Terminar», «Planificar obra» | Llega el plan y se abre el recorrido |
| 6 | Recorrido | Recorrer con «Siguiente» hasta «Terminar ✓» | Se ven todos los pasos de `plan.pasos` en orden y al final queda la vista normal |
| 7 | Palabras viejas | Leer todo el texto visible (inicio, cada paso, cada etapa, cada ruta y cada ventana del mapa) | Ninguna «arroyo», «cauce» ni «lluvia» |
| 8 | Errores del servidor | Respuestas 500 (JSON y HTML), 503, 400 real (zona muy grande) y servidor apagado | Mensaje claro en la pantalla, nunca HTML ni «undefined» |
| 9 | Consola | Leer los mensajes de la consola durante todas las pruebas | Sin errores rojos, salvo los provocados a propósito |
| 10 | Pedidos malos a la API | Cuerpo que no es JSON, lista en vez de objeto, `NaN`, coordenadas fuera de rango, zona muy grande, puntos mal formados | 400 con un mensaje en JSON, nunca 500 ni página HTML |

Las pruebas 5 a 9 se hicieron con Chrome sin ventana (headless), manejado por el protocolo de depuración
desde un script de Node, en 1366×768.
