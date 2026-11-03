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


def camera_params(scene_no: int, t: float, frame: int, impact_t: float | None, dur: float = 10.0) -> tuple[float, float, float, float]:
    """(échelle, décalage x, décalage y, rotation en degrés), en fraction de la largeur pour x et y."""
    glide = 1.0                                   # glissé d'entrée sur 24 images
    g = smootherstep(t / glide)
    dx0, dy0 = DIRS[scene_no % len(DIRS)]
    s = 1.075 - 0.045 * g                         # 1,075 → 1,03 pendant le glissé
    x = dx0 * 0.018 * (1 - g)
    y = dy0 * 0.012 * (1 - g)
    if t > glide:                                 # poussée lente continue jusqu'à la dernière image :
        rate = min(0.0008, 0.13 / max((dur - glide) * FPS, 1))   # ~0,05-0,08 % par image, total ≤ 13 %
        s += rate * (t - glide) * FPS
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


# =========================================================================== #
# Version 2 : guide de montage (../montage_guide.md) et plan de scènes (edit_plan.py)
# =========================================================================== #
TIERS = {  # secousse, coup de zoom, rotation, gain du son
    "strong": (0.007, 0.03, 1.6, 1.0),
    "medium": (0.004, 0.018, 0.9, 0.65),
    "light": (0.002, 0.008, 0.0, 0.35),
}


def scene_shots(kind: str, spans, scene_no: int, plan) -> list[tuple[float, float, float, float]]:
    """Cadrages successifs de la scène (couverture) : (début, échelle, décalage x, décalage y).

    Large au départ, puis plus serré à chaque nouvelle phrase ; le cadrage le plus serré est réservé aux moments clés.
    """
    fx_, fy_ = (-0.05, -0.035) if kind == "person" else (0.0, -0.01)   # visage de Marc dans le cadre
    shots = [(0.0, 1.0, 0.0, 0.0)]
    key_k = plan.CLOSEUPS.get(scene_no)
    framings = [(1.15, fx_ + (0.025 if scene_no % 2 else -0.025), fy_), (1.27, fx_, fy_ - 0.01)]
    for k, (s0, _) in enumerate(spans[1:], start=1):
        t = s0 + 0.15 - 0.05  # un peu avant la phrase (voix décalée de 0,15 s dans la scène)
        if key_k == k:
            shots.append((t, 1.42, fx_, fy_))
        elif scene_no in plan.KEY_SCENES or kind in plan.NO_COVERAGE:
            continue
        else:
            s, x, y = framings[(len(shots) - 1) % len(framings)]
            shots.append((t, s, x, y))
    if key_k == 0:
        shots[0] = (0.0, 1.42, fx_, fy_)
    return shots


def camera_v2(beat: int, t: float, frame: int, dur: float, shots, impacts, still: bool):
    i = max(j for j, sh in enumerate(shots) if sh[0] <= t)
    t0, s, fx_, fy_ = shots[i]
    x, y, rot = -fx_ * s, -fy_ * s, 0.0
    if i == 0 and not still:                      # glissé d'entrée, direction cohérente par partie
        g = smootherstep(t / 1.0)
        dx0, dy0 = DIRS[beat % len(DIRS)]
        s += 0.045 * (1 - g)
        x += dx0 * 0.018 * (1 - g)
        y += dy0 * 0.012 * (1 - g)
    rate = 0.00015 if still else min(0.0008, 0.13 / max((dur - 1) * FPS, 1))
    s += 0.03 + rate * t * FPS
    for ti, tier in impacts:
        if t < ti:
            continue
        shake, punch, roll, _ = TIERS[tier]
        k = (t - ti) * FPS
        if k < 7:
            amp = shake * (1 - k / 7)
            x += amp * (1 if frame % 2 else -1)
            y += amp * 0.6 * (-1 if frame % 2 else 1)
        s += punch * min(k, 12) / 12
        rot += roll * math.exp(-k / 18) * (1 if beat % 2 else -1)
    return s, x, y, rot


def warm_grade(img: Image.Image) -> Image.Image:
    a = np.asarray(img).astype(np.float32)
    a = a * np.array([1.2, 0.97, 0.72], dtype=np.float32) + np.array([18, 6, 0], dtype=np.float32)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


# ---- sons supplémentaires -------------------------------------------------- #
def reverse_cymbal(d: float = 1.3) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    x = _band(rng.normal(0, 1, n), 2500, 12000) * np.exp(-t / 0.35)
    x = x[::-1] * (t / d)
    return x / (np.abs(x).max() + 1e-9) * 0.5


def ding(f: float = 1318.5) -> np.ndarray:
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t / 0.35)
    return x * 0.3


def glitch_v(seed: int) -> np.ndarray:
    r = np.random.default_rng(seed)
    d = r.uniform(0.3, 0.5)
    n = int(d * SR)
    t = np.arange(n) / SR
    base = r.choice([660, 740, 880, 990])
    out = np.zeros(n)
    k, start = 0, 0.0
    while start < d - 0.08 and k < 4:
        m = (t >= start) & (t < start + r.uniform(0.05, 0.1))
        out[m] += np.sign(np.sin(2 * np.pi * base * r.choice([1, 0.75, 1.25]) * t[m])) * 0.22
        start += r.uniform(0.09, 0.14)
        k += 1
    out += _band(r.normal(0, 1, n), 2000, 7000) * (r.random(n) < 0.02) * 0.35
    return out


def tick_v(seed: int) -> np.ndarray:
    r = np.random.default_rng(seed)
    n = int(0.03 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * r.uniform(1900, 2500) * t) * np.exp(-t / r.uniform(0.004, 0.008)) * 0.3


def ambience(kind: str, d: float, seed: int) -> np.ndarray:
    """Ambiances discrètes par lieu (bruit filtré + bourdonnements)."""
    r = np.random.default_rng(seed)
    n = int(d * SR)
    t = np.arange(n) / SR
    noise = r.normal(0, 1, n)
    if kind == "room":
        x = _band(noise, 80, 900) * 0.6 + 0.08 * np.sin(2 * np.pi * 50 * t)
    elif kind == "street":
        x = _band(noise, 60, 1500) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t + r.uniform(0, 6)))
    elif kind == "store":
        x = _band(noise, 200, 3000) * 0.5 + 0.06 * np.sin(2 * np.pi * 100 * t)
    elif kind == "servers":
        x = _band(noise, 300, 6000) * 0.45 + 0.25 * np.sin(2 * np.pi * 120 * t) + 0.1 * np.sin(2 * np.pi * 240 * t)
    elif kind == "hospital":
        x = 0.25 * np.sin(2 * np.pi * 100 * t) + _band(noise, 3000, 9000) * 0.25 + _band(noise, 80, 600) * 0.3
    elif kind == "radio":
        crackle = (r.random(n) < 0.0015) * r.normal(0, 1, n) * 3
        x = _band(noise, 300, 3500) * 0.35 + _band(crackle, 1000, 8000)
    else:  # space : souffle grave
        x = _band(noise, 30, 220) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * t))
    return x / (np.abs(x).max() + 1e-9)


def drone(mood: str, d: float) -> np.ndarray:
    n = int(d * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    if mood == "dark":
        voices = [(55.0, 0.5), (110.0, 0.3), (116.5, 0.18), (82.4, 0.2)]
        for f, a in voices:
            for det in (-0.8, 0.8):
                out += a * np.sin(2 * np.pi * (f + det) * t)
        out += _band(rng.normal(0, 1, n), 60, 400) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.04 * t))
    elif mood == "bright":
        for f, a in [(220.0, 0.3), (277.2, 0.24), (329.6, 0.22), (493.9, 0.12), (659.3, 0.06)]:
            for det in (-0.4, 0.4):
                out += a * np.sin(2 * np.pi * (f + det) * t) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t))
    else:  # neutre : quintes ouvertes, timbre de cordes
        for f, a in [(110.0, 0.35), (164.8, 0.28), (220.0, 0.2)]:
            for h, ha in [(1, 1.0), (2, 0.25), (3, 0.1)]:
                out += a * ha * np.sin(2 * np.pi * f * h * t + h) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t))
    return out / (np.abs(out).max() + 1e-9)


def _fade_env(n: int, a: int, b: int, fade: int) -> np.ndarray:
    env = np.zeros(n)
    a, b = max(a, 0), min(b, n)
    if b <= a:
        return env
    env[a:b] = 1
    f = min(fade, (b - a) // 2)
    if f > 0:
        env[a:a + f] = np.linspace(0, 1, f)
        env[b - f:b] = np.linspace(1, 0, f)
    return env


def reverb(x: np.ndarray, wet: float = 0.18, decay: float = 0.45) -> np.ndarray:
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t / decay)
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[: len(x)]
    return x * (1 - wet) + y * wet * 3


def build_soundtrack_v2(work: Path, scenes, idx, starts, durs, spans, plan):
    """music.wav, sfx.wav, amb.wav et la liste des moments d'impact (pour la caméra et le contrôle du mixage)."""
    total = starts[-1] + durs[-1]
    n_total = int(total * SR) + SR
    sfx = np.zeros(n_total)
    foley = np.zeros(n_total)    # petits bruitages : seuls eux passent dans la réverbération de pièce
    amb = np.zeros(n_total)
    music_env = {m: np.zeros(n_total) for m in ("neutral", "dark", "bright")}
    gate = np.ones(n_total)
    impacts_by_scene: dict[int, list] = {}
    prev_beat = None
    lead = 0.15
    for n, i in enumerate(idx):
        beat, label, voice, onscreen, kind, p = scenes[i]
        sc, t0, d = i + 1, starts[n], durs[n]
        sp = spans[n]
        # drone par temps ; le drone clair du moment clé démarre 1,5 s avant (pont musical)
        mood = plan.DRONE.get(beat, "neutral")
        a = t0 - (1.5 if mood == "bright" and beat != prev_beat else 0.0)
        music_env[mood] += _fade_env(n_total, int(a * SR), int((t0 + d) * SR), int(3 * SR))
        # ambiance + pont sonore (démarre 1 s avant la coupe)
        amb_kind = plan.ambience_for(kind, p)
        if amb_kind:
            a0 = max(0.0, t0 - 1.0)
            seg = ambience(amb_kind, t0 + d - a0, sc) * _fade_env(int((t0 + d - a0) * SR), 0, int((t0 + d - a0) * SR), int(0.8 * SR))
            _add(amb, seg, a0, 0.5 if amb_kind != "radio" else 0.9)
        if beat != prev_beat:
            _add(sfx, whoosh(), t0 - 0.35, 0.4)
        # impacts dans le blanc après la phrase, aspiration inversée avant les impacts forts
        for (s_no, k, tier) in plan.IMPACTS:
            if s_no == sc and k < len(sp):
                ti = t0 + lead + sp[k][1] + 0.06
                impacts_by_scene.setdefault(sc, []).append((ti - t0, tier))
                tail = {"strong": 1.8, "medium": 0.9, "light": 0.6}[tier]   # la résonance ne déborde pas sur la phrase suivante
                hit = impact()[: int(tail * SR)]
                hit = hit * np.linspace(1, 0, len(hit)) ** 0.5
                _add(sfx, hit, ti, TIERS[tier][3])
                if tier == "strong":
                    rc = reverse_cymbal()
                    _add(sfx, rc, ti - len(rc) / SR, 0.55)
        # coupures de musique : la phrase est dite dans le silence
        for (s_no, k) in plan.STOPDOWNS:
            if s_no == sc and k < len(sp):
                g0, g1 = int((t0 + lead + sp[k][0] - 0.3) * SR), int((t0 + lead + sp[k][1] + 0.05) * SR)
                gate[max(g0, 0):g1] = 0
        status = str(p.get("status", "")).upper()
        if sc not in plan.KEY_SCENES and kind in ("device", "person") and (p.get("bad") or any(w in status for w in ERROR_WORDS)):
            _add(foley, glitch_v(sc), t0 + 0.5, 0.35)
        if kind == "number":
            for k in range(12):
                _add(foley, tick_v(sc * 100 + k), t0 + k * 0.12, 0.4 * (1 - k / 14))
        if kind == "chrono":
            for k in range(int(d * 2.2)):
                _add(foley, tick_v(sc * 100 + k), t0 + k / 2.2, 0.45)
        if sc == 50:
            _add(sfx, riser(), t0 - 3.0, 0.5)
        if beat == HEARTBEAT_BEAT:
            k = 0.0
            while k < d - 0.5:
                _add(sfx, heartbeat(), t0 + k, 0.4)
                k += 60 / 66
        if sc == 56 and len(sp) > 1:          # les terminaux se rallument : sons doux
            for j, f in enumerate((1046.5, 1318.5, 1568.0)):
                _add(foley, ding(f), t0 + lead + sp[1][0] + j * 0.55, 0.5)
        prev_beat = beat
    # musique : trois drones mélangés, coupures adoucies (0,15 s)
    music = np.zeros(n_total)
    for mood, env in music_env.items():
        if env.any():
            music += drone(mood, n_total / SR) * np.clip(env, 0, 1)
    k = int(0.15 * SR)
    gate = np.convolve(gate, np.ones(k) / k, mode="same")
    music *= gate
    music[: 3 * SR] *= np.linspace(0, 1, 3 * SR)
    music[-3 * SR:] *= np.linspace(1, 0, 3 * SR)
    music = music / (np.abs(music).max() + 1e-9) * 0.6
    sfx = sfx + reverb(foley)
    amb = amb / (np.abs(amb).max() + 1e-9) * 0.5
    for name, sig in (("music", music), ("sfx", sfx), ("amb", amb)):
        _write(work / f"{name}.wav", sig)
    return work / "music.wav", work / "sfx.wav", work / "amb.wav", impacts_by_scene


def mix_check(voice: np.ndarray, vsr: int, sfx: np.ndarray, gain_sfx: float, start_lead: float = 0.0) -> list[float]:
    """Instants où un effet arrive à moins de 3 dB de la voix pendant qu'elle parle (fenêtres de 50 ms)."""
    def env(x, sr):
        hop = int(sr * 0.05)
        m = len(x) // hop
        f = x[: m * hop].astype(np.float32).reshape(m, hop)
        return 20 * np.log10(np.sqrt((f ** 2).mean(axis=1)) + 1e-9)
    v = env(voice / 32768.0, vsr)
    s = env(sfx * gain_sfx, SR)
    m = min(len(v), len(s))
    bad = [i * 0.05 for i in range(m) if v[i] > -35 and s[i] > v[i] - 3]
    merged = []
    for t in bad:
        if not merged or t - merged[-1] > 0.5:
            merged.append(t)
    return merged
