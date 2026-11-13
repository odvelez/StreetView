// Mapa interactivo: el usuario marca un arroyo, el servidor lo analiza y aquí se dibujan los resultados.

const COLOR = {
  azul: "#2a78b5", azulClaro: "#7fb6e0", rojo: "#c4362f", verde: "#1b8a5a",
  naranja: "#d9730d", morado: "#7b3fb0", gris: "#8a8f93",
  carro: "#e8a100", pie: "#199e70", tinta: "#1f2a30",
};

const $ = (id) => document.getElementById(id);
const fmt = (x) => Math.round(x).toLocaleString("es-CO");
const pct = (m) => `${m.pct_mayor_200m.toFixed(0)} %`;

// ------------------------------------------------------------------ mapa base
const mapa = L.map("mapa", { zoomControl: true }).setView([10.9636, -74.7964], 13);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>',
}).addTo(mapa);

const capaOSM = L.layerGroup().addTo(mapa);
const capaArroyo = L.layerGroup().addTo(mapa);
const capaResultado = L.layerGroup().addTo(mapa);
const capaRuta = L.layerGroup().addTo(mapa);

const leyenda = L.control({ position: "bottomright" });
leyenda.onAdd = () => {
  const d = L.DomUtil.create("div", "leyenda");
  d.innerHTML = `
    <div><i style="background:${COLOR.azulClaro}"></i>Arroyos de OpenStreetMap</div>
    <div><i style="background:${COLOR.azul};height:6px"></i>Arroyo analizado</div>
    <div><i style="background:${COLOR.rojo}"></i>Calle bloqueada con lluvia</div>
    <div><i style="background:${COLOR.verde}"></i>Puente existente</div>
    <div><i style="background:${COLOR.naranja}"></i>Puente peatonal propuesto</div>
    <div><i style="background:${COLOR.morado}"></i>Calle a doble sentido</div>
    <div class="sep"><i class="ruta-carro"></i>Ruta alterna en carro</div>
    <div><i class="ruta-pie"></i>Ruta alterna a pie</div>`;
  return d;
};
leyenda.addTo(mapa);

// Recuadro con el detalle de lo que se seleccionó en la lista de resultados.
const detalle = L.control({ position: "topright" });
detalle.onAdd = () => {
  const d = L.DomUtil.create("div", "detalle");
  d.hidden = true;
  L.DomEvent.disableClickPropagation(d);
  L.DomEvent.disableScrollPropagation(d);
  return d;
};
detalle.addTo(mapa);

// ------------------------------------------------------------------ estado
const estado = {
  lineas: [],          // [{coords: [[lat, lon], ...], origen: "osm" | "dibujo" | "ejemplo", id}]
  dibujando: false,
  ejemplo: false,
  abiertos: new Set(), // tramos que el usuario marcó como transitables
  cerrados: new Set(), // tramos que el usuario marcó como bloqueados
  resultado: null,
};
let arroyosOSM = [];

// ------------------------------------------------------- arroyos de OpenStreetMap
fetch("/api/arroyos")
  .then((r) => r.json())
  .then((datos) => {
    arroyosOSM = datos.arroyos;
    for (const a of arroyosOSM) {
      const linea = L.polyline(a.coords, { color: COLOR.azulClaro, weight: 4, opacity: 0.85, className: "osm" });
      linea.on("click", (e) => {
        L.DomEvent.stopPropagation(e);
        if (estado.dibujando) return agregarPunto(e.latlng);
        popupArroyo(a, e.latlng);
      });
      linea.addTo(capaOSM);
    }
  })
  .catch(() => mostrarEstado("No se pudo cargar la capa de arroyos.", true));

function popupArroyo(a, latlng) {
  const div = document.createElement("div");
  const nombre = a.nombre || "Cauce sin nombre";
  const mismos = a.nombre ? arroyosOSM.filter((x) => x.nombre === a.nombre) : [a];
  div.innerHTML = `<b>${nombre}</b><br><small>Tipo en OpenStreetMap: ${a.tipo}</small><br>`;
  const b1 = document.createElement("button");
  b1.textContent = "Usar este tramo";
  b1.onclick = () => { usarArroyos([a]); mapa.closePopup(); };
  div.appendChild(b1);
  if (mismos.length > 1) {
    const b2 = document.createElement("button");
    b2.textContent = `Usar todo el arroyo (${mismos.length} tramos)`;
    b2.style.marginLeft = "4px";
    b2.onclick = () => { usarArroyos(mismos); mapa.closePopup(); };
    div.appendChild(b2);
  }
  L.popup().setLatLng(latlng).setContent(div).openOn(mapa);
}

function usarArroyos(lista) {
  salirDeEjemplo();
  for (const a of lista) {
    if (!estado.lineas.some((l) => l.origen === "osm" && l.id === a.id)) {
      estado.lineas.push({ coords: a.coords, origen: "osm", id: a.id });
    }
  }
  dibujarArroyo();
  mapa.fitBounds(L.latLngBounds(estado.lineas.flatMap((l) => l.coords)), { padding: [40, 40] });
}

// ------------------------------------------------------------------ dibujo
$("btn-dibujar").onclick = () => {
  if (estado.dibujando) return terminarDibujo();
  salirDeEjemplo();
  estado.dibujando = true;
  estado.lineas.push({ coords: [], origen: "dibujo" });
  mapa.doubleClickZoom.disable();
  document.body.classList.add("dibujando");
  $("btn-dibujar").classList.add("activo");
  $("btn-dibujar").textContent = "Terminar";
  $("estado-dibujo").textContent = "Haga clic sobre el mapa siguiendo el cauce. Doble clic o «Terminar» para acabar.";
};

function terminarDibujo() {
  estado.dibujando = false;
  const ultima = estado.lineas[estado.lineas.length - 1];
  if (ultima && ultima.origen === "dibujo" && ultima.coords.length < 2) estado.lineas.pop();
  mapa.doubleClickZoom.enable();
  document.body.classList.remove("dibujando");
  $("btn-dibujar").classList.remove("activo");
  $("btn-dibujar").textContent = "Dibujar";
  $("estado-dibujo").textContent = "";
  dibujarArroyo();
}

function agregarPunto(latlng) {
  const ultima = estado.lineas[estado.lineas.length - 1];
  ultima.coords.push([+latlng.lat.toFixed(6), +latlng.lng.toFixed(6)]);
  dibujarArroyo();
}

mapa.on("click", (e) => { if (estado.dibujando) agregarPunto(e.latlng); });
mapa.on("dblclick", () => { if (estado.dibujando) terminarDibujo(); });

$("btn-deshacer").onclick = () => {
  const ultima = estado.lineas[estado.lineas.length - 1];
  if (!ultima) return;
  if (ultima.origen === "dibujo" && ultima.coords.length > 0) ultima.coords.pop();
  if (ultima.coords.length === 0 || ultima.origen !== "dibujo") estado.lineas.pop();
  if (estado.lineas.length === 0) estado.ejemplo = false;
  dibujarArroyo();
};

$("btn-borrar").onclick = () => {
  if (estado.dibujando) terminarDibujo();
  estado.lineas = [];
  estado.ejemplo = false;
  limpiarResultado();
  dibujarArroyo();
};

function salirDeEjemplo() {
  if (estado.ejemplo) {
    estado.ejemplo = false;
    estado.lineas = [];
    limpiarResultado();
  }
}

function dibujarArroyo(cambio = true) {
  // Si cambia el arroyo, las correcciones hechas a mano dejan de aplicar.
  if (cambio && !estado.ejemplo) { estado.abiertos.clear(); estado.cerrados.clear(); }
  capaArroyo.clearLayers();
  for (const l of estado.lineas) {
    if (l.coords.length >= 2) {
      L.polyline(l.coords, { color: COLOR.azul, weight: 7, opacity: 0.8, interactive: false }).addTo(capaArroyo);
    }
    if (l.origen === "dibujo") {
      for (const p of l.coords) {
        L.circleMarker(p, { radius: 4, color: COLOR.azul, fillColor: "white", fillOpacity: 1, weight: 2, interactive: false })
          .addTo(capaArroyo);
      }
    }
  }
  const listo = estado.lineas.some((l) => l.coords.length >= 2);
  $("btn-analizar").disabled = !listo;
}

$("municipio").onchange = (e) => {
  if (!e.target.value) return;
  const [lat, lon, z] = e.target.value.split(",").map(Number);
  mapa.setView([lat, lon], z);
};

$("btn-ejemplo").onclick = async () => {
  if (estado.dibujando) terminarDibujo();
  const r = await fetch("/api/ejemplo").then((x) => x.json());
  estado.lineas = r.lineas.map((c) => ({ coords: c, origen: "ejemplo" }));
  estado.ejemplo = true;
  estado.abiertos.clear();
  estado.cerrados.clear();
  limpiarResultado();
  dibujarArroyo();
  mapa.fitBounds(L.latLngBounds(r.lineas.flat()), { padding: [40, 40] });
  analizar();
};

// ------------------------------------------------------------------ análisis
$("btn-analizar").onclick = () => {
  if (estado.dibujando) terminarDibujo();
  analizar();
};

function mostrarEstado(texto, error = false, cargando = false) {
  const e = $("estado");
  e.textContent = texto;
  e.className = "estado" + (error ? " error" : "") + (cargando ? " cargando" : "");
}

async function analizar() {
  const lineas = estado.lineas.filter((l) => l.coords.length >= 2).map((l) => l.coords);
  if (!lineas.length) return;
  $("btn-analizar").disabled = true;
  const inicio = performance.now();
  const avance = () => {
    const s = Math.round((performance.now() - inicio) / 1000);
    mostrarEstado(`Analizando… ${s} s` + (s >= 8 ? " (si es una zona nueva, primero se descargan sus calles)" : ""), false, true);
  };
  avance();
  const reloj = setInterval(avance, 1000);
  try {
    const r = await fetch("/api/analizar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lineas, radio: +$("radio").value, luz_max: +$("luz").value, k: +$("k").value,
        abiertos: [...estado.abiertos], cerrados: [...estado.cerrados],
      }),
    });
    let datos;
    try { datos = await r.json(); } catch { throw new Error(`El servidor respondió con un error (${r.status}).`); }
    if (!r.ok) throw new Error(datos.error || "Error del servidor");
    estado.resultado = datos;
    mostrarEstado(`Listo en ${(datos.tiempos.red_s + datos.tiempos.analisis_s).toFixed(1)} s.`);
    pintarResultado(datos);
  } catch (err) {
    mostrarEstado(err.message === "Failed to fetch" ? "No hay conexión con el servidor. ¿Está corriendo python app.py?" : err.message, true);
  } finally {
    clearInterval(reloj);
    $("btn-analizar").disabled = false;
  }
}

function limpiarResultado() {
  capaResultado.clearLayers();
  quitarSeleccion();
  $("resultados").hidden = true;
  $("resultados").innerHTML = "";
  estado.resultado = null;
  mostrarEstado("");
}

// ------------------------------------------------------------------ piezas de dibujo
function medio(coords) { return coords[Math.floor(coords.length / 2)]; }

function puntoEn(forma, fraccion) {
  // Punto a una fracción del largo de la línea (para poner rótulos sin que se encimen).
  const largos = [];
  let total = 0;
  for (let i = 1; i < forma.length; i++) { const l = L.latLng(forma[i - 1]).distanceTo(forma[i]); largos.push(l); total += l; }
  let falta = total * fraccion;
  for (let i = 1; i < forma.length; i++) {
    if (falta <= largos[i - 1]) {
      const f = largos[i - 1] ? falta / largos[i - 1] : 0;
      return [forma[i - 1][0] + (forma[i][0] - forma[i - 1][0]) * f, forma[i - 1][1] + (forma[i][1] - forma[i - 1][1]) * f];
    }
    falta -= largos[i - 1];
  }
  return forma[forma.length - 1];
}

function streetView(p) {
  return `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${p[0]},${p[1]}`;
}

// Línea con borde (para que se lea sobre cualquier fondo del mapa).
function trazo(forma, color, { peso = 5, borde = "white", dash = null, capa = capaRuta } = {}) {
  L.polyline(forma, { color: borde, weight: peso + 4, opacity: 0.95, interactive: false, lineCap: "round", lineJoin: "round" }).addTo(capa);
  return L.polyline(forma, { color, weight: peso, opacity: 1, dashArray: dash, lineCap: "round", lineJoin: "round" }).addTo(capa);
}

// Flechas a lo largo de una línea, en el sentido en que se recorre.
function flechas(forma, color, { cada = 110, max = 30, capa = capaRuta } = {}) {
  let acum = 0, siguiente = cada / 2, n = 0;
  for (let i = 1; i < forma.length && n < max; i++) {
    const a = L.latLng(forma[i - 1]), b = L.latLng(forma[i]);
    const largo = a.distanceTo(b);
    while (largo > 0 && siguiente <= acum + largo && n < max) {
      const f = (siguiente - acum) / largo;
      const p = [a.lat + (b.lat - a.lat) * f, a.lng + (b.lng - a.lng) * f];
      const ang = Math.atan2((b.lng - a.lng) * Math.cos(a.lat * Math.PI / 180), b.lat - a.lat) * 180 / Math.PI;
      L.marker(p, {
        interactive: false, keyboard: false,
        icon: L.divIcon({
          className: "flecha", iconSize: [14, 14], iconAnchor: [7, 7],
          html: `<svg viewBox="0 0 14 14" width="14" height="14" style="transform:rotate(${ang.toFixed(0)}deg)">
                   <path d="M3 10 L7 4 L11 10" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
        }),
      }).addTo(capa);
      siguiente += cada;
      n++;
    }
    acum += largo;
  }
}

function pin(p, texto, clase, capa = capaRuta) {
  return L.marker(p, {
    keyboard: false,
    icon: L.divIcon({ className: "", html: `<div class="pin ${clase}">${texto}</div>`, iconSize: [24, 24], iconAnchor: [12, 12] }),
  }).addTo(capa);
}

function rotulo(p, html, clase) {
  L.tooltip({ permanent: true, direction: "right", offset: [10, 0], className: `rotulo ${clase}`, interactive: false })
    .setLatLng(p).setContent(html).addTo(capaRuta);
}

// ------------------------------------------------------------------ resultados en el mapa
const MOTIVO = {
  cruza: "la calle atraviesa el cauce",
  sobre: "la calle va por encima del cauce",
  esquina: "llega a una esquina que queda dentro del cauce",
};

function pintarContacto(t) {
  const color = t.estado === "bloqueado" ? COLOR.rojo : t.estado === "puente" ? COLOR.verde : COLOR.gris;
  const linea = L.polyline(t.forma, {
    color, weight: t.estado === "puente" ? 7 : 5, opacity: 0.95, dashArray: t.estado === "abierto" ? "6 6" : null, className: "res",
  });
  linea.on("click", (e) => {
    L.DomEvent.stopPropagation(e);
    const div = document.createElement("div");
    const titulo = { bloqueado: "Bloqueada con lluvia", puente: "Puente (sigue abierto)", abierto: "Marcada como transitable" }[t.estado];
    div.innerHTML = `<b>${t.via}</b><br>${titulo}<br><small>Motivo: ${MOTIVO[t.motivo]}.</small><br>
      <a href="${streetView(medio(t.forma))}" target="_blank" rel="noopener">Verificar en Street View</a><br>`;
    const b = document.createElement("button");
    b.textContent = t.estado === "bloqueado" ? "Se puede pasar: marcar abierta" : "No se puede pasar: marcar bloqueada";
    b.onclick = () => {
      if (t.estado === "bloqueado") { estado.abiertos.add(t.id); estado.cerrados.delete(t.id); }
      else { estado.cerrados.add(t.id); estado.abiertos.delete(t.id); }
      mapa.closePopup();
      analizar();
    };
    div.appendChild(b);
    L.popup().setLatLng(e.latlng).setContent(div).openOn(mapa);
  });
  linea.addTo(capaResultado);
}

function etiqueta(p, n, clase = "") {
  return L.marker(p, {
    icon: L.divIcon({ className: "res", html: `<div class="etiqueta ${clase}">${n}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }),
  });
}

function pintarResultado(d) {
  capaResultado.clearLayers();
  quitarSeleccion();
  d.contacto.forEach(pintarContacto);

  (d.peatones?.propuestas ?? []).forEach((p, i) => {
    L.polyline(p.forma, { color: COLOR.naranja, weight: 6, dashArray: "2 8", lineCap: "round", className: "res" }).addTo(capaResultado);
    etiqueta(medio(p.forma), p.orden).on("click", () => seleccionar("lista-puentes", i)).addTo(capaResultado);
  });
  (d.vehiculos?.propuestas ?? []).forEach((p, i) => {
    L.polyline(p.forma, { color: COLOR.morado, weight: 7, opacity: 0.85, className: "res" }).addTo(capaResultado);
    etiqueta(medio(p.forma), p.orden, "morado").on("click", () => seleccionar("lista-sentidos", i)).addTo(capaResultado);
  });
  pintarPanel(d);
}

// ------------------------------------------------------------------ selección (lista <-> mapa)
function quitarSeleccion() {
  capaRuta.clearLayers();
  mapa.getContainer().classList.remove("enfoque");
  const caja = detalle.getContainer();
  caja.hidden = true;
  caja.innerHTML = "";
  document.querySelectorAll(".lista li.sel").forEach((x) => x.classList.remove("sel"));
}

function verTodo() {
  quitarSeleccion();
  const d = estado.resultado;
  if (!d) return;
  const puntos = d.arroyo.lineas.flat().concat(d.contacto.flatMap((t) => t.forma));
  if (puntos.length) mapa.fitBounds(L.latLngBounds(puntos), { padding: [40, 40] });
}

function mostrarDetalle(html, puntos) {
  mapa.getContainer().classList.add("enfoque");
  const caja = detalle.getContainer();
  caja.innerHTML = `${html}<button class="ver-todo">Ver todo el arroyo</button>`;
  caja.hidden = false;
  caja.querySelector(".ver-todo").onclick = verTodo;
  if (puntos.length) {
    mapa.fitBounds(L.latLngBounds(puntos), { paddingTopLeft: [60, 60], paddingBottomRight: [320, 60], maxZoom: 18 });
  }
}

function seleccionar(idLista, i) {
  const li = document.querySelector(`#${idLista} li[data-i="${i}"]`);
  if (li) li.click();
}

function enlazarLista(id, accion) {
  const ul = $(id);
  if (!ul) return;
  ul.querySelectorAll("li").forEach((li) => {
    const elegir = () => {
      const yaEstaba = li.classList.contains("sel");
      quitarSeleccion();
      if (yaEstaba) return verTodo();   // segundo clic: volver a la vista general
      li.classList.add("sel");
      accion(+li.dataset.i);
      li.scrollIntoView({ block: "nearest", behavior: "smooth" });
    };
    li.onclick = elegir;
    li.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); elegir(); } };
  });
}

function filaDetalle(clase, quien, dato) {
  if (!dato) return "";
  if (dato.lluvia_m === null) {
    return `<div class="det-fila"><i class="${clase}"></i><span>${quien}</span><span>${fmt(dato.seco_m)} m en seco</span><b>sin ruta con lluvia</b></div>`;
  }
  const extra = dato.lluvia_m - dato.seco_m;
  const veces = dato.seco_m > 0 ? dato.lluvia_m / dato.seco_m : 0;
  return `<div class="det-fila"><i class="${clase}"></i><span>${quien}</span>
    <span>${fmt(dato.seco_m)} m → ${fmt(dato.lluvia_m)} m</span>
    <b>+${fmt(extra)} m${veces >= 1.5 ? ` <small>(${veces.toFixed(1).replace(".", ",")} veces)</small>` : ""}</b></div>`;
}

function mostrarRuta(x) {
  const datos = [["carro", "En carro", x.carro], ["pie", "A pie", x.pie]].filter(([, , d]) => d);
  const puntos = [];

  // Cruce cerrado (el de carro y el de a pie pueden ser distintos).
  const vistos = new Set();
  for (const [, , d] of datos) {
    const clave = JSON.stringify(d.cerrado);
    if (vistos.has(clave)) continue;
    vistos.add(clave);
    trazo(d.cerrado, COLOR.rojo, { peso: 7 });
    pin(medio(d.cerrado), "✕", "cerrado").bindTooltip("Cerrado con lluvia", { direction: "top" });
    puntos.push(...d.cerrado);
  }
  // Rutas: la de carro debajo (más ancha) y la de a pie encima, para que se vean las dos.
  if (x.carro?.forma.length) {
    trazo(x.carro.forma, COLOR.carro, { peso: 6, borde: COLOR.tinta });
    flechas(x.carro.forma, COLOR.tinta);
    rotulo(puntoEn(x.carro.forma, 0.35), `En carro <b>${fmt(x.carro.lluvia_m)} m</b>`, "carro");
    puntos.push(...x.carro.forma);
  }
  if (x.pie?.forma.length) {
    trazo(x.pie.forma, COLOR.pie, { peso: 4, dash: "8 7" });
    if (!x.carro?.forma.length) flechas(x.pie.forma, COLOR.pie);
    rotulo(puntoEn(x.pie.forma, 0.65), `A pie <b>${fmt(x.pie.lluvia_m)} m</b>`, "pie");
    puntos.push(...x.pie.forma);
  }
  // Origen y destino del cruce.
  const [, , base] = datos[0];
  pin(base.cerrado[0], "A", "extremo").bindTooltip(base.desde, { direction: "top" });
  pin(base.cerrado[base.cerrado.length - 1], "B", "extremo").bindTooltip(base.hasta, { direction: "top" });

  mostrarDetalle(`
    <div class="det-tit">${x.via}</div>
    <div class="det-sub">Cruce que la lluvia cierra, de <b>A</b> (${base.desde}) a <b>B</b> (${base.hasta}).
      Camino más corto que queda abierto:</div>
    ${datos.map(([clase, quien, d]) => filaDetalle(clase, quien, d)).join("")}
    <div class="det-nota">Esto es lo que habría que señalizar. <a href="${streetView(medio(base.cerrado))}" target="_blank" rel="noopener">Ver el cruce en Street View</a></div>`,
  puntos);
}

function largo(forma) {
  let total = 0;
  for (let i = 1; i < forma.length; i++) total += L.latLng(forma[i - 1]).distanceTo(forma[i]);
  return total;
}

function filaCambio(clase, titulo, antes, despues, unidad) {
  const baja = antes > 0 ? (100 * (antes - despues)) / antes : 0;
  return `<div class="det-fila"><i class="${clase}"></i><span>${titulo}</span>
    <span>${fmt(antes)}${unidad} → ${fmt(despues)}${unidad}</span><b>${baja >= 0.5 ? `−${baja.toFixed(0)} %` : "sin cambio"}</b></div>`;
}

function mostrarPropuesta(tipo, lista, i, lluvia) {
  const p = lista[i];
  const previo = i === 0 ? lluvia : lista[i - 1];
  const antes = previo.desvio_medio_m;
  const quien = tipo === "puente" ? "a pie" : "en carro o moto";
  if (tipo === "puente") {
    trazo(p.forma, COLOR.naranja, { peso: 7, dash: "2 9" });
  } else {
    trazo(p.forma, COLOR.morado, { peso: 7 });
    flechas(p.forma, "white", { cada: 60 });
    flechas([...p.forma].reverse(), "white", { cada: 60 });
  }
  if (largo(p.forma) < 30) {
    // Tramo tan corto que A y B se encimarían: un solo marcador.
    pin(medio(p.forma), tipo === "puente" ? p.orden : "⇄", tipo === "puente" ? "extremo" : "sentido")
      .bindTooltip(`A: ${p.desde}<br>B: ${p.hasta}`, { direction: "top" });
  } else {
    pin(p.forma[0], "A", "extremo").bindTooltip(p.desde, { direction: "top" });
    pin(p.forma[p.forma.length - 1], "B", "extremo").bindTooltip(p.hasta, { direction: "top" });
  }

  const titulo = tipo === "puente" ? `Puente peatonal ${p.orden}` : `Doble sentido ${p.orden}`;
  const que = tipo === "puente"
    ? (p.tipo === "cruce" ? `Devuelve a los peatones el cruce de la <b>${p.via}</b>, que hoy se inunda.` : "Paso nuevo donde hoy no hay calle que cruce.")
      + ` Une A (${p.desde}) con B (${p.hasta}): ${fmt(p.recorrido_m)} m.`
    : `<b>${p.via}</b>, de A (${p.desde}) a B (${p.hasta}), ${fmt(p.metros)} m. Hoy solo se puede ir de A a B; la medida permite también ir de B a A.`;
  const conCuales = i === 0 ? "con esta medida" : `con las medidas 1 a ${p.orden}`;
  const clase = tipo === "puente" ? "m-puente" : "m-sentido";
  // Una medida puede no bajar el desvío medio y aun así devolver el camino a quien se quedaba sin salida.
  const filaSin = previo.sin_camino !== p.sin_camino
    ? filaCambio(clase, "Pares que se quedan sin camino", previo.sin_camino, p.sin_camino, "") : "";
  mostrarDetalle(`
    <div class="det-tit">${titulo}</div>
    <div class="det-sub">${que}</div>
    ${filaSin}
    ${filaCambio(clase, `Desvío medio ${quien}`, antes, p.desvio_medio_m, " m")}
    <div class="det-nota">Cifras ${conCuales}. <a href="${streetView(medio(p.forma))}" target="_blank" rel="noopener">Ver el lugar en Street View</a></div>`,
  p.forma);
}

// ------------------------------------------------------------------ resultados en el panel
function barras(m, clase) {
  // Desvío medio con lluvia frente a con la medida: una sola serie, mismo color, valor escrito.
  const filas = [["Con lluvia", m.lluvia], ["Con la medida", m.con_medida]];
  const max = Math.max(1, ...filas.map(([, x]) => x.desvio_medio_m));
  const sin = (x) => (x.sin_camino ? ` · ${fmt(x.sin_camino)} pares sin camino` : "");
  return `<div class="barras" role="table" aria-label="Desvío medio">
    ${filas.map(([nombre, x]) => `
      <div class="barra-fila" role="row" title="${nombre}: ${fmt(x.desvio_medio_m)} m de desvío medio${sin(x)}">
        <span class="barra-nombre" role="rowheader">${nombre}</span>
        <span class="barra-pista"><span class="barra ${clase}" style="width:${Math.max(1.5, (100 * x.desvio_medio_m) / max)}%"></span></span>
        <span class="barra-valor" role="cell">${fmt(x.desvio_medio_m)} m</span>
      </div>`).join("")}
  </div>
  <p class="nota">Recorridos que se alargan más de 200 m: <b>${pct(m.lluvia)} → ${pct(m.con_medida)}</b>.
    ${m.lluvia.sin_camino ? `Pares que se quedan sin camino: <b>${fmt(m.lluvia.sin_camino)} → ${fmt(m.con_medida.sin_camino)}</b>.` : ""}</p>`;
}

function extraDe(dato) {
  return dato && dato.lluvia_m !== null ? dato.lluvia_m - dato.seco_m : 0;
}

function miniBarra(quien, dato, clase, max) {
  if (!dato) return "";
  if (dato.lluvia_m === null) {
    return `<div class="mini"><span class="mini-nombre">${quien}</span><span class="mini-texto">sin ruta con lluvia</span></div>`;
  }
  const extra = extraDe(dato);
  return `<div class="mini" title="${quien}: ${fmt(dato.seco_m)} m en seco, ${fmt(dato.lluvia_m)} m con lluvia">
    <span class="mini-nombre">${quien}</span>
    <span class="mini-pista"><span class="mini-barra ${clase}" style="width:${Math.max(1.5, (100 * extra) / max)}%"></span></span>
    <span class="mini-valor">+${fmt(extra)} m</span></div>`;
}

function resumen(d) {
  const p = d.peatones, v = d.vehiculos;
  if (!p || !v) return "";
  const mejorPie = p.propuestas.length
    ? `un <b>puente peatonal</b> (${p.propuestas[0].tipo === "cruce" ? "en el cruce de la " + p.propuestas[0].via : "paso nuevo"}): el desvío baja de ${fmt(p.lluvia.desvio_medio_m)} a ${fmt(p.propuestas[0].desvio_medio_m)} m`
    : "ningún puente peatonal reduce el desvío al menos 2 %";
  const v1 = v.propuestas[0];
  let mejorCarro = "ningún cambio de sentido ayuda; lo útil es <b>señalizar las rutas alternas</b>";
  if (v1) {
    const efectos = [];
    if (v1.sin_camino < v.lluvia.sin_camino) {
      efectos.push(`devuelve el camino a ${fmt(v.lluvia.sin_camino - v1.sin_camino)} de los ${fmt(v.lluvia.sin_camino)} pares que con lluvia quedaban sin salida`);
    }
    if (v1.desvio_medio_m < v.lluvia.desvio_medio_m - 0.5) {
      efectos.push(`baja el desvío de ${fmt(v.lluvia.desvio_medio_m)} a ${fmt(v1.desvio_medio_m)} m`);
    }
    mejorCarro = `habilitar <b>doble sentido</b> en ${v1.via} ${efectos.join(" y ")}. Para el resto, <b>señalizar las rutas alternas</b>`;
  }
  return `<div class="resumen">
    <div class="heroes">
      <div class="hero"><b>+${fmt(p.lluvia.desvio_medio_m)} m</b><span>se alarga en promedio cruzar <b>a pie</b> cuando llueve</span></div>
      <div class="hero"><b>+${fmt(v.lluvia.desvio_medio_m)} m</b><span>se alarga en promedio cruzar <b>en carro o moto</b></span></div>
    </div>
    <p><span class="punto" style="background:${COLOR.naranja}"></span> A pie, la mejor medida es ${mejorPie}.</p>
    <p><span class="punto" style="background:${COLOR.morado}"></span> En carro, ${mejorCarro}.</p>
  </div>`;
}

function pintarPanel(d) {
  const r = $("resultados");
  r.hidden = false;
  const lados = Object.entries(d.zona.lados).map(([k, v]) => `${v} en el ${k}`).join(" y ");
  let html = `<h2><span class="num">3</span> Resultados</h2>`;
  html += `<p class="nota">Arroyo de ${fmt(d.arroyo.longitud_m)} m. Se bloquean <b>${d.red.bloqueados}</b> tramos de calle
    y hay <b>${d.red.puentes}</b> puentes. Zona de estudio: esquinas a menos de ${d.zona.radio_m} m del cauce (${lados}).</p>`;
  for (const a of d.avisos) html += `<div class="aviso">${a}</div>`;
  html += resumen(d);

  if (d.peatones) {
    const p = d.peatones;
    html += `<div class="tarjeta"><h3><span class="punto" style="background:${COLOR.naranja}"></span>Peatones: puente peatonal</h3>`;
    html += `<p class="nota">En seco, cruzar de un lado al otro mide en promedio ${fmt(p.seco.distancia_media_m)} m.
      Desvío medio (cuánto más hay que caminar):</p>`;
    html += barras(p, "naranja");
    html += p.propuestas.length
      ? `<ul class="lista" id="lista-puentes">${p.propuestas.map((x, i) => `<li data-i="${i}" tabindex="0"><b>${x.orden}.</b> Entre ${x.desde} y ${x.hasta}
          <br><small>${x.tipo === "cruce" ? "Cruce de la " + x.via + ", hoy inundable" : "Paso nuevo"} · ${fmt(x.recorrido_m)} m · desvío queda en ${fmt(x.desvio_medio_m)} m</small></li>`).join("")}</ul>`
      : `<p class="nota">Ningún puente peatonal posible reduce el desvío al menos 2 %.</p>`;
    html += `</div>`;
  }

  if (d.vehiculos) {
    const v = d.vehiculos;
    html += `<div class="tarjeta"><h3><span class="punto" style="background:${COLOR.morado}"></span>Vehículos: cambio de sentido</h3>`;
    html += `<p class="nota">En seco, cruzar en carro o moto mide en promedio ${fmt(v.seco.distancia_media_m)} m.
      Se probaron ${v.candidatos} calles de un solo sentido cercanas. Desvío medio:</p>`;
    html += barras(v, "morado");
    html += v.propuestas.length
      ? `<ul class="lista" id="lista-sentidos">${v.propuestas.map((x, i) => `<li data-i="${i}" tabindex="0"><b>${x.orden}.</b> Doble sentido en ${x.via}
          <br><small>Entre ${x.desde} y ${x.hasta} · ${fmt(x.metros)} m · desvío queda en ${fmt(x.desvio_medio_m)} m</small></li>`).join("")}</ul>`
      : `<p class="nota">Ningún cambio de sentido reduce el desvío al menos 2 %. Para carros y motos, la medida útil aquí es señalizar la ruta alterna.</p>`;
    html += `</div>`;
  }

  if (d.rutas.length) {
    const max = Math.max(1, ...d.rutas.flatMap((x) => [extraDe(x.carro), extraDe(x.pie)]));
    html += `<div class="tarjeta"><h3><span class="punto" style="background:${COLOR.rojo}"></span>Rutas alternas para señalizar</h3>
      <p class="nota">Cruces que la lluvia cierra, de mayor a menor desvío, y cuánto más hay que recorrer por el camino
        más corto que queda. Haga clic en uno para verlo en el mapa.</p>
      <div class="leyenda-mini"><span><i class="mini-barra carro"></i>En carro</span><span><i class="mini-barra pie"></i>A pie</span></div>
      <ul class="lista" id="lista-rutas">${d.rutas.map((x, i) => `<li data-i="${i}" tabindex="0"><b>${x.via}</b>
        ${miniBarra("En carro", x.carro, "carro", max)}${miniBarra("A pie", x.pie, "pie", max)}</li>`).join("")}</ul></div>`;
  }

  html += `<p class="nota">Cómo leer esto: para cada par de esquinas en lados opuestos del arroyo se calcula el camino más
    corto en seco y con lluvia (algoritmo de Dijkstra); el desvío es la diferencia. Se usa una muestra de
    ${Object.values(d.zona.muestra).join(" y ")} esquinas por lado. Si en Street View ve que una calle roja sí se puede pasar
    (o al revés), haga clic sobre ella para corregirla.</p>
    <p class="nota">Fuente: ${d.fuente}. Cálculo: ${d.tiempos.analisis_s} s.</p>`;
  r.innerHTML = html;

  enlazarLista("lista-puentes", (i) => mostrarPropuesta("puente", d.peatones.propuestas, i, d.peatones.lluvia));
  enlazarLista("lista-sentidos", (i) => mostrarPropuesta("sentido", d.vehiculos.propuestas, i, d.vehiculos.lluvia));
  enlazarLista("lista-rutas", (i) => mostrarRuta(d.rutas[i]));
  r.scrollIntoView({ behavior: "smooth", block: "start" });
}

// http://localhost:5000/?ejemplo abre la página con El Salao ya analizado (útil en la presentación).
if (new URLSearchParams(location.search).has("ejemplo")) $("btn-ejemplo").click();
