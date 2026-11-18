"""Minutage mot par mot des voix (Whisper) aligné sur le texte EXACT du script, avec contrôle.

    python3 -m moteur.mots b01            → b01/mots.json + rapport de contrôle à l'écran

Pour chaque fichier de voix (bXX/voix.json : {nom: texte}) :
1. Whisper (faster-whisper, modèle « small », français) donne des mots horodatés ;
2. le texte du script est aligné sur ces mots (difflib sur les mots normalisés) : on garde toujours les mots du script,
   jamais ceux de Whisper ; un mot du script non reconnu reçoit un temps interpolé entre ses voisins (« ok »: false) ;
3. contrôle : taux de correspondance, mots placés dans un silence (énergie du signal), fin de phrase sans pause,
   nombres et mots interpolés à vérifier à l'oreille.
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

FILM = Path(__file__).resolve().parents[1]
SR = 16000


def load(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def norm(w: str) -> str:
    w = unicodedata.normalize("NFD", w.lower().replace("’", "'"))
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def script_words(text: str) -> list[str]:
    return [w for w in re.findall(r"[\w’'\-,\.…!?;:]+", text) if norm(w)]


def energy(x: np.ndarray, hop=160):
    e = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)])
    return e / (e.max() + 1e-9)


_MODEL = None


def whisper_words(wav: Path):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel  # noqa: PLC0415
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = _MODEL.transcribe(load(wav), language="fr", word_timestamps=True, vad_filter=False, beam_size=5)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def align(text: str, wav: Path):
    """Alignement lettre par lettre (robuste aux élisions « qu'ils », « l'œil » et aux mots coupés par Whisper)."""
    sw = script_words(text)
    ww = whisper_words(wav)
    A, ai = "", []
    for i, w in enumerate(sw):
        n = norm(w); A += n; ai += [i] * len(n)
    Bs, bi = "", []
    for j, (w, _, _) in enumerate(ww):
        n = norm(w); Bs += n; bi += [j] * len(n)
    first, last = [None] * len(sw), [None] * len(sw)
    for blk in difflib.SequenceMatcher(None, A, Bs, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            i, j = ai[blk.a + k], bi[blk.b + k]
            if first[i] is None:
                first[i] = j
            last[i] = j
    x = load(wav); e = energy(x); dur = len(x) / SR
    out = []
    for i, w in enumerate(sw):
        nchar = len(norm(w)); got = sum(1 for k, v in enumerate(ai) if v == i)  # noqa: F841
        if first[i] is not None:
            s0, e0 = ww[first[i]][1], ww[last[i]][2]
            # la fin d'un mot ne déborde pas dans le silence qui suit : on la recale sur l'énergie du signal
            k0, k1 = int(s0 * 100), int(e0 * 100)
            seg = e[k0:k1 + 1]
            loud = np.nonzero(seg > 0.04)[0]
            if loud.size:
                e0 = min(e0, (k0 + loud[-1] + 1) / 100)
            out.append([s0, max(e0, s0 + 0.04), True])
        else:
            out.append(None)
    known = [i for i, v in enumerate(out) if v]
    res = []
    for i, w in enumerate(sw):
        if out[i]:
            res.append({"w": w, "start": round(out[i][0], 3), "end": round(out[i][1], 3), "ok": True})
            continue
        p = max([k for k in known if k < i], default=None); n = min([k for k in known if k > i], default=None)
        t0 = out[p][1] if p is not None else 0.0
        t1 = out[n][0] if n is not None else dur
        lo = p if p is not None else -1; hi = n if n is not None else len(sw)
        f0 = (i - lo) / (hi - lo); f1 = (i - lo + 1) / (hi - lo)
        res.append({"w": w, "start": round(t0 + (t1 - t0) * f0, 3), "end": round(t0 + (t1 - t0) * f1, 3), "ok": False})
    return res, len(known) / max(1, len(sw))


def check(name, words, ratio, wav):
    e = energy(load(wav))
    notes = []
    if ratio < 0.9:
        notes.append(f"correspondance faible ({ratio:.0%}) : texte et voix diffèrent ?")
    for w in words:
        i0, i1 = int(w["start"] * 100), max(int(w["start"] * 100) + 1, int(w["end"] * 100))
        if e[i0:i1].size and e[i0:i1].max() < 0.04:
            notes.append(f"« {w['w']} » tombe dans un silence ({w['start']:.2f} s)")
        if not w["ok"]:
            notes.append(f"« {w['w']} » non reconnu, temps interpolé ({w['start']:.2f} s) : à vérifier")
        if re.search(r"\d", w["w"]):
            notes.append(f"nombre « {w['w']} » à {w['start']:.2f} s : à vérifier à l'oreille")
    for a, b in zip(words, words[1:]):                      # une fin de phrase doit être suivie d'une pause
        if re.search(r"[\.!?…]$", a["w"]) and b["start"] - a["end"] < 0.08:
            notes.append(f"pas de pause après « {a['w']} » ({a['end']:.2f} s) : coupure de Whisper à vérifier")
    print(f"{name} : {len(words)} mots, {ratio:.0%} reconnus" + ("" if notes else ", rien à signaler"))
    for n in notes:
        print("   -", n)
    return notes


def main(bloc: str):
    d = FILM / bloc
    voix = json.loads((d / "voix.json").read_text())
    out, report = {}, {}
    for name, text in voix.items():
        words, ratio = align(text, d / f"{name}.wav")
        out[name] = words
        report[name] = check(name, words, ratio, d / f"{name}.wav")
    (d / "mots.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("écrit :", d / "mots.json")


if __name__ == "__main__":
    main(sys.argv[1])
