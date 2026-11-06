"""Bloc 1 (00:00–01:00, « Le dernier ciel ») : 4 images (Nano Banana via Kie.ai) + voix du narrateur (ElevenLabs).
    KIE_API_KEY=proxy-injected ELEVENLABS_API_KEY=proxy-injected python3 gen_b01.py   (cache : rien n'est regénéré)"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "b01"
sys.path.insert(0, str(HERE.parents[1] / "panne_internet"))
import kie  # noqa: E402
from render import tts_elevenlabs  # noqa: E402

STYLE_REF = HERE.parent / "film2d/images/decor_calern_nuit.png"
CHAR_REF = HERE.parent / "references_design/personnages/reference_2d.png"
STYLE = ("Flat 2D vector illustration for an animated documentary, same drawing style, line quality and palette as the reference "
         "image, soft gradients, cinematic atmospheric lighting, muted desaturated palette, clean shapes, no text, no letters, no logos")
IMGS = {
    "chambre_nuit": ("A bedroom at night seen from the bed, point of view of someone who just woke up: an unmade bed with a crumpled "
                     "duvet in the foreground, a large window on the far wall with thin half-open curtains, an intense cold white "
                     "moonlight floods the room, sharp window-shaped patches of light on the floor and wall, a bedside table with a "
                     "switched-off lamp and a phone, deep blue shadows. The Moon itself is not visible. No people. " + STYLE, [STYLE_REF]),
    "fenetre_rue": ("View from a bedroom window on the second floor at night: the dark window frame and curtains in the foreground frame "
                    "the view; outside, a small French town street with houses and rooftops; a gigantic Moon fills a third of the sky "
                    "above the rooftops, its craters clearly visible, its brilliant white light makes the streets glow like an unreal "
                    "landscape, a few lit windows. No people. " + STYLE, [STYLE_REF]),
    "rue_lune": ("A quiet street of a small French town at night, wide shot at street level, a gigantic Moon dominating the sky above "
                 "the roofs with its craters clearly visible, brilliant white moonlight casting long sharp shadows on the asphalt, parked "
                 "cars and street lamps on the sides, open empty space in the middle of the street. No people. " + STYLE, [STYLE_REF]),
    "figurants_dos": ("Five people seen from behind, standing still side by side and looking up at the sky, frozen: a man in a long coat, "
                      "a woman holding a bag, an old man with a cap, a teenager with a hoodie, a small girl holding her father's hand "
                      "(counts as two). Same flat 2D style as the reference characters: pure black bodies and heads without shading, "
                      "simple rounded limbs, only small touches of muted colour on clothes or hair, thin white outline. Pure flat magenta "
                      "background (#FF00FF) filling the whole image, no floor, no shadow, all characters fully visible.", [CHAR_REF]),
    "foule_dos": ("Eight different people seen from behind, standing still in a loose row and looking up at the sky, frozen, "
                  "all clearly different: a man in pyjamas and slippers, a woman in a bathrobe, a father carrying a small child on "
                  "his shoulders (counts as two), an old woman with a shawl, a young man holding his phone up to film the sky, a "
                  "couple holding each other, a teenage girl with a backpack. Same flat 2D style as the reference characters: pure "
                  "black bodies and heads without shading, simple rounded limbs, only small touches of muted colour on clothes or "
                  "hair, thin white outline, same proportions as the reference. Pure flat magenta background (#FF00FF) filling the "
                  "whole image, no floor, no shadow, all characters fully visible and not overlapping.", [CHAR_REF, HERE / "b01/figurants_dos.png"]),
}
NIC = "aQROLel5sQbj1vuIVi6B"
VOIX = {
    "v1": "Imaginez que vous vous réveilliez au milieu de la nuit. Votre chambre est éclairée. Pas par le soleil. Par la Lune.",
    "v2": "Vous vous approchez de la fenêtre. Et ce que vous découvrez dehors semble impossible. La Lune est devenue gigantesque. "
          "Elle domine le ciel. Ses cratères sont visibles à l’œil nu, et sa lumière blanche transforme les rues en paysages presque irréels.",
    "v3": "Certains restent immobiles, comme s’ils attendaient que quelqu’un leur explique ce qu’ils voient. Mais une chose est déjà "
          "certaine. Dans quelques heures, la Lune va percuter la Terre.",
    "v4": "Pour comprendre comment nous en sommes arrivés là, il faut revenir quatre jours en arrière. À un moment où personne, sur "
          "Terre, ne se doutait encore de rien.",
}


def img(name):
    prompt, refs = IMGS[name]
    aspect = "16:9"
    return kie.image(prompt, OUT / f"{name}.png", refs=refs, aspect=aspect, resolution="2K")


if __name__ == "__main__":
    only = sys.argv[1:]
    if only:
        for n in only:
            print("image", n, img(n))
        sys.exit()
    with ThreadPoolExecutor(5) as ex:
        futs = {n: ex.submit(img, n) for n in IMGS}
        chars = sum(tts_elevenlabs(t, OUT / f"{k}.wav", NIC, "eleven_v4", 0.7, 0.5) for k, t in VOIX.items())
        for n, f in futs.items():
            print("image", n, f.result(), flush=True)
    (OUT / "voix.json").write_text(json.dumps(VOIX, ensure_ascii=False, indent=1))
    print("caractères facturés :", chars)
