"""Horodatage mot à mot de la voix (faster-whisper en local), recalé sur le texte exact du script.

    python words.py <dossier_tts>      # écrit NN_ed.words.json à côté de chaque NN_ed.wav

Sert à caler les images sur les mots : un écran passe au rouge sur « refuse », un chiffre finit de
compter sur le mot qui le prononce, un texte apparaît sur le mot qu'il reprend.
"""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

from scenes import SCENES


def norm(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def script_words(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ'’-]+", text)


def align(script: list[str], heard: list[tuple[str, float, float]]) -> list[dict]:
    """Associe chaque mot du script à un temps, en interpolant les mots non reconnus."""
    a, b = [norm(w) for w in script], [norm(w) for w, _, _ in heard]
    out = [None] * len(script)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            out[blk.a + k] = (heard[blk.b + k][1], heard[blk.b + k][2])
    known = [i for i, v in enumerate(out) if v]
    for i in range(len(out)):
        if out[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            t0 = out[prev][1] if prev is not None else 0.0
            t1 = out[nxt][0] if nxt is not None else (t0 + 0.4)
            n_gap = (nxt if nxt is not None else len(out)) - (prev if prev is not None else -1) - 1
            j = i - (prev if prev is not None else -1) - 1
            out[i] = (t0 + (t1 - t0) * j / max(n_gap, 1), t0 + (t1 - t0) * (j + 1) / max(n_gap, 1))
    return [{"w": w, "a": round(s, 3), "b": round(e, 3)} for w, (s, e) in zip(script, out)]


def main(tts_dir: Path):
    from faster_whisper import WhisperModel  # noqa: PLC0415
    model = WhisperModel("small", device="cpu", compute_type="int8")
    for i, sc in enumerate(SCENES):
        wav = tts_dir / f"{i:02d}_ed.wav"
        out = tts_dir / f"{i:02d}_ed.words.json"
        if not wav.exists() or out.exists():
            continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        audio = np.frombuffer(raw, dtype=np.float32)
        segs, _ = model.transcribe(audio, language="fr", word_timestamps=True, initial_prompt=sc[2], beam_size=5)
        heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
        words = align(script_words(sc[2]), heard)
        out.write_text(json.dumps(words, ensure_ascii=False))
        print(f"  scène {i + 1} : {len(words)} mots ({sum(1 for _ in heard)} reconnus)", flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
