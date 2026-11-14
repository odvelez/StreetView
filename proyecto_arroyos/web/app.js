// Planificar una obra por etapas: el usuario define el eje de la obra, el servidor (POST /api/plan)
// la divide en etapas y aquí se muestra el plan. Contrato del JSON: equipo/cambio_a_obras.md, sección 5.
// Lo que llega del servidor puede traer campos de más o de menos: nada aquí debe romperse si falta uno.

const COLOR = {
  obra: "#3b4750", rojo: "#c4362f", verde: "#1b8a5a", naranja: "#d9730d", morado: "#7b3fb0",
  gris: "#8a8f93", carro: "#e8a100", pie: "#199e70", tinta: "#1f2a30",
};
// Colores de las etapas, aptos para daltonismo (Okabe-Ito).
const COLOR_ETAPA = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"];
const colorEtapa = (n) => COLOR_ETAPA[(Math.max(1, n) - 1) % COLOR_ETAPA.length];

const $ = (id) => document.getElementById(id);
const num = (x) => (typeof x === "number" && Number.isFinite(x) ? x : null);
const fmt = (x) => (num(x) === null ? "—" : Math.round(x).toLocaleString("es-CO"));
const lista = (x) => (Array.isArray(x) ? x : x == null ? [] : [x]);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// ------------------------------------------------------------------ mapa base
const mapa = L.map("mapa", { zoomControl: true, zoomSnap: 0.5 }).setView([10.9636, -74.7964], 13);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>',
}).addTo(mapa);

const capaObra = L.layerGroup().addTo(mapa);   // la obra que el usuario define

// ------------------------------------------------------------------ estado
const estado = {
  lineas: [],          // [{coords: [[lat, lon], ...], origen: "dibujo" | "ejemplo"}]
  dibujando: false,
  ejemplo: null,       // null | {nombre, ilustrativo}
  plan: null,          // última respuesta de /api/plan
};

// ------------------------------------------------------------------ paso 1: municipio
$("municipio").onchange = (e) => {
  if (!e.target.value) return;
  const [lat, lon, z] = e.target.value.split(",").map(Number);
  mapa.setView([lat, lon], z);
  marcarPasos();
};

// ------------------------------------------------------------------ paso 2: definir la obra
$("btn-dibujar").onclick = () => {
  if (estado.dibujando) return terminarDibujo();
  salirDeEjemplo();
  estado.dibujando = true;
  estado.lineas.push({ coords: [], origen: "dibujo" });
  mapa.doubleClickZoom.disable();
  document.body.classList.add("dibujando");
  $("btn-dibujar").classList.add("activo");
  $("btn-dibujar").textContent = "Terminar";
  $("estado-dibujo").textContent = "Haga clic sobre el mapa siguiendo las calles que cierra la obra. Doble clic o «Terminar» para acabar.";
};

function terminarDibujo() {
  estado.dibujando = false;
  const ultima = estado.lineas[estado.lineas.length - 1];
  if (ultima && ultima.origen === "dibujo" && ultima.coords.length < 2) estado.lineas.pop();
  mapa.doubleClickZoom.enable();
  document.body.classList.remove("dibujando");
  $("btn-dibujar").classList.remove("activo");
  $("btn-dibujar").textContent = "Dibujar la obra";
  $("estado-dibujo").textContent = "";
  dibujarObra();
}

function agregarPunto(latlng) {
  const ultima = estado.lineas[estado.lineas.length - 1];
  ultima.coords.push([+latlng.lat.toFixed(6), +latlng.lng.toFixed(6)]);
  dibujarObra();
}

mapa.on("click", (e) => { if (estado.dibujando) agregarPunto(e.latlng); });
mapa.on("dblclick", () => { if (estado.dibujando) terminarDibujo(); });

$("btn-deshacer").onclick = () => {
  const ultima = estado.lineas[estado.lineas.length - 1];
  if (!ultima) return;
  if (ultima.origen === "dibujo" && ultima.coords.length > 0) ultima.coords.pop();
  if (ultima.coords.length === 0 || ultima.origen !== "dibujo") estado.lineas.pop();
  if (estado.lineas.length === 0) ponerEjemplo(null);
  limpiarPlan();
  dibujarObra();
};

$("btn-borrar").onclick = () => {
  if (estado.dibujando) terminarDibujo();
  estado.lineas = [];
  ponerEjemplo(null);
  limpiarPlan();
  dibujarObra();
};

function ponerEjemplo(ej) {
  estado.ejemplo = ej;
  $("aviso-ilustrativo").hidden = !ej?.ilustrativo;
}

function salirDeEjemplo() {
  if (estado.ejemplo) {
    ponerEjemplo(null);
    estado.lineas = [];
    limpiarPlan();
  }
}

const lineasListas = () => estado.lineas.filter((l) => l.coords.length >= 2).map((l) => l.coords);

function dibujarObra() {
  capaObra.clearLayers();
  for (const l of estado.lineas) {
    if (l.coords.length >= 2) {
      L.polyline(l.coords, { color: "white", weight: 10, opacity: 0.9, interactive: false }).addTo(capaObra);
      L.polyline(l.coords, { color: COLOR.obra, weight: 6, opacity: 0.9, interactive: false }).addTo(capaObra);
    }
    if (l.origen === "dibujo") {
      for (const p of l.coords) {
        L.circleMarker(p, { radius: 4, color: COLOR.obra, fillColor: "white", fillOpacity: 1, weight: 2, interactive: false })
          .addTo(capaObra);
      }
    }
  }
  $("btn-planificar").disabled = lineasListas().length === 0;
  marcarPasos();
}

// El menú marca cada paso como hecho cuando ya se cumplió.
function marcarPasos() {
  $("paso-municipio").classList.toggle("hecho", !!$("municipio").value || lineasListas().length > 0);
  $("paso-obra").classList.toggle("hecho", lineasListas().length > 0);
  $("paso-planificar").classList.toggle("hecho", !!estado.plan);
}

async function cargarEjemplo(url, nombrePorDefecto, ilustrativo) {
  if (estado.dibujando) terminarDibujo();
  mostrarEstado("Cargando el ejemplo…", false, true);
  try {
    const r = await fetch(url);
    const datos = await r.json();
    if (!r.ok) throw new Error(datos.error || `No se pudo cargar el ejemplo (${r.status}).`);
    const lineas = lista(datos.lineas).filter((l) => Array.isArray(l) && l.length >= 2);
    if (!lineas.length) throw new Error("El ejemplo no trae el eje de la obra.");
    estado.lineas = lineas.map((c) => ({ coords: c, origen: "ejemplo" }));
    ponerEjemplo({ nombre: nombrePorDefecto, ilustrativo: ilustrativo ?? !!datos.ilustrativo });
    limpiarPlan();
    dibujarObra();
    mapa.fitBounds(L.latLngBounds(lineas.flat()), { padding: [40, 40] });
    planificar();
  } catch (err) {
    mostrarEstado(err.message === "Failed to fetch" ? "No hay conexión con el servidor. ¿Está corriendo python app.py?" : err.message, true);
  }
}

$("btn-ejemplo").onclick = () => cargarEjemplo("/api/ejemplo", "Obra de canalización de El Salao (Soledad)", false);
$("btn-ejemplo-calle").onclick = () => cargarEjemplo("/api/ejemplo_obra", "Obra ilustrativa en la calle 72", true);

// ------------------------------------------------------------------ paso 3: planificar
$("btn-planificar").onclick = () => {
  if (estado.dibujando) terminarDibujo();
  planificar();
};

function mostrarEstado(texto, error = false, cargando = false) {
  const e = $("estado");
  e.textContent = texto;
  e.className = "estado" + (error ? " error" : "") + (cargando ? " cargando" : "");
}

let pedidoActual = 0;

async function planificar() {
  const lineas = lineasListas();
  if (!lineas.length) return;
  const miPedido = ++pedidoActual;
  $("btn-planificar").disabled = true;
  const inicio = performance.now();
  const avance = () => {
    const s = Math.round((performance.now() - inicio) / 1000);
    mostrarEstado(`Planificando la obra… ${s} s` + (s >= 8 ? " (si es una zona nueva, primero se descargan sus calles)" : ""), false, true);
  };
  avance();
  const reloj = setInterval(avance, 1000);
  try {
    const r = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lineas,
        etapa_max_m: +$("etapa-max").value,
        un_puente_cada_m: +$("puente-cada").value,
        cerrar_puentes: $("cerrar-puentes").checked,
        abiertos: [], cerrados: [],
      }),
    });
    let datos;
    try { datos = await r.json(); } catch { throw new Error(`El servidor respondió con un error (${r.status}).`); }
    if (!r.ok) throw new Error(datos?.error || `Error del servidor (${r.status}).`);
    if (miPedido !== pedidoActual) return;   // llegó tarde: ya se pidió otro plan
    estado.plan = datos;
    const t = datos.tiempos ? (num(datos.tiempos.red_s) ?? 0) + (num(datos.tiempos.plan_s) ?? 0) : null;
    mostrarEstado(t === null ? "Listo." : `Listo en ${t.toFixed(1)} s.`);
    mostrarPlan(datos);
  } catch (err) {
    if (miPedido !== pedidoActual) return;
    mostrarEstado(err.message === "Failed to fetch" ? "No hay conexión con el servidor. ¿Está corriendo python app.py?" : err.message, true);
  } finally {
    clearInterval(reloj);
    if (miPedido === pedidoActual) $("btn-planificar").disabled = lineasListas().length === 0;
    marcarPasos();
  }
}

function limpiarPlan() {
  pedidoActual++;
  terminarRecorrido();
  estado.plan = null;
  etapaVista = null;
  quitarSeleccion();
  leyenda.remove();
  capaPlan.clearLayers();
  piezas = [];
  capaObra.addTo(mapa);
  $("resultados").hidden = true;
  $("resultados").innerHTML = "";
  mostrarEstado("");
  marcarPasos();
}

// ------------------------------------------------------------------ capas del plan
// Cada pieza dibujada se registra con su capa (etapas, puentes, sentidos, rutas, carga) y su etapa,
// para que el recorrido pueda resaltar solo las capas de cada paso y atenuar lo demás.
const capaPlan = L.layerGroup().addTo(mapa);
let piezas = [];   // [{capa, etapa, layer}]

function registrar(capa, etapa, layer) {
  layer.addTo(capaPlan);
  piezas.push({ capa, etapa, layer });
  return layer;
}

// Puntos [lat, lon] válidos de una línea; [] si no es una línea.
function puntos(forma) {
  return lista(forma).filter((p) => Array.isArray(p) && num(p[0]) !== null && num(p[1]) !== null);
}
const punto = (p) => (Array.isArray(p) && num(p[0]) !== null && num(p[1]) !== null ? p : null);

function medio(forma) { return forma[Math.floor(forma.length / 2)]; }

function streetView(p) {
  return `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${p[0]},${p[1]}`;
}
const enlaceStreetView = (p, texto = "Ver en Street View") =>
  p ? `<a href="${streetView(p)}" target="_blank" rel="noopener">${texto}</a>` : "";

// Línea con borde, para que se lea sobre cualquier fondo del mapa.
function trazo(capa, etapa, forma, color, { peso = 5, borde = "white", dash = null, popup = null } = {}) {
  registrar(capa, etapa, L.polyline(forma, { color: borde, weight: peso + 4, opacity: 0.95, interactive: false, lineCap: "round", lineJoin: "round" }));
  const linea = registrar(capa, etapa, L.polyline(forma, { color, weight: peso, opacity: 1, dashArray: dash, lineCap: "round", lineJoin: "round" }));
  if (popup) linea.bindPopup(popup);
  return linea;
}

function marca(capa, etapa, p, html, clase, popup = null) {
  const m = registrar(capa, etapa, L.marker(p, {
    keyboard: false,
    icon: L.divIcon({ className: "", html: `<div class="pin ${clase}">${html}</div>`, iconSize: [26, 26], iconAnchor: [13, 13] }),
  }));
  if (popup) m.bindPopup(popup);
  return m;
}

const ejeDe = (e) => puntos(e?.eje ?? e?.cauce);
const numeroDe = (e, i) => num(e?.numero) ?? i + 1;
const etapasDe = (d) => lista(d?.etapas).filter((e) => e && typeof e === "object");

function dibujarPlan(d) {
  capaPlan.clearLayers();
  piezas = [];
  capaObra.remove();
  const etapas = etapasDe(d);

  // 1. etapas: el eje en tramos de colores.
  etapas.forEach((e, i) => {
    const n = numeroDe(e, i), eje = ejeDe(e);
    if (eje.length < 2) return;
    trazo("etapas", n, eje, colorEtapa(n), { peso: 8,
      popup: `<b>Etapa ${n}</b><br>Del metro ${fmt(e.inicio_m)} al ${fmt(e.fin_m)} (${fmt(e.longitud_m)} m).` });
    marca("etapas", n, medio(eje), n, "etapa", null).getElement()?.style.setProperty("--c", colorEtapa(n));
  });

  // 2. rutas alternas: carro amarilla, a pie verde punteada; el cruce cerrado en rojo.
  etapas.forEach((e, i) => {
    const n = numeroDe(e, i);
    for (const x of lista(e.rutas)) {
      const vistos = new Set();
      for (const modo of ["carro", "pie"]) {
        const cerrado = puntos(x?.[modo]?.cerrado);
        const clave = JSON.stringify(cerrado);
        if (cerrado.length >= 2 && !vistos.has(clave)) {
          vistos.add(clave);
          trazo("rutas", n, cerrado, COLOR.rojo, { peso: 6 });
        }
      }
      const carro = puntos(x?.carro?.forma), pie = puntos(x?.pie?.forma);
      const pop = popupRuta(x, n);
      if (carro.length >= 2) trazo("rutas", n, carro, COLOR.carro, { peso: 5, borde: COLOR.tinta, popup: pop });
      if (pie.length >= 2) trazo("rutas", n, pie, COLOR.pie, { peso: 4, dash: "2 8", popup: pop });
    }
  });

  // 3. cambios de sentido: calle morada.
  etapas.forEach((e, i) => {
    const n = numeroDe(e, i);
    for (const m of lista(e.vehiculos?.medidas)) {
      const forma = puntos(m?.forma);
      if (forma.length < 2) continue;
      trazo("sentidos", n, forma, COLOR.morado, { peso: 7,
        popup: `<b>Doble sentido: ${esc(m.via || "calle sin nombre")}</b><br>Etapa ${n}. De ${esc(m.desde)} a ${esc(m.hasta)}, ${fmt(m.metros)} m.<br>${enlaceStreetView(medio(forma))}` });
    }
  });

  // 4. pasos peatonales provisionales: marcadores naranja.
  etapas.forEach((e, i) => {
    const n = numeroDe(e, i);
    for (const p of lista(e.peatones?.puentes)) {
      const forma = puntos(p?.forma);
      if (!forma.length) continue;
      if (forma.length >= 2) trazo("puentes", n, forma, COLOR.naranja, { peso: 5, dash: "1 7" });
      marca("puentes", n, medio(forma), "🚶", "puente",
        `<b>Paso peatonal provisional ${esc(p.orden ?? "")}</b><br>Etapa ${n}. ${p.tipo === "cruce" ? `Devuelve el cruce de la ${esc(p.via)}.` : "Paso nuevo."}<br>
         Une ${esc(p.desde)} con ${esc(p.hasta)}${num(p.recorrido_m) !== null ? ` (${fmt(p.recorrido_m)} m)` : ""}.<br>${enlaceStreetView(medio(forma))}`);
    }
  });

  // 5. carga: esquinas que reciben recorridos desviados (rojo sin semáforo, verde con semáforo, gris sin dato).
  etapas.forEach((e, i) => {
    const n = numeroDe(e, i);
    for (const c of lista(e.carga)) {
      const p = punto(c?.posicion);
      if (!p) continue;
      const color = c.semaforo === true ? COLOR.verde : c.semaforo === false ? COLOR.rojo : COLOR.gris;
      const sem = c.semaforo === true ? "tiene semáforo" : c.semaforo === false ? "sin semáforo registrado" : "sin dato de semáforo";
      registrar("carga", n, L.circleMarker(p, { radius: 9, color: "white", weight: 2, fillColor: color, fillOpacity: 0.95 }))
        .bindPopup(`<b>${esc(c.nombre || "Esquina")}</b><br>Etapa ${n}: ${fmt(c.recorridos)} recorridos desviados pasan por aquí
          ${num(c.porcentaje) !== null ? `(${String(c.porcentaje).replace(".", ",")} %)` : ""}; ${sem}.<br>${enlaceStreetView(p)}`);
    }
  });
}

function popupRuta(x, n) {
  const fila = (quien, dato) => {
    if (!dato) return "";
    const con = num(dato.lluvia_m), sin = num(dato.seco_m);
    return `<br>${quien}: ${con === null ? "sin ruta abierta" : `${fmt(sin)} m → ${fmt(con)} m`}`;
  };
  const cerrado = puntos(x?.carro?.cerrado ?? x?.pie?.cerrado);
  return `<b>Ruta alterna: ${esc(x?.via || "cruce")}</b><br>Etapa ${n}.${fila("En carro", x?.carro)}${fila("A pie", x?.pie)}
    <br>${enlaceStreetView(cerrado.length ? medio(cerrado) : null, "Ver el cruce cerrado en Street View")}`;
}

// Resalta solo las capas pedidas (y, si se da, solo de esa etapa); lo demás queda con opacidad 0.2.
function resaltar(capas = null, etapa = null) {
  const todas = capas === null;
  const set = new Set(lista(capas));
  for (const { capa, etapa: n, layer } of piezas) {
    const activo = todas || (set.has(capa) && (etapa === null || n === etapa));
    const el = layer.getElement?.();
    if (!el) continue;
    el.style.opacity = activo ? "" : "0.2";
    el.classList.toggle("apagado", !activo);
  }
}

function limitesObra() {
  const pts = [...etapasDe(estado.plan).flatMap(ejeDe), ...lineasListas().flat()];
  return pts.length ? L.latLngBounds(pts) : null;
}

// ------------------------------------------------------------------ recorrido paso a paso
const rec = { pasos: [], i: 0, activo: false };

function iniciarRecorrido() {
  // Los pasos vienen del servidor (plan.pasos): se muestran tal cual, en su orden.
  rec.pasos = lista(estado.plan?.pasos).filter((p) => p && typeof p === "object");
  if (!rec.pasos.length) return;
  rec.i = 0;
  rec.activo = true;
  mapa.closePopup();
  document.body.classList.add("recorriendo");
  $("panel").inert = true;
  mapa.keyboard.disable();
  $("recorrido").hidden = false;
  $("rec-ilustrativo").hidden = !estado.ejemplo?.ilustrativo;
  mostrarPaso();
  $("rec-siguiente").focus();
}

function mostrarPaso() {
  const p = rec.pasos[rec.i], total = rec.pasos.length;
  const etapa = num(p.etapa);
  $("rec-contador").textContent = `Paso ${rec.i + 1} de ${total}`;
  $("rec-puntos").innerHTML = rec.pasos.map((_, j) => `<i class="${j === rec.i ? "actual" : j < rec.i ? "visto" : ""}"></i>`).join("");
  $("rec-cifra").textContent = p.cifra ?? "";
  $("rec-unidad").textContent = p.unidad ?? "";
  $("rec-titulo").textContent = p.titulo ?? "";
  $("rec-detalle").innerHTML = lista(p.detalle).map((t) => `<li>${esc(t)}</li>`).join("");

  // Avisos de la etapa del paso (por ejemplo, cuando no hay datos de peatones o de vehículos).
  const e = etapa === null ? null : etapasDe(estado.plan).find((x, i) => numeroDe(x, i) === etapa);
  const avisos = e ? lista(e.avisos) : [];
  $("rec-avisos").innerHTML = avisos.map((a) => `<div class="aviso">${esc(a)}</div>`).join("");

  const tarjeta = document.querySelector(".rec-tarjeta");
  tarjeta.style.setProperty("--c", etapa === null ? "var(--acento)" : colorEtapa(etapa));
  tarjeta.classList.remove("entra");
  void tarjeta.offsetWidth;   // reinicia la animación
  tarjeta.classList.add("entra");

  $("rec-anterior").disabled = rec.i === 0;
  $("rec-siguiente").textContent = rec.i === total - 1 ? "Terminar ✓" : "Siguiente →";

  resaltar(lista(p.capas), etapa);
  enfocar(p.foco);
}

// Mueve el mapa con una animación corta (o sin ella, si el sistema pide reducir el movimiento).
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)").matches;
function irA(limites, opciones) {
  if (sinMovimiento) mapa.fitBounds(limites, { ...opciones, animate: false });
  else mapa.flyToBounds(limites, opciones);
}

// Acerca el mapa a paso.foco, dentro de la parte del mapa que la tarjeta no tapa.
function enfocar(foco) {
  const a = punto(lista(foco)[0]), b = punto(lista(foco)[1]);
  const limites = a && b ? L.latLngBounds([a, b]) : limitesObra();
  if (!limites) return;
  const m = mapa.getContainer().getBoundingClientRect();
  const t = document.querySelector(".rec-tarjeta").getBoundingClientRect();
  const margen = 24;
  // Cuatro zonas libres posibles alrededor de la tarjeta; se usa la de mayor área.
  const zonas = [
    { izq: 0, arr: 0, der: m.right - t.left, aba: 0 },   // a la izquierda de la tarjeta
    { izq: t.right - m.left, arr: 0, der: 0, aba: 0 },   // a la derecha
    { izq: 0, arr: 0, der: 0, aba: m.bottom - t.top },   // arriba
    { izq: 0, arr: t.bottom - m.top, der: 0, aba: 0 },   // abajo
  ].map((z) => {
    for (const k in z) z[k] = Math.min(Math.max(0, z[k]), k === "izq" || k === "der" ? m.width : m.height);
    return { ...z, area: Math.max(0, m.width - z.izq - z.der) * Math.max(0, m.height - z.arr - z.aba) };
  });
  const z = zonas.reduce((x, y) => (y.area > x.area ? y : x));
  const pad = (v, lado) => Math.min(v + margen, lado - 60);
  irA(limites, {
    paddingTopLeft: [pad(z.izq, m.width), pad(z.arr, m.height)],
    paddingBottomRight: [pad(z.der, m.width), pad(z.aba, m.height)],
    maxZoom: 17, duration: 0.6,
  });
}

function siguientePaso() {
  if (rec.i < rec.pasos.length - 1) { rec.i++; mostrarPaso(); } else terminarRecorrido();
}
function pasoAnterior() {
  if (rec.i > 0) { rec.i--; mostrarPaso(); }
}

function terminarRecorrido() {
  if (!rec.activo) return;
  rec.activo = false;
  $("recorrido").hidden = true;
  document.body.classList.remove("recorriendo");
  $("panel").inert = false;
  mapa.keyboard.enable();
  if (estado.plan && $("selector-etapa")) verEtapa(etapaVista);   // vuelve a la vista normal
  else resaltar(null);
  $("resultados").scrollIntoView({ block: "start" });
  $("btn-repetir")?.focus({ preventScroll: true });
}

$("rec-siguiente").onclick = siguientePaso;
$("rec-anterior").onclick = pasoAnterior;
$("rec-saltar").onclick = terminarRecorrido;

document.addEventListener("keydown", (e) => {
  if (!rec.activo) return;
  if (e.key === "ArrowRight") { e.preventDefault(); siguientePaso(); }
  else if (e.key === "ArrowLeft") { e.preventDefault(); pasoAnterior(); }
  else if (e.key === "Escape") { e.preventDefault(); terminarRecorrido(); }
});

// ------------------------------------------------------------------ plan
function mostrarPlan(d) {
  dibujarPlan(d);
  pintarResultados(d);
  pintarLeyenda(d);
  iniciarRecorrido();
}

// ------------------------------------------------------------------ resultados en el panel
const pl = (n, uno, varios) => `${fmt(n)} ${num(n) === 1 ? uno : varios}`;
const avisosHtml = (xs) => lista(xs).map((a) => `<div class="aviso">${esc(a)}</div>`).join("");
const CAPAS = ["etapas", "puentes", "sentidos", "rutas", "carga"];
let etapaVista = null;   // null = todas

function cifra(valor, texto, extra = "") {
  return `<div class="cifra"><b>${valor}</b><span>${texto}</span>${extra ? `<small>${extra}</small>` : ""}</div>`;
}

function pintarResultados(d) {
  const r = $("resultados");
  const s = d.resumen ?? {};
  const etapas = etapasDe(d);
  const nEtapas = num(s.etapas) ?? etapas.length;
  const largo = num(s.longitud_m) ?? num(d.obra?.longitud_m) ?? num(d.arroyo?.longitud_m);
  const sinSem = num(s.esquinas_sin_semaforo);
  r.hidden = false;
  r.innerHTML = `
    <h2><span class="num">✓</span> Plan de la obra</h2>
    ${estado.ejemplo ? `<p class="obra-nombre">${esc(estado.ejemplo.nombre)}</p>` : ""}
    ${estado.ejemplo?.ilustrativo ? `<div class="aviso">Ejemplo ilustrativo, no es una obra real.</div>` : ""}
    <div class="cifras" id="cifras">
      ${cifra(fmt(nEtapas), num(nEtapas) === 1 ? "etapa de obra" : "etapas de obra")}
      ${cifra(largo === null ? "—" : `${fmt(largo)} m`, "de obra")}
      ${cifra(fmt(s.puentes_peatonales), num(s.puentes_peatonales) === 1 ? "paso peatonal provisional" : "pasos peatonales provisionales")}
      ${cifra(fmt(s.cambios_de_sentido), num(s.cambios_de_sentido) === 1 ? "calle a doble sentido" : "calles a doble sentido")}
      ${cifra(fmt(s.rutas_alternas), num(s.rutas_alternas) === 1 ? "ruta alterna" : "rutas alternas")}
      ${cifra(fmt(s.esquinas_de_control), "esquinas para controlar", sinSem === null ? "" : `${fmt(sinSem)} sin semáforo`)}
    </div>
    <div class="botones dos">
      <button id="btn-repetir" class="sec" type="button">↺ Repetir el recorrido</button>
      <button id="btn-ver-todo" class="sec" type="button">Ver toda la obra</button>
    </div>
    ${lista(d.pasos).length ? "" : `<div class="aviso">El servidor no envió pasos para el recorrido.</div>`}
    <h3>Etapas</h3>
    <div id="selector-etapa" class="selector" role="tablist" aria-label="Etapa">
      <button type="button" role="tab" data-etapa="">Todas</button>
      ${etapas.map((e, i) => { const n = numeroDe(e, i); return `<button type="button" role="tab" data-etapa="${n}" style="--c:${colorEtapa(n)}">${n}</button>`; }).join("")}
    </div>
    <div id="detalle-etapa"></div>
    <p class="nota">Cómo leer esto: para cada par de esquinas a lados opuestos de la obra se calcula el camino más
      corto antes y durante la obra (algoritmo de Dijkstra); el desvío es la diferencia. No hay datos de volumen
      de tránsito: no se mide congestión.</p>
    <p class="nota">${d.fuente ? `Fuente del mapa: ${esc(d.fuente)}. ` : ""}${num(d.tiempos?.plan_s) !== null ? `Cálculo: ${d.tiempos.plan_s} s.` : ""}</p>`;

  $("btn-repetir").onclick = iniciarRecorrido;
  $("btn-ver-todo").onclick = () => verEtapa(null);
  $("selector-etapa").querySelectorAll("button").forEach((b) => {
    b.onclick = () => verEtapa(b.dataset.etapa ? +b.dataset.etapa : null);
  });
  verEtapa(null, false);
}

// Muestra en el panel una etapa (o todas) y la resalta en el mapa.
function verEtapa(n, mover = true) {
  etapaVista = n;
  quitarSeleccion();
  const d = estado.plan;
  const etapas = etapasDe(d);
  $("selector-etapa").querySelectorAll("button").forEach((b) => {
    const activo = (b.dataset.etapa ? +b.dataset.etapa : null) === n;
    b.classList.toggle("activo", activo);
    b.setAttribute("aria-selected", activo);
  });
  const caja = $("detalle-etapa");
  if (n === null) {
    caja.innerHTML = `<ul class="lista" id="lista-etapas">${etapas.map((e, i) => filaEtapa(e, numeroDe(e, i))).join("")}</ul>`;
    caja.querySelectorAll("li[data-etapa]").forEach((li) => {
      const ir = () => verEtapa(+li.dataset.etapa);
      li.onclick = ir;
      li.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); ir(); } };
    });
    resaltar(null);
    if (mover) { const l = limitesObra(); if (l) irA(l, { padding: [40, 40], maxZoom: 17, duration: 0.5 }); }
    return;
  }
  const e = etapas.find((x, i) => numeroDe(x, i) === n);
  if (!e) return verEtapa(null, mover);
  caja.innerHTML = tarjetaEtapa(e, n);
  enlazar(caja, "[data-ruta]", (i) => mostrarRuta(lista(e.rutas)[i], n));
  enlazar(caja, "[data-puente]", (i) => mostrarPieza(lista(e.peatones?.puentes)[i]?.forma, "puentes", n));
  enlazar(caja, "[data-sentido]", (i) => mostrarPieza(lista(e.vehiculos?.medidas)[i]?.forma, "sentidos", n));
  enlazar(caja, "[data-esquina]", (i) => mostrarPieza([lista(e.carga)[i]?.posicion], "carga", n));
  resaltar(CAPAS, n);
  const eje = ejeDe(e);
  if (mover && eje.length) irA(L.latLngBounds(eje), { padding: [40, 40], maxZoom: 17, duration: 0.5 });
}

function filaEtapa(e, n) {
  const ped = e.peatones, veh = e.vehiculos;
  return `<li data-etapa="${n}" tabindex="0" style="--c:${colorEtapa(n)}" class="clic">
    <div class="fila-tit"><b>Etapa ${n}</b><span>metro ${fmt(e.inicio_m)} al ${fmt(e.fin_m)} · ${fmt(e.longitud_m)} m</span></div>
    <small>${pl(e.cruces_cerrados, "cruce cerrado", "cruces cerrados")} ·
      ${pl(lista(ped?.puentes).length, "paso peatonal", "pasos peatonales")} ·
      ${pl(lista(veh?.medidas).length, "cambio de sentido", "cambios de sentido")} ·
      ${pl(lista(e.rutas).length, "ruta alterna", "rutas alternas")}</small>
    ${avisosHtml(e.avisos)}${ped === null || veh === null ? `<div class="aviso">${ped === null ? "Sin datos de peatones" : "Sin datos de vehículos"} en esta etapa.</div>` : ""}
  </li>`;
}

// Barra de antes / durante la obra / con las medidas, para el desvío medio.
function comparacion(titulo, m0, m1, conQue, clase) {
  if (!m0) return "";
  const a = num(m0.desvio_medio_m), b = num(m1?.desvio_medio_m);
  const max = Math.max(1, a ?? 0, b ?? 0);
  const barra = (nombre, v, cls) => v === null ? "" : `
    <div class="barra-fila"><span class="barra-nombre">${nombre}</span>
      <span class="barra-pista"><span class="barra ${cls}" style="width:${Math.max(1.5, (100 * v) / max)}%"></span></span>
      <span class="barra-valor">${fmt(v)} m</span></div>`;
  const sin0 = num(m0.sin_camino), sin1 = num(m1?.sin_camino);
  return `<div class="comparacion"><div class="comp-tit">${titulo}: desvío medio</div>
    ${barra("Con la obra", a, "gris")}${barra(conQue, b, clase)}
    ${sin0 ? `<div class="nota">Pares que se quedan sin camino: <b>${fmt(sin0)}${sin1 !== null ? ` → ${fmt(sin1)}` : ""}</b></div>` : ""}</div>`;
}

function tarjetaEtapa(e, n) {
  const ped = e.peatones, veh = e.vehiculos;
  const puentes = lista(ped?.puentes), medidas = lista(veh?.medidas), rutas = lista(e.rutas), carga = lista(e.carga);
  const item = (attr, i, html) => `<li ${attr}="${i}" tabindex="0" class="clic">${html}</li>`;
  let h = `<div class="tarjeta" style="--c:${colorEtapa(n)}">
    <div class="tarjeta-tit"><span class="chip">Etapa ${n}</span>
      metro ${fmt(e.inicio_m)} al ${fmt(e.fin_m)} · ${fmt(e.longitud_m)} m</div>
    <p class="nota">Se cierran <b>${pl(e.cruces_cerrados, "cruce", "cruces")}</b>${num(e.puentes_existentes_cerrados) ? `, ${pl(e.puentes_existentes_cerrados, "de ellos un puente existente", "de ellos puentes existentes")}` : ""}.
      ${num(e.recorridos_desviados) !== null ? `${fmt(e.recorridos_desviados)} recorridos de la muestra se desvían.` : ""}</p>
    ${avisosHtml(e.avisos)}
    ${ped === null ? `<div class="aviso">Esta etapa no trae datos de peatones.</div>` : comparacion("A pie", ped?.obra, ped?.con_puentes, `Con ${pl(puentes.length, "paso", "pasos")}`, "naranja")}
    ${veh === null ? `<div class="aviso">Esta etapa no trae datos de vehículos.</div>` : comparacion("En carro o moto", veh?.obra, veh?.con_medidas, `Con ${pl(medidas.length, "cambio", "cambios")}`, "morado")}`;

  if (puentes.length) {
    h += `<h4><i class="ico puente"></i>Pasos peatonales provisionales</h4><ul class="lista mini-lista">${puentes.map((p, i) => item("data-puente", i,
      `<b>${esc(p.orden ?? i + 1)}.</b> ${p.tipo === "cruce" ? `Cruce de la ${esc(p.via)}` : "Paso nuevo"}: entre ${esc(p.desde)} y ${esc(p.hasta)}
       <small>${num(p.recorrido_m) !== null ? `${fmt(p.recorrido_m)} m` : ""}${num(p.desvio_medio_m) !== null ? ` · desvío a pie queda en ${fmt(p.desvio_medio_m)} m` : ""}</small>`)).join("")}</ul>`;
  }
  if (medidas.length) {
    h += `<h4><i class="ico sentido"></i>Calles a doble sentido</h4><ul class="lista mini-lista">${medidas.map((m, i) => item("data-sentido", i,
      `<b>${esc(m.orden ?? i + 1)}.</b> ${esc(m.via || "Calle sin nombre")} <small>de ${esc(m.desde)} a ${esc(m.hasta)}${num(m.metros) !== null ? ` · ${fmt(m.metros)} m` : ""}</small>`)).join("")}</ul>`;
  }
  if (rutas.length) {
    const max = Math.max(1, ...rutas.flatMap((x) => [extra(x.carro), extra(x.pie)]));
    h += `<h4><i class="ico ruta"></i>Rutas alternas para señalizar</h4>
      <p class="nota">Cruces que la obra cierra y cuánto más hay que recorrer por el camino más corto que queda. Toque uno para verlo en el mapa.</p>
      <div class="leyenda-mini"><span><i class="mini-barra carro"></i>En carro</span><span><i class="mini-barra pie"></i>A pie</span></div>
      <ul class="lista mini-lista">${rutas.map((x, i) => item("data-ruta", i,
      `<b>${esc(x.via || "Cruce")}</b>${miniBarra("En carro", x.carro, "carro", max)}${miniBarra("A pie", x.pie, "pie", max)}`)).join("")}</ul>`;
  }
  if (carga.length) {
    h += `<h4><i class="ico esquina"></i>Esquinas que reciben más recorridos desviados</h4><ul class="lista mini-lista">${carga.map((c, i) => item("data-esquina", i,
      `<i class="semaforo ${c.semaforo === true ? "si" : c.semaforo === false ? "no" : "nd"}"></i><b>${esc(c.nombre || "Esquina")}</b>
       <small>${fmt(c.recorridos)} recorridos${num(c.porcentaje) !== null ? ` (${String(c.porcentaje).replace(".", ",")} %)` : ""} ·
       ${c.semaforo === true ? "tiene semáforo" : c.semaforo === false ? "sin semáforo registrado" : "sin dato de semáforo"}</small>`)).join("")}</ul>`;
  }
  return h + "</div>";
}

function extra(dato) {
  const a = num(dato?.seco_m), b = num(dato?.lluvia_m);
  return a !== null && b !== null ? Math.max(0, b - a) : 0;
}

function miniBarra(quien, dato, clase, max) {
  if (!dato) return "";
  if (num(dato.lluvia_m) === null) {
    return `<div class="mini"><span class="mini-nombre">${quien}</span><span class="mini-texto">no queda camino abierto</span></div>`;
  }
  const x = extra(dato);
  return `<div class="mini" title="${quien}: ${fmt(dato.seco_m)} m antes de la obra, ${fmt(dato.lluvia_m)} m con la obra">
    <span class="mini-nombre">${quien}</span>
    <span class="mini-pista"><span class="mini-barra ${clase}" style="width:${Math.max(1.5, (100 * x) / max)}%"></span></span>
    <span class="mini-valor">+${fmt(x)} m</span></div>`;
}

function enlazar(caja, selector, accion) {
  caja.querySelectorAll(selector).forEach((li) => {
    const attr = selector.slice(1, -1);
    const elegir = () => {
      const yaEstaba = li.classList.contains("sel");
      if (yaEstaba) return verEtapa(etapaVista);   // segundo clic: volver a la etapa
      quitarSeleccion();
      li.classList.add("sel");
      accion(+li.getAttribute(attr));
    };
    li.onclick = elegir;
    li.onkeydown = (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); elegir(); } };
  });
}

// ------------------------------------------------------------------ una ruta o pieza elegida en la lista
const capaRuta = L.layerGroup().addTo(mapa);

const detalle = L.control({ position: "topright" });
detalle.onAdd = () => {
  const d = L.DomUtil.create("div", "detalle");
  d.hidden = true;
  L.DomEvent.disableClickPropagation(d);
  L.DomEvent.disableScrollPropagation(d);
  return d;
};
detalle.addTo(mapa);

function quitarSeleccion() {
  capaRuta.clearLayers();
  mapa.closePopup();
  const caja = detalle.getContainer();
  caja.hidden = true;
  caja.innerHTML = "";
  document.querySelectorAll("#resultados li.sel").forEach((x) => x.classList.remove("sel"));
  if (estado.plan) resaltar(etapaVista === null ? null : CAPAS, etapaVista);
}

function pinRuta(p, texto, clase) {
  return L.marker(p, {
    keyboard: false,
    icon: L.divIcon({ className: "", html: `<div class="pin ${clase}">${texto}</div>`, iconSize: [26, 26], iconAnchor: [13, 13] }),
  }).addTo(capaRuta);
}

function lineaRuta(forma, color, { peso = 5, borde = "white", dash = null } = {}) {
  L.polyline(forma, { color: borde, weight: peso + 4, opacity: 0.95, interactive: false, lineCap: "round", lineJoin: "round" }).addTo(capaRuta);
  L.polyline(forma, { color, weight: peso, opacity: 1, dashArray: dash, interactive: false, lineCap: "round", lineJoin: "round" }).addTo(capaRuta);
}

function encuadrar(pts) {
  if (!pts.length) return;
  const ancho = mapa.getSize().x;
  const der = ancho > 600 ? Math.min(330, ancho / 2) : 20;   // deja sitio al recuadro de detalle
  irA(L.latLngBounds(pts), { paddingTopLeft: [40, 40], paddingBottomRight: [der, 40], maxZoom: 18, duration: 0.5 });
}

function filaDetalle(clase, quien, dato) {
  if (!dato) return "";
  const antes = num(dato.seco_m), con = num(dato.lluvia_m);
  if (con === null) {
    return `<div class="det-fila"><i class="${clase}"></i><span>${quien}</span><span>${fmt(antes)} m antes de la obra</span><b>no queda camino abierto</b></div>`;
  }
  const veces = antes > 0 ? con / antes : 0;
  return `<div class="det-fila"><i class="${clase}"></i><span>${quien}</span>
    <span>${fmt(antes)} m antes → ${fmt(con)} m con la obra</span>
    <b>+${fmt(con - antes)} m${veces >= 1.5 ? ` <small>(${veces.toFixed(1).replace(".", ",")} veces)</small>` : ""}</b></div>`;
}

// Una ruta alterna: cruce cerrado en rojo, ruta en carro amarilla, ruta a pie verde punteada.
function mostrarRuta(x, n) {
  if (!x) return;
  resaltar([], null);   // todo el plan atenuado: así el cruce y las dos rutas se distinguen
  const datos = [["carro", "En carro", x.carro], ["pie", "A pie", x.pie]].filter(([, , d]) => d);
  const todos = [];
  const vistos = new Set();
  let base = null;
  for (const [, , d] of datos) {
    const cerrado = puntos(d.cerrado);
    if (cerrado.length < 2) continue;
    base ??= { ...d, cerrado };
    const clave = JSON.stringify(cerrado);
    if (vistos.has(clave)) continue;
    vistos.add(clave);
    lineaRuta(cerrado, COLOR.rojo, { peso: 7 });
    pinRuta(medio(cerrado), "✕", "cerrado").bindTooltip("Cruce cerrado por la obra", { direction: "top" });
    todos.push(...cerrado);
  }
  const carro = puntos(x.carro?.forma), pie = puntos(x.pie?.forma);
  if (carro.length >= 2) { lineaRuta(carro, COLOR.carro, { peso: 6, borde: COLOR.tinta }); todos.push(...carro); }
  if (pie.length >= 2) { lineaRuta(pie, COLOR.pie, { peso: 4, dash: "2 8" }); todos.push(...pie); }
  if (base) {
    pinRuta(base.cerrado[0], "A", "extremo").bindTooltip(esc(base.desde || "Origen"), { direction: "top" });
    pinRuta(base.cerrado[base.cerrado.length - 1], "B", "extremo").bindTooltip(esc(base.hasta || "Destino"), { direction: "top" });
  }
  mostrarDetalle(`
    <div class="det-tit">${esc(x.via || "Cruce cerrado")}</div>
    <div class="det-sub">Etapa ${n}. ${base ? `Cruce que la obra cierra, de <b>A</b> (${esc(base.desde)}) a <b>B</b> (${esc(base.hasta)}).` : ""}
      Camino más corto que queda abierto:</div>
    ${datos.map(([clase, quien, d]) => filaDetalle(clase, quien, d)).join("")}
    <div class="det-leyenda"><span><i class="l-cerrado"></i>Cruce cerrado</span><span><i class="l-carro"></i>En carro</span><span><i class="l-pie"></i>A pie</span></div>
    <div class="det-nota">Esto es lo que habría que señalizar. ${enlaceStreetView(base ? medio(base.cerrado) : null, "Ver el cruce en Street View")}</div>`);
  encuadrar(todos);
}

function mostrarPieza(forma, capa, n) {
  const pts = puntos(forma);
  if (!pts.length) return;
  resaltar([capa], n);
  // Abre la ventana de la pieza (la que tiene popup) más cercana a su centro.
  const centro = L.latLng(medio(pts));
  const cand = piezas.filter((x) => x.capa === capa && x.etapa === n && x.layer.getPopup());
  const pos = (l) => (l.getLatLng ? l.getLatLng() : L.latLngBounds(l.getLatLngs()).getCenter());
  const elegida = cand.sort((a, b) => pos(a.layer).distanceTo(centro) - pos(b.layer).distanceTo(centro))[0];
  encuadrar(pts.length === 1 ? [[pts[0][0] - 0.0015, pts[0][1] - 0.0015], [pts[0][0] + 0.0015, pts[0][1] + 0.0015]] : pts);
  if (elegida) setTimeout(() => elegida.layer.openPopup(), sinMovimiento ? 0 : 550);
}

function mostrarDetalle(html) {
  const caja = detalle.getContainer();
  caja.innerHTML = `${html}<button class="ver-todo" type="button">Volver a la etapa</button>`;
  caja.hidden = false;
  caja.querySelector(".ver-todo").onclick = () => verEtapa(etapaVista);
}

// ------------------------------------------------------------------ leyenda del mapa
const leyenda = L.control({ position: "bottomright" });
leyenda.onAdd = () => {
  const d = L.DomUtil.create("details", "leyenda");
  L.DomEvent.disableClickPropagation(d);
  return d;
};

function pintarLeyenda(d) {
  if (!leyenda.getContainer()) leyenda.addTo(mapa);
  const caja = leyenda.getContainer();
  caja.open = window.innerWidth > 700;
  const etapas = etapasDe(d);
  caja.innerHTML = `<summary>Leyenda</summary>
    <div>${etapas.map((e, i) => `<i class="cuadro" style="background:${colorEtapa(numeroDe(e, i))}"></i>`).join("")}Eje de la obra por etapa</div>
    <div><i class="pin-mini puente"></i>Paso peatonal provisional</div>
    <div><i class="linea" style="background:${COLOR.morado}"></i>Calle a doble sentido</div>
    <div><i class="linea" style="background:${COLOR.rojo}"></i>Cruce cerrado</div>
    <div><i class="linea ruta-carro"></i>Ruta alterna en carro</div>
    <div><i class="linea ruta-pie"></i>Ruta alterna a pie</div>
    <div class="sep"><i class="circ" style="background:${COLOR.rojo}"></i>Esquina sin semáforo</div>
    <div><i class="circ" style="background:${COLOR.verde}"></i>Esquina con semáforo</div>
    <div><i class="circ" style="background:${COLOR.gris}"></i>Sin dato de semáforo</div>`;
}

// http://localhost:5000/?ejemplo abre la página con El Salao ya planificado (útil en la presentación).
if (new URLSearchParams(location.search).has("ejemplo")) $("btn-ejemplo").click();
