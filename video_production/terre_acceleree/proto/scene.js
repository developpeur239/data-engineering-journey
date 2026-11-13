// Prototype « Et si la Terre tournait de plus en plus vite ? » : Nice, Promenade des Anglais.
// Scène Three.js rendue image par image (render.cjs appelle window.frame(t)).
//
// Physique (modèle simple, sans auto-gravitation de l'eau ni déformation de la croûte) :
//   la surface des océans suit le potentiel centrifuge ; quand ω augmente, l'eau migre vers l'équateur.
//   Variation du niveau à la latitude φ : Δh = (R²/2g)·(ω² − ω0²)·(cos²φ − 2/3)
//   R²ω0²/2g ≈ 11,0 km ; à Nice (43,7° N) cos²φ − 2/3 = −0,144 → la mer BAISSE.
import * as THREE from 'three';
import { Water } from 'three/addons/objects/Water.js';

const W = 1920, H = 1080, DUREE = 20;
const LAT = 43.7 * Math.PI / 180;

// ---------- aléa reproductible ----------
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
const pick = a => a[Math.floor(rnd() * a.length)];
const lerp = (a, b, u) => a + (b - a) * u;
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };

// ---------- chronologie ----------
const jourH = t => 24 - 2.5 * Math.pow(clamp(t / DUREE, 0, 1), 3);           // durée du jour (h)
const baisse = t => 11000 * (Math.pow(24 / jourH(t), 2) - 1) * (2 / 3 - Math.cos(LAT) ** 2); // m
const poids = t => {
  const g = 9.806, R = 6.371e6, c2 = Math.cos(LAT) ** 2;
  const w = 2 * Math.PI / (jourH(t) * 3600), w0 = 2 * Math.PI / 86400;
  return 75 * (g - w * w * R * c2) / (g - w0 * w0 * R * c2);
};
const visuel = t => 46 * (1 - Math.exp(-baisse(t) / 250));                       // baisse visible (m)
const SOUS = [[0, 4.6, 'Nice, 14 h. Une journée dure 24 heures.'],
              [4.8, 9.6, 'La Terre se met à tourner un peu plus vite.'],
              [9.8, 14.6, 'Les océans glissent vers l’équateur.'],
              [14.8, 20, 'À Nice, la mer se retire.']];

// ---------- rendu ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.62;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x9fc2e0, 900, 9000);
const camera = new THREE.PerspectiveCamera(42, W / H, 0.5, 20000);

// ---------- textures dessinées en code ----------
function canvasTex(w, h, draw, repeat = [1, 1], srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
const normalesEau = (() => {                       // carte de normales tuilable : somme de sinus entiers
  const N = 256, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d'), img = g.createImageData(N, N);
  const waves = Array.from({ length: 14 }, () => [1 + Math.floor(rnd() * 9), Math.floor(rnd() * 9) - 4, rnd() * 6.28, 0.3 + rnd()]);
  const hgt = (x, y) => waves.reduce((s, [a, b, p, k]) => s + k / (Math.abs(a) + Math.abs(b)) * Math.sin(2 * Math.PI * (a * x + b * y) / N + p), 0);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = hgt(x + 1, y) - hgt(x - 1, y), dy = hgt(x, y + 1) - hgt(x, y - 1);
    const n = new THREE.Vector3(-dx * 2.2, -dy * 2.2, 1).normalize(), i = 4 * (y * N + x);
    img.data[i] = (n.x * .5 + .5) * 255; img.data[i + 1] = (n.y * .5 + .5) * 255; img.data[i + 2] = (n.z * .5 + .5) * 255; img.data[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; return t;
})();
const texDalles = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#d9d2c3'; g.fillRect(0, 0, w, h);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    const v = 200 + rnd() * 30; g.fillStyle = `rgb(${v + 10},${v + 4},${v - 10})`;
    g.fillRect(x * 64 + 1, y * 64 + 1, 62, 62);
  }
}, [80, 1.6]);
const texGalets = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#9d968c'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) {
    const v = 120 + rnd() * 90, r = 2 + rnd() * 6; g.fillStyle = `rgb(${v},${v - 4},${v - 12})`;
    g.beginPath(); g.ellipse(rnd() * w, rnd() * h, r, r * (0.6 + rnd() * 0.4), rnd() * 3, 0, 7); g.fill();
  }
}, [60, 4]);
const texAsphalte = canvasTex(512, 256, (g, w, h) => {
  g.fillStyle = '#4b4d50'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 4000; i++) { const v = 60 + rnd() * 30; g.fillStyle = `rgb(${v},${v},${v + 2})`; g.fillRect(rnd() * w, rnd() * h, 2, 2); }
  g.fillStyle = '#e9e9e2'; for (let x = 0; x < w; x += 128) g.fillRect(x, h / 2 - 3, 64, 6);
}, [60, 1]);
const texFacade = canvasTex(256, 512, (g, w, h) => {
  const tons = ['#e8d2a8', '#e6b98c', '#f0e2c6', '#d99a74', '#efd9b5'];
  g.fillStyle = pick(tons); g.fillRect(0, 0, w, h);
  for (let y = 30; y < h - 20; y += 52) for (let x = 18; x < w - 20; x += 46) {
    g.fillStyle = '#5a6a5c'; g.fillRect(x - 4, y, 6, 30); g.fillRect(x + 22, y, 6, 30);   // volets
    g.fillStyle = '#2d3640'; g.fillRect(x + 2, y + 2, 20, 28);
  }
}, [1, 1]);

// ---------- relief : promenade, galets, fond marin ----------
// z < 0 vers le large (sud), x le long de la côte. Promenade y = 0, plage de z = 0 à −40, puis fond marin.
const PLAGE = -40, Y0 = -4.0;
const fond = (x, z) => {
  if (z > PLAGE) return lerp(-3.0, Y0, -z / 40);
  const d = PLAGE - z;
  return Y0 - 0.085 * d - 0.00006 * d * d + 0.8 * Math.sin(x * 0.013 + z * 0.02) + 0.5 * Math.sin(x * 0.041 - z * 0.033);
};
{
  const geo = new THREE.PlaneGeometry(5200, 1400, 260, 140);
  geo.rotateX(-Math.PI / 2); geo.translate(0, 0, PLAGE - 700);
  const p = geo.attributes.position, col = [];
  const c = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), y = fond(x, z); p.setY(i, y);
    const d = Y0 - y, herbier = Math.sin(x * 0.02) * Math.sin(z * 0.017) + Math.sin(x * 0.007 + z * 0.011);
    const h2 = Math.sin(x * 0.06 + Math.sin(z * 0.05) * 2) * Math.sin(z * 0.045 + x * 0.01);
    if (d < 5) c.setRGB(0.50, 0.47, 0.42);                                   // galets mouillés
    else if ((herbier > 0.2 || h2 > 0.35) && d < 50) c.setRGB(0.12, 0.22, 0.08);  // herbiers de posidonies
    else c.setRGB(0.66 - d * 0.0012, 0.56 - d * 0.0012, 0.40 - d * 0.0009);  // sable
    c.multiplyScalar(0.85 + rnd() * 0.25);
    col.push(c.r, c.g, c.b);
  }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeVertexNormals();
  const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.45, metalness: 0.03 }));
  m.receiveShadow = true; scene.add(m);
  // rochers sur le fond
  const roc = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ color: 0x5f5a50, roughness: 0.9 }), 500);
  const o = new THREE.Object3D();
  for (let i = 0; i < 500; i++) {
    const x = (rnd() - 0.5) * 1600, z = PLAGE - 20 - rnd() * 700, s = 0.6 + rnd() * 3;
    o.position.set(x, fond(x, z) + s * 0.3, z); o.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3); o.scale.set(s, s * 0.6, s * 1.2);
    o.updateMatrix(); roc.setMatrixAt(i, o.matrix);
  }
  roc.castShadow = roc.receiveShadow = true; scene.add(roc);
}
const plage = new THREE.Mesh(new THREE.PlaneGeometry(2600, 40, 200, 4), new THREE.MeshStandardMaterial({ map: texGalets, roughness: 1 }));
{ const g = plage.geometry; g.rotateX(-Math.PI / 2); g.translate(0, 0, -20); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) p.setY(i, fond(p.getX(i), p.getZ(i)) + 0.05); g.computeVertexNormals(); }
plage.receiveShadow = true; scene.add(plage);

const ajoute = (geo, mat, x, y, z, ombre = true) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = ombre; scene.add(m); return m; };
ajoute(new THREE.BoxGeometry(2600, 0.3, 11), new THREE.MeshStandardMaterial({ map: texDalles, roughness: 0.8 }), 0, -0.15, 5.5);   // promenade
ajoute(new THREE.BoxGeometry(2600, 3.4, 0.6), new THREE.MeshStandardMaterial({ color: 0xcfc6b4, roughness: 0.9 }), 0, -1.6, -0.3); // mur
ajoute(new THREE.BoxGeometry(2600, 0.1, 13), new THREE.MeshStandardMaterial({ map: texAsphalte, roughness: 0.95 }), 0, -0.02, 18); // route
ajoute(new THREE.BoxGeometry(2600, 0.3, 2), new THREE.MeshStandardMaterial({ color: 0x8ea56b, roughness: 1 }), 0, 0.05, 11.2);     // terre-plein
ajoute(new THREE.BoxGeometry(2600, 0.2, 5), new THREE.MeshStandardMaterial({ map: texDalles, roughness: 0.8 }), 0, 0.1, 27);      // trottoir nord

// immeubles côté nord
for (let x = -1300; x < 1300; x += 26 + rnd() * 10) {
  const h = 16 + rnd() * 14, w = 20 + rnd() * 8;
  const mat = new THREE.MeshStandardMaterial({ map: texFacade.clone(), roughness: 0.9 });
  mat.map.repeat.set(w / 12, h / 22); mat.map.needsUpdate = true;
  mat.color.setHSL(0.08 + rnd() * 0.04, 0.35, 0.78 + rnd() * 0.1);
  ajoute(new THREE.BoxGeometry(w, h, 14), mat, x, h / 2, 37);
  ajoute(new THREE.BoxGeometry(w + 0.6, 0.8, 14.6), new THREE.MeshStandardMaterial({ color: 0xa8553a, roughness: 0.8 }), x, h + 0.4, 37);
}
// collines lointaines (Baie des Anges, Cap d'Antibes, Préalpes) dans la brume
for (let i = 0; i < 26; i++) {
  const a = -0.2 - i * 0.06, R = 3200 + rnd() * 900;
  const m = ajoute(new THREE.SphereGeometry(1, 24, 12), new THREE.MeshStandardMaterial({ color: 0x5e7259, roughness: 1 }),
    -R * Math.cos(a) * 0.9 - 600, -40, -R * Math.sin(a) * 0.35 + 200, false);
  m.scale.set(500 + rnd() * 500, 160 + rnd() * 260, 400);
}

// palmiers (tronc courbe + palmes en bandes)
const matTronc = new THREE.MeshStandardMaterial({ color: 0x8b7559, roughness: 1 });
const texPalme = canvasTex(256, 64, (g, w, h) => {
  g.clearRect(0, 0, w, h); g.strokeStyle = '#3e6b2c'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(0, h / 2); g.lineTo(w, h / 2); g.stroke();
  for (let x = 4; x < w - 6; x += 5) { const L = (h / 2 - 2) * Math.sin(Math.PI * x / w) ** 0.6;
    g.strokeStyle = `rgb(${50 + rnd() * 30},${100 + rnd() * 40},${40 + rnd() * 20})`; g.lineWidth = 2.2;
    g.beginPath(); g.moveTo(x, h / 2); g.lineTo(x + 9, h / 2 - L); g.moveTo(x, h / 2); g.lineTo(x + 9, h / 2 + L); g.stroke(); }
});
const matPalme = new THREE.MeshStandardMaterial({ map: texPalme, alphaTest: 0.5, side: THREE.DoubleSide, roughness: 0.8 });
function palmier(x, z, h) {
  const g = new THREE.Group(), pench = (rnd() - 0.5) * 0.25;
  const pts = [0, 0.33, 0.66, 1].map(u => new THREE.Vector3(pench * h * u * u, h * u, 0));
  const tronc = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 10, 0.22, 7), matTronc);
  tronc.castShadow = true; g.add(tronc);
  const top = pts[3];
  for (let k = 0; k < 11; k++) {
    const L = 4 + rnd() * 1.5, geo = new THREE.PlaneGeometry(L, 1.1, 10, 1);
    const p = geo.attributes.position;
    for (let i = 0; i < p.count; i++) { const u = (p.getX(i) + L / 2) / L; p.setY(i, p.getY(i) - 1.8 * u * u); p.setX(i, p.getX(i) + L / 2); }
    geo.computeVertexNormals();
    const f = new THREE.Mesh(geo, matPalme); f.castShadow = true;
    f.position.copy(top); f.rotation.set(rnd() * 0.5, (k / 11) * Math.PI * 2 + rnd() * 0.3, 0.25 + rnd() * 0.3, 'YZX');
    g.add(f);
  }
  g.position.set(x, 0.2, z); scene.add(g); return g;
}
const palmiers = [];
for (let x = -900; x < 400; x += 13 + rnd() * 4) palmiers.push(palmier(x, 11.2, 9 + rnd() * 3));

// lampadaires et chaises bleues
const matMetal = new THREE.MeshStandardMaterial({ color: 0x2e3b44, roughness: 0.5, metalness: 0.6 });
for (let x = -900; x < 400; x += 32) { ajoute(new THREE.CylinderGeometry(0.08, 0.1, 6, 6), matMetal, x, 3, 9.6); ajoute(new THREE.SphereGeometry(0.3, 8, 6), new THREE.MeshStandardMaterial({ color: 0xf6f0dc, emissive: 0x332a10 }), x, 6.1, 9.6); }
{
  const bleu = new THREE.MeshStandardMaterial({ color: 0x2f6fb3, roughness: 0.5, metalness: 0.2 });
  const assise = new THREE.BoxGeometry(0.55, 0.06, 0.5), dos = new THREE.BoxGeometry(0.55, 0.55, 0.06);
  const n = 420, A = new THREE.InstancedMesh(assise, bleu, n), B = new THREE.InstancedMesh(dos, bleu, n), o = new THREE.Object3D();
  let k = 0;
  for (let x = -900; x < 400 && k < n; x += 2.6 + rnd() * 1.5, k++) {
    const r = (rnd() - 0.5) * 0.6; o.rotation.set(0, Math.PI + r, 0);
    o.position.set(x, 0.42, 1.4); o.updateMatrix(); A.setMatrixAt(k, o.matrix);
    o.position.set(x + Math.sin(r) * 0.25, 0.7, 1.4 + 0.25 * Math.cos(r)); o.rotation.set(-0.2, Math.PI + r, 0); o.updateMatrix(); B.setMatrixAt(k, o.matrix);
  }
  A.count = B.count = k; A.castShadow = B.castShadow = true; scene.add(A, B);
}
// plages privées : transats blancs et parasols aux couleurs du club
const matTransat = new THREE.MeshStandardMaterial({ color: 0xf2efe8, roughness: 0.7 });
[[-260, 0x2a5f9e], [-140, 0xd8a23a], [-40, 0x1f7d78], [-480, 0xb8473a], [80, 0x2a5f9e]].forEach(([x0, coul]) => {
  const toile = new THREE.MeshStandardMaterial({ color: coul, roughness: 0.8, side: THREE.DoubleSide });
  for (let r = 0; r < 4; r++) for (let i = 0; i < 9; i++) {
    const x = x0 + i * 4.5, z = -8 - r * 6, y = fond(x, z);
    ajoute(new THREE.BoxGeometry(0.75, 0.25, 1.9), matTransat, x, y + 0.35, z);
    if (i % 2 == 0) { ajoute(new THREE.CylinderGeometry(0.03, 0.03, 2.4, 5), matMetal, x + 2.2, y + 1.2, z);
      ajoute(new THREE.ConeGeometry(1.5, 0.5, 10, 1, true), toile, x + 2.2, y + 2.4, z); }
  }
});
// bateaux au mouillage
const bateaux = [];
for (let i = 0; i < 16; i++) {
  const g = new THREE.Group(), L = 6 + rnd() * 9;
  const coque = new THREE.Mesh(new THREE.CylinderGeometry(L * 0.18, L * 0.12, L, 10, 1, false, 0, Math.PI), new THREE.MeshStandardMaterial({ color: pick([0xf4f4f0, 0xf4f4f0, 0x1d3550]), roughness: 0.4 }));
  coque.rotation.set(0, 0, Math.PI / 2); coque.rotation.order = 'ZYX'; coque.rotateY(Math.PI / 2); coque.castShadow = true; g.add(coque);
  const cab = new THREE.Mesh(new THREE.BoxGeometry(L * 0.3, L * 0.12, L * 0.2), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 }));
  cab.position.set(-L * 0.05, L * 0.06, 0); g.add(cab);
  if (rnd() < 0.5) { const mat = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, L * 1.1, 5), matMetal); mat.position.y = L * 0.55; g.add(mat); }
  const x = -500 + rnd() * 700, z = PLAGE - 120 - rnd() * 520;
  g.position.set(x, 0, z); g.rotation.y = rnd() * 6.28; g.userData = { x, z, fondY: fond(x, z), tilt: (rnd() - 0.5) * 0.5, phase: rnd() * 6 };
  scene.add(g); bateaux.push(g);
}

// ---------- foule (instances : jambes, torse, tête) ----------
const N = 520;
const peau = [0xf1c9a5, 0xd9a47c, 0xa8724f, 0x6e4a33, 0xe8b893];
const hauts = [0xe24b3b, 0x2e6fb7, 0xf2f2ee, 0xf2c330, 0x3a9d6a, 0x1f2a3a, 0xe58ab2, 0xf28c28, 0x7a4fa3, 0x19a7c4];
const bas = [0x2b3a55, 0x3b3b3b, 0xd9c9a3, 0x1f4d7a, 0x6b5a45, 0xf0f0ea];
const mk = (geo) => { const m = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.75 }), N); m.castShadow = true; m.receiveShadow = true; scene.add(m); return m; };
const IJ = mk(new THREE.BoxGeometry(0.34, 0.85, 0.22)), IT = mk(new THREE.BoxGeometry(0.46, 0.62, 0.26)), IH = mk(new THREE.SphereGeometry(0.13, 10, 8));
const gens = [];
for (let i = 0; i < N; i++) {
  const surPlage = i < 170;
  const p = {
    surPlage, x: (rnd() - 0.5) * 620 - 100, z: surPlage ? -6 - rnd() * 30 : 0.9 + rnd() * 8.5,
    dir: rnd() < 0.5 ? 1 : -1, v: 0.9 + rnd() * 0.6, assis: surPlage && rnd() < 0.55, ph: rnd() * 6, curieux: rnd(),
    t0: 10 + rnd() * 4.5,
  };
  p.z0 = p.z; p.x0 = p.x;
  IJ.setColorAt(i, new THREE.Color(pick(bas))); IT.setColorAt(i, new THREE.Color(pick(hauts))); IH.setColorAt(i, new THREE.Color(pick(peau)));
  gens.push(p);
}
const o3 = new THREE.Object3D();
function poseGens(t) {
  gens.forEach((p, i) => {
    let assis = p.assis, x = p.x0, z = p.z0, cap = p.dir > 0 ? -Math.PI / 2 : Math.PI / 2, marche = 1;
    const reac = smooth((t - p.t0) / 2.5);                              // ils s'arrêtent et regardent la mer
    if (!p.surPlage) {
      const tStop = p.t0 + 1.2 * reac;
      x = p.x0 + p.dir * p.v * Math.min(t, tStop);
      if (p.curieux > 0.45) z = lerp(p.z0, 0.6 + (i % 5) * 0.35, smooth((t - p.t0 - 0.5) / 4));
      cap = lerp(cap, Math.PI, reac); marche = 1 - reac;
    } else {
      cap = Math.PI + (p.ph - 3) * 0.2;
      if (p.curieux > 0.5 && t > p.t0 + 2.5) {                             // les plus curieux descendent vers l'eau
        const u = t - p.t0 - 2.5; z = p.z0 - u * p.v * 1.1; marche = 1; assis = false;
      } else marche = assis ? 0 : 0.15;
    }
    const y = fond(x, z) > -0.1 || z > 0 ? 0.05 : fond(x, z) + 0.06;
    const bob = Math.abs(Math.sin(t * 7 * p.v + p.ph)) * 0.05 * marche;
    const hJ = assis ? 0.25 : 0.85;
    o3.rotation.set(0, cap, 0);
    o3.position.set(x, y + hJ / 2 + bob, z); o3.scale.set(1, hJ / 0.85, assis ? 2.2 : 1); o3.updateMatrix(); IJ.setMatrixAt(i, o3.matrix);
    o3.scale.set(1, 1, 1); o3.position.set(x, y + hJ + 0.31 + bob, z); o3.updateMatrix(); IT.setMatrixAt(i, o3.matrix);
    o3.position.set(x, y + hJ + 0.75 + bob, z); o3.updateMatrix(); IH.setMatrixAt(i, o3.matrix);
  });
  IJ.instanceMatrix.needsUpdate = IT.instanceMatrix.needsUpdate = IH.instanceMatrix.needsUpdate = true;
}
// voitures sur la Promenade
const voitures = [];
for (let i = 0; i < 30; i++) {
  const g = new THREE.Group(), c = new THREE.MeshStandardMaterial({ color: pick([0xf0f0f0, 0x1c1c1e, 0x8a9199, 0xb2382f, 0x2b4f7d, 0xd6d0c4]), roughness: 0.35, metalness: 0.5 });
  const b1 = new THREE.Mesh(new THREE.BoxGeometry(4.3, 0.8, 1.8), c); b1.position.y = 0.6; b1.castShadow = true;
  const b2 = new THREE.Mesh(new THREE.BoxGeometry(2.3, 0.6, 1.6), new THREE.MeshStandardMaterial({ color: 0x26323c, roughness: 0.15, metalness: 0.6 })); b2.position.set(-0.2, 1.25, 0);
  g.add(b1, b2); const voie = i % 2; g.userData = { x0: (rnd() - 0.5) * 1400, v: (voie ? 1 : -1) * (9 + rnd() * 4), z: voie ? 14.5 : 21 };
  scene.add(g); voitures.push(g);
}

// ---------- mer, écume, ciel, soleil ----------
const eau = new Water(new THREE.PlaneGeometry(14000, 14000), {
  textureWidth: 1024, textureHeight: 1024, waterNormals: normalesEau, sunDirection: new THREE.Vector3(),
  sunColor: 0xfff1d6, waterColor: 0x0e5f8a, distortionScale: 3.0, fog: true,
});
eau.rotation.x = -Math.PI / 2; scene.add(eau);
eau.material.uniforms.size.value = 3.0;
// Méditerranée vue d'en haut : moins de reflet du ciel pâle, plus de bleu profond
eau.material.fragmentShader = eau.material.fragmentShader
  .replace('float rf0 = 0.3;', 'float rf0 = 0.12;')
  .replace('pow( ( 1.0 - theta ), 5.0 )', 'pow( ( 1.0 - theta ), 5.0 ) * 0.7')
  .replace('vec3 scatter = max( 0.0, dot( surfaceNormal, eyeDirection ) ) * waterColor;',
           'vec3 scatter = ( 0.35 + 0.65 * max( 0.0, dot( surfaceNormal, eyeDirection ) ) ) * waterColor * 1.7;')
  .replace('reflectionSample * 0.9', 'reflectionSample * vec3( 0.7, 0.86, 1.0 ) * 0.9');
eau.material.needsUpdate = true;
const texEcume = canvasTex(1024, 64, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  for (let i = 0; i < 1800; i++) { const x = rnd() * w, y = h * 0.5 + (rnd() - 0.5) * h * 0.7 * rnd(); g.fillStyle = `rgba(255,255,255,${0.15 + rnd() * 0.5})`; g.beginPath(); g.ellipse(x, y, 3 + rnd() * 10, 1 + rnd() * 3, 0, 0, 7); g.fill(); }
}, [12, 1]);
const ecume = new THREE.Mesh(new THREE.PlaneGeometry(5200, 7, 400, 1), new THREE.MeshBasicMaterial({ map: texEcume, transparent: true, depthWrite: false, fog: true }));
ecume.rotation.x = -Math.PI / 2; scene.add(ecume);

// ciel : dôme en shader (dégradé, halo du soleil, cumulus en bruit fractal), couleurs données en sRGB
const sky = new THREE.Mesh(new THREE.SphereGeometry(11000, 48, 24), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false, toneMapped: false,
  uniforms: { sunDir: { value: new THREE.Vector3(0, 1, 0) }, soir: { value: 0 }, temps: { value: 0 } },
  vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); gl_Position.z = gl_Position.w; }`,
  fragmentShader: `
    varying vec3 vDir; uniform vec3 sunDir; uniform float soir; uniform float temps;
    float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
      return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
    float fbm(vec2 p){ float s = 0., a = .5; for (int k = 0; k < 6; k++){ s += a * n(p); p = p * 2.03 + 17.1; a *= .5; } return s; }
    void main(){
      vec3 d = normalize(vDir); float e = max(d.y, 0.);
      vec3 zen = mix(vec3(.20,.44,.78), vec3(.24,.36,.62), soir);
      vec3 hor = mix(vec3(.74,.85,.94), vec3(.98,.80,.62), soir);
      vec3 c = mix(hor, zen, pow(e, .45));
      float sd = max(dot(d, normalize(sunDir)), 0.);
      vec3 chaud = mix(vec3(1.,.95,.85), vec3(1.,.72,.42), soir);
      c += chaud * (pow(sd, 8.) * .35 + pow(sd, 90.) * .6) + chaud * smoothstep(.9994, .9997, sd) * 2.;
      // cumulus : projection sur un plafond nuageux
      if (d.y > .015) {
        vec2 q = d.xz / d.y * 1.6 + vec2(temps * .004, 0.);
        float m = fbm(q * .55);
        float nu = smoothstep(.52, .78, m) * smoothstep(.015, .09, d.y) * (1. - smoothstep(.45, .8, d.y));
        vec3 cn = mix(vec3(.97,.97,.98), vec3(1.,.86,.72), soir) * (.78 + .3 * fbm(q * 1.7)) ;
        cn = mix(cn, vec3(.62,.66,.74), smoothstep(.6, .9, m) * .45);
        c = mix(c, cn, nu * .92);
      }
      c = mix(c, hor, smoothstep(.03, .0, d.y));
      gl_FragColor = vec4(c, 1.);
    }`,
}));
scene.add(sky);
const soleil = new THREE.DirectionalLight(0xfff0dc, 3.2);
soleil.castShadow = true; soleil.shadow.mapSize.set(2048, 2048);
Object.assign(soleil.shadow.camera, { left: -120, right: 120, top: 120, bottom: -120, near: 1, far: 900 });
soleil.shadow.bias = -0.0004; scene.add(soleil, soleil.target);
const ciel = new THREE.HemisphereLight(0xbcd6f0, 0x8a7c66, 1.1); scene.add(ciel);
// ---------- image t ----------
const el = id => document.getElementById(id);
const fmtJour = h => { const H = Math.floor(h), M = Math.floor((h - H) * 60 + 1e-6); return `${H} h ${String(M).padStart(2, '0')} min`; };
window.frame = (t) => {
  // soleil : 14 h → environ 17 h 30 (azimut SO → O), le jour raccourcit
  const u = smooth(t / DUREE) * 0.5 + (t / DUREE) * 0.5;
  const elev = THREE.MathUtils.degToRad(lerp(33, 9, u)), azi = THREE.MathUtils.degToRad(lerp(205, 246, u));
  // azimut compté depuis le nord, sens horaire ; est = +x, nord = +z
  const sunDir = new THREE.Vector3(Math.sin(azi) * Math.cos(elev), Math.sin(elev), Math.cos(azi) * Math.cos(elev));
  sky.material.uniforms.sunDir.value.copy(sunDir); sky.material.uniforms.soir.value = smooth((u - 0.45) / 0.55); sky.material.uniforms.temps.value = t; sky.position.copy(camera.position);
  eau.material.uniforms.sunDirection.value.copy(sunDir).normalize();
  soleil.position.copy(camera.position).addScaledVector(sunDir, 400); soleil.target.position.copy(camera.position).add(new THREE.Vector3(-30, 0, -40));
  soleil.color.setHSL(0.09, lerp(0.2, 0.75, u), lerp(0.93, 0.78, u));
  soleil.intensity = lerp(3.2, 2.4, u);
  scene.fog.color.setRGB(...[0, 1, 2].map(i => lerp([.74, .85, .94][i], [.98, .80, .62][i], smooth((u - 0.45) / 0.55)))).convertSRGBToLinear();
  ciel.intensity = lerp(1.1, 0.8, u);

  // niveau de la mer
  const niveau = Y0 + 0.05 - visuel(t);
  eau.position.y = niveau;
  eau.material.uniforms.time.value = t * 0.6;
  let zs = PLAGE; while (fond(0, zs) > niveau && zs > PLAGE - 1400) zs -= 0.5;               // trait de côte
  ecume.position.set(0, niveau + 0.04, zs + 1.5 + Math.sin(t * 1.3) * 0.8);
  texEcume.offset.x = t * 0.01;
  bateaux.forEach(b => { const d = b.userData, flotte = niveau > d.fondY + 0.9;
    b.position.y = flotte ? niveau + Math.sin(t * 1.2 + d.phase) * 0.12 : d.fondY + 0.35;
    b.rotation.z = flotte ? Math.sin(t * 0.9 + d.phase) * 0.04 : d.tilt; });
  voitures.forEach(v => { const d = v.userData, ralenti = 1 - 0.85 * smooth((t - 12) / 4);
    v.position.set(((d.x0 + d.v * (t < 12 ? t : 12 + (t - 12) * ralenti)) + 1300) % 2600 - 1300, 0, d.z); v.rotation.y = d.v > 0 ? 0 : Math.PI; });
  poseGens(t);

  // caméra : léger travelling le long de la Promenade
  const k = t / DUREE;
  camera.position.set(lerp(46, 30, k), lerp(19, 21, k), lerp(31, 29, k));
  camera.lookAt(lerp(-40, -52, k), lerp(-5, -12, k), lerp(-70, -105, k));

  // incrustations
  el('jour').textContent = fmtJour(jourH(t));
  el('poids').textContent = `VOUS PESEZ ${poids(t).toFixed(2).replace('.', ',')} KG`;
  const b = baisse(t);
  el('mer').textContent = b < 0.5 ? 'LA MER EST À SON NIVEAU HABITUEL' : `LA MER A BAISSÉ DE ${b < 10 ? b.toFixed(1).replace('.', ',') : Math.round(b)} M`;
  const s = SOUS.find(([a, z]) => t >= a && t < z);
  const sous = el('sous');
  sous.innerHTML = s ? `<span>${s[2]}</span>` : '';
  sous.style.opacity = s ? Math.min(1, (t - s[0]) / 0.35, (s[1] - t) / 0.35) : 0;
  el('voileBas').style.opacity = sous.style.opacity;

  renderer.render(scene, camera);
  return true;
};
await document.fonts.ready;
window.frame(0);
window.pret = true;
