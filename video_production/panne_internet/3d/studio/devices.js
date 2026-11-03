// Décors d'objets et de lieux : aéroport, téléphone, terminal, distributeur, serveurs, centre d'appels,
// ordinateur, carnet, entrepôt, rayons, horloge, globe, mur d'écrans, fond graphique.
import { THREE, scene, M, E, mesh, box, canvasTex, rep, screenTex, TEX, facade, rnd, reseed, clamp, sstep, lerp, V, room, counter, shelfUnit, bokeh, camPath, handheld } from "./core.js";
import { person, face, blinkAt, walk, stand, sit } from "./people.js";

const INTER = "Inter, sans-serif";
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }

// ---------- aéroport : tableau des départs (Delta, 2024) ----------
export function airport(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x1a2026, 0.03);
  room(G, { w: 24, d: 18, h: 7, wall: M(0x3a4148, 0.8), floor: new THREE.MeshStandardMaterial({ map: rep(TEX.granite, 12, 9), roughness: 0.25, metalness: 0.2 }), ceil: 0x2a2f34, open: ["front"] });
  for (let i = 0; i < 6; i++) box(0.3, 0.06, 16, E(0xe8f4ff), -10 + i * 4, 6.9, 0, G, false);
  for (let i = 0; i < 6; i++) { const l = new THREE.PointLight(0xe0eeff, 10, 14, 1.5); l.position.set(-10 + i * 4, 6.5, -2); G.add(l); }
  G.add(new THREE.HemisphereLight(0x9fb0c0, 0x202428, 0.6));
  const board = screenTex(1600, 900);
  const bm = mesh(new THREE.PlaneGeometry(8, 4.5), new THREE.MeshBasicMaterial({ map: board.t }), 0, 3.6, -8.9, G, false);
  box(8.3, 4.8, 0.2, M(0x111418, 0.4, 0.6), 0, 3.6, -9.0, G);
  const boardL = new THREE.PointLight(0xffd27a, 8, 10, 1.6); boardL.position.set(0, 3.5, -7.5); G.add(boardL);
  reseed(70);
  const cities = ["ATLANTA", "NEW YORK JFK", "LOS ANGELES", "SEATTLE", "BOSTON", "DETROIT", "MINNEAPOLIS", "SALT LAKE CITY", "ORLANDO", "LAS VEGAS", "CHICAGO", "MIAMI"];
  const rows = cities.map((c, i) => ({ c, f: `DL ${1000 + Math.floor(rnd() * 8000)}`, h: `${String(6 + Math.floor(i / 2)).padStart(2, "0")}:${["05", "20", "35", "50"][i % 4]}`, k: rnd() }));
  const people = [];
  for (let i = 0; i < 10; i++) { const p = person({ coat: [0x3a3330, 0x2b3a45, 0x6a4a2a, 0x262626, 0x51463d, 0x34424a, 0x5a2e2e, 0x2e4a3a, 0x3d3d52, 0x704030][i], hair: [0x1a1410, 0x5a4030, 0x2a2420, 0x8a7a6a, 0x151515, 0x40301f, 0x6a3a1a, 0x222222, 0x9a8a70, 0x302010][i], shoes: 0x202020, long: i % 3 == 1, bag: i % 2 == 0 });
    p.g.position.set(-5 + (i % 5) * 2.4 + rnd(), 0, -2 - Math.floor(i / 5) * 2.2 + rnd()); p.g.rotation.y = Math.PI + (rnd() - 0.5) * 0.8; people.push(p);
    const suit = box(0.4, 0.6, 0.25, M([0x2a4a7a, 0x7a2a2a, 0x333333][i % 3], 0.5), p.g.position.x + 0.4, 0.3, p.g.position.z + 0.2, G); }
  return (t) => {
    const d = S.dur, a0 = S.at(/annuler|cinq/i, d * 0.5);
    board.draw((g, w, h) => {
      g.fillStyle = "#07090c"; g.fillRect(0, 0, w, h);
      g.fillStyle = "#ffd27a"; g.font = `bold 46px ${INTER}`; g.fillText("DÉPARTS", 50, 70); g.fillStyle = "#8a96a0"; g.font = `bold 26px ${INTER}`;
      ["HEURE", "VOL", "DESTINATION", "STATUT"].forEach((s, i) => g.fillText(s, [50, 230, 470, 1200][i], 120));
      rows.forEach((r, i) => {
        const y = 175 + i * 60, cancel = t > a0 - 0.4 + r.k * 2.2, flip = sstep(0, 0.12, (t - (a0 - 0.4 + r.k * 2.2)));
        g.fillStyle = i % 2 ? "#0d1116" : "#0a0d11"; g.fillRect(30, y - 42, w - 60, 56);
        g.font = `bold 34px "JetBrains Mono", monospace`; g.fillStyle = "#f2f4f5"; g.fillText(r.h, 50, y); g.fillText(r.f, 230, y); g.fillText(r.c, 470, y);
        g.fillStyle = cancel ? "#ff4d55" : "#5fd48a"; if (cancel && flip < 1) g.globalAlpha = flip;
        g.fillText(cancel ? "ANNULÉ" : "À L'HEURE", 1200, y); g.globalAlpha = 1;
      });
    });
    boardL.color.set(t > a0 ? 0xff7070 : 0xffd27a);
    people.forEach((p, i) => { stand(p, t, i); p.P.head.rotation.set(-0.25, Math.sin(t * 0.3 + i) * 0.2, 0); face(p, { worry: sstep(a0, a0 + 2, t) * 0.7, blink: blinkAt(t, i) }); });
    const [P0, T0] = camPath(t, [[0, V(-3, 1.7, 7), V(0, 3.2, -9)], [d + 1, V(1.5, 2.2, 2.5), V(0.5, 3.6, -9)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 42 };
  };
}

// ---------- téléphone en main ----------
export function phone(S) {
  const G = new THREE.Group(); scene.add(G);
  const night = S.n === 26 || S.n === 29;
  scene.background = new THREE.Color(night ? 0x0a0e14 : 0x161a1e);
  bokeh(G, 40, [8, 4, 10], night ? [0xffb060, 0xff5050, 0x60a0ff, 0xffffff] : [0xffd9a0, 0xa0c0ff, 0xffffff], 1.6);
  G.add(new THREE.HemisphereLight(0xa0b4c8, 0x202020, 0.7));
  const key = new THREE.SpotLight(0xfff0e0, 10, 6, 0.7, 0.6, 1.5); key.position.set(-1, 2.6, 1.5); key.target.position.set(0, 1.3, 0); G.add(key, key.target);
  const ph = new THREE.Group(); ph.position.set(0, 1.3, 0); G.add(ph);
  box(0.075, 0.155, 0.009, M(0x1b1c1f, 0.25, 0.7), 0, 0, 0, ph);
  const scr = screenTex(540, 1110);
  const sm = mesh(new THREE.PlaneGeometry(0.07, 0.148), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 0, 0.0047, ph, false);
  const glow = new THREE.PointLight(0x8fbfff, 1.2, 0.6, 2); glow.position.set(0, 0, 0.12); ph.add(glow);
  // main qui tient le téléphone
  const skin = new THREE.MeshPhysicalMaterial({ color: 0xe2b08f, roughness: 0.55, sheen: 0.4 });
  const hand = new THREE.Group(); hand.position.set(0.0, -0.06, -0.012); ph.add(hand);
  mesh(new THREE.CapsuleGeometry(0.03, 0.05, 6, 14), skin, 0, -0.02, -0.01, hand).scale.set(1.5, 1, 0.7);
  for (let i = 0; i < 3; i++) { const f = mesh(new THREE.CapsuleGeometry(0.009, 0.05, 4, 10), skin, 0.042, 0.02 + i * 0.024, -0.004, hand); f.rotation.z = 1.3; }
  const th = mesh(new THREE.CapsuleGeometry(0.01, 0.045, 4, 10), skin, -0.04, 0.0, 0.002, hand); th.rotation.z = -0.6;
  mesh(new THREE.CapsuleGeometry(0.035, 0.25, 6, 14), M(0x1d2a44, 0.85), 0.0, -0.2, -0.03, hand).rotation.x = 0.2;
  const p = S.p, lines = p.lines || [], bars = p.bars ?? 4;
  return (t) => {
    const d = S.dur, err = S.events.err ?? 0.6;
    scr.draw((g, w, h) => {
      const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, "#10161f"); bg.addColorStop(1, "#0a0d12"); g.fillStyle = bg; g.fillRect(0, 0, w, h);
      g.fillStyle = "#e9eef2"; g.font = `600 30px ${INTER}`; g.fillText(S.n === 26 ? "11:02" : S.n === 23 ? "08:30" : S.n === 29 ? "08:47" : "14:21", 40, 56);
      for (let i = 0; i < 4; i++) { g.fillStyle = i < bars ? "#e9eef2" : "rgba(233,238,242,.25)"; g.fillRect(w - 170 + i * 16, 52 - 8 - i * 6, 10, 8 + i * 6); }
      g.fillText("4G", w - 98, 56); rr(g, w - 54, 36, 36, 20, 4); g.strokeStyle = "#e9eef2"; g.lineWidth = 2; g.stroke(); g.fillRect(w - 51, 39, 22, 14);
      if (S.n === 10) {
        g.fillStyle = "#e9eef2"; g.font = `700 44px ${INTER}`; g.fillText("Applications", 40, 170);
        lines.forEach((name, i) => { const y = 240 + i * 230, bad = t > err + i * 0.5;
          rr(g, 40, y, w - 80, 190, 28); g.fillStyle = "#18202a"; g.fill();
          rr(g, 70, y + 35, 120, 120, 26); g.fillStyle = ["#2b2f36", "#1f3b33", "#1e3a24"][i]; g.fill();
          g.fillStyle = "#e9eef2"; g.font = `700 44px ${INTER}`; g.fillText(name[0], 112, y + 112);
          g.font = `700 38px ${INTER}`; g.fillText(name, 220, y + 85);
          g.fillStyle = bad ? "#ff5a5f" : "#8a96a0"; g.font = `500 28px ${INTER}`; g.fillText(bad ? "Service indisponible" : "Chargement…", 220, y + 130);
          if (bad) { g.fillStyle = "#ff5a5f"; g.beginPath(); g.arc(w - 100, y + 95, 26, 0, 7); g.fill(); g.fillStyle = "#fff"; g.font = `800 36px ${INTER}`; g.fillText("!", w - 107, y + 108); } });
      } else if (S.n === 26) {
        g.fillStyle = "#e9eef2"; g.textAlign = "center"; g.font = `500 34px ${INTER}`; g.fillText("Appel en cours", w / 2, 260);
        g.font = `700 70px ${INTER}`; g.fillText("Crèche", w / 2, 350);
        const busy = t > err; g.fillStyle = busy ? "#ff5a5f" : "#8a96a0"; g.font = `600 36px ${INTER}`;
        g.fillText(busy ? "Réseau occupé" : "Appel…", w / 2, 420);
        if (busy) { const pul = (t * 1.5) % 1; g.strokeStyle = `rgba(255,90,95,${1 - pul})`; g.lineWidth = 4; g.beginPath(); g.arc(w / 2, 640, 80 + pul * 90, 0, 7); g.stroke(); }
        g.beginPath(); g.arc(w / 2, 640, 80, 0, 7); g.fillStyle = "#26303a"; g.fill(); g.fillStyle = "#e9eef2"; g.font = `700 60px ${INTER}`; g.fillText("C", w / 2, 662);
        g.beginPath(); g.arc(w / 2, 960, 62, 0, 7); g.fillStyle = "#e5484d"; g.fill(); g.textAlign = "left";
      } else {
        // fil d'actualité qui ne charge pas
        for (let i = 0; i < 4; i++) { rr(g, 40, 150 + i * 220, w - 80, 190, 22); g.fillStyle = "#151c24"; g.fill();
          g.fillStyle = `rgba(255,255,255,${0.06 + 0.04 * Math.sin(t * 3 + i)})`; rr(g, 70, 180 + i * 220, 90, 90, 45); g.fill(); rr(g, 180, 190 + i * 220, 260, 22, 11); g.fill(); rr(g, 180, 230 + i * 220, 200, 18, 9); g.fill(); }
        g.fillStyle = "rgba(8,10,14,.82)"; g.fillRect(0, 380, w, 340);
        g.save(); g.translate(w / 2, 470); g.rotate(t * 5); g.strokeStyle = "#e9eef2"; g.lineWidth = 8; g.lineCap = "round"; g.beginPath(); g.arc(0, 0, 40, 0, Math.PI * 1.4); g.stroke(); g.restore();
        g.fillStyle = "#ff8a8d"; g.textAlign = "center"; g.font = `700 36px ${INTER}`;
        lines.forEach((l, i) => g.fillText(l, w / 2, 580 + i * 48)); g.textAlign = "left";
      }
    });
    ph.rotation.set(-0.25 + Math.sin(t * 0.7) * 0.03, 0.3 + Math.sin(t * 0.5) * 0.05, -0.08 + Math.sin(t * 0.9) * 0.02);
    ph.position.y = 1.3 + Math.sin(t * 1.1) * 0.004;
    glow.color.set(t > err && S.n !== 23 ? 0xff7070 : 0x8fbfff);
    const [P0, T0] = camPath(t, [[0, V(0.05, 1.33, 0.42), V(0, 1.3, 0)], [d + 1, V(-0.04, 1.32, 0.26), V(0, 1.3, 0)]]);
    return { pos: P0.add(handheld(t, 0.4)), tgt: T0, fov: 34 };
  };
}

// ---------- terminal de paiement sur un comptoir ----------
export function terminal(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x1d1a16, 0.05);
  const shop = S.n === 21;
  room(G, { w: 8, d: 7, h: 3, wall: M(shop ? 0xcfc0a8 : 0xb8c2c6, 0.9), floor: new THREE.MeshStandardMaterial({ map: rep(TEX.lino, 6, 6) }), ceil: 0xe0e0dc, open: ["front"] });
  if (shop) for (let i = 0; i < 4; i++) shelfUnit(G, -3 + i * 1.9, -3.2, 1.8, 5, 0.9);
  else { box(6, 1.2, 0.04, new THREE.MeshStandardMaterial({ color: 0xcfe8f0, transparent: true, opacity: 0.18, roughness: 0.05 }), 0, 1.75, -0.95, G, false);
    const sign = canvasTex(512, 128, (g, w, h) => { g.fillStyle = "#1d4f7a"; g.fillRect(0, 0, w, h); g.fillStyle = "#fff"; g.font = `bold 56px ${INTER}`; g.textAlign = "center"; g.fillText("RÉGIE · CAISSE", w / 2, 84); });
    mesh(new THREE.PlaneGeometry(1.6, 0.4), new THREE.MeshStandardMaterial({ map: sign, emissive: 0xffffff, emissiveMap: sign, emissiveIntensity: 0.4 }), 0, 2.6, -3.4, G, false); }
  counter(G, 0, -0.6, 3.6, 0.8, 1.0, M(shop ? 0x6a4a32 : 0x8a9196, 0.6), new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 2, 1), roughness: 0.4 }));
  const term = new THREE.Group(); term.position.set(0.2, 1.0, -0.4); term.rotation.set(-0.5, -0.25, 0); G.add(term);
  box(0.09, 0.03, 0.19, M(0x1a1d21, 0.3, 0.3), 0, 0.015, 0, term);
  const scr = screenTex(240, 180); const sm = mesh(new THREE.PlaneGeometry(0.07, 0.052), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 0.031, -0.045, term, false); sm.rotation.x = -Math.PI / 2;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) box(0.018, 0.006, 0.014, M(r === 3 ? [0xd04040, 0xe0c040, 0x40b060][c] : 0xd0d4d8, 0.4), -0.025 + c * 0.025, 0.033, 0.015 + r * 0.02, term);
  const card = box(0.054, 0.0015, 0.085, M(0x2d6fb7, 0.3, 0.4), 0, 0.03, 0.12, term);
  const tl = new THREE.PointLight(0x80c0ff, 0.6, 0.6, 2); tl.position.set(0.2, 1.08, -0.4); G.add(tl);
  if (shop) { box(0.25, 0.3, 0.12, M(0xd8b070, 0.7), -0.6, 1.15, -0.55, G); mesh(new THREE.CapsuleGeometry(0.035, 0.5, 6, 12), M(0xd59a4a, 0.7), -0.25, 1.04, -0.7, G).rotation.z = Math.PI / 2;
    mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.24, 14), M(0x3a7a4a, 0.3), 0.75, 1.12, -0.55, G); box(0.16, 0.08, 0.1, M(0xe85a3a, 0.6), 0.55, 1.04, -0.75, G); }
  for (let i = 0; i < 4; i++) { const l = new THREE.PointLight(0xfff1dc, 5, 7, 1.6); l.position.set(-2.4 + i * 1.6, 2.8, -1); G.add(l); }
  G.add(new THREE.HemisphereLight(0xffeedd, 0x302820, 0.6));
  const key = new THREE.SpotLight(0xffe8c8, 14, 6, 0.6, 0.6, 1.4); key.position.set(-1, 2.6, 1.2); key.target.position.set(0.2, 1, -0.4); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); G.add(key, key.target);
  const cust = person({ coat: 0x4a3b2a, inner: 0xcfc5b5, hair: 0x2a2420, long: true, shoes: 0x222222 }); cust.g.position.set(0.9, 0, 0.35); cust.g.rotation.y = Math.PI + 0.4;
  const clerk = person({ coat: 0x2f5d50, inner: 0xe0e0e0, hair: 0x151515, style: "apron", shoes: 0x222222, beard: true }); clerk.g.position.set(-0.2, 0, -1.4); clerk.g.rotation.y = 0.1;
  return (t) => {
    const d = S.dur, err = S.events.err ?? 0.6, bad = t > err;
    card.position.z = lerp(0.12, 0.08, sstep(err - 0.6, err - 0.2, t));
    scr.draw((g, w, h) => { g.fillStyle = bad ? "#9e1520" : "#163a55"; g.fillRect(0, 0, w, h); g.fillStyle = "#fff"; g.textAlign = "center";
      if (bad) { g.globalAlpha = 0.7 + 0.3 * Math.sign(Math.sin(t * 8)); g.font = `800 64px ${INTER}`; g.fillText("✕", w / 2, 92); g.globalAlpha = 1; g.font = `700 22px ${INTER}`; g.fillText(S.p.status || "ERREUR", w / 2, 150); }
      else { g.font = `700 26px ${INTER}`; g.fillText("CONNEXION…", w / 2, 100); } });
    tl.color.set(bad ? 0xff3030 : 0x80c0ff); tl.intensity = bad ? 1.4 : 0.6;
    stand(cust, t, 1); stand(clerk, t, 2);
    face(cust, { worry: sstep(err, err + 1, t) * 0.8, blink: blinkAt(t, 1) }); face(clerk, { worry: sstep(err, err + 1, t) * 0.6, blink: blinkAt(t, 3) });
    clerk.P.armL.sh.rotation.set(-0.5 * sstep(err + 0.6, err + 1.2, t), 0, 0.2); clerk.P.armL.el.rotation.x = -0.8 * sstep(err + 0.6, err + 1.2, t);
    if (shop) { const leave = S.at(/abandonnent/i, d * 0.7); cust.g.rotation.y = Math.PI + 0.4 + sstep(leave, leave + 0.8, t) * 2.4;
      cust.g.position.x = 0.9 + sstep(leave + 0.6, leave + 3, t) * 2.2; if (t > leave + 0.6) walk(cust, t * 6); }
    const [P0, T0] = camPath(t, [[0, V(0.45, 1.25, -0.15), V(0.2, 1.02, -0.4)], [err + 0.8, V(0.3, 1.32, -0.05), V(0.2, 1.03, -0.42)], [d + 1, V(-1.3, 1.65, 1.5), V(0.3, 1.15, -0.6)]]);
    return { pos: P0.add(handheld(t, 0.7)), tgt: T0, fov: 36 };
  };
}

// ---------- distributeur de billets dans la rue ----------
export function atm(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x1d242b, 0.04);
  scene.background = new THREE.Color(0x1a222a);
  const fl = mesh(new THREE.PlaneGeometry(30, 20), new THREE.MeshStandardMaterial({ map: rep(TEX.asphalt, 12, 8), roughness: 0.6, metalness: 0.1 }), 0, 0, 0, G); fl.rotation.x = -Math.PI / 2;
  box(30, 0.15, 3, M(0xa8a39a, 0.7), 0, 0.075, -1.5, G);
  box(14, 7, 0.4, new THREE.MeshStandardMaterial({ map: rep(TEX.stone, 4, 3), roughness: 0.9 }), 0, 3.5, -3.2, G);
  const mach = new THREE.Group(); mach.position.set(0, 0, -2.98); G.add(mach);
  box(1.0, 1.6, 0.06, M(0x2c3438, 0.4, 0.7), 0, 1.25, 0, mach);
  const scr = screenTex(400, 300); mesh(new THREE.PlaneGeometry(0.34, 0.255), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 1.5, 0.04, mach, false);
  for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) box(0.05, 0.04, 0.02, M(0xc9d1d4, 0.3, 0.8), -0.06 + c * 0.06, 1.15 - r * 0.05, 0.05, mach);
  box(0.12, 0.02, 0.03, M(0x0a0a0a), 0.25, 1.25, 0.05, mach); box(0.3, 0.03, 0.03, M(0x0a0a0a), 0, 0.88, 0.05, mach);
  const gl = new THREE.PointLight(0x80c0ff, 3, 3, 2); gl.position.set(0, 1.5, -2.5); G.add(gl);
  for (const x of [-5, 5]) { mesh(new THREE.CylinderGeometry(0.06, 0.08, 4.5, 10), M(0x1b1d20, 0.5, 0.6), x, 2.25, -0.5, G); const l = new THREE.PointLight(0xffb060, 14, 10, 1.6); l.position.set(x, 4.4, -0.4); G.add(l); mesh(new THREE.SphereGeometry(0.16, 12, 10), E(0xffd090), x, 4.5, -0.5, G, false); }
  G.add(new THREE.HemisphereLight(0x6a7f95, 0x1a1a1a, 0.55));
  const key = new THREE.SpotLight(0xdde8ff, 12, 10, 0.6, 0.7, 1.5); key.position.set(-2, 4, 3); key.target.position.set(0, 1.3, -2.8); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); G.add(key, key.target);
  const queue = [];
  const n = S.p.queue ? 6 : S.n === 15 ? 1 : 2;
  for (let i = 0; i < n; i++) { const p = person({ coat: [0x1d2a44, 0x4a3b2a, 0x2b3a45, 0x5a2e2e, 0x3a4a3a, 0x444444][i], hair: [0x3b2a20, 0x8a7a6a, 0x151515, 0x6a3a1a, 0x2a2420, 0x9a8a70][i], shoes: 0x222222, long: i % 2 == 1, bag: i === 2 });
    p.g.position.set(0.3 + i * 0.25, 0, -2.45 + i * 0.75); p.g.rotation.y = Math.PI + (i ? 0.25 : 0); queue.push(p); }
  return (t) => {
    const d = S.dur, err = S.events.err ?? 0.8, dark = S.n === 25 ? S.at(/rien/i, d - 1) : 1e9;
    const st = S.n === 24 ? "wait" : (t > err ? "bad" : "wait");
    scr.draw((g, w, h) => { if (t > dark) { g.fillStyle = "#020304"; g.fillRect(0, 0, w, h); return; }
      g.fillStyle = st === "bad" ? "#8e1420" : "#0f2f4a"; g.fillRect(0, 0, w, h); g.fillStyle = "#fff"; g.textAlign = "center";
      if (st === "bad") { g.font = `800 90px ${INTER}`; g.fillText("✕", w / 2, 150); g.font = `700 26px ${INTER}`; g.fillText(S.p.status, w / 2, 230); }
      else { g.save(); g.translate(w / 2, 120); g.rotate(t * 4); g.strokeStyle = "#fff"; g.lineWidth = 10; g.lineCap = "round"; g.beginPath(); g.arc(0, 0, 44, 0, Math.PI * 1.4); g.stroke(); g.restore();
        g.font = `700 26px ${INTER}`; g.fillText(S.p.status, w / 2, 230); } });
    gl.color.set(t > dark ? 0x000000 : st === "bad" ? 0xff3030 : 0x80c0ff); gl.intensity = t > dark ? 0 : 3;
    queue.forEach((p, i) => { stand(p, t, i); face(p, { worry: 0.4 + 0.4 * sstep(err, err + 1, t), blink: blinkAt(t, i) }); p.P.head.rotation.set(0.1, Math.sin(t * 0.4 + i) * 0.25, 0); });
    if (queue[0]) { queue[0].P.armR.sh.rotation.set(-1.0, 0, -0.1); queue[0].P.armR.el.rotation.x = -0.6 + Math.sin(t * 5) * 0.05 * (t < err ? 1 : 0); }
    const [P0, T0] = S.p.queue ? camPath(t, [[0, V(4.5, 1.8, 3.2), V(0.6, 1.4, -1.0)], [d + 1, V(3.4, 1.7, 1.2), V(0.3, 1.4, -2.0)]])
      : camPath(t, [[0, V(-1.8, 1.7, 0.8), V(0, 1.4, -3)], [err + 0.5, V(-1.0, 1.65, -1.2), V(0, 1.45, -3)], [d + 1, V(-0.75, 1.6, -1.9), V(0, 1.48, -3)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 38 };
  };
}

// ---------- salle de serveurs (et centre d'appels) ----------
export function servers(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x070a0d, 0.06);
  const mode = S.p.mode || "fail";
  if (S.p.label) return callCenter(S, G);
  const fl = mesh(new THREE.PlaneGeometry(10, 40), new THREE.MeshStandardMaterial({ color: 0x23272b, roughness: 0.3, metalness: 0.4 }), 0, 0, -12, G); fl.rotation.x = -Math.PI / 2;
  const ledTex = []; const racks = [];
  for (const s of [-1, 1]) for (let i = 0; i < 12; i++) {
    const z = 2 - i * 1.4, rk = new THREE.Group(); rk.position.set(s * 1.4, 0, z); rk.rotation.y = -s * Math.PI / 2; G.add(rk);
    box(1.2, 2.2, 1.0, M(0x15181b, 0.4, 0.6), 0, 1.1, 0, rk);
    const tx = screenTex(64, 128); mesh(new THREE.PlaneGeometry(1.0, 2.0), new THREE.MeshBasicMaterial({ map: tx.t, transparent: true }), 0, 1.1, 0.505, rk, false);
    racks.push({ tx, z, s, k: rnd() });
  }
  box(0.4, 0.06, 36, E(0xbfd8ff), 0, 2.9, -12, G, false);
  const beacon = new THREE.PointLight(0xff2020, 0, 12, 1.5); beacon.position.set(0, 2.6, -4); G.add(beacon);
  G.add(new THREE.HemisphereLight(0x5a6a80, 0x101010, 0.5));
  for (let i = 0; i < 4; i++) { const l = new THREE.PointLight(0xbfd8ff, 4, 8, 1.6); l.position.set(0, 2.8, 1 - i * 4); G.add(l); }
  let tech = null;
  if (mode === "sync") { tech = person({ coat: 0x2a2e36, inner: 0x4a6a8a, hair: 0x2a1a10, shoes: 0x222222, style: "shirt", glasses: true }); tech.g.position.set(0.3, 0, -1.5); tech.g.rotation.y = -Math.PI / 2 + 0.2;
    box(0.5, 0.9, 0.4, M(0x333333, 0.5, 0.5), 0.9, 0.45, -1.5, G); const lap = screenTex(256, 160); const lm = mesh(new THREE.PlaneGeometry(0.34, 0.22), new THREE.MeshBasicMaterial({ map: lap.t }), 0.9, 1.06, -1.38, G, false); lm.rotation.set(-0.3, -Math.PI / 2 + 0.2, 0); tech.lap = lap; }
  return (t) => {
    const d = S.dur, ok = S.at(/retirée|corriger|retir/i, d * 0.4);
    racks.forEach((r, i) => r.tx.draw((g, w, h) => {
      g.clearRect(0, 0, w, h);
      for (let y = 0; y < 14; y++) { g.fillStyle = "rgba(40,44,50,.9)"; g.fillRect(4, 4 + y * 9, w - 8, 7);
        for (let x = 0; x < 6; x++) {
          const on = Math.sin(t * (6 + ((i * 7 + y * 3 + x) % 9)) + x + y) > 0.2;
          let c;
          if (mode === "fail") c = (Math.floor(t * 3 + r.k * 5) % 2) ? "#ff2a2a" : "#4a0a0a";
          else if (mode === "ok") c = t > ok - 0.5 + r.k ? (on ? "#3dff8a" : "#0a4a2a") : "#ff2a2a";
          else { const front = clamp((t / d) * 1.3 - (2 - r.z) / 18); c = r.k < front ? (on ? "#3dff8a" : "#0a4a2a") : (on ? "#ffb02a" : "#4a3000"); }
          g.fillStyle = c; g.fillRect(8 + x * 9, 6 + y * 9, 4, 3);
        } }
    }));
    beacon.intensity = mode === "fail" ? (Math.sin(t * 6) > 0 ? 8 : 0) : 0;
    if (tech) { stand(tech, t); tech.P.armL.sh.rotation.set(-0.9, 0, 0.15); tech.P.armR.sh.rotation.set(-0.9, 0, -0.15); tech.P.armL.el.rotation.x = -0.6 + Math.sin(t * 14) * 0.05; tech.P.armR.el.rotation.x = -0.6 + Math.sin(t * 13 + 1) * 0.05;
      face(tech, { worry: 0.4, blink: blinkAt(t), look: [0, 0.3] }); tech.P.head.rotation.set(0.4, 0, 0);
      tech.lap.draw((g, w, h) => { g.fillStyle = "#0b0f14"; g.fillRect(0, 0, w, h); g.fillStyle = "#3dff8a"; g.font = `14px "JetBrains Mono"`; for (let i = 0; i < 9; i++) g.fillText(`> reset db-${String(1000 + Math.floor(t * 4) * 9 + i).padStart(5, "0")} … ok`, 10, 20 + i * 16); }); }
    const [P0, T0] = camPath(t, [[0, V(0, 1.5, 4.5), V(0, 1.3, -10)], [d + 1, V(0.2, 1.4, 0.5), V(0, 1.3, -12)]]);
    return { pos: P0.add(handheld(t, 0.6)), tgt: T0, fov: 40 };
  };
}
function callCenter(S, G) {
  room(G, { w: 12, d: 10, h: 3, wall: M(0x2a3138, 0.9), floor: new THREE.MeshStandardMaterial({ color: 0x3a4046, roughness: 0.8 }), ceil: 0x1e2226, open: ["front"] });
  const ops = [], lamps = [];
  for (let i = 0; i < 6; i++) {
    const x = -3 + (i % 3) * 3, z = -2.5 + Math.floor(i / 3) * 2.6;
    counter(G, x, z, 2.2, 0.8, 0.75, M(0x4a5056, 0.6), M(0xd8dcdc, 0.4));
    const mon = box(0.55, 0.35, 0.03, M(0x0a0a0a), x, 1.1, z - 0.2, G);
    const lamp = mesh(new THREE.SphereGeometry(0.03, 12, 10), E(0xff2020), x + 0.6, 0.8, z - 0.1, G, false); lamps.push(lamp);
    const op = person({ coat: [0x3a4a6a, 0x6a3a3a, 0x3a5a4a, 0x5a4a3a, 0x444a5a, 0x6a5a3a][i], inner: 0xddd, hair: [0x151515, 0x5a3a20, 0x2a2420, 0x8a6a4a, 0x111111, 0x3a2a1a][i], style: "shirt", long: i % 2 == 0, shoes: 0x222222 });
    op.g.position.set(x, 0.0, z + 0.6); op.g.rotation.y = Math.PI; sit(op); op.g.position.y = 0.45; ops.push(op);
    const hs = mesh(new THREE.TorusGeometry(0.115, 0.01, 8, 24, Math.PI), M(0x111111, 0.4), 0, 0.03, 0, op.P.head, false); hs.rotation.z = 0;
    mesh(new THREE.CapsuleGeometry(0.005, 0.08, 4, 8), M(0x111111), 0.08, -0.07, 0.07, op.P.head, false).rotation.z = 1.1;
  }
  for (let i = 0; i < 4; i++) { const l = new THREE.PointLight(0xe0e8ff, 5, 8, 1.6); l.position.set(-3 + i * 2, 2.8, -1); G.add(l); }
  G.add(new THREE.HemisphereLight(0x8090a0, 0x202020, 0.5));
  const red = new THREE.PointLight(0xff2020, 3, 10, 1.5); red.position.set(0, 2.5, -1); G.add(red);
  return (t) => {
    const d = S.dur;
    lamps.forEach((l, i) => l.material.color.set(Math.sin(t * 8 + i * 1.7) > 0 ? 0xff2020 : 0x330000));
    red.intensity = 2 + Math.sin(t * 6) * 1.2;
    ops.forEach((o, i) => { o.P.armR.sh.rotation.set(-1.5, 0, -0.3); o.P.armR.el.rotation.set(-1.6, 0, 0); o.P.armL.sh.rotation.set(-0.8, 0, 0.1); o.P.armL.el.rotation.x = -0.8;
      face(o, { worry: 0.8, blink: blinkAt(t, i), open: 0.3 * Math.max(0, Math.sin(t * 4 + i)) }); o.P.head.rotation.set(0.1, Math.sin(t * 0.6 + i) * 0.2, 0); });
    const [P0, T0] = camPath(t, [[0, V(-4.5, 1.8, 3.5), V(0, 1.0, -1.5)], [d + 1, V(-2.0, 1.6, 1.8), V(0, 1.1, -1.8)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 40 };
  };
}

// ---------- ordinateur (maison ou hôpital) ----------
export function computer(S) {
  const G = new THREE.Group(); scene.add(G);
  const hosp = S.p.hospital; scene.fog = new THREE.FogExp2(hosp ? 0x15201f : 0x14100c, 0.05);
  room(G, { w: 6, d: 6, h: 2.8, wall: M(hosp ? 0xb8d0cc : 0xc9b89c, 0.9), floor: new THREE.MeshStandardMaterial({ map: rep(hosp ? TEX.lino : TEX.wood, 4, 4), roughness: 0.5 }), ceil: 0xe8e8e4, open: ["front"] });
  counter(G, 0, -1.6, 1.8, 0.75, 0.76, M(hosp ? 0xe0e4e4 : 0x6a4a32, 0.6), new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 1, 1), roughness: 0.4, color: hosp ? 0xe8eceb : 0xffffff }));
  const mon = new THREE.Group(); mon.position.set(0, 0.76, -1.75); G.add(mon);
  box(0.64, 0.4, 0.03, M(0x101214, 0.3), 0, 0.42, 0, mon); box(0.05, 0.2, 0.05, M(0x202224), 0, 0.12, -0.03, mon); box(0.22, 0.015, 0.16, M(0x202224), 0, 0.008, -0.03, mon);
  const scr = screenTex(640, 400); mesh(new THREE.PlaneGeometry(0.6, 0.37), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 0.42, 0.017, mon, false);
  box(0.42, 0.015, 0.14, M(0x2a2c2e, 0.5), 0, 0.775, -1.35, G);
  const glow = new THREE.PointLight(0x9cc6ff, 2.5, 2.5, 2); glow.position.set(0, 1.2, -1.4); G.add(glow);
  if (!hosp) { const lamp = new THREE.PointLight(0xffb060, 5, 4, 2); lamp.position.set(-0.8, 1.3, -1.6); G.add(lamp); mesh(new THREE.ConeGeometry(0.1, 0.14, 20, 1, true), M(0x1a1a1a, 0.5), -0.8, 1.32, -1.6, G);
    mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.18, 16), M(0xb8733b, 0.6), 0.7, 0.85, -1.8, G); mesh(new THREE.SphereGeometry(0.2, 14, 10), M(0x3a6a3a, 0.8), 0.7, 1.1, -1.8, G); }
  else for (let i = 0; i < 3; i++) { const l = new THREE.PointLight(0xeaffff, 4, 6, 1.6); l.position.set(-1.5 + i * 1.5, 2.7, -1); G.add(l); }
  G.add(new THREE.HemisphereLight(hosp ? 0xcfe8e4 : 0xffe0c0, 0x2a2420, 0.55));
  const who = person(hosp ? { coat: 0xf3f4f2, inner: 0x7fb0c8, pants: 0x6a8aa0, hair: 0x2a1a14, style: "whitecoat", long: true, shoes: 0xeeeeee, iris: 0x3a5a3a }
    : { ...{ coat: 0x2a3a4a, inner: 0xd8d8d8, pants: 0x232a36, hair: 0x6a3a1a, shoes: 0x333333, style: "shirt" } });
  who.g.position.set(0.15, 0, -0.75); who.g.rotation.y = Math.PI + 0.15; sit(who); who.g.position.y = 0.42;
  return (t) => {
    const d = S.dur, err = S.events.err ?? 0.6, bad = t > err;
    scr.draw((g, w, h) => {
      g.fillStyle = "#f2f4f6"; g.fillRect(0, 0, w, h); g.fillStyle = "#dfe3e8"; g.fillRect(0, 0, w, 46);
      for (let i = 0; i < 3; i++) { g.fillStyle = ["#ff5f57", "#febc2e", "#28c840"][i]; g.beginPath(); g.arc(22 + i * 22, 23, 7, 0, 7); g.fill(); }
      rr(g, 90, 10, w - 120, 26, 13); g.fillStyle = "#fff"; g.fill(); g.fillStyle = "#6a7480"; g.font = `16px ${INTER}`; g.fillText(hosp ? "dossier-patient.hopital.local" : "www.actualites.fr", 106, 28);
      g.textAlign = "center";
      if (!bad) { g.save(); g.translate(w / 2, h / 2); g.rotate(t * 5); g.strokeStyle = "#7a8590"; g.lineWidth = 6; g.lineCap = "round"; g.beginPath(); g.arc(0, 0, 26, 0, Math.PI * 1.4); g.stroke(); g.restore(); }
      else { g.strokeStyle = "#5a6470"; g.lineWidth = 5; rr(g, w / 2 - 40, 110, 80, 64, 8); g.stroke(); g.beginPath(); g.moveTo(w / 2 - 18, 128); g.lineTo(w / 2 + 18, 156); g.moveTo(w / 2 + 18, 128); g.lineTo(w / 2 - 18, 156); g.stroke();
        g.fillStyle = "#1f2a36"; g.font = `700 30px ${INTER}`; g.fillText(S.p.status, w / 2, 240); g.fillStyle = "#6a7480"; g.font = `20px ${INTER}`;
        g.fillText(hosp ? "Serveur du laboratoire injoignable" : "Impossible de trouver l'adresse du serveur", w / 2, 280);
        rr(g, w / 2 - 80, 310, 160, 40, 20); g.fillStyle = "#2f6fd6"; g.fill(); g.fillStyle = "#fff"; g.font = `600 18px ${INTER}`; g.fillText("Réessayer", w / 2, 336); }
      g.textAlign = "left";
    });
    stand(who, t); sit(who); who.g.position.y = 0.42;
    who.P.armL.sh.rotation.set(-0.9, 0, 0.12); who.P.armR.sh.rotation.set(-0.9, 0, -0.12); who.P.armL.el.rotation.x = -0.5; who.P.armR.el.rotation.x = -0.5 + (t < err ? Math.sin(t * 12) * 0.05 : 0);
    who.P.head.rotation.set(0.05, 0, 0); face(who, { worry: sstep(err, err + 1, t) * 0.8, blink: blinkAt(t) });
    const [P0, T0] = camPath(t, [[0, V(0.9, 1.35, 0.3), V(0, 1.15, -1.75)], [err + 0.4, V(0.35, 1.22, -0.95), V(0, 1.18, -1.75)], [d + 1, V(0.12, 1.2, -1.25), V(0, 1.18, -1.75)]]);
    return { pos: P0.add(handheld(t, 0.5)), tgt: T0, fov: 38 };
  };
}

// ---------- carnet papier : écriture à la main ----------
export function notebook(S) {
  const G = new THREE.Group(); scene.add(G); scene.background = new THREE.Color(0x15110d);
  const hosp = S.n === 33;
  const desk = mesh(new THREE.PlaneGeometry(3, 2), new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 2, 2), roughness: 0.5, color: hosp ? 0xd8dcdc : 0xffffff }), 0, 0, 0, G); desk.rotation.x = -Math.PI / 2;
  const page = screenTex(800, 1000);
  const pm = mesh(new THREE.PlaneGeometry(0.32, 0.4), new THREE.MeshStandardMaterial({ map: page.t, roughness: 0.95 }), 0, 0.006, 0, G); pm.rotation.x = -Math.PI / 2;
  box(0.33, 0.006, 0.41, M(hosp ? 0x2a5a7a : 0x7a2a1e, 0.7), 0, 0.002, 0, G);
  const pen = new THREE.Group(); G.add(pen);
  mesh(new THREE.CylinderGeometry(0.004, 0.0045, 0.14, 12), M(0x1a2a5a, 0.3, 0.4), 0, 0.07, 0, pen); mesh(new THREE.ConeGeometry(0.004, 0.012, 12), M(0xcccccc, 0.2, 0.9), 0, -0.006, 0, pen).rotation.x = Math.PI;
  const skin = new THREE.MeshPhysicalMaterial({ color: 0xe2b08f, roughness: 0.55, sheen: 0.4 });
  const hand = mesh(new THREE.CapsuleGeometry(0.03, 0.05, 6, 14), skin, 0.02, 0.05, 0.04, pen); hand.scale.set(1.4, 1, 0.8); hand.rotation.z = 0.8;
  mesh(new THREE.CapsuleGeometry(0.035, 0.25, 6, 14), M(hosp ? 0xf3f4f2 : 0x2f5d50, 0.8), 0.12, 0.1, 0.12, pen).rotation.set(0.5, 0, 1.2);
  G.add(new THREE.HemisphereLight(0xffeedd, 0x2a2018, 0.7));
  const key = new THREE.SpotLight(0xffe2b8, 10, 3, 0.6, 0.6, 1.4); key.position.set(-0.4, 0.9, 0.3); key.target.position.set(0, 0, 0); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); G.add(key, key.target);
  const lines = [S.p.title, ...(S.p.lines || [])];
  return (t) => {
    const d = S.dur, a = 0.5, b = d - 0.6, total = lines.reduce((s, l) => s + l.length, 0);
    const k = clamp((t - a) / (b - a)) * total;
    let acc = 0, px = 0, py = 0;
    page.draw((g, w, h) => {
      g.fillStyle = "#f8f4ea"; g.fillRect(0, 0, w, h); g.strokeStyle = "rgba(80,120,170,.3)"; g.lineWidth = 2;
      for (let y = 140; y < h; y += 70) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); } g.strokeStyle = "rgba(220,80,80,.35)"; g.beginPath(); g.moveTo(90, 0); g.lineTo(90, h); g.stroke();
      lines.forEach((l, i) => { const n = Math.floor(clamp(k - acc, 0, l.length)); acc += l.length;
        g.fillStyle = "#1c2a5a"; g.font = i === 0 ? "700 54px 'Segoe Print', 'Comic Sans MS', cursive" : "44px 'Segoe Print', 'Comic Sans MS', cursive";
        const txt = l.slice(0, n), y = 120 + i * 140; g.fillText(txt, 110, y);
        if (n > 0 && n < l.length) { px = 110 + g.measureText(txt).width; py = y; } else if (n === l.length) { px = 110 + g.measureText(txt).width; py = y; } });
    });
    pen.position.set(-0.16 + px / 800 * 0.32, 0.01 + Math.abs(Math.sin(t * 18)) * 0.003, -0.2 + py / 1000 * 0.4);
    pen.rotation.set(0.5, 0, -0.5);
    const [P0, T0] = camPath(t, [[0, V(0.05, 0.42, 0.28), V(0, 0, -0.02)], [d + 1, V(-0.08, 0.36, 0.2), V(0.02, 0, -0.03)]]);
    return { pos: P0.add(handheld(t, 0.3)), tgt: T0, fov: 36 };
  };
}

// ---------- billets dans la main (option 3) ----------
// (la course dans la rue est dans places.street)

// ---------- entrepôt : camions bloqués ----------
export function warehouse(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x2a3038, 0.03); scene.background = new THREE.Color(0x3a4450);
  const fl = mesh(new THREE.PlaneGeometry(80, 60), new THREE.MeshStandardMaterial({ map: rep(TEX.concrete, 20, 15), roughness: 0.9 }), 0, 0, 0, G); fl.rotation.x = -Math.PI / 2;
  const corr = canvasTex(256, 256, (g, w, h) => { g.fillStyle = "#8a9296"; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 16) { g.fillStyle = "rgba(0,0,0,.18)"; g.fillRect(x, 0, 6, h); } });
  box(40, 9, 12, new THREE.MeshStandardMaterial({ map: rep(corr, 12, 3), roughness: 0.7, metalness: 0.3 }), 0, 4.5, -14, G);
  const trucks = [];
  for (let i = 0; i < 6; i++) {
    const x = -12.5 + i * 5; box(3.4, 3.6, 0.1, M(0x2a2e32, 0.6), x, 1.8, -7.95, G);
    const tr = new THREE.Group(); tr.position.set(x, 0, -2.2); G.add(tr);
    box(2.5, 2.8, 9, M([0xe8e8e8, 0xd0d8e0, 0xe8e0d0][i % 3], 0.6), 0, 2.0, -1.2, tr);
    box(2.4, 2.4, 2.0, M([0x2a4a7a, 0xa03030, 0x2a6a4a, 0x444444, 0x7a6a2a, 0x3a3a6a][i], 0.4, 0.4), 0, 1.6, 4.4, tr);
    box(2.0, 0.9, 0.05, new THREE.MeshStandardMaterial({ color: 0x1a2a3a, roughness: 0.05, metalness: 0.6 }), 0, 2.2, 5.42, tr);
    for (const [wx, wz] of [[-1.1, 4.6], [1.1, 4.6], [-1.1, -3.5], [1.1, -3.5], [-1.1, -4.8], [1.1, -4.8]]) mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.35, 20), M(0x111111, 0.8), wx, 0.5, wz, tr).rotation.z = Math.PI / 2;
    const hl = new THREE.PointLight(0xfff0d0, 3, 6, 2); hl.position.set(0, 1.0, 5.8); tr.add(hl); trucks.push(tr);
  }
  for (let i = 0; i < 5; i++) { mesh(new THREE.CylinderGeometry(0.1, 0.12, 8, 10), M(0x333333, 0.6, 0.5), -16 + i * 8, 4, 6, G); const l = new THREE.PointLight(0xffa040, 26, 22, 1.5); l.position.set(-16 + i * 8, 7.8, 5.5); G.add(l); mesh(new THREE.SphereGeometry(0.25, 12, 10), E(0xffc070), -16 + i * 8, 8, 6, G, false); }
  G.add(new THREE.HemisphereLight(0x8a9ab0, 0x2a2420, 0.6));
  const dawn = new THREE.DirectionalLight(0xffb880, 1.2); dawn.position.set(30, 10, 20); G.add(dawn);
  return (t) => {
    const d = S.dur;
    trucks.forEach((tr, i) => { tr.position.y = Math.sin(t * 40 + i) * 0.006; });
    const [P0, T0] = camPath(t, [[0, V(-14, 2.0, 16), V(-4, 2.0, -4)], [d + 1, V(-6, 6.5, 14), V(0, 1.5, -4)]]);
    return { pos: P0.add(handheld(t, 0.5)), tgt: T0, fov: 42 };
  };
}

// ---------- supermarché : rayons frais vides ----------
export function shelves(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x1e2420, 0.04);
  room(G, { w: 10, d: 30, h: 4, wall: M(0xd8dcd6, 0.9), floor: new THREE.MeshStandardMaterial({ map: rep(TEX.lino, 8, 24), roughness: 0.25 }), ceil: 0xe8ece8, open: ["front"], z: -10 });
  for (let i = 0; i < 6; i++) { shelfUnit(G, -2.2, 2 - i * 3.2, 3.0, 5, i < 2 ? 0.15 : 0.05, Math.PI / 2); shelfUnit(G, 2.2, 2 - i * 3.2, 3.0, 5, 0.45, -Math.PI / 2); }
  for (let i = 0; i < 8; i++) box(0.3, 0.05, 2.4, E(0xf4fff8), 0, 3.95, 3 - i * 3.4, G, false);
  for (let i = 0; i < 5; i++) { const l = new THREE.PointLight(0xeafff4, 6, 9, 1.6); l.position.set(0, 3.7, 2 - i * 4.5); G.add(l); }
  G.add(new THREE.HemisphereLight(0xdfeee6, 0x303030, 0.55));
  const shoppers = [];
  for (let i = 0; i < 5; i++) { const p = person({ coat: [0x5a4a3a, 0x2b3a45, 0x6a2e2e, 0x3a4a3a, 0x444444][i], hair: [0x2a2420, 0x8a7a6a, 0x151515, 0x6a3a1a, 0x444444][i], shoes: 0x222222, long: i % 2 == 0, bag: i === 3 });
    p.g.position.set(-0.8 + (i % 2) * 1.4, 0, -1 - i * 3); p.g.rotation.y = i % 2 ? -Math.PI / 2 : Math.PI / 2; shoppers.push(p); }
  return (t) => {
    const d = S.dur;
    shoppers.forEach((p, i) => { stand(p, t, i); p.P.head.rotation.set(0.15, Math.sin(t * 0.5 + i) * 0.4, 0); face(p, { worry: 0.8, blink: blinkAt(t, i) });
      p.P.armR.sh.rotation.set(-0.9 * (Math.sin(t * 0.7 + i) > 0.6 ? 1 : 0.2), 0, -0.1); });
    const [P0, T0] = camPath(t, [[0, V(0, 1.6, 6), V(0, 1.3, -10)], [d + 1, V(0.2, 1.5, 1.5), V(-0.5, 1.2, -12)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 42 };
  };
}

// ---------- horloge numérique 3D (19 juillet 2024, 04:08:40 UTC) ----------
export function chrono(S) {
  const G = new THREE.Group(); scene.add(G); scene.background = new THREE.Color(0x050607);
  const deskM = new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 2, 1), roughness: 0.35, color: 0x5a4a3a });
  const desk = mesh(new THREE.PlaneGeometry(4, 2), deskM, 0, 0, 0, G); desk.rotation.x = -Math.PI / 2;
  const clk = new THREE.Group(); G.add(clk);
  box(0.5, 0.2, 0.14, M(0x0c0d0e, 0.35, 0.3), 0, 0.1, 0, clk);
  const dig = screenTex(800, 300); mesh(new THREE.PlaneGeometry(0.44, 0.165), new THREE.MeshBasicMaterial({ map: dig.t }), 0, 0.105, 0.0705, clk, false);
  const glow = new THREE.PointLight(0xff6a2a, 2.2, 1.5, 2); glow.position.set(0, 0.12, 0.3); G.add(glow);
  const mons = [];
  for (let i = 0; i < 5; i++) { const m = box(0.7, 0.42, 0.03, E(0x0b1020), -1.4 + i * 0.7, 0.6, -1.0 - Math.abs(i - 2) * 0.15, G, false); m.rotation.y = (2 - i) * 0.15; mons.push(m); }
  const monL = new THREE.PointLight(0x2a6aff, 0, 4, 2); monL.position.set(0, 0.7, -0.6); G.add(monL);
  G.add(new THREE.HemisphereLight(0x404850, 0x101010, 0.2));
  const [h0, m0, s0] = S.p.start.split(":").map(Number);
  return (t) => {
    const d = S.dur, secs = h0 * 3600 + m0 * 60 + s0 + t * (20 / Math.max(d, 1)) * 1.6;
    const hh = Math.floor(secs / 3600), mm = Math.floor(secs / 60) % 60, ss = Math.floor(secs) % 60;
    dig.draw((g, w, h) => { g.fillStyle = "#070505"; g.fillRect(0, 0, w, h); g.font = `700 190px "JetBrains Mono", monospace`; g.textAlign = "center";
      g.shadowColor = "#ff5a1a"; g.shadowBlur = 30; g.fillStyle = "#ff7a2a"; g.fillText(`${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`, w / 2, 215); g.shadowBlur = 0; });
    const crash = secs >= h0 * 3600 + 9 * 60;
    mons.forEach((m, i) => m.material.color.set(crash && t > (S.at(/diffusée/i, d * 0.7)) - 0.3 + i * 0.15 ? 0x0a4adf : 0x0b1020));
    monL.intensity = crash ? 3 : 0;
    const [P0, T0] = camPath(t, [[0, V(0.0, 0.16, 0.55), V(0, 0.1, 0)], [d * 0.6, V(0.18, 0.22, 0.75), V(0, 0.12, 0)], [d + 1, V(0.35, 0.45, 1.25), V(-0.1, 0.25, -0.6)]]);
    return { pos: P0.add(handheld(t, 0.3)), tgt: T0, fov: 34 };
  };
}

// ---------- mur d'écrans (8,5 millions de machines) ----------
export function monitors(S) {
  const G = new THREE.Group(); scene.add(G); scene.background = new THREE.Color(0x040506);
  const ms = [];
  for (let r = 0; r < 6; r++) for (let c = 0; c < 12; c++) { const m = box(0.6, 0.36, 0.03, E(0x1d3a44), -3.6 + c * 0.66, 0.4 + r * 0.42, -2 - Math.abs(c - 5.5) * 0.08, G, false); ms.push({ m, k: rnd() }); }
  const L = new THREE.PointLight(0x2a6aff, 0, 8, 1.5); L.position.set(0, 1.5, 0); G.add(L);
  return (t) => {
    const d = S.dur, a = S.at(/^huit$/i, d * 0.6);
    let on = 0; ms.forEach(({ m, k }) => { const b = t > a - 1.2 + k * 1.6; m.material.color.set(b ? 0x0a4adf : (Math.sin(t * 2 + k * 9) > 0.95 ? 0x2a5a66 : 0x1d3a44)); on += b; });
    L.intensity = on / ms.length * 4;
    const [P0, T0] = camPath(t, [[0, V(0, 1.4, 5.5), V(0, 1.4, -2)], [d + 1, V(0.4, 1.5, 3.0), V(0, 1.45, -2)]]);
    return { pos: P0.add(handheld(t, 0.3)), tgt: T0, fov: 40 };
  };
}

// ---------- globe ----------
export async function globe(S) {
  const G = new THREE.Group(); scene.add(G); scene.background = new THREE.Color(0x020306);
  const L = new THREE.TextureLoader(), load = (f) => new Promise((r) => L.load("/assets/" + f, (t) => { t.colorSpace = THREE.SRGBColorSpace; r(t); }, undefined, () => r(null)));
  const [day, lights, clouds] = await Promise.all([load("earth_atmos_2048.jpg"), load("earth_lights_2048.png"), load("earth_clouds_1024.png")]);
  const night = S.p.mode === "night";
  const mat = new THREE.MeshStandardMaterial({ map: day, roughness: 0.9, emissive: 0xffc070, emissiveMap: lights, emissiveIntensity: night ? 2.2 : 0.0 });
  if (night) mat.color.set(0x56647a);
  const earth = mesh(new THREE.SphereGeometry(1, 96, 64), mat, 0, 0, 0, G, false);
  const cl = mesh(new THREE.SphereGeometry(1.012, 72, 48), new THREE.MeshStandardMaterial({ map: clouds, transparent: true, opacity: night ? 0.25 : 0.7, depthWrite: false }), 0, 0, 0, G, false);
  const atm = new THREE.Mesh(new THREE.SphereGeometry(1.08, 64, 48), new THREE.ShaderMaterial({ transparent: true, side: THREE.BackSide, depthWrite: false,
    vertexShader: "varying vec3 n; void main(){ n = normalize(normalMatrix*normal); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} ",
    fragmentShader: "varying vec3 n; void main(){ float k = pow(0.72 - dot(n, vec3(0,0,1.0)), 3.0); gl_FragColor = vec4(0.35,0.6,1.0,1.0)*k; }" }));
  G.add(atm);
  const sun = new THREE.DirectionalLight(0xffffff, night ? 0.7 : 2.4); sun.position.set(-5, 2, 5); G.add(sun);
  G.add(new THREE.AmbientLight(0x223344, night ? 0.25 : 0.15));
  const stars = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(Array.from({ length: 3000 }, () => (rnd() - 0.5) * 200), 3)), new THREE.PointsMaterial({ color: 0xffffff, size: 0.15 }));
  G.add(stars);
  const ll = (lon, lat, r = 1.0) => { const ph = (90 - lat) * Math.PI / 180, th = (lon + 180) * Math.PI / 180; return V(-r * Math.sin(ph) * Math.cos(th), r * Math.cos(ph), r * Math.sin(ph) * Math.sin(th)); };
  const arcs = [], nodes = [];
  if (S.p.cables) {
    const C = [[[-74, 40], [-5, 50]], [[-80, 26], [-9, 38]], [[-43, -23], [-9, 38]], [[18, -34], [-9, 38]], [[-122, 37], [140, 35]], [[-118, 34], [151, -34]], [[103, 1], [72, 19]], [[32, 30], [12, 44]], [[103, 1], [151, -34]], [[121, 25], [103, 1]], [[-157, 21], [174, -37]], [[72, 19], [55, 25]], [[-5, 36], [32, 31]]];
    for (const [a, b] of C) {
      const pa = ll(...a, 1.002), pb = ll(...b, 1.002), mid = pa.clone().add(pb).normalize().multiplyScalar(1.0 + pa.distanceTo(pb) * 0.08);
      const curve = new THREE.QuadraticBezierCurve3(pa, mid, pb);
      const tube = mesh(new THREE.TubeGeometry(curve, 64, 0.0035, 6), new THREE.MeshBasicMaterial({ color: 0x5fd4dc, transparent: true, opacity: 0.9 }), 0, 0, 0, earth, false);
      arcs.push({ tube, curve }); for (const p of [pa, pb]) { const n = mesh(new THREE.SphereGeometry(0.012, 10, 8), E(0x5fd4dc), p.x, p.y, p.z, earth, false); nodes.push(n); }
    }
  }
  const pulses = arcs.map((a) => mesh(new THREE.SphereGeometry(0.008, 8, 6), E(0xe0ffff), 0, 0, 0, earth, false));
  const lon0 = S.p.lon0 ?? 0, lat0 = S.p.lat0 ?? 20;
  return (t) => {
    const d = S.dur;
    earth.rotation.y = -(lon0 + 90) * Math.PI / 180 + t * 0.03; cl.rotation.y = earth.rotation.y + t * 0.01;
    G.rotation.x = lat0 * Math.PI / 180 * 0.6;
    if (S.p.lights_off) { const off = sstep(S.at(/panne|Domain/i, d * 0.3), S.at(/soixante|heures/i, d * 0.85), t); mat.emissiveIntensity = 2.2 * (1 - off * 0.92); }
    if (S.p.nodes_off) { const off = sstep(S.at(/effacée|carte/i, d * 0.4), S.at(/effacée|carte/i, d * 0.4) + 2.5, t);
      nodes.forEach((n, i) => n.material.color.set(off * nodes.length > i ? 0xff3a3a : 0x5fd4dc)); mat.emissiveIntensity = 2.2 * (1 - off * 0.7); }
    arcs.forEach((a, i) => { const u = (t * 0.25 + i * 0.17) % 1; pulses[i].position.copy(a.curve.getPoint(u)); pulses[i].visible = !(S.p.nodes_off && t > S.at(/effacée|carte/i, d * 0.4) + 1); });
    const r = lerp(3.6, 2.7, sstep(0, d, t));
    const pos = V(Math.sin(t * 0.04) * 0.4, 0.2, r), tgt = V(0.25, 0, 0);
    return { pos, tgt, fov: 38 };
  };
}

// ---------- fond graphique (cartes, chiffres, graphiques, titres) ----------
export function backdrop(S) {
  const G = new THREE.Group(); scene.add(G); scene.background = new THREE.Color(0x0a0c0e);
  const n = 500, pos = [];
  for (let i = 0; i < n; i++) pos.push((rnd() - 0.5) * 16, rnd() * 8, -rnd() * 14);
  const dust = new THREE.Points(new THREE.BufferGeometry().setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)), new THREE.PointsMaterial({ color: 0x9fb0c0, size: 0.025, transparent: true, opacity: 0.5 }));
  G.add(dust);
  const grid = new THREE.GridHelper(40, 40, 0x1e2a30, 0x14191c); grid.position.y = -0.5; G.add(grid);
  return (t) => { dust.rotation.y = t * 0.01; dust.position.y = -t * 0.02;
    return { pos: V(Math.sin(t * 0.1) * 0.3, 2 + Math.sin(t * 0.13) * 0.1, 6 - t * 0.04), tgt: V(0, 1.6, -4), fov: 40 }; };
}
