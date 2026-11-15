"""Plan de obra por etapas: cómo hacer una obra que cierra calles sin parar la movilidad.

Uso (desde proyecto_obras/):
    python herramientas/plan_etapas.py                              # canalización de El Salao (caso de estudio)
    python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json
    python herramientas/plan_etapas.py --etapa-max 700 --un-puente-cada 400 --ancho 20

Guarda resultados/plan_etapas.json (para la web) y resultados/plan_etapas.txt (informe).
"""
import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src import fuente
from src.analisis import TOLERANCIA_M
from src.etapas import ETAPA_MAX_M, MEDICIONES, UN_PUENTE_CADA_M, plan_por_etapas, plural

SALIDA = RAIZ / "resultados"


def informe(nombre, plan):
    r = plan["resumen"]
    p = [f"PLAN DE OBRA POR ETAPAS: {nombre}",
         f"Obra de {r['longitud_m']} m a lo largo de su eje en {r['etapas']} "
         f"{plural(r['etapas'], 'etapa', 'etapas')} de hasta "
         f"{plan['parametros']['etapa_max_m']} m; un paso peatonal provisional por cada "
         f"{plan['parametros']['un_puente_cada_m']} m de obra (mínimo uno).",
         f"En total: {r['puentes_peatonales']} "
         f"{plural(r['puentes_peatonales'], 'paso peatonal provisional', 'pasos peatonales provisionales')}, "
         f"{r['cambios_de_sentido']} {plural(r['cambios_de_sentido'], 'cambio', 'cambios')} de sentido, "
         f"{r['rutas_alternas']} {plural(r['rutas_alternas'], 'ruta alterna', 'rutas alternas')} y "
         f"{r['esquinas_de_control']} {plural(r['esquinas_de_control'], 'esquina', 'esquinas')} para controlar "
         f"({r['esquinas_sin_semaforo']} sin semáforo registrado).",
         f"Durante cada etapa se cierran todos los tramos que tocan la franja de obra ({plan['parametros']['ancho_m']:g} m "
         "desde el eje) dentro del tramo en obra"
         + (", incluidos los puentes existentes." if plan["parametros"]["cerrar_puentes"]
            else "; los puentes existentes se mantienen abiertos.")]
    for e in plan["etapas"]:
        p.append(f"\nETAPA {e['numero']}: metro {e['inicio_m']} al {e['fin_m']} ({e['longitud_m']} m)")
        pex = e["puentes_existentes_cerrados"]
        p.append(f"  Cierra {e['cruces_cerrados']} {plural(e['cruces_cerrados'], 'cruce', 'cruces')} "
                 f"({pex} {plural(pex, 'es un puente existente', 'son puentes existentes')}); "
                 f"{len(e['tramos_cerrados'])} {plural(len(e['tramos_cerrados']), 'tramo', 'tramos')} en total.")
        pe, ve = e["peatones"], e["vehiculos"]
        if not pe:
            p += [f"  AVISO: {a}" for a in e["avisos"]]
            continue
        o, c = pe["obra"], pe["con_puentes"]
        p.append(f"  A pie: desvío medio {o['desvio_medio_m']:.0f} m -> {c['desvio_medio_m']:.0f} m con "
                 f"{len(pe['puentes'])} de {e['puentes_necesarios']} "
                 f"{plural(e['puentes_necesarios'], 'paso peatonal', 'pasos peatonales')} (máximo {o['desvio_max_m']:.0f} -> "
                 f"{c['desvio_max_m']:.0f} m).")
        for q in pe["puentes"]:
            donde = f"cruce de la {q['via']}" if q["tipo"] == "cruce" else "paso nuevo"
            p.append(f"     paso peatonal {q['orden']}: {q['desde']} <-> {q['hasta']} ({donde}, {q['recorrido_m']} m, "
                     f"metro {q['pos_m']} de la obra)")
        o, c = ve["obra"], ve["con_medidas"]
        p.append(f"  En carro: desvío medio {o['desvio_medio_m']:.0f} m; pares sin camino {o['sin_camino']} -> "
                 f"{c['sin_camino']}; desvío medio sobre los mismos pares {o['desvio_fijo_m']:.0f} -> "
                 f"{c['desvio_fijo_m']:.0f} m.")
        for q in ve["medidas"]:
            p.append(f"     doble sentido {q['orden']}: {q['via']}, {q['desde']} -> {q['hasta']} ({q['metros']} m, "
                     f"metro {q['pos_m']})")
        for r_ in e["rutas"]:
            partes = []
            for quien, k in (("carro", "carro"), ("a pie", "pie")):
                if k in r_:
                    v = r_[k]
                    partes.append(f"{quien} {v['seco_m']} -> {v['lluvia_m'] if v['lluvia_m'] is not None else 'sin ruta'}")
            p.append(f"     ruta alterna {r_['via']:<20} " + "   ".join(partes))
        for c_ in e["carga"]:
            sem = {True: "con semáforo", False: "SIN semáforo registrado", None: "semáforo desconocido"}[c_["semaforo"]]
            p.append(f"     esquina a controlar: {c_['nombre']} ({c_['recorridos']} recorridos desviados, "
                     f"{c_['porcentaje']} %, {sem})")
        p += [f"  AVISO: {a}" for a in e["avisos"]]
    p.append("\nLÍMITES: no hay datos de volumen de tránsito (no se mide congestión, solo desvíos en metros y cuántos "
             "recorridos desviados pasan por cada esquina); no se diseñan carriles ni tiempos de semáforo; todo debe "
             "verificarse en terreno.")
    return "\n".join(p)


def main():
    # En Windows, con la salida redirigida a un archivo, los acentos salen mal sin esto.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Plan de obra por etapas.")
    ap.add_argument("--obra", help="archivo JSON con el eje de la obra (por defecto, la canalización de El Salao)")
    ap.add_argument("--radio", type=float, default=400)
    ap.add_argument("--luz", type=float, default=60, help="largo máximo de un paso peatonal provisional nuevo")
    ap.add_argument("--etapa-max", type=float, default=ETAPA_MAX_M, help="largo máximo de una etapa, en metros")
    ap.add_argument("--un-puente-cada", type=float, default=UN_PUENTE_CADA_M,
                    help="metros de obra por cada paso peatonal provisional")
    ap.add_argument("--ancho", type=float, default=TOLERANCIA_M,
                    help=f"ancho de la franja de obra, en m desde el eje (por defecto {TOLERANCIA_M})")
    ap.add_argument("--medicion", default="lados", choices=MEDICIONES, help="cómo se miden los recorridos")
    ap.add_argument("--mantener-puentes", action="store_true",
                    help="la obra no cierra los puentes que ya existen en el tramo")
    args = ap.parse_args()

    if args.obra:
        try:
            datos = fuente.leer_obra(args.obra)
        except (OSError, ValueError) as ex:
            raise SystemExit(f"No se pudo leer la obra: {ex}")
        nombre, lineas = datos["nombre"], datos["lineas"]
        if datos["ilustrativo"] and "no es una obra real" not in nombre.lower():
            nombre += " (ejemplo ilustrativo, no es una obra real)"
    else:
        nombre, lineas = "Canalización del arroyo El Salao, Soledad (caso de estudio)", fuente.lineas_ejemplo()
    recuadro, lado = fuente.recuadro_de(lineas, args.radio)
    if lado > fuente.MAX_LADO_M:
        raise SystemExit("La obra es demasiado grande para analizarla de una vez.")
    t = time.time()
    red, _ = fuente.red_para(recuadro)
    plan = plan_por_etapas(red, lineas, radio=args.radio, luz_max=args.luz, etapa_max_m=args.etapa_max,
                           un_puente_cada_m=args.un_puente_cada, recuadro=recuadro,
                           cerrar_puentes=not args.mantener_puentes, ancho_m=args.ancho, medicion=args.medicion)
    texto = informe(nombre, plan)
    print(texto)
    print(f"\nTiempo: {time.time() - t:.1f} s")
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "plan_etapas.txt").write_text(texto + "\n", encoding="utf-8")
    (SALIDA / "plan_etapas.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
