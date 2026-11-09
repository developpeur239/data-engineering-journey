"""Image fixe déjà générée (aucun coût), animée en code : poussière en suspension et léger scintillement des écrans.
shots.json → "reglages": {"image": "chemin relatif à lune/", "poussiere": true}."""
from pathlib import Path

import numpy as np

from decors.commun import dust, load_rgb

LUNE = Path(__file__).resolve().parents[2]


class Image:
    def __init__(self, bloc):
        self.cache = {}

    def render(self, t, shot, bloc):
        R = shot.get("reglages", {})
        p = R["image"]
        if p not in self.cache:
            self.cache[p] = load_rgb(LUNE / p)
        f = self.cache[p].copy()
        if R.get("poussiere", True):
            h, w = f.shape[:2]
            dust(f, t, (40, 40, w - 40, h - 40), n=70, alpha=0.18)
        return f
