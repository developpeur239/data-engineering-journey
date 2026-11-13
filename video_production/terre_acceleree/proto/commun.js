// Outils communs aux décors (espace, navire, paris) : rendu, ciel, mer, physique, compteur, sous-titres, cartons.
// Le décor de Nice/Kourou (scene.js) garde son propre code, validé tel quel.
import * as THREE from 'three';
import { Water } from 'three/addons/objects/Water.js';

export const W = 1920, H = 1080;
export const PARAMS = new URLSearchParams(location.search);

// ---------- petits outils ----------
export function alea(graine = 7) {
  let s = graine;
  return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
}
export const lerp = (a, b, u) => a + (b - a) * u;
export const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
export const smooth = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
export const env = (pts, t) => {                                   // interpolation linéaire par points [t, v]
  if (t <= pts[0][0]) return pts[0][1];
  for (let i = 1; i < pts.length; i++) if (t <= pts[i][0]) return lerp(pts[i - 1][1], pts[i][1], (t - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0]));
  return pts[pts.length - 1][1];
};

// interpolation monotone (Fritsch–Carlson) : le compteur ne remonte jamais et n'a pas d'à-coups
export function pchip(pts) {
  const n = pts.length, x = pts.map(p => p[0]), y = pts.map(p => p[1]);
  const h = x.slice(1).map((v, i) => v - x[i]), d = h.map((hi, i) => (y[i + 1] - y[i]) / hi);
  const m = y.map((_, i) => i === 0 ? d[0] : i === n - 1 ? d[n - 2] : (d[i - 1] * d[i] <= 0 ? 0 : 3 * (h[i - 1] + h[i]) / ((2 * h[i] + h[i - 1]) / d[i - 1] + (h[i] + 2 * h[i - 1]) / d[i])));
  return t => {
    t = clamp(t, x[0], x[n - 1]); let i = 0; while (i < n - 2 && t > x[i + 1]) i++;
    const u = (t - x[i]) / h[i], u2 = u * u, u3 = u2 * u;
    return (2 * u3 - 3 * u2 + 1) * y[i] + (u3 - 2 * u2 + u) * h[i] * m[i] + (-2 * u3 + 3 * u2) * y[i + 1] + (u3 - u2) * h[i] * m[i + 1];
  };
}
// chemin de caméra continu (Catmull-Rom sur le temps) : points [t, position, visée]
export function chemin(ch, t, idx) {
  t = clamp(t, ch[0][0], ch[ch.length - 1][0]);
  let i = 0; while (i < ch.length - 2 && t > ch[i + 1][0]) i++;
  const P = k => ch[clamp(k, 0, ch.length - 1)];
  const t0 = P(i)[0], t1 = P(i + 1)[0], u = (t - t0) / (t1 - t0), u2 = u * u, u3 = u2 * u;
  return [0, 1, 2].map(c => {
    const p0 = P(i - 1)[idx][c], p1 = P(i)[idx][c], p2 = P(i + 1)[idx][c], p3 = P(i + 2)[idx][c];
    const m1 = (p2 - p0) / 2, m2 = (p3 - p1) / 2;
    return (2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2;
  });
}

// ---------- physique (même modèle que texte.md) ----------
const R = 6.371e6, REQ = 6.378e6, G = 9.81;
const dw2 = jourH => (2 * Math.PI / (jourH * 3600)) ** 2 - (2 * Math.PI / 86400) ** 2;
export const physique = {
  poids(latDeg, jourH) {                                          // kg ressentis (75 kg aujourd'hui)
    const p = latDeg * Math.PI / 180, d = dw2(jourH);
    const rad = G - d * R * Math.cos(p) ** 2, tan = d * R * Math.cos(p) * Math.sin(p);
    return Math.max(0, 75 * Math.hypot(rad, tan) / G * Math.sign(rad));
  },
  pente(latDeg, jourH) {                                          // degrés : le sol semble pencher vers l'équateur
    const p = latDeg * Math.PI / 180, d = dw2(jourH);
    return Math.atan2(d * R * Math.cos(p) * Math.sin(p), G - d * R * Math.cos(p) ** 2) * 180 / Math.PI;
  },
  mer(latDeg, jourH) {                                            // m (équilibre, Terre rigide) : + monte, − baisse
    const p = latDeg * Math.PI / 180;
    return R * R / (2 * G) * dw2(jourH) * (Math.cos(p) ** 2 - 2 / 3);
  },
  vitesseEquateur: jourH => 2 * Math.PI * REQ / (jourH * 3600) * 3.6,   // km/h
};

// ---------- compteur, sous-titres, cartons, noir ----------
const el = id => document.getElementById(id);
export function fmtJour(h) {
  if (h < 1) return `${Math.floor(h * 60 + 1e-6)} min`;
  const H = Math.floor(h), M = Math.floor((h - H) * 60 + 1e-6);
  return `${H} h ${String(M).padStart(2, '0')} min`;
}
export const fmtNombre = (x, dec = 0) => x.toLocaleString('fr-FR', { minimumFractionDigits: dec, maximumFractionDigits: dec }).replace(/ /g, ' ');
export function hud({ jour, poids, lieu, orange, visible = true }) {
  const v = visible ? 1 : 0;
  el('hud').style.opacity = v; el('voileHaut').style.opacity = v;
  if (!visible) return;
  el('jour').textContent = fmtJour(jour);
  el('poids').textContent = `VOUS PESEZ ${fmtNombre(poids, poids < 10 ? 1 : (poids >= 74.9 ? 2 : 1))} KG`;
  el('lieu').textContent = lieu;
  el('mer').textContent = orange || '';
}
export function sousTitres(t, liste) {
  const s = liste.find(([a, z]) => t >= a && t < z), sous = el('sous');
  sous.innerHTML = s ? `<span>${s[2]}</span>` : '';
  sous.style.opacity = s ? Math.min(1, (t - s[0]) / 0.35, (s[1] - t) / 0.35) : 0;
}
export function carton(t, liste) {                                // [début, fin, grand texte, petit texte]
  const c = liste.find(([a, z]) => t >= a && t < z), box = el('carton');
  box.innerHTML = c ? `<div class="t1">${c[2]}</div>${c[3] ? `<div class="t2">${c[3]}</div>` : ''}` : '';
  box.style.opacity = c ? Math.min(1, (t - c[0]) / 0.6, (c[1] - t) / 0.6) : 0;
}
export function noir(t, duree, entree = 0.5, sortie = 0.5) {     // fondus au noir en début / fin de séquence
  el('noir').style.opacity = Math.max(entree > 0 ? 1 - t / entree : 0, sortie > 0 ? 1 - (duree - t) / sortie : 0, 0);
}

// ---------- rendu ----------
export function moteur({ exposition = 0.62, ombres = true, brume = [0x9fc2e0, 900, 9000], fov = 42 } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = exposition;
  renderer.shadowMap.enabled = ombres; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  if (brume) scene.fog = new THREE.Fog(...brume);
  const camera = new THREE.PerspectiveCamera(fov, W / H, 0.5, 30000);
  return { renderer, scene, camera };
}
export function canvasTex(w, h, draw, repeat = [1, 1], srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
export function normalesEau(rnd) {                                // carte de normales tuilable : somme de sinus entiers
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
}
export function mer(scene, rnd, { couleur = 0x0e5f8a, taille = 3.0 } = {}) {
  const eau = new Water(new THREE.PlaneGeometry(30000, 30000), {
    textureWidth: 1024, textureHeight: 1024, waterNormals: normalesEau(rnd), sunDirection: new THREE.Vector3(),
    sunColor: 0xfff1d6, waterColor: couleur, distortionScale: 3.0, fog: true,
  });
  eau.rotation.x = -Math.PI / 2; scene.add(eau);
  eau.material.uniforms.size.value = taille;
  eau.material.fragmentShader = eau.material.fragmentShader
    .replace('float rf0 = 0.3;', 'float rf0 = 0.12;')
    .replace('pow( ( 1.0 - theta ), 5.0 )', 'pow( ( 1.0 - theta ), 5.0 ) * 0.7')
    .replace('vec3 scatter = max( 0.0, dot( surfaceNormal, eyeDirection ) ) * waterColor;',
             'vec3 scatter = ( 0.35 + 0.65 * max( 0.0, dot( surfaceNormal, eyeDirection ) ) ) * waterColor * 1.7;')
    .replace('reflectionSample * 0.9', 'reflectionSample * vec3( 0.7, 0.86, 1.0 ) * 0.9');
  eau.material.needsUpdate = true;
  return eau;
}
// ciel de jour (même shader que Nice) ; nuit : le ciel s'assombrit avec `nuit` (0–1), étoiles comprises
export function ciel(scene) {
  const sky = new THREE.Mesh(new THREE.SphereGeometry(20000, 48, 24), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false, toneMapped: false,
    uniforms: { sunDir: { value: new THREE.Vector3(0, 1, 0) }, soir: { value: 0 }, temps: { value: 0 }, nuit: { value: 0 }, nuages: { value: 1 } },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); gl_Position.z = gl_Position.w; }`,
    fragmentShader: `
      varying vec3 vDir; uniform vec3 sunDir; uniform float soir; uniform float temps; uniform float nuit; uniform float nuages;
      float h(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
      float n(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
        return mix(mix(h(i), h(i+vec2(1,0)), f.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), f.x), f.y); }
      float fbm(vec2 p){ float s = 0., a = .5; for (int k = 0; k < 6; k++){ s += a * n(p); p = p * 2.03 + 17.1; a *= .5; } return s; }
      void main(){
        vec3 d = normalize(vDir); float e = max(d.y, 0.);
        vec3 zen = mix(vec3(.20,.44,.78), vec3(.24,.36,.62), soir);
        float cote = pow(max(dot(normalize(d.xz + 1e-4), normalize(sunDir.xz + 1e-4)), 0.), 7.);
        float chaudH = soir * (.25 + .75 * cote);
        vec3 hor = mix(vec3(.74,.85,.94), vec3(.98,.80,.62), chaudH);
        vec3 c = mix(hor, zen, pow(e, .45));
        float sd = max(dot(d, normalize(sunDir)), 0.);
        vec3 chaud = mix(vec3(1.,.95,.85), vec3(1.,.72,.42), soir);
        c += chaud * (pow(sd, 8.) * .35 + pow(sd, 90.) * .6) + chaud * smoothstep(.9994, .9997, sd) * 2.;
        if (d.y > .015) {
          vec2 q = d.xz / d.y * 1.6 + vec2(temps * .004, 0.);
          float m = fbm(q * .55);
          float nu = smoothstep(.52, .78, m) * smoothstep(.015, .09, d.y) * (1. - smoothstep(.45, .8, d.y)) * nuages;
          vec3 cn = mix(vec3(.97,.97,.98), vec3(1.,.86,.72), soir) * (.78 + .3 * fbm(q * 1.7));
          cn = mix(cn, vec3(.62,.66,.74), smoothstep(.6, .9, m) * .45);
          c = mix(c, cn, nu * .92);
        }
        c = mix(c, hor, smoothstep(.03, .0, d.y));
        // nuit : ciel bleu nuit et étoiles
        vec3 cn2 = mix(vec3(.03,.05,.11), vec3(.06,.09,.18), 1. - e);
        float etoile = step(.9975, h(floor(d.xz / max(d.y, .05) * 380.))) * smoothstep(.05, .2, d.y);
        cn2 += vec3(etoile) * .9;
        c = mix(c, cn2, nuit);
        gl_FragColor = vec4(c, 1.);
      }`,
  }));
  scene.add(sky);
  return sky;
}
// direction du soleil : azimut depuis le nord (horaire) ; repère nord = +z, ouest = +x
export const dirSoleil = (elevDeg, aziDeg) => {
  const e = elevDeg * Math.PI / 180, a = aziDeg * Math.PI / 180;
  return new THREE.Vector3(-Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e));
};

// ---------- personnages simples (instances : jambes, torse, tête) ----------
export function foule(scene, n, rnd) {
  const peau = [0xf1c9a5, 0xd9a47c, 0xa8724f, 0x6e4a33, 0xe8b893];
  const hauts = [0xe24b3b, 0x2e6fb7, 0xf2f2ee, 0xf2c330, 0x3a9d6a, 0x1f2a3a, 0xe58ab2, 0xf28c28, 0x7a4fa3, 0x19a7c4];
  const bas = [0x2b3a55, 0x3b3b3b, 0xd9c9a3, 0x1f4d7a, 0x6b5a45, 0xf0f0ea];
  const pick = a => a[Math.floor(rnd() * a.length)];
  const mk = geo => { const m = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.75 }), n); m.castShadow = true; m.receiveShadow = true; scene.add(m); return m; };
  const J = mk(new THREE.BoxGeometry(0.34, 0.85, 0.22)), T = mk(new THREE.BoxGeometry(0.46, 0.62, 0.26)), Te = mk(new THREE.SphereGeometry(0.13, 10, 8));
  for (let i = 0; i < n; i++) { J.setColorAt(i, new THREE.Color(pick(bas))); T.setColorAt(i, new THREE.Color(pick(hauts))); Te.setColorAt(i, new THREE.Color(pick(peau))); }
  const o = new THREE.Object3D();
  return {
    // pose une personne : position des pieds, cap (rad), inclinaison (rad, autour de l'axe x local), échelle (0 = masquée)
    pose(i, x, y, z, cap = 0, incl = 0, ech = 1, bob = 0) {
      o.rotation.set(incl, cap, 0, 'YXZ');
      const up = new THREE.Vector3(0, 1, 0).applyEuler(o.rotation);
      const at = h => [x + up.x * h, y + up.y * h + bob, z + up.z * h];
      o.scale.setScalar(ech);
      o.position.set(...at(0.425)); o.updateMatrix(); J.setMatrixAt(i, o.matrix);
      o.position.set(...at(1.16)); o.updateMatrix(); T.setMatrixAt(i, o.matrix);
      o.position.set(...at(1.6)); o.updateMatrix(); Te.setMatrixAt(i, o.matrix);
    },
    maj() { J.instanceMatrix.needsUpdate = T.instanceMatrix.needsUpdate = Te.instanceMatrix.needsUpdate = true; },
  };
}

// ---------- tic-tac : le son lit le compteur ----------
export function exposer({ duree, jour, etat, frame }) {
  window.DUREE = duree;
  window.jourSeq = jour;
  window.etat = etat;
  window.frame = frame;
}
