let selected = null, evChart = null, hriChart = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const clock = ts => new Date(ts * 1000).toLocaleTimeString([], {hour12: false});
const label = t => t.replace(/_/g, " ");
const kind = t => /sim_/.test(t) ? "k-sim" : /pin_reset|pin_changed|session_created/.test(t) ? "k-pin"
  : /transfer|alert/.test(t) ? "k-money" : "";
const brief = d => Object.entries(d || {}).filter(([k]) => !["campaign_id"].includes(k))
  .map(([k, v]) => `${k}=${v}`).join(", ");

function metrics(m) {
  const cards = [["Active alerts", m.active], ["Highest level", m.top_level], ["Human Risk Index", m.hri],
    ["SIM re-registrations", m.sim], ["PIN-reset attempts", m.pin_reset], ["Failed PINs", m.failed],
    ["Transfers flagged", m.flagged_transfers]];
  $("metrics").innerHTML = cards.map(([l, v]) => `<div class="metric"><b>${esc(v)}</b><span>${l}</span></div>`).join("");
}

function alerts(list) {
  if (!list.length) return;
  $("alerts").innerHTML = list.map(a => `<div class="alert l-${a.level} ${a.status === "resolved" ? "resolved" : ""} ${a.id === selected ? "sel" : ""}" data-id="${a.id}">
    <div class="row"><strong>${esc(a.user)}</strong><span class="badge b-${a.level}">${a.level}</span></div>
    <div class="muted">Score ${a.score}/100 · ${a.rules.join(", ")} · ${a.status} · ${clock(a.updated)}</div></div>`).join("");
  document.querySelectorAll(".alert").forEach(el => el.onclick = () => { selected = +el.dataset.id; loadDetail(); });
  if (selected === null) { selected = list[0].id; loadDetail(); }
}

async function loadDetail() {
  if (selected === null) return;
  const r = await fetch(`/api/alerts/${selected}`); if (!r.ok) return;
  const {alert: a, timeline} = await r.json();
  $("detail").innerHTML = `
    <div class="row" style="display:flex;justify-content:space-between;align-items:center">
      <strong>${esc(a.user)} <span class="muted">${esc(a.phone)}</span></strong><span class="badge b-${a.level}">${a.level} · ${a.score}</span></div>
    <h2 style="margin-top:14px">Why this was flagged</h2>
    <ul class="why">${a.explanation.map(x => `<li><strong>${esc(x.rule)} · ${esc(x.name)}</strong><br><span class="muted">${esc(x.text)}</span></li>`).join("")}</ul>
    <h2 style="margin-top:14px">Recommended response</h2>
    <ul class="why">${a.recommended.map(x => `<li>${esc(x)}</li>`).join("")}</ul>
    <div class="actions">
      ${a.restricted ? `<button data-act="release">Release transfers</button>` : `<button class="danger" data-act="restrict">Restrict transfers</button>`}
      ${a.status === "open" ? `<button data-act="resolve">Mark resolved</button>` : ""}</div>
    <h2 style="margin-top:14px">Attack timeline</h2>
    <ul class="tl">${timeline.map(e => `<li class="${kind(e.type)}"><time>${clock(e.ts)}</time>${esc(label(e.type))}${e.type.startsWith("alert") ? " · " + esc(e.details.level) : ""}
      <span class="muted">${esc(brief(e.details))}</span></li>`).join("")}</ul>`;
  document.querySelectorAll("[data-act]").forEach(b => b.onclick = async () => {
    await fetch(`/api/alerts/${selected}/action`, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: b.dataset.act})});
    refresh();
  });
}

function charts(s) {
  const types = Object.keys(s.counts).sort(), vals = types.map(t => s.counts[t]);
  if (!evChart) evChart = new Chart($("evChart"), {type: "bar", data: {labels: [], datasets: [{data: [], backgroundColor: "#0b6b6b"}]},
    options: {indexAxis: "y", plugins: {legend: {display: false}}, animation: false}});
  evChart.data.labels = types.map(label); evChart.data.datasets[0].data = vals; evChart.update();
  if (!hriChart) hriChart = new Chart($("hriChart"), {type: "bar", data: {labels: [], datasets: [{data: [], backgroundColor: "#b34700"}]},
    options: {plugins: {legend: {display: false}}, scales: {y: {min: 0, max: 100}}, animation: false}});
  hriChart.data.labels = s.scenario_rates.map(x => x.scenario); hriChart.data.datasets[0].data = s.scenario_rates.map(x => x.rate); hriChart.update();
  $("hriEmpty").textContent = s.scenario_rates.length ? "" : "No phishing drill has been run yet.";
}

async function refresh() {
  const r = await fetch("/api/state"); if (!r.ok) return;
  const s = await r.json();
  $("stamp").textContent = "Live · refreshed " + clock(s.now);
  metrics(s.metrics); alerts(s.alerts); charts(s);
  $("users").innerHTML = s.users.map(u => `<tr><td>${esc(u.name)}</td><td>${esc(u.phone)}</td>
    <td><span class="chip ${u.sim_state === "attacker" ? "warn" : "ok"}">${esc(u.sim_state)}</span></td><td class="muted">${esc(u.device)}</td>
    <td>${u.hri === null ? "—" : u.hri}</td><td>${u.risk}</td><td>${u.restricted ? '<span class="chip warn">restricted</span>' : "open"}</td></tr>`).join("");
  $("events").innerHTML = s.events.map(e => `<tr><td>${clock(e.ts)}</td><td>${esc(e.source)}</td><td>${esc(label(e.type))}</td><td>${esc(e.user || "")}</td><td class="muted">${esc(brief(e.details))}</td></tr>`).join("");
  if (selected !== null) loadDetail();
}
refresh(); setInterval(refresh, 3000);
