"""Shorts verticaux (1080×1920) découpés dans les blocs rendus, sans rien régénérer.

  python3 shorts/shorts.py [nom]     → shorts/<nom>.mp4

Chaque Short : le plan 16:9 agrandi au centre sur un fond flouté du même plan, une accroche en haut,
les sous-titres mot à mot (Whisper, mots.json) sous l'image, « Simulation hypothétique » et un renvoi au film.
Police : Anton (SIL Open Font License), shorts/polices/Anton.ttf.
"""
import json
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
FILM = ICI.parent
sys.path.insert(0, str(FILM))
from moteur.core import Bloc  # noqa: E402

SHORTS = {
    "s1_006_seconde": dict(bloc="b10", debut=27.6, fin=55.8, voix=["v3", "v4"],
                           accroche=("0,06 SECONDE", "La Lune n'est plus qu'à 9 000 km")),
    "s2_la_lune_se_brise": dict(bloc="b11", debut=0.0, fin=46.6, voix=["v1", "v2"],
                                accroche=("LA LUNE SE BRISE", "Et si elle tombait sur la Terre ?")),
    "s3_impact": dict(bloc="b12", debut=2.0, fin=48.6, voix=["v1", "v2"],
                      accroche=("L'IMPACT", "10 km par seconde")),
}
H_IMG = 760                                   # hauteur du plan 16:9 dans le cadre vertical (rogné à 1080 de large)
Y_IMG = 560


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


PETITS = {"la", "le", "les", "de", "des", "du", "à", "au", "aux", "un", "une", "et", "en", "sur", "plus", "qui",
          "que", "se", "ne", "n’a", "d’une", "d’un", "l’", "d’", "son", "sa", "ses", "leurs", "leur", "est", "sont"}


def morceaux(mots, n=3):
    """Groupes de 1 à n mots (n+2 au plus), coupés après la ponctuation, jamais sur un petit mot."""
    g = []
    for w in mots:
        g.append(w)
        fin = w["w"].rstrip("»\"").endswith((".", ",", "?", "!", ":", ";"))
        petit = w["w"].lower() in PETITS or w["w"].endswith("’")
        if fin or (len(g) >= n and not petit) or len(g) > n + 1:
            yield g; g = []
    if g:
        yield g


def ass(nom, S):
    B = Bloc(S["bloc"])
    d, f = S["debut"], S["fin"]
    dur = f - d
    a1, a2 = S["accroche"]
    lignes = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        "Style: Accroche,Anton,132,&H001E96FF,&H00FFFFFF,&H00100808,&H80000000,0,0,0,0,100,100,1,0,1,6,4,8,40,40,0,1",
        "Style: Sous,Anton,58,&H00FFFFFF,&H00FFFFFF,&H00100808,&H80000000,0,0,0,0,100,100,0,0,1,4,3,8,40,40,0,1",
        "Style: Mot,Anton,92,&H00FFFFFF,&H00FFFFFF,&H00100808,&H80000000,0,0,0,0,100,100,1,0,1,6,4,8,60,60,0,1",
        "Style: Petit,Anton,40,&H00D8D0C8,&H00FFFFFF,&H00100808,&H80000000,0,0,0,0,100,100,2,0,1,3,2,8,40,40,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 1,{ts(0)},{ts(dur)},Petit,,0,0,0,,{{\\pos(540,90)}}SIMULATION HYPOTHÉTIQUE",
        f"Dialogue: 1,{ts(0)},{ts(dur)},Accroche,,0,0,0,,{{\\pos(540,200)\\fad(200,0)}}{a1}",
        f"Dialogue: 1,{ts(0)},{ts(dur)},Sous,,0,0,0,,{{\\pos(540,375)\\fad(400,0)}}{a2}",
        f"Dialogue: 1,{ts(0)},{ts(dur - 4)},Petit,,0,0,0,,{{\\pos(540,1700)}}LE FILM COMPLET SUR LA CHAÎNE",
        f"Dialogue: 2,{ts(dur - 4)},{ts(dur)},Mot,,0,0,0,,{{\\pos(540,1650)\\fad(250,0)\\c&H001E96FF&}}LE FILM COMPLET\\NSUR LA CHAÎNE",
    ]
    mj = json.load(open(FILM / S["bloc"] / "mots.json"))
    for v in S["voix"]:
        t0 = B.t(v)
        mots = [w for w in mj[v] if d <= t0 + w["start"] < f]
        gs = list(morceaux(mots))
        for i, g in enumerate(gs):
            a = t0 + g[0]["start"] - d
            b = t0 + (gs[i + 1][0]["start"] if i + 1 < len(gs) else g[-1]["end"] + 0.3) - d
            b = min(b, t0 + g[-1]["end"] - d + 0.6)
            txt = " ".join(w["w"] for w in g).upper()
            lignes.append(f"Dialogue: 0,{ts(a)},{ts(b)},Mot,,0,0,0,,{{\\pos(540,1395)}}{txt}")
    p = ICI / f"{nom}.ass"
    p.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return p


def rendre(nom):
    S = SHORTS[nom]
    sub = ass(nom, S)
    src = FILM / S["bloc"] / f"bloc{S['bloc'][1:]}.mp4"
    dur = S["fin"] - S["debut"]
    w_img = round(H_IMG * 16 / 9 / 2) * 2
    fc = (f"[0:v]split[a][b];"
          f"[a]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18:saturation=0.8[fond];"
          f"[b]crop=1760:990:80:90,scale={w_img}:{H_IMG},crop=1080:{H_IMG}[img];"          # ôte le bandeau du film
          f"[fond][img]overlay=0:{Y_IMG},ass={sub}:fontsdir={ICI / 'polices'},"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={dur - 0.4:.2f}:d=0.4[v];"
          f"[0:a]afade=t=in:st=0:d=0.15,afade=t=out:st={dur - 0.5:.2f}:d=0.5[s]")
    out = ICI / f"{nom}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(S["debut"]), "-t", f"{dur:.2f}", "-i", str(src),
                    "-filter_complex", fc, "-map", "[v]", "-map", "[s]", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(out)], check=True)
    print("ok", out, f"{dur:.1f} s")


if __name__ == "__main__":
    for n in (sys.argv[1:] or SHORTS):
        rendre(n)
