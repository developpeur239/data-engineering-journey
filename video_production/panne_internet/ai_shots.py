"""Plans en 3D stylisée générés par IA (Kie.ai) : personnages de référence, puis une image et un clip par plan.

    python ai_shots.py <work> refs          # images de référence de Marc et de son fils
    python ai_shots.py <work> shots 2 32    # première image + clip Kling pour ces scènes

Aucun texte lisible, aucune marque ni logo réel dans les images (les écrans affichent des pictogrammes).
"""
from __future__ import annotations

import sys
from pathlib import Path

import kie

STYLE = ("High-end 3D animated feature film still, stylized but physically based rendering, soft subsurface "
         "skin, detailed fabric and hair, cinematic lighting, shallow depth of field, winter in Paris, palette "
         "of deep blue and teal with warm orange accent lights, no text, no letters, no logos, no watermark.")

MARC = ("Marc, a 34-year-old Parisian man, slim, short dark brown hair, light stubble, tired kind eyes, "
        "navy wool coat over a grey hoodie, dark jeans, white sneakers, a small backpack")
SON = ("his 2-year-old son, round cheeks, curly light brown hair, yellow puffer snowsuit and a knitted "
       "orange beanie")

REFS = {
    "marc_sheet": (f"Character reference sheet of {MARC}. Three views side by side on a plain neutral dark "
                   f"teal background: front, three-quarter, profile. Full body, neutral pose. {STYLE}"),
    "marc_son": (f"{MARC}, holding {SON} on his hip in a Paris apartment kitchen at dawn, both looking at "
                 f"the camera, medium shot. {STYLE}"),
}

# scène : (image de départ, mouvement du clip)
SHOTS = {
    2: (f"Entrance hall of a Paris metro station at 7:45 am in winter, tiled walls, commuters blurred in the "
        f"background. {MARC} stands at a ticket vending machine and taps his bank card on the reader; the "
        f"machine screen glows red with a large cross pictogram. Over-the-shoulder medium shot, 35 mm lens. {STYLE}",
        "The man taps his bank card on the reader again, the red screen blinks, he frowns and looks at the "
        "card in disbelief. Slow push-in of the camera towards his face, commuters walk past in the background, "
        "steam of breath in the cold air. Natural, realistic motion."),
    32: (f"Inside a small Paris pharmacy at night, warm green cross sign glowing through the window, shelves "
         f"of boxes softly blurred. {MARC} holds {SON} who has a fever, red cheeks, head on his father's "
         f"shoulder. Across the counter a pharmacist in a white coat looks at a dark computer screen and shakes "
         f"his head. Medium shot from the side. {STYLE}",
         "The pharmacist shakes his head slowly and spreads his hands apologetically; the father leans forward, "
         "worried, gently rocking his feverish son. Slow lateral camera move along the counter, the green cross "
         "light flickers softly outside. Natural, realistic motion."),
}


def refs(work: Path):
    out = {}
    for name, prompt in REFS.items():
        ref = [out["marc_sheet"]] if "marc_sheet" in out else []
        out[name] = kie.image(prompt, work / "ai" / f"ref_{name}.png", refs=ref)
        print("  référence :", out[name], flush=True)
    return out


def shots(work: Path, scenes):
    r = refs(work)
    for sc in scenes:
        still_prompt, motion = SHOTS[sc]
        still = kie.image(still_prompt, work / "ai" / f"s{sc:02d}_still.png", refs=[r["marc_sheet"], r["marc_son"]])
        print("  image :", still, flush=True)
        vid = kie.clip(motion, still, work / "ai" / f"s{sc:02d}_clip.mp4")
        print("  clip :", vid, flush=True)


if __name__ == "__main__":
    w, what = Path(sys.argv[1]), sys.argv[2]
    print(f"Crédits Kie avant : {kie.credits():.0f}")
    refs(w) if what == "refs" else shots(w, [int(x) for x in sys.argv[3:]])
    print(f"Crédits Kie après : {kie.credits():.0f}")
