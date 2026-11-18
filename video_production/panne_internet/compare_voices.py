"""Compare des voix (ElevenLabs, MiniMax) sur 3 phrases pièges du script, avant tout rendu complet.

    python compare_voices.py --out <dossier> eleven:JBFqnCBsd6RMkjVDRZzb eleven:onwK4e9ZLuTAKqWW03F9 minimax:French_MaleNarrator

Scènes testées : 1 (ouverture), 4 (« Domain Name System », « Orange, Rogers, Cloudflare et CrowdStrike »),
10 (« l'application X, ChatGPT ou Spotify »). Pour chaque voix : un MP3 (les 3 scènes, 0,5 s entre elles),
débit, durée estimée de la vidéo complète, caractères envoyés, et re-transcription Whisper si disponible.
Une voix dont la clé manque est ignorée (avec un message).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from render import PAD_S, tts_elevenlabs, tts_minimax  # noqa: E402
from scenes import SCENES  # noqa: E402

TEST_SCENES = [0, 3, 9]
TOTAL_WORDS = sum(len(re.findall(r"[\wÀ-ÿ'’-]+", sc[2])) for sc in SCENES)
WATCH = ["Domain Name System", "Rogers", "Cloudflare", "CrowdStrike", "ChatGPT", "Spotify"]


def wav_seconds(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def transcribe(p: Path) -> str | None:
    try:
        from faster_whisper import WhisperModel  # noqa: PLC0415
    except ImportError:
        return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), language="fr")
    return " ".join(s.text.strip() for s in segs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("voices", nargs="+", help="eleven:<voice_id> ou minimax:<voice_id>")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--eleven-model", default="eleven_v4")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in a.voices:
        provider, voice = spec.split(":", 1)
        if provider == "eleven" and not os.environ.get("ELEVENLABS_API_KEY"):
            print(f"{spec} : ELEVENLABS_API_KEY absente, ignorée")
            continue
        if provider == "minimax" and not os.environ.get("MINIMAX_API_KEY"):
            print(f"{spec} : MINIMAX_API_KEY absente, ignorée")
            continue
        tag = f"{provider}_{voice}".replace(" ", "_")
        parts, chars, words = [], 0, 0
        for i in TEST_SCENES:
            text = SCENES[i][2]
            wav = a.out / f"{tag}_{i + 1:02d}.wav"
            if provider == "eleven":
                tts_elevenlabs(text, wav, voice, a.eleven_model)
            else:
                tts_minimax(text, wav, voice, "speech-2.8-hd", 1.0, None)
            chars += len(text)
            words += len(re.findall(r"[\wÀ-ÿ'’-]+", text))
            parts.append(wav)
        secs = sum(wav_seconds(p) for p in parts)
        wpm = words / secs * 60
        est = TOTAL_WORDS / wpm + PAD_S * len(SCENES) / 60
        listfile = a.out / f"{tag}.txt"
        silence = a.out / "silence.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "0.5", str(silence)], check=True)
        listfile.write_text("".join(f"file '{p}'\nfile '{silence}'\n" for p in parts))
        mp3 = a.out / f"{tag}.mp3"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listfile),
                        "-ar", "44100", "-ac", "1", "-b:a", "128k", str(mp3)], check=True)
        heard = transcribe(mp3)
        ok = [w for w in WATCH if heard and w.lower().replace(" ", "") in heard.lower().replace(" ", "")]
        rows.append((spec, round(wpm), round(est, 1), chars, ", ".join(ok) if heard else "n/a", mp3))
    print("\n| Voix | Débit (mots/min) | Durée estimée de la vidéo | Caractères envoyés | Noms anglais reconnus par Whisper | Fichier |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} min | {r[3]} | {r[4]} | {r[5].name} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
