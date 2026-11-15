"""Plan de obra por etapas: cómo hacer una obra que cierra calles sin parar la movilidad.

Uso (desde proyecto_arroyos/):
    python herramientas/plan_etapas.py                              # canalización de El Salao (caso de estudio)
    python herramientas/plan_etapas.py --obra datos/ejemplos/obra_ilustrativa.json
    python herramientas/plan_etapas.py --etapa-max 700 --un-puente-cada 400 --ancho 20
    python herramientas/plan_etapas.py --calculadas [--d0 400]      # agrega las propuestas calculadas

Guarda resultados/plan_etapas.json (para la web) y resultados/plan_etapas.txt (informe). Con --calculadas
solo imprime (no toca resultados/), salvo que también se pase --guardar.
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
from src.supuestos import SUPUESTOS

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
    if "supuestos" in plan:
        p += informe_calculadas(plan)
    p.append("\nLÍMITES: no hay datos de volumen de tránsito (no se mide congestión, solo desvíos en metros y cuántos "
             "recorridos desviados pasan por cada esquina); no se diseñan carriles ni tiempos de semáforo; todo debe "
             "verificarse en terreno.")
    return "\n".join(p)


def _m(x):
    return f"{x['desvio_ponderado_m']:.0f} m" + (f" ({x['sin_camino']} pares sin camino)" if x["sin_camino"] else "")


def informe_calculadas(plan):
    """Sección de las propuestas calculadas (src/circulacion.py), con sus supuestos."""
    c = plan["parametros"]["calculadas"]
    p = ["\nPROPUESTAS CALCULADAS (demanda supuesta; no hay conteos)",
         f"Demanda: modelo de gravedad, peso del par = exp(-distancia sin obra / {c['d0_m']} m), esquinas de igual peso. "
         f"Capacidad: carriles del corte mínimo (flujo máximo de un lado al otro); 1 carril ≈ {c['veh_h_carril']} veh/h "
         "(supuesto)."]
    for e in plan["etapas"]:
        p.append(f"\nETAPA {e['numero']}")
        ci = e["circulacion"]
        if not ci:
            p.append(f"  {e['pares_viales']['motivo']}")
            continue
        k = ci["capacidad"]
        p.append(f"  Carriles para cruzar (A->B / B->A): sin obra {k['seco']['a_b']} / {k['seco']['b_a']}; con la obra "
                 f"{k['obra']['a_b']} / {k['obra']['b_a']}; con las medidas {k['con_medidas']['a_b']} / {k['con_medidas']['b_a']}. "
                 f"Calles del corte con la obra (A->B): {', '.join(k['obra']['calles_a_b']) or 'ninguna'} (el corte "
                 "mínimo es el cuello de botella de toda la red entre los dos lados; puede estar lejos del eje).")
        pe, ve = ci["peatones"], ci["vehiculos"]
        p.append(f"  A pie, desvío ponderado: {_m(pe['obra'])} con la obra; {_m(pe['con_pasos_regla_500m'])} con la regla "
                 f"de 500 m; {_m(pe['con_pasos_por_demanda'])} con los pasos por demanda "
                 f"(solo alargamiento: {pe['con_pasos_por_demanda']['desvio_positivo_m']:.0f} m).")
        p.append(f"  En carro, desvío ponderado: {_m(ve['obra'])} con la obra; {_m(ve['con_cambios_de_sentido'])} con los "
                 f"cambios de sentido; {_m(ve['con_cambios_y_pares_viales'])} con los pares viales.")
        pv = e["pares_viales"]
        if pv["pares"]:
            for par in pv["pares"]:
                p.append(f"  Par vial {' y '.join(par['calles'])} ({par['relacion']}, {par['separacion_m']} m): "
                         f"{par['elegida']}. {par['motivo']}")
                for a in par["alternativas"]:
                    if a["evaluada"]:
                        p.append(f"     {a['configuracion']:<34} desvío {a['desvio_ponderado_m']:>6.0f} m, sin camino "
                                 f"{a['sin_camino']:>4}, carriles {a['capacidad_a_b']} / {a['capacidad_b_a']}")
                    else:
                        p.append(f"     {a['configuracion']:<34} {a['nota']}")
        else:
            p.append(f"  Pares viales: {pv['motivo']}")
        for x in pv["excluidas"]:
            p.append(f"     no se usa {x['via']}: {x['motivo']}")
        pd = e["pasos_por_demanda"]
        reg = pd["comparacion_regla_500m"]
        p.append(f"  Pasos peatonales por demanda: {pd['numero']} (con la regla de 500 m: {reg['numero']}). Mayor tramo "
                 f"sin cruce: {pd['brecha_max_m']} m (con la regla: {reg['brecha_max_m']} m)."
                 + (" Se llegó al máximo de pasos por etapa." if pd["limitado_por_maximo"] else ""))
        for q in pd["pasos"]:
            donde = f"cruce de la {q['via']}" if q["tipo"] == "cruce" else "paso nuevo"
            p.append(f"     paso {q['orden']}: {q['desde']} <-> {q['hasta']} ({donde}, metro {q['pos_m']}) -> alargamiento "
                     f"ponderado {q['desvio_positivo_m']:.0f} m")
        for b in pd["tramos_sobre_brecha"]:
            p.append(f"     tramo sin cruce del metro {b['inicio_m']} al {b['fin_m']} ({b['largo_m']} m); candidatos "
                     f"dentro: {b['candidatos_dentro']}")
        ct = e["control_temporal"]
        for q in ct["esquinas"]:
            p.append(f"  Control temporal: {q['nombre']} ({q['puntaje_pct']:.0f} % de la demanda desviada, "
                     f"{q['accesos']} accesos{', vía principal' if q['cruza_via_mayor'] else ''})")
        if ct["descartadas_por_semaforo"]:
            p.append(f"     {ct['descartadas_por_semaforo']} esquinas muy cargadas ya tienen semáforo registrado.")
    p.append("\nSUPUESTOS (valor, rango, estado):")
    for s_ in plan["supuestos"]:
        rango = f"{s_['rango'][0]}–{s_['rango'][1]}" if isinstance(s_["rango"], list) and len(s_["rango"]) == 2 else s_["rango"]
        valor = s_["valor"] if not isinstance(s_["valor"], (dict, list)) else "ver src/supuestos.py"
        p.append(f"  {s_['nombre']:<28} {valor} {s_['unidad']}; rango {rango}; {s_['estado']}")
    p.append("Control temporal: es una priorización sin conteos, no un criterio para instalar semáforos (los criterios "
             "del MUTCD, capítulo 4C, exigen conteos). No se calculan tiempos de semáforo.")
    return p


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
    ap.add_argument("--calculadas", action="store_true",
                    help="agrega las propuestas calculadas (pares viales, pasos por demanda, control temporal, capacidad)")
    d0 = SUPUESTOS["d0_m"]
    ap.add_argument("--d0", type=float, default=d0.valor,
                    help=f"distancia de la demanda supuesta, en m ({d0.rango[0]} a {d0.rango[1]}; por defecto {d0.valor})")
    ap.add_argument("--guardar", action="store_true", help="con --calculadas, también escribe en resultados/")
    args = ap.parse_args()
    if not (d0.rango[0] <= args.d0 <= d0.rango[1]):
        ap.error(f"--d0 entre {d0.rango[0]} y {d0.rango[1]}")

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
                           cerrar_puentes=not args.mantener_puentes, ancho_m=args.ancho, medicion=args.medicion,
                           propuestas_calculadas=args.calculadas, d0_m=args.d0)
    texto = informe(nombre, plan)
    print(texto)
    print(f"\nTiempo: {time.time() - t:.1f} s")
    if args.calculadas and not args.guardar:
        print("(Con --calculadas no se escribe en resultados/; use --guardar para escribirlo.)")
        return
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "plan_etapas.txt").write_text(texto + "\n", encoding="utf-8")
    (SALIDA / "plan_etapas.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
