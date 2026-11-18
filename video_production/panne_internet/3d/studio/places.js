// Décors avec personnages : appartement de Marc, station de métro, pharmacie, cage d'escalier, rue.
import { THREE, scene, M, E, mesh, box, canvasTex, rep, screenTex, TEX, facade, rnd, clamp, sstep, lerp, V, room, counter, shelfUnit, bokeh, camPath, handheld } from "./core.js";
import { person, child, face, blinkAt, walk, stand, sit, carry, carryPose, cry, reach, plant, local, act } from "./people.js";

export const MARC = { role: "marc", coat: 0x1d2a44, inner: 0x8a8f96, pants: 0x232a36, hair: 0x3b2a20, shoes: 0xeeeeee };

// ---------- appartement : cuisine et fenêtre sur Paris ----------
export function apartment(S, variant) {
  const K = new THREE.Group(); scene.add(K);
  const warm = variant === "day3" || variant === "radio" || variant === "cash" || variant === "neighbor";
  scene.fog = new THREE.FogExp2(0x1b2a33, 0.006);
  const wallM = new THREE.MeshStandardMaterial({ map: rep(TEX.plaster, 3, 2), roughness: 0.95 });
  const fl = mesh(new THREE.PlaneGeometry(8, 7), new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 3, 3), roughness: 0.6 }), 0, 0, -0.5, K); fl.rotation.x = -Math.PI / 2;
  const wz = -3;
  box(3.1, 2.9, 0.15, wallM, -1.45, 1.45, wz, K); box(2.3, 2.9, 0.15, wallM, 2.85, 1.45, wz, K);
  box(1.6, 0.4, 0.15, wallM, 0.9, 2.7, wz, K); box(1.6, 0.25, 0.15, wallM, 0.9, 0.125, wz, K);
  const frameM = M(0xe8e4dc, 0.5);
  for (const x of [0.12, 0.9, 1.68]) box(0.06, 2.25, 0.1, frameM, x, 1.375, wz, K);
  for (const y of [0.28, 1.0, 1.75, 2.47]) box(1.6, 0.05, 0.1, frameM, 0.9, y, wz, K);
  box(1.7, 0.06, 0.08, M(0x1b1d20, 0.4, 0.6), 0.9, 1.05, wz + 0.28, K);
  for (let i = 0; i < 14; i++) box(0.015, 0.75, 0.015, M(0x1b1d20, 0.4, 0.6), 0.12 + i * 0.12, 0.68, wz + 0.28, K);
  mesh(new THREE.PlaneGeometry(1.56, 2.2), new THREE.MeshStandardMaterial({ color: 0x9fc7d6, transparent: true, opacity: 0.07, roughness: 0.05 }), 0.9, 1.37, wz + 0.01, K, false);
  box(0.15, 2.9, 7, wallM, -3.0, 1.45, -0.5, K); box(0.15, 2.9, 7, wallM, 4.0, 1.45, -0.5, K);
  box(8, 0.1, 7, M(0xd9d2c6, 1), 0.5, 2.92, -0.5, K, false);
  // îlot et objets
  box(1.9, 0.86, 0.85, M(0x2f4a4c, 0.7), -0.5, 0.43, -0.9, K);
  box(2.0, 0.06, 0.95, new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 1, 1), roughness: 0.45 }), -0.5, 0.89, -0.9, K);
  mesh(new THREE.SphereGeometry(0.09, 24, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), M(0xf2efe8, 0.3), -0.25, 1.0, -0.75, K);
  mesh(new THREE.CircleGeometry(0.085, 24), M(0xf7f3e8, 0.2), -0.25, 0.975, -0.75, K).rotation.x = -Math.PI / 2;
  for (const [x, c] of [[-1.15, 0xd7c9a8], [-0.95, 0x4f7f82]]) mesh(new THREE.CylinderGeometry(0.045, 0.04, 0.1, 18), M(c, 0.4), x, 0.97, -0.7, K);
  mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.2, 18), M(0x2a1a10, 0.2, 0.3), -1.35, 1.02, -1.05, K);
  // suspension
  mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.75, 6), M(0x111111), -0.5, 2.5, -0.9, K, false);
  mesh(new THREE.ConeGeometry(0.17, 0.2, 28, 1, true), new THREE.MeshStandardMaterial({ color: 0xb8733b, roughness: 0.3, metalness: 0.9, side: THREE.DoubleSide }), -0.5, 2.05, -0.9, K, false);
  mesh(new THREE.SphereGeometry(0.045, 14, 10), E(0xfff0c8), -0.5, 1.96, -0.9, K, false);
  const pend = new THREE.SpotLight(0xffb469, warm ? 14 : 22, 7, 0.95, 0.6, 1.6); pend.position.set(-0.5, 1.98, -0.9);
  pend.target.position.set(-0.4, 0, -0.6); pend.castShadow = true; pend.shadow.mapSize.set(1024, 1024); pend.shadow.bias = -0.0004; K.add(pend, pend.target);
  const fill = new THREE.PointLight(0xffa860, 2.2, 6, 2); fill.position.set(2.5, 2.2, 1.2); K.add(fill);
  const dawn = new THREE.DirectionalLight(warm ? 0xffc489 : 0x7fb3d6, warm ? 2.6 : 1.6); dawn.position.set(1.2, warm ? 4 : 3, -9); K.add(dawn);
  if (warm) { dawn.castShadow = true; dawn.shadow.mapSize.set(1024, 1024); dawn.shadow.camera.left = -4; dawn.shadow.camera.right = 4; dawn.shadow.camera.top = 4; dawn.shadow.camera.bottom = -4; }
  K.add(new THREE.HemisphereLight(warm ? 0xbfae98 : 0x8fa9bb, 0x3a2416, warm ? 0.9 : 0.75));
  const keyK = new THREE.SpotLight(0xffc996, 16, 9, 0.5, 0.8, 1.2); keyK.position.set(1.8, 2.4, 1.6); keyK.target.position.set(-0.55, 1.6, -1.55); K.add(keyK, keyK.target);
  { const l = new THREE.DirectionalLight(0x9fb7d0, 0.9); l.position.set(0, 12, 30); K.add(l); }
  box(0.7, 1.8, 0.65, M(0xe8e2d4, 0.35), 3.4, 0.9, -2.5, K);
  box(1.4, 0.04, 0.25, new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 1, 1), roughness: 0.5 }), -2.2, 1.7, -2.8, K);
  for (let i = 0; i < 5; i++) mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.14, 14), M([0x6a8f8a, 0xd8cfbf, 0xb8733b, 0x37545a, 0xe3d8c4][i], 0.5), -2.75 + i * 0.27, 1.79, -2.8, K);
  // horloge murale
  const clockG = new THREE.Group(); clockG.position.set(-2.9, 1.95, -1.4); clockG.rotation.y = Math.PI / 2; K.add(clockG);
  mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.04, 40), M(0x1c1f22, 0.4, 0.5), 0, 0, 0, clockG).rotation.x = Math.PI / 2;
  mesh(new THREE.CircleGeometry(0.18, 40), M(0xf1ece2, 0.6), 0, 0, 0.022, clockG, false);
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; box(i % 3 ? 0.008 : 0.014, i % 3 ? 0.025 : 0.04, 0.005, M(0x1c1f22), Math.sin(a) * 0.15, Math.cos(a) * 0.15, 0.025, clockG, false).rotation.z = -a; }
  const hand = (len, wdt, col) => { const p = new THREE.Group(); p.position.z = 0.03; clockG.add(p); box(wdt, len, 0.006, M(col, 0.5), 0, len / 2 - 0.02, 0, p, false); return p; };
  const hH = hand(0.09, 0.012, 0x1c1f22), hM = hand(0.14, 0.008, 0x1c1f22), hS = hand(0.15, 0.003, 0xd2672a);
  // Paris par la fenêtre
  const sky = canvasTex(2048, 1024, (g, w, h) => {
    const gr = g.createLinearGradient(0, 0, 0, h);
    if (warm) { gr.addColorStop(0, "#3f6f9a"); gr.addColorStop(0.5, "#86a9c2"); gr.addColorStop(0.8, "#e8c08e"); gr.addColorStop(1, "#f3cf9a"); }
    else { gr.addColorStop(0, "#0b1a2e"); gr.addColorStop(0.45, "#1f4560"); gr.addColorStop(0.72, "#5a8197"); gr.addColorStop(0.86, "#d99a68"); gr.addColorStop(1, "#f0b27a"); }
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
    const cx = w * 0.62, base = h * 0.93, top = h * 0.55; g.fillStyle = warm ? "#6a6e76" : "#1a2433";
    g.beginPath(); g.moveTo(cx - 70, base); g.quadraticCurveTo(cx - 20, h * 0.75, cx - 3, top); g.lineTo(cx + 3, top);
    g.quadraticCurveTo(cx + 20, h * 0.75, cx + 70, base); g.lineTo(cx + 40, base); g.quadraticCurveTo(cx, h * 0.84, cx - 40, base); g.fill();
    g.fillRect(cx - 1.5, top - 40, 3, 40); g.fillRect(cx - 34, h * 0.8, 68, 5); g.fillRect(cx - 18, h * 0.7, 36, 4);
  });
  mesh(new THREE.PlaneGeometry(260, 130), new THREE.MeshBasicMaterial({ map: sky, fog: false }), 0, 20, -140, K, false);
  const facs = [facade(warm ? 0.05 : 0.35), facade(warm ? 0.08 : 0.5), facade(warm ? 0.03 : 0.25)];
  const zinc = M(0x55636f, 0.45, 0.5);
  for (let i = 0; i < 60; i++) {
    const x = -60 + rnd() * 120, z = -10 - rnd() * 80, w = 6 + rnd() * 10, h = 10 + rnd() * 8, d = 8 + rnd() * 6;
    if (Math.abs(x - 0.9) < 3 && z > -14) continue;
    const tx = rep(facs[i % 3], Math.round(w / 4), Math.round(h / 4));
    mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshStandardMaterial({ map: tx, emissive: 0xffffff, emissiveMap: tx, emissiveIntensity: warm ? 0.05 : 0.35, roughness: 0.9 }), x, -14 + h / 2, z, K, false);
    const roof = mesh(new THREE.CylinderGeometry(w * 0.36, w * 0.52, 2.6, 4, 1), zinc, x, -14 + h + 1.3, z, K, false); roof.rotation.y = Math.PI / 4; roof.scale.z = d / w;
    for (let c = 0; c < 2; c++) { const cx = x - w / 3 + rnd() * w * 0.66;
      box(0.8, 1.6, 0.5, M(0xb49a7c, 0.9), cx, -14 + h + 2.6, z, K, false);
      for (let p = 0; p < 3; p++) mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.4, 8), M(0xb4532a, 0.8), cx - 0.25 + p * 0.25, -14 + h + 3.6, z, K, false); }
  }
  { const l = new THREE.DirectionalLight(0xf0a46a, 1.4); l.position.set(30, 10, -100); K.add(l); }
  // radio FM (posée sur l'îlot)
  const radio = new THREE.Group(); radio.position.set(-1.05, 0.92, -0.62); radio.rotation.y = 0.35; K.add(radio);
  box(0.34, 0.2, 0.12, M(0x7a2e22, 0.5), 0, 0.1, 0, radio);
  const dial = screenTex(256, 64);
  dial.draw((g, w, h) => { g.fillStyle = "#f3c98a"; g.fillRect(0, 0, w, h); g.strokeStyle = "#5a3a1a"; g.lineWidth = 2;
    for (let i = 0; i < 40; i++) { g.beginPath(); g.moveTo(10 + i * 6, h * 0.25); g.lineTo(10 + i * 6, h * (i % 5 ? 0.45 : 0.6)); g.stroke(); }
    g.fillStyle = "#c0392b"; g.fillRect(150, 6, 3, h - 12); });
  mesh(new THREE.PlaneGeometry(0.2, 0.05), new THREE.MeshBasicMaterial({ map: dial.t }), 0.04, 0.15, 0.062, radio, false);
  const grill = canvasTex(128, 128, (g, w, h) => { g.fillStyle = "#2a1a14"; g.fillRect(0, 0, w, h); g.fillStyle = "#8a5a3a"; for (let y = 6; y < h; y += 10) for (let x = 6; x < w; x += 10) { g.beginPath(); g.arc(x, y, 2.5, 0, 7); g.fill(); } });
  mesh(new THREE.CircleGeometry(0.055, 24), new THREE.MeshStandardMaterial({ map: grill, roughness: 0.8 }), -0.09, 0.09, 0.062, radio, false);
  for (const x of [0.02, 0.1]) mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.02, 14), M(0xd9c7a0, 0.3, 0.6), x, 0.07, 0.07, radio).rotation.x = Math.PI / 2;
  const ant = mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.4, 6), M(0xcccccc, 0.2, 0.9), 0.13, 0.38, -0.02, radio, false); ant.rotation.z = -0.4;
  const radioLight = new THREE.PointLight(0xffb070, 0, 1.2, 2); radioLight.position.set(-1.0, 1.1, -0.5); K.add(radioLight);
  radio.visible = variant !== "morning";
  // personnages
  const marc = person({ ...MARC });
  const kid = child();
  let doc = null;
  const chair = new THREE.Group(); chair.position.set(0.95, 0, -0.55); chair.rotation.y = -0.9; K.add(chair);
  for (const [x, z] of [[-.18, -.18], [.18, -.18], [-.18, .18], [.18, .18]]) { const l = mesh(new THREE.CylinderGeometry(0.018, 0.022, 0.78, 8), M(0xd8c3a0, 0.6), x * 1.2, 0.39, z * 1.2, chair); l.rotation.set(z * 0.3, 0, -x * 0.3); }
  box(0.36, 0.05, 0.36, M(0xd8c3a0, 0.6), 0, 0.78, 0, chair); box(0.36, 0.4, 0.04, M(0xd8c3a0, 0.6), 0, 1.0, -0.17, chair); box(0.42, 0.04, 0.2, M(0xf2efe8, 0.4), 0, 1.0, 0.26, chair);
  const carton = new THREE.Group(); marc.P.armR.hand.add(carton); carton.position.set(0, -0.06, 0.04);
  box(0.07, 0.19, 0.07, M(0xf4f4f0, 0.5), 0, 0, 0, carton); box(0.072, 0.05, 0.072, M(0x3b78a8, 0.5), 0, -0.04, 0, carton);
  carton.visible = variant === "morning" && marc.kind !== "mx";
  if (variant === "morning") { K.add(marc.g); marc.g.position.set(-0.55, 0, -1.55); chair.add(kid.g); kid.g.position.set(0, kid.mx ? 0.5 : 0.8, kid.mx ? 0.06 : 0); }
  if (variant === "day3" || variant === "radio") {
    // Marc debout près de la fenêtre, son fils dans les bras, la radio allumée sur l'îlot
    K.add(marc.g); marc.g.position.set(0.8, 0, -0.3); marc.g.rotation.y = 0.55; carry(marc, kid); chair.visible = false;
    chair.visible = false;
  }
  if (variant === "neighbor") {
    doc = person({ coat: 0x5b4b3a, inner: 0xd8d2c4, pants: 0x3a3a3a, hair: 0xb9b5ad, shoes: 0x3a2a20, glasses: true, style: "shirt", iris: 0x4a6a8a });
    K.add(doc.g); doc.g.position.set(0.47, 0, -0.15); doc.g.rotation.y = 2.24;
    chair.add(kid.g); kid.g.position.set(0, kid.mx ? 0.5 : 0.8, kid.mx ? 0.06 : 0);
    K.add(marc.g); marc.g.position.set(1.45, 0, -0.12); marc.g.rotation.y = -2.24;
    const steth = new THREE.Group(); doc.P.armR.hand.add(steth);
    mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.012, 20), M(0xd0d4d8, 0.2, 0.9), 0, -0.08, 0.02, steth);
    const kit = box(0.34, 0.2, 0.18, M(0x6a2a1e, 0.6), -0.1, 0.99, -0.6, K); kit.rotation.y = 0.4;
    box(0.1, 0.02, 0.06, M(0xf2f2f2, 0.4), -0.1, 1.1, -0.6, K);
  }
  // billets et carnet (scène 63)
  let notes = null, book = null;
  if (variant === "cash") {
    const noteTex = canvasTex(256, 132, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, "#d9a75a"); gr.addColorStop(1, "#c98d3e"); g.fillStyle = gr; g.fillRect(0, 0, w, h);
      g.fillStyle = "rgba(120,70,20,.5)"; g.font = "bold 46px Inter"; g.fillText("50", 18, 56); g.fillText("50", w - 76, h - 16);
      g.strokeStyle = "rgba(255,255,255,.4)"; g.lineWidth = 2; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(w * 0.6, h * 0.45, 12 + i * 8, 0, 7); g.stroke(); } });
    notes = mesh(new THREE.PlaneGeometry(0.14, 0.072), new THREE.MeshStandardMaterial({ map: noteTex, roughness: 0.8, side: THREE.DoubleSide }), -0.3, 0.925, -0.65, K, false);
    notes.rotation.set(-Math.PI / 2, 0, 0.25);
    const page = screenTex(512, 360);
    book = { page, mesh: mesh(new THREE.PlaneGeometry(0.2, 0.14), new THREE.MeshStandardMaterial({ map: page.t, roughness: 0.9 }), -0.62, 0.925, -0.72, K, false) };
    book.mesh.rotation.set(-Math.PI / 2, 0, -0.1);
    box(0.205, 0.008, 0.145, M(0x2a3f5a, 0.7), -0.62, 0.919, -0.72, K).rotation.y = 0.1;
  }
  return (t) => {
    const sp = S.spans, d = S.dur;
    // horloge
    const base = variant === "morning" ? 7 * 3600 + 45 * 60 : 14 * 3600 - 40;
    const secs = base + t, mm = secs / 60;
    hS.rotation.z = -(secs % 60) / 60 * Math.PI * 2; hM.rotation.z = -(mm % 60) / 60 * Math.PI * 2; hH.rotation.z = -((mm / 60) % 12) / 12 * Math.PI * 2;
    radioLight.intensity = radio.visible ? 0.6 + 0.1 * Math.sin(t * 3) : 0;
    let pos, tgt, fov = 38;
    if (variant === "morning") {
      const tc = (sp[3] || sp[sp.length - 1])[0];
      [pos, tgt] = camPath(t, [[0, V(0.95, 1.55, -2.3), V(0.8, 1.2, -40)], [sp[0][1], V(0.7, 1.5, -1.9), V(1.2, 1.4, -40)],
        [sp[1][0] + 1.6, V(1.4, 1.55, 0.9), V(-0.5, 1.35, -1.3)], [tc - 0.2, V(0.6, 1.4, 0.2), V(-0.4, 1.3, -1.2)],
        [tc + 1.3, V(-1.6, 1.9, -0.4), V(-2.9, 1.92, -1.4)], [d, V(-1.95, 1.93, -0.9), V(-2.9, 1.95, -1.4)]]);
      const pour = Math.max(0, Math.sin(clamp((t - sp[2][0]) / 3.2) * Math.PI));
      marc.P.armR.sh.rotation.set(-0.9 - pour * 0.35, 0, -0.15); marc.P.armR.el.rotation.set(-0.7 + pour * 0.2, 0, 0); carton.rotation.set(0, 0, pour * 1.6);
      reach(marc, "L", local(marc, -0.22, 0.95, 0.33));
      reach(marc, "R", local(marc, 0.24, 1.08, 0.3).lerp(V(-0.2, 1.2, -0.75), pour));
      marc.P.head.rotation.set(0.25 + pour * 0.1, Math.sin(t * 0.6) * 0.08 + (t > sp[1][0] && t < sp[2][0] ? -0.5 : 0), 0);
      marc.g.rotation.y = 0.15 + Math.sin(t * 0.4) * 0.03;
      face(marc, { smile: 0.35, blink: blinkAt(t), worry: sstep(tc, tc + 1, t) * 0.4 });
      face(kid, { smile: 0.6 + 0.3 * Math.sin(t * 0.8), blink: blinkAt(t, 2) });
      kid.P.head.rotation.set(Math.sin(t * 1.7) * 0.08, Math.sin(t * 0.9) * 0.3, 0);
      kid.P.armL.rotation.x = -0.6 + Math.sin(t * 3.1) * 0.35; kid.P.armR.rotation.x = -0.4 + Math.sin(t * 2.3 + 1) * 0.3;
    } else if (variant === "day3" || variant === "radio") {
      const close = (sp[3] || sp[sp.length - 1])[0];
      if (variant === "day3") [pos, tgt] = camPath(t, [[0, V(2.75, 1.6, 2.05), V(0.75, 1.4, -0.35)], [close - 0.3, V(2.15, 1.62, 1.35), V(0.75, 1.5, -0.3)], [close + 2.5, V(1.75, 1.78, 0.55), V(0.72, 1.5, -0.3)], [d + 2, V(1.68, 1.78, 0.48), V(0.72, 1.52, -0.3)]]);
      else [pos, tgt] = camPath(t, [[0, V(-0.55, 1.12, 0.05), V(-1.05, 1.0, -0.62)], [d, V(-0.75, 1.08, -0.1), V(-1.05, 1.0, -0.62)]]), fov = 32;
      stand(marc, t); carryPose(marc, t);
      marc.P.head.rotation.set(0.22, -0.35 + 0.08 * Math.sin(t * 0.5), 0);
      face(marc, { smile: 0.55 + 0.25 * sstep(close, close + 1.5, t), blink: blinkAt(t) });
      face(kid, { smile: 0.4 + 0.5 * sstep(close, close + 1.5, t), blink: blinkAt(t, 3) });
      kid.P.head.rotation.set(-0.15, 0.5 + 0.1 * Math.sin(t * 0.7), 0); kid.P.armR.rotation.x = -0.9 + Math.sin(t * 1.3) * 0.15;
      dial.draw((g, w, h) => { g.fillStyle = `rgb(243,${200 + 10 * Math.sin(t * 2)},138)`; g.fillRect(0, 0, w, h); g.strokeStyle = "#5a3a1a"; g.lineWidth = 2;
        for (let i = 0; i < 40; i++) { g.beginPath(); g.moveTo(10 + i * 6, h * 0.25); g.lineTo(10 + i * 6, h * (i % 5 ? 0.45 : 0.6)); g.stroke(); }
        g.fillStyle = "#c0392b"; g.fillRect(150 + Math.sin(t * 0.3) * 4, 6, 3, h - 12); });
    } else if (variant === "neighbor") {
      const ok = (sp[1] || sp[sp.length - 1])[0];
      [pos, tgt] = camPath(t, [[0, V(2.2, 1.85, -2.1), V(0.3, 1.25, -0.3)], [ok, V(2.0, 1.8, -1.95), V(0.25, 1.35, -0.4)], [d, V(1.9, 1.78, -1.85), V(0.2, 1.42, -0.45)]]);
      marc.idle = t > ok ? "Relieved_Sigh" : "Nervously_Look_Around"; doc.idle = t < ok + 1.5 ? "Reaching_Out" : "Breathing_Idle";
      stand(doc, t, 1); stand(marc, t, 2);
      doc.P.body.rotation.x = 0.25;
      // le stéthoscope se pose sur la poitrine de l'enfant, l'autre main sur son épaule
      if (doc.kind !== "mx") reach(doc, "R", kid.g.localToWorld(V(0.02, 0.24, 0.17 + 0.01 * Math.sin(t * 0.8))));
      face(doc, { worry: 0.3 * (1 - sstep(ok, ok + 1, t)), smile: sstep(ok, ok + 1, t) * 0.5, blink: blinkAt(t, 1), look: [0, 0.3] });
      face(marc, { worry: 0.8 * (1 - sstep(ok, ok + 1.2, t)), smile: sstep(ok, ok + 1.2, t) * 0.6, blink: blinkAt(t, 4) });
      marc.P.armL.sh.rotation.set(-0.2, 0, 0.1); marc.P.armR.sh.rotation.set(-0.9, 0, -0.5); marc.P.armR.el.rotation.set(-1.4, 0, 0);
      face(kid, { worry: 0.5 * (1 - sstep(ok, ok + 1, t)), smile: sstep(ok, ok + 1.5, t) * 0.7, blink: 0.4 * (1 - sstep(ok, ok + 1, t)) + blinkAt(t, 5) });
      kid.P.head.rotation.set(0, 0.6, 0);
    } else if (variant === "cash") {
      [pos, tgt] = camPath(t, [[0, V(-0.2, 1.55, -0.2), V(-0.45, 0.92, -0.7)], [d, V(-0.55, 1.45, -0.25), V(-0.5, 0.92, -0.7)]]); fov = 34;
      const k2 = sstep((sp[1] || [d * 0.5])[0], (sp[1] || [d * 0.5])[0] + 2.5, t);
      book.page.draw((g, w, h) => { g.fillStyle = "#f7f2e6"; g.fillRect(0, 0, w, h); g.strokeStyle = "rgba(80,120,170,.35)"; g.lineWidth = 2;
        for (let y = 50; y < h; y += 42) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
        g.fillStyle = "#1c2a5a"; g.font = "italic 30px 'Kalam', 'Segoe Print', cursive";
        const lines = ["Maman  06 12 .. .. ..", "Crèche  01 43 .. .. ..", "Voisin (Dr)  3e gauche", "Mairie  01 .. .. .. .."];
        lines.forEach((l, i) => { const n = Math.floor(clamp(k2 * 4 - i) * l.length); g.fillText(l.slice(0, n), 26, 84 + i * 42); }); });
      marc.g.visible = false; kid.g.visible = false;
    }
    if (variant !== "morning") marc.P.body.position.y = 0;
    return { pos: pos.add(handheld(t, variant === "day3" ? 0.4 : 1)), tgt, fov };
  };
}

// ---------- station de métro ----------
export function metro(S, variant) {
  const G = new THREE.Group(); scene.add(G);
  scene.fog = new THREE.FogExp2(0x18201f, 0.035);
  const tileM = new THREE.MeshStandardMaterial({ map: TEX.tiles, roughness: 0.18, metalness: 0.05, bumpMap: TEX.tiles, bumpScale: 0.6 });
  const HR = 3.4, HY = 1.1, HL = 46;
  const geo = new THREE.BufferGeometry(), pos = [], nor = [], uv = [], idx = [], NU = 48, NV = 2;
  for (let i = 0; i <= NU; i++) for (let j = 0; j <= NV; j++) { const th = Math.PI * i / NU, z = -HL / 2 + HL * j / NV;
    pos.push(HR * Math.cos(th), HY + HR * Math.sin(th), z); nor.push(-Math.cos(th), -Math.sin(th), 0); uv.push(i / NU * Math.PI * HR / 0.6, j / NV * HL / 0.6); }
  for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) { const a = i * (NV + 1) + j, b = a + NV + 1; idx.push(a, a + 1, b, b, a + 1, b + 1); }
  geo.setIndex(idx); geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3)); geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  const vm = tileM.clone(); vm.side = THREE.DoubleSide; mesh(geo, vm, 0, 0, -8, G, false);
  for (const s of [-1, 1]) { const wm = tileM.clone(); wm.map = rep(TEX.tiles, HL / 0.6, HY / 0.6); wm.bumpMap = wm.map;
    const w = mesh(new THREE.PlaneGeometry(HL, HY), wm, s * HR, HY / 2, -8, G, false); w.rotation.y = -s * Math.PI / 2; }
  const fl = mesh(new THREE.PlaneGeometry(2 * HR, HL), new THREE.MeshStandardMaterial({ map: rep(TEX.granite, 6, 40), roughness: 0.35, metalness: 0.1 }), 0, 0, -8, G); fl.rotation.x = -Math.PI / 2;
  for (const x of [-1.2, 1.2]) box(0.12, 0.06, HL - 2, E(0xf2fbff), x, HY + Math.sqrt(HR * HR - x * x) - 0.08, -8, G, false);
  for (let z = 8; z >= -26; z -= 5.5) { const l = new THREE.PointLight(0xd8f0ff, 7, 9, 1.6); l.position.set(0, HY + HR - 0.5, z); G.add(l); }
  G.add(new THREE.HemisphereLight(0x9fb8c4, 0x2a2e30, 0.45));
  for (let i = 0; i < 4; i++) { const z = 4 - i * 6.5;
    box(0.06, 1.25, 2.1, M(0x1e2a2c, 0.5, 0.6), -HR + 0.08, 1.55, z, G, false);
    const pm = canvasTex(256, 160, (g, w, h) => { const cols = [["#0f4c5c", "#e36414"], ["#1b263b", "#e9c46a"], ["#3d405b", "#81b29a"], ["#264653", "#e76f51"]][i];
      g.fillStyle = cols[0]; g.fillRect(0, 0, w, h); g.fillStyle = cols[1]; g.beginPath(); g.arc(w * (0.3 + 0.4 * (i % 2)), h * 0.5, h * 0.38, 0, Math.PI * 2); g.fill();
      g.fillStyle = "rgba(255,255,255,.85)"; g.fillRect(w * 0.08, h * 0.78, w * 0.4, 8); g.fillRect(w * 0.08, h * 0.86, w * 0.25, 6); });
    const p = mesh(new THREE.PlaneGeometry(2.0, 1.15), new THREE.MeshStandardMaterial({ map: pm, emissive: 0xffffff, emissiveMap: pm, emissiveIntensity: 0.25, roughness: 0.4 }), -HR + 0.12, 1.55, z, G, false); p.rotation.y = Math.PI / 2; }
  for (let i = 0; i < 4; i++) { const x = -2.1 + i * 1.4;
    box(0.28, 1.0, 1.1, M(0x9aa4a8, 0.3, 0.8), x, 0.5, -9, G);
    box(0.3, 0.7, 0.03, new THREE.MeshStandardMaterial({ color: 0xbfe4ff, transparent: true, opacity: 0.25, roughness: 0.1 }), x + 0.3, 0.85, -9, G, false); }
  // automate
  const MX = HR - 0.33;
  const mach = new THREE.Group(); mach.position.set(MX, 0, 0.6); mach.rotation.y = -Math.PI / 2; G.add(mach);
  box(0.82, 1.78, 0.5, M(0x26363a, 0.45, 0.6), 0, 0.89, 0, mach); box(0.86, 0.1, 0.54, M(0x3fae9c, 0.4, 0.4), 0, 1.83, 0, mach);
  box(0.6, 0.46, 0.04, M(0x0d1416, 0.3), 0, 1.36, 0.26, mach);
  const scr = screenTex(512, 384);
  const drawScreen = (state, t) => scr.draw((g, w, h) => {
    const bad = state === "bad", coins = state === "coins";
    g.fillStyle = bad ? "#b3121f" : coins ? "#5a4a0a" : "#0f2f4a"; g.fillRect(0, 0, w, h);
    g.fillStyle = "rgba(255,255,255,.12)"; g.fillRect(0, 0, w, 54);
    if (bad) { const bl = 0.75 + 0.25 * Math.sign(Math.sin(t * 9)); g.globalAlpha = bl; g.strokeStyle = "#fff"; g.lineWidth = 18; g.beginPath(); g.arc(w / 2, h * 0.48, 92, 0, Math.PI * 2); g.stroke();
      g.beginPath(); g.moveTo(w / 2 - 48, h * 0.48 - 48); g.lineTo(w / 2 + 48, h * 0.48 + 48); g.moveTo(w / 2 + 48, h * 0.48 - 48); g.lineTo(w / 2 - 48, h * 0.48 + 48); g.stroke(); g.globalAlpha = 1;
      g.fillStyle = "#fff"; g.font = "bold 34px Inter"; g.textAlign = "center"; g.fillText("CARTE REFUSÉE", w / 2, h * 0.88); }
    else if (coins) { for (let k = 0; k < 3; k++) { g.fillStyle = "#f2c94c"; g.beginPath(); g.arc(w / 2 - 90 + k * 90, h * 0.45, 40, 0, 7); g.fill(); g.strokeStyle = "#a07a10"; g.lineWidth = 6; g.stroke(); }
      g.fillStyle = "#fff"; g.font = "bold 34px Inter"; g.textAlign = "center"; g.fillText("PIÈCES UNIQUEMENT", w / 2, h * 0.86); }
    else { g.fillStyle = "#e9f2f7"; g.beginPath(); g.roundRect(w / 2 - 95, h * 0.3, 150, 100, 14); g.fill(); g.fillStyle = "#3a6f96"; g.fillRect(w / 2 - 95, h * 0.3 + 22, 150, 18);
      g.strokeStyle = "#e9f2f7"; g.lineWidth = 9; for (let k = 0; k < 3; k++) { g.beginPath(); g.arc(w / 2 + 70, h * 0.45, 30 + k * 26, -0.7, 0.7); g.stroke(); } }
  });
  mesh(new THREE.PlaneGeometry(0.56, 0.42), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 1.36, 0.285, mach, false);
  box(0.16, 0.12, 0.08, M(0x161b1d, 0.3, 0.5), 0.2, 1.03, 0.28, mach);
  const led = mesh(new THREE.CircleGeometry(0.03, 20), E(0x41d18b), 0.2, 1.03, 0.322, mach, false);
  for (let r = 0; r < 4; r++) for (let c = 0; c < 3; c++) box(0.045, 0.035, 0.02, M(0xc9d1d4, 0.3, 0.7), -0.22 + c * 0.06, 1.08 - r * 0.05, 0.26, mach);
  box(0.3, 0.12, 0.08, M(0x0d1112, 0.4), 0, 0.55, 0.26, mach);
  const screenLight = new THREE.PointLight(0x7fc4ff, 3, 3.5, 2); screenLight.position.set(MX - 0.55, 1.4, 0.6); G.add(screenLight);
  const key = new THREE.SpotLight(0xe8f6ff, 30, 12, 0.6, 0.7, 1.5); key.position.set(-0.5, HY + HR - 0.3, 2.5); key.target.position.set(MX - 0.4, 1.0, 0.4);
  key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004; G.add(key, key.target);
  // personnages
  const marc = variant !== "coins" ? person({ ...MARC, bag: true }) : null;
  const card = marc ? mesh(new THREE.BoxGeometry(0.085, 0.004, 0.054), M(0x2d6fb7, 0.3, 0.3), 0, -0.05, 0.03, marc.P.armR.hand) : null;
  let kid = null;
  if (variant === "stuck") { kid = child(); carry(marc, kid); }
  const crowd = [];
  for (let i = 0; i < (variant === "coins" ? 9 : 6); i++) {
    const p = person({ coat: [0x3a3330, 0x2b3a45, 0x4a3b2a, 0x262626, 0x51463d, 0x34424a, 0x5a2e2e, 0x2e4a3a, 0x3d3d52][i], inner: 0x6b6b6b, pants: 0x1f2328,
      hair: [0x1a1410, 0x5a4030, 0x2a2420, 0x8a7a6a, 0x151515, 0x40301f, 0x6a3a1a, 0x222222, 0x9a8a70][i], shoes: 0x202020, bag: i % 2 == 0, long: i % 3 == 1 });
    crowd.push({ p, x: [-1.4, 0.0, 1.4][i % 3] + (rnd() - 0.5) * 0.15, z0: -20 + rnd() * 6 + (i % 2) * 14, dir: i % 2 ? -1 : 1, sp: 1.1 + rnd() * 0.3, ph: rnd() * 6 });
  }
  const ev = S.events || {};
  return (t) => {
    const d = S.dur, sp = S.spans, err = ev.err ?? 0.8;
    let P0, T0;
    if (marc) {
      const arrive = variant === "refuse" ? 1.6 : 0;
      const u = sstep(-0.3, arrive, t);
      marc.g.position.set(lerp(-0.6, MX - 0.62, variant === "refuse" ? u : 1), 0, lerp(4.2, 0.62, variant === "refuse" ? u : 1));
      marc.g.rotation.y = variant === "refuse" ? lerp(Math.PI * 0.85, Math.PI / 2, sstep(arrive - 0.8, arrive + 0.2, t)) : Math.PI / 2 - 0.35 * sstep(err + 1, err + 2, t) * Math.sin(t * 0.8);
      if (variant === "refuse" && t < arrive) walk(marc, t * 7.5); else stand(marc, t);
      const tap = (a) => sstep(a - 0.35, a, t) * (1 - sstep(a + 0.7, a + 1.1, t));
      const k = Math.max(tap(err), ev.tap2 ? tap(ev.tap2) : 0);
      const readerW = mach.localToWorld(V(0.2, 1.03, 0.36));
      if (kid) carryPose(marc, t);
      if (k > 0.01) reach(marc, "R", local(marc, 0.24, kid ? 1.1 : 0.95, 0.22).lerp(readerW, k));
      if (marc.kind === "mx" && !kid && t > err - 1.2 && t < err + 1.6) act(marc, "Reaching_Out", t - err + 1.0);
      else if (!kid) { marc.P.armR.sh.rotation.set(-0.25, 0, -0.12); marc.P.armR.el.rotation.set(-0.5, 0, 0); }
      card.rotation.set(Math.PI / 2 * k, 0, 0);
      const look = sstep(err + 0.3, err + 1.0, t);
      marc.P.head.rotation.set(0.12 + look * 0.2, look * -0.2 + Math.sin(t * 0.8) * 0.04, 0);
      face(marc, { worry: look * 0.9, blink: blinkAt(t) });
      if (kid) cry(kid, t, sstep((sp[2] || [err])[0] - 0.5, (sp[2] || [err])[0], t) * 0.3 + 0.7);
    }
    const refused = variant === "coins" ? false : t > err + 0.15;
    drawScreen(variant === "coins" ? (t > err ? "coins" : "ok") : refused ? "bad" : "ok", t);
    const blink = refused ? (0.75 + 0.25 * Math.sign(Math.sin((t - err) * 9))) : 1;
    screenLight.color.set(refused ? 0xff2a2a : variant === "coins" && t > err ? 0xffc040 : 0x7fc4ff); screenLight.intensity = refused ? 6 * blink : 3;
    led.material.color.set(refused ? 0xff3030 : 0x41d18b);
    for (const c of crowd) { const z = c.z0 + c.dir * c.sp * (t + 6); c.p.g.position.set(c.x, 0, ((z + 24) % 34 + 34) % 34 - 24); c.p.g.rotation.y = c.dir > 0 ? 0 : Math.PI; walk(c.p, t * 7 + c.ph); face(c.p, { blink: blinkAt(t, c.ph) }); }
    if (variant === "refuse") {
      const cut2 = sp[2][0];
      [P0, T0] = camPath(t, [[0, V(-1.8, 1.55, 5.0), V(0.6, 1.2, 0.8)], [1.9, V(-0.8, 1.6, 2.4), V(1.9, 1.3, 0.5)], [err + 0.2, V(0.9, 1.75, 1.75), V(2.75, 1.15, 0.6)],
        [err + 1.6, V(2.72, 1.84, 1.95), V(2.35, 1.74, 0.55)], [cut2 + 0.2, V(1.2, 1.7, 2.4), V(1.2, 3.6, -2.0)], [cut2 + 2.2, V(1.0, 1.55, 2.9), V(2.7, 1.3, 0.55)], [d + 1, V(0.4, 1.6, 4.2), V(1.8, 1.3, 0.3)]]);
    } else if (variant === "stuck") {
      [P0, T0] = camPath(t, [[0, V(0.4, 1.6, 3.8), V(2.4, 1.4, 0.6)], [err + 0.5, V(1.1, 1.7, 2.8), V(2.4, 1.5, 0.6)], [(sp[2] || [d * 0.6])[0] + 0.4, V(2.1, 1.65, 2.6), V(2.4, 1.45, 0.6)], [d + 1, V(2.3, 1.6, 2.35), V(2.4, 1.45, 0.62)]]);
    } else {
      [P0, T0] = camPath(t, [[0, V(-2.0, 1.4, 6.0), V(1.0, 1.2, -2.0)], [err, V(0.2, 1.5, 2.6), V(2.9, 1.3, 0.6)], [d + 1, V(1.6, 1.45, 1.6), V(3.0, 1.35, 0.6)]]);
    }
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 38, project: { screen: V(MX - 0.3, 1.4, 0.6), ceiling: V(1.2, HY + HR - 0.15, -1.0) } };
  };
}

// ---------- pharmacie de nuit ----------
export function pharmacy(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x0e1a18, 0.02);
  room(G, { w: 7, d: 6, h: 2.8, wall: M(0xdfe6e2, 0.9), floor: new THREE.MeshStandardMaterial({ map: rep(TEX.lino, 6, 6), roughness: 0.4 }), ceil: 0xeef2f0, open: ["front"] });
  for (let i = 0; i < 3; i++) shelfUnit(G, -2.2 + i * 1.5, -2.7, 1.4, 6, 0.85);
  shelfUnit(G, -3.2, 0, 1.6, 6, 0.8, Math.PI / 2);
  counter(G, 0.2, -1.2, 3.2, 0.7, 1.0, M(0x2e6a5c, 0.6), M(0xf3f3f0, 0.3));
  const mon = new THREE.Group(); mon.position.set(0.9, 1.0, -1.25); mon.rotation.y = -2.6; G.add(mon);
  box(0.42, 0.28, 0.03, M(0x111111, 0.3), 0, 0.3, 0, mon); box(0.04, 0.16, 0.04, M(0x222222), 0, 0.08, -0.02, mon);
  const scr = screenTex(256, 170); mesh(new THREE.PlaneGeometry(0.39, 0.25), new THREE.MeshBasicMaterial({ map: scr.t }), 0, 0.3, 0.017, mon, false);
  // croix verte à l'extérieur (vitrine)
  const cross = new THREE.Group(); cross.position.set(2.6, 2.1, 2.2); cross.rotation.y = -0.4; G.add(cross);
  const cm = E(0x31e07a); box(0.5, 0.16, 0.05, cm, 0, 0, 0, cross, false); box(0.16, 0.5, 0.05, cm, 0, 0, 0, cross, false);
  const crossL = new THREE.PointLight(0x31e07a, 5, 6, 2); crossL.position.set(2.3, 2.0, 1.8); G.add(crossL);
  for (let i = 0; i < 6; i++) { const l = new THREE.PointLight(0xf4fbff, 3.5, 6, 2); l.position.set(-2.5 + (i % 3) * 2.2, 2.6, -2 + Math.floor(i / 3) * 2.4); G.add(l); }
  G.add(new THREE.HemisphereLight(0xcfe3dc, 0x30302c, 0.6));
  const key = new THREE.SpotLight(0xffffff, 18, 10, 0.7, 0.6, 1.4); key.position.set(-1.5, 2.7, 2.5); key.target.position.set(0.3, 1.2, -0.5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); G.add(key, key.target);
  const ph = person({ coat: 0xf3f4f2, inner: 0x7fb0c8, pants: 0x3a3f48, hair: 0x2a2020, shoes: 0x222222, style: "whitecoat", glasses: true, iris: 0x3a2a1a });
  ph.g.position.set(0.3, 0, -1.75); ph.g.rotation.y = 0.15;
  const marc = person({ ...MARC }); marc.g.position.set(0.15, 0, -0.35); marc.g.rotation.y = Math.PI - 0.1;
  const kid = child(); carry(marc, kid);
  return (t) => {
    const d = S.dur, sp = S.spans, no = (sp[2] || sp[sp.length - 1])[0];
    ph.idle = t > no ? "Shaking_Head_No" : "Breathing_Idle"; marc.idle = "Nervously_Look_Around";
    stand(ph, t, 1); stand(marc, t, 2); carryPose(marc, t);
    const shakeH = sstep(no, no + 0.4, t) * Math.sin((t - no) * 6) * (1 - sstep(no + 2, no + 2.6, t));
    ph.P.head.rotation.set(0.1, shakeH * 0.35, 0);
    ph.P.armL.sh.rotation.set(-0.6 * sstep(no, no + 0.6, t), 0, 0.5 * sstep(no, no + 0.6, t)); ph.P.armL.el.rotation.set(-0.9 * sstep(no, no + 0.6, t), 0, 0);
    ph.P.armR.sh.rotation.set(-0.6 * sstep(no, no + 0.6, t), 0, -0.5 * sstep(no, no + 0.6, t)); ph.P.armR.el.rotation.set(-0.9 * sstep(no, no + 0.6, t), 0, 0);
    face(ph, { worry: 0.5, blink: blinkAt(t, 1) });
    face(marc, { worry: 0.95, blink: blinkAt(t, 2), open: 0.2 * Math.max(0, Math.sin(t * 3)) });
    face(kid, { worry: 0.6, blink: 0.65, smile: 0 }); kid.P.head.rotation.set(0.3, -0.6, 0.3);
    scr.draw((g, w, h) => { g.fillStyle = "#1b2228"; g.fillRect(0, 0, w, h); g.fillStyle = "#e5484d"; g.font = "bold 18px Inter"; g.textAlign = "center";
      g.fillText("CONNEXION IMPOSSIBLE", w / 2, h / 2 + 30); g.strokeStyle = "#e5484d"; g.lineWidth = 6; g.beginPath(); g.arc(w / 2, h / 2 - 20, 26, 0, 7); g.stroke();
      g.beginPath(); g.moveTo(w / 2 - 14, h / 2 - 34); g.lineTo(w / 2 + 14, h / 2 - 6); g.stroke(); });
    crossL.intensity = 5 + Math.sin(t * 2.5) * 0.6;
    const [P0, T0] = camPath(t, [[0, V(2.4, 1.6, 2.2), V(0.2, 1.3, -1.0)], [no, V(1.7, 1.6, 1.0), V(0.2, 1.45, -1.2)], [d + 1, V(1.2, 1.62, 0.55), V(0.25, 1.6, -1.5)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 38 };
  };
}

// ---------- cage d'escalier : le voisin médecin ----------
export function stairwell(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x1a1612, 0.05);
  room(G, { w: 4, d: 5, h: 5.6, wall: new THREE.MeshStandardMaterial({ map: rep(TEX.plaster, 2, 3), roughness: 0.95, color: 0xe9d9bf }), floor: new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 2, 2), roughness: 0.5 }), ceil: null, open: ["front"] });
  const stepTop = (z) => { if (z > 0.34) return 0; const i = Math.min(15, Math.floor((0.34 - z) / 0.28)); return 0.18 * (i + 1); };
  for (let i = 0; i < 16; i++) { box(1.2, 0.18 * (i + 1), 0.28, new THREE.MeshStandardMaterial({ map: rep(TEX.wood, 1, 1), roughness: 0.5 }), -1.2, 0.09 * (i + 1), 0.2 - i * 0.28, G);
    mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.9, 6), M(0x1a1a1a, 0.4, 0.7), -0.6, 0.18 * (i + 1) + 0.45, 0.2 - i * 0.28, G); }
  const rail = box(0.06, 0.06, 4.6, M(0x4a2a1a, 0.4), -0.6, 0.18 * 8 + 0.92, 0.2 - 7.5 * 0.28, G); rail.rotation.x = Math.atan2(0.18, 0.28);
  const door = new THREE.Group(); door.position.set(1.95, 0, -0.8); G.add(door);
  box(0.06, 2.2, 1.0, M(0x6a3a22, 0.5), 0, 1.1, 0, door); mesh(new THREE.SphereGeometry(0.03, 12, 10), M(0xd4af37, 0.3, 0.9), -0.05, 1.0, 0.35, door);
  const lamp = new THREE.PointLight(0xffc27a, 9, 7, 1.6); lamp.position.set(0, 3.2, 0); G.add(lamp);
  mesh(new THREE.SphereGeometry(0.12, 18, 14), E(0xffe2b0), 0, 3.3, 0, G, false);
  G.add(new THREE.HemisphereLight(0xffe0b8, 0x2a1a10, 0.55));
  const key = new THREE.SpotLight(0xffd6a0, 16, 9, 0.6, 0.7, 1.4); key.position.set(1.5, 3, 2.5); key.target.position.set(0, 1.4, -0.5); key.castShadow = true; key.shadow.mapSize.set(1024, 1024); G.add(key, key.target);
  const marc = person({ ...MARC }); marc.g.position.set(0.6, 0, 0.6); marc.g.rotation.y = -2.5;
  const kid = child(); carry(marc, kid);
  const doc = person({ coat: 0x6b5a45, inner: 0xd8d2c4, pants: 0x3a3a3a, hair: 0xb9b5ad, shoes: 0x3a2a20, glasses: true, style: "shirt", bald: true, iris: 0x4a6a8a });
  return (t) => {
    const d = S.dur, sp = S.spans, meet = (sp[1] || sp[0])[0];
    // descente : de la 9e marche au palier, puis trois pas vers Marc
    const t0d = Math.max(0.2, meet - 3.6), t1d = t0d + 2.8, t2d = t1d + 1.2;
    const zd = lerp(0.2 - 9 * 0.28, 0.6, clamp((t - t0d) / (t1d - t0d)));
    let x = -1.2, z = zd, ry = 0;
    if (t > t1d) { const u2 = sstep(t1d, t2d, t); x = lerp(-1.2, -0.35, u2); z = lerp(0.6, 0.15, u2); ry = lerp(0, 0.9, u2); }
    doc.g.position.set(x, stepTop(z), z); doc.g.rotation.y = ry;
    doc.idle = t > t0d && t < t1d ? "Descending_Stairs" : t < t2d && t > t1d ? null : "Breathing_Idle";
    if (doc.kind === "mx" && t > t1d && t < t2d) walk(doc, (t - t1d) * 6); else stand(doc, t, 1);
    if (t > t0d && t < t2d) {
      const ph = (t - t0d) * 2.6, f = ph % 1, lead = Math.floor(ph) % 2;
      for (const [side, sgn] of [["L", -1], ["R", 1]]) {
        const moving = (side === "L") === (lead === 0), fz = z + (moving ? 0.14 * (f - 0.5) * 2 : -0.1), fx = x + sgn * 0.1;
        const lift = moving ? Math.sin(f * Math.PI) * 0.1 : 0;
        plant(doc, side, V(fx, stepTop(fz) + 0.06 + lift, fz));
      }
      doc.P.armL.sh.rotation.set(0.2, 0, 0.1); doc.P.armR.sh.rotation.set(-0.1, 0, -0.35);
    }
    stand(marc, t); carryPose(marc, t); marc.P.head.rotation.set(0.05, -0.4 * sstep(meet - 1, meet, t), 0);
    face(marc, { worry: 0.9 - 0.3 * sstep(meet + 0.5, meet + 1.5, t), blink: blinkAt(t) });
    face(doc, { worry: 0.3, smile: 0.2, blink: blinkAt(t, 2) });
    face(kid, { worry: 0.6, blink: 0.6 }); kid.P.head.rotation.set(0.3, -0.5, 0.3);
    lamp.intensity = 9 + Math.sin(t * 30) * 0.15;
    const [P0, T0] = camPath(t, [[0, V(1.6, 1.5, 3.0), V(0.3, 1.4, -0.2)], [meet, V(1.3, 1.65, 2.2), V(0.0, 1.5, 0.0)], [d + 1, V(0.9, 1.6, 1.8), V(-0.1, 1.55, 0.1)]]);
    return { pos: P0.add(handheld(t)), tgt: T0, fov: 38 };
  };
}

// ---------- rue haussmannienne : Marc court à l'épicerie ----------
export function street(S) {
  const G = new THREE.Group(); scene.add(G); scene.fog = new THREE.FogExp2(0x8fa3b0, 0.02);
  scene.background = new THREE.Color(0x9fb4c2);
  const road = mesh(new THREE.PlaneGeometry(14, 120), new THREE.MeshStandardMaterial({ map: rep(TEX.asphalt, 6, 50), roughness: 0.85 }), 0, 0, -40, G); road.rotation.x = -Math.PI / 2;
  for (const s of [-1, 1]) { const sw = box(3.2, 0.14, 120, M(0xb8b3aa, 0.8), s * 5.4, 0.07, -40, G); }
  for (let i = 0; i < 12; i++) for (const s of [-1, 1]) {
    const z = 4 - i * 10, h = 17 + rnd() * 3, tx = rep(facade(0.05, "#cdbb9c"), 3, 5);
    box(8, h, 9.6, new THREE.MeshStandardMaterial({ map: tx, roughness: 0.9 }), s * 11, h / 2, z, G);
    const roof = mesh(new THREE.CylinderGeometry(3.2, 4.6, 2.4, 4), M(0x55636f, 0.45, 0.5), s * 11, h + 1.2, z, G); roof.rotation.y = Math.PI / 4; roof.scale.z = 1.25;
    for (let f = 0; f < 4; f++) box(0.25, 0.08, 9.6, M(0x1b1d20, 0.4, 0.6), s * 7.1, 4.2 + f * 3.3, z, G, false);
  }
  // auvent de l'épicerie
  const aw = canvasTex(512, 128, (g, w, h) => { for (let i = 0; i < 16; i++) { g.fillStyle = i % 2 ? "#f2efe6" : "#2f6e4f"; g.fillRect(i * w / 16, 0, w / 16, h); } g.fillStyle = "#1c2a22"; g.fillRect(0, h * 0.62, w, h * 0.38);
    g.fillStyle = "#f2efe6"; g.font = "bold 44px Inter"; g.textAlign = "center"; g.fillText("ÉPICERIE", w / 2, h * 0.92); });
  const awn = mesh(new THREE.PlaneGeometry(5, 1.2), new THREE.MeshStandardMaterial({ map: aw, side: THREE.DoubleSide }), 6.95, 3.3, -26, G); awn.rotation.set(0, -Math.PI / 2, -0.35);
  const sun = new THREE.DirectionalLight(0xffe1b8, 2.4); sun.position.set(-20, 30, 10); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -12, right: 12, top: 12, bottom: -12, far: 80 }); G.add(sun, sun.target);
  G.add(new THREE.HemisphereLight(0xbcd2e2, 0x6a5e50, 0.9));
  const marc = person({ ...MARC });
  const noteTex = canvasTex(128, 66, (g, w, h) => { g.fillStyle = "#6fa0c8"; g.fillRect(0, 0, w, h); g.fillStyle = "rgba(20,50,90,.6)"; g.font = "bold 26px Inter"; g.fillText("20", 8, 28); g.fillText("20", w - 38, h - 8); });
  for (let k = 0; k < 2; k++) { const n = mesh(new THREE.PlaneGeometry(0.13, 0.068), new THREE.MeshStandardMaterial({ map: noteTex, side: THREE.DoubleSide, roughness: 0.8 }), 0.01 * k, -0.07, 0.05 + k * 0.004, marc.P.armR.hand, false); n.rotation.set(0.3, 0, 0.2 + k * 0.3); }
  const people = [];
  for (let i = 0; i < 5; i++) { const p = person({ coat: [0x5a4a3a, 0x2b3a45, 0x6a2e2e, 0x3a4a3a, 0x444444][i], hair: [0x2a2420, 0x8a7a6a, 0x151515, 0x6a3a1a, 0x444444][i], shoes: 0x222222, long: i % 2 == 1 });
    people.push({ p, x: (i % 2 ? 4.15 : -5.2) + rnd() * 0.25, z: -6 - i * 7, dir: i % 2 ? 1 : -1 }); }
  return (t) => {
    const d = S.dur, z = 2 - t * 3.6;
    marc.g.position.set(5.0, 0.14, z); marc.g.rotation.y = Math.PI; walk(marc, t * 11, 0.75);
    marc.P.armR.sh.rotation.x = -0.6 + Math.sin(t * 11) * 0.3; marc.P.armR.el.rotation.x = -1.0;
    marc.P.body.rotation.x = 0.12; face(marc, { worry: 0.6, blink: blinkAt(t), open: 0.25 });
    for (const q of people) { q.p.g.position.set(q.x, 0.14, q.z + q.dir * t * 1.2); q.p.g.rotation.y = q.dir > 0 ? 0 : Math.PI; walk(q.p, t * 6 + q.z); face(q.p, { blink: blinkAt(t, q.z) }); }
    const pos = V(3.0, 1.5, z + 2.6 + Math.sin(t * 0.5) * 0.2), tgt = V(5.0, 1.3, z - 1.5);
    return { pos: pos.add(handheld(t, 2)), tgt, fov: 40 };
  };
}
