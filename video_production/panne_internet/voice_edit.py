"""Préparation de la voix d'une scène : bornes de chaque phrase et respirations ajoutées.

Les fins de phrases sont retrouvées dans l'audio : on cherche les silences de la voix et on garde, pour chaque
fin de phrase du texte (. ? !), le silence le plus proche de sa position estimée (proportionnelle au nombre de
caractères). Pas d'appel réseau, pas de transcription.
"""

from __future__ import annotations

import json
import re
import wave
from pathlib import Path

import numpy as np


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return x, sr


def write_wav(path: Path, x: np.ndarray, sr: int):
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(x.astype(np.int16).tobytes())


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if s]


def silence_gaps(x: np.ndarray, sr: int, min_gap: float = 0.18, thresh_db: float = -42) -> list[tuple[float, float]]:
    hop = int(sr * 0.01)
    n = len(x) // hop
    frames = x[: n * hop].astype(np.float32).reshape(n, hop) / 32768
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    quiet = db < thresh_db
    gaps, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        if (not q or i == n - 1) and start is not None:
            end = i if not q else i + 1
            if (end - start) * 0.01 >= min_gap:
                gaps.append((start * 0.01, end * 0.01))
            start = None
    return gaps


def sentence_spans(x: np.ndarray, sr: int, text: str) -> list[tuple[float, float]]:
    """(début, fin) de chaque phrase, en secondes dans le fichier audio."""
    sents = sentences(text)
    gaps = silence_gaps(x, sr)
    dur = len(x) / sr
    speech_start = gaps[0][1] if gaps and gaps[0][0] <= 0.02 else 0.0
    speech_end = gaps[-1][0] if gaps and gaps[-1][1] >= dur - 0.02 else dur
    inner = [g for g in gaps if g[0] > speech_start + 0.05 and g[1] < speech_end - 0.05]
    total = sum(len(s) for s in sents) or 1
    bounds, used, acc = [], set(), 0
    for s in sents[:-1]:
        acc += len(s)
        est = speech_start + (speech_end - speech_start) * acc / total
        cands = [(abs((g[0] + g[1]) / 2 - est), j) for j, g in enumerate(inner)
                 if j not in used and (not bounds or g[0] > bounds[-1][1])]
        cands = [c for c in cands if c[0] < 1.2]
        if cands:
            j = min(cands)[1]
            used.add(j)
            bounds.append(inner[j])
        else:
            bounds.append((est, est))
    spans, cur = [], speech_start
    for g0, g1 in bounds:
        spans.append((cur, g0))
        cur = g1
    spans.append((cur, speech_end))
    return spans


def prepare(raw: Path, out: Path, text: str, pauses: dict[int, float]) -> list[tuple[float, float]]:
    """Écrit la voix avec ses respirations ajoutées et renvoie les bornes des phrases (après insertion)."""
    meta = out.with_suffix(".json")
    if out.exists() and meta.exists():
        data = json.loads(meta.read_text())
        if data.get("pauses") == {str(k): v for k, v in pauses.items()}:
            return [tuple(s) for s in data["spans"]]
    x, sr = read_wav(raw)
    spans = sentence_spans(x, sr, text)
    pieces, shifted, offset, last = [], [], 0.0, 0
    for k, (s0, s1) in enumerate(spans):
        shifted.append((s0 + offset, s1 + offset))
        if k in pauses and k < len(spans) - 1:
            cut = int((s1 + 0.04) * sr)
            pieces.append(x[last:cut])
            pieces.append(np.zeros(int(pauses[k] * sr), dtype=np.int16))
            last = cut
            offset += pauses[k]
    pieces.append(x[last:])
    write_wav(out, np.concatenate(pieces), sr)
    meta.write_text(json.dumps({"pauses": {str(k): v for k, v in pauses.items()}, "spans": shifted}))
    return shifted
