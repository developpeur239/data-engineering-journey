// Décor « Paris » (séquence 4) : quai de Seine, immeubles haussmanniens, tour Eiffel ; jours et nuits qui défilent,
// séismes, sol qui penche vers le sud, une bille qui roule. ?scene=paris&seq=paris
import * as THREE from 'three';
import { PARAMS, alea, lerp, clamp, smooth, env, pchip, chemin, physique, fmtNombre, hud, sousTitres, noir, moteur, mer, ciel, dirSoleil, foule, canvasTex, exposer } from './commun.js';

const rnd = alea(77);
const SEQ = {
  duree: 90, jour: [[0, 12], [15, 8], [25, 7.5], [45, 6], [65, 4.5], [90, 4]],
  sous: [[0.5, 13, 'Paris. Le soleil traverse le ciel en six heures.'], [15, 24, 'La roche ne suit plus.'], [25, 38, 'Séismes, partout à la fois.'],
         [45, 60, 'Le jour se lève, et se couche déjà.'], [65, 78, 'Le sol penche vers le sud.'], [80, 89.3, 'Une bille roule toute seule.']],
  // repère : la Seine coule le long de x ; ouest = +x (la tour Eiffel est à l'ouest), nord = +z
  chemin: [[0, [-140, 14, 40], [600, 70, -10]], [30, [-100, 10, 38], [600, 60, -20]], [60, [-60, 7, 36], [600, 50, -30]],
           [78, [-30, 4, 34], [200, 6, -40]], [90, [-22, 2.2, 33], [40, -2, 10]]],
  lat: 48.86,
};
const D = SEQ.duree, jourH = pchip(SEQ.jour);
const { renderer, scene, camera } = moteur({ exposition: 0.62, brume: [0xb7c6d6, 300, 3200] });
const sky = ciel(scene);
const eau = mer(scene, rnd, { couleur: 0x3d5a52, taille: 6 });
eau.position.y = -5;
const soleil = new THREE.DirectionalLight(0xfff0dc, 3.0);
soleil.castShadow = true; soleil.shadow.mapSize.set(2048, 2048);
Object.assign(soleil.shadow.camera, { left: -160, right: 160, top: 160, bottom: -160, near: 1, far: 1200 });
soleil.shadow.bias = -0.0004; scene.add(soleil, soleil.target);
const amb = new THREE.HemisphereLight(0xbcd6f0, 0x6a6458, 1.0); scene.add(amb);
const villeG = new THREE.Group(); scene.add(villeG);                     // tout ce qui tremble
const M = (c, r = 0.8, m = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: r, metalness: m });
const box = (w, h, d, mat, x, y, z, parent = villeG) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; parent.add(b); return b; };

// quais, chaussées, trottoirs
const pierre = M(0xc9bda6, 0.9);
for (const s of [1, -1]) {
  box(3000, 5.5, 12, pierre, 0, -2.75, s * 31);                          // mur de quai
  box(3000, 0.3, 30, M(0x3e4045, 0.95), 0, 0.15, s * 52);                // chaussée
  box(3000, 0.4, 8, M(0xb9b2a4, 0.9), 0, 0.2, s * 40);                   // trottoir
}
// immeubles haussmanniens : pierre de taille, balcons filants, toits d'ardoise ; fenêtres qui s'allument la nuit
const texFac = canvasTex(256, 512, (g, w, h) => {
  g.fillStyle = '#e4d8bf'; g.fillRect(0, 0, w, h);
  for (let y = 40; y < h - 30; y += 62) {
    g.fillStyle = '#c9bb9e'; g.fillRect(0, y + 44, w, 6);                // balcon filant
    for (let x = 14; x < w - 20; x += 40) { g.fillStyle = '#3b4652'; g.fillRect(x, y, 22, 40); }
  }
}, [1, 1]);
const texNuit = canvasTex(256, 512, (g, w, h) => {
  g.fillStyle = '#000'; g.fillRect(0, 0, w, h);
  for (let y = 40; y < h - 30; y += 62) for (let x = 14; x < w - 20; x += 40) if (Math.random() < 0.55) { g.fillStyle = '#ffcf7a'; g.fillRect(x + 2, y + 2, 18, 36); }
}, [1, 1]);
const matsImm = [];
for (const s of [1, -1]) for (let x = -1400; x < 1400; x += 34 + rnd() * 10) {
  const h = 20 + rnd() * 6, w = 30 + rnd() * 6, z = s * 82;
  const mat = new THREE.MeshStandardMaterial({ map: texFac.clone(), emissiveMap: texNuit, emissive: 0x000000, roughness: 0.9 });
  mat.map.repeat.set(w / 14, h / 26); mat.map.needsUpdate = true; mat.emissiveMap = texNuit.clone(); mat.emissiveMap.repeat.set(w / 14, h / 26); mat.emissiveMap.needsUpdate = true;
  matsImm.push(mat);
  box(w, h, 30, mat, x, h / 2, z);
  const toit = new THREE.Mesh(new THREE.CylinderGeometry(10, 15, 6, 4, 1), M(0x5d6670, 0.6, 0.3));
  toit.rotation.y = Math.PI / 4; toit.scale.set(w / 21, 1, 30 / 21); toit.position.set(x, h + 3, z); toit.castShadow = true; villeG.add(toit);
}
// la tour Eiffel (silhouette en treillis simplifiée) à l'ouest
{
  const fer = M(0x5b4636, 0.7, 0.5), tE = new THREE.Group(); villeG.add(tE);
  const jambe = (sx, sz) => { for (let i = 0; i < 12; i++) { const y = i * 9, e = 62 * Math.pow(1 - y / 330, 2.2) / 2;
    const b = new THREE.Mesh(new THREE.BoxGeometry(3.2, 9.6, 3.2), fer); b.position.set(sx * e, y + 4.5, sz * e); b.castShadow = true; tE.add(b); } };
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([a, b]) => jambe(a, b));
  for (let y = 108; y < 300; y += 8) { const e = 62 * Math.pow(1 - y / 330, 2.2); const b = new THREE.Mesh(new THREE.BoxGeometry(e * 0.95 + 2, 8.4, e * 0.95 + 2), fer); b.position.y = y + 4; tE.add(b); }
  for (const [y, w] of [[57, 70], [115, 40], [276, 16]]) { const p = new THREE.Mesh(new THREE.BoxGeometry(w, 4, w), fer); p.position.y = y; tE.add(p); }
  const arc = new THREE.Mesh(new THREE.TorusGeometry(26, 2, 6, 24, Math.PI), fer); arc.position.y = 20; tE.add(arc);
  tE.position.set(820, 0, -30); tE.rotation.y = 0.5;
}
// réverbères, platanes, voitures, passants
const arbres = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), M(0x4f6b38, 1), 120);
const POS_CAM = Array.from({ length: 91 }, (_, i) => chemin(SEQ.chemin, i, 1));
{ const o = new THREE.Object3D(); for (let i = 0; i < 120; i++) { const x = -1200 + i * 20, z = (i % 2 ? 1 : -1) * 44;
  const libre = POS_CAM.some(c => Math.hypot(c[0] - x, c[2] - z) < 24) ? 0 : 1;              // pas d'arbre devant l'objectif
  o.position.set(x, 9, z); o.scale.set(5.5 * libre, 6 * libre, 5.5 * libre); o.updateMatrix(); arbres.setMatrixAt(i, o.matrix);
  if (libre) box(0.6, 7, 0.6, M(0x6d5a44, 1), x, 3.5, z); } }
arbres.castShadow = true; villeG.add(arbres);
const voitures = Array.from({ length: 26 }, (_, i) => {
  const g = new THREE.Group(), c = M([0xf0f0f0, 0x1c1c1e, 0x8a9199, 0xb2382f, 0x2b4f7d][i % 5], 0.35, 0.5);
  const b1 = new THREE.Mesh(new THREE.BoxGeometry(4.3, 0.8, 1.8), c); b1.position.y = 0.7; const b2 = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.6, 1.6), M(0x26323c, 0.15, 0.6)); b2.position.set(-0.2, 1.35, 0);
  g.add(b1, b2); b1.castShadow = true; villeG.add(g);
  return { g, x0: -1200 + rnd() * 2400, v: (i % 2 ? 1 : -1) * (10 + rnd() * 5), z: (i % 2 ? 1 : -1) * (47 + (i % 4 < 2 ? 0 : 7)) };
});
const NP = 160, gens = foule(scene, NP, rnd);
const P = Array.from({ length: NP }, () => ({ x: -400 + rnd() * 700, z: (rnd() < 0.5 ? 1 : -1) * (37 + rnd() * 5), v: 0.8 + rnd() * 0.7, dir: rnd() < 0.5 ? 1 : -1, ph: rnd() * 6 }));
// la bille (sur le quai nord, elle roule vers le sud, vers la Seine)
const bille = new THREE.Mesh(new THREE.SphereGeometry(0.35, 24, 16), M(0xd8382b, 0.3, 0.1)); bille.castShadow = true; scene.add(bille);

// soleil : on accumule sa course ; une « journée » à l'écran raccourcit avec la vraie durée du jour
const phase = t => { let a = 0; const n = 300; for (let i = 0; i < n; i++) { const u = (i + 0.5) / n * t; a += (t / n) / (34 * jourH(u) / 12); } return a + 0.3; };
const seisme = t => (smooth((t - 15) / 4) * (1 - smooth((t - 52) / 10)) * (0.6 + 0.4 * Math.sin(t * 0.7))) ** 1.2;

function frame(t) {
  const jour = jourH(t), ph = phase(t) % 1;                              // 0 → lever, 0,5 → coucher
  const haut = Math.sin(ph * 2 * Math.PI);                               // > 0 : le jour
  const sd = dirSoleil(Math.max(-30, 52 * haut), 90 + ph * 360 * 0.5);   // il se lève à l'est (−x), se couche à l'ouest (+x)
  const nuit = smooth(-haut / 0.25 + 0.2);
  sky.material.uniforms.sunDir.value.copy(sd); sky.material.uniforms.nuit.value = nuit; sky.material.uniforms.soir.value = smooth(1 - Math.abs(haut) / 0.35) * (1 - nuit);
  sky.material.uniforms.temps.value = t;
  soleil.intensity = 3.0 * smooth(haut / 0.15); amb.intensity = lerp(0.18, 1.0, 1 - nuit);
  scene.fog.color.setRGB(...[0, 1, 2].map(i => lerp([.72, .78, .84][i], [.05, .07, .12][i], nuit))).convertSRGBToLinear();
  matsImm.forEach(m => m.emissive.setScalar(nuit * 0.9));
  // caméra, tremblement, pente
  const q = seisme(t);
  camera.position.set(...chemin(SEQ.chemin, t, 1)); camera.lookAt(...chemin(SEQ.chemin, t, 2));
  camera.position.x += q * 0.35 * Math.sin(t * 37); camera.position.y += q * 0.25 * Math.sin(t * 43 + 1);
  camera.rotateZ(physique.pente(SEQ.lat, jour) * Math.PI / 180 * 1.0 + q * 0.01 * Math.sin(t * 29));
  camera.updateMatrixWorld();
  villeG.position.set(q * 0.15 * Math.sin(t * 31), 0, q * 0.12 * Math.sin(t * 27 + 2));
  sky.position.copy(camera.position);
  eau.material.uniforms.sunDirection.value.copy(sd); eau.material.uniforms.time.value = t * 0.5;
  soleil.position.copy(camera.position).addScaledVector(sd, 500); soleil.target.position.copy(camera.position);
  voitures.forEach(c => { const x = ((c.x0 + c.v * t) + 1200) % 2400 - 1200; c.g.position.set(x, 0.3, c.z); c.g.rotation.y = c.v > 0 ? 0 : Math.PI; });
  P.forEach((p, i) => { const arret = smooth((t - 25 - p.ph) / 3), x = p.x + p.dir * p.v * Math.min(t, 25 + p.ph);
    gens.pose(i, x, 0.4, p.z, p.dir > 0 ? -Math.PI / 2 : Math.PI / 2, 0, 1, Math.abs(Math.sin(t * 7 + p.ph)) * 0.05 * (1 - arret)); });
  gens.maj();
  // la bille : posée, puis elle roule vers le sud quand la pente dépasse sa résistance
  const tb = Math.max(0, t - 79), a = 9.81 * Math.sin(physique.pente(SEQ.lat, jour) * Math.PI / 180) * 0.55;
  bille.position.set(-14, 0.75, 36.5 - 0.5 * a * tb * tb); bille.rotation.x = -(0.5 * a * tb * tb) / 0.35;
  // incrustations
  const pente = physique.pente(SEQ.lat, jour);
  hud({ jour, poids: physique.poids(SEQ.lat, jour), lieu: 'PARIS · 48,9° NORD',
        orange: pente >= 1 ? `LE SOL PENCHE DE ${fmtNombre(pente, 1)}°` : (q > 0.3 ? 'LA CROÛTE SE DÉFORME : SÉISMES' : `PARIS FILE À ${fmtNombre(Math.round(physique.vitesseEquateur(jour) * Math.cos(SEQ.lat * Math.PI / 180) / 10) * 10)} KM/H`) });
  sousTitres(t, SEQ.sous);
  noir(t, D, 0.6, 0.6);
  renderer.render(scene, camera);
  return true;
}
exposer({ duree: D, jour: jourH, frame, etat: t => {
  const ph = phase(t) % 1; camera.position.set(...chemin(SEQ.chemin, t, 1));
  return { t, jour: jourH(t), jourNuit: Math.sin(ph * 2 * Math.PI), seisme: seisme(t), bille: Math.max(0, t - 79), pente: physique.pente(SEQ.lat, jourH(t)) };
} });
await document.fonts.ready;
frame(0);
window.pret = true;
