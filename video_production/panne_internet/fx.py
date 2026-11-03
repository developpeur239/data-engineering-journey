"""Caméra et bande-son de la vidéo « La panne mondiale d'Internet ».

Règles de caméra inspirées des mesures publiées dans le dépôt MIT mromidev/claude-animated-shorts
(SKILL.md, « Camera ») : entrée en glissé lissé (smootherstep), poussée lente et continue pendant
les plans fixes (aucun plan figé), secousse qui change de sens à chaque image et s'éteint en 7 images
sur les impacts, légère rotation sur les moments forts. Le code ci-dessous est écrit pour ce projet.

Bande-son entièrement synthétisée (aucun son sous droits) : souffles de transition, impacts graves,
bips d'erreur numérique, tic-tac des chiffres, montée avant le retournement, battement de cœur pendant
l'escalade, nappe musicale dont l'intensité suit les temps du script. La musique baisse sous la voix
(compression déclenchée par la voix, dans ffmpeg).
"""

from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np
from PIL import Image

FPS = 24
SR = 48000

# --------------------------------------------------------------------------- #
# Repères par scène (numéros 1 à 64). Le mot-clé place l'impact sur le mot prononcé.
# --------------------------------------------------------------------------- #
IMPACTS = {          # scène : mot-clé du texte de voix
    16: "Soixante-dix-huit",
    17: "Minute zéro",
    25: "plus rien",
    50: "change tout",
    53: "Soixante-dix-huit",
    57: "la vérité",
}
RISER_BEFORE = 50     # montée de tension pendant les 3 dernières secondes avant cette scène
HEARTBEAT_BEAT = 6    # battement de cœur pendant le temps 6 (escalade)
BEAT_INTENSITY = {1: 0.55, 2: 0.4, 3: 0.5, 4: 0.55, 5: 0.75, 6: 0.9, 7: 0.6, 8: 0.4, 9: 0.55}
ERROR_WORDS = ("REFUS", "ERREUR", "IMPOSSIBLE", "INDISPONIBLE", "AUCUN", "OCCUPÉ", "HORS SERVICE", "PIÈCES")


def keyword_time(text: str, keyword: str, voice_dur: float, lead: float = 0.15) -> float:
    """Instant approximatif d'un mot dans la phrase (débit de la voix supposé régulier)."""
    i = text.find(keyword)
    if i < 0:
        return lead
    return lead + voice_dur * (i / max(len(text), 1))


# --------------------------------------------------------------------------- #
# Caméra
# --------------------------------------------------------------------------- #
def smootherstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * x * (x * (x * 6 - 15) + 10)


DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]


def camera_params(scene_no: int, t: float, frame: int, impact_t: float | None) -> tuple[float, float, float, float]:
    """(échelle, décalage x, décalage y, rotation en degrés), en fraction de la largeur pour x et y."""
    glide = 1.0                                   # glissé d'entrée sur 24 images
    g = smootherstep(t / glide)
    dx0, dy0 = DIRS[scene_no % len(DIRS)]
    s = 1.075 - 0.045 * g                         # 1,075 → 1,03 pendant le glissé
    x = dx0 * 0.018 * (1 - g)
    y = dy0 * 0.012 * (1 - g)
    if t > glide:                                 # poussée lente : environ 0,06 % par image
        s += min(0.12, 0.0006 * (t - glide) * FPS)
    rot = 0.0
    if impact_t is not None and t >= impact_t:
        k = (t - impact_t) * FPS                  # images écoulées depuis l'impact
        if k < 7:                                 # secousse : change de sens à chaque image, s'éteint en 7 images
            amp = 0.006 * (1 - k / 7)
            x += amp * (1 if frame % 2 else -1)
            y += amp * 0.6 * (-1 if frame % 2 else 1)
        if k < 14:                                # poussée « coup de poing » sur le mot-clé
            s += 0.0025 * min(k, 14)
        else:
            s += 0.035
        rot = 1.6 * math.exp(-max(k, 0) / 18) * (1 if scene_no % 2 else -1)
    return s, x, y, rot


def apply_camera(img: Image.Image, s: float, x: float, y: float, rot: float) -> Image.Image:
    w, h = img.size
    cx, cy = w / 2, h / 2
    dx, dy = x * w, y * w
    a = math.radians(rot)
    c, si = math.cos(a), math.sin(a)
    # application inverse : pixel de sortie -> pixel source
    coeffs = (
        c / s, si / s, cx - (c * (cx + dx) + si * (cy + dy)) / s,
        -si / s, c / s, cy - (-si * (cx + dx) + c * (cy + dy)) / s,
    )
    return img.transform((w, h), Image.AFFINE, coeffs, resample=Image.BILINEAR)


# --------------------------------------------------------------------------- #
# Sons synthétisés
# --------------------------------------------------------------------------- #
rng = np.random.default_rng(11)


def _env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))


def _band(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    """Filtre passe-bande par FFT."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def whoosh(d: float = 0.7) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    for i, (lo, hi) in enumerate([(200, 800), (600, 2000), (1500, 4500)]):
        seg = _band(noise, lo, hi)
        out += seg * np.sin(np.pi * np.clip(t / d - i * 0.12, 0, 1)) ** 2
    return out / (np.abs(out).max() + 1e-9) * 0.5


def impact(d: float = 1.8) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 62 * np.exp(-t * 1.8) + 30
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    crack = _band(rng.normal(0, 1, n), 80, 2500) * np.exp(-t / 0.07)
    out = boom * 0.9 + crack * 0.35
    return out / (np.abs(out).max() + 1e-9) * 0.9


def glitch(d: float = 0.45) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for start, f in ((0.0, 880), (0.12, 660), (0.24, 880)):
        m = (t >= start) & (t < start + 0.09)
        out[m] += np.sign(np.sin(2 * np.pi * f * t[m])) * 0.25
    out += _band(rng.normal(0, 1, n), 2000, 7000) * (rng.random(n) < 0.02) * 0.4
    return out


def tick() -> np.ndarray:
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * 2200 * t) * np.exp(-t / 0.006) * 0.35


def riser(d: float = 3.0) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    f = 180 + 700 * (t / d) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR)
    noise = _band(rng.normal(0, 1, n), 1000, 8000)
    out = (tone * 0.4 + noise / (np.abs(noise).max() + 1e-9) * 0.4) * (t / d) ** 2
    return out


def heartbeat() -> np.ndarray:
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    beat = np.zeros(n)
    for start, a in ((0.0, 1.0), (0.24, 0.7)):
        tt = np.clip(t - start, 0, None)
        beat += a * np.sin(2 * np.pi * 48 * tt) * np.exp(-tt / 0.09) * (t >= start)
    return beat * 0.8


def _add(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    j = min(len(buf), i + len(sig))
    buf[max(i, 0):j] += sig[max(0, -i): j - i] * gain


def music_bed(total: float, beat_spans: list[tuple[int, float, float]]) -> np.ndarray:
    """Nappe en la mineur (la, fa, do, sol), intensité par temps du script, fondu entre temps."""
    n = int(total * SR)
    t = np.arange(n) / SR
    chords = [(110.0, 130.8, 164.8), (87.3, 110.0, 130.8), (65.4, 98.0, 130.8), (98.0, 123.5, 146.8)]
    out = np.zeros(n)
    chord_len = 8.0
    for ci in range(int(total // chord_len) + 1):
        a, b = ci * chord_len, (ci + 1) * chord_len + 1.5
        m = (t >= a) & (t < b)
        tt = t[m] - a
        fade = np.minimum(1, tt / 1.5) * np.minimum(1, (b - t[m]) / 1.5)
        for k, f in enumerate(chords[ci % 4]):
            for det in (-0.6, 0.6):
                out[m] += np.sin(2 * np.pi * (f + det) * tt + k) * fade * (0.22 if k == 0 else 0.14)
    inten = np.zeros(n)
    for beat, a, b in beat_spans:
        inten[int(a * SR):int(b * SR)] = BEAT_INTENSITY.get(beat, 0.5)
    k = int(2 * SR)                                # lissage des changements d'intensité sur 2 s
    inten = np.convolve(inten, np.ones(k) / k, mode="same")
    out *= inten
    fade = int(3 * SR)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out / (np.abs(out).max() + 1e-9) * 0.6


def build_soundtrack(work: Path, scenes, starts: list[float], durs: list[float], voice_durs: list[float], idx: list[int]):
    """Écrit music.wav et sfx.wav (48 kHz) calés sur les scènes rendues."""
    total = starts[-1] + durs[-1]
    sfx = np.zeros(int(total * SR) + SR)
    beat_spans = []
    prev_beat, prev_kind = None, None
    for n, i in enumerate(idx):
        beat, label, voice, onscreen, kind, p = scenes[i]
        t0, d = starts[n], durs[n]
        beat_spans.append((beat, t0, t0 + d))
        scene_no = i + 1
        if beat != prev_beat or (kind in ("map", "globe") and kind != prev_kind):
            _add(sfx, whoosh(), t0 - 0.35, 0.55)
        if scene_no in IMPACTS:
            _add(sfx, impact(), t0 + keyword_time(voice, IMPACTS[scene_no], voice_durs[n]), 1.0)
        status = str(p.get("status", "")).upper()
        if kind in ("device", "person") and (p.get("bad") or any(w in status for w in ERROR_WORDS)):
            _add(sfx, glitch(), t0 + 0.5, 0.45)
        if kind == "number":
            for k in range(14):
                _add(sfx, tick(), t0 + k * 0.11, 0.5 * (1 - k / 16))
        if kind == "chrono":
            for k in range(int(d)):
                _add(sfx, tick(), t0 + k * (1 / 2.2), 0.6)
        if scene_no == RISER_BEFORE:
            _add(sfx, riser(), t0 - 3.0, 0.6)
        if beat == HEARTBEAT_BEAT:
            k = 0.0
            while k < d:
                _add(sfx, heartbeat(), t0 + k, 0.55)
                k += 60 / 66
        prev_beat, prev_kind = beat, kind
    music = music_bed(total, beat_spans)
    _write(work / "sfx.wav", sfx)
    _write(work / "music.wav", music)
    return work / "music.wav", work / "sfx.wav"


def _write(path: Path, sig: np.ndarray):
    sig = np.clip(sig, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())
