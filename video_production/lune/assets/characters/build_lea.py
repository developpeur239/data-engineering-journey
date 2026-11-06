"""Léa en 3D (Blender + Python), d'après la planche de référence 2D validée (references_design/personnages/reference_2d.png).

Construction : volumes simples qui se chevauchent, fondus en une seule surface (remaillage voxel) puis adoucis.

    python3 build_lea.py            # écrit lea.blend et les rendus face / trois-quarts / profil dans renders/

Principe du style : silhouettes noires mates aux formes continues (le corps, les membres et les mains se fondent sans
articulation mécanique), grande tête ronde, petits yeux blancs ovales sans pupille, coiffure en volumes
doux, contour blanc fin comme sur le dessin (coque inversée), éclairage doux et peu contrasté.
Toutes les proportions sont des paramètres (P) ; un squelette (rig) est relié au corps pour l'animation.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"

# ---------- paramètres (mètres ; Z vers le haut, la face regarde vers −Y) ----------
P = dict(
    height=1.60,                  # hauteur totale ≈ 2,6 têtes (mesurée sur la référence)
    head_rx=0.3, head_rz=0.3, head_ry=0.285, head_z=1.28,
    hair_k=0.3 / 0.245,           # les cheveux sont dessinés pour une tête de 0,245 m puis mis à l'échelle
    shoulder_z=0.90, shoulder_x=0.165, hip_x=0.19, crotch_z=0.41,
    leg_x=0.075, leg_r=0.066,
    arm_r=0.039, hand_r=0.058, hand_z=0.45, hand_x=0.245,
    hair="#9b4e2a", scarf="#e8b33c", skin="#141518", eye="#f4f2ec", outline="#f2f2f0",
    outline_w=0.011,
)


def srgb(h: str, a: float = 1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*lin, a)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat_diffuse(name, color, rough=0.75, spec=0.15):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(color); b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m


def mat_emit(name, color, strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = srgb(color); e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0])
    return m


def mat_outline(name, color):
    """Coque inversée : visible seulement par ses faces arrière (contour blanc autour de la silhouette)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = srgb(color); em.inputs["Strength"].default_value = 1.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0]); nt.links.new(em.outputs[0], mix.inputs[1]); nt.links.new(tr.outputs[0], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(mix.outputs[0], out.inputs[0])
    return m


def add_outline(ob, mat_out, w):
    ob.data.materials.append(mat_out)
    mod = ob.modifiers.new("Contour", "SOLIDIFY")
    mod.thickness = w; mod.offset = 1.0; mod.use_flip_normals = True; mod.use_rim = False
    mod.material_offset = len(ob.data.materials) - 1
    return mod


def sel(*obs):
    for o in bpy.context.view_layer.objects:
        o.select_set(o in obs)
    bpy.context.view_layer.objects.active = obs[0]


def ellipsoid(loc, r, rot=(0, 0, 0), seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc)
    o = bpy.context.active_object; o.scale = r; o.rotation_euler = [math.radians(a) for a in rot]; return o


def capsule(a, b, r):
    """Capsule entre deux points (cylindre et deux demi-sphères)."""
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=r, depth=d.length, location=(a + b) / 2)
    c = bpy.context.active_object; c.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    s1 = ellipsoid(tuple(a), (r, r, r)); s2 = ellipsoid(tuple(b), (r, r, r))
    return [c, s1, s2]


def fuse(name, obs, mat, voxel=0.007, smooth=12):
    """Fond les volumes en une seule surface continue, puis adoucit les jonctions."""
    sel(*obs); bpy.ops.object.join(); o = bpy.context.active_object; o.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    m = o.modifiers.new("Fusion", "REMESH"); m.mode = "VOXEL"; m.voxel_size = voxel; bpy.ops.object.modifier_apply(modifier=m.name)
    if smooth:
        m = o.modifiers.new("Adoucir", "SMOOTH"); m.factor = 0.6; m.iterations = smooth; bpy.ops.object.modifier_apply(modifier=m.name)
    o.data.materials.clear(); o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    return o


def build_lea():
    p = P
    skin = mat_diffuse("Lea_peau", p["skin"], 0.62, 0.25)
    hair = mat_diffuse("Lea_cheveux", p["hair"], 0.7, 0.2)
    scarf = mat_diffuse("Lea_echarpe", p["scarf"], 0.85, 0.1)
    eye = mat_emit("Lea_yeux", p["eye"], 1.0)
    outl = mat_outline("Contour_blanc", p["outline"])
    sz, cz = p["shoulder_z"], p["crotch_z"]

    # --- corps : buste en trapèze arrondi, bras fins, mains rondes, jambes droites, chaussures arrondies ---
    B = [ellipsoid((0, 0, (sz + cz) / 2 + 0.02), (p["hip_x"], 0.12, (sz - cz) / 2 + 0.06)),       # buste
         ellipsoid((0, 0, sz - 0.03), (p["shoulder_x"], 0.105, 0.07)),                              # épaules tombantes
         ellipsoid((0, 0, cz + 0.06), (p["hip_x"] * 0.98, 0.118, 0.1))]                             # bassin
    for s in (-1, 1):
        B += capsule((s * p["leg_x"], 0, cz + 0.05), (s * p["leg_x"], 0, 0.07), p["leg_r"])         # jambe
        B.append(ellipsoid((s * (p["leg_x"] + 0.012), -0.04, 0.045), (0.078, 0.11, 0.048)))          # chaussure
        B += capsule((s * (p["shoulder_x"] + 0.0), 0, sz - 0.02), (s * (p["hand_x"] - 0.005), 0, p["hand_z"] + 0.05), p["arm_r"])   # bras
        B.append(ellipsoid((s * p["hand_x"], -0.005, p["hand_z"]), (p["hand_r"], p["hand_r"] * 0.8, p["hand_r"] * 1.05)))            # main
    B += capsule((0, 0, sz), (0, 0, sz + 0.12), 0.05)                                               # cou
    body = fuse("Lea_corps", B, skin); add_outline(body, outl, p["outline_w"])

    # --- tête ---
    hz = p["head_z"]
    head = ellipsoid((0, 0, hz), (p["head_rx"], p["head_ry"], p["head_rz"]), seg=64); head.name = "Lea_tete"
    bpy.ops.object.transform_apply(scale=True); head.data.materials.append(skin); bpy.ops.object.shade_smooth(); add_outline(head, outl, p["outline_w"])

    # --- cheveux : carré volumineux qui encadre le visage, grande mèche balayée, pointes qui rebiquent ---
    rx, rz = p["head_rx"], p["head_rz"]
    R0 = 0.245   # tête de dessin des cheveux
    Hs = [ellipsoid((0, 0.045, hz + 0.05), (R0 * 1.12, 0.23, R0 * 1.12)),                          # calotte
          ellipsoid((-0.2, 0.04, hz - 0.08), (0.1, 0.16, 0.2)),                                    # côté gauche de l'écran
          ellipsoid((0.21, 0.04, hz - 0.06), (0.095, 0.16, 0.2)),                                   # côté droit
          ellipsoid((-0.27, -0.02, hz - 0.2), (0.075, 0.12, 0.075)),                                 # pointe qui rebique
          ellipsoid((0.27, -0.02, hz - 0.18), (0.07, 0.11, 0.07)),
          ellipsoid((-0.02, -0.16, hz + 0.16), (0.24, 0.09, 0.1), rot=(0, -14, 0)),                  # grande mèche balayée
          ellipsoid((0.18, -0.15, hz + 0.02), (0.08, 0.08, 0.17), rot=(0, 12, 0))]                   # la mèche retombe sur la tempe droite
    hairo = fuse("Lea_cheveux", Hs, hair, voxel=0.006, smooth=10)
    bpy.context.scene.cursor.location = (0, 0, hz); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    hairo.scale = (p["hair_k"],) * 3; bpy.ops.object.transform_apply(scale=True); add_outline(hairo, outl, p["outline_w"])

    # --- yeux : deux ovales blancs verticaux, sans pupille ---
    for s in (-1, 1):
        x, z = s * 0.098, hz - 0.01
        y = -p["head_ry"] * math.sqrt(max(0.0, 1 - (x / rx) ** 2 - ((z - hz) / rz) ** 2)) - 0.001
        e = ellipsoid((x, y, z), (0.024, 0.009, 0.057), seg=24); e.name = f"Lea_oeil_{'G' if s < 0 else 'D'}"
        e.data.materials.append(eye); bpy.ops.object.shade_smooth()

    # --- écharpe : un gros tour autour du cou et un long pan qui tombe sur le côté gauche de l'écran ---
    S = []
    for i in range(14):
        a = i / 14 * 2 * math.pi
        S.append(ellipsoid((math.cos(a) * 0.12, math.sin(a) * 0.095, sz + 0.05), (0.06, 0.06, 0.05)))
    S += capsule((-0.13, -0.07, sz + 0.03), (-0.2, -0.09, sz - 0.2), 0.045)
    S.append(ellipsoid((-0.205, -0.09, sz - 0.24), (0.05, 0.03, 0.05)))
    sc = fuse("Lea_echarpe", S, scarf, voxel=0.006, smooth=8); add_outline(sc, outl, p["outline_w"])
    return dict(body=body, head=head, hair=hairo, scarf=sc)


def build_rig(parts):
    """Squelette simple : bassin, colonne, cou, tête, bras (épaule, coude, main), jambes (hanche, genou, pied)."""
    p = P
    arm = bpy.data.armatures.new("Lea_squelette"); rig = bpy.data.objects.new("Lea_rig", arm)
    bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones

    def bone(n, h, t, parent=None):
        b = eb.new(n); b.head = Vector(h); b.tail = Vector(t)
        if parent:
            b.parent = eb[parent]; b.use_connect = False
        return b
    bone("bassin", (0, 0, p["crotch_z"]), (0, 0, p["crotch_z"] + 0.15))
    bone("colonne", (0, 0, p["crotch_z"] + 0.15), (0, 0, p["shoulder_z"]), "bassin")
    bone("cou", (0, 0, p["shoulder_z"]), (0, 0, p["head_z"] - p["head_rz"]), "colonne")
    bone("tete", (0, 0, p["head_z"] - p["head_rz"]), (0, 0, p["head_z"] + p["head_rz"]), "cou")
    for s, n in ((-1, "G"), (1, "D")):
        sx, sz = s * (p["shoulder_x"] + 0.01), p["shoulder_z"] - 0.02
        ex, ez = s * (p["shoulder_x"] + 0.03), (p["shoulder_z"] + p["hand_z"]) / 2
        bone(f"bras_{n}", (sx, 0, sz), (ex, 0, ez), "colonne")
        bone(f"avant_bras_{n}", (ex, 0, ez), (s * p["hand_x"], 0, p["hand_z"] + 0.04), f"bras_{n}")
        bone(f"main_{n}", (s * p["hand_x"], 0, p["hand_z"] + 0.04), (s * p["hand_x"], 0, p["hand_z"] - 0.06), f"avant_bras_{n}")
        bone(f"cuisse_{n}", (s * p["leg_x"], 0, p["crotch_z"]), (s * p["leg_x"], 0, 0.22), "bassin")
        bone(f"tibia_{n}", (s * p["leg_x"], 0, 0.22), (s * p["leg_x"], 0, 0.06), f"cuisse_{n}")
        bone(f"pied_{n}", (s * p["leg_x"], 0, 0.06), (s * p["leg_x"], -0.1, 0.02), f"tibia_{n}")
    bpy.ops.object.mode_set(mode="OBJECT")
    # le corps suit le squelette (poids automatiques) ; tête, cheveux et écharpe suivent leurs os
    for o in bpy.context.view_layer.objects:
        o.select_set(o in (parts["body"], rig))
    bpy.context.view_layer.objects.active = rig
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except RuntimeError as err:  # en cas d'échec des poids automatiques, simple parentage (le modèle reste utilisable)
        print("poids automatiques indisponibles :", err)
        parts["body"].parent = rig
    for key, b in (("head", "tete"), ("hair", "tete"), ("scarf", "cou")):
        o = parts[key]; mw = o.matrix_world.copy(); o.parent = rig; o.parent_type = "BONE"; o.parent_bone = b; o.matrix_world = mw
    return rig


def stage():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.render.resolution_x, sc.render.resolution_y = 900, 1200; sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    # monde : gris neutre vu par la caméra, lumière d'ambiance douce et blanche
    w = bpy.data.worlds.new("Monde"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    lp = nt.nodes.new("ShaderNodeLightPath")
    bg_cam = nt.nodes.new("ShaderNodeBackground"); bg_cam.inputs["Color"].default_value = srgb("#8c8d91"); bg_cam.inputs["Strength"].default_value = 1.0
    bg_light = nt.nodes.new("ShaderNodeBackground"); bg_light.inputs["Color"].default_value = (1, 1, 1, 1); bg_light.inputs["Strength"].default_value = 0.85
    mix = nt.nodes.new("ShaderNodeMixShader"); out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); nt.links.new(bg_light.outputs[0], mix.inputs[1]); nt.links.new(bg_cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    # sol (ombre portée douce) et deux lumières larges
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0)); fl = bpy.context.active_object; fl.name = "Sol"
    fl.data.materials.append(mat_diffuse("Sol", "#8c8d91", 0.95, 0.0)); fl.is_shadow_catcher = True
    for name, loc, energy, size in (("Cle", (-1.6, -2.6, 3.0), 260, 2.5), ("Contre", (1.8, 2.2, 2.4), 140, 2.0)):
        L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size
        o = bpy.data.objects.new(name, L); bpy.context.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 0.8)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")); bpy.context.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.15
    return cam


def render_views(rig, cam):
    OUT.mkdir(exist_ok=True)
    files = []
    for name, yaw in (("face", 0), ("trois_quarts", -35), ("profil", -90)):
        rig.rotation_euler = (0, 0, math.radians(yaw)); bpy.context.view_layer.update()
        cam.location = (0, -6, 0.84); cam.rotation_euler = (math.radians(90), 0, 0)
        bpy.context.scene.render.filepath = str(OUT / f"lea_{name}.png")
        bpy.ops.render.render(write_still=True); files.append(OUT / f"lea_{name}.png")
    rig.rotation_euler = (0, 0, 0)
    return files


if __name__ == "__main__":
    reset()
    parts = build_lea()
    rig = build_rig(parts)
    cam = stage()
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "lea.blend"))
    for f in render_views(rig, cam):
        print("rendu", f)
    sys.exit(0)
