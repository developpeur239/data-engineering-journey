// Décor « espace » : ouverture (flash-forward), séquence 3 (océans vers l'équateur), séquence 8 (l'anneau), cartons de fin.
// ?scene=espace&seq=ouverture|espace|anneau|fin
import * as THREE from 'three';
import { PARAMS, alea, lerp, clamp, smooth, env, pchip, physique, fmtNombre, hud, sousTitres, carton, noir, moteur, exposer } from './commun.js';

const rnd = alea(23);
const SEQS = {
  ouverture: { duree: 7, jour: [[0, 0.99], [7, 0.983]], k: 1, anneau: 1, hud: false, entree: 0, sortie: 0.8,
               sous: [[0.6, 6.2, 'Dans 8 minutes, voici la Terre.']],
               cam: [[0, 4700, 0.30, -0.9], [7, 4500, 0.28, -0.75]] },
  espace: { duree: 50, jour: [[0, 22], [12, 20], [25, 18 + 1 / 3], [50, 12]], k: [[0, 0.04], [50, 0.62]], anneau: 0, hud: true, entree: 0.6, sortie: 0.6,
            sous: [[0.8, 11, 'Vue de l’espace, les pôles se vident…'], [12, 23.5, '…et les océans s’entassent autour de l’équateur.'],
                   [25, 37, 'Le nord de la Méditerranée est à sec.'], [39.5, 49.3, 'Une journée ne dure plus que 12 heures.']],
            cam: [[0, 4300, 0.70, 0.35], [50, 4000, 0.45, 0.25]] },                 // [t, distance, latitude (rad), longitude]
  anneau: { duree: 50, jour: [[0, 1 + 20 / 60], [20, 1 + 5 / 60], [35, 1.0], [50, 0.983]], k: 1, anneau: [[0, 0.02], [12, 0.25], [35, 0.85], [50, 1]],
            hud: true, entree: 0.6, sortie: 1.6,
            sous: [[1, 14, 'La Terre commence à jeter son équateur dans l’espace.'], [16, 30, 'Des roches, de l’eau, des villes.'],
                   [34, 46.5, 'Plus rien ne la retient.']],
            cam: [[0, 4200, 0.12, 0.2], [50, 4800, 0.36, -0.6]] },
  fin: { duree: 20, jour: [[0, 0.983], [20, 0.983]], k: 1, anneau: 1, hud: false, entree: 0, sortie: 0.8, noirFond: true, sous: [],
         cartons: [[0.6, 6.4, 'Est-ce que c’est réel ?'],
                   [7, 13.8, 'Non.', 'En réalité, la Terre ralentit : la Lune freine sa rotation,<br>et la journée s’allonge d’environ 2 millièmes de seconde par siècle.'],
                   [14.4, 19.6, 'Et si la Lune tombait sur la Terre ?', 'Le film est sur la chaîne.']],
         cam: [[0, 3300, 0.3, 0], [20, 3300, 0.3, 0]] },
};
const SEQ = SEQS[PARAMS.get('seq') || 'espace'];
if (PARAMS.get('rot')) SEQ.rot0 = +PARAMS.get('rot');
const D = SEQ.duree;
const jourH = pchip(SEQ.jour);
const val = (v, t) => (typeof v === 'number' ? v : env(v, t));

const { renderer, scene, camera } = moteur({ exposition: 0.9, ombres: false, brume: null, fov: 34 });
scene.background = new THREE.Color(0x000000);

// étoiles
{
  const n = 9000, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) { const v = new THREE.Vector3(rnd() - .5, rnd() - .5, rnd() - .5).normalize().multiplyScalar(15000); pos.set([v.x, v.y, v.z], i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xcfd8ff, size: 1.6, sizeAttenuation: false, transparent: true, opacity: 0.75 })));
}

// la Terre : texture NASA ; les océans quittent les hautes latitudes et s'entassent sur l'équateur (k : 0 → 1)
const RT = 1000;
const texTerre = new THREE.TextureLoader().load('textures/terre_bluemarble_nasa.png');
texTerre.colorSpace = THREE.SRGBColorSpace; texTerre.anisotropy = 8;
const matTerre = new THREE.ShaderMaterial({
  uniforms: { carte: { value: texTerre }, k: { value: 0 }, soleil: { value: new THREE.Vector3(1, 0.2, 0.4).normalize() }, fonte: { value: 0 } },
  vertexShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vNo;
    void main(){ vUv = uv; vNo = normalize(position); vN = normalize(mat3(modelMatrix) * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }`,
  fragmentShader: `
    uniform sampler2D carte; uniform float k; uniform vec3 soleil; uniform float fonte;
    varying vec2 vUv; varying vec3 vN; varying vec3 vNo;
    vec3 lin(vec3 c){ return pow(c, vec3(2.2)); }
    void main(){
      vec3 c = texture2D(carte, vUv).rgb;
      float lat = degrees(asin(clamp(vNo.y, -1., 1.)));
      float ocean = smoothstep(.02, .10, c.b - max(c.r, c.g) * .85) * (1. - smoothstep(.75, .95, c.r + c.g));
      float seuil = 90. - 72. * k;                                   // au-delà, l'océan s'est vidé
      float vide = ocean * smoothstep(seuil - 4., seuil + 4., abs(lat));
      vec3 fondNu = vec3(.30, .26, .21) * (.7 + .6 * c.g);           // fond marin découvert
      c = mix(c, fondNu, vide);
      float bande = 6. + 26. * k;                                   // ceinture d'eau qui grossit à l'équateur
      float noye = (1. - ocean) * smoothstep(bande + 3., bande - 3., abs(lat)) * smoothstep(.15, .5, k);
      c = mix(c, vec3(.03, .14, .32), noye * .92);
      c = mix(c, c * vec3(.75, .9, 1.2), ocean * (1. - vide) * smoothstep(bande + 6., 0., abs(lat)) * k);
      c = mix(c, vec3(1., .42, .12) * (.6 + .4 * fract(sin(dot(vUv, vec2(91.3, 17.7))) * 4375.)), fonte * smoothstep(20., 0., abs(lat)));
      float l = max(dot(vN, soleil), 0.);
      vec3 col = lin(c) * (0.05 + 1.7 * l) + vec3(.004, .01, .025) * ocean * l;
      gl_FragColor = vec4(col, 1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
});
const terre = new THREE.Mesh(new THREE.SphereGeometry(RT, 160, 96), matTerre);
scene.add(terre);
// atmosphère : liseré bleu sur le bord éclairé
const atmo = new THREE.Mesh(new THREE.SphereGeometry(RT * 1.025, 96, 64), new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, side: THREE.BackSide, blending: THREE.AdditiveBlending,
  uniforms: { soleil: matTerre.uniforms.soleil },
  vertexShader: `varying vec3 vN; varying vec3 vV; void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position,1.); vV = normalize(cameraPosition - w.xyz); gl_Position = projectionMatrix * viewMatrix * w; }`,
  fragmentShader: `uniform vec3 soleil; varying vec3 vN; varying vec3 vV;
    void main(){ float r = pow(1. - abs(dot(vN, vV)), 3.); float l = clamp(dot(-vN, soleil) * .7 + .4, 0., 1.); gl_FragColor = vec4(vec3(.35,.6,1.) * r * l * 1.4, r * l); }`,
}));
scene.add(atmo);

// l'anneau : débris (roches, glace, morceaux de croûte) en orbite dans le plan de l'équateur
const ND = 2600, NP = 26000;
const debris = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1, 0), new THREE.MeshStandardMaterial({ roughness: 0.95 }), ND);
const dd = [];
const teintes = [0x6b5a48, 0x8a7a66, 0x4e4a46, 0x9a8f80, 0x5d6f7d, 0xb9c4cc];
for (let i = 0; i < ND; i++) {
  dd.push({ r: RT * (1.12 + rnd() * 0.75), a: rnd() * Math.PI * 2, h: (rnd() - 0.5) * 30, s: 1.5 + rnd() ** 4 * 11, seuil: rnd(), rot: rnd() * 6 });
  debris.setColorAt(i, new THREE.Color(teintes[Math.floor(rnd() * teintes.length)]));
}
scene.add(debris);
const poussiere = (() => {
  const pos = new Float32Array(NP * 3), meta = [];
  for (let i = 0; i < NP; i++) meta.push([RT * (1.06 + rnd() * 0.95), rnd() * Math.PI * 2, (rnd() - 0.5) * 18, rnd()]);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const p = new THREE.Points(g, new THREE.PointsMaterial({ color: 0xb8a58c, size: 2.2, sizeAttenuation: false, transparent: true, opacity: 0.55, depthWrite: false }));
  scene.add(p); return { p, pos, meta };
})();
const lumiere = new THREE.DirectionalLight(0xfff4e6, 3.0); scene.add(lumiere);
scene.add(new THREE.AmbientLight(0x223044, 0.35));

// rotation propre de la Terre : on l'accumule (elle tourne de plus en plus vite)
const spin = t => { let a = 0; const n = 200; for (let i = 0; i < n; i++) { const u = (i + 0.5) / n * t; a += 0.012 * (24 / jourH(u)) ** 0.55 * (t / n); } return a; };

function frame(t) {
  const jour = jourH(t), k = val(SEQ.k, t), an = val(SEQ.anneau, t);
  // aplatissement (sphéroïde d'équilibre ≈ 1,25·ω²R/g), plafonné
  const q = (2 * Math.PI / (jour * 3600)) ** 2 * 6.371e6 / 9.81;
  const f = Math.min(0.34, 1.25 * q * 0.8);
  terre.scale.set(1, 1 - f, 1); atmo.scale.set(1, 1 - f, 1);
  terre.rotation.y = (SEQ.rot0 ?? 4.0) + spin(t); atmo.rotation.y = terre.rotation.y;
  matTerre.uniforms.k.value = k;
  matTerre.uniforms.fonte.value = SEQ === SEQS.anneau ? smooth((t - 22) / 26) * 0.3 : (an > 0.9 ? 0.3 : 0);
  // anneau
  const o = new THREE.Object3D();
  dd.forEach((d, i) => {
    const vis = an > d.seuil ? 1 : 0;
    const w = 0.05 * Math.sqrt((RT * 1.2 / d.r) ** 3);
    const a = d.a + w * t * 4 + (SEQ === SEQS.anneau ? 0 : 1.7);
    const r = lerp(RT * (1 - f * 0.2), d.r, smooth((an - d.seuil) / 0.25));    // les débris montent depuis l'équateur
    o.position.set(Math.cos(a) * r, d.h * (1 - f), Math.sin(a) * r);
    o.rotation.set(d.rot + t * 0.3, d.rot * 2 + t * 0.2, 0);
    o.scale.setScalar(d.s * vis);
    o.updateMatrix(); debris.setMatrixAt(i, o.matrix);
  });
  debris.instanceMatrix.needsUpdate = true;
  poussiere.meta.forEach(([r0, a0, h, s], i) => {
    const vis = an > s ? 1 : 0, a = a0 + 0.05 * Math.sqrt((RT * 1.2 / r0) ** 3) * t * 4, r = lerp(RT, r0, smooth((an - s) / 0.25));
    poussiere.pos.set(vis ? [Math.cos(a) * r, h, Math.sin(a) * r] : [0, 0, 0], i * 3);
  });
  poussiere.p.geometry.attributes.position.needsUpdate = true;
  // caméra en orbite lente
  const c0 = SEQ.cam[0], c1 = SEQ.cam[SEQ.cam.length - 1], u = smooth(t / D) * 0.5 + (t / D) * 0.5;
  const dist = lerp(c0[1], c1[1], u), lat = lerp(c0[2], c1[2], u), lon = lerp(c0[3], c1[3], u);
  camera.position.set(Math.cos(lat) * Math.sin(lon) * dist, Math.sin(lat) * dist, Math.cos(lat) * Math.cos(lon) * dist);
  camera.lookAt(0, 120, 0);
  // soleil du côté de la caméra, un peu à gauche et en haut : on voit la face éclairée, avec un terminateur sur la droite
  const vc = camera.position.clone().normalize(), droite = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), vc).normalize();
  const sol = vc.clone().multiplyScalar(0.8).addScaledVector(droite, -0.55).add(new THREE.Vector3(0, 0.3, 0)).normalize();
  matTerre.uniforms.soleil.value.copy(sol); lumiere.position.copy(sol).multiplyScalar(5000);
  terre.visible = atmo.visible = debris.visible = poussiere.p.visible = !SEQ.noirFond;
  // incrustations
  const v = physique.vitesseEquateur(jour);
  const comp = jour > 18.4 ? 'PLUS VITE QUE LE SON' : jour > 13.1 ? 'PLUS VITE QUE LE CONCORDE'
             : jour > 1.45 ? 'PLUS VITE QU’UNE BALLE DE FUSIL' : jour > 1.0 ? 'VITESSE D’UN SATELLITE' : 'AU-DELÀ DE LA VITESSE DE LIBÉRATION';
  hud({ visible: SEQ.hud, jour, poids: physique.poids(0, jour), lieu: SEQ === SEQS.anneau ? 'À L’ÉQUATEUR' : 'LA TERRE · À L’ÉQUATEUR',
        orange: `L’ÉQUATEUR : ${fmtNombre(Math.round(v / 10) * 10)} KM/H · ${comp}` });
  sousTitres(t, SEQ.sous);
  carton(t, SEQ.cartons || []);
  noir(t, D, SEQ.entree, SEQ.sortie);
  renderer.render(scene, camera);
  return true;
}
exposer({ duree: D, jour: jourH, frame, etat: t => ({ t, jour: jourH(t), k: val(SEQ.k, t), anneau: val(SEQ.anneau, t) }) });
await document.fonts.ready;
await new Promise(r => { const tst = () => (texTerre.image ? r() : setTimeout(tst, 50)); tst(); });
frame(0);
window.pret = true;
