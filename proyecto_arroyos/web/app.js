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
  resaltar(null);
  const limites = limitesObra();
  if (limites) irA(limites, { padding: [40, 40], maxZoom: 17, duration: 0.6 });
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
  iniciarRecorrido();
}

function pintarResultados(d) {
  const r = $("resultados");
  const s = d.resumen ?? {};
  r.hidden = false;
  let html = `<h2><span class="num">✓</span> Plan de la obra</h2>
    <button id="btn-repetir" class="sec ancho" type="button">↺ Repetir el recorrido</button>
    <p class="nota">${fmt(s.etapas)} etapas, ${fmt(s.puentes_peatonales)} pasos peatonales provisionales,
      ${fmt(s.cambios_de_sentido)} cambios de sentido y ${fmt(s.rutas_alternas)} rutas alternas.</p>
    <ul class="lista" id="lista-etapas">`;
  etapasDe(d).forEach((e, i) => {
    const n = numeroDe(e, i);
    html += `<li style="--c:${colorEtapa(n)}"><b>Etapa ${n}</b> · del metro ${fmt(e.inicio_m)} al ${fmt(e.fin_m)}
      ${lista(e.avisos).map((a) => `<div class="aviso">${esc(a)}</div>`).join("")}</li>`;
  });
  r.innerHTML = html + "</ul>";
  $("btn-repetir").onclick = iniciarRecorrido;
}

// http://localhost:5000/?ejemplo abre la página con El Salao ya planificado (útil en la presentación).
if (new URLSearchParams(location.search).has("ejemplo")) $("btn-ejemplo").click();
