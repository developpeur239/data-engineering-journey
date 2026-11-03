"""Analyse le montage, le son et le script de vidéos, pour comprendre ce qui fait leur succès.

Tout tourne en local. On produit un petit dossier par vidéo, à partager ensuite (quelques Mo) :
    report.md        résumé lisible (rythme, voix, accroche)
    summary.json     les mêmes chiffres, pour comparer les vidéos
    transcript.txt   texte horodaté (si faster-whisper est installé)
    cuts.csv         instant de chaque changement de plan
    sheet_intro.jpg  planche : une image toutes les 2 s sur la première minute
    sheet_XX.jpg     planches : une image toutes les 10 s sur toute la vidéo

Prérequis :
    ffmpeg et ffprobe dans le PATH   (Windows : winget install ffmpeg)
    pip install faster-whisper       (optionnel, pour la transcription)

Usage :
    python analyze_video.py "C:\\Users\\User1\\Downloads\\Videos" --out analyse_hindcast
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from statistics import mean, median

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def duration_of(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.stdout.strip())


# --------------------------------------------------------------------------- #
# Montage
# --------------------------------------------------------------------------- #
def detect_cuts(path: Path, threshold: float) -> list[float]:
    """Instants (s) des changements de plan, via le filtre « scene » de ffmpeg."""
    out = run([
        "ffmpeg", "-hide_banner", "-i", str(path), "-an",
        "-vf", f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-",
    ])
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", out.stderr)]


def pacing(cuts: list[float], duration: float) -> dict:
    bounds = [0.0, *cuts, duration]
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    per_minute = [sum(1 for c in cuts if m * 60 <= c < (m + 1) * 60) for m in range(int(duration // 60) + 1)]
    return {
        "cuts": len(cuts),
        "avg_shot_s": round(mean(shots), 2) if shots else duration,
        "median_shot_s": round(median(shots), 2) if shots else duration,
        "cuts_first_60s": per_minute[0] if per_minute else 0,
        "cuts_per_minute": per_minute,
    }


def contact_sheets(path: Path, out: Path, duration: float) -> list[str]:
    """Planches d'images pour voir le style visuel sans regarder toute la vidéo."""
    sheets = []
    intro = out / "sheet_intro.jpg"
    run(["ffmpeg", "-y", "-v", "error", "-t", "60", "-i", str(path),
         "-vf", "fps=1/2,scale=320:-2,tile=6x5", "-frames:v", "1", str(intro)])
    if intro.exists():
        sheets.append(intro.name)
    # une image toutes les 10 s, 30 images (5 min) par planche
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
         "-vf", "fps=1/10,scale=320:-2,tile=6x5", str(out / "sheet_%02d.jpg")])
    sheets += sorted(p.name for p in out.glob("sheet_[0-9]*.jpg"))
    return sheets


# --------------------------------------------------------------------------- #
# Son
# --------------------------------------------------------------------------- #
def loudness(path: Path) -> float | None:
    out = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"])
    found = re.findall(r"I:\s+(-?[0-9.]+) LUFS", out.stderr)
    return float(found[-1]) if found else None


def silences(path: Path, min_s: float = 0.6) -> list[tuple[float, float]]:
    """Pauses de la voix (silences d'au moins `min_s` secondes à -35 dB)."""
    out = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vn",
               "-af", f"silencedetect=noise=-35dB:d={min_s}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out.stderr)]
    return list(zip(starts, ends))


def transcribe(path: Path, model_size: str, language: str | None) -> list[dict] | None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    import numpy as np

    # Décodage audio par ffmpeg (16 kHz mono float32) plutôt que par PyAV : certaines
    # versions de PyAV sont incompatibles avec faster-whisper (open() metadata_errors).
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        capture_output=True,
    ).stdout
    audio = np.frombuffer(raw, dtype=np.float32)
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, _ = model.transcribe(audio, language=language, vad_filter=True)
    return [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segments]


def fmt_time(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


# --------------------------------------------------------------------------- #
# Rapport
# --------------------------------------------------------------------------- #
def analyze(path: Path, out: Path, args: argparse.Namespace) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    print(f"→ {path.name}")
    duration = duration_of(path)

    print("  montage (changements de plan)…")
    cuts = detect_cuts(path, args.scene)
    with open(out / "cuts.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["time_s"], *[[c] for c in cuts]])

    print("  planches d'images…")
    sheets = contact_sheets(path, out, duration)

    print("  son (volume, pauses)…")
    pauses = silences(path)
    summary = {
        "file": path.name,
        "duration_min": round(duration / 60, 2),
        **pacing(cuts, duration),
        "loudness_lufs": loudness(path),
        "pauses": len(pauses),
        "pauses_per_minute": round(len(pauses) / (duration / 60), 2),
        "sheets": sheets,
    }

    segments = None
    if not args.no_transcript:
        print(f"  transcription ({args.model})… (peut prendre plusieurs minutes)")
        segments = transcribe(path, args.model, args.lang)
    if segments:
        words = sum(len(s["text"].split()) for s in segments)
        speech_s = sum(s["end"] - s["start"] for s in segments)
        summary["words"] = words
        summary["words_per_minute"] = round(words / (duration / 60))
        summary["speech_share"] = round(speech_s / duration, 2)
        summary["hook_30s"] = " ".join(s["text"] for s in segments if s["start"] < 30)
        (out / "transcript.txt").write_text(
            "\n".join(f"[{fmt_time(s['start'])}] {s['text']}" for s in segments), encoding="utf-8"
        )
    elif segments is None and not args.no_transcript:
        print("  (faster-whisper non installé : pas de transcription. pip install faster-whisper)")
    elif segments == []:
        summary["words"] = 0  # aucune voix détectée (musique seule ?)
        summary["words_per_minute"] = 0
        summary["speech_share"] = 0.0
        summary["hook_30s"] = "(aucune voix détectée)"

    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render_report(summary), encoding="utf-8")
    return summary


def render_report(s: dict) -> str:
    lines = [
        f"# {s['file']}",
        "",
        f"- Durée : **{s['duration_min']} min**",
        f"- Plans : **{s['cuts']} changements**, plan moyen **{s['avg_shot_s']} s** (médiane {s['median_shot_s']} s)",
        f"- Première minute : **{s['cuts_first_60s']} changements de plan**",
        f"- Changements par minute : {s['cuts_per_minute']}",
        f"- Volume intégré : {s['loudness_lufs']} LUFS (YouTube normalise vers -14)",
        f"- Pauses de plus de 0,6 s : {s['pauses']} ({s['pauses_per_minute']}/min)",
    ]
    if "words" in s:
        lines += [
            f"- Voix : **{s['words_per_minute']} mots/min**, parole sur {int(s['speech_share'] * 100)} % de la durée",
            "",
            "## Accroche (30 premières secondes)",
            "",
            f"> {s['hook_30s']}",
        ]
    lines += ["", "## Planches", "", *[f"![]({name})" for name in s["sheets"]], ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Analyse montage, son et script de vidéos.")
    p.add_argument("source", type=Path, help="une vidéo ou un dossier de vidéos")
    p.add_argument("--out", type=Path, default=Path("analyse_videos"), help="dossier de sortie")
    p.add_argument("--scene", type=float, default=0.3, help="sensibilité des changements de plan (0.2 à 0.5)")
    p.add_argument("--model", default="small", help="modèle faster-whisper : tiny, base, small, medium")
    p.add_argument("--lang", help="langue de la voix, ex. en (sinon détection auto)")
    p.add_argument("--no-transcript", action="store_true", help="ne pas transcrire")
    args = p.parse_args(argv)

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("Erreur : ffmpeg et ffprobe doivent être dans le PATH (Windows : winget install ffmpeg).", file=sys.stderr)
        return 1
    videos = [args.source] if args.source.is_file() else sorted(
        v for v in args.source.iterdir() if v.suffix.lower() in VIDEO_EXT
    )
    if not videos:
        print(f"Aucune vidéo trouvée dans {args.source}", file=sys.stderr)
        return 1

    summaries = [analyze(v, args.out / v.stem[:60], args) for v in videos]
    (args.out / "comparatif.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTerminé : {args.out.resolve()}  ->  envoie ce dossier (sans les vidéos) sur Google Drive.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
