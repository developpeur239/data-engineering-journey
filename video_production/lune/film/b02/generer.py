"""Bloc 2 : 1 image (extérieur de Calern la nuit) + la voix (2 passages). Cache : rien n'est regénéré.
    KIE_API_KEY=proxy-injected ELEVENLABS_API_KEY=proxy-injected python3 b02/generer.py"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUNE = HERE.parents[1]
sys.path.insert(0, str(LUNE.parent / "panne_internet"))
import kie  # noqa: E402
from render import tts_elevenlabs  # noqa: E402

PROMPT = ("Night exterior of the Calern astronomical observatory on a high limestone plateau in the south of France: two white "
          "telescope domes on the left half, the nearest one open with its slit facing the upper right, a low technical building, "
          "low Mediterranean scrub and pale rocks in the foreground, a clear deep-blue starry sky, a small normal-size full Moon high "
          "in the upper right, faint distant lights of the coast on the horizon, calm and quiet. No laser beam, no people, no text. "
          "Flat 2D vector illustration, same drawing style, line quality and palette as the reference image.")
if __name__ == "__main__":
    print(kie.image(PROMPT, HERE / "calern_exterieur.png", refs=[LUNE / "film2d/images/decor_calern_nuit.png"], aspect="16:9", resolution="2K"))
    n = sum(tts_elevenlabs(t, HERE / f"{k}.wav", "aQROLel5sQbj1vuIVi6B", "eleven_v4", 0.7, 0.5)
            for k, t in json.loads((HERE / "voix.json").read_text()).items())
    print("caractères facturés :", n)
