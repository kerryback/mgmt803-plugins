/* Sullivan Family Activities — front end (no build step, no dependencies) */
"use strict";

/* ------------------------------------------------------------ utilities */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (n, cls = "") =>
  `<svg class="ic ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${(window.ICONS || {})[n] || ""}</svg>`;

const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DOW_LONG = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTH = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

const pad = (n) => String(n).padStart(2, "0");
const iso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parseISO = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const startOfWeek = (d) => { const x = addDays(d, -((d.getDay() + 6) % 7)); x.setHours(0, 0, 0, 0); return x; };
const toMin = (t) => { if (!t) return null; const [h, m] = t.split(":").map(Number); return h * 60 + m; };
const hhmm = (mins) => `${pad(Math.floor(mins / 60))}:${pad(mins % 60)}`;
const fmtTime = (t, short = false) => {
  if (!t) return "";
  let [h, m] = t.split(":").map(Number);
  const ap = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  return short ? `${h}:${pad(m)}` : `${h}:${pad(m)} ${ap}`;
};
const fmtDay = (s) => { const d = parseISO(s); return `${DOW[d.getDay()]}, ${MON[d.getMonth()]} ${d.getDate()}`; };
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

/* -------------------------------------------------- API + parent PIN */
const PIN_KEY = "sfa.pin";
const PIN_TTL = 15 * 60 * 1000; // stay unlocked for 15 minutes
const Pin = {
  isSet: false,
  get() {
    try {
      const v = JSON.parse(sessionStorage.getItem(PIN_KEY) || "null");
      return v && v.until > Date.now() ? v.pin : null;
    } catch { return null; }
  },
  remember(pin) { try { sessionStorage.setItem(PIN_KEY, JSON.stringify({ pin, until: Date.now() + PIN_TTL })); } catch { /* ignore */ } },
  forget() { try { sessionStorage.removeItem(PIN_KEY); } catch { /* ignore */ } },
};

function errorMessage(j, status) {
  let msg = `Something went wrong (${status})`;
  if (typeof j?.detail === "string") return j.detail;
  if (Array.isArray(j?.detail) && j.detail[0]) {
    const d = j.detail[0];
    const field = d.loc && d.loc.length > 1 ? d.loc[d.loc.length - 1] : "";
    msg = String(d.msg || msg).replace(/^Value error, /, "");
    if (field && !/^Value error/.test(d.msg || "") && d.type !== "value_error") msg = `${String(field).replace(/_/g, " ")}: ${msg}`;
  }
  return msg;
}

async function api(path, { method = "GET", body, retried = false } = {}) {
  const headers = body ? { "Content-Type": "application/json" } : {};
  const pin = Pin.get();
  if (pin) headers["X-Parent-Pin"] = pin;
  const res = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    let j = null;
    try { j = await res.json(); } catch { /* not JSON */ }
    if (res.status === 401 && j?.detail === "parent_pin_required" && !retried) {
      Pin.forget();
      await askPin();                       // throws if cancelled
      return api(path, { method, body, retried: true });
    }
    throw new Error(errorMessage(j, res.status));
  }
  return res.status === 204 ? null : res.json();
}

/** Show the PIN pad. Resolves once a correct PIN is entered; rejects on cancel. */
function askPin({ title = "Grown-ups only", sub = "Enter the 4-digit parent PIN", verify = true } = {}) {
  const dlg = $("#pin-modal");
  $("#pin-title").textContent = title;
  $("#pin-sub").textContent = sub;
  const dots = $$(".pin-dots i", dlg), err = $("#pin-err");
  let entry = "";
  const paint = () => dots.forEach((d, i) => d.classList.toggle("on", i < entry.length));
  err.textContent = ""; paint();
  return new Promise((resolve, reject) => {
    const finish = (ok) => {
      dlg.removeEventListener("click", onClick);
      document.removeEventListener("keydown", onKey, true);
      dlg.close();
      ok ? resolve(entry) : reject(new Error("A grown-up PIN is needed for that."));
    };
    const tryPin = async () => {
      if (!verify) return setTimeout(() => finish(true), 120);
      try {
        await fetch("/api/pin/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pin: entry }) })
          .then((r) => { if (!r.ok) throw new Error(); });
        Pin.remember(entry);
        updateLockButton();
        finish(true);
      } catch {
        err.textContent = "Oops — that's not it. Try again.";
        dlg.querySelector(".pin-box").classList.remove("shake"); void dlg.offsetWidth;
        dlg.querySelector(".pin-box").classList.add("shake");
        entry = ""; paint();
      }
    };
    const press = (d) => { if (entry.length < 4) { entry += d; paint(); if (entry.length === 4) tryPin(); } };
    const onClick = (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.digit) press(b.dataset.digit);
      else if (b.hasAttribute("data-pin-back")) { entry = entry.slice(0, -1); paint(); }
      else if (b.hasAttribute("data-pin-cancel")) finish(false);
    };
    const onKey = (e) => {
      if (!dlg.open) return;
      if (/^\d$/.test(e.key)) { e.preventDefault(); press(e.key); }
      else if (e.key === "Backspace") { entry = entry.slice(0, -1); paint(); }
      else if (e.key === "Escape") { e.preventDefault(); finish(false); }
    };
    dlg.addEventListener("click", onClick);
    document.addEventListener("keydown", onKey, true);
    dlg.showModal();
  });
}

function updateLockButton() {
  const b = $("#lock-btn");
  if (!b) return;
  b.hidden = !Pin.isSet;
  const unlocked = !!Pin.get();
  b.innerHTML = icon(unlocked ? "unlock" : "lock");
  b.classList.toggle("unlocked", unlocked);
  b.title = unlocked ? "Grown-up mode is on — click to lock" : "Locked — grown-ups tap to unlock";
}

/* ------------------------------------------------ celebrations (fun!) */
const STICKERS = {
  star: { emoji: "⭐", label: "Star", points: 1 },
  smiley: { emoji: "😊", label: "Smiley", points: 1 },
  heart: { emoji: "💖", label: "Heart", points: 1 },
  rainbow: { emoji: "🌈", label: "Rainbow", points: 2 },
  rocket: { emoji: "🚀", label: "Rocket", points: 3 },
  trophy: { emoji: "🏆", label: "Trophy", points: 5 },
};
const CHEERS = ["Awesome!", "Way to go!", "You did it!", "Super job!", "High five!", "Amazing!", "Woo-hoo!", "Great work!"];
const reducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
const celebratePref = (k, d = true) => { try { const v = localStorage.getItem("sfa." + k); return v === null ? d : v === "1"; } catch { return d; } };
const setCelebratePref = (k, on) => { try { localStorage.setItem("sfa." + k, on ? "1" : "0"); } catch { /* ignore */ } };

let audioCtx;
function playSound(kind = "ding") {
  if (!celebratePref("sound")) return;
  try {
    audioCtx ||= new (window.AudioContext || window.webkitAudioContext)();
    const notes = kind === "fanfare" ? [523.25, 659.25, 783.99, 1046.5, 783.99, 1046.5]
      : kind === "tick" ? [880] : [659.25, 783.99, 1046.5];
    const step = kind === "fanfare" ? 0.12 : 0.09;
    notes.forEach((f, i) => {
      const o = audioCtx.createOscillator(), g = audioCtx.createGain();
      const t0 = audioCtx.currentTime + i * step;
      o.type = "triangle"; o.frequency.value = f;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.18, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + (kind === "fanfare" && i === notes.length - 1 ? 0.6 : 0.25));
      o.connect(g).connect(audioCtx.destination);
      o.start(t0); o.stop(t0 + 0.7);
    });
  } catch { /* audio not available */ }
}

function confetti(amount = 140, emojis = null) {
  if (!celebratePref("confetti") || reducedMotion()) return;
  const cv = $("#confetti");
  const ctx = cv.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
  ctx.scale(dpr, dpr);
  const colors = ["#F7A8C8", "#C7A4FF", "#8FD3FF", "#8BE0BC", "#FFD66B", "#FFB38A", "#F2548A", "#3D8FEF"];
  const parts = Array.from({ length: amount }, (_, i) => ({
    x: innerWidth / 2 + (Math.random() - 0.5) * 120, y: innerHeight * 0.45,
    vx: (Math.random() - 0.5) * 16, vy: -Math.random() * 15 - 5,
    r: Math.random() * 6 + 4, rot: Math.random() * 6, vr: (Math.random() - 0.5) * 0.3,
    c: colors[i % colors.length], shape: i % 3, emoji: emojis && i % 7 === 0 ? emojis[i % emojis.length] : null,
  }));
  const t0 = performance.now();
  cv.classList.add("on");
  const frame = (t) => {
    const age = (t - t0) / 1000;
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    ctx.globalAlpha = Math.max(0, 1 - Math.max(0, age - 1.6) / 0.8);
    for (const p of parts) {
      p.vy += 0.45; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.rot += p.vr;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot);
      if (p.emoji) { ctx.font = `${p.r * 4}px serif`; ctx.fillText(p.emoji, -p.r * 2, p.r * 2); }
      else {
        ctx.fillStyle = p.c;
        if (p.shape === 0) ctx.fillRect(-p.r, -p.r / 2, p.r * 2, p.r);
        else if (p.shape === 1) { ctx.beginPath(); ctx.arc(0, 0, p.r / 1.3, 0, Math.PI * 2); ctx.fill(); }
        else { ctx.beginPath(); ctx.moveTo(0, -p.r); ctx.lineTo(p.r, p.r); ctx.lineTo(-p.r, p.r); ctx.fill(); }
      }
      ctx.restore();
    }
    if (age < 2.4) requestAnimationFrame(frame);
    else { ctx.clearRect(0, 0, innerWidth, innerHeight); cv.classList.remove("on"); }
  };
  requestAnimationFrame(frame);
}

let popTimer;
function popup(html, ms = 2200) {
  const el = $("#celebrate");
  el.innerHTML = `<div class="cel-card">${html}</div>`;
  el.classList.remove("show"); void el.offsetWidth; el.classList.add("show");
  clearTimeout(popTimer);
  popTimer = setTimeout(() => el.classList.remove("show"), ms);
  el.onclick = () => el.classList.remove("show");
}

/** Big happy moment after a task is completed. `reward` comes from the API (may be null). */
function celebrate(reward, { title = null } = {}) {
  const cheer = CHEERS[Math.floor(Math.random() * CHEERS.length)];
  if (!reward) {
    confetti(70); playSound("tick");
    popup(`<div class="cel-emoji">🎉</div><b>${cheer}</b>${title ? `<small>${esc(title)} is done</small>` : ""}`, 1500);
    return;
  }
  const m = State.byId[reward.member_id];
  const s = STICKERS[reward.sticker] || STICKERS.star;
  confetti(150, [s.emoji, "⭐"]); playSound("ding");
  popup(`
    <div class="cel-emoji">${s.emoji}</div>
    <b>${cheer}</b>
    <span class="cel-pts">+${reward.points} ⭐ ${m ? `for ${esc(m.name)}` : ""}</span>
    <small>${plural(reward.balance, "star")} in the jar${reward.streak >= 2 ? ` · 🔥 ${reward.streak}-day streak!` : ""}</small>`);
  if (reward.new_badges?.length) setTimeout(() => showBadges(reward.new_badges, m), 2300);
}

function showBadges(badges, m) {
  const b = badges[0];
  confetti(200, [b.emoji, "✨"]); playSound("fanfare");
  popup(`
    <div class="cel-ribbon">New badge!</div>
    <div class="cel-emoji badge-pop">${b.emoji}</div>
    <b>${esc(b.name)}</b>
    <small>${m ? `${esc(m.name)} — ` : ""}${esc(b.how)}</small>`, 3200);
  if (badges.length > 1) setTimeout(() => showBadges(badges.slice(1), m), 3300);
}

function initTopbar() {
  const snd = $("#sound-toggle");
  const paintSound = () => {
    const on = celebratePref("sound");
    snd.innerHTML = icon(on ? "volume" : "volume-x");
    snd.setAttribute("aria-pressed", on);
    snd.title = on ? "Sound is on" : "Sound is off";
  };
  snd.onclick = () => { setCelebratePref("sound", !celebratePref("sound")); paintSound(); if (celebratePref("sound")) playSound("tick"); };
  paintSound();
  $("#lock-btn").onclick = async () => {
    if (Pin.get()) { Pin.forget(); updateLockButton(); toast("Locked 🔒"); }
    else { try { await askPin(); toast("Grown-up mode on for 15 minutes"); } catch { /* cancelled */ } }
  };
  api("/api/pin").then((r) => { Pin.isSet = r.set; updateLockButton(); }).catch(() => {});
}

let toastTimer;
function toast(msg, isErr = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (isErr ? " err" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.className = "toast"), 2600);
}

/* ------------------------------------------------------ family members */
const State = { members: [], byId: {} };
async function loadMembers() {
  State.members = await api("/api/members");
  State.byId = Object.fromEntries(State.members.map((m) => [m.id, m]));
}
const colorOf = (id) => (id == null ? "family" : State.byId[id]?.color || "family");
const nameOf = (id, allLabel = "Everyone") => (id == null ? allLabel : State.byId[id]?.name || "—");
const initials = (name) => name.split(/\s+/).map((w) => w[0]).join("").slice(0, 2).toUpperCase();
const photoUrl = (m) => `/api/members/${m.id}/photo?v=${m.photo_version}`;
function avatar(m, size = "") {
  if (m.has_photo) {
    return `<span class="avatar photo c-${m.color} ${size}" aria-hidden="true"><img src="${photoUrl(m)}" alt="" loading="lazy" decoding="async"></span>`;
  }
  const txt = m.emoji || initials(m.name);
  return `<span class="avatar c-${m.color} ${size} ${m.emoji ? "emoji" : ""}" aria-hidden="true">${esc(txt)}</span>`;
}

/* ------------------------------------------------ profile photo picker */
/** HTML for a photo picker with a drag-to-position, slide-to-zoom circular cropper. */
function photoPickerHtml(m) {
  const placeholder = m && m.has_photo
    ? `<img src="${photoUrl(m)}" alt="Current photo of ${esc(m.name)}">`
    : `<span class="pp-empty">📷<small>No photo yet</small></span>`;
  return `
    <div class="photo-pick">
      <div class="pp-stage c-${m?.color || "purple"}">
        <canvas class="pp-canvas" width="480" height="480" hidden aria-label="Drag to move the photo"></canvas>
        <div class="pp-current">${placeholder}</div>
      </div>
      <div class="pp-controls">
        <label class="btn soft sm pp-choose">${icon("smile")} ${m?.has_photo ? "Change photo" : "Choose a photo"}
          <input type="file" accept="image/*" class="pp-file"></label>
        <button type="button" class="btn ghost sm pp-remove" ${m?.has_photo ? "" : "hidden"}>Remove photo</button>
        <label class="pp-zoom" hidden>Zoom <input type="range" min="1" max="4" step="0.01" value="1" aria-label="Zoom"></label>
        <small class="pp-hint" hidden>Drag the picture to move it. Slide to zoom.</small>
      </div>
    </div>`;
}

/** Wires up the picker inside `root`. Returns helpers to read the result. */
function bindPhotoPicker(root) {
  const cv = $(".pp-canvas", root), ctx = cv.getContext("2d"), S = cv.width;
  const cur = $(".pp-current", root), zoomWrap = $(".pp-zoom", root), zoom = $(".pp-zoom input", root);
  const hint = $(".pp-hint", root), removeBtn = $(".pp-remove", root);
  const st = { img: null, scale: 1, x: 0, y: 0, removed: false, drag: null };

  const k = () => (S / Math.min(st.img.width, st.img.height)) * st.scale;
  const draw = () => {
    if (!st.img) return;
    const w = st.img.width * k(), h = st.img.height * k();
    st.x = Math.min(0, Math.max(S - w, st.x));
    st.y = Math.min(0, Math.max(S - h, st.y));
    ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, S, S);
    ctx.drawImage(st.img, st.x, st.y, w, h);
  };
  const show = (editing) => {
    cv.hidden = !editing; cur.hidden = editing; zoomWrap.hidden = !editing; hint.hidden = !editing;
  };

  $(".pp-file", root).addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) { toast("That picture is too big — try a smaller one", true); return; }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      st.img = img; st.scale = 1; st.removed = false; zoom.value = 1;
      const w = img.width * k(), h = img.height * k();
      st.x = (S - w) / 2; st.y = (S - h) / 2;
      show(true); draw();
      removeBtn.hidden = false;
      URL.revokeObjectURL(url);
    };
    img.onerror = () => { toast("That picture type isn't supported here — try a JPG or PNG", true); URL.revokeObjectURL(url); };
    img.src = url;
  });

  zoom.addEventListener("input", () => {
    if (!st.img) return;
    const before = k();
    const cx = (S / 2 - st.x) / before, cy = (S / 2 - st.y) / before;
    st.scale = Number(zoom.value);
    const after = k();
    st.x = S / 2 - cx * after; st.y = S / 2 - cy * after;
    draw();
  });
  cv.addEventListener("wheel", (e) => {
    e.preventDefault();
    zoom.value = Math.min(4, Math.max(1, Number(zoom.value) - e.deltaY * 0.002));
    zoom.dispatchEvent(new Event("input"));
  }, { passive: false });
  cv.addEventListener("pointerdown", (e) => { st.drag = { x: e.clientX, y: e.clientY }; cv.setPointerCapture(e.pointerId); cv.classList.add("dragging"); });
  cv.addEventListener("pointermove", (e) => {
    if (!st.drag) return;
    const ratio = S / cv.getBoundingClientRect().width;
    st.x += (e.clientX - st.drag.x) * ratio; st.y += (e.clientY - st.drag.y) * ratio;
    st.drag = { x: e.clientX, y: e.clientY };
    draw();
  });
  const stop = () => { st.drag = null; cv.classList.remove("dragging"); };
  cv.addEventListener("pointerup", stop); cv.addEventListener("pointercancel", stop);
  cv.addEventListener("keydown", (e) => {   // arrow keys nudge the picture
    const d = { ArrowLeft: [12, 0], ArrowRight: [-12, 0], ArrowUp: [0, 12], ArrowDown: [0, -12] }[e.key];
    if (d) { e.preventDefault(); st.x += d[0]; st.y += d[1]; draw(); }
  });
  cv.tabIndex = 0;

  removeBtn.addEventListener("click", () => {
    st.img = null; st.removed = true;
    cur.innerHTML = `<span class="pp-empty">📷<small>Photo will be removed</small></span>`;
    show(false); removeBtn.hidden = true;
  });

  return {
    changed: () => !!st.img || st.removed,
    removed: () => st.removed && !st.img,
    dataUrl: () => {
      const out = document.createElement("canvas");
      out.width = out.height = 320;
      out.getContext("2d").drawImage(cv, 0, 0, 320, 320);
      return out.toDataURL("image/jpeg", 0.86);
    },
  };
}

async function savePhoto(memberId, picker) {
  if (picker.removed()) await api(`/api/members/${memberId}/photo`, { method: "DELETE" });
  else if (picker.changed()) await api(`/api/members/${memberId}/photo`, { method: "PUT", body: { data: picker.dataUrl() } });
}

/** Stand-alone "change my picture" window (Family page, Kid Mode). No PIN needed. */
function openPhotoEditor(m) {
  let picker;
  openModal(`${m.name}'s picture`, photoPickerHtml(m), {
    submitLabel: "Save picture",
    onOpen(form) { picker = bindPhotoPicker(form); },
    async onSubmit() {
      if (!picker.changed()) return;
      await savePhoto(m.id, picker);
      playSound("ding");
      toast(picker.removed() ? "Photo removed" : "Looking great! 📸");
      changed();
    },
  });
}

/** Tell every widget on the page to reload. */
async function changed() {
  try { await loadMembers(); } catch { /* keep old list */ }
  document.dispatchEvent(new CustomEvent("fam:changed"));
}

/* --------------------------------------------------------------- modal */
function openModal(title, bodyHtml, { submitLabel = "Save", onSubmit, onDelete, onOpen } = {}) {
  const dlg = $("#modal");
  const form = $("#modal-form");
  form.innerHTML = `
    <div class="modal-head"><h3>${esc(title)}</h3>
      <button type="button" class="icon-btn" data-close aria-label="Close">${icon("x")}</button></div>
    <div class="modal-body">${bodyHtml}<p class="form-error" hidden></p></div>
    <div class="modal-foot">
      ${onDelete ? `<button type="button" class="btn danger" data-delete>Delete</button>` : ""}
      <span class="spacer"></span>
      <button type="button" class="btn ghost" data-close>Cancel</button>
      <button type="submit" class="btn primary">${esc(submitLabel)}</button>
    </div>`;
  const errEl = $(".form-error", form);
  const showErr = (m) => { errEl.textContent = m; errEl.hidden = false; };

  $$("[data-close]", form).forEach((b) => (b.onclick = () => dlg.close()));
  form.onsubmit = async (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const btn = $("button[type=submit]", form);
    btn.disabled = true;
    try { await onSubmit(new FormData(form), form); dlg.close(); }
    catch (err) { showErr(err.message); }
    finally { btn.disabled = false; }
  };
  if (onDelete) {
    const del = $("[data-delete]", form);
    let armed = false;
    del.onclick = async () => {
      if (!armed) { armed = true; del.classList.add("armed"); del.textContent = "Tap again to delete"; return; }
      try { await onDelete(); dlg.close(); } catch (err) { showErr(err.message); }
    };
  }
  onOpen?.(form);
  dlg.showModal();
  $("input:not([type=hidden]), select", form)?.focus();
}

const REC_OPTS = [
  ["none", "Doesn't repeat"],
  ["daily", "Every day"],
  ["weekdays", "Every weekday (Mon–Fri)"],
  ["weekly", "Every week"],
  ["biweekly", "Every 2 weeks"],
  ["monthly", "Every month"],
  ["quarterly", "Every 3 months"],
  ["semiannual", "Every 6 months"],
  ["yearly", "Every year"],
];
const REC_LABEL = { none: "One time", daily: "Daily", weekdays: "Weekdays", weekly: "Weekly", biweekly: "Every 2 weeks",
  monthly: "Monthly", quarterly: "Every 3 months", semiannual: "Every 6 months", yearly: "Yearly" };
const CATEGORY = { task: "Task", chore: "Chore", maintenance: "Home upkeep" };
const DEFAULT_STICKER = { task: ["star", 1], chore: ["smiley", 1], maintenance: ["trophy", 5] };
const recOptions = (sel) => REC_OPTS.map(([v, l]) => `<option value="${v}" ${v === sel ? "selected" : ""}>${l}</option>`).join("");
const memberOptions = (sel, allLabel) =>
  `<option value="" ${sel == null ? "selected" : ""}>${allLabel}</option>` +
  State.members.map((m) => `<option value="${m.id}" ${m.id === sel ? "selected" : ""}>${esc(m.name)}</option>`).join("");
const numOrNull = (v) => (v ? Number(v) : null);

function syncRepeatField(form) {
  const rec = form.elements.recurrence, until = form.elements.recurrence_end;
  const sync = () => { until.disabled = rec.value === "none"; };
  rec.addEventListener("change", sync);
  sync();
}

/* ---------------------------------------------------------- event form */
/** Mark one occurrence of an event done / not done. */
async function toggleEventDone(id, date) {
  try {
    const r = await api(`/api/events/${id}/toggle`, { method: "POST", body: { on_date: date } });
    if (r.done) { playSound("tick"); confetti(50); }
    toast(r.done ? "Marked done ✓" : "Marked not done");
    changed();
    return r.done;
  } catch (err) { toast(err.message, true); return null; }
}

async function openEventEditor(id = null, preset = {}, occ = null) {
  let ev = {
    title: "", member_id: null, start_date: iso(new Date()), start_time: "09:00", end_time: "10:00",
    location: "", notes: "", recurrence: "none", recurrence_end: null, ...preset,
  };
  if (id) {
    try { ev = await api(`/api/events/${id}`); } catch (err) { return toast(err.message, true); }
  }
  const allDay = !ev.start_time;
  const doneLine = id && occ ? `
    <label class="done-line ${occ.done ? "on" : ""}">
      <input type="checkbox" data-occ-done ${occ.done ? "checked" : ""}>
      <span class="box"></span><span>Done for ${fmtDay(occ.date)}</span>
    </label>` : "";
  const body = `${doneLine}
    <label class="field"><span>What's happening?</span>
      <input name="title" required maxlength="120" value="${esc(ev.title)}" placeholder="e.g. Soccer practice"></label>
    <div class="row2">
      <label class="field"><span>Who</span><select name="member_id">${memberOptions(ev.member_id, "Whole family")}</select></label>
      <label class="field"><span>Date</span><input type="date" name="start_date" required value="${ev.start_date}"></label>
    </div>
    <label class="check-line"><input type="checkbox" name="all_day" ${allDay ? "checked" : ""}> All day</label>
    <div class="row2 times">
      <label class="field"><span>Starts</span><input type="time" name="start_time" value="${ev.start_time || "09:00"}"></label>
      <label class="field"><span>Ends</span><input type="time" name="end_time" value="${ev.end_time || ""}"></label>
    </div>
    <div class="row2">
      <label class="field"><span>Repeats</span><select name="recurrence">${recOptions(ev.recurrence)}</select></label>
      <label class="field"><span>Repeat until (optional)</span><input type="date" name="recurrence_end" value="${ev.recurrence_end || ""}"></label>
    </div>
    <label class="field"><span>Where</span><input name="location" maxlength="120" value="${esc(ev.location)}" placeholder="Optional"></label>
    <label class="field"><span>Notes</span><textarea name="notes" rows="2" maxlength="2000" placeholder="Optional">${esc(ev.notes)}</textarea></label>
    ${id && ev.recurrence !== "none" ? `<p class="hint">${icon("repeat")} This event repeats — changes apply to every occurrence.</p>` : ""}`;

  openModal(id ? "Edit event" : "New event", body, {
    submitLabel: id ? "Save changes" : "Add event",
    onOpen(form) {
      syncRepeatField(form);
      const occBox = $("[data-occ-done]", form);
      if (occBox) occBox.addEventListener("change", async () => {
        const done = await toggleEventDone(id, occ.date);
        if (done === null) occBox.checked = !occBox.checked;
        occBox.closest(".done-line").classList.toggle("on", occBox.checked);
      });
      const ad = form.elements.all_day;
      const sync = () => $$(".times input", form).forEach((i) => (i.disabled = ad.checked));
      ad.addEventListener("change", sync);
      sync();
    },
    async onSubmit(fd) {
      const allDay = fd.get("all_day") === "on";
      const payload = {
        title: fd.get("title").trim(),
        member_id: numOrNull(fd.get("member_id")),
        start_date: fd.get("start_date"),
        start_time: allDay ? null : fd.get("start_time") || null,
        end_time: allDay ? null : fd.get("end_time") || null,
        recurrence: fd.get("recurrence"),
        recurrence_end: fd.get("recurrence_end") || null,
        location: fd.get("location") || "",
        notes: fd.get("notes") || "",
      };
      await api(id ? `/api/events/${id}` : "/api/events", { method: id ? "PUT" : "POST", body: payload });
      toast(id ? "Event updated" : "Event added");
      changed();
    },
    onDelete: id ? async () => {
      await api(`/api/events/${id}`, { method: "DELETE" });
      toast("Event deleted");
      changed();
    } : null,
  });
}

/* ----------------------------------------------------------- task form */
async function openTaskEditor(id = null, preset = {}) {
  const cat0 = preset.category || "task";
  let t = { title: "", member_id: null, due_date: iso(new Date()), due_time: null, notes: "", recurrence: "none",
    recurrence_end: null, category: cat0, sticker: DEFAULT_STICKER[cat0][0], points: DEFAULT_STICKER[cat0][1],
    rotation: [], rotate_every: "week", ...preset };
  if (id) {
    try { t = await api(`/api/tasks/${id}`); } catch (err) { return toast(err.message, true); }
  }
  const rot = new Set((t.rotation || []).map(Number));
  const noun = { task: "Task", chore: "Chore", maintenance: "Upkeep job" }[t.category] || "Task";
  const body = `
    <label class="field"><span>${noun}</span>
      <input name="title" required maxlength="120" value="${esc(t.title)}" placeholder="${t.category === "maintenance" ? "e.g. Change air filter" : t.category === "chore" ? "e.g. Feed the dog" : "e.g. Pack soccer bag"}"></label>
    <div class="row2">
      <label class="field"><span>Type</span><select name="category">${Object.entries(CATEGORY).map(([k, l]) => `<option value="${k}" ${k === t.category ? "selected" : ""}>${l}</option>`).join("")}</select></label>
      <label class="field"><span>Time (optional)</span><input type="time" name="due_time" value="${t.due_time || ""}"></label>
    </div>
    <label class="field who-field"><span>Who</span><select name="member_id">${memberOptions(t.member_id, "Everyone")}</select></label>
    <div class="field rotation-field">
      <span>Take turns (optional) — pick 2 or more to rotate</span>
      <div class="rot-picks">${State.members.map((m) => `
        <label class="rot-pick c-${m.color}"><input type="checkbox" name="rotation" value="${m.id}" ${rot.has(m.id) ? "checked" : ""}>${avatar(m, "xs")}<span>${esc(m.name)}</span></label>`).join("")}
      </div>
      <label class="rot-every">Switch every
        <select name="rotate_every"><option value="week" ${t.rotate_every !== "day" ? "selected" : ""}>week</option><option value="day" ${t.rotate_every === "day" ? "selected" : ""}>day</option></select>
      </label>
    </div>
    <div class="field"><span>Reward sticker</span>
      <div class="sticker-pick">${Object.entries(STICKERS).map(([k, st]) => `
        <label class="stk-opt" title="${st.label}"><input type="radio" name="sticker" value="${k}" data-pts="${st.points}" ${k === t.sticker ? "checked" : ""}><span>${st.emoji}</span></label>`).join("")}
        <label class="pts-field">worth <input type="number" name="points" min="0" max="50" value="${t.points ?? 1}"> ⭐</label>
      </div>
    </div>
    <div class="row2">
      <label class="field"><span>${t.recurrence === "none" ? "Due date" : "Starting"}</span><input type="date" name="due_date" required value="${t.due_date}"></label>
      <label class="field"><span>Repeats</span><select name="recurrence">${recOptions(t.recurrence)}</select></label>
    </div>
    <label class="field"><span>Repeat until (optional)</span><input type="date" name="recurrence_end" value="${t.recurrence_end || ""}"></label>
    <div class="field"><span>Checklist (optional) — items get their own check marks</span>
      <ul class="cl-edit">${(t.items || []).map(checklistEditRow).join("")}</ul>
      <button type="button" class="btn soft sm cl-add" data-add-item>${icon("plus")} Add checklist item</button>
    </div>
    <label class="field"><span>Notes</span><textarea name="notes" rows="2" maxlength="2000" placeholder="Optional">${esc(t.notes)}</textarea></label>
    <p class="hint">${icon("star")} Stars go to whoever does it that day. Tasks for "Everyone" get confetti but no personal stars. Checking off a repeating task only counts for that day.</p>`;

  openModal(id ? `Edit ${noun.toLowerCase()}` : `New ${noun.toLowerCase()}`, body, {
    submitLabel: id ? "Save changes" : `Add ${noun.toLowerCase()}`,
    onOpen(form) {
      syncRepeatField(form);
      const syncRot = () => {
        const picked = $$("input[name=rotation]:checked", form).length;
        $(".who-field", form).classList.toggle("dim", picked >= 2);
        $(".rot-every", form).hidden = picked < 2;
        $(".rotation-field", form).hidden = form.elements.category.value !== "chore";
      };
      form.addEventListener("change", (e) => {
        if (e.target.name === "rotation" || e.target.name === "category") syncRot();
        if (e.target.name === "sticker") form.elements.points.value = e.target.dataset.pts;
      });
      syncRot();
      const list = $(".cl-edit", form);
      const addRow = (after = null) => {
        const tmp = document.createElement("ul");
        tmp.innerHTML = checklistEditRow({ id: null, title: "" });
        const li = tmp.firstElementChild;
        after ? after.after(li) : list.append(li);
        $("input", li).focus();
      };
      $("[data-add-item]", form).onclick = () => addRow();
      list.addEventListener("click", (e) => {
        const rm = e.target.closest("[data-remove-item]");
        if (rm) rm.closest("li").remove();
      });
      list.addEventListener("keydown", (e) => {
        // Enter adds the next item instead of submitting the form
        if (e.key === "Enter" && e.target.matches(".cl-input")) { e.preventDefault(); addRow(e.target.closest("li")); }
      });
    },
    async onSubmit(fd, form) {
      const items = $$(".cl-edit li", form)
        .map((li) => ({ id: li.dataset.id ? Number(li.dataset.id) : null, title: $("input", li).value.trim() }))
        .filter((it) => it.title);
      const payload = {
        title: fd.get("title").trim(),
        member_id: numOrNull(fd.get("member_id")),
        due_date: fd.get("due_date"),
        due_time: fd.get("due_time") || null,
        recurrence: fd.get("recurrence"),
        recurrence_end: fd.get("recurrence_end") || null,
        notes: fd.get("notes") || "",
        items,
        category: fd.get("category"),
        sticker: fd.get("sticker") || "star",
        points: Number(fd.get("points") || 0),
        rotation: fd.get("category") === "chore" ? fd.getAll("rotation").map(Number) : [],
        rotate_every: fd.get("rotate_every") || "week",
      };
      await api(id ? `/api/tasks/${id}` : "/api/tasks", { method: id ? "PUT" : "POST", body: payload });
      toast(id ? "Saved" : `${noun} added`);
      changed();
    },
    onDelete: id ? async () => {
      await api(`/api/tasks/${id}`, { method: "DELETE" });
      toast("Task deleted");
      changed();
    } : null,
  });
}

/* --------------------------------------------------------- member form */
const COLORS = ["pink", "blue", "green", "yellow", "purple", "peach", "teal", "coral"];
function openMemberEditor(m = null) {
  const cur = m || { name: "", role: "kid", color: COLORS.find((c) => !State.members.some((x) => x.color === c)) || "pink", emoji: "" };
  let picker;
  const body = `
    <div class="field"><span>Profile picture</span>${photoPickerHtml(m ? { ...m } : null)}</div>
    <div class="row2">
      <label class="field"><span>Name</span><input name="name" required maxlength="50" value="${esc(cur.name)}" placeholder="e.g. Grandma"></label>
      <label class="field"><span>Role</span><select name="role">
        ${["parent", "kid", "other"].map((r) => `<option value="${r}" ${r === cur.role ? "selected" : ""}>${r[0].toUpperCase() + r.slice(1)}</option>`).join("")}
      </select></label>
    </div>
    <label class="field"><span>Emoji (optional — shown when there's no photo)</span>
      <input name="emoji" maxlength="8" value="${esc(cur.emoji)}" placeholder="e.g. 🌸"></label>
    <div class="field"><span>Color</span><div class="swatches">
      ${COLORS.map((c) => `<label class="swatch c-${c}" title="${c}"><input type="radio" name="color" value="${c}" ${c === cur.color ? "checked" : ""} aria-label="${c}"><span></span></label>`).join("")}
    </div></div>
    ${m ? `<p class="hint">Deleting ${esc(m.name)} keeps their events and tasks — they move to the whole family.</p>` : ""}`;

  openModal(m ? `Edit ${m.name}` : "Add family member", body, {
    submitLabel: m ? "Save changes" : "Add member",
    onOpen(form) { picker = bindPhotoPicker(form); },
    async onSubmit(fd) {
      const payload = { name: fd.get("name").trim(), role: fd.get("role"), emoji: (fd.get("emoji") || "").trim(), color: fd.get("color") };
      const saved = await api(m ? `/api/members/${m.id}` : "/api/members", { method: m ? "PUT" : "POST", body: payload });
      try { await savePhoto(saved.id, picker); } catch (err) { toast(`Saved, but the photo didn't upload: ${err.message}`, true); }
      toast(m ? "Saved" : `Welcome, ${payload.name}!`);
      changed();
    },
    onDelete: m ? async () => {
      await api(`/api/members/${m.id}`, { method: "DELETE" });
      toast(`${m.name} removed`);
      changed();
    } : null,
  });
}

/* ------------------------------------------------------------ task list */
const checklistEditRow = (it) => `
  <li ${it.id ? `data-id="${it.id}"` : ""}>
    <span class="cl-dot" aria-hidden="true"></span>
    <input class="cl-input" maxlength="120" value="${esc(it.title)}" placeholder="Checklist item" aria-label="Checklist item">
    <button type="button" class="icon-btn sm" data-remove-item aria-label="Remove item">${icon("x")}</button>
  </li>`;

State.openTasks = new Set(); // which checklists are dropped down, kept across re-renders

function taskRow(t) {
  const color = colorOf(t.member_id);
  const key = `${t.id}|${t.date}`;
  const hasItems = t.items_total > 0;
  const open = hasItems && State.openTasks.has(key);
  const pct = hasItems ? Math.round((t.items_done / t.items_total) * 100) : 0;
  return `<li class="task c-${color} ${t.done ? "done" : ""} ${open ? "open" : ""}" data-id="${t.id}" data-date="${t.date}">
    <div class="task-main">
      <label class="check"><input type="checkbox" class="task-cb" ${t.done ? "checked" : ""} aria-label="Mark ${esc(t.title)} done"><span class="box"></span></label>
      <button type="button" class="task-title" data-edit><span>${esc(t.title)}</span>${t.recurrence !== "none" ? icon("repeat") : ""}${t.overdue ? `<em class="tag-overdue">Overdue · ${fmtDay(t.date)}</em>` : ""}${t.points > 0 && t.member_id != null ? `<em class="stk-badge ${t.done ? "got" : ""}" title="Earns ${plural(t.points, "star")}">${(STICKERS[t.sticker] || STICKERS.star).emoji}<b>${t.points}</b></em>` : ""}${t.category === "maintenance" ? `<em class="cat-tag">upkeep</em>` : t.category === "chore" ? `<em class="cat-tag chore">chore</em>` : ""}</button>
      ${hasItems ? `<button type="button" class="cl-toggle ${t.items_done === t.items_total ? "complete" : ""}" data-expand aria-expanded="${open}"
          aria-label="Checklist, ${t.items_done} of ${t.items_total} checked. ${open ? "Hide" : "Show"} items">
          ${icon("list")}<span>${t.items_done}/${t.items_total}</span>${icon("chevron-down", "chev")}</button>` : `<span></span>`}
      <span class="pill">${esc(nameOf(t.member_id, "All"))}</span>
      <span class="who" title="${esc(nameOf(t.member_id, "Everyone"))}">${State.byId[t.member_id] ? avatar(State.byId[t.member_id], "xs") : `<span class="avatar xs c-family all">All</span>`}</span>
      <span class="task-time">${t.due_time ? fmtTime(t.due_time) : ""}</span>
    </div>
    ${hasItems ? `
    <div class="subitems" ${open ? "" : "hidden"}>
      <div class="sub-bar"><i style="width:${pct}%"></i></div>
      <ul>${t.items.map((i) => `
        <li class="subitem ${i.done ? "done" : ""}" data-item="${i.id}">
          <label class="sub-check"><input type="checkbox" class="item-cb" ${i.done ? "checked" : ""}><span class="box"></span><span class="sub-title">${esc(i.title)}</span></label>
        </li>`).join("")}</ul>
    </div>` : ""}
  </li>`;
}

function bindTaskList(ul) {
  ul.addEventListener("change", async (e) => {
    const cb = e.target;
    const li = cb.closest(".task");
    if (!li) return;

    if (cb.matches(".item-cb")) {
      const sub = cb.closest(".subitem");
      sub.classList.toggle("done", cb.checked);
      try {
        const r = await api(`/api/tasks/${li.dataset.id}/items/${sub.dataset.item}/toggle`, { method: "POST", body: { on_date: li.dataset.date } });
        if (r.task_done && cb.checked) celebrate(r.reward, { title: $(".task-title span", li).textContent });
        else if (cb.checked) playSound("tick");
        changed();
      } catch (err) {
        cb.checked = !cb.checked;
        sub.classList.toggle("done", cb.checked);
        toast(err.message, true);
      }
      return;
    }

    if (!cb.matches(".task-cb")) return;
    li.classList.toggle("done", cb.checked);
    try {
      const r = await api(`/api/tasks/${li.dataset.id}/toggle`, { method: "POST", body: { on_date: li.dataset.date } });
      if (r.done) celebrate(r.reward, { title: $(".task-title span", li).textContent });
      changed();
    } catch (err) {
      cb.checked = !cb.checked;
      li.classList.toggle("done", cb.checked);
      toast(err.message, true);
    }
  });

  ul.addEventListener("click", (e) => {
    const ex = e.target.closest("[data-expand]");
    if (ex) {
      const li = ex.closest(".task");
      const key = `${li.dataset.id}|${li.dataset.date}`;
      const open = !State.openTasks.has(key);
      open ? State.openTasks.add(key) : State.openTasks.delete(key);
      li.classList.toggle("open", open);
      ex.setAttribute("aria-expanded", open);
      $(".subitems", li).hidden = !open;
      return;
    }
    const b = e.target.closest("[data-edit]");
    if (b) openTaskEditor(Number(b.closest(".task").dataset.id));
  });
}

function taskChips(el, tasks, filter) {
  const n = (k) => tasks.filter((t) => String(t.member_id) === k).length;
  el.innerHTML =
    `<button type="button" class="fchip c-all ${filter === "all" ? "on" : ""}" data-f="all">All (${tasks.length})</button>` +
    State.members.map((m) => `<button type="button" class="fchip c-${m.color} ${filter === String(m.id) ? "on" : ""}" data-f="${m.id}">${esc(m.name)} (${n(String(m.id))})</button>`).join("");
}
const applyTaskFilter = (tasks, f) => (f === "all" ? tasks : tasks.filter((t) => String(t.member_id) === f));

/* ------------------------------------------------- dropdown menus/prefs */
const Prefs = (() => {
  let p = {};
  try { p = JSON.parse(localStorage.getItem("sfa.prefs")) || {}; } catch { /* storage unavailable */ }
  return {
    get: (k, d) => ({ ...d, ...(p[k] || {}) }),
    set: (k, v) => { p[k] = v; try { localStorage.setItem("sfa.prefs", JSON.stringify(p)); } catch { /* ignore */ } },
  };
})();

const SHOW_OPTS = [["all", "All tasks"], ["todo", "To do"], ["done", "Completed"]];
const SORT_OPTS = [["time", "By time"], ["person", "By person"], ["status", "To-do first"]];
const EVENT_SHOW_OPTS = [["all", "All events"], ["todo", "Not done yet"], ["done", "Done"]];

function dropdown(name, label, opts, value) {
  return `<label class="dd"><span class="dd-label">${label}</span>
    <select class="dd-select" data-ctl="${name}">${opts.map(([v, l]) => `<option value="${v}" ${v === value ? "selected" : ""}>${l}</option>`).join("")}</select></label>`;
}

/** Renders Show + Sort dropdowns into `el`; `ctl` is mutated and saved under `prefKey`. */
function taskControls(el, ctl, prefKey, onChange) {
  el.innerHTML = dropdown("show", "Show", SHOW_OPTS, ctl.show) + dropdown("sort", "Sort", SORT_OPTS, ctl.sort);
  el.onchange = (e) => {
    const sel = e.target.closest("[data-ctl]");
    if (!sel) return;
    ctl[sel.dataset.ctl] = sel.value;
    Prefs.set(prefKey, { ...ctl });
    onChange();
  };
}

function applyControls(tasks, ctl) {
  const shown = tasks.filter((t) => ctl.show === "all" || (ctl.show === "done" ? t.done : !t.done));
  const order = Object.fromEntries(State.members.map((m, i) => [m.id, i]));
  const tkey = (t) => t.due_time || "99:99";
  const byTime = (a, b) => (b.overdue - a.overdue) || tkey(a).localeCompare(tkey(b)) || a.title.localeCompare(b.title);
  const cmp = {
    time: byTime,
    person: (a, b) => (order[a.member_id] ?? 999) - (order[b.member_id] ?? 999) || byTime(a, b),
    status: (a, b) => a.done - b.done || byTime(a, b),
  }[ctl.sort] || byTime;
  return [...shown].sort(cmp);
}

const emptyTasksMsg = (ctl) =>
  ctl.show === "done" ? "Nothing checked off yet — you've got this!"
  : ctl.show === "todo" ? "All done! Everything is checked off. 🎉"
  : "No tasks here — enjoy the free time!";

/* ------------------------------------------------------------- calendar */
function layoutDay(items) {
  // Side-by-side layout for overlapping events.
  items.sort((a, b) => a.s - b.s || b.e - a.e);
  let cluster = [], clusterEnd = -1;
  const flush = () => {
    const lanes = [];
    for (const it of cluster) {
      let i = lanes.findIndex((end) => end <= it.s);
      if (i < 0) { i = lanes.length; lanes.push(0); }
      lanes[i] = it.e;
      it.lane = i;
    }
    cluster.forEach((it) => (it.lanes = lanes.length));
    cluster = [];
  };
  for (const it of items) {
    if (cluster.length && it.s >= clusterEnd) { flush(); clusterEnd = -1; }
    cluster.push(it);
    clusterEnd = Math.max(clusterEnd, it.e);
  }
  if (cluster.length) flush();
  return items;
}

class CalendarView {
  constructor(root, opts = {}) {
    Object.assign(this, {
      root, view: "week", anchor: new Date(), filter: new Set(), status: "all", compact: false,
      startHour: 6, endHour: 22, scrollTo: 7, title: "Calendar",
    }, opts);
    this.events = [];
    this.root.innerHTML = `
      <div class="cal-toolbar">
        <div class="cal-title"><span class="head-ic c-blue">${icon("calendar")}</span><h2>${esc(this.title)}</h2>${this.compact
          ? `<button type="button" class="icon-btn add-ev" data-act="add" aria-label="Add event" title="Add event">${icon("plus")}</button>` : ""}</div>
        <div class="cal-nav">
          <button type="button" class="btn ghost sm" data-act="today">Today</button>
          <button type="button" class="icon-btn" data-act="prev" aria-label="Previous">${icon("chevron-left")}</button>
          <button type="button" class="icon-btn" data-act="next" aria-label="Next">${icon("chevron-right")}</button>
          <span class="cal-label" aria-live="polite"></span>
        </div>
        <div class="seg">${["day", "week", "month"].map((v) => `<button type="button" data-view="${v}">${v[0].toUpperCase() + v.slice(1)}</button>`).join("")}</div>
        ${this.compact ? "" : `<button type="button" class="btn primary sm" data-act="add">${icon("plus")} Event</button>`}
      </div>
      <div class="cal-body"></div>`;
    this.body = $(".cal-body", this.root);
    this.labelEl = $(".cal-label", this.root);
    this.root.addEventListener("click", (e) => this.onClick(e));
    this.root.addEventListener("keydown", (e) => {
      if ((e.key === "Enter" || e.key === " ") && e.target.matches(".ev[role=button]")) { e.preventDefault(); e.target.click(); }
    });
  }

  range() {
    if (this.view === "day") return [this.anchor, this.anchor];
    if (this.view === "week") { const s = startOfWeek(this.anchor); return [s, addDays(s, 6)]; }
    const s = startOfWeek(new Date(this.anchor.getFullYear(), this.anchor.getMonth(), 1));
    return [s, addDays(s, 41)];
  }

  label() {
    const a = this.anchor;
    if (this.view === "day") return `${DOW_LONG[a.getDay()]}, ${MON[a.getMonth()]} ${a.getDate()}, ${a.getFullYear()}`;
    if (this.view === "month") return `${MONTH[a.getMonth()]} ${a.getFullYear()}`;
    const [s, e] = this.range();
    return `${MON[s.getMonth()]} ${s.getDate()} – ${s.getMonth() !== e.getMonth() ? MON[e.getMonth()] + " " : ""}${e.getDate()}, ${e.getFullYear()}`;
  }

  visible() {
    return this.events.filter((ev) =>
      (!this.filter.size || this.filter.has(ev.member_id == null ? "family" : String(ev.member_id))) &&
      (this.status === "all" || (this.status === "done" ? ev.done : !ev.done)));
  }

  async refresh() {
    $$("[data-view]", this.root).forEach((b) => b.classList.toggle("on", b.dataset.view === this.view));
    this.labelEl.textContent = this.label();
    const [s, e] = this.range();
    try { this.events = await api(`/api/events?start=${iso(s)}&end=${iso(e)}`); }
    catch (err) { this.events = []; toast(err.message, true); }
    this.draw();
  }

  draw() {
    if (this.view === "month") return this.drawMonth();
    const days = this.view === "day" ? [this.anchor] : Array.from({ length: 7 }, (_, i) => addDays(startOfWeek(this.anchor), i));
    this.drawTime(days);
  }

  drawTime(days) {
    const H = (this.hourPx = this.compact ? 40 : 48);
    const sh = this.startHour, hours = this.endHour - this.startHour;
    const todayKey = iso(new Date());
    const timed = {}, allDay = {};
    days.forEach((d) => { timed[iso(d)] = []; allDay[iso(d)] = []; });
    for (const ev of this.visible()) {
      if (!(ev.date in timed)) continue;
      (ev.start_time ? timed : allDay)[ev.date].push(ev);
    }
    const cols = `grid-template-columns:54px repeat(${days.length},minmax(0,1fr))`;
    const hourLabel = (h) => `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`;
    const evLabel = (ev) => `${ev.title}, ${fmtTime(ev.start_time)}${ev.end_time ? " to " + fmtTime(ev.end_time) : ""}, ${nameOf(ev.member_id, "Whole family")}`;

    const head = days.map((d) => `
      <button type="button" class="tg-dayhead ${iso(d) === todayKey ? "is-today" : ""}" data-goto="${iso(d)}">
        <span class="dow">${DOW[d.getDay()]}</span><span class="dnum">${MON[d.getMonth()]} ${d.getDate()}</span></button>`).join("");

    const hasAllDay = Object.values(allDay).some((a) => a.length);
    const allRow = hasAllDay ? `<div class="tg-allday" style="${cols}"><div class="tg-gutter">all day</div>${days.map((d) =>
      `<div class="tg-adcell">${allDay[iso(d)].map((ev) => `<button type="button" class="chip-ev c-${colorOf(ev.member_id)} ${ev.done ? "done" : ""}" data-ev="${ev.id}" data-date="${ev.date}">${ev.done ? icon("tick") : ""}${esc(ev.title)}</button>`).join("")}</div>`).join("")}</div>` : "";

    const times = Array.from({ length: hours }, (_, i) => `<span style="top:${i * H}px">${hourLabel(sh + i)}</span>`).join("");
    const now = new Date(), nowMin = now.getHours() * 60 + now.getMinutes();

    const colsHtml = days.map((d) => {
      const key = iso(d);
      const items = layoutDay(timed[key].map((ev) => {
        const s = toMin(ev.start_time);
        return { ev, s, e: ev.end_time ? toMin(ev.end_time) : s + 60 };
      }));
      const blocks = items.map(({ ev, s, e, lane, lanes }) => {
        const top = Math.max(0, s - sh * 60) / 60 * H;
        const bottom = Math.min(hours * 60, e - sh * 60) / 60 * H;
        if (bottom <= 0 || top >= hours * H) return "";
        const ht = Math.max(22, bottom - top);
        const lbl = evLabel(ev) + (ev.done ? " (done)" : "");
        return `<div class="ev c-${colorOf(ev.member_id)} ${ev.done ? "done" : ""}" role="button" tabindex="0" data-ev="${ev.id}" data-date="${ev.date}"
          style="top:${top}px;height:${ht}px;left:${(lane / lanes) * 100}%;width:${100 / lanes}%" title="${esc(lbl)}" aria-label="${esc(lbl)}">
          <span class="ev-inner"><b>${esc(ev.title)}</b>${ht >= 38 ? `<small>${fmtTime(ev.start_time, true)}${ev.end_time ? " – " + fmtTime(ev.end_time, true) : ""}</small>` : ""}</span>
          <button type="button" class="ev-check" data-evdone aria-pressed="${ev.done}" aria-label="${ev.done ? "Mark not done" : "Mark done"}: ${esc(ev.title)}">${icon("tick")}</button></div>`;
      }).join("");
      const nowLine = key === todayKey && nowMin >= sh * 60 && nowMin <= this.endHour * 60
        ? `<div class="now-line" style="top:${(nowMin - sh * 60) / 60 * H}px"></div>` : "";
      return `<div class="tg-col ${key === todayKey ? "is-today" : ""}" data-date="${key}">${blocks}${nowLine}</div>`;
    }).join("");

    this.body.innerHTML = `
      <div class="tg" style="--hour:${H}px;--grid-h:${hours * H}px">
        <div class="tg-inner ${days.length === 1 ? "single" : ""}">
          <div class="tg-head" style="${cols}"><div></div>${head}</div>
          ${allRow}
          <div class="tg-scroll" style="max-height:${this.compact ? 580 : 680}px">
            <div class="tg-grid" style="${cols}"><div class="tg-times" style="height:${hours * H}px">${times}</div>${colsHtml}</div>
          </div>
        </div>
      </div>`;
    const sc = $(".tg-scroll", this.body);
    if (this.scrollTo > sh) sc.scrollTop = (this.scrollTo - sh) * H;
  }

  drawMonth() {
    const [gs] = this.range();
    const month = this.anchor.getMonth();
    const todayKey = iso(new Date());
    const by = {};
    for (const ev of this.visible()) (by[ev.date] ||= []).push(ev);
    let html = `<div class="month">${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => `<div class="month-dow">${d}</div>`).join("")}`;
    for (let i = 0; i < 42; i++) {
      const d = addDays(gs, i), k = iso(d), list = by[k] || [];
      html += `<div class="mc ${d.getMonth() !== month ? "out" : ""} ${k === todayKey ? "today" : ""}" data-date="${k}">
        <span class="mc-num">${d.getDate()}</span>
        ${list.slice(0, 3).map((ev) => `<button type="button" class="chip-ev c-${colorOf(ev.member_id)} ${ev.done ? "done" : ""}" data-ev="${ev.id}" data-date="${ev.date}" title="${esc(ev.title)}${ev.done ? " (done)" : ""}">${ev.done ? icon("tick") : ev.start_time ? `<i>${fmtTime(ev.start_time, true)}</i> ` : ""}${esc(ev.title)}</button>`).join("")}
        ${list.length > 3 ? `<span class="more">+${list.length - 3} more</span>` : ""}</div>`;
    }
    this.body.innerHTML = html + "</div>";
  }

  onClick(e) {
    const t = e.target;
    const view = t.closest("[data-view]")?.dataset.view;
    if (view) { this.view = view; return this.refresh(); }

    const act = t.closest("[data-act]")?.dataset.act;
    if (act === "today") { this.anchor = new Date(); return this.refresh(); }
    if (act === "prev" || act === "next") {
      const s = act === "next" ? 1 : -1;
      if (this.view === "day") this.anchor = addDays(this.anchor, s);
      else if (this.view === "week") this.anchor = addDays(this.anchor, 7 * s);
      else this.anchor = new Date(this.anchor.getFullYear(), this.anchor.getMonth() + s, 1);
      return this.refresh();
    }
    if (act === "add") {
      const [s, en] = this.range();
      const today = new Date();
      const inRange = iso(today) >= iso(s) && iso(today) <= iso(en);
      const day = this.view === "day" ? this.anchor : inRange ? today : this.view === "month" ? new Date(this.anchor.getFullYear(), this.anchor.getMonth(), 1) : s;
      return openEventEditor(null, { start_date: iso(day) });
    }

    const doneBtn = t.closest("[data-evdone]");
    if (doneBtn) {
      const host = doneBtn.closest("[data-ev]");
      return toggleEventDone(Number(host.dataset.ev), host.dataset.date);
    }
    const evEl = t.closest("[data-ev]");
    if (evEl) {
      const occ = this.events.find((x) => x.id === Number(evEl.dataset.ev) && x.date === evEl.dataset.date);
      return openEventEditor(Number(evEl.dataset.ev), {}, occ);
    }

    const head = t.closest("[data-goto]");
    if (head) { this.anchor = parseISO(head.dataset.goto); this.view = "day"; return this.refresh(); }

    const col = t.closest(".tg-col");
    if (col) {
      const r = col.getBoundingClientRect();
      const mins = Math.min(this.startHour * 60 + Math.floor(((e.clientY - r.top) / this.hourPx) * 2) * 30, 22 * 60 + 30);
      return openEventEditor(null, { start_date: col.dataset.date, start_time: hhmm(mins), end_time: hhmm(Math.min(mins + 60, 23 * 60 + 59)) });
    }

    const cell = t.closest(".mc");
    if (cell) { this.anchor = parseISO(cell.dataset.date); this.view = "day"; this.refresh(); }
  }
}

/* ================================================================ pages */
/** A round check button for an event occurrence (used in lists). */
const eventCheck = (ev) => `<button type="button" class="up-check" data-evdone data-ev="${ev.id}" data-date="${ev.date}"
  aria-pressed="${ev.done}" aria-label="${ev.done ? "Mark not done" : "Mark done"}: ${esc(ev.title)}">${icon("tick")}</button>`;

/** Shared click handling for lists of events with check buttons. */
function bindEventList(el, getEvents) {
  el.addEventListener("click", (e) => {
    const done = e.target.closest("[data-evdone]");
    if (done) return toggleEventDone(Number(done.dataset.ev), done.dataset.date);
    const b = e.target.closest("[data-ev]");
    if (!b) return;
    const occ = getEvents().find((x) => x.id === Number(b.dataset.ev) && x.date === b.dataset.date);
    openEventEditor(Number(b.dataset.ev), {}, occ);
  });
}

async function initHome() {
  const cal = new CalendarView($("#home-cal"), { compact: true, startHour: 7, endHour: 21 });
  const chips = $("#task-chips"), list = $("#task-list"), upcoming = $("#upcoming");
  const row = $("#member-row"), panel = $("#member-panel");
  let tasks = [], upcomingEvents = [], todayEvents = [], filter = "all", openMember = null;
  const ctl = Prefs.get("home-tasks", { show: "all", sort: "time" });
  bindTaskList(list);
  bindTaskList(panel);

  /* --- Today's Tasks card */
  const drawTasks = () => {
    taskChips(chips, tasks, filter);
    const shown = applyControls(applyTaskFilter(tasks, filter), ctl);
    list.innerHTML = shown.length ? shown.map(taskRow).join("") : `<li class="empty">${emptyTasksMsg(ctl)}</li>`;
  };
  taskControls($("#task-controls"), ctl, "home-tasks", drawTasks);
  chips.addEventListener("click", (e) => {
    const c = e.target.closest("[data-f]");
    if (c) { filter = c.dataset.f; drawTasks(); }
  });
  $("#add-task").onclick = () => openTaskEditor(null, { due_date: iso(new Date()), member_id: filter === "all" ? null : Number(filter) });

  /* --- Member cards that drop down into a panel */
  const drawMembers = (sum) => {
    row.innerHTML = sum.members.map(({ member: m, tasks_total: tt, tasks_done: td, events, events_done: ed, balance: bal, streak: stk }) => {
      const open = openMember === m.id;
      return `
      <button type="button" class="member-card c-${m.color} ${open ? "open" : ""}" data-member="${m.id}" aria-expanded="${open}" aria-controls="member-panel">
        ${avatar(m, "lg")}
        <span class="mc-info">
          <span class="mc-name">${esc(m.name)} <span class="mc-stars" title="${bal} stars in the jar${stk ? `, ${stk}-day streak` : ""}">⭐ ${bal}${stk >= 2 ? ` <span class="flame">🔥${stk}</span>` : ""}</span>${icon("chevron-down", "chev")}</span>
          <span class="mc-meta">${icon("check")} ${td}/${tt} task${tt === 1 ? "" : "s"} done</span>
          <span class="mc-meta">${icon("calendar")} ${ed}/${events} event${events === 1 ? "" : "s"} done</span>
          <span class="bar"><i style="width:${tt ? Math.round((td / tt) * 100) : 0}%"></i></span>
        </span>
      </button>`;
    }).join("") || `<p class="muted">No family members yet — <a href="/family">add someone</a>.</p>`;
  };

  const drawPanel = () => {
    const m = State.byId[openMember];
    if (!m) { panel.hidden = true; panel.innerHTML = ""; return; }
    const mt = applyControls(tasks.filter((t) => t.member_id === m.id), { show: "all", sort: "time" });
    const me = todayEvents.filter((e) => e.member_id === m.id || e.member_id == null);
    const td = mt.filter((t) => t.done).length, ed = me.filter((e) => e.done).length;
    panel.className = `member-panel card c-${m.color}`;
    panel.hidden = false;
    panel.innerHTML = `
      <div class="mp-head">
        ${avatar(m, "")}<h3>${esc(m.name)}'s day</h3><span class="mp-date">${fmtDay(iso(new Date()))}</span>
        <span class="spacer"></span>
        <a class="btn ghost sm" href="/calendar?member=${m.id}">${icon("calendar")} Calendar</a>
        <button type="button" class="icon-btn" data-close-panel aria-label="Close ${esc(m.name)}'s day">${icon("x")}</button>
      </div>
      <div class="mp-cols">
        <section>
          <h4>${icon("check")} Tasks <small>${td}/${mt.length} done</small></h4>
          <ul class="task-list mp-tasks">${mt.length ? mt.map(taskRow).join("") : `<li class="empty">No tasks today.</li>`}</ul>
          <button type="button" class="btn soft sm" data-add-for="${m.id}">${icon("plus")} Task for ${esc(m.name)}</button>
        </section>
        <section>
          <h4>${icon("calendar")} Events <small>${ed}/${me.length} done</small></h4>
          <ul class="mp-events">${me.length ? me.map((ev) => `
            <li class="c-${colorOf(ev.member_id)} ${ev.done ? "done" : ""}">
              ${eventCheck(ev)}
              <span class="mp-time">${ev.start_time ? fmtTime(ev.start_time) : "All day"}</span>
              <button type="button" class="up-title" data-ev="${ev.id}" data-date="${ev.date}">${esc(ev.title)}</button>
              ${ev.member_id == null ? `<span class="pill">Family</span>` : ""}
            </li>`).join("") : `<li class="empty">No events today.</li>`}</ul>
        </section>
      </div>`;
  };

  row.addEventListener("click", (e) => {
    const card = e.target.closest("[data-member]");
    if (!card) return;
    const id = Number(card.dataset.member);
    openMember = openMember === id ? null : id;
    $$("[data-member]", row).forEach((c) => {
      const on = Number(c.dataset.member) === openMember;
      c.classList.toggle("open", on);
      c.setAttribute("aria-expanded", on);
    });
    drawPanel();
    if (openMember) panel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  });
  panel.addEventListener("click", (e) => {
    if (e.target.closest("[data-close-panel]")) {
      openMember = null;
      $$("[data-member]", row).forEach((c) => { c.classList.remove("open"); c.setAttribute("aria-expanded", false); });
      return drawPanel();
    }
    const add = e.target.closest("[data-add-for]");
    if (add) return openTaskEditor(null, { due_date: iso(new Date()), member_id: Number(add.dataset.addFor) });
  });
  bindEventList(upcoming, () => upcomingEvents);                  // upcoming list
  panel.addEventListener("click", (e) => {                         // panel event list
    if (!e.target.closest(".mp-events")) return;
    const done = e.target.closest("[data-evdone]");
    if (done) return toggleEventDone(Number(done.dataset.ev), done.dataset.date);
    const b = e.target.closest("[data-ev]");
    if (b) openEventEditor(Number(b.dataset.ev), {}, todayEvents.find((x) => x.id === Number(b.dataset.ev)));
  });

  /* --- Upcoming events */
  const drawUpcoming = () => {
    const now = new Date(), nowKey = iso(now), nowMin = now.getHours() * 60 + now.getMinutes();
    const items = upcomingEvents
      .filter((ev) => !["daily", "weekdays"].includes(ev.recurrence)) // skip everyday routines
      .filter((ev) => ev.date > nowKey || (ev.date === nowKey && (ev.done || !ev.start_time || toMin(ev.end_time || ev.start_time) >= nowMin)))
      .slice(0, 7);
    upcoming.innerHTML = items.length ? items.map((ev) => `
      <li class="c-${colorOf(ev.member_id)} ${ev.done ? "done" : ""}">
        <span class="up-date">${fmtDay(ev.date)}</span>
        ${eventCheck(ev)}
        <button type="button" class="up-title" data-ev="${ev.id}" data-date="${ev.date}">${esc(ev.title)}</button>
        <span class="up-time">${ev.start_time ? fmtTime(ev.start_time) : "All day"}</span>
      </li>`).join("") : `<li class="empty">Nothing coming up in the next two weeks.</li>`;
  };

  async function refresh() {
    const today = new Date();
    try {
      const [sum, t, up, ov] = await Promise.all([
        api(`/api/summary?date=${iso(today)}`),
        api(`/api/tasks?date=${iso(today)}`),
        api(`/api/events?start=${iso(today)}&end=${iso(addDays(today, 13))}`),
        api("/api/rewards"),
      ]);
      $("#leaderboard").innerHTML = leaderboardHtml(ov);
      tasks = t;
      upcomingEvents = up;
      todayEvents = up.filter((e) => e.date === iso(today));
      drawMembers(sum);
      drawPanel();
      drawTasks();
      drawUpcoming();
    } catch (err) { toast(err.message, true); }
    cal.refresh();
  }
  document.addEventListener("fam:changed", refresh);
  refresh();
}

function initCalendar() {
  const p = new URLSearchParams(location.search);
  const filter = new Set(p.get("member") ? [p.get("member")] : []);
  const view = ["day", "week", "month"].includes(p.get("view")) ? p.get("view") : "week";
  const anchor = /^\d{4}-\d{2}-\d{2}$/.test(p.get("date") || "") ? parseISO(p.get("date")) : new Date();
  const prefs = Prefs.get("calendar", { status: "all" });
  const cal = new CalendarView($("#cal"), { view, anchor, filter, status: prefs.status, title: "Family Calendar" });
  const chips = $("#cal-filters");

  const statusEl = $("#cal-status");
  statusEl.innerHTML = dropdown("status", "Status", EVENT_SHOW_OPTS, prefs.status);
  statusEl.onchange = (e) => {
    cal.status = e.target.value;
    Prefs.set("calendar", { status: cal.status });
    cal.draw();
  };

  const drawChips = () => {
    chips.innerHTML =
      `<button type="button" class="fchip c-all ${filter.size ? "" : "on"}" data-k="">Everyone</button>` +
      State.members.map((m) => `<button type="button" class="fchip c-${m.color} ${filter.has(String(m.id)) ? "on" : ""}" data-k="${m.id}" aria-pressed="${filter.has(String(m.id))}">${avatar(m, "xs")} ${esc(m.name)}</button>`).join("") +
      `<button type="button" class="fchip c-family ${filter.has("family") ? "on" : ""}" data-k="family" aria-pressed="${filter.has("family")}">Whole family</button>`;
  };
  chips.addEventListener("click", (e) => {
    const c = e.target.closest("[data-k]");
    if (!c) return;
    const k = c.dataset.k;
    if (!k) filter.clear();
    else if (filter.has(k)) filter.delete(k);
    else filter.add(k);
    drawChips();
    cal.draw();
  });
  document.addEventListener("fam:changed", () => { drawChips(); cal.refresh(); });
  drawChips();
  cal.refresh();
}

function initTasks() {
  const p = new URLSearchParams(location.search);
  let day = /^\d{4}-\d{2}-\d{2}$/.test(p.get("date") || "") ? parseISO(p.get("date")) : new Date();
  let tasks = [], filter = "all";
  const ctl = Prefs.get("tasks-page", { show: "all", sort: "person" });
  const list = $("#task-list"), chips = $("#task-chips");
  bindTaskList(list);

  const draw = () => {
    const isToday = iso(day) === iso(new Date());
    $("#tasks-date").textContent = `${isToday ? "Today · " : ""}${DOW_LONG[day.getDay()]}, ${MON[day.getMonth()]} ${day.getDate()}`;
    taskChips(chips, tasks, filter);

    const shown = applyControls(applyTaskFilter(tasks, filter), ctl);
    const grouped = ctl.sort === "person";
    list.classList.toggle("grouped", grouped);
    if (!shown.length) {
      list.innerHTML = `<li class="empty">${tasks.length ? emptyTasksMsg(ctl) : "No tasks for this day. Add one with the + Task button."}</li>`;
    } else if (grouped) {
      const groups = [...State.members.map((m) => ({ m, items: shown.filter((t) => t.member_id === m.id) })),
        { m: null, items: shown.filter((t) => t.member_id == null) }].filter((g) => g.items.length);
      list.innerHTML = groups.map(({ m, items }) => {
        const all = tasks.filter((t) => t.member_id === (m ? m.id : null));
        return `
        <li class="group-head c-${m ? m.color : "family"}">${m ? avatar(m, "") : ""}${m ? esc(m.name) : "Everyone"}
          <small>${all.filter((t) => t.done).length}/${all.length} done</small></li>
        ${items.map(taskRow).join("")}`;
      }).join("");
    } else {
      list.innerHTML = shown.map(taskRow).join("");
    }

    // progress panel — counts tasks, plus checklist items for a finer-grained picture
    const done = tasks.filter((t) => t.done).length, total = tasks.length;
    const itemsTotal = tasks.reduce((n, t) => n + t.items_total, 0);
    const itemsDone = tasks.reduce((n, t) => n + t.items_done, 0);
    const pct = total ? Math.round((done / total) * 100) : 0;
    const C = 2 * Math.PI * 62;
    $("#ring").innerHTML = `<div class="ring"><svg viewBox="0 0 150 150">
        <circle cx="75" cy="75" r="62" fill="none" stroke="#F0EAFF" stroke-width="14"/>
        <circle cx="75" cy="75" r="62" fill="none" stroke="url(#rg)" stroke-width="14" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - pct / 100)}" style="transition:stroke-dashoffset .5s"/>
        <defs><linearGradient id="rg" x1="0" x2="1"><stop offset="0" stop-color="#9B7BFF"/><stop offset="1" stop-color="#F07AB0"/></linearGradient></defs></svg>
        <div class="ring-label"><b>${pct}%</b><small>${done} of ${total} tasks</small></div></div>
        ${itemsTotal ? `<p class="ring-sub">${icon("list")} ${itemsDone} of ${itemsTotal} checklist items</p>` : ""}`;
    $("#progress-list").innerHTML = State.members.map((m) => {
      const mine = tasks.filter((t) => t.member_id === m.id), d = mine.filter((t) => t.done).length;
      return `<li class="c-${m.color}">${avatar(m, "xs")}<span>${esc(m.name)}</span><small>${d}/${mine.length}</small>
        <div class="bar"><i style="width:${mine.length ? (d / mine.length) * 100 : 0}%"></i></div></li>`;
    }).join("");
  };

  async function refresh() {
    try { tasks = await api(`/api/tasks?date=${iso(day)}`); } catch (err) { toast(err.message, true); }
    draw();
  }
  taskControls($("#task-controls"), ctl, "tasks-page", draw);
  chips.addEventListener("click", (e) => {
    const c = e.target.closest("[data-f]");
    if (c) { filter = c.dataset.f; draw(); }
  });
  $$("[data-day]").forEach((b) => (b.onclick = () => {
    day = b.dataset.day === "today" ? new Date() : addDays(day, Number(b.dataset.day));
    history.replaceState(null, "", `/tasks?date=${iso(day)}`);
    refresh();
  }));
  $("#add-task").onclick = () => openTaskEditor(null, { due_date: iso(day), member_id: filter === "all" ? null : Number(filter) });
  document.addEventListener("fam:changed", refresh);
  refresh();
}

function initFamily() {
  const grid = $("#family-grid");
  async function refresh() {
    const today = new Date(), wk = startOfWeek(today);
    let events = [], tasks = [];
    try {
      [events, tasks] = await Promise.all([
        api(`/api/events?start=${iso(wk)}&end=${iso(addDays(wk, 6))}`),
        api(`/api/tasks?date=${iso(today)}`),
      ]);
    } catch (err) { toast(err.message, true); }
    grid.innerHTML = State.members.map((m) => {
      const ev = events.filter((e) => e.member_id === m.id).length;
      const tk = tasks.filter((t) => t.member_id === m.id);
      return `<article class="fam-card c-${m.color}">
        <div class="fam-band"></div>
        <button type="button" class="fam-photo" data-photo="${m.id}" aria-label="Change ${esc(m.name)}'s picture" title="Change picture">
          ${avatar(m, "xl")}<span class="cam">📷</span></button>
        <h3>${esc(m.name)}</h3>
        <span class="fam-role">${esc(m.role)}</span>
        <div class="fam-stats">
          <span class="pill">${plural(ev, "event")} this week</span>
          <span class="pill">${tk.filter((t) => t.done).length}/${tk.length} tasks today</span>
        </div>
        <div class="fam-actions">
          <a class="btn ghost sm" href="/calendar?member=${m.id}">${icon("calendar")} Calendar</a>
          <button type="button" class="btn soft sm" data-edit="${m.id}">${icon("edit")} Edit</button>
        </div>
      </article>`;
    }).join("") + `<button type="button" class="fam-add" data-add>${icon("plus")} Add family member</button>`;
  }
  grid.addEventListener("click", (e) => {
    const ph = e.target.closest("[data-photo]");
    if (ph) return openPhotoEditor(State.byId[ph.dataset.photo]);
    const ed = e.target.closest("[data-edit]");
    if (ed) return openMemberEditor(State.byId[ed.dataset.edit]);
    if (e.target.closest("[data-add]")) openMemberEditor();
  });
  $("#add-member").onclick = () => openMemberEditor();
  document.addEventListener("fam:changed", refresh);
  refresh();
}

/* ============================================================ rewards UI */
function leaderboardHtml(ov, big = false) {
  const rows = [...ov.members].sort((a, b) => b.week_stars - a.week_stars);
  if (!rows.some((r) => r.week_stars > 0)) {
    return `<li class="lb-empty">No stars yet this week — check off a task to get on the board! ⭐</li>`;
  }
  const max = Math.max(1, ...rows.map((r) => r.week_stars));
  return rows.map((r, i) => `
    <li class="c-${r.member.color} ${r.star_of_week ? "top" : ""}">
      <span class="lb-rank">${r.star_of_week ? "👑" : i + 1}</span>
      ${avatar(r.member, big ? "" : "xs")}
      <span class="lb-name">${esc(r.member.name)}</span>
      <span class="lb-bar"><i style="width:${(r.week_stars / max) * 100}%"></i></span>
      <span class="lb-num">${r.week_stars} ⭐</span>
    </li>`).join("");
}

const PRIZE_EMOJIS = ["🎁", "🍦", "🍕", "🍩", "🎬", "📺", "🎮", "🛝", "🧸", "🌙", "🎨", "📚", "🏊", "🎳", "🛍️", "💵"];

function openPrizeEditor(p = null) {
  const cur = p || { title: "", emoji: "🎁", cost: 10 };
  const body = `
    <label class="field"><span>Prize</span><input name="title" required maxlength="80" value="${esc(cur.title)}" placeholder="e.g. Trip to the zoo"></label>
    <div class="field"><span>Picture</span><div class="emoji-pick">${[...new Set([cur.emoji, ...PRIZE_EMOJIS])].map((e) => `
      <label><input type="radio" name="emoji" value="${e}" ${e === cur.emoji ? "checked" : ""}><span>${e}</span></label>`).join("")}</div></div>
    <label class="field"><span>Costs how many stars?</span><input type="number" name="cost" min="1" max="1000" required value="${cur.cost}"></label>`;
  openModal(p ? "Edit prize" : "New prize", body, {
    submitLabel: p ? "Save" : "Add prize",
    async onSubmit(fd) {
      const payload = { title: fd.get("title").trim(), emoji: fd.get("emoji") || "🎁", cost: Number(fd.get("cost")) };
      await api(p ? `/api/prizes/${p.id}` : "/api/prizes", { method: p ? "PUT" : "POST", body: payload });
      toast(p ? "Prize saved" : "Prize added 🎁");
      changed();
    },
    onDelete: p ? async () => { await api(`/api/prizes/${p.id}`, { method: "DELETE" }); toast("Prize removed"); changed(); } : null,
  });
}

function openBonus(memberId = null) {
  const body = `
    <label class="field"><span>Who gets them?</span><select name="member_id" required>${State.members.map((m) => `<option value="${m.id}" ${m.id === memberId ? "selected" : ""}>${esc(m.name)}</option>`).join("")}</select></label>
    <div class="field"><span>Sticker</span><div class="sticker-pick">${Object.entries(STICKERS).map(([k, st], i) => `
      <label class="stk-opt" title="${st.label}"><input type="radio" name="sticker" value="${k}" data-pts="${st.points}" ${i === 0 ? "checked" : ""}><span>${st.emoji}</span></label>`).join("")}
      <label class="pts-field">worth <input type="number" name="points" min="1" max="50" value="1"> ⭐</label></div></div>
    <label class="field"><span>What for? (optional)</span><input name="note" maxlength="120" placeholder="e.g. Helped a sibling without being asked"></label>`;
  openModal("Give bonus stars ⭐", body, {
    submitLabel: "Give stars",
    onOpen(form) { form.addEventListener("change", (e) => { if (e.target.name === "sticker") form.elements.points.value = e.target.dataset.pts; }); },
    async onSubmit(fd) {
      const r = await api("/api/rewards/bonus", { method: "POST", body: {
        member_id: Number(fd.get("member_id")), sticker: fd.get("sticker"), points: Number(fd.get("points")), note: fd.get("note") || "" } });
      celebrate(r);
      changed();
    },
  });
}

async function openRedeem(prize, onlyMember = null) {
  const ov = await api("/api/rewards");
  const people = ov.members.filter((x) => !onlyMember || x.member.id === onlyMember);
  const body = `
    <div class="redeem-head"><span class="redeem-emoji">${prize.emoji}</span><div><b>${esc(prize.title)}</b><small>${prize.cost} ⭐</small></div></div>
    <div class="field"><span>Who is cashing in stars?</span>
      <div class="redeem-people">${people.map((x) => {
        const short = prize.cost - x.balance;
        return `<label class="redeem-person c-${x.member.color} ${short > 0 ? "short" : ""}">
          <input type="radio" name="member_id" value="${x.member.id}" ${short > 0 ? "disabled" : ""}>
          ${avatar(x.member, "")}<b>${esc(x.member.name)}</b>
          <small>${short > 0 ? `needs ${short} more ⭐` : `has ${x.balance} ⭐`}</small></label>`;
      }).join("")}</div></div>
    <p class="hint">${icon("gift")} A grown-up will approve it. The stars are saved for this prize until then.</p>`;
  openModal("Get a prize", body, {
    submitLabel: "Ask for it!",
    async onSubmit(fd) {
      const mid = fd.get("member_id");
      if (!mid) throw new Error("Pick who's getting it (they need enough stars).");
      await api("/api/redemptions", { method: "POST", body: { member_id: Number(mid), prize_id: prize.id } });
      playSound("ding");
      popup(`<div class="cel-emoji">${prize.emoji}</div><b>Asked a grown-up!</b><small>${esc(prize.title)} is waiting for a yes 🤞</small>`, 2400);
      changed();
    },
  });
}

async function decideRedemption(id, approve) {
  try {
    const r = await api(`/api/redemptions/${id}/${approve ? "approve" : "decline"}`, { method: "POST" });
    if (approve) {
      confetti(180, [r.prize_emoji, "🎉"]); playSound("fanfare");
      popup(`<div class="cel-emoji">${r.prize_emoji}</div><b>Enjoy!</b><small>${esc(nameOf(r.member_id))} got ${esc(r.prize_title)}</small>`, 2600);
      if (r.new_badges?.length) setTimeout(() => showBadges(r.new_badges, State.byId[r.member_id]), 2700);
    } else toast("Declined — the stars went back in the jar");
    changed();
  } catch (err) { if (!/PIN/.test(err.message)) toast(err.message, true); }
}

async function initRewards() {
  let badgeFor = null;
  const el = { lb: $("#leaderboard"), jars: $("#jars"), prizes: $("#prizes"), pending: $("#pending"),
    pendingCard: $("#pending-card"), chips: $("#badge-chips"), badges: $("#badges"), recent: $("#recent") };
  let ov, prizes, pending, recent;

  const drawBadges = () => {
    const kid = State.members.find((m) => m.role === "kid");
    badgeFor ??= (kid || State.members[0])?.id;
    el.chips.innerHTML = State.members.map((m) => `<button type="button" class="fchip c-${m.color} ${m.id === badgeFor ? "on" : ""}" data-bf="${m.id}">${esc(m.name)}</button>`).join("");
    const me = ov.members.find((x) => x.member.id === badgeFor);
    el.badges.innerHTML = me ? me.badges.map((b) => `
      <div class="badge ${b.earned ? "on" : ""}" title="${esc(b.how)}">
        <span class="badge-emoji">${b.emoji}</span><b>${esc(b.name)}</b>
        <small>${b.earned ? `Earned ${fmtDay(b.earned_at.slice(0, 10))}` : esc(b.how)}</small>
      </div>`).join("") : "";
  };

  const draw = () => {
    const ws = parseISO(ov.week_start), we = parseISO(ov.week_end);
    $("#week-range").textContent = `${MON[ws.getMonth()]} ${ws.getDate()} – ${MON[we.getMonth()]} ${we.getDate()}`;
    el.lb.innerHTML = leaderboardHtml(ov, true);
    el.jars.innerHTML = ov.members.map((x) => `
      <div class="jar c-${x.member.color}">
        ${avatar(x.member, "lg")}
        <b class="jar-name">${esc(x.member.name)}</b>
        <span class="jar-stars">⭐ ${x.balance}</span>
        <small>${x.streak >= 1 ? `🔥 ${x.streak}-day streak` : "Start a streak today!"}</small>
        <small>${x.badges.filter((b) => b.earned).length} of ${x.badges.length} badges</small>
      </div>`).join("");
    el.pendingCard.hidden = !pending.length;
    el.pending.innerHTML = pending.map((r) => `
      <li class="c-${colorOf(r.member_id)}">
        <span class="pend-emoji">${r.prize_emoji}</span>
        <span><b>${esc(nameOf(r.member_id))}</b> wants <b>${esc(r.prize_title)}</b><small>${r.cost} ⭐</small></span>
        <button type="button" class="btn primary sm" data-approve="${r.id}">Yes! 🎉</button>
        <button type="button" class="btn ghost sm" data-decline="${r.id}">Not now</button>
      </li>`).join("");
    el.prizes.innerHTML = prizes.map((p) => `
      <div class="prize">
        <button type="button" class="prize-edit icon-btn sm" data-edit-prize="${p.id}" aria-label="Edit ${esc(p.title)}">${icon("edit")}</button>
        <span class="prize-emoji">${p.emoji}</span>
        <b>${esc(p.title)}</b>
        <span class="prize-cost">${p.cost} ⭐</span>
        <button type="button" class="btn soft sm" data-get="${p.id}">Get it</button>
      </div>`).join("") || `<div class="empty-state">🎁<b>No prizes yet</b><span>Add a few treats the kids can save up for.</span></div>`;
    el.recent.innerHTML = recent.length ? recent.map((r) => `
      <li class="c-${colorOf(r.member_id)}"><span class="rec-emoji">${r.kind === "bonus" ? "🎁" : r.emoji}</span>
        <span><b>${esc(nameOf(r.member_id))}</b> +${r.points} ⭐ <small>${esc(r.note)}</small></span>
        <span class="rec-day">${fmtDay(r.on_date)}</span></li>`).join("") : `<li class="empty">Stars will show up here as tasks get done.</li>`;
    drawBadges();
  };

  async function refresh() {
    try {
      [ov, prizes, pending, recent] = await Promise.all([
        api("/api/rewards"), api("/api/prizes"), api("/api/redemptions?status=pending"), api("/api/rewards/recent"),
      ]);
      draw();
    } catch (err) { toast(err.message, true); }
  }
  el.chips.addEventListener("click", (e) => { const b = e.target.closest("[data-bf]"); if (b) { badgeFor = Number(b.dataset.bf); drawBadges(); } });
  el.prizes.addEventListener("click", (e) => {
    const g = e.target.closest("[data-get]"), ed = e.target.closest("[data-edit-prize]");
    if (g) openRedeem(prizes.find((p) => p.id === Number(g.dataset.get)));
    if (ed) openPrizeEditor(prizes.find((p) => p.id === Number(ed.dataset.editPrize)));
  });
  el.pending.addEventListener("click", (e) => {
    const a = e.target.closest("[data-approve]"), d = e.target.closest("[data-decline]");
    if (a) decideRedemption(Number(a.dataset.approve), true);
    if (d) decideRedemption(Number(d.dataset.decline), false);
  });
  $("#add-prize").onclick = () => openPrizeEditor();
  $("#bonus-btn").onclick = () => openBonus();
  document.addEventListener("fam:changed", refresh);
  refresh();
}

/* ============================================================== chores */
const CHORE_IDEAS = [
  ["🛏️", "Make bed", "daily"], ["🐶", "Feed the pet", "daily"], ["🍽️", "Set the table", "daily"],
  ["🧽", "Clear the table", "daily"], ["🧸", "Put toys away", "daily"], ["🧺", "Clothes in the hamper", "daily"],
  ["🪥", "Brush teeth", "daily"], ["🗑️", "Take out the trash", "weekly"], ["🪴", "Water the plants", "weekly"],
  ["🧹", "Sweep the kitchen", "weekly"], ["🧦", "Fold & put away laundry", "weekly"], ["🚗", "Help wash the car", "biweekly"],
];

function assigneeFor(t, day) {
  const ids = t.rotation || [];
  if (ids.length < 2) return t.member_id;
  const start = parseISO(t.due_date);
  const idx = t.rotate_every === "day"
    ? Math.round((day - start) / 864e5)
    : Math.round((startOfWeek(day) - startOfWeek(start)) / (7 * 864e5));
  return ids[((idx % ids.length) + ids.length) % ids.length];
}

async function initChores() {
  const grid = $("#chore-grid"), ideas = $("#chore-ideas");
  ideas.innerHTML = `<span class="idea-label">Quick add:</span>` +
    CHORE_IDEAS.map(([e, t], i) => `<button type="button" class="idea" data-idea="${i}">${e} ${t}</button>`).join("");
  ideas.onclick = (e) => {
    const b = e.target.closest("[data-idea]");
    if (!b) return;
    const [em, title, rec] = CHORE_IDEAS[b.dataset.idea];
    const kids = State.members.filter((m) => m.role === "kid").map((m) => m.id);
    openTaskEditor(null, { category: "chore", title: `${em} ${title}`, recurrence: rec, rotation: kids.length > 1 ? kids : [], member_id: kids[0] ?? null });
  };
  $("#add-chore").onclick = () => openTaskEditor(null, { category: "chore" });

  const card = (c, occ) => {
    const today = new Date();
    const nowId = occ ? occ.member_id : assigneeFor(c, today);
    const nextId = c.rotation.length > 1 ? assigneeFor(c, addDays(today, c.rotate_every === "day" ? 1 : 7)) : null;
    const st = STICKERS[c.sticker] || STICKERS.star;
    return `
      <article class="chore-card c-${colorOf(nowId)} ${occ?.done ? "done" : ""}">
        <div class="chore-top">
          <h3>${esc(c.title)}</h3>
          <button type="button" class="icon-btn sm" data-edit-chore="${c.id}" aria-label="Edit ${esc(c.title)}">${icon("edit")}</button>
        </div>
        <div class="chore-meta"><span class="pill">${REC_LABEL[c.recurrence] || c.recurrence}</span><span class="stk-badge">${st.emoji}<b>${c.points}</b></span></div>
        ${c.rotation.length > 1 ? `
          <div class="rot-line">${c.rotation.map((id) => State.byId[id] ? `<span class="rot-av ${id === nowId ? "now" : ""}">${avatar(State.byId[id], "")}</span>` : "").join(`<span class="rot-arrow">→</span>`)}</div>
          <p class="chore-who">This ${c.rotate_every}: <b>${esc(nameOf(nowId))}</b> · Next: ${esc(nameOf(nextId))}</p>`
        : `<p class="chore-who">Done by <b>${esc(nameOf(nowId))}</b></p>`}
        ${occ ? `<button type="button" class="btn ${occ.done ? "soft" : "primary"} block chore-do" data-do="${c.id}" data-date="${occ.date}">
            ${occ.done ? "✓ Done today — nice!" : "Mark done today"}</button>`
        : `<p class="muted-sm">Not on today's list</p>`}
      </article>`;
  };

  async function refresh() {
    try {
      const [chores, todays] = await Promise.all([
        api("/api/tasks/all?category=chore"), api(`/api/tasks?date=${iso(new Date())}&category=chore`),
      ]);
      const byId = Object.fromEntries(todays.map((t) => [t.id, t]));
      grid.innerHTML = chores.length ? chores.map((c) => card(c, byId[c.id])).join("")
        : `<div class="empty-state">🧹<b>No chores yet</b><span>Tap a quick-add idea above, or “+ Chore”.</span></div>`;
    } catch (err) { toast(err.message, true); }
  }
  grid.addEventListener("click", async (e) => {
    const ed = e.target.closest("[data-edit-chore]");
    if (ed) return openTaskEditor(Number(ed.dataset.editChore));
    const d = e.target.closest("[data-do]");
    if (!d) return;
    try {
      const r = await api(`/api/tasks/${d.dataset.do}/toggle`, { method: "POST", body: { on_date: d.dataset.date } });
      if (r.done) celebrate(r.reward, { title: d.closest(".chore-card").querySelector("h3").textContent });
      changed();
    } catch (err) { toast(err.message, true); }
  });
  document.addEventListener("fam:changed", refresh);
  refresh();
}

/* ========================================================= maintenance */
async function openStarter() {
  let items;
  try { items = await api("/api/maintenance/starter"); } catch (err) { return toast(err.message, true); }
  const groups = {};
  items.forEach((it) => (groups[it.label] ||= []).push(it));
  const body = `
    <p class="muted" style="margin:0">Tick the jobs that fit your home. You can edit or delete any of them later.</p>
    ${Object.entries(groups).map(([label, list]) => `
      <div class="starter-group"><h4>${label}</h4>
        ${list.map((it) => `
          <label class="starter-item ${it.added ? "added" : ""}">
            <input type="checkbox" name="keys" value="${it.key}" ${it.added ? "checked disabled" : ""}>
            <span class="st-emoji">${it.emoji}</span>
            <span><b>${esc(it.title)}</b>${it.added ? `<small>Already added</small>` : it.tip ? `<small>${esc(it.tip)}</small>` : ""}</span>
          </label>`).join("")}
      </div>`).join("")}
    <div class="row2">
      <label class="field"><span>Who's in charge?</span><select name="member_id">${memberOptions(null, "Everyone")}</select></label>
      <label class="field"><span>Start on</span><input type="date" name="start_date" value="${iso(new Date())}"></label>
    </div>`;
  openModal("Home upkeep starter list", body, {
    submitLabel: "Add selected",
    async onSubmit(fd) {
      const keys = fd.getAll("keys");
      if (!keys.length) throw new Error("Tick at least one job to add.");
      const r = await api("/api/maintenance/starter", { method: "POST", body: {
        keys, member_id: numOrNull(fd.get("member_id")), start_date: fd.get("start_date") || null } });
      toast(`Added ${plural(r.added, "job")} 🛠️`);
      changed();
    },
  });
}

async function initMaintenance() {
  const list = $("#maint-list"), stats = $("#maint-stats");
  $("#add-maint").onclick = () => openTaskEditor(null, { category: "maintenance", recurrence: "monthly" });
  $("#starter-btn").onclick = openStarter;

  const status = (m) => {
    if (!m.due) return ["ok", "All done ✓"];
    if (m.overdue) return ["late", `Overdue since ${fmtDay(m.due)}`];
    if (m.days_until === 0) return ["today", "Due today"];
    if (m.days_until <= 7) return ["soon", `Due in ${plural(m.days_until, "day")}`];
    return ["later", `Next: ${fmtDay(m.due)}`];
  };

  async function refresh() {
    let items;
    try { items = await api("/api/maintenance"); } catch (err) { return toast(err.message, true); }
    const late = items.filter((m) => m.overdue).length;
    const soon = items.filter((m) => !m.overdue && m.due && m.days_until <= 7).length;
    stats.innerHTML = items.length ? `
      <div class="mstat c-coral"><b>${late}</b><span>Overdue</span></div>
      <div class="mstat c-yellow"><b>${soon}</b><span>Due this week</span></div>
      <div class="mstat c-teal"><b>${items.length}</b><span>Jobs tracked</span></div>` : "";
    if (!items.length) {
      list.innerHTML = `<div class="empty-state">🏡<b>Keep the house happy</b>
        <span>Track air filters, HVAC service, smoke alarms, gutters and more. Start with the ready-made list.</span>
        <button type="button" class="btn primary" data-starter>${icon("list")} Browse the starter list</button></div>`;
      return;
    }
    const groups = {};
    items.forEach((m) => (groups[m.label] ||= []).push(m));
    list.innerHTML = Object.entries(groups).map(([label, ms]) => `
      <section class="maint-group"><h3>${label}</h3><ul>
        ${ms.map((m) => {
          const [cls, text] = status(m);
          const who = State.byId[m.member_id];
          return `<li class="maint-row ${cls}">
            <button type="button" class="m-title" data-edit-m="${m.id}"><b>${esc(m.title)}</b>${m.notes ? `<small>${esc(m.notes)}</small>` : ""}</button>
            <span class="m-who">${who ? avatar(who, "xs") + esc(who.name) : "Everyone"}</span>
            <span class="m-last">${m.last_done ? `Last: ${fmtDay(m.last_done)}` : "Not done yet"}</span>
            <span class="m-status">${text}</span>
            ${m.due ? `<button type="button" class="btn ${m.overdue || m.days_until === 0 ? "primary" : "soft"} sm" data-mdone="${m.id}" data-date="${m.due}">${icon("tick")} Done</button>` : `<span></span>`}
          </li>`;
        }).join("")}
      </ul></section>`).join("");
  }
  list.addEventListener("click", async (e) => {
    if (e.target.closest("[data-starter]")) return openStarter();
    const ed = e.target.closest("[data-edit-m]");
    if (ed) return openTaskEditor(Number(ed.dataset.editM));
    const d = e.target.closest("[data-mdone]");
    if (!d) return;
    try {
      const r = await api(`/api/tasks/${d.dataset.mdone}/toggle`, { method: "POST", body: { on_date: d.dataset.date } });
      if (r.done) celebrate(r.reward, { title: d.closest("li").querySelector(".m-title b").textContent });
      changed();
    } catch (err) { toast(err.message, true); }
  });
  document.addEventListener("fam:changed", refresh);
  refresh();
}

/* ============================================================ settings */
async function initSettings() {
  const status = $("#pin-status"), actions = $("#pin-actions");
  async function drawPin() {
    const r = await api("/api/pin");
    Pin.isSet = r.set;
    updateLockButton();
    status.textContent = r.set
      ? "A PIN is set. Kids can check things off and ask for prizes. Adding, editing, deleting and approving prizes needs the PIN."
      : "No PIN yet, so anyone can add, edit or delete anything. Set one so only grown-ups can.";
    actions.innerHTML = r.set
      ? `<button type="button" class="btn primary" data-pin="change">Change PIN</button><button type="button" class="btn ghost" data-pin="remove">Remove PIN</button>`
      : `<button type="button" class="btn primary" data-pin="set">Set a parent PIN</button>`;
  }
  actions.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-pin]");
    if (!b) return;
    try {
      let current = null;
      if (Pin.isSet) current = await askPin({ sub: "Enter the current PIN" });
      if (b.dataset.pin === "remove") {
        await api("/api/pin/remove", { method: "POST", body: { pin: current } });
        Pin.forget(); toast("PIN removed");
      } else {
        const p1 = await askPin({ title: "New parent PIN", sub: "Choose 4 numbers", verify: false });
        const p2 = await askPin({ title: "One more time", sub: "Type the same 4 numbers again", verify: false });
        if (p1 !== p2) return toast("Those didn't match — try again", true);
        await api("/api/pin", { method: "POST", body: { pin: p1, current_pin: current } });
        Pin.remember(p1); toast("PIN saved 🔒");
      }
      drawPin();
    } catch (err) { if (!/PIN is needed/.test(err.message)) toast(err.message, true); }
  });

  api("/api/phone-link").then((r) => {
    const el = $("#phone-link");
    if (r.on_phone) {
      el.innerHTML = `<p class="phone-here">👍 You're already on another device. Follow the steps below to add this to your home screen.</p>`;
      return;
    }
    if (!r.url) {
      el.innerHTML = `<p class="muted">Couldn't find this computer on your home network. Make sure it's connected to Wi-Fi, then reopen this page.</p>`;
      return;
    }
    el.innerHTML = `
      <div class="qr"><img src="/api/phone-link/qr.svg" width="170" height="170" alt="QR code for ${r.url}"></div>
      <div class="phone-addr">
        <span class="muted-sm">Scan the code, or type this on your phone:</span>
        <b class="phone-url">${r.url}</b>
        <button type="button" class="btn soft sm" data-copy>Copy address</button>
      </div>`;
    $("[data-copy]", el).onclick = async () => {
      try { await navigator.clipboard.writeText(r.url); toast("Address copied"); } catch { toast(r.url); }
    };
  }).catch(() => {});

  const snd = $("#set-sound"), conf = $("#set-confetti");
  snd.checked = celebratePref("sound"); conf.checked = celebratePref("confetti");
  snd.onchange = () => { setCelebratePref("sound", snd.checked); initTopbar(); };
  conf.onchange = () => setCelebratePref("confetti", conf.checked);
  $("#test-celebrate").onclick = () => {
    const kid = State.members.find((m) => m.role === "kid") || State.members[0];
    celebrate({ member_id: kid?.id, points: 2, sticker: "rainbow", balance: 42, streak: 3, new_badges: [] });
  };

  $$("[data-clear]").forEach((b) => {
    let armed = false;
    const label = b.textContent;
    b.onclick = async () => {
      if (!armed) { armed = true; b.classList.add("armed"); b.textContent = "Tap again to confirm"; setTimeout(() => { armed = false; b.classList.remove("armed"); b.textContent = label; }, 4000); return; }
      try {
        await api("/api/admin/clear", { method: "POST", body: { what: b.dataset.clear } });
        toast(b.dataset.clear === "activities" ? "All activities cleared — fresh start!" : "Rewards reset");
        changed();
      } catch (err) { if (!/PIN is needed/.test(err.message)) toast(err.message, true); }
      armed = false; b.classList.remove("armed"); b.textContent = label;
    };
  });
  drawPin();
}

/* ============================================================ kid mode */
async function initKidsPicker() {
  const ov = await api("/api/rewards");
  const people = [...ov.members].sort((a, b) => (a.member.role === "kid" ? 0 : 1) - (b.member.role === "kid" ? 0 : 1));
  $("#kid-tiles").innerHTML = people.map((x) => `
    <a class="kid-tile c-${x.member.color}" href="/kids/${x.member.id}">
      ${avatar(x.member, "xl")}<b>${esc(x.member.name)}</b><span>⭐ ${x.balance}</span>
    </a>`).join("");
}

async function initKid(id) {
  const root = $("#kid-app");
  let tasks = [], prizes = [], mine = [];

  const kidCard = (t) => {
    const st = STICKERS[t.sticker] || STICKERS.star;
    return `
    <article class="kid-card c-${colorOf(t.member_id)} ${t.done ? "done" : ""}" data-id="${t.id}" data-date="${t.date}">
      <button type="button" class="kid-check" data-kdone aria-pressed="${t.done}" aria-label="${t.done ? "Undo" : "Done"}: ${esc(t.title)}">${t.done ? st.emoji : ""}</button>
      <div class="kid-body">
        <b>${esc(t.title)}</b>
        <small>${t.due_time ? fmtTime(t.due_time) : "Anytime today"}${t.member_id == null ? " · whole family" : ""}${t.overdue ? " · from before" : ""}</small>
        ${t.items_total ? `<div class="kid-items">${t.items.map((i) => `
          <button type="button" class="kid-item ${i.done ? "done" : ""}" data-kitem="${i.id}" aria-pressed="${i.done}">${i.done ? "✅" : "⬜"} ${esc(i.title)}</button>`).join("")}</div>` : ""}
      </div>
      ${t.member_id != null && t.points > 0 ? `<span class="kid-reward">${st.emoji}<b>+${t.points}</b></span>` : ""}
    </article>`;
  };

  async function refresh() {
    let ov, pend;
    try {
      [tasks, ov, prizes, pend] = await Promise.all([
        api(`/api/tasks?date=${iso(new Date())}`), api("/api/rewards"), api("/api/prizes"), api("/api/redemptions?status=pending"),
      ]);
    } catch (err) { return toast(err.message, true); }
    const me = ov.members.find((x) => x.member.id === id);
    if (!me) { root.innerHTML = `<div class="card empty-state">🤔<b>We couldn't find that person.</b><a class="btn primary" href="/kids">Pick again</a></div>`; return; }
    const m = me.member;
    mine = tasks.filter((t) => t.member_id === id || t.member_id == null);
    const left = mine.filter((t) => !t.done).length;
    const waiting = pend.filter((r) => r.member_id === id);
    root.innerHTML = `
      <header class="kid-head c-${m.color}">
        <button type="button" class="fam-photo kid-photo" data-kphoto aria-label="Change my picture" title="Change my picture">${avatar(m, "xl")}<span class="cam">📷</span></button>
        <div class="kid-hello"><h2>Hi ${esc(m.name)}! 👋</h2>
          <p>${left ? `${plural(left, "job")} left today` : mine.length ? "All done today — you rock! 🎉" : "No jobs today — play time! 🎈"}</p></div>
        <div class="kid-stats">
          <span class="kid-stat">⭐<b>${me.balance}</b><small>stars</small></span>
          <span class="kid-stat">🔥<b>${me.streak}</b><small>day streak</small></span>
          ${me.star_of_week ? `<span class="kid-stat crown">👑<b>Star</b><small>of the week</small></span>` : ""}
        </div>
        <button type="button" class="btn ghost kid-exit" data-exit>${icon("log-out")} Exit</button>
      </header>
      <section class="kid-jobs">${mine.length ? mine.map(kidCard).join("") : `<div class="card empty-state">🌈<b>Nothing to do today!</b></div>`}</section>
      <section class="card kid-shelf">
        <h3>🎁 Prizes</h3>
        ${waiting.length ? `<p class="kid-waiting">Waiting for a grown-up: ${waiting.map((w) => `${w.prize_emoji} ${esc(w.prize_title)}`).join(", ")}</p>` : ""}
        <div class="kid-prizes">${prizes.map((p) => {
          const short = p.cost - me.balance;
          return `<div class="kid-prize ${short > 0 ? "locked" : ""}">
            <span class="kp-emoji">${p.emoji}</span><b>${esc(p.title)}</b>
            ${short > 0 ? `<span class="kp-need">${short} more ⭐</span><span class="kp-bar"><i style="width:${Math.min(100, (me.balance / p.cost) * 100)}%"></i></span>`
              : `<button type="button" class="btn primary sm" data-kprize="${p.id}">Get it! (${p.cost} ⭐)</button>`}
          </div>`;
        }).join("")}</div>
      </section>
      <section class="card kid-shelf">
        <h3>🏅 My badges</h3>
        <div class="kid-badges">${me.badges.map((b) => `<span class="kb ${b.earned ? "on" : ""}" title="${esc(b.how)}">${b.emoji}<small>${esc(b.name)}</small></span>`).join("")}</div>
      </section>`;
  }

  root.addEventListener("click", async (e) => {
    if (e.target.closest("[data-exit]")) {
      if (Pin.isSet && !Pin.get()) { try { await askPin({ sub: "A grown-up can unlock to leave Kid Mode" }); } catch { return; } }
      location.href = "/";
      return;
    }
    if (e.target.closest("[data-kphoto]")) return openPhotoEditor(State.byId[id]);
    const pz = e.target.closest("[data-kprize]");
    if (pz) return openRedeem(prizes.find((p) => p.id === Number(pz.dataset.kprize)), id);
    const card = e.target.closest(".kid-card");
    if (!card) return;
    const t = mine.find((x) => x.id === Number(card.dataset.id) && x.date === card.dataset.date);
    try {
      const item = e.target.closest("[data-kitem]");
      if (item) {
        const r = await api(`/api/tasks/${t.id}/items/${item.dataset.kitem}/toggle`, { method: "POST", body: { on_date: t.date } });
        if (r.task_done && r.done) celebrate(r.reward, { title: t.title }); else if (r.done) playSound("tick");
      } else if (e.target.closest("[data-kdone]")) {
        const r = await api(`/api/tasks/${t.id}/toggle`, { method: "POST", body: { on_date: t.date } });
        if (r.done) celebrate(r.reward, { title: t.title });
      } else return;
      changed();
    } catch (err) { toast(err.message, true); }
  });
  document.addEventListener("fam:changed", refresh);
  refresh();
}

/* --------------------------------------------------------------- search */
function initSearch() {
  const input = $("#search-input"), box = $("#search-results");
  if (!input) return;
  let timer, seq = 0;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (!q) { box.classList.remove("open"); return; }
    timer = setTimeout(async () => {
      const mine = ++seq;
      let res = [];
      try { res = await api(`/api/search?q=${encodeURIComponent(q)}`); } catch { /* ignore */ }
      if (mine !== seq) return;
      box.innerHTML = res.length ? res.map((r) => `
        <a class="sr c-${colorOf(r.member_id)}" href="${r.type === "event" ? `/calendar?date=${r.date}&view=day` : `/tasks?date=${r.date}`}">
          <span class="dot"></span>
          <span><b>${esc(r.title)}</b><small>${r.type === "event" ? "Event" : "Task"} · ${esc(nameOf(r.member_id))} · ${fmtDay(r.date)}${r.time ? " · " + fmtTime(r.time) : ""}</small></span>
        </a>`).join("") : `<div class="sr-empty">No matches for “${esc(q)}”</div>`;
      box.classList.add("open");
    }, 180);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { input.value = ""; box.classList.remove("open"); }
  });
  document.addEventListener("click", (e) => { if (!e.target.closest(".search")) box.classList.remove("open"); });
}

/* ----------------------------------------------------------------- boot */
document.addEventListener("DOMContentLoaded", async () => {
  initSearch();
  initTopbar();
  try { await loadMembers(); } catch { toast("Couldn't load the family list", true); }
  const kid = Number(document.body.dataset.kid || 0);
  const pages = {
    home: initHome, calendar: initCalendar, tasks: initTasks, family: initFamily,
    chores: initChores, maintenance: initMaintenance, rewards: initRewards, settings: initSettings,
    kids: kid ? () => initKid(kid) : initKidsPicker,
  };
  pages[document.body.dataset.page]?.();
});
