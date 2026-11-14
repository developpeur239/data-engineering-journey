// Décor « plateforme en pleine mer, sur l'équateur » (inspiré de Sea Launch) : séquences 5 (on devient léger) et 7 (1 h 24).
// ?scene=navire&seq=equateur|apesanteur
import * as THREE from 'three';
import { PARAMS, alea, lerp, clamp, smooth, env, pchip, chemin, physique, fmtNombre, hud, sousTitres, noir, moteur, mer, ciel, dirSoleil, foule, exposer } from './commun.js';

const rnd = alea(41);
const SEQS = {
  equateur: { duree: 70, jour: [[0, 4], [20, 3], [45, 2], [70, 1 + 50 / 60]], fusee: 44,
    sous: [[0.5, 10, 'Sur l’océan, à l’équateur.'], [12, 22, 'Ici, vous devenez léger.'], [25, 37, 'Un saut, et vous retombez lentement.'],
           [41, 54, 'Les fusées n’ont presque plus besoin de pousser.'], [58, 68.5, 'Les vagues retombent au ralenti.']],
    chemin: [[0, [70, 16, 60], [0, 6, 0]], [20, [44, 13, 36], [-10, 8, -6]], [38, [16, 14, 34], [-14, 10, -4]],
             [52, [-30, 12, 70], [-20, 40, -10]], [70, [-80, 18, 60], [0, 10, 0]]],
    soleil: [[40, 120], [12, 245]] },
  apesanteur: { duree: 30, jour: [[0, 1 + 26 / 60], [15, 1 + 24.6 / 60], [30, 1 + 23 / 60]], fusee: -1,
    sous: [[0.5, 13, 'À l’équateur, le sol va aussi vite que la Station spatiale.'], [15, 28, 'Vous ne pesez plus rien.']],
    chemin: [[0, [55, 10, 50], [0, 6, 0]], [30, [30, 22, 60], [0, 14, 0]]],
    soleil: [[14, 250], [9, 255]] },
  // image fixe pour la miniature YouTube (pas dans le film) : tout décolle, contre-plongée, ciel de fin de journée
  miniature: { duree: 30, jour: [[0, 1 + 26 / 60], [15, 1 + 24.6 / 60], [30, 1 + 23 / 60]], fusee: -1, sous: [],
    chemin: [[0, [34, 9.2, 44], [-6, 24, 2]], [30, [34, 9.2, 44], [-6, 24, 2]]],
    soleil: [[7, 248], [7, 248]] },
};
const SEQ = SEQS[PARAMS.get('seq') || 'equateur'];
const MINI = SEQ === SEQS.miniature, APES = SEQ === SEQS.apesanteur || MINI;
const D = SEQ.duree, jourH = pchip(SEQ.jour);
const gRel = t => physique.poids(0, jourH(t)) / 75;                       // pesanteur ressentie (1 = aujourd'hui)

const { renderer, scene, camera } = moteur({ exposition: MINI ? 0.72 : 0.6, brume: [0x9fc2e0, 1500, 14000] });
const sky = ciel(scene);
const eau = mer(scene, rnd, { couleur: 0x0b5f8c, taille: 1.6 });
const soleil = new THREE.DirectionalLight(0xfff0dc, 3.0);
soleil.castShadow = true; soleil.shadow.mapSize.set(2048, 2048);
Object.assign(soleil.shadow.camera, { left: -90, right: 90, top: 90, bottom: -90, near: 1, far: 800 });
soleil.shadow.bias = -0.0004; scene.add(soleil, soleil.target);
const amb = new THREE.HemisphereLight(0xbcd6f0, 0x6a7a80, MINI ? 2.2 : 1.1); scene.add(amb);

// ---------- la plateforme ----------
const plate = new THREE.Group(); scene.add(plate);
const M = (c, r = 0.7, m = 0.1) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, mat, x, y, z) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; plate.add(b); return b; };
const PONT = 8;                                                            // hauteur du pont au-dessus de l'eau
box(110, 2.4, 66, M(0x9aa3a8, 0.8, 0.3), 0, PONT - 1.2, 0);              // pont
for (const [x, z] of [[-42, -24], [42, -24], [-42, 24], [42, 24]]) {      // colonnes et flotteurs
  const c = new THREE.Mesh(new THREE.CylinderGeometry(4.5, 4.5, 26, 20), M(0xd9d4c4, 0.6, 0.2)); c.position.set(x, PONT - 14, z); c.castShadow = true; plate.add(c);
}
box(100, 4, 8, M(0xd9d4c4, 0.6, 0.2), 0, -10, -24); box(100, 4, 8, M(0xd9d4c4, 0.6, 0.2), 0, -10, 24);
const rail = M(0xf2c330, 0.5, 0.3);
for (let x = -54; x <= 54; x += 3) for (const z of [-32.5, 32.5]) box(0.12, 1.1, 0.12, rail, x, PONT + 0.55, z);
box(110, 0.12, 0.12, rail, 0, PONT + 1.1, -32.5); box(110, 0.12, 0.12, rail, 0, PONT + 1.1, 32.5);
// tour de lancement, fusée, hangar, conteneurs
const tour = M(0xb63a2e, 0.6, 0.4);
for (const [x, z] of [[-24, -6], [-16, -6], [-24, 2], [-16, 2]]) box(0.8, 46, 0.8, tour, x, PONT + 23, z);
for (let y = 4; y < 46; y += 4) { box(9, 0.4, 0.4, tour, -20, PONT + y, -6); box(9, 0.4, 0.4, tour, -20, PONT + y, 2); box(0.4, 0.4, 9, tour, -24, PONT + y, -2); }
const fusee = new THREE.Group(); plate.add(fusee);
const blanc = M(0xf4f4f0, 0.35, 0.2), noirM = M(0x1d1d22, 0.5, 0.2);
{ const corps = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, 38, 24), blanc); corps.position.y = 19; corps.castShadow = true; fusee.add(corps);
  const coiffe = new THREE.Mesh(new THREE.ConeGeometry(2.0, 6, 24), blanc); coiffe.position.y = 41; fusee.add(coiffe);
  for (const y of [8, 26]) { const b = new THREE.Mesh(new THREE.CylinderGeometry(2.03, 2.03, 1.2, 24), noirM); b.position.y = y; fusee.add(b); } }
const flamme = new THREE.Mesh(new THREE.ConeGeometry(2.2, 14, 16, 1, true), new THREE.MeshBasicMaterial({ color: 0xffb25a, transparent: true, opacity: 0.9, side: THREE.DoubleSide }));
flamme.rotation.x = Math.PI; flamme.position.y = -7; fusee.add(flamme);
fusee.position.set(-9, PONT, -2);
box(26, 12, 18, M(0xe9e6dd, 0.7, 0.1), 28, PONT + 6, -10);              // hangar
const coulC = MINI ? [0xff3b30, 0xffcc00, 0x0a84ff, 0xff9500, 0x30d158, 0xbf5af2, 0xff2d92] : [0x2f6fb3, 0xc0392b, 0x2a7f62, 0xe8a33a, 0x6b6f75];
const conteneurs = [];
for (let i = 0; i < 10; i++) { const b = box(6, 2.6, 2.4, M(coulC[i % coulC.length], 0.6, 0.3), 12 + (i % 5) * 7, PONT + 1.3 + Math.floor(i / 5) * 2.6, 16); conteneurs.push({ b, y0: b.position.y, s: 0.3 + rnd() }); }
// miniature : beaucoup plus d'objets en l'air (conteneurs, fûts, caisses)
const objets = [];
if (MINI) {
  const coulF = [0xe24b3b, 0xf2c330, 0x2e6fb7, 0x3a9d6a, 0xf28c28, 0xe8e8e2];
  for (let i = 0; i < 70; i++) {
    const k = i % 3, c = coulF[i % coulF.length];
    const g = k === 0 ? new THREE.BoxGeometry(6, 2.6, 2.4) : k === 1 ? new THREE.CylinderGeometry(0.45, 0.45, 1.3, 14) : new THREE.BoxGeometry(1.2, 1.2, 1.2);
    const m = new THREE.Mesh(g, M(k === 0 ? coulC[i % coulC.length] : coulC[(i * 3 + 1) % coulC.length], 0.45, 0.15)); m.castShadow = true; plate.add(m);
    objets.push({ m, x: -20 + rnd() * 60, z: -20 + rnd() * 55, h: 3 + rnd() * 30, r: [rnd() * 6, rnd() * 6, rnd() * 6] });
  }
}
// fumée du décollage (particules)
const NF = 900, fum = { pos: new Float32Array(NF * 3), meta: Array.from({ length: NF }, () => [rnd(), rnd() * 6.28, 0.3 + rnd()]) };
const gF = new THREE.BufferGeometry(); gF.setAttribute('position', new THREE.BufferAttribute(fum.pos, 3));
const rond = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const fumee = new THREE.Points(gF, new THREE.PointsMaterial({ color: 0xeeeeee, map: rond, size: 16, sizeAttenuation: true, transparent: true, opacity: 0.28, depthWrite: false }));
scene.add(fumee);
// gouttes et embruns qui montent à 1 h 24
const NG = 1600, gou = { pos: new Float32Array(NG * 3), meta: Array.from({ length: NG }, () => [(rnd() - 0.5) * (MINI ? 160 : 400), (rnd() - 0.5) * (MINI ? 160 : 400), rnd(), 0.4 + rnd()]) };
const gG = new THREE.BufferGeometry(); gG.setAttribute('position', new THREE.BufferAttribute(gou.pos, 3));
const gouttes = new THREE.Points(gG, new THREE.PointsMaterial({ color: 0xd8ecff, map: rond, size: MINI ? 1.4 : 0.9, transparent: true, opacity: 0.8, depthWrite: false }));
scene.add(gouttes);

// miniature : la mer se soulève en colonnes derrière la plateforme
const NC = 40000, colPos = new Float32Array(NC * 3);
const gC = new THREE.BufferGeometry(); gC.setAttribute('position', new THREE.BufferAttribute(colPos, 3));
const colonnes = new THREE.Points(gC, new THREE.PointsMaterial({ color: 0xeaf7ff, map: rond, size: 7, transparent: true, opacity: 0.32, depthWrite: false }));
colonnes.visible = MINI; scene.add(colonnes);
const COL = Array.from({ length: 9 }, (_, i) => ({ a: -0.6 + i * 0.17 + (rnd() - 0.5) * 0.05, d: 85 + rnd() * 70, h: 40 + rnd() * 60, r: 2.5 + rnd() * 2.5 }));

// ---------- l'équipe sur le pont ----------
const NP = MINI ? 150 : 46, gens = foule(scene, NP, rnd);
const P = Array.from({ length: NP }, (_, i) => ({ x: MINI ? -15 + rnd() * 52 : -40 + rnd() * 80, z: MINI ? -10 + rnd() * 48 : -26 + rnd() * 52, ph: rnd() * 10, saute: i % 3 === 0, cap: rnd() * 6.28, v: 0.4 + rnd() }));

// miniature : rien ne passe devant le compteur (coin haut gauche de l'écran)
const _v = new THREE.Vector3();
const dansCoin = (x, y, z) => { _v.set(x, y, z).project(camera); return _v.x < 0.02 && _v.y > 0.05; };
let colPrete = false;
function placeColonnes() {
  // repère caméra : direction horizontale de visée, et sa droite
  const f = new THREE.Vector3(); camera.getWorldDirection(f); f.y = 0; f.normalize();
  const r = new THREE.Vector3(-f.z, 0, f.x);
  for (let i = 0; i < NC; i++) {
    const c = COL[i % COL.length], u = rnd(), h = c.h * Math.pow(u, 0.7);
    const base = camera.position.clone().addScaledVector(f, c.d).addScaledVector(r, Math.tan(c.a) * c.d);
    const rr = c.r * (1 + 1.6 * u * u) * Math.sqrt(rnd()), an = rnd() * 6.28;
    let x = base.x + Math.cos(an) * rr, y = -1 + h, z = base.z + Math.sin(an) * rr;
    if (dansCoin(x, y, z)) y = -999;
    colPos.set([x, y, z], i * 3);
  }
  gC.attributes.position.needsUpdate = true; colPrete = true;
}
function premierPlan() {
  // quelques personnes proches de la caméra, côté droit, qui flottent
  const f = new THREE.Vector3(); camera.getWorldDirection(f);
  const r = new THREE.Vector3().crossVectors(f, camera.up).normalize(), up = new THREE.Vector3().crossVectors(r, f);
  [[9, 3.2, -1.2, 0.7], [12, 1.4, 1.6, -0.5], [14, 4.8, 2.4, 1.6], [10, 5.2, -2.6, 2.4], [16, 2.6, 4.2, -1.1]].forEach(([d, rx, uy, rot], k) => {
    const p = camera.position.clone().addScaledVector(f, d).addScaledVector(r, rx).addScaledVector(up, uy);
    gens.pose(k, p.x, p.y - 0.9, p.z, rot * 2, rot, 1);
  });
  gens.maj();
}
function masqueCoin() {
  P.forEach((p, i) => { if (dansCoin(p.x, p.yv, p.z)) gens.pose(i, 0, -999, 0, 0, 0, 0); });
  gens.maj();
}
function frame(t) {
  const jour = jourH(t), g = gRel(t);
  const u = t / D;
  const sd = dirSoleil(lerp(SEQ.soleil[0][0], SEQ.soleil[1][0], u), lerp(SEQ.soleil[0][1], SEQ.soleil[1][1], u));
  camera.position.set(...chemin(SEQ.chemin, t, 1)); camera.lookAt(...chemin(SEQ.chemin, t, 2)); camera.updateMatrixWorld();
  sky.material.uniforms.sunDir.value.copy(sd); sky.material.uniforms.soir.value = smooth((u - 0.6) / 0.4) * (APES ? 1 : 0.8);
  sky.material.uniforms.temps.value = t; sky.position.copy(camera.position);
  eau.material.uniforms.sunDirection.value.copy(sd);
  // vagues : leur rythme suit √g (elles retombent au ralenti quand on s'allège)
  eau.material.uniforms.time.value = (eau.userData.tacc = (eau.userData.tacc ?? 0) + 0.6 * Math.sqrt(Math.max(g, 0.02)) / 30);
  soleil.position.copy(camera.position).addScaledVector(sd, 300); soleil.target.position.set(0, PONT, 0);
  // personnes : sauts de plus en plus hauts et lents ; à 1 h 24 elles quittent le pont
  const flotte = APES ? smooth((t - 9) / 14) : 0;
  P.forEach((p, i) => {
    let y = PONT, incl = 0;
    if (p.saute) {
      const v0 = 2.6, T = 2 * v0 / (9.81 * Math.max(g, 0.05)), ph = ((t + p.ph) % (T + 0.8));
      if (ph < T) y += v0 * ph - 0.5 * 9.81 * g * ph * ph;
    }
    y += flotte * (1.5 + 14 * p.v) * smooth((t - 9 - p.ph * 0.4) / 12);
    incl = flotte * Math.sin(t * 0.4 + p.ph) * 0.8;
    p.yv = y; gens.pose(i, p.x, y, p.z, p.cap + flotte * t * 0.1, incl, 1);
  });
  gens.maj();
  if (MINI) { masqueCoin(); premierPlan(); if (!colPrete) placeColonnes(); }
  objets.forEach(o => { o.m.position.set(o.x, PONT + 1.5 + o.h * flotte, o.z); o.m.rotation.set(o.r[0] * flotte, o.r[1], o.r[2] * flotte); o.m.visible = !dansCoin(o.x, o.m.position.y, o.z); });
  conteneurs.forEach(c => { c.b.position.y = c.y0 + flotte * 10 * c.s * smooth((t - 12 - c.s * 4) / 14); c.b.rotation.z = flotte * c.s * 0.4; });
  // fusée : allumage puis décollage (accélération ≈ poussée − g ressentie)
  const tf = SEQ.fusee >= 0 ? t - SEQ.fusee : -1;
  fusee.visible = SEQ.fusee >= 0;
  flamme.visible = tf > 0; flamme.scale.set(1, 0.8 + 0.3 * Math.sin(t * 40), 1);
  const a = 5 + 9.81 * (1 - g);                                           // m/s² : plus la pesanteur baisse, plus elle file
  fusee.position.y = PONT + (tf > 1.2 ? 0.5 * a * (tf - 1.2) ** 2 : 0);
  fum.meta.forEach(([r, ang, s], i) => {
    const age = tf - r * 6;
    if (tf < 0 || age < 0) { fum.pos.set([0, -999, 0], i * 3); return; }
    const rr = 4 + age * 6 * s;
    fum.pos.set([fusee.position.x + plate.position.x + Math.cos(ang) * rr, PONT + 1 + age * 1.5 * s, -2 + Math.sin(ang) * rr], i * 3);
  });
  gF.attributes.position.needsUpdate = true; fumee.visible = tf > 0;
  gou.meta.forEach(([x, z, r, s], i) => gou.pos.set([x, -0.5 + flotte * (r * 60 * s) * smooth((t - 10 - r * 8) / 12), z], i * 3));
  gG.attributes.position.needsUpdate = true; gouttes.visible = flotte > 0.01;
  // incrustations
  const v = physique.vitesseEquateur(jour);
  hud({ jour, poids: physique.poids(0, jour), lieu: 'SUR L’OCÉAN · ÉQUATEUR',
        orange: v > 27500 ? `L’ÉQUATEUR : ${fmtNombre(Math.round(v / 10) * 10)} KM/H · VITESSE D’UN SATELLITE` : `L’ÉQUATEUR : ${fmtNombre(Math.round(v / 10) * 10)} KM/H` });
  sousTitres(t, SEQ.sous);
  noir(t, D, 0.6, 0.6);
  if (MINI) conteneurs.forEach(c => { c.b.visible = !dansCoin(c.b.position.x, c.b.position.y, c.b.position.z); });
  renderer.render(scene, camera);
  return true;
}
exposer({ duree: D, jour: jourH, frame, etat: t => {
  camera.position.set(...chemin(SEQ.chemin, t, 1));
  const tf = SEQ.fusee >= 0 ? t - SEQ.fusee : -1;
  return { t, jour: jourH(t), g: gRel(t), fusee: tf, dist: camera.position.distanceTo(new THREE.Vector3(0, PONT, 0)) };
} });
await document.fonts.ready;
frame(0);
window.pret = true;
