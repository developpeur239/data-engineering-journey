"""Bloc 3 : voix (3 passages, 1 045 caractères) + 2 images (rue de jour, enfants) + 2 bruitages. Cache : rien n'est regénéré.
À NE LANCER QU'APRÈS VALIDATION DU COÛT PAR L'UTILISATEUR.
    KIE_API_KEY=proxy-injected ELEVENLABS_API_KEY=proxy-injected python3 b03/generer.py [voix] [images] [sons]"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUNE = HERE.parents[1]
sys.path.insert(0, str(LUNE.parent / "panne_internet"))

STYLE = ("Flat 2D vector illustration, same drawing style, line quality and palette as the reference image, "
         "but in soft morning daylight. No text, no letters, no signs with writing, no logos.")
RUE = ("The same small French town street as the reference image, the next morning in clear daylight, wide shot: "
       "pale blue sky with a few light clouds over the upper third, a small pale normal-size daytime Moon high in the "
       "upper right of the sky, plenty of empty sky above the roofs for a distant plane; on the left side a primary "
       "school with a low wall and an open green metal gate leading to a small schoolyard with a tree; on the right side "
       "a small restaurant on the ground floor with an empty terrace (folded chairs stacked, a closed parasol) and a "
       "large shop window whose metal roller shutter is fully closed; stone houses with shutters, parked cars, "
       "quiet cobbled street. No people, no plane, no birds. " + STYLE)
ENFANTS = ("Character sheet on a plain flat light grey background, five separate full-body figures standing side by side "
           "with space between them, seen in three-quarter back view, standing still and waiting: three school children "
           "(about 8 years old) wearing small backpacks, one holding a parent's hand, and one adult parent. Same minimalist "
           "character design, proportions and thin discreet outline as the reference image, matte colors, soft daylight, "
           "no shadow on the ground, no text.")


def voix():
    from render import tts_elevenlabs  # noqa: PLC0415
    n = sum(tts_elevenlabs(t, HERE / f"{k}.wav", "aQROLel5sQbj1vuIVi6B", "eleven_v4", 0.7, 0.5)
            for k, t in json.loads((HERE / "voix.json").read_text()).items())
    print("caractères facturés :", n)


def images():
    import kie  # noqa: PLC0415
    print(kie.image(RUE, HERE / "rue_jour.png", refs=[LUNE / "film/b01/rue_lune.png"], aspect="16:9", resolution="2K"))
    print(kie.image(ENFANTS, HERE / "enfants.png", refs=[LUNE / "film/b01/figurants_dos.png"], aspect="16:9", resolution="2K"))


def sons():
    import sfx_real  # noqa: PLC0415
    sfx_real.LIBRARY["amb_matin"] = ("Quiet small French town street on a weekday morning: a few distant children's voices "
                                     "near a school, a door, birds, light distant traffic, calm, no music, seamless ambience", 10.0, 0.45)
    sfx_real.LIBRARY["avion"] = ("A jet airliner climbing after take-off, heard from far away in a town, smooth rising "
                                 "then fading roar, no other sounds", 6.0, 0.5)
    print(sfx_real.generate(HERE, ["amb_matin", "avion"]))


if __name__ == "__main__":
    what = sys.argv[1:] or ["voix", "images", "sons"]
    for w in what:
        globals()[w]()
