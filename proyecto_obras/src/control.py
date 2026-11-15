"""Control de la clasificación de lados: producto cruz contra componentes conexas.

El análisis decide de qué lado de la obra queda cada esquina con el signo del producto
cruz respecto al segmento más cercano del eje de la obra (`Obra.ubicar`). Este módulo lo revisa
con un método independiente que solo usa el grafo:

  1. Se arma el grafo de peatones con las esquinas que se quieren clasificar.
  2. Se quitan los tramos que tocan la franja de obra.
  3. Se calculan las componentes conexas (BFS).

Si la obra separa de verdad dos lados, cada componente debe quedar casi toda de un solo
lado. Para cada componente se toma su lado mayoritario; el porcentaje de acuerdo es la
fracción de esquinas cuyo lado por producto cruz coincide con el mayoritario de su
componente. Es un control, no un reemplazo: no dice cuál método tiene razón en cada
esquina, solo qué tan de acuerdo están.

Qué esquinas se clasifican:
  - `lados_de_zona`: las de la zona de estudio. La zona ya deja fuera las esquinas a menos de
    10 m del eje, así que el grafo queda separado en parte por construcción: el acuerdo
    alto es esperable y dice poco.
  - `lados_por_distancia`: todas las esquinas a menos de `radio` metros del eje, incluidas
    las de la orilla. Es el control más exigente: ahí aparecen los desacuerdos reales.

Hay dos variantes de grafo:
  - "barrera_total": se quitan todos los tramos que tocan la franja, también los puentes
    y los que el usuario marcó como abiertos. La obra es una barrera completa.
  - "lluvia" (nombre heredado): se quitan solo los tramos cerrados por la obra hecha toda a la vez.
    Los puentes siguen uniendo los dos lados, así que se espera menos acuerdo: mide cuánto conectan.
"""
from src.grafo import Grafo, componentes_conexas


def lados_de_zona(lados_todos):
    """{esquina: lado} de las esquinas de la zona de estudio (`zona` las separa por lado)."""
    return {n: s for s in (1, -1) for n in lados_todos[s]}


def lados_por_distancia(red, obra, radio):
    """{esquina: lado} de toda esquina a menos de `radio` m del eje y no más allá de sus extremos."""
    lado = {}
    for n, p in red.pos.items():
        d, s, extremo = obra.ubicar(red.plano.xy(p))
        if d <= radio and not extremo:
            lado[n] = 1 if s > 0 else -1
    return lado


def control_de_lados(red, contacto, lado, modo="barrera_total", ejemplos=15):
    """`lado` es {esquina: 1 o -1} según el producto cruz (ver `lados_de_zona`, `lados_por_distancia`)."""
    g = Grafo(dirigido=False)
    for n in lado:
        g.agregar_nodo(n)
    for t in red.tramos:
        if not t.peatonal or t.u not in lado or t.v not in lado:
            continue
        estado = contacto.get(t.id, (None,))[0]
        if estado == "bloqueado" or (modo == "barrera_total" and estado is not None):
            continue
        g.agregar_arista(t.u, t.v, t.metros)

    de_acuerdo = 0
    componentes, mezcladas, minoritarias = [], 0, []
    for comp in componentes_conexas(g):
        a = sum(1 for n in comp if lado[n] == 1)
        b = len(comp) - a
        mayor = 1 if a >= b else -1
        de_acuerdo += max(a, b)
        mezcladas += a > 0 and b > 0
        componentes.append(dict(esquinas=len(comp), lado_1=a, lado_menos_1=b))
        if a and b:
            for n in comp:
                if lado[n] != mayor:
                    minoritarias.append((len(comp), n))
    minoritarias.sort(key=lambda x: (-x[0], str(x[1])))
    return dict(
        modo=modo,
        esquinas=len(lado),
        componentes=len(componentes),
        componentes_mezcladas=mezcladas,
        mayores=componentes[:5],
        acuerdo_pct=round(100 * de_acuerdo / max(len(lado), 1), 2),
        desacuerdos=len(lado) - de_acuerdo,
        ejemplos=[dict(esquina=n, posicion=list(red.pos[n]), nombre=red.nombre(n), lado_producto_cruz=lado[n])
                  for _, n in minoritarias[:ejemplos]],
    )
