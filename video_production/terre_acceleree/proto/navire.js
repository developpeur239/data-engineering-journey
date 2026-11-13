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
};
const SEQ = SEQS[PARAMS.get('seq') || 'equateur'];
const D = SEQ.duree, jourH = pchip(SEQ.jour);
const gRel = t => physique.poids(0, jourH(t)) / 75;                       // pesanteur ressentie (1 = aujourd'hui)

const { renderer, scene, camera } = moteur({ exposition: 0.6, brume: [0x9fc2e0, 1500, 14000] });
const sky = ciel(scene);
const eau = mer(scene, rnd, { couleur: 0x0b5f8c, taille: 1.6 });
const soleil = new THREE.DirectionalLight(0xfff0dc, 3.0);
soleil.castShadow = true; soleil.shadow.mapSize.set(2048, 2048);
Object.assign(soleil.shadow.camera, { left: -90, right: 90, top: 90, bottom: -90, near: 1, far: 800 });
soleil.shadow.bias = -0.0004; scene.add(soleil, soleil.target);
const amb = new THREE.HemisphereLight(0xbcd6f0, 0x2a4a5a, 1.1); scene.add(amb);

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
const coulC = [0x2f6fb3, 0xc0392b, 0x2a7f62, 0xe8a33a, 0x6b6f75];
const conteneurs = [];
for (let i = 0; i < 10; i++) { const b = box(6, 2.6, 2.4, M(coulC[i % 5], 0.6, 0.3), 12 + (i % 5) * 7, PONT + 1.3 + Math.floor(i / 5) * 2.6, 16); conteneurs.push({ b, y0: b.position.y, s: 0.3 + rnd() }); }
// fumée du décollage (particules)
const NF = 900, fum = { pos: new Float32Array(NF * 3), meta: Array.from({ length: NF }, () => [rnd(), rnd() * 6.28, 0.3 + rnd()]) };
const gF = new THREE.BufferGeometry(); gF.setAttribute('position', new THREE.BufferAttribute(fum.pos, 3));
const rond = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.45)'); gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const fumee = new THREE.Points(gF, new THREE.PointsMaterial({ color: 0xeeeeee, map: rond, size: 16, sizeAttenuation: true, transparent: true, opacity: 0.28, depthWrite: false }));
scene.add(fumee);
// gouttes et embruns qui montent à 1 h 24
const NG = 1600, gou = { pos: new Float32Array(NG * 3), meta: Array.from({ length: NG }, () => [(rnd() - 0.5) * 400, (rnd() - 0.5) * 400, rnd(), 0.4 + rnd()]) };
const gG = new THREE.BufferGeometry(); gG.setAttribute('position', new THREE.BufferAttribute(gou.pos, 3));
const gouttes = new THREE.Points(gG, new THREE.PointsMaterial({ color: 0xd8ecff, map: rond, size: 0.9, transparent: true, opacity: 0.8, depthWrite: false }));
scene.add(gouttes);

// ---------- l'équipe sur le pont ----------
const NP = 46, gens = foule(scene, NP, rnd);
const P = Array.from({ length: NP }, (_, i) => ({ x: -40 + rnd() * 80, z: -26 + rnd() * 52, ph: rnd() * 10, saute: i % 3 === 0, cap: rnd() * 6.28, v: 0.4 + rnd() }));

function frame(t) {
  const jour = jourH(t), g = gRel(t);
  const u = t / D;
  const sd = dirSoleil(lerp(SEQ.soleil[0][0], SEQ.soleil[1][0], u), lerp(SEQ.soleil[0][1], SEQ.soleil[1][1], u));
  camera.position.set(...chemin(SEQ.chemin, t, 1)); camera.lookAt(...chemin(SEQ.chemin, t, 2)); camera.updateMatrixWorld();
  sky.material.uniforms.sunDir.value.copy(sd); sky.material.uniforms.soir.value = smooth((u - 0.6) / 0.4) * (SEQ === SEQS.apesanteur ? 1 : 0.8);
  sky.material.uniforms.temps.value = t; sky.position.copy(camera.position);
  eau.material.uniforms.sunDirection.value.copy(sd);
  // vagues : leur rythme suit √g (elles retombent au ralenti quand on s'allège)
  eau.material.uniforms.time.value = (eau.userData.tacc = (eau.userData.tacc ?? 0) + 0.6 * Math.sqrt(Math.max(g, 0.02)) / 30);
  soleil.position.copy(camera.position).addScaledVector(sd, 300); soleil.target.position.set(0, PONT, 0);
  // personnes : sauts de plus en plus hauts et lents ; à 1 h 24 elles quittent le pont
  const flotte = SEQ === SEQS.apesanteur ? smooth((t - 9) / 14) : 0;
  P.forEach((p, i) => {
    let y = PONT, incl = 0;
    if (p.saute) {
      const v0 = 2.6, T = 2 * v0 / (9.81 * Math.max(g, 0.05)), ph = ((t + p.ph) % (T + 0.8));
      if (ph < T) y += v0 * ph - 0.5 * 9.81 * g * ph * ph;
    }
    y += flotte * (1.5 + 14 * p.v) * smooth((t - 9 - p.ph * 0.4) / 12);
    incl = flotte * Math.sin(t * 0.4 + p.ph) * 0.8;
    gens.pose(i, p.x, y, p.z, p.cap + flotte * t * 0.1, incl, 1);
  });
  gens.maj();
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
