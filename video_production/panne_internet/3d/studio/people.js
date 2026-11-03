// Personnages 3D (formes lisses, éclairage réaliste) : adulte, enfant, poses et expressions.
import { THREE, M, mesh, scene, clamp } from "./core.js";

const SKIN = 0xe2b08f;
function skinMat(c = SKIN) { return new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.55, sheen: 0.4, sheenColor: new THREE.Color(0xffd2b8) }); }

// profil de buste (Lathe) : hanches -> taille -> poitrine -> épaules
function lathe(points, mat, parent, y = 0, sz = 0.74) {
  const m = mesh(new THREE.LatheGeometry(points.map(([r, h]) => new THREE.Vector2(r, h)), 32), mat, 0, y, 0, parent);
  m.scale.z = sz; return m;
}

export function person(o = {}) {
  const {
    coat = 0x1d2a44, inner = 0x8a8f96, pants = 0x232a36, hair = 0x3b2a20, shoes = 0xeeeeee, bag = false,
    skin = SKIN, style = "coat", glasses = false, beard = false, long = false, bald = false, scale = 1, iris = 0x5a3b22,
  } = o;
  const g = new THREE.Group(), P = { o };
  const body = new THREE.Group(); g.add(body); P.body = body;
  const mTop = M(coat, style === "whitecoat" ? 0.7 : 0.85), mSkin = skinMat(skin), mPants = M(pants, 0.9);
  // jambes : cuisse, genou, tibia, chaussure
  const leg = (sx) => {
    const hip = new THREE.Group(); hip.position.set(sx * 0.095, 0.92, 0); body.add(hip);
    mesh(new THREE.CapsuleGeometry(0.078, 0.34, 6, 16), mPants, 0, -0.22, 0, hip);
    const knee = new THREE.Group(); knee.position.set(0, -0.45, 0); hip.add(knee);
    mesh(new THREE.CapsuleGeometry(0.066, 0.34, 6, 16), mPants, 0, -0.2, 0, knee);
    const sh = mesh(new THREE.CapsuleGeometry(0.055, 0.15, 6, 14), M(shoes, 0.45), 0, -0.43, 0.06, knee);
    sh.rotation.x = Math.PI / 2; sh.scale.set(1.05, 1, 0.75);
    return { hip, knee };
  };
  P.legL = leg(-1); P.legR = leg(1);
  // buste et vêtement
  lathe([[0.001, 0.84], [0.19, 0.84], [0.2, 0.95], [0.18, 1.1], [0.205, 1.32], [0.215, 1.48], [0.17, 1.6], [0.08, 1.67], [0.001, 1.68]], mTop, body);
  if (style === "coat" || style === "whitecoat") {
    const skirt = mesh(new THREE.CylinderGeometry(0.205, 0.235, 0.3, 28, 1, true), mTop, 0, 0.78, 0, body); skirt.scale.z = 0.78;
    for (const s of [-1, 1]) { const l = mesh(new THREE.BoxGeometry(0.06, 0.34, 0.02), M(coat, 0.8), s * 0.06, 1.47, 0.152, body); l.rotation.z = s * 0.35; }
    mesh(new THREE.BoxGeometry(0.1, 0.3, 0.02), M(inner, 0.95), 0, 1.47, 0.148, body);
  }
  if (style === "apron") mesh(new THREE.BoxGeometry(0.34, 0.6, 0.02), M(0x2f5d50, 0.9), 0, 1.15, 0.16, body);
  mesh(new THREE.TorusGeometry(0.085, 0.035, 10, 24), M(style === "coat" ? inner : coat, 0.95), 0, 1.66, 0, body).rotation.x = Math.PI / 2;
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(0.082, 18, 14), mTop, s * 0.19, 1.57, 0, body);
  mesh(new THREE.CylinderGeometry(0.048, 0.054, 0.12, 16), mSkin, 0, 1.71, 0, body);
  if (bag) { const b = mesh(new THREE.CapsuleGeometry(0.12, 0.16, 6, 16), M(0x2f3a2c, 0.9), 0, 1.32, -0.19, body); b.scale.set(1.15, 1, 0.55);
    for (const s of [-1, 1]) { const st = mesh(new THREE.BoxGeometry(0.03, 0.42, 0.02), M(0x22291f, 0.9), s * 0.1, 1.38, 0.0, body); st.rotation.x = 0.1; st.position.z = 0.145; } }
  // tête
  const head = new THREE.Group(); head.position.set(0, 1.83, 0); body.add(head); P.head = head;
  mesh(new THREE.SphereGeometry(0.108, 36, 26), mSkin, 0, 0.006, 0, head).scale.set(1, 1.18, 1.07);
  mesh(new THREE.SphereGeometry(0.09, 30, 22), mSkin, 0, -0.06, 0.018, head).scale.set(0.98, 0.82, 1);   // mâchoire
  if (beard) mesh(new THREE.SphereGeometry(0.093, 30, 22), new THREE.MeshStandardMaterial({ color: hair, roughness: 1, transparent: true, opacity: 0.35 }), 0, -0.064, 0.02, head).scale.set(0.99, 0.8, 1.01);
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(0.03, 14, 10), mSkin, s * 0.058, -0.03, 0.074, head).scale.set(1, 0.8, 0.7);   // pommettes
  const nose = mesh(new THREE.CapsuleGeometry(0.016, 0.03, 6, 12), mSkin, 0, -0.005, 0.104, head); nose.rotation.x = 0.35;
  mesh(new THREE.SphereGeometry(0.02, 14, 10), mSkin, 0, -0.028, 0.114, head).scale.set(1.1, 0.8, 0.9);
  P.eyes = []; P.lids = []; P.brows = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group(); eye.position.set(s * 0.04, 0.022, 0.087); head.add(eye);
    mesh(new THREE.SphereGeometry(0.019, 18, 14), M(0xf6f3ee, 0.25), 0, 0, 0, eye, false);
    mesh(new THREE.SphereGeometry(0.0105, 16, 12), M(iris, 0.3), 0, 0, 0.012, eye, false);
    mesh(new THREE.SphereGeometry(0.0058, 12, 10), M(0x0b0705, 0.1), 0, 0, 0.0185, eye, false);
    const lid = mesh(new THREE.SphereGeometry(0.0205, 18, 12, 0, Math.PI * 2, 0, Math.PI * 0.5), mSkin, 0, 0, 0, eye, false);
    lid.rotation.x = -1.25; P.lids.push(lid);
    const brow = mesh(new THREE.CapsuleGeometry(0.006, 0.036, 4, 8), M(hair, 0.9), s * 0.041, 0.058, 0.1, head, false);
    brow.rotation.z = Math.PI / 2; P.brows.push({ m: brow, s });
    P.eyes.push(eye);
    mesh(new THREE.SphereGeometry(0.025, 14, 10), mSkin, s * 0.108, 0.0, -0.005, head).scale.set(0.42, 1, 0.72);   // oreilles
  }
  // bouche : arc qui sourit ou s'inquiète
  const mouth = mesh(new THREE.TorusGeometry(0.022, 0.0045, 8, 20, Math.PI * 0.75), M(0x9a5048, 0.5), 0, -0.068, 0.097, head, false);
  mouth.rotation.z = Math.PI + Math.PI * 0.125; P.mouth = mouth;
  const mouthO = mesh(new THREE.SphereGeometry(0.014, 14, 10), M(0x3a1512, 0.6), 0, -0.07, 0.099, head, false);
  mouthO.scale.set(1.2, 0.2, 0.5); P.mouthO = mouthO;
  if (glasses) for (const s of [-1, 1]) {
    mesh(new THREE.TorusGeometry(0.022, 0.0025, 8, 24), M(0x1a1a1a, 0.3, 0.6), s * 0.04, 0.022, 0.11, head, false);
    mesh(new THREE.BoxGeometry(0.03, 0.003, 0.003), M(0x1a1a1a, 0.3, 0.6), 0, 0.026, 0.112, head, false);
  }
  const hairM = M(hair, 0.85);
  if (!bald) {
    const cap = mesh(new THREE.SphereGeometry(0.12, 30, 18, 0, Math.PI * 2, 0, Math.PI * 0.36), hairM, 0, 0.026, -0.004, head);
    cap.scale.set(1.03, 1.16, 1.1); cap.rotation.x = -0.18;
    const back = mesh(new THREE.SphereGeometry(0.121, 30, 18, Math.PI, Math.PI, 0, Math.PI * (long ? 0.85 : 0.66)), hairM, 0, 0.014, -0.008, head);
    back.scale.set(1.04, long ? 1.3 : 1.15, 1.1);
    mesh(new THREE.SphereGeometry(0.058, 16, 10), hairM, 0.022, 0.125, 0.05, head).scale.set(1.5, 0.45, 0.9);
    if (long) for (const s of [-1, 1]) mesh(new THREE.CapsuleGeometry(0.035, 0.16, 6, 12), hairM, s * 0.1, -0.07, -0.03, head);
  } else {
    mesh(new THREE.SphereGeometry(0.121, 30, 18, Math.PI, Math.PI, Math.PI * 0.35, Math.PI * 0.3), M(0xbdbab2, 0.9), 0, 0.01, -0.006, head).scale.set(1.04, 1.15, 1.1);
  }
  // bras : épaule -> coude -> main (paume, pouce, doigts)
  const arm = (sx) => {
    const sh = new THREE.Group(); sh.position.set(sx * 0.215, 1.57, 0); body.add(sh);
    mesh(new THREE.CapsuleGeometry(0.06, 0.24, 6, 16), mTop, 0, -0.16, 0, sh);
    const el = new THREE.Group(); el.position.set(0, -0.31, 0); sh.add(el);
    mesh(new THREE.CapsuleGeometry(0.052, 0.21, 6, 16), mTop, 0, -0.13, 0, el);
    const hand = new THREE.Group(); hand.position.set(0, -0.28, 0.005); el.add(hand);
    mesh(new THREE.CapsuleGeometry(0.028, 0.035, 6, 12), mSkin, 0, -0.02, 0, hand).scale.set(1.3, 1, 0.7);
    mesh(new THREE.CapsuleGeometry(0.024, 0.04, 6, 12), mSkin, 0, -0.07, 0.006, hand).scale.set(1.35, 1, 0.65);
    const th = mesh(new THREE.CapsuleGeometry(0.012, 0.03, 4, 10), mSkin, -sx * 0.03, -0.035, 0.016, hand); th.rotation.z = sx * 0.6;
    return { sh, el, hand };
  };
  P.armL = arm(-1); P.armR = arm(1);
  g.scale.setScalar(scale);
  scene.add(g);
  P.expr = { worry: 0, smile: 0, blink: 0, open: 0 };
  return { g, P, kind: "adult" };
}

// expression : inquiétude (sourcils, bouche), sourire, clignement, bouche ouverte
export function face(p, { worry = 0, smile = 0, blink = 0, open = 0, look = [0, 0] } = {}) {
  const P = p.P;
  for (const b of P.brows) { b.m.rotation.z = Math.PI / 2 + b.s * (worry * 0.35 - smile * 0.1); b.m.position.y = (p.kind === "child" ? 0.052 : 0.058) + worry * 0.005; }
  const curve = clamp(smile - worry * 0.8, -1, 1);
  P.mouth.rotation.z = curve >= 0 ? Math.PI + Math.PI * 0.125 : Math.PI * 0.125;
  P.mouth.position.y = (p.kind === "child" ? -0.055 : -0.068) + (curve < 0 ? -0.01 : 0);
  P.mouth.scale.set(1, 0.35 + Math.abs(curve) * 0.65, 1);
  P.mouthO.scale.set(1.2, 0.2 + open * 1.6, 0.5);
  for (const l of P.lids) l.rotation.x = -1.25 + blink * 1.1 + worry * 0.12;
  for (const e of P.eyes) { e.rotation.y = look[0]; e.rotation.x = look[1]; }
}
// clignement naturel toutes les ~3,5 s
export const blinkAt = (t, seed = 0) => { const k = (t + seed * 1.3) % 3.6; return k < 0.12 ? Math.sin(k / 0.12 * Math.PI) : 0; };

export function walk(p, phase, amp = 0.42) {
  const s = Math.sin(phase), P = p.P;
  P.legL.hip.rotation.x = s * amp; P.legR.hip.rotation.x = -s * amp;
  P.legL.knee.rotation.x = Math.max(0, -s) * amp * 1.3; P.legR.knee.rotation.x = Math.max(0, s) * amp * 1.3;
  P.armL.sh.rotation.set(-s * amp * 0.7, 0, 0.06); P.armR.sh.rotation.set(s * amp * 0.7, 0, -0.06);
  P.armL.el.rotation.x = -0.3; P.armR.el.rotation.x = -0.3;
  P.body.position.y = Math.abs(Math.cos(phase)) * 0.022;
}
export function stand(p, t = 0, seed = 0) {
  const P = p.P;
  for (const L of [P.legL, P.legR]) { L.hip.rotation.x = 0; L.knee.rotation.x = 0; }
  P.armL.sh.rotation.set(0.03, 0, 0.07); P.armR.sh.rotation.set(0.03, 0, -0.07);
  P.armL.el.rotation.x = -0.15; P.armR.el.rotation.x = -0.15;
  P.body.position.y = Math.sin(t * 1.6 + seed) * 0.004;         // respiration
  P.body.scale.set(1, 1 + Math.sin(t * 1.6 + seed) * 0.004, 1);
}
export function sit(p) {
  const P = p.P;
  for (const L of [P.legL, P.legR]) { L.hip.rotation.x = -1.45; L.knee.rotation.x = 1.45; }
  P.body.position.y = -0.45;
}

export function child(o = {}) {
  const { suit = 0xe9b12c, hat = 0xd2672a } = o;
  const g = new THREE.Group(), P = {};
  const mSuit = M(suit, 0.75), mSkin = skinMat(0xf0c3a4);
  const torso = mesh(new THREE.CapsuleGeometry(0.13, 0.16, 8, 18), mSuit, 0, 0.18, 0, g); torso.scale.set(1, 1, 0.9);
  for (const s of [-1, 1]) {
    const a = new THREE.Group(); a.position.set(s * 0.14, 0.3, 0); g.add(a); P[s < 0 ? "armL" : "armR"] = a;
    mesh(new THREE.CapsuleGeometry(0.05, 0.13, 6, 12), mSuit, 0, -0.08, 0.02, a);
    mesh(new THREE.SphereGeometry(0.035, 12, 10), mSkin, 0, -0.19, 0.03, a);
    const leg = new THREE.Group(); leg.position.set(s * 0.07, 0.02, 0.02); g.add(leg); P[s < 0 ? "legL" : "legR"] = leg;
    mesh(new THREE.CapsuleGeometry(0.055, 0.14, 6, 12), mSuit, 0, -0.1, 0, leg);
    mesh(new THREE.SphereGeometry(0.05, 12, 10), M(0xd9a024, 0.7), 0, -0.21, 0.02, leg).scale.set(1, 0.8, 1.3);
  }
  const head = new THREE.Group(); head.position.set(0, 0.47, 0); g.add(head); P.head = head;
  mesh(new THREE.SphereGeometry(0.112, 32, 24), mSkin, 0, 0, 0, head).scale.set(1, 1, 0.98);
  for (const s of [-1, 1]) mesh(new THREE.SphereGeometry(0.034, 14, 10), skinMat(0xf2a78f), s * 0.058, -0.035, 0.075, head);
  P.eyes = []; P.lids = []; P.brows = [];
  for (const s of [-1, 1]) {
    const eye = new THREE.Group(); eye.position.set(s * 0.04, 0.008, 0.094); head.add(eye);
    mesh(new THREE.SphereGeometry(0.021, 16, 12), M(0xf6f3ee, 0.25), 0, 0, 0, eye, false);
    mesh(new THREE.SphereGeometry(0.013, 14, 10), M(0x3a2618, 0.2), 0, 0, 0.012, eye, false);
    mesh(new THREE.SphereGeometry(0.006, 10, 8), M(0x050505, 0.1), 0, 0, 0.0205, eye, false);
    const lid = mesh(new THREE.SphereGeometry(0.0225, 16, 10, 0, Math.PI * 2, 0, Math.PI * 0.5), mSkin, 0, 0, 0, eye, false);
    lid.rotation.x = -1.25; P.lids.push(lid); P.eyes.push(eye);
    const brow = mesh(new THREE.CapsuleGeometry(0.004, 0.026, 4, 8), M(0x9a7350, 0.9), s * 0.042, 0.052, 0.098, head, false);
    brow.rotation.z = Math.PI / 2; P.brows.push({ m: brow, s });
  }
  mesh(new THREE.SphereGeometry(0.016, 12, 8), mSkin, 0, -0.02, 0.11, head);
  const mouth = mesh(new THREE.TorusGeometry(0.018, 0.0042, 8, 20, Math.PI * 0.75), M(0xb5605a, 0.5), 0, -0.055, 0.1, head, false);
  mouth.rotation.z = Math.PI + Math.PI * 0.125; P.mouth = mouth;
  const mouthO = mesh(new THREE.SphereGeometry(0.014, 14, 10), M(0x4a1a16, 0.6), 0, -0.058, 0.1, head, false); mouthO.scale.set(1.2, 0.2, 0.5); P.mouthO = mouthO;
  const beanie = mesh(new THREE.SphereGeometry(0.12, 28, 16, 0, Math.PI * 2, 0, Math.PI * 0.5), M(hat, 0.95), 0, 0.03, -0.005, head);
  beanie.rotation.x = -0.18;
  mesh(new THREE.TorusGeometry(0.113, 0.022, 10, 28), M(0xc65d24, 0.95), 0, 0.035, 0.005, head).rotation.x = Math.PI / 2 - 0.18;
  mesh(new THREE.SphereGeometry(0.035, 12, 10), M(hat, 1), 0, 0.15, -0.03, head);
  P.tears = [];
  for (const s of [-1, 1]) { const tr = mesh(new THREE.SphereGeometry(0.006, 8, 6), new THREE.MeshPhysicalMaterial({ color: 0xcfe8ff, roughness: 0, transmission: 0.5, transparent: true, opacity: 0.0 }), s * 0.045, -0.012, 0.106, head, false); P.tears.push(tr); }
  scene.add(g);
  return { g, P, kind: "child" };
}
// enfant porté dans les bras (côté gauche de l'adulte)
export function carry(adult, kid) {
  adult.P.body.add(kid.g); kid.g.position.set(-0.12, 1.08, 0.16); kid.g.rotation.set(0, 0.5, 0); kid.g.scale.setScalar(0.92);
  kid.P.legL.rotation.x = -1.2; kid.P.legR.rotation.x = -1.1;
}
export function carryPose(adult, t) {
  const P = adult.P;
  P.armL.sh.rotation.set(-0.55, 0.3, 0.35); P.armL.el.rotation.set(-1.5, 0, 0);
  P.armR.sh.rotation.set(-0.35, -0.2, -0.25); P.armR.el.rotation.set(-1.3, 0, 0);
}
export function cry(kid, t, k = 1) {
  face(kid, { worry: k, blink: 0.75 * k, open: (0.6 + 0.4 * Math.sin(t * 7)) * k });
  kid.P.head.rotation.set(Math.sin(t * 5) * 0.06 * k, Math.sin(t * 2.2) * 0.12, 0);
  for (const tr of kid.P.tears) { tr.material.opacity = 0.85 * k; tr.position.y = -0.012 - ((t * 0.04) % 0.05); }
}
