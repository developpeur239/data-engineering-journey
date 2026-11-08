// Socle commun : rendu, matériaux, textures dessinées, caméra, aléatoire déterministe.
import * as THREE from "three";
export { THREE };

export const W = +new URLSearchParams(location.search).get("w") || 1920;
export const H = Math.round(W * 9 / 16);
export const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07090b);
export const camera = new THREE.PerspectiveCamera(38, W / H, 0.03, 600);

let _seed = 11;
export const reseed = (s) => { _seed = s % 2147483646 + 1; };
export const rnd = () => (_seed = (_seed * 16807) % 2147483647) / 2147483647;
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * t * (t * (t * 6 - 15) + 10); };
export const lerp = (a, b, t) => a + (b - a) * t;
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const M = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
export const E = (c) => new THREE.MeshBasicMaterial({ color: c });

export function mesh(geo, mat, x = 0, y = 0, z = 0, parent = scene, shadow = true) {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z);
  m.castShadow = shadow; m.receiveShadow = true; parent.add(m); return m;
}
export const box = (w, h, d, mat, x, y, z, parent, shadow) => mesh(new THREE.BoxGeometry(w, h, d), mat, x, y, z, parent, shadow);

export function canvasTex(w, h, draw, rep = [1, 1]) {
  const c = document.createElement("canvas"); c.width = w; c.height = h; draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep[0], rep[1]); t.userData.canvas = c; return t;
}
export const rep = (tex, x, y) => { const t = tex.clone(); t.needsUpdate = true; t.repeat.set(x, y); return t; };
// écran dynamique : on redessine la toile, la texture suit
export function screenTex(w, h) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return { t, g: c.getContext("2d"), w, h, draw(fn) { fn(this.g, w, h); t.needsUpdate = true; } };
}

// ---------- textures de matières ----------
export const TEX = {};
TEX.wood = canvasTex(512, 512, (g, w, h) => {
  for (let i = 0; i < 8; i++) {
    const c = 120 + rnd() * 40; g.fillStyle = `rgb(${c},${c * 0.72 | 0},${c * 0.5 | 0})`; g.fillRect(0, i * h / 8, w, h / 8);
    for (let k = 0; k < 40; k++) { g.strokeStyle = `rgba(60,35,20,${0.05 + rnd() * 0.08})`; g.beginPath();
      const y = i * h / 8 + rnd() * h / 8; g.moveTo(0, y); g.bezierCurveTo(w * .3, y + rnd() * 6 - 3, w * .6, y + rnd() * 6 - 3, w, y); g.stroke(); }
    g.fillStyle = "rgba(30,18,10,.6)"; g.fillRect(0, i * h / 8, w, 2);
  }
});
TEX.plaster = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = "#cfc6b8"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 3000; i++) { g.fillStyle = `rgba(${rnd() < .5 ? 255 : 120},${rnd() < .5 ? 250 : 110},${rnd() < .5 ? 240 : 100},.04)`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
});
TEX.tiles = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = "#a9b0ae"; g.fillRect(0, 0, w, h);
  const tw = w / 4, th = h / 8;
  for (let r = 0; r < 8; r++) for (let c = 0; c < 4; c++) {
    const x = c * tw + 3, y = r * th + 3, ww = tw - 6, hh = th - 6;
    const gr = g.createLinearGradient(x, y, x, y + hh); gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.15, "#eef1ef"); gr.addColorStop(0.85, "#e3e7e5"); gr.addColorStop(1, "#c4cac8");
    g.fillStyle = gr; g.beginPath(); g.roundRect(x, y, ww, hh, 10); g.fill();
    g.fillStyle = "rgba(255,255,255,.7)"; g.fillRect(x + 10, y + 5, ww - 20, 3);
  }
});
TEX.granite = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = "#4a4f52"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 4000; i++) { const c = 50 + rnd() * 60; g.fillStyle = `rgba(${c},${c},${c + 4},.5)`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
  g.strokeStyle = "rgba(20,22,24,.7)"; g.lineWidth = 3; g.strokeRect(0, 0, w, h);
});
TEX.asphalt = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = "#2b2f33"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 5000; i++) { const c = 30 + rnd() * 40; g.fillStyle = `rgba(${c},${c},${c},.6)`; g.fillRect(rnd() * w, rnd() * h, 1.5, 1.5); }
});
TEX.lino = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = "#b9c4c2"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2500; i++) { g.fillStyle = `rgba(255,255,255,${rnd() * .12})`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
  g.strokeStyle = "rgba(90,100,100,.35)"; g.lineWidth = 2; g.strokeRect(0, 0, w, h);
});
TEX.concrete = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = "#8d8f8c"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 4000; i++) { const c = 110 + rnd() * 60; g.fillStyle = `rgba(${c},${c},${c - 4},.25)`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
});
TEX.stone = canvasTex(256, 256, (g, w, h) => {   // façade haussmannienne
  g.fillStyle = "#cbb898"; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 32) { g.fillStyle = "rgba(120,100,70,.35)"; g.fillRect(0, y, w, 2); }
  for (let i = 0; i < 2500; i++) { g.fillStyle = `rgba(255,240,210,${rnd() * .08})`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
});

export function facade(lit, base = "#c9b79c") {
  return canvasTex(128, 128, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    for (let y = 10; y < 118; y += 26) for (let x = 8; x < 120; x += 22) {
      const on = rnd() < lit; g.fillStyle = on ? (rnd() < .8 ? "#ffc27a" : "#d9ecff") : "#3a4652"; g.fillRect(x, y, 11, 17);
      g.fillStyle = "#2b2b2b"; g.fillRect(x - 2, y + 17, 15, 2);
    }
  });
}

// ---------- pièces et mobilier génériques ----------
export function room(parent, { w = 7, d = 7, h = 2.9, wall, floor, ceil = 0xd9d2c6, x = 0, z = 0, open = [] } = {}) {
  const f = mesh(new THREE.PlaneGeometry(w, d), floor, x, 0, z, parent); f.rotation.x = -Math.PI / 2;
  if (!open.includes("back")) box(w, h, 0.12, wall, x, h / 2, z - d / 2, parent);
  if (!open.includes("left")) box(0.12, h, d, wall, x - w / 2, h / 2, z, parent);
  if (!open.includes("right")) box(0.12, h, d, wall, x + w / 2, h / 2, z, parent);
  if (!open.includes("front")) box(w, h, 0.12, wall, x, h / 2, z + d / 2, parent, false);
  if (ceil !== null) box(w, 0.1, d, M(ceil, 1), x, h + 0.05, z, parent, false);
}
export function counter(parent, x, z, w, d, h, body, top) {
  box(w, h - 0.05, d, body, x, (h - 0.05) / 2, z, parent);
  box(w + 0.06, 0.05, d + 0.06, top, x, h - 0.025, z, parent);
}
export function shelfUnit(parent, x, z, w, rows, fill, rot = 0, h = 1.9) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = rot; parent.add(g);
  const mt = M(0xdfe3e2, 0.5, 0.3);
  box(w, h, 0.05, mt, 0, h / 2, -0.25, g);
  for (let r = 0; r < rows; r++) {
    const y = 0.25 + r * (h - 0.3) / rows;
    box(w, 0.03, 0.5, mt, 0, y, 0, g);
    let px = -w / 2 + 0.06;
    while (px < w / 2 - 0.08) {
      const bw = 0.07 + rnd() * 0.09, bh = 0.1 + rnd() * 0.2;
      if (rnd() < fill) box(bw, bh, 0.16 + rnd() * 0.1, M(new THREE.Color().setHSL(rnd(), 0.45, 0.45 + rnd() * 0.2), 0.6), px + bw / 2, y + 0.015 + bh / 2, (rnd() - .5) * 0.2, g);
      px += bw + 0.01;
    }
  }
  return g;
}
// halo lumineux flou (bokeh) pour les arrière-plans
export function bokeh(parent, n, spread, color, y0 = 1.5) {
  const tex = canvasTex(64, 64, (g, w, h) => {
    const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, "rgba(255,255,255,.9)"); gr.addColorStop(0.5, "rgba(255,255,255,.35)"); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  });
  const out = [];
  for (let i = 0; i < n; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, color: color[i % color.length], transparent: true, opacity: 0.5, depthWrite: false }));
    s.position.set((rnd() - .5) * spread[0], y0 + (rnd() - .5) * spread[1], -spread[2] * (0.4 + rnd() * 0.6)); s.scale.setScalar(0.2 + rnd() * 0.5);
    parent.add(s); out.push(s);
  }
  return out;
}

// ---------- caméra ----------
// clés : [temps, position, cible] ; transitions lissées entre deux clés, jamais d'arrêt complet (dérive lente)
export function camPath(t, keys) {
  let i = 0; while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
  const [t0, p0, q0] = keys[i], [t1, p1, q1] = keys[Math.min(i + 1, keys.length - 1)];
  const u = t1 > t0 ? sstep(t0, t1, t) : 0;
  return [p0.clone().lerp(p1, u), q0.clone().lerp(q1, u)];
}
export function handheld(t, a = 1) { return V(Math.sin(t * 0.9) * 0.012 * a, Math.sin(t * 1.3 + 1) * 0.008 * a, Math.sin(t * 0.7 + 2) * 0.01 * a); }
export function shake(t, impacts) {
  const v = V(0, 0, 0); let roll = 0;
  for (const [ti, tier] of impacts) {
    const a = { strong: 0.02, medium: 0.011, light: 0.005 }[tier] || 0.01, d = t - ti;
    if (d > 0 && d < 0.45) { const k = a * Math.exp(-d * 9); v.x += Math.sin(d * 70) * k; v.y += Math.sin(d * 53 + 1) * k; roll += Math.sin(d * 40) * k * 2; }
  }
  return [v, roll];
}
export function place(pos, tgt, roll = 0, fov = 38) {
  camera.position.copy(pos); camera.lookAt(tgt); camera.rotateZ(roll);
  camera.fov = fov; camera.updateProjectionMatrix();
}
