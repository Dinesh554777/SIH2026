/* Monsoon Decision Support — frontend (vanilla JS, talks only to the real API). */
"use strict";

const DEMO_CELL = "10.75_77.5";
const DEMO_DATES = {
  "2024-06-07": "False onset",
  "2024-08-08": "Dry spell eve",
  "2024-08-12": "Revival",
};

const el = (id) => document.getElementById(id);

function fmtPct(p) {
  return (p * 100).toFixed(1) + "%";
}

function showError(msg, retry) {
  const card = el("errorCard");
  card.hidden = false;
  card.innerHTML = '<span class="error">' + msg + "</span>";
  if (retry) {
    const b = document.createElement("button");
    b.className = "retry";
    b.textContent = "Retry";
    b.onclick = retry;
    card.appendChild(b);
  }
}

function hideError() {
  el("errorCard").hidden = true;
}

async function getJSON(url) {
  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = body && body.error ? body.error : { message: "Request failed" };
    const e = new Error(`[${res.status}] ${err.code || "error"}: ${err.message}`);
    e.status = res.status;
    e.code = err.code;
    throw e;
  }
  return body;
}

async function bootPing() {
  // pre-warm: forces the frozen model load once, surfaces boot problems early
  hideError();
  try {
    const h = await getJSON("/health");
    el("modeBadge").textContent = `data mode: ${h.data_mode}`;
    return h;
  } catch (e) {
    if (e.status >= 500 || !e.status) {
      showError(
        "Backend not ready yet — model cold start takes a few seconds. Waiting…",
        () => bootPing(),
      );
      throw e;
    }
    throw e;
  }
}

async function initLocations() {
  try {
    const data = await getJSON("/locations");
    const dl = el("cellList");
    data.locations.forEach((l) => {
      const o = document.createElement("option");
      o.value = l.cell_id;
      o.label = `${l.cell_id} (lat ${l.lat}, lon ${l.lon}, ${l.region})`;
      dl.appendChild(o);
    });
    el("locMeta").textContent =
      `${data.locations.length} pilot cells · ${data.spatial_unit.step_degrees}° grid · ` +
      `regions: ${data.spatial_unit.pilot_regions.join(", ")}`;
    el("modeBadge").textContent = `data mode: ${data.data_mode}`;
    return data;
  } catch (e) {
    showError("Could not load locations: " + e.message, () => initLocations());
    return null;
  }
}

function bandClass(band) {
  return "band-" + band;
}

function renderCards(targets, confidence) {
  const wrap = el("targetCards");
  wrap.innerHTML = "";
  const order = ["onset", "break", "revival", "dry_spell"];
  for (const t of order) {
    const v = targets[t];
    const pct = fmtPct(v.probability);
    const card = document.createElement("div");
    card.className = "card " + bandClass(v.band);
    card.innerHTML = `
      <div class="t">${t.replace("_", " ")}</div>
      <div class="p">${pct}</div>
      <div class="b">${v.band} · ${v.band_meaning}</div>
      <div class="meta">model: ${v.model}${v.calibration_ece_val !== undefined
        ? " · val ECE " + v.calibration_ece_val.toExponential(1) : ""}</div>
    `;
    wrap.appendChild(card);
  }
  el("confidenceNote").textContent = confidence.note +
    ` Band thresholds: ${confidence.bands.map((b) => `${b.band} ${b.range[0] * 100}–${(b.range[1] * 100).toFixed(1)}%`).join(" · ")}.`;
}

function renderCalibration(confidence) {
  const strip = el("calibrationStrip");
  if (!confidence.calibration) {
    strip.hidden = true;
    return;
  }
  const row = el("calibrationRow");
  row.innerHTML = "";
  for (const c of confidence.calibration) {
    const cell = document.createElement("span");
    cell.className = "cal-cell";
    cell.innerHTML =
      `<b>${c.state}</b> ECE ${c.ece != null ? c.ece.toExponential(2) : "—"} · ` +
      `Brier ${(c.brier * 1000).toFixed(2)}‰ (val ${c.period})`;
    row.appendChild(cell);
  }
  strip.hidden = false;
}

function renderSignal(signal) {
  const wrap = el("currentSignal");
  const items = [
    ["Rainfall today", signal.rain_t_mm + " mm"],
    ["7-day total", signal.sum7_mm + " mm"],
    ["Trend", signal.rainfall_trend],
    ["Regime", signal.rainfall_regime],
    ["Wet streak", signal.wet_streak_days + " d"],
    ["Dry streak", signal.dry_streak_days + " d"],
    ["Wet days (7d)", signal.wet_days_last7],
  ];
  wrap.innerHTML = "";
  for (const [lbl, val] of items) {
    const k = document.createElement("div");
    k.className = "kpi";
    k.innerHTML = `<div class="lbl">${lbl}</div><div class="val">${val}</div>`;
    wrap.appendChild(k);
  }
}

function renderAdvisory(a) {
  el("guidanceSummary").textContent = a.summary;
  const wrap = el("guidanceItems");
  wrap.innerHTML = "";
  for (const it of a.items) {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <div class="s">${it.state_label} — ${it.probability_pct}% (${it.band})</div>
      <div class="act">${it.interpretation}</div>
      <div class="act">${it.suggested_action}</div>
      <div class="flag">${it.expert_validation}</div>
    `;
    wrap.appendChild(div);
  }
  el("disclaimer").textContent = a.disclaimer;
  el("disclaimer").textContent += " Evidence: " +
    Object.entries(a.evidence).map(([k, v]) => `${k}=${v}`).join(" · ");
}

function renderExplain(e) {
  el("explainCaveat").textContent = e.caveat;
  const tbody = el("sensitivityTable").querySelector("tbody");
  tbody.innerHTML = "";
  for (const s of e.sensitivity) {
    const tr = document.createElement("tr");
    const delta = s.delta_probability * 100;
    tr.innerHTML = `
      <td>${s.feature}</td>
      <td>${s.value}</td>
      <td>${s.train_median}</td>
      <td class="${delta >= 0 ? "" : "error"}">${delta >= 0 ? "+" : ""}${delta.toFixed(3)} pp</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderProvenance(p) {
  el("provenance").textContent = JSON.stringify(p, null, 2);
}

async function loadForecast(force) {
  const cell = (el("cellInput").value || DEMO_CELL).trim();
  const date = el("dateInput").value;
  if (force !== true && !cell) {
    showError("Enter a pilot cell id (e.g. " + DEMO_CELL + ")");
    return;
  }
  try {
    hideError();
    const fc = await getJSON(`/api/v1/cells/${encodeURIComponent(cell)}/forecast?date=${date}`);
    const adv = await getJSON(`/api/v1/cells/${encodeURIComponent(cell)}/advisory?date=${date}`);
    const exp = await getJSON(`/api/v1/cells/${encodeURIComponent(cell)}/explain?date=${date}`);

    el("generatedAt").textContent =
      `observation ${fc.forecast_date} · generated ${fc.generated_at} · ${fc.data_mode}`;
    renderCards(fc.targets, fc.confidence);
    renderCalibration(fc.confidence);
    renderSignal(adv.current_signal);
    renderAdvisory(adv);
    renderExplain(exp);
    renderProvenance(fc.provenance);

    el("forecastPanel").hidden = false;
    el("signalPanel").hidden = false;
    el("whyPanel").hidden = false;
    el("provenancePanel").hidden = false;
  } catch (e) {
    showError(`API error: ${e.message}`, () => loadForecast(true));
  }
}

function setDemo(date) {
  el("cellInput").value = DEMO_CELL;
  el("dateInput").value = date;
  loadForecast(true);
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await bootPing();
    const data = await initLocations();
    if (data) {
      const lo = data.locations.find((l) => l.cell_id === DEMO_CELL);
      el("cellInput").value = lo ? DEMO_CELL : data.locations[0].cell_id;
    }
    // default to the latest JJAS observation for the resolved cell (also warms the model)
    const cell = el("cellInput").value;
    const fc = await getJSON(`/api/v1/cells/${encodeURIComponent(cell)}/forecast`);
    el("dateInput").value = fc.forecast_date;
    await loadForecast(true);
  } catch (e) {
    el("dateInput").value = "2024-08-12";
    if (!el("errorCard") || el("errorCard").hidden) {
      showError("Boot failed: " + e.message, () => document.location.reload());
    }
  }
  el("loadBtn").addEventListener("click", () => loadForecast(true));
  document.querySelectorAll(".demo-row button").forEach((b) =>
    b.addEventListener("click", () => setDemo(b.dataset.date)));
});