// Personnages Mixamo (qualité studio) : chargement, animations adaptées à chaque squelette, IK sur les vrais os.
// Les fichiers .fbx sont servis depuis /assets/mixamo/ (téléchargés par l'utilisateur, non versionnés).
import { THREE, scene } from "./core.js";
import { FBXLoader } from "three/addons/loaders/FBXLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const CHARS = { marc: "Ch23_nonPBR.fbx", doctor: "Ch01_nonPBR.fbx", remy: "Remy.fbx", womanA: "Ch21_nonPBR.fbx", womanB: "Ch37_nonPBR.fbx" };
const HEIGHT = { marc: 1.78, doctor: 1.74, remy: 1.8, womanA: 1.68, womanB: 1.66 };
export const ANIMS = ["Breathing_Idle", "Walking", "Running", "Descending_Stairs", "Ascending_Stairs", "Typing", "Writing", "Carrying", "Box_Idle",
  "Nervously_Look_Around", "Reaching_Out", "Relieved_Sigh", "Shaking_Head_No", "Sitting_Idle", "Talking_On_A_Cell_Phone", "Texting_While_Standing"];
const base = {}, clips = {};
let ready = false;
export const mxReady = () => ready;

const loader = new FBXLoader();
const load = (f) => new Promise((ok, ko) => loader.load("/assets/mixamo/" + f, ok, undefined, ko));
function prefixOf(root) { let p = null; root.traverse((o) => { if (!p && o.isBone && /Hips$/.test(o.name)) p = o.name.replace(/Hips$/, ""); }); return p; }

export async function loadMixamo(roles = Object.keys(CHARS)) {
  const need = [...new Set(roles)].filter((r) => !base[r]);
  const [models, anims] = await Promise.all([Promise.all(need.map((r) => load(CHARS[r]))), Object.keys(clips).length ? [] : Promise.all(ANIMS.map((a) => load(a + ".fbx")))]);
  need.forEach((r, i) => {
    const m = models[i];
    m.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false;
      for (const mt of [].concat(o.material)) { if (mt) { mt.side = THREE.FrontSide; if (mt.shininess !== undefined) mt.shininess = Math.min(mt.shininess, 12); } } } });
    m.updateMatrixWorld(true);
    const bb = new THREE.Box3().setFromObject(m, true);
    m.scale.multiplyScalar(HEIGHT[r] / (bb.max.y - bb.min.y));
    let hips = null; m.traverse((o) => { if (!hips && o.isBone && /Hips$/.test(o.name)) hips = o; });
    base[r] = { model: m, prefix: prefixOf(m), hipsY: hips.position.y };
  });
  if (anims.length) anims.forEach((a, i) => { clips[ANIMS[i]] = a.animations[0]; });
  ready = true;
}

// clip adapté : noms d'os du personnage, déplacement des hanches remis à l'échelle et sur place
function retarget(name, prefix, hipsY) {
  const src = clips[name]; if (!src) return null;
  const ref = clips.Breathing_Idle.tracks.find((t) => t.name === "mixamorigHips.position");
  const refY = ref ? ref.values[1] : 100, k = hipsY / refY;
  const tracks = [];
  for (const tr of src.tracks) {
    if (/\.scale$/.test(tr.name)) continue;
    const t2 = tr.clone(); t2.name = tr.name.replace(/^mixamorig/, prefix);
    if (/Hips\.position$/.test(tr.name)) {
      const v = t2.values, x0 = v[0], z0 = v[2];
      // sur place (la scène déplace le personnage) ; dérive verticale retirée (escaliers) : la marche est faite par l'IK des pieds
      const n = v.length / 3, y0 = v[1], y1 = v[v.length - 2];
      for (let j = 0, i = 0; j < v.length; j += 3, i++) { v[j] = 0; v[j + 1] = (v[j + 1] - (y1 - y0) * i / Math.max(1, n - 1)) * k; v[j + 2] = 0; }
    } else if (/\.position$/.test(tr.name)) continue;
    tracks.push(t2);
  }
  return new THREE.AnimationClip(name, src.duration, tracks);
}

const TMP = new THREE.Vector3(), TMP2 = new THREE.Vector3(), Q = new THREE.Quaternion(), Q2 = new THREE.Quaternion();
function rotateBoneTo(bone, from, to) {           // tourne l'os (repère monde) pour que la direction from devienne to
  const q = new THREE.Quaternion().setFromUnitVectors(from.clone().normalize(), to.clone().normalize());
  bone.parent.getWorldQuaternion(Q); const wq = bone.getWorldQuaternion(Q2);
  bone.quaternion.copy(Q.clone().invert().multiply(q).multiply(wq));
  bone.updateMatrixWorld(true);
}
function ikChain(a, b, c, target, pole) {
  a.updateMatrixWorld(true);
  const pa = a.getWorldPosition(new THREE.Vector3()), pb = b.getWorldPosition(new THREE.Vector3()), pc = c.getWorldPosition(new THREE.Vector3());
  const la = pa.distanceTo(pb), lb = pb.distanceTo(pc);
  const d = target.clone().sub(pa); let L = Math.min(Math.max(d.length(), Math.abs(la - lb) + 1e-4), la + lb - 1e-4); d.normalize();
  const n = d.clone().cross(pole).normalize(), m = n.clone().cross(d).normalize();
  const cosA = (la * la + L * L - lb * lb) / (2 * la * L), sinA = Math.sqrt(Math.max(0, 1 - cosA * cosA));
  const elbow = pa.clone().add(d.clone().multiplyScalar(la * cosA)).add(m.multiplyScalar(la * sinA));
  rotateBoneTo(a, pb.clone().sub(pa), elbow.clone().sub(pa));
  const pb2 = b.getWorldPosition(new THREE.Vector3()), pc2 = c.getWorldPosition(new THREE.Vector3());
  rotateBoneTo(b, pc2.clone().sub(pb2), target.clone().sub(pb2));
}

// personnage prêt à l'emploi, même interface que les personnages faits en code (g, P, kind)
export function mxPerson(role, tint = null) {
  const B = base[role];
  const model = SkeletonUtils.clone(B.model);
  const g = new THREE.Group(); g.add(model); scene.add(g);
  if (tint !== null) model.traverse((o) => { if (o.isMesh) { o.material = [].concat(o.material).map((mt) => { const c = mt.clone(); c.color = (c.color || new THREE.Color(1, 1, 1)).clone().offsetHSL(tint, 0, 0); return c; }); if (o.material.length === 1) o.material = o.material[0]; } });
  const bones = {}; model.traverse((o) => { if (o.isBone) bones[o.name.slice(B.prefix.length)] = o; });
  const mixer = new THREE.AnimationMixer(model), actions = {};
  const action = (name) => { if (!actions[name]) { const c = retarget(name, B.prefix, B.hipsY); if (!c) return null; actions[name] = mixer.clipAction(c); actions[name].play(); actions[name].enabled = true; } return actions[name]; };
  // attaches pour les objets tenus : repère indépendant de l'échelle de l'os, doigts vers -y, paume vers +z
  const socket = (boneName) => { const s = new THREE.Group(); const bone = bones[boneName]; bone.add(s);
    model.updateMatrixWorld(true); const ws = bone.getWorldScale(new THREE.Vector3()); s.scale.set(1 / ws.x, 1 / ws.y, 1 / ws.z); s.rotation.x = Math.PI; s.position.y = 6; return s; };
  const dummy = () => { const o = new THREE.Object3D(); return { sh: o, el: new THREE.Object3D(), hand: null }; };
  const P = { armL: dummy(), armR: dummy(), legL: { hip: new THREE.Object3D(), knee: new THREE.Object3D() }, legR: { hip: new THREE.Object3D(), knee: new THREE.Object3D() },
    head: new THREE.Object3D(), body: new THREE.Group(), lids: [], brows: [], eyes: [], tears: [] };
  g.add(P.body);
  // convention des scènes : « L » = côté -x du personnage (sa main droite chez Mixamo, qui regarde vers +z)
  P.armL.hand = socket("RightHand"); P.armR.hand = socket("LeftHand");
  const p = { g, P, kind: "mx", role, bones, mixer, t: 0, cur: null,
    // joue une animation à l'instant t (déterministe) ; mélange doux si on change d'animation
    play(name, t, speed = 1) {
      const a = action(name) || action("Breathing_Idle");
      for (const [k, x] of Object.entries(actions)) x.weight = x === a ? 1 : 0;
      a.time = (t * speed) % a.getClip().duration; mixer.update(0); model.updateMatrixWorld(true); this.t = t; this.cur = name;
    },
    ik(side, target, pole) {
      const s = side === "L" ? "Right" : "Left";
      const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion()));
      const out = new THREE.Vector3(side === "L" ? -1 : 1, 0, 0).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion()));
      ikChain(bones[s + "Arm"], bones[s + "ForeArm"], bones[s + "Hand"], target, pole || fwd.multiplyScalar(0.6).add(out).add(new THREE.Vector3(0, -0.6, 0)).normalize());
    },
    leg(side, target) {
      const s = side === "L" ? "Right" : "Left";
      const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(g.getWorldQuaternion(new THREE.Quaternion()));
      ikChain(bones[s + "UpLeg"], bones[s + "Leg"], bones[s + "Foot"], target, fwd);
    },
  };
  p.play("Breathing_Idle", 0);
  return p;
}
