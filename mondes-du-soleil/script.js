/* ==================================================================
   Mondes du Soleil · page d'accueil
   Script unique, classique et différé (defer) : fonctionne aussi quand
   la page est ouverte directement depuis le disque (file://).
   Tout est enveloppé dans une fonction pour ne rien exposer en global
   (pas de conflit avec les scripts de WordPress).
   Sommaire :
     0. Configuration (FRAME_URLS)
     1. En-tête : menu burger
     2. Apparitions au scroll
     3. Hero : progression du scroll et textes
     4. Hero : séquence d'images (si FRAME_URLS est rempli)
     5. Hero : scène 3D Three.js
     5b. Hero : bonhomme (salut au lever du soleil, regard qui suit le curseur)
     6. Démarrage
   ================================================================== */

/* ------------------------------------------------------------------
   0. CONFIGURATION
   La vidéo réaliste et le bonhomme sont décrits dans assets/medias.js,
   généré par outils/preparer-medias.py (voir MEDIAS.md).
   FRAME_URLS peut aussi être rempli à la main : s'il contient des
   images, la séquence remplace la scène 3D.
   ------------------------------------------------------------------ */
(() => {
"use strict";

const MEDIAS = window.MDS_MEDIAS || {};
const SEQUENCE = MEDIAS.sequence || {};
const FRAME_URLS = (window.matchMedia("(max-width: 767px)").matches && SEQUENCE.mobile?.length
  ? SEQUENCE.mobile
  : SEQUENCE.ordinateur) || [];

const LISSAGE = 0.08;            // part de l'écart rattrapée à chaque image (60 i/s)
// Three.js (version réduite aux classes utilisées), chargé à la demande.
// Le chemin est résolu à partir de script.js, où que la page soit intégrée.
// (Dans l'aperçu autonome, le script est intégré à la page : on se rabat sur l'URL de la page.)
const BASE_SCRIPT = (document.currentScript && document.currentScript.src) || location.href;
const CHEMIN_THREE = new URL("vendor/three.min.js", BASE_SCRIPT).href;

const racine = document.documentElement;
racine.classList.add("module-ok"); // signale au <head> que le script s'exécute bien
const reduireMouvement = window.matchMedia("(prefers-reduced-motion: reduce)");
const ecranLeger = window.matchMedia("(max-width: 767px)").matches
  || (navigator.hardwareConcurrency || 8) <= 4;

/* Aperçu en double-clic (file://) : polices déclarées depuis un script,
   car Chrome bloque les fichiers de police lus sur le disque */
if (location.protocol === "file:" && !document.documentElement.hasAttribute("data-autonome")) {
  const balise = document.createElement("script");
  balise.src = new URL("vendor/polices-hors-ligne.js", BASE_SCRIPT).href;
  document.head.appendChild(balise);
}

/* Petits outils mathématiques */
const borner = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v));
const interpoler = (a, b, t) => a + (b - a) * t;
const lisser = (a, b, v) => { const t = borner((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const sortieCubique = (t) => 1 - Math.pow(1 - t, 3);
const sinusoidal = (t) => 0.5 - 0.5 * Math.cos(Math.PI * t);

/* ------------------------------------------------------------------
   1. EN-TÊTE : MENU BURGER
   ------------------------------------------------------------------ */
function initialiserMenu() {
  const bouton = document.querySelector(".burger");
  const nav = document.getElementById("nav-principale");
  if (!bouton || !nav) return;

  const basculer = (ouvrir) => {
    bouton.setAttribute("aria-expanded", String(ouvrir));
    bouton.setAttribute("aria-label", ouvrir ? "Fermer le menu" : "Ouvrir le menu");
    nav.classList.toggle("nav--ouverte", ouvrir);
  };

  bouton.addEventListener("click", () => basculer(bouton.getAttribute("aria-expanded") !== "true"));

  // Fermeture : touche Échap, clic sur un lien, passage en affichage large
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav.classList.contains("nav--ouverte")) {
      basculer(false);
      bouton.focus();
    }
  });
  nav.addEventListener("click", (e) => { if (e.target.closest("a")) basculer(false); });
  window.matchMedia("(min-width: 1100px)").addEventListener("change", (e) => { if (e.matches) basculer(false); });
}

/* ------------------------------------------------------------------
   2. APPARITIONS AU SCROLL
   ------------------------------------------------------------------ */
function initialiserApparitions() {
  const elements = document.querySelectorAll(".apparition");
  if (reduireMouvement.matches || !("IntersectionObserver" in window)) {
    elements.forEach((el) => el.classList.add("est-visible"));
    return;
  }
  const observateur = new IntersectionObserver((entrees) => {
    for (const entree of entrees) {
      if (!entree.isIntersecting) continue;
      entree.target.classList.add("est-visible");
      observateur.unobserve(entree.target);
    }
  }, { rootMargin: "0px 0px -10% 0px", threshold: 0.1 });
  elements.forEach((el) => observateur.observe(el));
}

/* ------------------------------------------------------------------
   3. HERO : PROGRESSION DU SCROLL ET TEXTES
   La progression brute (0 → 1) est lue au scroll, puis lissée à chaque
   image. Le rendu (3D ou séquence) reçoit la valeur lissée.
   ------------------------------------------------------------------ */
const hero = document.getElementById("hero");
const scene = hero?.querySelector(".hero__scene");
const canvas = hero?.querySelector(".hero__canvas");
const temps = hero ? [...hero.querySelectorAll(".hero__temps")] : [];

/* Fenêtres d'apparition des trois textes : [début entrée, fin entrée, début sortie, fin sortie] */
const FENETRES_TEXTES = [
  [-1, 0, 0.16, 0.24],
  [0.30, 0.38, 0.56, 0.63],
  [0.70, 0.78, 2, 3],
];

function progressionBrute() {
  const rect = hero.getBoundingClientRect();
  const course = hero.offsetHeight - scene.offsetHeight;
  const decalage = parseFloat(getComputedStyle(scene).top) || 0;
  return course > 0 ? borner((decalage - rect.top) / course) : 0;
}

function mettreAJourTextes(p) {
  temps.forEach((el, i) => {
    const [a, b, c, d] = FENETRES_TEXTES[i];
    const opacite = Math.min(lisser(a, b, p), 1 - lisser(c, d, p));
    el.style.opacity = opacite.toFixed(3);
    el.style.visibility = opacite < 0.02 ? "hidden" : "visible";
    el.style.translate = `0 ${((1 - opacite) * 16).toFixed(1)}px`;
  });
}

/* Autres éléments qui suivent la progression lissée (le bonhomme) */
const suiveursProgression = [];

/**
 * Boucle de rendu commune : interpole la progression et n'appelle
 * `dessiner` que lorsque la valeur bouge et que le hero est à l'écran.
 */
function lancerBoucle(dessiner) {
  let cible = progressionBrute();
  let courant = cible;
  let visible = true;
  let enCours = false;
  let dernierTemps = performance.now();

  const image = (maintenant) => {
    // L'horodatage de rAF peut précéder performance.now() : écart borné à [0, 64] ms
    const dt = borner(maintenant - dernierTemps, 0, 64) / (1000 / 60);
    dernierTemps = maintenant;
    courant = interpoler(courant, cible, 1 - Math.pow(1 - LISSAGE, dt));
    if (Math.abs(cible - courant) < 0.0004) courant = cible;

    mettreAJourTextes(courant);
    suiveursProgression.forEach((f) => f(courant));
    dessiner(courant);

    if (courant !== cible && visible) requestAnimationFrame(image);
    else enCours = false;
  };

  const relancer = () => {
    if (enCours || !visible) return;
    enCours = true;
    dernierTemps = performance.now();
    requestAnimationFrame(image);
  };

  window.addEventListener("scroll", () => { cible = progressionBrute(); relancer(); }, { passive: true });
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; relancer(); }).observe(hero);

  // Premier rendu immédiat
  mettreAJourTextes(courant);
  suiveursProgression.forEach((f) => f(courant));
  dessiner(courant);
  return { redessiner: () => dessiner(courant) };
}

/* ------------------------------------------------------------------
   4. HERO : SÉQUENCE D'IMAGES (FRAME_URLS)
   ------------------------------------------------------------------ */
function demarrerSequence(urls) {
  const ctx = canvas.getContext("2d");
  const images = urls.map((url) => { const img = new Image(); img.decoding = "async"; img.src = url; return img; });
  let indexAffiche = -1;

  const dimensionner = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(scene.clientWidth * ratio);
    canvas.height = Math.round(scene.clientHeight * ratio);
    indexAffiche = -1;
  };

  // Dessin en mode « cover » : l'image remplit le canvas sans déformation
  const dessiner = (p) => {
    let index = Math.round(borner(p) * (images.length - 1));
    // Si l'image voulue n'est pas encore chargée, on affiche la plus proche déjà prête
    while (index > 0 && !images[index].complete) index--;
    const img = images[index];
    if (!img.complete || !img.naturalWidth || index === indexAffiche) return;
    indexAffiche = index;
    const echelle = Math.max(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
    const l = img.naturalWidth * echelle;
    const h = img.naturalHeight * echelle;
    ctx.drawImage(img, (canvas.width - l) / 2, (canvas.height - h) / 2, l, h);
  };

  dimensionner();
  const boucle = lancerBoucle(dessiner);
  new ResizeObserver(() => { dimensionner(); boucle.redessiner(); }).observe(scene);
  images[0].addEventListener("load", () => { boucle.redessiner(); canvas.classList.add("est-pret"); }, { once: true });
}

/* ------------------------------------------------------------------
   5. HERO : SCÈNE 3D THREE.JS
   Chronologie (progression p de 0 à 1) :
     0,00 → 1,00  la caméra tourne lentement autour de la maison
     0,18 → 0,58  les dix panneaux se posent un à un sur le toit
     0,55 → 0,90  le soleil se lève ; reflets sur les panneaux
     0,82 → 0,97  la maison s'illumine de l'intérieur
   ------------------------------------------------------------------ */
function webglDisponible() {
  try {
    const test = document.createElement("canvas");
    return !!(test.getContext("webgl2") || test.getContext("webgl"));
  } catch {
    return false;
  }
}

/* Rend la main au navigateur entre deux étapes d'initialisation (pas de tâche longue) */
const pause = () => new Promise((r) => (window.requestIdleCallback ? requestIdleCallback(() => r(), { timeout: 120 }) : setTimeout(r, 16)));

/* Charge Three.js par une balise <script> classique (compatible file://) */
function chargerThree() {
  if (window.THREE) return Promise.resolve(window.THREE);
  return new Promise((resoudre, rejeter) => {
    const balise = document.createElement("script");
    balise.src = CHEMIN_THREE;
    balise.async = true;
    balise.onload = () => (window.THREE ? resoudre(window.THREE) : rejeter(new Error("Three.js indisponible")));
    balise.onerror = rejeter;
    document.head.appendChild(balise);
  });
}

async function demarrer3D() {
  const THREE = await chargerThree();
  await pause();
  const leger = ecranLeger;

  /* --- Rendu --- */
  const rendu = new THREE.WebGLRenderer({ canvas, antialias: !leger, powerPreference: "high-performance" });
  rendu.setPixelRatio(Math.min(window.devicePixelRatio || 1, leger ? 1.5 : 2));
  rendu.outputColorSpace = THREE.SRGBColorSpace;
  rendu.toneMapping = THREE.ACESFilmicToneMapping;
  rendu.toneMappingExposure = 1.0;
  if (!leger) {
    rendu.shadowMap.enabled = true;
    rendu.shadowMap.type = THREE.PCFSoftShadowMap;
    rendu.shadowMap.autoUpdate = false; // ombres recalculées seulement quand le soleil est levé
  }

  const monde = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.5, 500);

  /* --- Couleurs de la chronologie (nuit → aube → matin) --- */
  const C = (hex) => new THREE.Color(hex);
  const CIEL_HAUT = [C("#07090D"), C("#1C2640"), C("#3F5F8C")];
  const CIEL_HORIZON = [C("#121824"), C("#E2823A"), C("#EDB27E")];
  const tempCouleur = new THREE.Color();
  const melanger = (palette, t, cible = tempCouleur) => (t < 0.5
    ? cible.copy(palette[0]).lerp(palette[1], t * 2)
    : cible.copy(palette[1]).lerp(palette[2], (t - 0.5) * 2));

  /* --- Ciel : dégradé + disque solaire calculés dans un shader --- */
  const uniformesCiel = {
    uHaut: { value: CIEL_HAUT[0].clone() },
    uHorizon: { value: CIEL_HORIZON[0].clone() },
    uDirSoleil: { value: new THREE.Vector3(0, -0.1, -1).normalize() },
    uEclat: { value: 0 },
  };
  const materiauCiel = new THREE.ShaderMaterial({
    uniforms: uniformesCiel,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    vertexShader: /* glsl */`
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: /* glsl */`
      uniform vec3 uHaut;
      uniform vec3 uHorizon;
      uniform vec3 uDirSoleil;
      uniform float uEclat;
      varying vec3 vDir;
      void main() {
        vec3 d = normalize(vDir);
        float h = max(d.y, 0.0);
        vec3 couleur = mix(uHorizon, uHaut, pow(h, 0.55));
        float alignement = max(dot(d, normalize(uDirSoleil)), 0.0);
        couleur += vec3(1.0, 0.62, 0.25) * pow(alignement, 12.0) * 0.55 * uEclat;
        couleur += vec3(1.0, 0.86, 0.55) * pow(alignement, 180.0) * 1.2 * uEclat;
        couleur += vec3(1.0, 0.95, 0.8) * smoothstep(0.9993, 0.9997, alignement) * 3.0 * uEclat;
        gl_FragColor = vec4(couleur, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  const ciel = new THREE.Mesh(new THREE.SphereGeometry(220, 32, 16), materiauCiel);
  monde.add(ciel);
  monde.fog = new THREE.Fog(CIEL_HORIZON[0].clone(), 45, 150);

  /* --- Environnement réfléchi par les panneaux (ciel seul, régénéré par paliers) --- */
  const pmrem = new THREE.PMREMGenerator(rendu);
  const sceneReflets = new THREE.Scene();
  sceneReflets.add(new THREE.Mesh(new THREE.SphereGeometry(40, 32, 16), materiauCiel));
  let cibleReflets = null;
  let paletteReflets = -1;
  let refletsActifs = false; // activés après le premier rendu, pour ne pas bloquer le démarrage
  const majReflets = (t) => {
    if (!refletsActifs) return;
    const palier = Math.round(t * (leger ? 6 : 16));
    if (palier === paletteReflets) return;
    paletteReflets = palier;
    const nouvelle = pmrem.fromScene(sceneReflets, 0.02);
    monde.environment = nouvelle.texture;
    cibleReflets?.dispose();
    cibleReflets = nouvelle;
  };

  await pause();

  /* --- Étoiles --- */
  const nbEtoiles = leger ? 160 : 420;
  const positions = new Float32Array(nbEtoiles * 3);
  for (let i = 0; i < nbEtoiles; i++) {
    const az = Math.random() * Math.PI * 2;
    const el = 0.08 + Math.random() * 1.4;
    positions.set([Math.cos(az) * Math.cos(el) * 180, Math.sin(el) * 180, Math.sin(az) * Math.cos(el) * 180], i * 3);
  }
  const geoEtoiles = new THREE.BufferGeometry();
  geoEtoiles.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  const materiauEtoiles = new THREE.PointsMaterial({ color: 0xffffff, size: leger ? 1.6 : 1.4, sizeAttenuation: false, transparent: true, fog: false, depthWrite: false });
  monde.add(new THREE.Points(geoEtoiles, materiauEtoiles));

  /* --- Lumières --- */
  const hemi = new THREE.HemisphereLight(0x9DB4D8, 0x2A2620, 0.25);
  monde.add(hemi);
  const lune = new THREE.DirectionalLight(0x8FA6D6, 0.5);
  lune.position.set(-20, 30, 18);
  monde.add(lune);
  const soleil = new THREE.DirectionalLight(0xFF9A4A, 0);
  if (!leger) {
    soleil.castShadow = true;
    soleil.shadow.mapSize.set(1024, 1024);
    soleil.shadow.camera.left = -14;
    soleil.shadow.camera.right = 14;
    soleil.shadow.camera.top = 14;
    soleil.shadow.camera.bottom = -14;
    soleil.shadow.camera.far = 120;
    soleil.shadow.bias = -0.0004;
    soleil.shadow.normalBias = 0.03;
  }
  monde.add(soleil, soleil.target);
  const lueurInterieure = new THREE.PointLight(0xFFB466, 0, 9, 1.6);
  lueurInterieure.position.set(0.5, 1.6, 4.4);
  monde.add(lueurInterieure);

  /* --- Textures procédurales (aucun fichier externe) --- */
  const textureCanvas = (largeur, hauteur, peindre) => {
    const c = document.createElement("canvas");
    c.width = largeur;
    c.height = hauteur;
    peindre(c.getContext("2d"), largeur, hauteur);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = Math.min(8, rendu.capabilities.getMaxAnisotropy());
    return t;
  };

  // Tuiles orangées : rangs décalés, légère variation de teinte par tuile
  const textureTuiles = textureCanvas(512, 512, (ctx, l, h) => {
    const colonnes = 8, rangs = 8;
    const tl = l / colonnes, th = h / rangs;
    ctx.fillStyle = "#7E3A1C";
    ctx.fillRect(0, 0, l, h);
    for (let r = 0; r < rangs; r++) {
      for (let c = -1; c <= colonnes; c++) {
        const x = c * tl + (r % 2 ? tl / 2 : 0);
        const y = r * th;
        const v = (Math.random() - 0.5) * 18;
        const g = ctx.createLinearGradient(0, y, 0, y + th);
        g.addColorStop(0, `hsl(${20 + v * 0.3} 62% ${52 + v * 0.4}%)`);
        g.addColorStop(0.85, `hsl(${18 + v * 0.3} 60% ${42 + v * 0.4}%)`);
        g.addColorStop(1, "hsl(16 55% 28%)");
        ctx.fillStyle = g;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x + 2, y + 1, tl - 4, th - 3, [2, 2, tl / 2.4, tl / 2.4]);
        else ctx.rect(x + 2, y + 1, tl - 4, th - 3);
        ctx.fill();
      }
    }
  });
  textureTuiles.wrapS = textureTuiles.wrapT = THREE.RepeatWrapping;
  textureTuiles.repeat.set(4, 2.2);

  // Cellules des panneaux : fond noir, grille fine, rails discrets
  const textureCellules = textureCanvas(256, 384, (ctx, l, h) => {
    ctx.fillStyle = "#0B0F15";
    ctx.fillRect(0, 0, l, h);
    ctx.strokeStyle = "#1F2A38";
    ctx.lineWidth = 2;
    for (let i = 1; i < 6; i++) { ctx.beginPath(); ctx.moveTo((l / 6) * i, 0); ctx.lineTo((l / 6) * i, h); ctx.stroke(); }
    for (let j = 1; j < 10; j++) { ctx.beginPath(); ctx.moveTo(0, (h / 10) * j); ctx.lineTo(l, (h / 10) * j); ctx.stroke(); }
    ctx.strokeStyle = "#151C26";
    ctx.lineWidth = 1;
    for (let i = 0; i < 6; i++) {
      for (const k of [0.33, 0.66]) {
        ctx.beginPath(); ctx.moveTo((l / 6) * (i + k), 0); ctx.lineTo((l / 6) * (i + k), h); ctx.stroke();
      }
    }
  });

  await pause();

  /* --- Matériaux --- */
  const M = (options) => new THREE.MeshStandardMaterial(options);
  const mat = {
    enduit: M({ color: 0xEDE6DA, roughness: 0.95 }),
    soubassement: M({ color: 0xC9BFAF, roughness: 1 }),
    tuiles: M({ map: textureTuiles, roughness: 0.82 }),
    faitage: M({ color: 0xA24E26, roughness: 0.8 }),
    menuiserie: M({ color: 0x2A2E35, roughness: 0.6 }),
    vitre: M({ color: 0x10141A, roughness: 0.15, metalness: 0.2, emissive: 0xFFA850, emissiveIntensity: 0 }),
    bois: M({ color: 0x9C6E48, roughness: 0.85 }),
    acrotere: M({ color: 0xDCD3C4, roughness: 0.95 }),
    terrasse: M({ color: 0xCBBDA4, roughness: 1 }),
    sol: M({ color: 0x7D8762, roughness: 1 }),
    allee: M({ color: 0xD5C8AF, roughness: 1 }),
    vegetal: M({ color: 0x5C6D4C, roughness: 0.9 }),
    cypres: M({ color: 0x3E5140, roughness: 0.9 }),
    cadrePanneau: M({ color: 0x1A1E24, roughness: 0.4, metalness: 0.6 }),
  };
  const matPanneau = new THREE.MeshPhysicalMaterial({
    map: textureCellules,
    color: 0xffffff,
    roughness: 0.22,
    metalness: 0.35,
    clearcoat: 1,
    clearcoatRoughness: 0.06,
    envMapIntensity: 1.4,
    emissive: 0xFFE9C4,
    emissiveIntensity: 0,
  });

  /* --- Construction de la maison --- */
  const maison = new THREE.Group();
  monde.add(maison);

  const boite = (l, h, p, materiau, x, y, z, ombre = true) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(l, h, p), materiau);
    m.position.set(x, y, z);
    m.castShadow = ombre;
    m.receiveShadow = true;
    maison.add(m);
    return m;
  };

  // Dimensions du volume principal (mètres)
  const LARG = 9, PROF = 6.5, HAUT_MUR = 3.2, PENTE = Math.PI / 6, DEBORD = 0.45;
  const demiP = PROF / 2;
  const hauteurFaitage = HAUT_MUR + demiP * Math.tan(PENTE);

  boite(LARG, HAUT_MUR, PROF, mat.enduit, 0, HAUT_MUR / 2, 0);
  boite(LARG + 0.06, 0.35, PROF + 0.06, mat.soubassement, 0, 0.175, 0);

  // Pignons triangulaires
  const formePignon = new THREE.Shape();
  formePignon.moveTo(-demiP, 0);
  formePignon.lineTo(demiP, 0);
  formePignon.lineTo(0, hauteurFaitage - HAUT_MUR);
  formePignon.closePath();
  const geoPignon = new THREE.ExtrudeGeometry(formePignon, { depth: 0.2, bevelEnabled: false });
  for (const cote of [-1, 1]) {
    const pignon = new THREE.Mesh(geoPignon, mat.enduit);
    pignon.rotation.y = Math.PI / 2;
    pignon.position.set(cote * LARG / 2 - (cote > 0 ? 0.2 : 0), HAUT_MUR, 0);
    pignon.castShadow = true;
    pignon.receiveShadow = true;
    maison.add(pignon);
  }

  // Deux pans de toiture
  const longueurPan = (demiP + DEBORD) / Math.cos(PENTE);
  const epaisseurPan = 0.2;
  const pans = [];
  for (const sens of [1, -1]) {
    const pan = boite(LARG + DEBORD * 2, epaisseurPan, longueurPan, mat.tuiles, 0, 0, 0);
    const milieuHorizontal = (demiP + DEBORD) / 2;
    pan.position.set(0, hauteurFaitage - milieuHorizontal * Math.tan(PENTE) + 0.06, sens * milieuHorizontal);
    pan.rotation.x = sens * PENTE;
    pans.push(pan);
  }
  const faitage = boite(LARG + DEBORD * 2 + 0.05, 0.22, 0.32, mat.faitage, 0, hauteurFaitage + 0.12, 0);
  faitage.rotation.x = Math.PI / 4;
  faitage.scale.set(1, 1, 0.8);
  boite(0.7, 1.6, 0.7, mat.enduit, -3, hauteurFaitage + 0.1, -1.1);

  // Façade avant (z positif) : baies, porte, encadrements
  const facade = demiP + 0.01;
  const baie = (l, h, x, y, z = facade, rotY = 0) => {
    const groupe = new THREE.Group();
    const cadre = new THREE.Mesh(new THREE.BoxGeometry(l + 0.16, h + 0.16, 0.08), mat.menuiserie);
    const vitre = new THREE.Mesh(new THREE.PlaneGeometry(l, h), mat.vitre);
    vitre.position.z = 0.045;
    groupe.add(cadre, vitre);
    groupe.position.set(x, y, z);
    groupe.rotation.y = rotY;
    maison.add(groupe);
  };
  baie(2.4, 2.2, -2.4, 1.45);
  baie(1.1, 1.3, 0.5, 1.9);
  baie(2.4, 2.2, 2.9, 1.45);
  boite(1.0, 2.2, 0.1, mat.bois, 0.5, 1.1 - 0.05, facade - 0.02).position.y = 1.15;
  baie(1.1, 1.3, -LARG / 2 - 0.01, 1.9, -0.8, -Math.PI / 2);

  // Aile basse contemporaine, bardage bois et toit plat
  const AILE_X = LARG / 2 + 2.1;
  boite(4.2, 2.8, 5.2, mat.bois, AILE_X, 1.4, -0.4);
  boite(4.5, 0.25, 5.5, mat.acrotere, AILE_X, 2.92, -0.4);
  baie(3.0, 2.1, AILE_X, 1.2, -0.4 + 2.61);

  // Terrasse, allée, sol
  boite(7.5, 0.12, 2.6, mat.terrasse, -0.6, 0.06, demiP + 1.3, false);
  const allee = boite(1.4, 0.04, 9, mat.allee, 0.5, 0.02, demiP + 6.5, false);
  allee.receiveShadow = true;
  const sol = new THREE.Mesh(new THREE.CircleGeometry(90, 48), mat.sol);
  sol.rotation.x = -Math.PI / 2;
  sol.receiveShadow = true;
  monde.add(sol);

  // Végétation sobre : massifs arrondis et cyprès
  const geoMassif = new THREE.IcosahedronGeometry(1, 2);
  const geoCypres = new THREE.ConeGeometry(0.55, 4.2, 12);
  const vegetaux = [
    ["massif", -5.6, 0.55, 3.8, 1.1], ["massif", -6.6, 0.45, 2.2, 0.85], ["massif", 3.6, 0.45, 4.4, 0.8],
    ["cypres", -7.4, 2.1, -1.6], ["cypres", -8.3, 2.0, 0.2], ["cypres", 9.6, 2.1, -2.6],
    ["massif", 8.8, 0.5, 2.6, 0.95], ["massif", -4.2, 0.4, -4.6, 1.2],
  ];
  for (const [type, x, y, z, s] of leger ? vegetaux.slice(0, 5) : vegetaux) {
    const m = new THREE.Mesh(type === "massif" ? geoMassif : geoCypres, type === "massif" ? mat.vegetal : mat.cypres);
    m.position.set(x, y, z);
    if (s) m.scale.set(s * 1.2, s * 0.8, s);
    m.castShadow = !leger;
    maison.add(m);
  }

  await pause();

  /* --- Panneaux solaires : 2 rangs de 5 sur le pan avant --- */
  const repereToit = new THREE.Group();
  repereToit.position.copy(pans[0].position);
  repereToit.rotation.copy(pans[0].rotation);
  maison.add(repereToit);

  const PANNEAU_L = 1.08, PANNEAU_P = 1.66;
  const geoPanneau = new THREE.BoxGeometry(PANNEAU_L, 0.04, PANNEAU_P);
  const geoCadre = new THREE.BoxGeometry(PANNEAU_L + 0.04, 0.035, PANNEAU_P + 0.04);
  const panneaux = [];
  const colonnes = 5, rangs = 2;
  for (let r = 0; r < rangs; r++) {
    for (let c = 0; c < colonnes; c++) {
      const groupe = new THREE.Group();
      const verre = new THREE.Mesh(geoPanneau, matPanneau.clone());
      const cadre = new THREE.Mesh(geoCadre, mat.cadrePanneau);
      cadre.position.y = -0.01;
      verre.castShadow = cadre.castShadow = !leger;
      groupe.add(cadre, verre);
      const x = -1.2 + (c - (colonnes - 1) / 2) * (PANNEAU_L + 0.06);
      const z = -0.95 + r * (PANNEAU_P + 0.06);
      groupe.userData = { x, z, colonne: c, verre };
      groupe.visible = false;
      repereToit.add(groupe);
      panneaux.push(groupe);
    }
  }
  const POSE_DEBUT = 0.18, POSE_PAS = 0.036, POSE_DUREE = 0.085;
  const hauteurPose = epaisseurPan / 2 + 0.07;

  /* --- Cadrage : décalage de l'image pour laisser la place au texte --- */
  let largeur = 1, hauteur = 1;
  const dimensionner = () => {
    largeur = scene.clientWidth;
    hauteur = scene.clientHeight;
    rendu.setSize(largeur, hauteur, false);
    const aspect = largeur / hauteur;
    camera.aspect = aspect;
    camera.fov = aspect < 1 ? 46 : 35;
    if (aspect >= 1.1) camera.setViewOffset(largeur, hauteur, -largeur * 0.17, 0, largeur, hauteur);
    else camera.setViewOffset(largeur, hauteur, 0, hauteur * 0.17, largeur, hauteur);
    camera.updateProjectionMatrix();
  };

  /* --- Mise à jour de la scène selon la progression --- */
  const cibleCamera = new THREE.Vector3(2.0, 2.2, 0);
  const ANGLE_FIN = 0.42;
  const dirSoleil = new THREE.Vector3();

  const dessiner = (p) => {
    const aspect = largeur / hauteur;
    const recul = aspect < 1 ? borner(1.15 / aspect, 1.2, 2.1) : aspect < 1.3 ? 1.15 : 1;

    // Caméra : rotation lente autour de la maison
    const t = sinusoidal(p);
    const angle = interpoler(-0.78, ANGLE_FIN, t);
    const rayon = interpoler(28, 23, t) * recul;
    camera.position.set(
      cibleCamera.x + Math.sin(angle) * rayon,
      interpoler(9, 5.4, t) * Math.min(recul, 1.4),
      Math.cos(angle) * rayon,
    );
    camera.lookAt(cibleCamera);

    // Panneaux posés un à un
    panneaux.forEach((panneau, i) => {
      const k = borner((p - (POSE_DEBUT + i * POSE_PAS)) / POSE_DUREE);
      const { x, z } = panneau.userData;
      panneau.visible = k > 0;
      const e = sortieCubique(k);
      panneau.position.set(x, hauteurPose + (1 - e) * 3.2, z - (1 - e) * 0.6);
      panneau.rotation.set((1 - e) * -0.35, 0, (1 - e) * 0.12);
    });

    // Lever du soleil
    const jour = lisser(0.55, 0.9, p);
    const elevation = interpoler(-0.1, 0.3, jour);
    const azimut = ANGLE_FIN + Math.PI - 0.55;
    dirSoleil.set(Math.sin(azimut) * Math.cos(elevation), Math.sin(elevation), Math.cos(azimut) * Math.cos(elevation));
    uniformesCiel.uDirSoleil.value.copy(dirSoleil);
    uniformesCiel.uEclat.value = lisser(0.5, 0.75, p);
    melanger(CIEL_HAUT, jour, uniformesCiel.uHaut.value);
    melanger(CIEL_HORIZON, jour, uniformesCiel.uHorizon.value);
    monde.fog.color.copy(uniformesCiel.uHorizon.value);
    materiauEtoiles.opacity = 0.85 * (1 - lisser(0.5, 0.75, p));

    // La lumière principale vient du même côté que le soleil, un peu plus haut
    soleil.position.set(dirSoleil.x * 40, Math.max(dirSoleil.y, 0.12) * 40 + 4, dirSoleil.z * 40 + 18);
    soleil.intensity = 3.0 * jour;
    if (!leger && jour > 0) rendu.shadowMap.needsUpdate = true;
    soleil.color.setHSL(0.07 + 0.04 * jour, 0.9, 0.62 + 0.12 * jour);
    hemi.intensity = interpoler(0.28, 1.05, jour);
    hemi.color.setHSL(interpoler(0.6, 0.1, jour), 0.45, interpoler(0.55, 0.78, jour));
    lune.intensity = 0.55 * (1 - jour);
    rendu.toneMappingExposure = interpoler(0.95, 1.05, jour);
    majReflets(jour);

    // Reflets : un éclat parcourt les panneaux de gauche à droite
    const vague = lisser(0.58, 0.92, p) * 1.8 - 0.4;
    panneaux.forEach((panneau) => {
      const d = vague - panneau.userData.colonne / 5;
      panneau.userData.verre.material.emissiveIntensity = 1.3 * Math.exp(-(d * d) / 0.012) * jour;
    });

    // La maison s'illumine de l'intérieur
    const interieur = lisser(0.82, 0.97, p);
    mat.vitre.emissiveIntensity = interieur * 1.9;
    lueurInterieure.intensity = interieur * (leger ? 0 : 6);

    rendu.render(monde, camera);
  };

  dimensionner();
  // Les panneaux sont rendus visibles le temps de la compilation pour que tous
  // les shaders soient préparés en parallèle (sans bloquer la page)
  panneaux.forEach((panneau) => { panneau.visible = true; });
  await rendu.compileAsync(monde, camera);
  await pause();
  const boucle = lancerBoucle(dessiner);
  new ResizeObserver(() => { dimensionner(); boucle.redessiner(); }).observe(scene);
  canvas.classList.add("est-pret");

  // Reflets du ciel sur les panneaux : générés une fois la page au repos
  await pause();
  refletsActifs = true;
  boucle.redessiner();

  // Contexte WebGL perdu : on bascule sur l'image fixe
  canvas.addEventListener("webglcontextlost", () => racine.classList.add("mode-fixe"));
}

/* ------------------------------------------------------------------
   5b. HERO : BONHOMME
   - Au lever du soleil (progression ≥ apparition), il entre par la
     droite, joue son animation de salut et la bulle « Bonjour ! »
     apparaît. Il repart si l'on remonte avant le lever du soleil.
   - Ensuite, son regard suit le curseur (ou le doigt sur mobile) :
     on affiche, dans une grille d'images du même visage regardant
     dans toutes les directions, celle qui pointe vers le curseur.
   - Sans images (medias.js vide) : cadre provisoire dont les yeux
     simplifiés suivent le curseur, pour valider le comportement.
   ------------------------------------------------------------------ */
function initialiserBonhomme() {
  const el = hero?.querySelector(".bonhomme");
  if (!el) return;
  const config = MEDIAS.bonhomme || {};
  const regard = config.regard || {};
  const salut = config.salut || [];
  const grille = regard.images || [];
  const colonnes = regard.colonnes || 1;
  const lignes = regard.lignes || 1;
  const [teteX, teteY] = regard.tete || [0.5, 0.22];
  const seuil = config.apparition ?? 0.78;
  const ips = config.ips || 24;
  const reel = salut.length > 0 || grille.length > 0;
  // L'image n'est créée que si des médias réels existent (sinon : cadre provisoire)
  const img = document.createElement("img");
  img.className = "bonhomme__image";
  img.alt = "";
  img.decoding = "async";

  // Préchargement (une fois le bonhomme proche d'apparaître)
  let precharge = false;
  const precharger = () => {
    if (precharge || !reel) return;
    precharge = true;
    [...salut, ...grille].forEach((url) => { const i = new Image(); i.decoding = "async"; i.src = url; });
  };
  if (reel) {
    img.src = grille[Math.floor(grille.length / 2)] || salut[0];
    el.querySelector(".bonhomme__cadre").prepend(img);
    el.classList.add("bonhomme--reel");
  }

  let etat = "absent"; // absent → salut → regard
  let minuteurBulle = 0;
  let animSalut = 0;

  // --- Regard : direction lissée vers le pointeur, de -1 à 1 sur chaque axe
  const pointeur = { x: 0, y: 0, actif: false };
  const vue = { x: 0, y: 0 };
  let dernierMouvement = 0;
  let boucleRegard = 0;

  const suivrePointeur = (x, y) => {
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width * teteX;
    const cy = r.top + r.height * teteY;
    // -1 / +1 = le bord de l'écran dans cette direction (amplitude pleine où que soit la tête)
    const dx = x - cx, dy = y - cy;
    pointeur.x = borner(dx / Math.max(80, dx < 0 ? cx : window.innerWidth - cx), -1, 1);
    pointeur.y = borner(dy / Math.max(80, dy < 0 ? cy : window.innerHeight - cy), -1, 1);
    pointeur.actif = true;
    dernierMouvement = performance.now();
    lancerRegard();
  };
  window.addEventListener("pointermove", (e) => suivrePointeur(e.clientX, e.clientY), { passive: true });
  window.addEventListener("touchmove", (e) => { const t = e.touches[0]; if (t) suivrePointeur(t.clientX, t.clientY); }, { passive: true });

  const afficherRegard = () => {
    if (grille.length && etat === "regard") {
      const c = Math.round(((vue.x + 1) / 2) * (colonnes - 1));
      const l = Math.round(((vue.y + 1) / 2) * (lignes - 1));
      const url = grille[l * colonnes + c];
      if (url && img.getAttribute("src") !== url) img.src = url;
    }
    el.style.setProperty("--regard-x", vue.x.toFixed(3));
    el.style.setProperty("--regard-y", vue.y.toFixed(3));
  };

  let dernierRegard = 0;
  const etapeRegard = (maintenant) => {
    const dt = dernierRegard ? borner(maintenant - dernierRegard, 0, 64) / (1000 / 60) : 1;
    dernierRegard = maintenant;
    const k = 1 - Math.pow(1 - 0.2, dt);
    // Sans mouvement depuis 3 s, il revient doucement regarder le visiteur
    const cibleX = pointeur.actif && performance.now() - dernierMouvement < 3000 ? pointeur.x : 0;
    const cibleY = pointeur.actif && performance.now() - dernierMouvement < 3000 ? pointeur.y : 0;
    vue.x = interpoler(vue.x, cibleX, k);
    vue.y = interpoler(vue.y, cibleY, k);
    afficherRegard();
    const enMouvement = Math.abs(vue.x - cibleX) > 0.01 || Math.abs(vue.y - cibleY) > 0.01 || cibleX !== 0 || cibleY !== 0;
    boucleRegard = enMouvement && etat !== "absent" ? requestAnimationFrame(etapeRegard) : 0;
    if (!boucleRegard) dernierRegard = 0;
  };
  const lancerRegard = () => { if (!boucleRegard && etat !== "absent") boucleRegard = requestAnimationFrame(etapeRegard); };

  // --- Animation de salut, jouée en temps réel (indépendante du scroll)
  const jouerSalut = () => {
    if (!salut.length || reduireMouvement.matches) { etat = "regard"; lancerRegard(); return; }
    const debut = performance.now();
    const image = (maintenant) => {
      if (etat !== "salut") return;
      const index = Math.floor(((maintenant - debut) / 1000) * ips);
      if (index >= salut.length) { etat = "regard"; lancerRegard(); return; }
      if (img.getAttribute("src") !== salut[index]) img.src = salut[index];
      animSalut = requestAnimationFrame(image);
    };
    animSalut = requestAnimationFrame(image);
  };

  const arriver = () => {
    etat = "salut";
    el.classList.add("est-present");
    if (salut.length) img.src = salut[0];
    minuteurBulle = setTimeout(() => el.classList.add("dit-bonjour"), 500);
    jouerSalut();
  };
  const partir = () => {
    etat = "absent";
    clearTimeout(minuteurBulle);
    cancelAnimationFrame(animSalut);
    cancelAnimationFrame(boucleRegard);
    boucleRegard = 0;
    el.classList.remove("est-present", "dit-bonjour");
  };

  suiveursProgression.push((p) => {
    if (p > seuil - 0.15) precharger();
    if (etat === "absent" && p >= seuil) arriver();
    else if (etat !== "absent" && p < seuil - 0.04) partir();
  });
}

/* ------------------------------------------------------------------
   6. DÉMARRAGE
   ------------------------------------------------------------------ */
initialiserMenu();
initialiserApparitions();
if (!racine.classList.contains("mode-fixe")) initialiserBonhomme();

if (hero && scene && canvas && !racine.classList.contains("mode-fixe")) {
  if (FRAME_URLS.length > 0) {
    demarrerSequence(FRAME_URLS);
  } else if (!webglDisponible()) {
    racine.classList.add("mode-fixe");
  } else {
    // Three.js n'est chargé qu'une fois la page affichée, pour ne pas
    // retarder le premier rendu (le titre reste l'élément principal).
    // Ordinateur : dès que la page est au repos. Mobile et appareils
    // modestes : à la première interaction (défilement, toucher, clavier).
    let lance = false;
    const lancer = () => {
      if (lance) return;
      lance = true;
      demarrer3D().catch(() => racine.classList.add("mode-fixe"));
    };
    if (ecranLeger) {
      for (const type of ["scroll", "touchstart", "pointerdown", "keydown", "wheel"]) {
        window.addEventListener(type, lancer, { once: true, passive: true });
      }
    } else {
      const auRepos = window.requestIdleCallback || ((f) => setTimeout(f, 200));
      if (document.readyState === "complete") auRepos(lancer);
      else window.addEventListener("load", () => auRepos(lancer), { once: true });
    }
  }
}

// Si la préférence de mouvement change en cours de visite, on fige le hero
reduireMouvement.addEventListener("change", (e) => { if (e.matches) racine.classList.add("mode-fixe"); });
})();
