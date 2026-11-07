// SunDial companion app — talks to the hub REST API + WebSocket, no build step.
let room = "living";
let mode = "lights";
let ws = null;
const $ = (id) => document.getElementById(id);
const CIRC = 2 * Math.PI * 108;

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function render(s) {
  const pct = s.mode === "lights" ? s.brightness
    : s.mode === "fan" ? Math.round(s.fan_speed / 3 * 100)
    : Math.round((s.target_temp_c - 16) / 14 * 100);
  $("pct").textContent = pct + "%";
  $("ring").style.strokeDasharray = `${CIRC * pct / 100} ${CIRC}`;
  $("roomTemp").textContent = `${s.current_temp_c}°C now · target ${s.target_temp_c}°C · ${s.hvac_mode}`;
  $("brightness").value = s.brightness;
  $("brightnessVal").textContent = s.brightness + "%";
  $("fanSpeed").value = String(s.fan_speed);
  $("targetTemp").value = s.target_temp_c;
  $("hvacMode").value = s.hvac_mode;
  mode = s.mode;
  document.querySelectorAll("#modes button").forEach(b =>
    b.classList.toggle("active", b.dataset.mode === mode));
  $("status").textContent = `Synced · ${room} · ${mode}`;
}

async function refresh() {
  try { render(await api(`/rooms/${room}/state`)); } catch (e) { $("status").textContent = "Hub unreachable: " + e.message; }
}

function connectWs() {
  if (ws) ws.close();
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws/${room}`);
  ws.onmessage = (ev) => render(JSON.parse(ev.data));
  ws.onclose = () => setTimeout(connectWs, 3000);
}

document.querySelectorAll("#rooms button").forEach(b => b.onclick = () => {
  room = b.dataset.room;
  document.querySelectorAll("#rooms button").forEach(x => x.classList.toggle("active", x === b));
  refresh(); connectWs();
});
document.querySelectorAll("#modes button").forEach(b => b.onclick = async () => {
  await api(`/rooms/${room}/dial/event`, { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: b.dataset.mode, delta: 0, action: "rotate" }) });
});
$("brightness").onchange = async (e) => api(`/rooms/${room}/lights`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ brightness: Number(e.target.value) }) }).then(render);
$("lightsToggle").onclick = async () => api(`/rooms/${room}/dial/event`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: "lights", delta: 0, action: "tap" }) }).then(render);
$("fanSpeed").onchange = async (e) => api(`/rooms/${room}/fan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ speed: Number(e.target.value) }) }).then(render);
$("targetTemp").onchange = async (e) => api(`/rooms/${room}/hvac`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target_temp_c: Number(e.target.value) }) }).then(render);
$("hvacMode").onchange = async (e) => api(`/rooms/${room}/hvac`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: e.target.value }) }).then(render);
$("allOff").onclick = async () => api(`/rooms/${room}/dial/event`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ delta: 0, action: "long_press" }) }).then(render);
refresh(); connectWs();
