"""Miniature dramatique : Nano Banana (Kie.ai) à partir de notre rendu 3D, puis compteur incrusté par miniature.cjs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "panne_internet"))
import kie

ICI = Path(__file__).resolve().parent
BASE = ("Dramatic YouTube thumbnail image, stylized 3D CGI render in the same simulation style as the reference image "
        "(clean 3D, saturated colors), 16:9. Scene: an offshore rocket launch platform on the equator at the exact moment "
        "Earth spins so fast that gravity disappears. IMPORTANT: keep the whole upper-left third of the image as plain sky "
        "with no objects, so a text can be placed there. No text, no letters, no watermark. ")
VARIANTES = {
    "ia_1": BASE + ("Apocalyptic stormy sky, dark blue-grey clouds with a burning orange sunset glow on the horizon. "
                    "A gigantic wall of ocean water rising vertically into the sky behind the platform, huge spray. "
                    "Clearly recognizable panicked people with arms and legs flailing, floating up into the air, screaming. "
                    "In the foreground right, a big terrified worker in an orange safety suit and helmet, mouth open, reaching "
                    "out as he is lifted off the deck. Brightly colored shipping containers and barrels tumbling upward. "
                    "Red launch tower on the right. Strong contrast, cinematic lighting, high drama."),
    "ia_2": BASE + ("The ocean itself is lifting off: massive columns and blobs of seawater floating up into a dark red-orange sky. "
                    "The platform deck is cracking and tilting, a rocket on the red launch tower breaking loose. Dozens of "
                    "recognizable people in colorful clothes floating helplessly upward, some holding on to railings with their "
                    "legs in the air. Close-up foreground: a woman in a yellow raincoat floating, looking terrified at the camera. "
                    "Colorful containers flying. Epic, chaotic, very dramatic."),
    "ia_3": BASE + ("Low angle looking up: the sky is filled with floating people, containers, water droplets and fish, all rising "
                    "toward a huge dark cloud vortex. Below, the ocean surface bulges upward into a giant dome of water around "
                    "the platform. A worker in the foreground is desperately gripping the yellow railing with both hands while "
                    "his body floats horizontally, terrified face. Warm orange rim light, deep blue shadows, maximum drama."),
}
print(f"Crédits Kie avant : {kie.credits():.0f}")
for nom, p in VARIANTES.items():
    kie.image(p, ICI / f"{nom}.png", refs=[ICI / "ref_rendu.jpg"])
    print("ok", nom, flush=True)
print(f"Crédits Kie après : {kie.credits():.0f}")
