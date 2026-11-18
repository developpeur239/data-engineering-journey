"""Assemble le film complet : b01 → b13 (vidéos des blocs reconstruites par le moteur), coupes franches, son de chaque
bloc déjà normalisé (−14 LUFS) ; contrôle final des niveaux.   python3 assembler.py  →  le_dernier_echo.mp4"""
import re
import subprocess
from pathlib import Path

FILM = Path(__file__).resolve().parent
BLOCS = [f"b{k:02d}" for k in range(1, 14)]

if __name__ == "__main__":
    parts = [FILM / b / f"bloc{b[1:]}.mp4" for b in BLOCS]
    missing = [str(p) for p in parts if not p.exists()]
    if missing:
        raise SystemExit("blocs manquants : " + ", ".join(missing))
    lst = FILM / "assemblage.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = FILM / "le_dernier_echo.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", str(out)], check=True)
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1]
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout)
    print(f"{out.name} : {int(d // 60)} min {d % 60:.1f} s · {I} LUFS · crête {TP} dBTP")
