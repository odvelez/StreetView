"""Geometría plana local: distancias en metros, cruces y lado del arroyo.

En una zona de pocos kilómetros la Tierra se puede tratar como plana:
1 grado de latitud mide unos 110.6 km y 1 grado de longitud mide 111.3 km * cos(latitud).
"""
import math

M_LAT = 110600.0


def m_lon(lat):
    return 111320.0 * math.cos(math.radians(lat))


class Plano:
    """Convierte (lat, lon) a (x, y) en metros alrededor de una latitud de referencia."""

    def __init__(self, lat_ref):
        self.k = m_lon(lat_ref)

    def xy(self, p):
        return p[1] * self.k, p[0] * M_LAT

    def dist(self, a, b):
        ax, ay = self.xy(a)
        bx, by = self.xy(b)
        return math.hypot(ax - bx, ay - by)


def se_cruzan(a, b, c, d):
    """True si el segmento a-b corta al segmento c-d (puntos ya en metros)."""
    den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
    if abs(den) < 1e-9:
        return False
    t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
    u = ((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / den
    return -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9


def proyectar(p, a, b):
    """Punto más cercano a p sobre el segmento a-b: (distancia, t, producto_cruz).

    t en [0, 1] dice en qué parte del segmento cae; el signo del producto cruz
    dice si p está a la izquierda (+) o a la derecha (-) del sentido a -> b.
    """
    vx, vy = b[0] - a[0], b[1] - a[1]
    l2 = vx * vx + vy * vy
    t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2)) if l2 else 0.0
    qx, qy = a[0] + t * vx, a[1] + t * vy
    cruz = vx * (p[1] - a[1]) - vy * (p[0] - a[0])
    return math.hypot(p[0] - qx, p[1] - qy), t, cruz


class Arroyo:
    """Cauce formado por una o varias líneas quebradas [(lat, lon), ...]."""

    def __init__(self, lineas, plano):
        self.plano = plano
        self.lineas = [[plano.xy(p) for p in linea] for linea in lineas if len(linea) >= 2]
        if not self.lineas:
            raise ValueError("El arroyo necesita al menos dos puntos")
        self.segmentos = [(l[i], l[i + 1]) for l in self.lineas for i in range(len(l) - 1)]
        # Metros recorridos por el cauce hasta el inicio de cada segmento (para `posicion`).
        self.inicio_segmento, total = [], 0.0
        for a, b in self.segmentos:
            self.inicio_segmento.append(total)
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        # Índice espacial: cuadrícula de CELDA metros con los segmentos que pasan por cada celda.
        # Así, para saber si una calle toca el arroyo, solo se revisan los segmentos cercanos.
        self.celdas = {}
        for i, (a, b) in enumerate(self.segmentos):
            for c in self._celdas(a, b, 20):
                self.celdas.setdefault(c, []).append(i)

    CELDA = 100.0

    def _celdas(self, a, b, margen):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for cx in range(int((x0 - margen) // self.CELDA), int((x1 + margen) // self.CELDA) + 1):
            for cy in range(int((y0 - margen) // self.CELDA), int((y1 + margen) // self.CELDA) + 1):
                yield cx, cy

    def cercanos(self, a, b, margen):
        """Índices de los segmentos del cauce que podrían estar a menos de `margen` de a-b."""
        res = set()
        for c in self._celdas(a, b, margen):
            res.update(self.celdas.get(c, ()))
        return res

    def longitud(self):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in self.segmentos)

    def posicion(self, p):
        """Metros, medidos a lo largo del cauce desde su inicio, del punto del cauce más cercano a p."""
        mejor = None
        for i, (a, b) in enumerate(self.segmentos):
            d, t, _ = proyectar(p, a, b)
            if mejor is None or d < mejor[0]:
                mejor = (d, i, t)
        _, i, t = mejor
        a, b = self.segmentos[i]
        return self.inicio_segmento[i] + t * math.hypot(b[0] - a[0], b[1] - a[1])

    def corta(self, p, q):
        """True si el segmento p-q (en metros) atraviesa el cauce."""
        return any(se_cruzan(p, q, a, b) for a, b in self.segmentos)

    def ubicar(self, p):
        """(distancia al cauce, lado +1/-1, True si el punto queda frente a un extremo)."""
        mejor = None
        for linea in self.lineas:
            ultimo = len(linea) - 2
            for i in range(len(linea) - 1):
                d, t, cruz = proyectar(p, linea[i], linea[i + 1])
                if mejor is None or d < mejor[0]:
                    extremo = (i == 0 and t <= 0.0) or (i == ultimo and t >= 1.0)
                    mejor = (d, 1 if cruz >= 0 else -1, extremo)
        return mejor


def orientar(lineas):
    """Ordena y orienta los tramos para que todos sigan el mismo sentido del cauce.

    Así "izquierda" significa lo mismo en todos los tramos, aunque el usuario
    los haya dibujado o seleccionado en desorden.
    """
    lineas = [list(l) for l in lineas if len(l) >= 2]
    if len(lineas) <= 1:
        return lineas

    def cerca(p, q):
        return abs(p[0] - q[0]) < 2e-5 and abs(p[1] - q[1]) < 2e-5

    # 1. Unir tramos que se tocan por sus extremos.
    unido = True
    while unido:
        unido = False
        for i in range(len(lineas)):
            for j in range(i + 1, len(lineas)):
                a, b = lineas[i], lineas[j]
                if cerca(a[-1], b[0]):
                    nueva = a + b[1:]
                elif cerca(b[-1], a[0]):
                    nueva = b + a[1:]
                elif cerca(a[-1], b[-1]):
                    nueva = a + b[::-1][1:]
                elif cerca(a[0], b[0]):
                    nueva = a[::-1] + b[1:]
                else:
                    continue
                lineas[i] = nueva
                del lineas[j]
                unido = True
                break
            if unido:
                break

    # 2. Los que siguen separados se orientan según la dirección del más largo.
    ref = max(lineas, key=len)
    dx, dy = ref[-1][1] - ref[0][1], ref[-1][0] - ref[0][0]
    return [l if (l[-1][1] - l[0][1]) * dx + (l[-1][0] - l[0][0]) * dy >= 0 else l[::-1]
            for l in lineas]
