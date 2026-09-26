// SN1/SN2 Reaction Lab -- static, client-side app. All chemistry data and
// decision logic live in chemistry.js; this file wires up the UI and the
// mechanism animation.

const SVG_NS = "http://www.w3.org/2000/svg";
const CX = 230;
const CY = 140;

// ---------------------------------------------------------------- helpers --
function svgEl(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  setAttrs(el, attrs);
  return el;
}
function setAttrs(el, attrs) {
  for (const k in attrs) el.setAttribute(k, attrs[k]);
}
function lerp(a, b, t) {
  return a + (b - a) * t;
}
// Piecewise-linear interpolation across three keyframes at t=0, 0.5, 1.
function keyframeValue(start, mid, end, t) {
  return t <= 0.5 ? lerp(start, mid, t / 0.5) : lerp(mid, end, (t - 0.5) / 0.5);
}
function gauss(t, mu, sigma, amp) {
  const z = (t - mu) / sigma;
  return amp * Math.exp(-0.5 * z * z);
}

// ---------------------------------------------------------- populate UI ---
const els = {
  substrate: document.getElementById("substrate"),
  nucleophile: document.getElementById("nucleophile"),
  solvent: document.getElementById("solvent"),
  exampleButtons: document.getElementById("example-buttons"),
  visualizeBtn: document.getElementById("visualize-btn"),
  verdictPanel: document.getElementById("verdict-panel"),
  verdictLabel: document.getElementById("verdict-label"),
  verdictReasons: document.getElementById("verdict-reasons"),
  stagePanel: document.getElementById("stage-panel"),
  scene: document.getElementById("scene"),
  sceneCaption: document.getElementById("scene-caption"),
  energy: document.getElementById("energy"),
  resetBtn: document.getElementById("reset-btn"),
  stepBackBtn: document.getElementById("step-back-btn"),
  playBtn: document.getElementById("play-btn"),
  stepFwdBtn: document.getElementById("step-fwd-btn"),
  speed: document.getElementById("speed"),
  scrub: document.getElementById("scrub"),
};

function fillSelect(select, items, defaultId) {
  select.innerHTML = "";
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = item.name;
    select.appendChild(opt);
  }
  if (defaultId) select.value = defaultId;
}

const DEFAULT_EXAMPLE = EXAMPLES[0];
fillSelect(els.substrate, SUBSTRATES, DEFAULT_EXAMPLE.substrate);
fillSelect(els.nucleophile, NUCLEOPHILES, DEFAULT_EXAMPLE.nucleophile);
fillSelect(els.solvent, SOLVENTS, DEFAULT_EXAMPLE.solvent);

for (const ex of EXAMPLES) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = ex.label;
  btn.addEventListener("click", () => {
    els.substrate.value = ex.substrate;
    els.nucleophile.value = ex.nucleophile;
    els.solvent.value = ex.solvent;
    runVisualization();
  });
  els.exampleButtons.appendChild(btn);
}

els.visualizeBtn.addEventListener("click", runVisualization);

// ------------------------------------------------------- mechanism build --
// Reusable R-group geometry: three substituent stubs. Before reaction they
// tilt away from the leaving group (toward where the nucleophile will come
// from); at the transition state / carbocation they flatten (dx -> 0); after,
// they mirror to the other side. This is the classic "umbrella inversion"
// picture, simplified to 2D.
const STUB_BASE = [
  { dx: -47.6, dy: 27.5 },
  { dx: -47.6, dy: -27.5 },
  { dx: -14.2, dy: -53.1 },
];

function buildKeyframes(mechanism, substrate) {
  const flat = STUB_BASE.map((s) => ({ dx: 0, dy: s.dy }));
  const mirrored = STUB_BASE.map((s) => ({ dx: -s.dx, dy: s.dy }));

  if (mechanism === "SN2") {
    return {
      start: {
        nuX: 30, nuBondOpacity: 0,
        lgX: 275, lgOpacity: 1,
        stubs: STUB_BASE, chargeOpacity: 0, racemHint: 0,
        caption: `${substrate.lg}⁻ is fully bonded, ${nucName()} is still approaching from the back side.`,
      },
      mid: {
        nuX: 170, nuBondOpacity: 0.7,
        lgX: 292, lgOpacity: 0.7,
        stubs: flat, chargeOpacity: 0.6, racemHint: 0,
        caption: "Transition state: both bonds are half-formed, and the three other groups pass through a flat arrangement.",
      },
      end: {
        nuX: 185, nuBondOpacity: 1,
        lgX: 430, lgOpacity: 0.15,
        stubs: mirrored, chargeOpacity: 0, racemHint: 0,
        caption: `${nucName()} is fully bonded on the opposite face -- the configuration at carbon has inverted.`,
      },
    };
  }
  // SN1: leaving group departs first (slow step) to give a flat carbocation;
  // the nucleophile only arrives afterward (fast step). Shown here attacking
  // from the same face the leaving group vacated -- in reality it can attack
  // from either face with equal probability, giving a racemic mixture; see
  // the faint second arrow once the cation has formed.
  return {
    start: {
      nuX: 30, nuBondOpacity: 0,
      lgX: 275, lgOpacity: 1,
      stubs: STUB_BASE, chargeOpacity: 0, racemHint: 0,
      caption: `${substrate.lg}⁻ is still bonded. Ionization has not started yet.`,
    },
    mid: {
      nuX: 95, nuBondOpacity: 0,
      lgX: 430, lgOpacity: 0.3,
      stubs: flat, chargeOpacity: 1, racemHint: 1,
      caption: `Slow step complete: ${substrate.lg}⁻ has left, leaving a flat carbocation. ${nucName()} can attack either face.`,
    },
    end: {
      nuX: 185, nuBondOpacity: 1,
      lgX: 430, lgOpacity: 0.3,
      stubs: mirrored, chargeOpacity: 0, racemHint: 1,
      caption: `Fast step: ${nucName()} has bonded. Attack from the other face was equally likely -- SN1 racemizes a stereocenter.`,
    },
  };

  function nucName() {
    return currentState.nucleophile.symbol;
  }
}

function frameAt(keyframes, t) {
  const s = keyframes.start, m = keyframes.mid, e = keyframes.end;
  const num = (key) => keyframeValue(s[key], m[key], e[key], t);
  const stubs = [0, 1, 2].map((i) => ({
    dx: keyframeValue(s.stubs[i].dx, m.stubs[i].dx, e.stubs[i].dx, t),
    dy: keyframeValue(s.stubs[i].dy, m.stubs[i].dy, e.stubs[i].dy, t),
  }));
  const caption = t < 0.4 ? s.caption : t <= 0.62 ? m.caption : e.caption;
  return {
    nuX: num("nuX"), nuBondOpacity: num("nuBondOpacity"),
    lgX: num("lgX"), lgOpacity: num("lgOpacity"),
    chargeOpacity: num("chargeOpacity"),
    racemHint: t > 0.42 ? Math.max(s.racemHint, m.racemHint, e.racemHint) : 0,
    stubs, caption,
  };
}

// ------------------------------------------------------------- energy ----
function energyValue(mechanism, t) {
  if (mechanism === "SN2") {
    return 0.15 + gauss(t, 0.5, 0.18, 0.75) - 0.05 * t;
  }
  return (
    0.12 +
    gauss(t, 0.5, 0.22, 0.22) +
    gauss(t, 0.25, 0.09, 0.55) +
    gauss(t, 0.75, 0.09, 0.35) -
    0.04 * t
  );
}
function energyToY(e) {
  return 145 - e * 115;
}

// -------------------------------------------------------------- scene -----
let scene = null; // populated by buildScene()

function buildScene(substrate) {
  const svg = els.scene;
  svg.innerHTML = "";

  const carbon = svgEl("circle", { cx: CX, cy: CY, r: 13, fill: "#1b2430" });
  const carbonLabel = svgEl("text", {
    x: CX, y: CY + 4, "text-anchor": "middle", fill: "#fff",
    "font-size": 11, "font-weight": 700,
  });
  carbonLabel.textContent = "C";

  const charge = svgEl("text", {
    x: CX + 18, y: CY - 16, "text-anchor": "middle", fill: "#b5482f",
    "font-size": 16, "font-weight": 700, opacity: 0,
  });
  charge.textContent = "+";

  // Nucleophile
  const nuBond = svgEl("line", { x1: 0, y1: CY, x2: CX, y2: CY, stroke: "#2f5fbf", "stroke-width": 2 });
  const nuAtom = svgEl("circle", { cy: CY, r: 11, fill: "#2f5fbf" });
  const nuLabel = svgEl("text", { y: CY - 18, "text-anchor": "middle", fill: "#1d3f85", "font-size": 12, "font-weight": 700 });

  // Leaving group
  const lgBond = svgEl("line", { x1: CX, y1: CY, x2: CX, y2: CY, stroke: "#b5482f", "stroke-width": 2 });
  const lgAtom = svgEl("circle", { cy: CY, r: 11, fill: "#b5482f" });
  const lgLabel = svgEl("text", { y: CY - 18, "text-anchor": "middle", fill: "#b5482f", "font-size": 12, "font-weight": 700 });
  lgLabel.textContent = substrate.lg + "⁻";

  // Racemization hint: a faint dashed arc showing attack from the far face.
  const racemArc = svgEl("path", {
    d: `M 40 ${CY + 70} Q ${CX} ${CY + 40} ${CX - 5} ${CY + 10}`,
    fill: "none", stroke: "#8a6d1f", "stroke-width": 1.5,
    "stroke-dasharray": "4,4", opacity: 0,
  });
  const racemLabel = svgEl("text", {
    x: 90, y: CY + 92, "font-size": 10, fill: "#8a6d1f", opacity: 0,
  });
  racemLabel.textContent = "...or attack from the far face (racemization)";

  // R-groups (3 stubs)
  const stubEls = substrate.groups.map((g) => {
    const line = svgEl("line", { x1: CX, y1: CY, stroke: "#5b6472", "stroke-width": 2 });
    const label = svgEl("text", { "text-anchor": "middle", fill: "#1b2430", "font-size": 11, "font-weight": 600 });
    label.textContent = g;
    return { line, label };
  });

  svg.append(nuBond, lgBond, ...stubEls.flatMap((s) => [s.line, s.label]), carbon, carbonLabel, charge, nuAtom, nuLabel, lgAtom, lgLabel, racemArc, racemLabel);

  scene = { nuBond, nuAtom, nuLabel, lgBond, lgAtom, lgLabel, charge, stubEls, racemArc, racemLabel };
}

function renderScene(vals) {
  const nuDashed = vals.nuBondOpacity < 0.95;
  setAttrs(scene.nuBond, {
    x2: vals.nuX, opacity: Math.max(vals.nuBondOpacity, 0.001),
    "stroke-dasharray": nuDashed ? "6,5" : "0",
  });
  setAttrs(scene.nuAtom, { cx: vals.nuX });
  setAttrs(scene.nuLabel, { x: vals.nuX });
  scene.nuLabel.textContent = currentState.nucleophile.symbol;

  const lgDashed = vals.lgOpacity < 0.95;
  setAttrs(scene.lgBond, {
    x2: vals.lgX, opacity: vals.lgOpacity,
    "stroke-dasharray": lgDashed ? "6,5" : "0",
  });
  setAttrs(scene.lgAtom, { cx: vals.lgX, opacity: vals.lgOpacity });
  setAttrs(scene.lgLabel, { x: vals.lgX, opacity: vals.lgOpacity });

  setAttrs(scene.charge, { opacity: vals.chargeOpacity });
  setAttrs(scene.racemArc, { opacity: vals.racemHint * 0.8 });
  setAttrs(scene.racemLabel, { opacity: vals.racemHint * 0.9 });

  vals.stubs.forEach((s, i) => {
    const x2 = CX + s.dx, y2 = CY + s.dy;
    setAttrs(scene.stubEls[i].line, { x2, y2 });
    setAttrs(scene.stubEls[i].label, {
      x: CX + s.dx * 1.25, y: CY + s.dy * 1.25 + 4,
    });
  });

  els.sceneCaption.textContent = vals.caption;
}

// --------------------------------------------------------- energy chart ---
let energyMarker = null;

function buildEnergyChart(mechanism) {
  const svg = els.energy;
  svg.innerHTML = "";
  const axis = svgEl("line", { x1: 20, y1: 145, x2: 280, y2: 145, stroke: "#5b6472", "stroke-width": 1.5 });
  const axisLabel = svgEl("text", { x: 150, y: 158, "text-anchor": "middle", fill: "#5b6472", "font-size": 10 });
  axisLabel.textContent = "reaction coordinate";
  const yLabel = svgEl("text", { x: 8, y: 24, fill: "#5b6472", "font-size": 10 });
  yLabel.textContent = "energy";

  const N = 60;
  let d = "";
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const x = 20 + t * 260;
    const y = energyToY(energyValue(mechanism, t));
    d += (i === 0 ? "M " : "L ") + x.toFixed(1) + " " + y.toFixed(1) + " ";
  }
  const path = svgEl("path", { d, fill: "none", stroke: mechanism === "SN2" ? "#2f7a4f" : "#b5482f", "stroke-width": 2.5 });

  const labels = [];
  if (mechanism === "SN2") {
    labels.push({ t: 0.5, text: "‡", dy: -8 });
  } else {
    labels.push({ t: 0.25, text: "‡ (slow)", dy: -8 });
    labels.push({ t: 0.75, text: "‡ (fast)", dy: -8 });
    labels.push({ t: 0.5, text: "carbocation", dy: 14 });
  }
  const labelEls = labels.map((l) => {
    const x = 20 + l.t * 260;
    const y = energyToY(energyValue(mechanism, l.t)) + l.dy;
    const t = svgEl("text", { x, y, "text-anchor": "middle", "font-size": 10, fill: "#1b2430" });
    t.textContent = l.text;
    return t;
  });

  const guide = svgEl("line", { x1: 20, y1: 0, x2: 20, y2: 145, stroke: "#5b6472", "stroke-width": 1, "stroke-dasharray": "3,3", opacity: 0.6 });
  const marker = svgEl("circle", { cx: 20, cy: 145, r: 5, fill: mechanism === "SN2" ? "#2f7a4f" : "#b5482f" });

  svg.append(axis, axisLabel, yLabel, path, ...labelEls, guide, marker);
  energyMarker = { marker, guide, mechanism };
}

function renderEnergy(t) {
  const x = 20 + t * 260;
  const y = energyToY(energyValue(energyMarker.mechanism, t));
  setAttrs(energyMarker.marker, { cx: x, cy: y });
  setAttrs(energyMarker.guide, { x1: x, x2: x, y2: y });
}

// --------------------------------------------------------------- state ----
const currentState = {
  substrate: null,
  nucleophile: null,
  solvent: null,
  mechanism: null, // "SN1" | "SN2" -- the one currently animated
  keyframes: null,
  t: 0,
  playing: false,
  rafId: null,
  lastTime: 0,
};

function render() {
  const vals = frameAt(currentState.keyframes, currentState.t);
  renderScene(vals);
  renderEnergy(currentState.t);
  els.scrub.value = currentState.t;
  els.playBtn.textContent = currentState.playing ? "⏸ Pause" : "▶ Play";
}

function setMechanism(mechanism) {
  currentState.mechanism = mechanism;
  currentState.keyframes = buildKeyframes(mechanism, currentState.substrate);
  currentState.t = 0;
  currentState.playing = false;
  buildScene(currentState.substrate);
  buildEnergyChart(mechanism);
  render();
}

function runVisualization() {
  currentState.substrate = byId(SUBSTRATES, els.substrate.value);
  currentState.nucleophile = byId(NUCLEOPHILES, els.nucleophile.value);
  currentState.solvent = byId(SOLVENTS, els.solvent.value);

  const verdict = decideMechanism(currentState.substrate, currentState.nucleophile, currentState.solvent);

  els.verdictPanel.hidden = false;
  els.stagePanel.hidden = false;

  const labelText = verdict.mechanism === "borderline" ? "Borderline (both compete)" : verdict.mechanism + (verdict.slow ? " (slow)" : "");
  els.verdictLabel.textContent = labelText;
  els.verdictLabel.className = verdict.mechanism === "borderline" ? "borderline" : verdict.mechanism.toLowerCase();

  els.verdictReasons.innerHTML = "";
  for (const r of verdict.reasons) {
    const li = document.createElement("li");
    li.textContent = r;
    els.verdictReasons.appendChild(li);
  }

  // Remove any previous mechanism toggle before possibly re-adding one.
  const oldToggle = document.getElementById("mech-toggle");
  if (oldToggle) oldToggle.remove();

  if (verdict.mechanism === "borderline") {
    const toggle = document.createElement("div");
    toggle.className = "mech-toggle";
    toggle.id = "mech-toggle";
    const label = document.createElement("span");
    label.textContent = "Show:";
    label.style.fontSize = "0.85rem";
    label.style.color = "#5b6472";
    toggle.appendChild(label);
    for (const m of ["SN2", "SN1"]) {
      const btn = document.createElement("button");
      btn.textContent = m;
      btn.type = "button";
      btn.className = m === "SN2" ? "active" : "";
      btn.addEventListener("click", () => {
        setMechanism(m);
        [...toggle.querySelectorAll("button")].forEach((b) => b.classList.toggle("active", b === btn));
      });
      toggle.appendChild(btn);
    }
    els.verdictPanel.appendChild(toggle);
    setMechanism("SN2");
  } else {
    setMechanism(verdict.mechanism);
  }

  if (els.stagePanel.scrollIntoView) {
    els.stagePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// ----------------------------------------------------------- transport ----
function stopPlaying() {
  currentState.playing = false;
  if (currentState.rafId) cancelAnimationFrame(currentState.rafId);
  currentState.rafId = null;
}

function tick(now) {
  if (!currentState.playing) return;
  const dt = (now - currentState.lastTime) / 1000;
  currentState.lastTime = now;
  const speed = parseFloat(els.speed.value);
  const totalDuration = 4.5; // seconds for a full 0 -> 1 pass at speed 1
  currentState.t = Math.min(1, currentState.t + dt * speed / totalDuration);
  render();
  if (currentState.t >= 1) {
    stopPlaying();
    render();
    return;
  }
  currentState.rafId = requestAnimationFrame(tick);
}

els.playBtn.addEventListener("click", () => {
  if (!currentState.keyframes) return;
  if (currentState.playing) {
    stopPlaying();
    render();
    return;
  }
  if (currentState.t >= 1) currentState.t = 0;
  currentState.playing = true;
  currentState.lastTime = performance.now();
  currentState.rafId = requestAnimationFrame(tick);
});

els.resetBtn.addEventListener("click", () => {
  stopPlaying();
  currentState.t = 0;
  render();
});

const SNAP_POINTS = [0, 0.5, 1];
els.stepFwdBtn.addEventListener("click", () => {
  stopPlaying();
  const next = SNAP_POINTS.find((p) => p > currentState.t + 0.001);
  currentState.t = next === undefined ? 1 : next;
  render();
});
els.stepBackBtn.addEventListener("click", () => {
  stopPlaying();
  const prev = [...SNAP_POINTS].reverse().find((p) => p < currentState.t - 0.001);
  currentState.t = prev === undefined ? 0 : prev;
  render();
});
els.scrub.addEventListener("input", () => {
  stopPlaying();
  currentState.t = parseFloat(els.scrub.value);
  render();
});

// ------------------------------------------------------------- startup ----
runVisualization();
