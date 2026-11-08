"""Test Léa (interactions) : 2 images générées, en une fois. Cache : rien n'est regénéré.
    KIE_API_KEY=proxy-injected python3 test_lea/generer.py"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUNE = HERE.parents[1]
sys.path.insert(0, str(LUNE.parent / "panne_internet"))
import kie  # noqa: E402

LEA = LUNE / "film2d/images/lea_profil.png"
MAIN = LUNE / "insert_2d/main_ref/main_index_silhouette.png"
DECOR = LUNE / "film2d/images/decor_calern_nuit.png"
JOBS = {
    "mains": ("Animation model sheet: six separate drawings on a pure flat magenta background (#FF00FF), all at the same scale, "
              "evenly spaced in a 3x2 grid, not overlapping, same flat 2D style as the reference woman: pure black skin with no "
              "shading, a very thin white outline, a black long-sleeve cuff at the wrist. It is HER hand seen exactly from the "
              "side, fingers pointing to the right, with the wrist and a short part of the forearm on the left. "
              "1) hand in typing position hovering over an invisible keyboard, five distinct gently curved fingers, the index "
              "finger pressed down; 2) same hand, the middle finger pressed down, the index raised; 3) same hand open, fingers "
              "relaxed and slightly apart, reaching forward and slightly down; 4) same hand gripping a black smartphone that lies "
              "flat, thumb on top of the phone, fingers wrapped under its edge; 5) same hand holding the same smartphone upright, "
              "its glowing screen facing left, thumb resting on the screen; 6) the same black smartphone alone, lying flat, seen "
              "from the side, screen off. Anatomically correct hands, natural proportions, no text.", [LEA, MAIN], "16:9"),
    "poste_profil": ("Side view (90 degrees) of a scientist's workstation desk inside an astronomical observatory at night: a long "
                     "light-grey desk seen exactly from the side at mid height across the lower part of the image, a flat dark "
                     "keyboard on the desk in the left half, a computer monitor on the right half of the desk seen from the side "
                     "and slightly from the front, its glowing blue screen facing left; empty space on the left of the desk for a "
                     "seated person; NO chair, NO people, NO phone, nothing on the floor on the left. Behind, the dark observatory "
                     "interior with racks, tiny status lights and soft blue screen light, softly blurred (depth of field). Flat 2D "
                     "vector illustration, same drawing style, line quality and palette as the reference image, no text.", [DECOR], "16:9"),
}


def job(n):
    prompt, refs, aspect = JOBS[n]
    return kie.image(prompt, HERE / f"{n}.png", refs=refs, aspect=aspect, resolution="2K")


if __name__ == "__main__":
    with ThreadPoolExecutor(2) as ex:
        for n, r in zip(JOBS, ex.map(job, JOBS)):
            print("ok", n, r)
