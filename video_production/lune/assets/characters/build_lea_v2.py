"""Léa V2 : mains à cinq doigts articulés (la V1, build_lea.py et lea.blend, reste intacte).

    python3 build_lea_v2.py stills     # lea_v2.blend + planche des mains (renders/mains_*.png)
    python3 build_lea_v2.py clavier    # animation de 5 s : Léa tape au clavier (renders/lea_clavier.mp4)
    python3 build_lea_v2.py telephone  # animation de 5 s : Léa prend son téléphone, le tient, tape du pouce, le repose

Mains : paume arrondie, quatre doigts courts en léger éventail et un pouce opposable, fondus en une seule surface
(remaillage voxel puis lissage) ; espaces visibles entre les doigts ; noir mat comme le visage ; contour blanc.
Squelette : main, puis deux phalanges par doigt (pouce compris), axes orientés pour que la flexion soit une rotation
autour de l'axe X local. Les poids de la main sont calculés à la main (os le plus proche, fondu aux articulations), ce
qui évite que deux doigts voisins se déforment ensemble. Bras pilotés par cinématique inverse (IK avec orientation).
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_lea as L  # noqa: E402

HERE, OUT = L.HERE, L.OUT
P = L.P
P["hands_in_body"] = False
FINGERS = ["index", "majeur", "annulaire", "auriculaire"]
# (décalage dans la largeur de la paume, rayon, phalange 1, phalange 2, ouverture en degrés)
FDIM = [(-0.0255, 0.0076, 0.019, 0.015, -8), (-0.0085, 0.0079, 0.021, 0.016, -3), (0.0085, 0.0076, 0.02, 0.015, 3), (0.0255, 0.0068, 0.016, 0.012, 8)]
SIDES = ((-1, "G"), (1, "D"))
HK = 1.18   # échelle de la main (la référence a des mains pleines et lisibles de loin)


def wrist(s):
    return Vector((s * P["hand_x"], 0.0, P["hand_z"] + 0.04))


def hand_layout(s):
    """Points des os de la main au repos (main pendante, doigts vers le bas, paume tournée vers le corps)."""
    w = wrist(s); knuckle_z = w.z - 0.066 * HK
    out = {"main": (w, Vector((w.x, 0.0, knuckle_z)))}
    for (dy, r, l1, l2, fan), f in zip(FDIM, FINGERS):
        a = math.radians(fan); d = Vector((0.0, math.sin(a), -math.cos(a)))
        b0 = Vector((w.x - s * 0.002 * (abs(dy) < 0.01), dy * HK, knuckle_z)); b1 = b0 + d * l1 * HK; b2 = b1 + d * l2 * 0.95 * HK
        out[f] = (b0, b1, b2, r * HK)
    td = Vector((-s * 0.25, -0.5, -0.83)).normalized()
    t0 = w + Vector((-s * 0.007, -0.029, -0.034)) * HK; t1 = t0 + td * 0.019 * HK; t2 = t1 + td * 0.016 * HK
    out["pouce"] = (t0, t1, t2, 0.0088 * HK)
    return out


def build_hand(s, skin, outl):
    lay = hand_layout(s); w = wrist(s)
    parts = [L.ellipsoid(tuple(w + Vector((0, 0, -0.037 * HK))), (0.019 * HK, 0.036 * HK, 0.038 * HK))]                  # paume
    parts.append(L.ellipsoid(tuple(w + Vector((0, 0, 0.008))), (0.02 * HK, 0.027 * HK, 0.036)))      # poignet, aplati comme la paume
    for f in FINGERS + ["pouce"]:
        b0, b1, b2, r = lay[f]
        start = b0 + (b0 - b1).normalized() * 0.012                                                   # la base plonge dans la paume
        parts += L.capsule(tuple(start), tuple(b1), r)
        parts += L.capsule(tuple(b1), tuple(b2), r * 0.92)
    h = L.fuse(f"Lea_main_{'G' if s < 0 else 'D'}", parts, skin, voxel=0.0009, smooth=14)
    L.add_outline(h, outl, P["outline_w"] * 0.5)
    return h


def seg_dist(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared)); return (p - (a + ab * t)).length, t


def weight_hand(h, s, rig):
    """Poids : l'os le plus proche, fondu avec son parent près de l'articulation (aucun lien entre doigts voisins)."""
    n = "G" if s < 0 else "D"; lay = hand_layout(s)
    segs = [(f"main_{n}", lay["main"][0], lay["main"][1], f"avant_bras_{n}")]
    for f in FINGERS + ["pouce"]:
        b0, b1, b2, _ = lay[f]
        segs += [(f"{f}_1_{n}", b0, b1, f"main_{n}"), (f"{f}_2_{n}", b1, b2, f"{f}_1_{n}")]
    groups = {}
    for name in {x[0] for x in segs} | {x[3] for x in segs}:
        groups[name] = h.vertex_groups.new(name=name)
    knuckle_z = lay["main"][1].z; fsegs = [sg for sg in segs if not sg[0].startswith("main")]
    tsegs = [sg for sg in fsegs if sg[0].startswith("pouce")]
    for v in h.data.vertices:
        p = h.matrix_world @ v.co
        near_thumb = min(seg_dist(p, sg[1], sg[2])[0] for sg in tsegs) < 0.0125
        if p.z > knuckle_z + 0.003 and not near_thumb:          # paume et poignet : os de la main, fondu vers l'avant-bras
            t = max(0.0, min(1.0, (lay["main"][0].z - p.z) / (lay["main"][0].z - knuckle_z)))
            wp = 0.6 * max(0.0, 1 - t / 0.35)
            groups[f"main_{n}"].add([v.index], 1 - wp, "REPLACE")
            if wp > 0:
                groups[f"avant_bras_{n}"].add([v.index], wp, "REPLACE")
            continue
        best = min(fsegs, key=lambda sg: seg_dist(p, sg[1], sg[2])[0])
        _, t = seg_dist(p, best[1], best[2])
        wp = 0.5 * max(0.0, 1 - t / 0.3) if t < 0.3 else 0.0
        groups[best[0]].add([v.index], 1 - wp, "REPLACE")
        if wp > 0:
            groups[best[3]].add([v.index], wp, "REPLACE")
    mod = h.modifiers.new("Squelette", "ARMATURE"); mod.object = rig
    # le contour (solidify) doit suivre la déformation : il passe après le squelette
    bpy.context.view_layer.objects.active = h
    while h.modifiers.find("Squelette") > 0:
        bpy.ops.object.modifier_move_up(modifier="Squelette")
    h.parent = rig


def add_finger_bones(rig):
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode="EDIT"); eb = rig.data.edit_bones
    for s, n in SIDES:
        lay = hand_layout(s); palm_n = Vector((-s, 0, 0))
        m = eb[f"main_{n}"]; m.head, m.tail = lay["main"]; m.align_roll(palm_n)
        for f in FINGERS + ["pouce"]:
            b0, b1, b2, _ = lay[f]
            up = palm_n if f != "pouce" else Vector((-s * 0.55, 1.0, 0.0)).normalized()   # le pouce se replie vers la paume
            for k, (a, b, par) in enumerate(((b0, b1, f"main_{n}"), (b1, b2, f"{f}_1_{n}")), 1):
                bb = eb.new(f"{f}_{k}_{n}"); bb.head, bb.tail = a, b; bb.parent = eb[par]; bb.use_connect = k == 2; bb.align_roll(up)
    bpy.ops.object.mode_set(mode="OBJECT")


def fade_body_outline(body, reach=0.07):
    """Le contour du corps s'efface près des poignets : il traverserait sinon la paume quand la main pivote."""
    vg = body.vertex_groups.new(name="contour_poids")
    ws = [wrist(s) for s, _ in SIDES]
    for v in body.data.vertices:
        p = body.matrix_world @ v.co; d = min((p - w).length for w in ws)
        k = max(0.0, min(1.0, (d - 0.015) / reach)); vg.add([v.index], k * k * (3 - 2 * k), "REPLACE")
    m = body.modifiers["Contour"]; m.vertex_group = "contour_poids"; m.thickness_vertex_group = 0.0


def ik_targets(rig):
    """Cibles IK des mains : la position de la paume et son orientation pilotent bras, avant-bras et main."""
    T = {}
    for s, n in SIDES:
        e = bpy.data.objects.new(f"cible_main_{n}", None); bpy.context.collection.objects.link(e); e.empty_display_size = 0.04
        e.rotation_mode = "QUATERNION"
        rest = rig.data.bones[f"main_{n}"].matrix_local.copy(); e.matrix_world = rig.matrix_world @ Matrix.Translation(rest.to_translation() * 0) @ rest
        ik = rig.pose.bones[f"avant_bras_{n}"].constraints.new("IK"); ik.target = e; ik.chain_count = 2; ik.use_tail = True; ik.use_stretch = False; ik.iterations = 500
        cr = rig.pose.bones[f"main_{n}"].constraints.new("COPY_ROTATION"); cr.target = e; cr.target_space = "WORLD"; cr.owner_space = "WORLD"
        T[n] = e
    return T


def place_target(e, rig, n, pos, R):
    """Place la cible : la tête de l'os de la main (poignet) en pos, orientation = R appliquée à l'orientation de repos."""
    rest = rig.data.bones[f"main_{n}"].matrix_local.to_3x3()
    e.matrix_world = Matrix.LocRotScale(Vector(pos), (R @ rest).to_quaternion(), None)


def Rx(a): return Matrix.Rotation(a, 3, "X")
def Ry(a): return Matrix.Rotation(a, 3, "Y")
def Rz(a): return Matrix.Rotation(a, 3, "Z")


def pose_fingers(rig, n, curl, thumb=None, spread=0.0):
    """curl : un réel ou un dict par doigt (radians, phalange 1) ; la phalange 2 suit à 0,8."""
    for f in FINGERS:
        c = curl[f] if isinstance(curl, dict) else curl
        for k, fac in ((1, 1.0), (2, 0.85)):
            pb = rig.pose.bones[f"{f}_{k}_{n}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (c * fac, 0, 0)
    t = thumb if thumb is not None else (curl if not isinstance(curl, dict) else 0.2)
    for k, fac in ((1, 0.7), (2, 1.0)):
        pb = rig.pose.bones[f"pouce_{k}_{n}"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (t * fac, 0, 0)


def key_fingers(rig, n, frame):
    for f in FINGERS + ["pouce"]:
        for k in (1, 2):
            rig.pose.bones[f"{f}_{k}_{n}"].keyframe_insert("rotation_euler", frame=frame)


def build():
    L.reset()
    parts = L.build_lea()
    rig = L.build_rig(parts)
    add_finger_bones(rig)
    skin = bpy.data.materials["Lea_peau"]; outl = bpy.data.materials["Contour_blanc"]
    hands = {}
    for s, n in SIDES:
        h = build_hand(s, skin, outl); weight_hand(h, s, rig); hands[n] = h
    fade_body_outline(parts["body"])
    T = ik_targets(rig)
    cam = L.stage()
    return rig, hands, T, cam


def render_still(path, res=(1000, 1000), samples=48):
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = res; sc.cycles.samples = samples
    sc.render.filepath = str(path); bpy.ops.render.render(write_still=True)


def aim_cam(cam, target, direction, scale):
    cam.data.type = "ORTHO"; cam.data.ortho_scale = scale
    d = Vector(direction).normalized(); cam.location = Vector(target) - d * 3
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def stills(rig, hands, T, cam):
    """Planche des mains : ouverte (face, profil, trois-quarts), fermée, prise (main présentée devant la poitrine)."""
    OUT.mkdir(exist_ok=True); files = []
    n, s = "D", 1
    pos = Vector((0.22, -0.42, 0.62))                       # main présentée devant le corps, hors des cheveux
    R_open = Rz(s * math.pi / 2) @ Rx(math.pi)              # doigts vers le haut, paume face à la caméra
    place_target(T[n], rig, n, pos, R_open)
    place_target(T["G"], rig, "G", wrist(-1), Matrix.Identity(3))
    poses = [("ouverte", 0.05, 0.0), ("demi", 0.7, 0.5), ("fermee", 1.45, 1.2)]
    centre = pos + Vector((0, 0, 0.06))
    for name, c, t in poses:
        pose_fingers(rig, n, c, thumb=t); bpy.context.view_layer.update()
        views = [("face", (0, 1, 0)), ("profil", (-1, 0, 0)), ("trois_quarts", (-0.6, 1, 0))] if name == "ouverte" else [("face", (0, 1, 0)), ("trois_quarts", (-0.6, 1, 0))]
        for vn, d in views:
            aim_cam(cam, centre, d, 0.24); f = OUT / f"mains_{name}_{vn}.png"; render_still(f, (800, 800), samples=24); files.append(f)
    # main pendante au repos, vue d'ensemble pour juger la taille par rapport au corps
    place_target(T[n], rig, n, wrist(1), Matrix.Identity(3)); pose_fingers(rig, n, 0.15, thumb=0.1); pose_fingers(rig, "G", 0.15, thumb=0.1)
    bpy.context.view_layer.update(); cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.15; cam.location = (0, -6, 0.84); cam.rotation_euler = (math.radians(90), 0, 0)
    f = OUT / "mains_ensemble.png"; render_still(f, (900, 1200), samples=24); files.append(f)
    return files


def contact_sheet(files, out, cols=4, tile=480):
    from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
    font = ImageFont.truetype(str(HERE.parents[1] / "prototype/fonts/InstrumentSans-Bold.ttf"), 22)
    rows = math.ceil(len(files) / cols); sheet = Image.new("RGB", (cols * tile, rows * (tile + 40)), (40, 42, 46)); d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB"); im.thumbnail((tile, tile)); x, y = (i % cols) * tile, (i // cols) * (tile + 40)
        sheet.paste(im, (x + (tile - im.width) // 2, y + 40)); d.text((x + 10, y + 8), Path(f).stem.replace("mains_", "").replace("_", " · "), fill=(235, 236, 238), font=font)
    sheet.save(out); return out



# ---------------------------------------------------------------------------------------------------------------
# Animations : Léa assise à son bureau
# ---------------------------------------------------------------------------------------------------------------
FPS, NF = 24, 120
SEAT_DROP = 0.19          # le personnage descend de 19 cm pour s'asseoir (genoux à 0,22 m)
DESK_Z, KB_Y, KEY_TOP = 0.46, -0.33, 0.484


def point_bone(rig, name, direction):
    """Oriente un os (pose) le long d'une direction, en espace armature, sans changer sa tête."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; rest = rig.data.bones[name].matrix_local.to_3x3()
    q = Vector(rest.col[1]).rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.LocRotScale(pb.head.copy(), q @ rest.to_quaternion(), None)
    bpy.context.view_layer.update()


def seat(rig):
    rig.location.z = -SEAT_DROP
    for _, n in SIDES:
        point_bone(rig, f"cuisse_{n}", (0, -1, -0.05)); point_bone(rig, f"tibia_{n}", (0, 0.08, -1)); point_bone(rig, f"pied_{n}", (0, -1, -0.3))


def mat(name, color, rough=0.7):
    return L.mat_diffuse(name, color, rough, 0.2)


def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True); o.data.materials.append(m)
    bev = o.modifiers.new("Arrondi", "BEVEL"); bev.width = min(size) * 0.25; bev.segments = 3
    return o


def office(with_phone=False):
    """Bureau, clavier à touches séparées, écran, chaise ; téléphone posé écran contre le bureau."""
    grey, dark, keyc, wood = mat("Gris", "#3a3d43"), mat("Noir_meuble", "#1d1f23"), mat("Touche", "#d9dcdf", 0.5), mat("Bois", "#7b6650", 0.6)
    box("Plateau", (1.1, 0.6, 0.03), (0, -0.48, DESK_Z - 0.015), wood)
    for x in (-0.52, 0.52):
        box("Pied_bureau", (0.04, 0.55, DESK_Z - 0.03), (x, -0.48, (DESK_Z - 0.03) / 2), dark)
    box("Clavier", (0.36, 0.12, 0.012), (0, KB_Y, DESK_Z + 0.006), dark)
    keys = []
    for r in range(4):
        for c in range(12):
            k = box(f"Touche_{r}_{c}", (0.024, 0.022, 0.012), (-0.154 + c * 0.028, KB_Y + 0.042 - r * 0.028, KEY_TOP - 0.006), keyc); keys.append(k)
    box("Ecran", (0.48, 0.03, 0.3), (0.12, -0.7, DESK_Z + 0.25), dark)
    scr = bpy.data.materials.new("Ecran_lumiere"); scr.use_nodes = True; nt = scr.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = L.srgb("#7fb7d6"); em.inputs["Strength"].default_value = 1.6
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0])
    box("Ecran_dalle", (0.44, 0.005, 0.26), (0.12, -0.684, DESK_Z + 0.25), scr)
    box("Pied_ecran", (0.05, 0.05, 0.1), (0.12, -0.72, DESK_Z + 0.05), dark)
    # chaise : assise sous les cuisses, dossier, pied central
    box("Assise", (0.42, 0.4, 0.05), (0, -0.02, 0.18), grey); box("Dossier", (0.4, 0.05, 0.38), (0, 0.2, 0.42), grey)
    box("Pied_chaise", (0.05, 0.05, 0.16), (0, -0.02, 0.08), dark)
    phone = None
    if with_phone:
        phone = make_phone()
    return keys, phone


def make_phone():
    """Téléphone : coque sombre, écran avec l'interface de messagerie validée (état 1 de la planche)."""
    from PIL import Image  # noqa: PLC0415
    sheet = HERE.parents[1] / "references_design/4b_telephone_six_etats.png"
    tex_path = OUT / "telephone_ecran.png"
    Image.open(sheet).crop((40, 100, 310, 650)).rotate(90, expand=True).save(tex_path)
    body = box("Telephone", (0.14, 0.07, 0.008), (0, 0, 0), mat("Coque", "#16171a", 0.35))
    m = bpy.data.materials.new("Telephone_ecran"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(str(tex_path))
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.2
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(tx.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.0041)); scr = bpy.context.active_object; scr.name = "Telephone_dalle"
    scr.scale = (0.132, 0.064, 1); bpy.ops.object.transform_apply(scale=True); scr.data.materials.append(m)
    scr.parent = body
    return body


def tip(rig, n, f):
    return rig.matrix_world @ rig.pose.bones[f"{f}_2_{n}"].tail


def anim_camera(cam, loc, target, lens=40):
    cam.data.type = "PERSP"; cam.data.lens = lens; cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def render_anim(name):
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, NF; sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = 960, 540; sc.cycles.samples = 10
    d = OUT / f"_{name}"; d.mkdir(exist_ok=True); sc.render.filepath = str(d / "f_")
    sc.render.image_settings.file_format = "PNG"; bpy.ops.render.render(animation=True)
    mp4 = OUT / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(d / "f_%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", str(mp4)], check=True)
    return mp4


def keyboard_anim(rig, T, cam, preview=False):
    keys, _ = office()
    seat(rig)
    R_type = {n: Ry(-s * math.pi / 2) @ Rx(-math.pi / 2) @ Rx(0.12) for s, n in SIDES}   # paume vers le bas, poignet à peine relevé
    base = {n: Vector((s * 0.085, KB_Y + 0.095, KEY_TOP + 0.05)) for s, n in SIDES}
    rest_curl = {"index": 0.62, "majeur": 0.6, "annulaire": 0.62, "auriculaire": 0.66}
    # hauteur : les doigts frappés touchent le dessus des touches
    for s, n in SIDES:
        place_target(T[n], rig, n, base[n], R_type[n]); pose_fingers(rig, n, {**rest_curl, "index": 1.0}, thumb=0.35); bpy.context.view_layer.update()
        base[n].z -= tip(rig, n, "index").z - (KEY_TOP + 0.002)
    rng = [((-1) ** i, FINGERS[(i * 7) % 4] if i % 3 else "index") for i in range(40)]
    taps = []
    t = 8
    for i, (s, f) in enumerate(rng):
        if t > NF - 8:
            break
        taps.append((t, "G" if s < 0 else "D", f)); t += 5 + (i % 3)
    for fr in range(1, NF + 1):
        bpy.context.scene.frame_set(fr)
        for s, n in SIDES:
            drift = Vector((0.012 * math.sin(fr / 17 + s), 0.008 * math.sin(fr / 23), 0.003 * math.sin(fr / 9 + s)))
            place_target(T[n], rig, n, base[n] + drift, R_type[n]); T[n].keyframe_insert("location", frame=fr); T[n].keyframe_insert("rotation_quaternion", frame=fr)
            curl = dict(rest_curl)
            for (tf, tn, ff) in taps:
                if tn == n and abs(fr - tf) <= 3:
                    curl[ff] = rest_curl[ff] + 0.38 * (1 - abs(fr - tf) / 3.0)
            pose_fingers(rig, n, curl, thumb=0.35); key_fingers(rig, n, fr)
    # chaque frappe enfonce la touche réellement atteinte par le bout du doigt
    for (tf, tn, ff) in taps:
        bpy.context.scene.frame_set(tf); p = tip(rig, tn, ff)
        k = min(keys, key=lambda o: (Vector((o.location.x, o.location.y)) - Vector((p.x, p.y))).length)
        z0 = KEY_TOP - 0.006
        for fr, z in ((tf - 2, z0), (tf, z0 - 0.0045), (tf + 2, z0)):
            k.location.z = z; k.keyframe_insert("location", index=2, frame=fr)
    anim_camera(cam, (-0.58, -1.3, 0.92), (0.02, -0.2, 0.72), 34)
    bpy.context.scene.frame_set(1)
    if preview:
        return [preview_frames("clavier", (1, 40, 80))]
    return render_anim("lea_clavier")


def phone_anim(rig, T, cam, preview=False):
    keys, phone = office(with_phone=True)
    seat(rig)
    n, s = "D", 1
    R_down = Ry(-s * math.pi / 2) @ Rx(-math.pi / 2)
    R_hold = Rx(-0.35) @ Ry(s * math.pi / 2) @ Rx(-math.pi / 2) @ Rz(-0.25)
    rest_curl = {"index": 0.6, "majeur": 0.58, "annulaire": 0.6, "auriculaire": 0.64}
    # le téléphone est posé écran contre le bureau, en travers, à portée de la main gauche du plan
    ph_pos = Vector((0.33, -0.3, DESK_Z + 0.004 + 0.0001))
    phone.location = ph_pos; phone.rotation_euler = (math.pi, 0, 0)
    wrist_grab = ph_pos + Vector((0, 0.075, 0.042))
    wrist_idle = Vector((0.24, KB_Y + 0.12, KEY_TOP + 0.06)); wrist_hold = Vector((0.22, -0.25, 0.58))
    G = {"G": Vector((-0.085, KB_Y + 0.095, KEY_TOP + 0.04))}
    def ease(x):
        x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
    def slerpR(a, b, k):
        return a.to_quaternion().slerp(b.to_quaternion(), k).to_matrix()
    plan = []   # (image, position du poignet, orientation, ouverture des doigts, pouce)
    for fr in range(1, NF + 1):
        if fr < 18:   pos, R, c, th = wrist_idle, R_down, 0.6, 0.35
        elif fr < 36: k = ease((fr - 18) / 18); pos, R, c, th = wrist_idle.lerp(wrist_grab + Vector((0, 0, 0.03)), k), R_down, 0.6 - 0.45 * k, 0.35 - 0.25 * k
        elif fr < 42: k = ease((fr - 36) / 6); pos, R, c, th = (wrist_grab + Vector((0, 0, 0.03))).lerp(wrist_grab, k), R_down, 0.15 + 0.9 * k, 0.1 + 0.45 * k
        elif fr < 62: k = ease((fr - 42) / 20); pos, R, c, th = wrist_grab.lerp(wrist_hold, k), slerpR(R_down, R_hold, k), 1.05 - 0.35 * k, 0.55 - 0.25 * k
        elif fr < 96: pos, R, c = wrist_hold + Vector((0, 0, 0.004 * math.sin(fr / 6))), R_hold, 0.7; th = 0.3 + 0.45 * max(0.0, math.sin((fr - 62) / 34 * 3 * math.pi))
        elif fr < 112: k = ease((fr - 96) / 16); pos, R, c, th = wrist_hold.lerp(wrist_grab, k), slerpR(R_hold, R_down, k), 0.7 + 0.35 * k, 0.3 + 0.25 * k
        else: k = ease((fr - 112) / 8); pos, R, c, th = wrist_grab.lerp(wrist_grab + Vector((0, 0.03, 0.035)), k), R_down, 1.05 - 0.6 * k, 0.55 - 0.3 * k
        plan.append((fr, pos, R, c, th))
    for fr, pos, R, c, th in plan:
        bpy.context.scene.frame_set(fr)
        place_target(T[n], rig, n, pos, R); T[n].keyframe_insert("location", frame=fr); T[n].keyframe_insert("rotation_quaternion", frame=fr)
        pose_fingers(rig, n, c if isinstance(c, dict) else {f: c + (rest_curl[f] - 0.6) for f in FINGERS}, thumb=th); key_fingers(rig, n, fr)
        place_target(T["G"], rig, "G", G["G"] + Vector((0.008 * math.sin(fr / 15), 0, 0)), Ry(math.pi / 2) @ Rx(-math.pi / 2) @ Rx(0.12))
        T["G"].keyframe_insert("location", frame=fr); T["G"].keyframe_insert("rotation_quaternion", frame=fr)
        pose_fingers(rig, "G", rest_curl, thumb=0.35); key_fingers(rig, "G", fr)
    # le téléphone suit la main entre la prise (image 42) et la pose (image 112) : contrainte « enfant de »
    bpy.context.scene.frame_set(42); bpy.context.view_layer.update()
    c = phone.constraints.new("CHILD_OF"); c.target = rig; c.subtarget = f"main_{n}"
    c.inverse_matrix = (rig.matrix_world @ rig.pose.bones[f"main_{n}"].matrix).inverted()
    for fr, inf in ((41, 0.0), (42, 1.0), (112, 1.0), (113, 0.0)):
        c.influence = inf; c.keyframe_insert("influence", frame=fr)
    # à la pose, le téléphone reste là où la main l'a déposé
    bpy.context.scene.frame_set(112); bpy.context.view_layer.update(); final = phone.matrix_world.copy()
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "CONSTANT"   # le téléphone ne glisse pas entre deux clés
    for fr in (1, 112):
        phone.location = ph_pos if fr == 1 else final.to_translation(); phone.rotation_euler = (math.pi, 0, 0) if fr == 1 else final.to_euler()
        phone.keyframe_insert("location", frame=fr); phone.keyframe_insert("rotation_euler", frame=fr)
    phone.location = final.to_translation(); phone.rotation_euler = final.to_euler()
    phone.keyframe_insert("location", frame=113); phone.keyframe_insert("rotation_euler", frame=113)
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "BEZIER"
    anim_camera(cam, (0.72, 0.16, 0.84), (0.2, -0.27, 0.55), 34)
    bpy.context.scene.frame_set(1)
    if preview:
        return [preview_frames("telephone", (1, 30, 45, 75, 105, 118))]
    return render_anim("lea_telephone")


def preview_frames(name, frames):
    from PIL import Image  # noqa: PLC0415
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y = 640, 360; sc.cycles.samples = 8
    ims = []
    for fr in frames:
        sc.frame_set(fr); p = OUT / f"_apercu_{name}_{fr}.png"; sc.render.filepath = str(p); bpy.ops.render.render(write_still=True); ims.append(Image.open(p))
    W = Image.new("RGB", (640 * min(3, len(ims)), 360 * math.ceil(len(ims) / 3)))
    for i, im in enumerate(ims):
        W.paste(im, ((i % 3) * 640, (i // 3) * 360))
    out = OUT / f"apercu_{name}.png"; W.save(out); return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stills"
    rig, hands, T, cam = build()
    if mode == "stills":
        bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "lea_v2.blend"))
        fs = stills(rig, hands, T, cam)
        print("planche", contact_sheet(fs, OUT / "mains_planche.png"))
    elif mode in ("clavier", "clavier_apercu"):
        print("clavier", keyboard_anim(rig, T, cam, preview=mode.endswith("apercu")))
    elif mode in ("telephone", "telephone_apercu"):
        print("telephone", phone_anim(rig, T, cam, preview=mode.endswith("apercu")))
    sys.exit(0)
