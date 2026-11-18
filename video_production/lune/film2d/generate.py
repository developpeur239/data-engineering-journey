"""Images 2D du prototype (Nano Banana via Kie.ai) : 5 décors et 6 poses de personnages.
    KIE_API_KEY=proxy-injected python3 generate.py      (cache : une image déjà présente n'est pas regénérée)"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "panne_internet"))
import kie  # noqa: E402

IMG = HERE / "images"
REF = HERE.parent / "references_design/personnages/reference_2d.png"
CROPS = {"lea": (100, 280, 450, 860), "mere": (500, 260, 800, 860), "garcon": (900, 380, 1200, 860), "collegue": (1290, 240, 1600, 860)}
for k, box in CROPS.items():
    p = IMG / f"ref_{k}.png"
    if not p.exists():
        Image.open(REF).convert("RGB").crop(box).save(p)

STYLE = ("Flat 2D vector illustration for an animated documentary, soft gradients, cinematic atmospheric lighting, "
         "muted desaturated palette, clean shapes, subtle depth of field on far objects, no text, no letters, no logos")
BG = {
    "decor_calern_nuit": "Interior of a professional astronomical observatory dome at night, wide shot. A large white telescope in the "
        "center under the open dome slit showing a starry sky; on the right a modern scientific workstation desk with two glowing "
        "monitors showing graphs, a keyboard and an empty office chair; on the left a doorway open to a warmly lit corridor; technical "
        "racks with tiny status lights; dim red safety lights and cool blue light from the screens, soft haze. No people. " + STYLE,
    "decor_calern_jour": "The same astronomical observatory dome interior in calm daylight, wide shot: large white telescope in the "
        "center, the dome slit open on a bright blue sky, the scientific workstation desk with two monitors on the right with an empty "
        "chair, the doorway on the left; soft natural light, peaceful ordinary morning. No people. " + STYLE,
    "decor_espace": "Outer space, the Earth and the Moon touching: the Moon is breaking apart against the Earth with a huge "
        "blinding white-orange flash of light at the contact point, glowing debris, black starry background, dramatic but simple, "
        "seen from far away. " + STYLE,
    "decor_plage": "A calm sunny beach in late morning, wide shot: soft sand in the foreground with a few footprints, gentle "
        "irregular waves with white foam, a low dune with beach grass on the left, rocks on the right, a wooden boardwalk far behind, "
        "light haze on the horizon, bright and peaceful. No people. " + STYLE,
}
KEY = ("Pure flat magenta background (#FF00FF) filling the whole image, no floor, no shadow on the background, "
       "the character only, fully visible, centered, flat 2D vector style exactly like the reference character: "
       "pure black head and body without any shading, small white oval eyes, simple rounded limbs.")
CH = {
    "lea_profil": ("lea", "The woman from the reference (copper-red bob haircut, yellow scarf, black body) sitting on an office chair seen "
                   "exactly from the side, facing right, typing on an invisible keyboard at table height, slightly worried eyes. " + KEY),
    "lea_face": ("lea", "The woman from the reference (copper-red bob haircut, yellow scarf, black body) sitting on an office chair, "
                 "having turned her chair toward the viewer, three-quarter front view, calm determined eyes, hands resting on her knees. " + KEY),
    "collegue_porte": ("collegue", "The man from the reference (short black hair, round glasses, badge) standing straight, seen from the "
                       "front, worried eyes, arms along the body, as if standing in a doorway. " + KEY),
    "collegue_marche": ("collegue", "The man from the reference (short black hair, round glasses, badge) walking to the left, seen from the "
                        "side, relaxed and smiling eyes, holding a coffee cup. " + KEY),
    "garcon_court": ("garcon", "The boy from the reference (brown hair, turquoise top, black body) running happily to the left, seen from "
                     "the side, holding a small red bucket in one hand. " + KEY),
    "mere_marche": ("mere", "The woman from the reference (long chestnut hair, cream coat, black body) walking calmly to the left, seen "
                    "from the side, gentle smiling eyes. " + KEY),
}


def job(name):
    out = IMG / f"{name}.png"
    if name in BG:
        return kie.image(BG[name], out, aspect="16:9", resolution="2K")
    ref, prompt = CH[name]
    return kie.image(prompt, out, refs=[IMG / f"ref_{ref}.png"], aspect="3:4", resolution="2K")


if __name__ == "__main__":
    names = sys.argv[1:] or list(BG) + list(CH)
    with ThreadPoolExecutor(4) as ex:
        for n, r in zip(names, ex.map(lambda n: (lambda: job(n))(), names)):
            print("ok", n, r, flush=True)
