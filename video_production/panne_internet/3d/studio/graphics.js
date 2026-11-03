// Couche graphique éditoriale (style de référence) : étiquettes, titres, panneaux, cartes, chiffres, graphiques.
// Tout est dessiné en 1920x1080 logiques, puis mis à l'échelle de la vidéo.
import { sstep, clamp, lerp, reseed, rnd } from "./core.js";

const hudEl = document.getElementById("hud");
const cv = document.getElementById("g2d"); cv.width = 1920; cv.height = 1080;
export const g2 = cv.getContext("2d");
const RED = "#ff5a5f", CYAN = "#5fd4dc", ORANGE = "#f5a524", GREY = "#9aa3a8", WHITE = "#f2f4f5", LIME = "#c6f36b";
export const COL = { RED, CYAN, ORANGE, GREY, WHITE, LIME };

export function el(html, cls = "", style = "") {
  const e = document.createElement("div"); e.className = "el " + cls; e.style.cssText = style; e.innerHTML = html; hudEl.appendChild(e); return e;
}
export function reveal(e, t, a, b = 1e9, fi = 0.45, fo = 0.35, dy = 18) {
  const v = sstep(a, a + fi, t) * (1 - sstep(b - fo, b, t));
  e.style.opacity = v.toFixed(3);
  e.style.transform = `translateY(${((1 - sstep(a, a + fi, t)) * dy).toFixed(1)}px)`;
  e.style.filter = v < 0.999 && v > 0.001 ? `blur(${((1 - v) * 5).toFixed(1)}px)` : "none";
  return v;
}
const caps = (s) => `<span class="caps">${s}</span>`;
export function fmtNum(v, dec = 0) {
  const s = v.toFixed(dec).split("."); s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, " "); return s.join(",");
}

// ---------- éléments communs à toutes les scènes ----------
export function commonHud(S) {
  const real = S.label.startsWith("HIST");
  const H = {};
  H.vig = el("", "", "left:0;top:0;width:1920px;height:1080px;background:radial-gradient(ellipse at 50% 46%,rgba(0,0,0,0) 55%,rgba(0,0,0,.55) 100%)");
  H.shade = el("", "", "left:0;top:0;width:1920px;height:1080px;background:linear-gradient(to top,rgba(0,0,0,.55) 0%,rgba(0,0,0,0) 36%),linear-gradient(to bottom,rgba(0,0,0,.35) 0%,rgba(0,0,0,0) 16%)");
  H.tag = el(`<i></i>${real ? "HISTOIRE RÉELLE" : "SIMULATION"}`, "tag " + (real ? "real" : "sim"));
  H.sect = el(`<b class="mono">0${S.beat}</b>——&nbsp;&nbsp;${S.beatName}`, "caps sect");
  if (S.p.hud) H.panel = el(S.p.hud.map(([k, v]) => `<div class="row"><span class="caps">${k}</span><b>${v}</b></div>`).join(""), "panel");
  if (S.p.coords) H.coords = el(S.p.coords, "mono coords");
  if (real && (S.kind === "device" || S.kind === "person")) H.recon = el("RECONSTITUTION", "caps recon");
  H.fade = el("", "", "left:0;top:0;width:1920px;height:1080px;background:#000");
  return H;
}
export function updateCommon(H, S, t) {
  const d = S.dur;
  H.vig.style.opacity = 1; H.shade.style.opacity = S.kind === "device" || S.kind === "person" || S.kind === "globe" || S.kind === "chrono" ? 1 : 0.4;
  reveal(H.tag, t, S.fadeIn ? 0.3 : -1, 1e9, 0.4);
  reveal(H.sect, t, S.fadeIn ? 0.5 : -1, S.fadeIn ? 4.5 : -0.5);
  if (H.panel) reveal(H.panel, t, (S.spans[0] || [0.5])[0] + 0.8, d + 1);
  if (H.coords) reveal(H.coords, t, 0.8, d + 1);
  if (H.recon) reveal(H.recon, t, 0.6, d + 1);
  let f = 0;
  if (S.fadeIn) f = 1 - sstep(0, 0.35, t);
  if (S.fadeOut) f = Math.max(f, sstep(d - 0.22, d, t));
  H.fade.style.opacity = f.toFixed(3);
}

// titre en bas à gauche : libellé de la scène et sous-titre
export function lowerTitle(S, big, sub, subCol = "o") {
  const e = el(`<div class="big">${big}</div>${sub ? `<div class="sub caps ${subCol}">${sub}</div>` : ""}`, "title");
  return (t, a = (S.spans[0] || [0.4])[0] + 0.25, b = S.dur + 1) => reveal(e, t, a, b);
}
// repère accroché à un point 3D projeté
export function pin3d(text, cls = "ok") {
  const e = el(`<i></i><span>${text}</span>`, "pin " + cls);
  return (t, a, b, sx, sy) => { const v = reveal(e, t, a, b, 0.4, 0.3, 0); e.style.left = (sx - 6) + "px"; e.style.top = (sy - 12) + "px"; return v; };
}

// ---------- fond graphique (cartes, chiffres, graphiques) ----------
export function clear2d() { g2.setTransform(1, 0, 0, 1, 0, 0); g2.clearRect(0, 0, 1920, 1080); }

// ---------- CHIFFRES ----------
export function numberKind(S) {
  const p = S.p, dec = p.decimals || 0, acc = p.accent;
  const big = el(`<div class="mono numv ${acc ? "acc" : ""}"></div><div class="caps unit">${p.unit}</div><div class="caps nsub">${p.sub || ""}</div>`, "number");
  const v = big.querySelector(".numv");
  const sp = S.spans, a0 = (sp[0] || [0.3])[0];
  // moment où le chiffre est prononcé : on vise la phrase qui le contient (heuristique simple : 2e phrase si elle existe)
  const k = S.n === 16 ? 1 : S.n === 53 ? 1 : S.n === 14 ? 1 : S.n === 6 ? 2 : 0;
  const tc = (sp[k] || sp[0] || [0.3])[0];
  return (t) => {
    reveal(big, t, Math.max(0.2, tc - 0.3), S.dur + 1);
    const u = sstep(tc - 0.2, tc + 1.6, t);
    let val = p.value * (S.n === 16 || S.n === 53 ? 1 : u);
    if (S.n === 53) {   // 78 minutes, puis 72 heures pour tout relancer
      const sw = (sp[3] || sp[sp.length - 1])[0];
      v.textContent = t < sw ? "78 MIN" : "72 H"; v.classList.toggle("acc2", t >= sw);
    } else if (S.n === 16) v.textContent = `${Math.round(lerp(0, 78, sstep(tc - 0.2, tc + 1.0, t)))} MIN`;
    else v.textContent = fmtNum(val, dec);
    clear2d();
    // illustrations : grilles d'icônes
    if (S.n === 14) iconGrid(t, tc + 1.2, 53, 11, "atm");
    if (S.n === 27 || S.n === 60) iconGrid(t, tc + 1.2, 100, 11, "phone");
    if (S.n === 16 || S.n === 53) ring(t, tc, S.n === 53 ? (sp[3] || sp[sp.length - 1])[0] : null);
  };
}
function iconGrid(t, a, n, nbad, kind) {
  const cols = kind === "atm" ? 9 : 20, sz = kind === "atm" ? 54 : 30, gap = kind === "atm" ? 22 : 14;
  const x0 = 1920 - 160 - cols * (sz + gap), y0 = 330;
  for (let i = 0; i < n; i++) {
    const x = x0 + (i % cols) * (sz + gap), y = y0 + Math.floor(i / cols) * (sz + gap) * (kind === "atm" ? 1.25 : 1.1);
    const on = sstep(a + i * 0.012, a + i * 0.012 + 0.25, t); if (on <= 0) continue;
    const bad = kind === "atm" ? i >= n - nbad : i < nbad;
    const fade = bad ? sstep(a + 1.3, a + 2.0, t) : 0;
    g2.globalAlpha = on * (1 - fade * 0.65);
    g2.strokeStyle = bad && fade > 0 ? RED : "rgba(220,230,235,.8)"; g2.lineWidth = 2.2;
    if (kind === "atm") { g2.strokeRect(x, y, sz, sz * 1.3); g2.strokeRect(x + 9, y + 9, sz - 18, sz * 0.45); g2.beginPath(); g2.moveTo(x + 14, y + sz); g2.lineTo(x + sz - 14, y + sz); g2.stroke(); }
    else { g2.beginPath(); g2.roundRect(x + sz * 0.22, y, sz * 0.56, sz, 5); g2.stroke(); }
    if (bad && fade > 0.5) { g2.strokeStyle = RED; g2.beginPath(); g2.moveTo(x - 3, y - 3); g2.lineTo(x + sz + 3, y + sz * (kind === "atm" ? 1.3 : 1) + 3); g2.stroke(); }
  }
  g2.globalAlpha = 1;
}
function ring(t, a, sw) {
  const cx = 1420, cy = 540, r = 230;
  g2.lineWidth = 10; g2.strokeStyle = "rgba(255,255,255,.08)"; g2.beginPath(); g2.arc(cx, cy, r, 0, Math.PI * 2); g2.stroke();
  const u = sstep(a, a + 1.2, t) * (78 / 1440);
  g2.strokeStyle = ORANGE; g2.lineCap = "round"; g2.beginPath(); g2.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + u * Math.PI * 2 * 6); g2.stroke();
  if (sw !== null) { const k = sstep(sw, sw + 2.2, t); g2.strokeStyle = RED; g2.beginPath(); g2.arc(cx, cy, r + 26, -Math.PI / 2, -Math.PI / 2 + k * Math.PI * 2); g2.stroke(); }
  for (let i = 0; i < 60; i++) { const an = i / 60 * Math.PI * 2; g2.strokeStyle = "rgba(255,255,255,.18)"; g2.lineWidth = i % 5 ? 1 : 2;
    g2.beginPath(); g2.moveTo(cx + Math.cos(an) * (r - 24), cy + Math.sin(an) * (r - 24)); g2.lineTo(cx + Math.cos(an) * (r - (i % 5 ? 32 : 40)), cy + Math.sin(an) * (r - (i % 5 ? 32 : 40))); g2.stroke(); }
  g2.lineCap = "butt";
}

// ---------- GRAPHIQUES EN BARRES ----------
export function barsKind(S) {
  const p = S.p;
  const head = el(`<div class="caps bsub">${S.label.startsWith("HIST") ? "Données réelles" : ""}</div><div class="btitle">${p.title}</div>`, "bars");
  const rows = p.items.map(([k, v, u], i) => el(`<div class="caps blab">${k}</div><div class="mono bval"></div>`, "brow", `left:150px;top:${430 + i * 190}px`));
  const sp = S.spans;
  return (t) => {
    reveal(head, t, 0.3, S.dur + 1);
    clear2d();
    p.items.forEach(([k, v, u], i) => {
      const a = (sp[Math.min(i + (sp.length > 2 ? 1 : 0), sp.length - 1)] || [0.5])[0] + 0.1 + i * 0.25;
      reveal(rows[i], t, a - 0.3, S.dur + 1, 0.4, 0.3, 0);
      const k2 = sstep(a, a + 1.4, t), val = v * k2;
      const lab = p.labels ? p.labels[i] : `${Math.round(val)}${u}`;
      rows[i].querySelector(".bval").textContent = p.labels ? (k2 > 0.95 ? lab : `${Math.round(val)}${u}`) : lab;
      const x = 150, y = 490 + i * 190, wmax = 1280, w = Math.max(6, wmax * (v / p.max) * k2);
      g2.globalAlpha = sstep(a - 0.3, a, t);
      g2.fillStyle = "rgba(255,255,255,.07)"; g2.fillRect(x, y, wmax, 46);
      g2.fillStyle = i === 0 ? CYAN : ORANGE; g2.fillRect(x, y, w, 46);
      g2.globalAlpha = 1;
    });
  };
}

// ---------- CERCLES ----------
export function circlesKind(S) {
  const cx = 1180, cy = 560, R = [110, 205, 300, 395];
  const names = ["CERCLE 1 · CHEZ VOUS", "CERCLE 2 · LA RUE", "CERCLE 3 · LES COMMERCES", "CERCLE 4 · MARC"];
  const head = el(`<div class="btitle">OÙ ÊTES-VOUS ?</div><div class="caps bsub r">Minute 10 · la gravité dépend de l'endroit</div>`, "bars");
  const labs = names.map((n, i) => el(n, "caps clab", `left:${cx + R[i] * 0.72 + 30}px;top:${cy - R[i] * 0.72 - 14}px`));
  return (t) => {
    reveal(head, t, 0.3, S.dur + 1); clear2d();
    const a0 = (S.spans[1] || S.spans[0])[0];
    R.forEach((r, i) => {
      const a = a0 + i * 0.35, k = sstep(a, a + 0.6, t); if (k <= 0) return;
      reveal(labs[i], t, a + 0.2, S.dur + 1, 0.4, 0.3, 0);
      g2.setLineDash([10, 9]); g2.lineWidth = 2; g2.strokeStyle = i === 3 ? RED : `rgba(95,212,220,${0.9 - i * 0.15})`;
      g2.beginPath(); g2.arc(cx, cy, r * (0.85 + 0.15 * k), 0, Math.PI * 2 * k); g2.stroke(); g2.setLineDash([]);
    });
    const pul = (t * 1.2) % 1;
    g2.fillStyle = RED; g2.beginPath(); g2.arc(cx, cy, 9, 0, Math.PI * 2); g2.fill();
    g2.strokeStyle = `rgba(255,90,95,${1 - pul})`; g2.lineWidth = 2; g2.beginPath(); g2.arc(cx, cy, 9 + pul * 40, 0, Math.PI * 2); g2.stroke();
  };
}

// ---------- CHOIX ----------
const ICON = {
  radio: (g, x, y) => { g.strokeRect(x - 60, y - 30, 120, 75); g.beginPath(); g.arc(x - 25, y + 8, 20, 0, Math.PI * 2); g.stroke();
    for (let i = 0; i < 4; i++) { g.beginPath(); g.moveTo(x + 10, y - 10 + i * 12); g.lineTo(x + 45, y - 10 + i * 12); g.stroke(); }
    g.beginPath(); g.moveTo(x + 30, y - 30); g.lineTo(x + 60, y - 75); g.stroke(); },
  pump: (g, x, y) => { g.strokeRect(x - 45, y - 60, 70, 115); g.strokeRect(x - 33, y - 48, 46, 30);
    g.beginPath(); g.moveTo(x + 25, y - 30); g.lineTo(x + 50, y - 30); g.lineTo(x + 50, y + 30); g.lineTo(x + 38, y + 40); g.stroke(); },
  cash: (g, x, y) => { g.strokeRect(x - 65, y - 35, 130, 70); g.beginPath(); g.arc(x, y, 20, 0, Math.PI * 2); g.stroke();
    g.strokeRect(x - 55, y - 25, 110, 50); },
};
export function choiceKind(S) {
  const opts = [["radio", "OPTION 01", "RESTER CHEZ SOI", "Écouter la radio FM"], ["pump", "OPTION 02", "FAIRE LE PLEIN", "Pompes bloquées sans banque"], ["cash", "OPTION 03", "ACHETER EN ESPÈCES", "Avec le peu de liquide"]];
  const head = el(`<div class="caps bsub o">Jour 01 · 24 heures de coupure</div><div class="btitle">CHOIX IMPOSSIBLE</div>`, "bars");
  const cards = opts.map((o, i) => el(`<div class="caps ck">${o[1]}</div><div class="ct">${o[2]}</div><div class="caps cd">${o[3]}</div>`, "card", `left:${190 + i * 540}px;top:560px`));
  const act = S.p.active;
  return (t) => {
    reveal(head, t, 0.3, S.dur + 1); clear2d();
    opts.forEach((o, i) => {
      const a = act < 0 ? (S.spans[2] || S.spans[S.spans.length - 1])[0] + i * 0.3 : 0.25 + i * 0.12;
      const v = reveal(cards[i], t, a, S.dur + 1, 0.45, 0.3, 24);
      const on = act < 0 || act === i, dim = on ? 1 : 0.35;
      cards[i].style.opacity = (v * dim).toFixed(3);
      cards[i].classList.toggle("on", act === i && t > 0.6);
      g2.globalAlpha = v * dim; g2.strokeStyle = act === i && i === 1 ? RED : act === i ? CYAN : "rgba(230,236,240,.85)"; g2.lineWidth = 3;
      ICON[o[0]](g2, 190 + i * 540 + 230, 430);
      if (act === 1 && i === 1 && t > 1.2) { g2.strokeStyle = RED; g2.lineWidth = 5; const k = sstep(1.2, 1.6, t);
        g2.beginPath(); g2.moveTo(190 + 540 + 150, 350); g2.lineTo(190 + 540 + 150 + 160 * k, 350 + 160 * k); g2.stroke(); }
    });
    g2.globalAlpha = 1;
  };
}

// ---------- LISTES (cartes « réel ») ----------
export function listKind(S) {
  const items = S.p.items, n = items.length, big = n <= 2;
  const head = el(`<div class="caps bsub c">Ce qui s'est vraiment produit</div><div class="btitle">${big ? "DEUX PANNES RÉELLES" : "TOUT EST DÉJÀ ARRIVÉ"}</div>`, "bars");
  const cols = big ? 2 : 4;
  const cards = items.map((it, i) => {
    const [a, b] = it.includes(" · ") ? it.split(" · ") : [it, ""];
    const x = 150 + (i % cols) * (big ? 820 : 420), y = (big ? 470 : 400) + Math.floor(i / cols) * 230;
    return el(`<div class="caps rk"><i></i>RÉEL</div><div class="ct">${big ? b : a}</div><div class="caps cd">${big ? a : b}</div>`, "card rcard" + (big ? " wide" : ""), `left:${x}px;top:${y}px`);
  });
  return (t) => {
    reveal(head, t, 0.3, S.dur + 1); clear2d();
    const a0 = (S.spans[0] || [0.4])[0] + 0.4, step = big ? Math.max(1.2, ((S.spans[1] || [S.dur * 0.5])[0] - a0)) : Math.min(0.45, (S.dur - 2) / n);
    cards.forEach((c, i) => reveal(c, t, a0 + i * step, S.dur + 1, 0.45, 0.3, 24));
  };
}

// ---------- TITRES ----------
export function titleKind(S) {
  const p = S.p, sp = S.spans;
  if (S.n === 3) {
    const head = el("Ce qui est inventé", "caps simhead");
    const lines = [["MARC", "INVENTÉ"], ["LE DÉCLENCHEUR", "INVENTÉ"], ["LA CHRONOLOGIE", "INVENTÉE"]].map(([a, b], i) => el(`${a} — <em>${b}</em>`, "simline", `top:${470 + i * 66}px`));
    const chip = el(`<i></i>SIMULATION`, "tag sim bigchip");
    return (t) => {
      reveal(chip, t, (sp[0] || [0.2])[0], S.dur + 1); reveal(head, t, (sp[1] || [1])[0] - 0.2, S.dur + 1);
      reveal(lines[0], t, (sp[1] || [1])[0], S.dur + 1); reveal(lines[1], t, (sp[2] || [2])[0], S.dur + 1); reveal(lines[2], t, (sp[2] || [2])[0] + 0.9, S.dur + 1);
    };
  }
  if (S.n === 61) {
    const l = el(`<div class="caps cd">L'électricité</div><div class="sbig c">LUMIÈRE OK</div>`, "split", "left:0;background:rgba(10,40,44,.85)");
    const r = el(`<div class="caps cd">Le réseau</div><div class="sbig r">DONNÉES KO</div>`, "split", "left:960px;background:rgba(60,10,14,.85)");
    return (t) => { reveal(l, t, (sp[0] || [0.2])[0], S.dur + 1, 0.5, 0.3, 0); reveal(r, t, (sp[0] || [0.2])[1] - 1.2, S.dur + 1, 0.5, 0.3, 0); };
  }
  const box = el(`<div class="tbig">${p.big}</div><div class="caps tsub">${p.sub}</div>`, "tcenter" + (S.n === 64 ? " q" : ""));
  const cur = S.n === 64 ? el("", "cursor") : null;
  return (t) => {
    reveal(box, t, (sp[0] || [0.2])[0] + 0.1, S.dur + 1, 0.6);
    if (cur) cur.style.opacity = (Math.floor(t * 2) % 2 && t > 1) ? 1 : 0;
  };
}

// ---------- CARTES ----------
let GEO = null;
export async function loadGeo() { if (!GEO) GEO = await (await fetch("/assets/countries.geojson")).json(); return GEO; }
const REG = { usa: [-128, -64, 22, 52], canada: [-142, -50, 40, 72], france: [-5.6, 10.2, 41.0, 51.6], world: [-170, 190, -58, 78], pacific: [160, 205, -32, -8] };
const CABLES = [[[-74, 40], [-5, 50]], [[-70, 41], [-9, 43]], [[-80, 26], [-9, 38]], [[-43, -23], [-9, 38]], [[-38, -4], [-17, 14]], [[18, -34], [-9, 38]],
  [[-122, 37], [140, 35]], [[-118, 34], [151, -34]], [[-122, 47], [141, 39]], [[-157, 21], [174, -37]], [[103, 1], [72, 19]], [[72, 19], [55, 25]],
  [[32, 30], [12, 44]], [[103, 1], [151, -34]], [[121, 25], [103, 1]], [[-80, 9], [-77, -12]], [[-5, 36], [32, 31]], [[-9, 38], [-5, 50]]];
export function mapKind(S, geo) {
  const p = S.p, reg = REG[p.region] || REG.world;
  const shiftLon = (lon) => (p.region === "pacific" && lon < 0 ? lon + 360 : lon);
  const [lo0, lo1, la0, la1] = reg, midLat = (la0 + la1) / 2, kx = Math.cos(midLat * Math.PI / 180);
  const pad = 70, sx = (1920 - 2 * pad) / ((lo1 - lo0) * kx), sy = (1080 - 2 * pad) / (la1 - la0), s = Math.min(sx, sy);
  const ox = 960 - (lo0 + lo1) / 2 * kx * s, oy = 540 + (la0 + la1) / 2 * s;
  const proj = (lon, lat) => [ox + shiftLon(lon) * kx * s, oy - lat * s];
  const paths = [];
  for (const f of geo.features) {
    const iso = f.properties.ADM0_A3 || f.properties.ISO_A3, polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    const path = new Path2D(); let any = false;
    for (const poly of polys) for (const ring of poly) {
      if (p.region === "pacific") { const xs = ring.map((c) => shiftLon(c[0])); if (Math.max(...xs) - Math.min(...xs) > 180) continue; }
      ring.forEach(([lon, lat], i) => { const [x, y] = proj(lon, lat); if (i) path.lineTo(x, y); else path.moveTo(x, y); }); path.closePath(); any = true;
    }
    if (any) paths.push({ iso, path });
  }
  const hl = new Set(p.highlight || (p.region === "france" ? ["FRA"] : []));
  // points à l'intérieur de la France (départements : répartition pseudo-aléatoire)
  const dots = [];
  if (p.dots) { reseed(S.n * 7); const fra = paths.find((q) => q.iso === "FRA");
    while (dots.length < p.dots) { const lon = -4.8 + rnd() * 13, lat = 42.3 + rnd() * 8.8, [x, y] = proj(lon, lat);
      if (fra && g2.isPointInPath(fra.path, x, y)) dots.push([x, y, rnd()]); } }
  const pts = (p.points || []).map(([lon, lat, name]) => [...proj(lon, lat), name]);
  const labels = pts.map(([x, y, name], i) => el(`<i></i><span>${name}</span>`, "pin " + (p.cable_cut ? (i ? "ok" : "bad") : "bad"), `left:${x - 6}px;top:${y - 12}px`));
  const title = el(`<div class="big">${S.onscreen.split(" · ")[0]}</div><div class="sub caps o">${S.onscreen.split(" · ").slice(1).join(" · ") || ""}</div>`, "title maptitle");
  const cuts = [];
  return (t) => {
    clear2d();
    const z = 1 + 0.06 * sstep(0, S.dur, t), cx = 960, cy = 540;
    g2.setTransform(z, 0, 0, z, cx * (1 - z), cy * (1 - z));
    const bg = g2.createRadialGradient(960, 500, 100, 960, 540, 1100); bg.addColorStop(0, "#1a1d20"); bg.addColorStop(1, "#0b0d0f");
    g2.fillStyle = bg; g2.fillRect(-200, -200, 2320, 1480);
    g2.strokeStyle = "rgba(255,255,255,.035)"; g2.lineWidth = 1;
    for (let lon = -180; lon <= 360; lon += 10) { const [x] = proj(lon, 0); g2.beginPath(); g2.moveTo(x, -200); g2.lineTo(x, 1300); g2.stroke(); }
    for (let lat = -80; lat <= 80; lat += 10) { const [, y] = proj(0, lat); g2.beginPath(); g2.moveTo(-200, y); g2.lineTo(2200, y); g2.stroke(); }
    const lv = sstep(0, 0.8, t);
    for (const q of paths) {
      const h = hl.has(q.iso), k = h ? sstep(0.6, 1.4, t) : 0;
      g2.fillStyle = h ? `rgba(${lerp(46, 70, k)},${lerp(50, 76, k)},${lerp(55, 84, k)},${lv})` : `rgba(42,45,49,${lv})`; g2.fill(q.path);
      g2.strokeStyle = h ? `rgba(240,244,245,${0.25 + 0.6 * k})` : `rgba(110,118,125,${0.5 * lv})`; g2.lineWidth = h ? 1.6 : 0.8; g2.stroke(q.path);
    }
    if (p.cables) CABLES.forEach(([a, b], i) => {
      const [x0, y0] = proj(...a), [x1, y1] = proj(...b), k = sstep(0.5 + i * 0.08, 1.6 + i * 0.08, t);
      const mx = (x0 + x1) / 2, my = (y0 + y1) / 2 + Math.abs(x1 - x0) * 0.12;
      g2.strokeStyle = `rgba(95,212,220,${0.75 * k})`; g2.lineWidth = 2.2; g2.setLineDash([2000]); g2.lineDashOffset = 2000 * (1 - k);
      g2.beginPath(); g2.moveTo(x0, y0); g2.quadraticCurveTo(mx, my, x1, y1); g2.stroke(); g2.setLineDash([]);
      // impulsions de données le long des câbles
      const u = ((t * 0.35 + i * 0.13) % 1);
      const px = (1 - u) * (1 - u) * x0 + 2 * (1 - u) * u * mx + u * u * x1, py = (1 - u) * (1 - u) * y0 + 2 * (1 - u) * u * my + u * u * y1;
      g2.fillStyle = `rgba(220,250,255,${k})`; g2.beginPath(); g2.arc(px, py, 3, 0, Math.PI * 2); g2.fill();
    });
    if (p.cable_cut && pts.length > 1) {
      const [x0, y0] = pts[0], [x1, y1] = pts[1], mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
      g2.strokeStyle = CYAN; g2.lineWidth = 3; g2.beginPath(); g2.moveTo(x1, y1); g2.lineTo(mx + (x1 - mx) * 0.1, my + (y1 - my) * 0.1); g2.stroke();
      const cut = sstep(1.5, 1.8, t);
      g2.strokeStyle = cut > 0 ? RED : CYAN; g2.beginPath(); g2.moveTo(x0, y0); g2.lineTo(mx - (mx - x0) * 0.1, my - (my - y0) * 0.1); g2.stroke();
      if (cut > 0) { const bl = 0.6 + 0.4 * Math.sin(t * 8); g2.strokeStyle = `rgba(255,90,95,${bl})`; g2.lineWidth = 5;
        g2.beginPath(); g2.moveTo(mx - 16, my - 16); g2.lineTo(mx + 16, my + 16); g2.moveTo(mx + 16, my - 16); g2.lineTo(mx - 16, my + 16); g2.stroke(); }
    }
    dots.forEach(([x, y, r], i) => {
      const a = 0.6 + r * Math.max(1, S.dur * 0.45), k = sstep(a, a + 0.3, t);
      if (k <= 0) return;
      const lit = p.relight ? sstep(a + 0.25, a + 0.6, t) : 0;
      g2.fillStyle = p.relight ? (lit > 0.5 ? CYAN : "rgba(255,90,95,.8)") : ORANGE; g2.globalAlpha = k;
      g2.beginPath(); g2.arc(x, y, p.relight ? 4.5 : 5, 0, Math.PI * 2); g2.fill();
      if (p.relight && lit > 0 && lit < 1) { g2.strokeStyle = `rgba(95,212,220,${1 - lit})`; g2.lineWidth = 2; g2.beginPath(); g2.arc(x, y, 4 + lit * 18, 0, Math.PI * 2); g2.stroke(); }
      g2.globalAlpha = 1;
    });
    pts.forEach(([x, y], i) => {
      const a = 0.8 + i * 0.5, k = sstep(a, a + 0.4, t); if (k <= 0) return;
      const pul = (t * 1.1 + i * 0.3) % 1, col = p.cable_cut && i ? CYAN : RED;
      g2.fillStyle = col; g2.beginPath(); g2.arc(x, y, 8, 0, Math.PI * 2); g2.fill();
      g2.strokeStyle = col; g2.globalAlpha = 1 - pul; g2.lineWidth = 2; g2.beginPath(); g2.arc(x, y, 8 + pul * 46, 0, Math.PI * 2); g2.stroke(); g2.globalAlpha = 1;
    });
    g2.setTransform(1, 0, 0, 1, 0, 0);
    pts.forEach(([x, y], i) => { const e = labels[i]; const X = cx + (x - cx) * z, Y = cy + (y - cy) * z; reveal(e, t, 1.0 + i * 0.5, S.dur + 1, 0.4, 0.3, 0); e.style.left = (X + 14) + "px"; e.style.top = (Y - 12) + "px"; });
    reveal(title, t, (S.spans[0] || [0.4])[0] + 0.2, S.dur + 1);
  };
}
