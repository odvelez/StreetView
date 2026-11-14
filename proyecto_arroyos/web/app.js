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
const mapa = L.map("mapa", { zoomControl: true }).setView([10.9636, -74.7964], 13);
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
  estado.plan = null;
  $("resultados").hidden = true;
  $("resultados").innerHTML = "";
  mostrarEstado("");
  marcarPasos();
}

// ------------------------------------------------------------------ plan
function mostrarPlan(d) {
  const r = $("resultados");
  const s = d.resumen ?? {};
  r.hidden = false;
  r.innerHTML = `<h2><span class="num">✓</span> Plan de la obra</h2>
    <p class="nota">${fmt(s.etapas)} etapas, ${fmt(s.puentes_peatonales)} pasos peatonales provisionales,
      ${fmt(s.cambios_de_sentido)} cambios de sentido y ${fmt(s.rutas_alternas)} rutas alternas.</p>`;
}

// http://localhost:5000/?ejemplo abre la página con El Salao ya planificado (útil en la presentación).
if (new URLSearchParams(location.search).has("ejemplo")) $("btn-ejemplo").click();
