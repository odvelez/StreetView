# Arroyos y desvíos (Barranquilla y área metropolitana)

Proyecto final de Matemáticas Discretas (MAT 4021), Universidad del Norte.

Cuando un arroyo crece, las calles que lo cruzan quedan bloqueadas y la gente tiene que dar la vuelta. Este programa:

1. Deja que el usuario marque un arroyo en el mapa: puede elegir uno de OpenStreetMap o dibujarlo.
2. Convierte las calles de la zona en grafos: uno **no dirigido** para peatones y uno **dirigido** para vehículos, que respeta los sentidos viales.
3. Mide con Dijkstra cuánto se alargan los recorridos entre los dos lados del arroyo cuando llueve.
4. Propone la mejor medida temporal mientras se canaliza el arroyo:
   - **Puente peatonal**, para quien va a pie.
   - **Habilitar doble sentido** en una calle de un solo sentido, para carros y motos.
   - **Ruta alterna para señalizar** en cada cruce que la lluvia cierra.

El caso de estudio es el arroyo El Salao, en Soledad.

## Requisitos

- Python 3.10 o superior.
- `pip install flask matplotlib`
  - Flask es necesario para la página web.
  - matplotlib es opcional; solo se usa para generar `resultados/mapa.png`.
- Los algoritmos (BFS, Dijkstra, centralidades y selección voraz) usan solo la biblioteca estándar.

## Cómo ejecutarlo

Abra una terminal dentro de esta carpeta.

### Página web

```bash
python app.py
```

Después abra http://localhost:5000 en el navegador.

1. Elija un municipio. Luego haga clic en un arroyo azul claro y pulse «Usar todo el arroyo», o dibuje el arroyo con «Dibujar».
2. Pulse **Analizar**.
3. Haga clic en los resultados para verlos en el mapa. Cada ruta alterna muestra el cruce cerrado (✕), el origen y el destino (A y B), el camino en carro con flechas y el camino a pie. El recuadro de arriba a la derecha da las cifras; «Ver todo el arroyo» vuelve a la vista general.
4. Si una calle roja en realidad sí se puede pasar, haga clic sobre ella, revise el enlace a Street View y márquela como abierta. El análisis se repite solo.

«Cargar el ejemplo» analiza El Salao directamente.

### Línea de comandos

```bash
python main.py                               # caso de estudio: El Salao
python main.py --arroyo "Arroyo Don Juan"    # otro arroyo de OpenStreetMap
python main.py --listar                      # nombres de arroyos disponibles
python main.py --radio 500 --k 2 --luz 80    # otros ajustes
python -m unittest -v                        # casos de prueba de resultado conocido
```

## Entrada y salida

| Archivo | Contenido |
|---|---|
| `datos/calles_area_metropolitana.json.gz` | Calles del área metropolitana tomadas de OpenStreetMap. Permite trabajar sin internet |
| `datos/arroyos_area_metropolitana.json` | Cauces con nombre: la capa azul del mapa |
| `datos/arroyo_el_salao.csv` | Cauce del caso de estudio |
| `resultados/resumen.txt` | Informe de `main.py` |
| `resultados/analisis.json` | Todos los números del análisis |
| `resultados/mapa.png` | Mapa para el documento y las diapositivas |

Si el arroyo marcado queda fuera del área guardada, el programa descarga las calles desde el servicio Overpass y las guarda en `datos/cache/`. Esa descarga puede tardar varios minutos.

## Organización del código

```
app.py                      servidor web (Flask)
main.py                     análisis por línea de comandos e informe
web/                        página: mapa (Leaflet), panel y estilos
src/grafo.py                grafo dirigido / no dirigido, BFS, componentes, Dijkstra, centralidades
src/red.py                  convierte calles de OpenStreetMap en tramos y grafos
src/geometria.py            cruces calle–arroyo, distancia y lado del cauce
src/analisis.py             escenarios, desvíos, candidatos y selección voraz
src/fuente.py               elige de dónde salen las calles de cada zona
src/osm.py                  lectura y descarga de OpenStreetMap
tests/test_proyecto.py      casos de prueba
herramientas/descargar_mapa.py   vuelve a descargar el mapa (solo para actualizarlo)
documento/main.tex          documento en LaTeX
version_anterior/           primera versión (solo El Salao), como referencia
```

## Fuente de los datos

Calles y arroyos: © colaboradores de OpenStreetMap, licencia ODbL. Se descargaron el 10 de noviembre de 2026 para el recuadro 10,84–11,12 N y 74,96–74,73 O, que cubre Barranquilla, Soledad, Malambo, Puerto Colombia y Galapa.
