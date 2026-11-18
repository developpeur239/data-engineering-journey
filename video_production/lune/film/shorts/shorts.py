"""Shorts verticaux (1080×1920) découpés dans les blocs rendus, sans rien régénérer.

  python3 shorts/shorts.py [nom]     → shorts/<nom>.mp4

Accroche dès la première image : pas de fondu d'entrée, la voix démarre dans la première demi-seconde
(le premier Short, avec 0,6 s de noir avant la voix, a été balayé par 49 % des spectateurs).
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
    "s1_006_seconde": dict(segments=[("b10", 27.8, 55.8, ["v3", "v4"])],
                           accroche=("0,06 SECONDE", "La Lune n'est plus qu'à 9 000 km")),
    "s2_la_lune_se_brise": dict(segments=[("b11", 2.9, 46.6, ["v1", "v2"])],
                                accroche=("LA LUNE SE BRISE", "Et si elle tombait sur la Terre ?")),
    "s3_impact": dict(segments=[("b12", 2.5, 48.6, ["v1", "v2"])],
                      accroche=("L'IMPACT", "10 km par seconde")),
    # Teaser : ne montre pas la fin, s'arrête sur une question pour envoyer vers le film (lien « vidéo associée »).
    "s4_teaser_elle_tombe": dict(segments=[("b02", 51.48, 55.9, ["v2"]),      # elle ne suit plus son orbite, elle tombe
                                           ("b03", 16.9, 24.4, ["v1"]),      # quatre jours et vingt heures
                                           ("b03", 25.9, 39.7, ["v2"])],     # moins de cinq jours… rien n'a changé
                                 accroche=("LA LUNE TOMBE", "Il reste moins de 5 jours"),
                                 carte_fin=("QUE VA-T-IL\\NSE PASSER ?", "LE FILM COMPLET : TOUCHE LE LIEN EN BAS", 3.5)),
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


def duree(S):
    return sum(f - d for _, d, f, _ in S["segments"]) + (S["carte_fin"][2] if "carte_fin" in S else 0)


def ass(nom, S):
    dur = duree(S)
    fin = S.get("carte_fin")
    t_carte = dur - fin[2] if fin else None
    a1, a2 = S["accroche"]
    haut = t_carte if fin else dur
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
        "Style: Voile,Anton,20,&H40000000,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 1,{ts(0)},{ts(dur)},Petit,,0,0,0,,{{\\pos(540,90)}}SIMULATION HYPOTHÉTIQUE",
        f"Dialogue: 1,{ts(0)},{ts(haut)},Accroche,,0,0,0,,{{\\pos(540,200)}}{a1}",
        f"Dialogue: 1,{ts(0)},{ts(haut)},Sous,,0,0,0,,{{\\pos(540,375)}}{a2}",
    ]
    if fin:
        lignes += [
            f"Dialogue: 3,{ts(t_carte)},{ts(dur)},Voile,,0,0,0,,{{\\pos(0,0)\\fad(300,0)\\p1}}m 0 0 l 1080 0 1080 1920 0 1920{{\\p0}}",
            f"Dialogue: 4,{ts(t_carte)},{ts(dur)},Accroche,,0,0,0,,{{\\pos(540,720)\\fad(300,0)}}{fin[0]}",
            f"Dialogue: 4,{ts(t_carte + 0.6)},{ts(dur)},Sous,,0,0,0,,{{\\pos(540,1080)\\fad(300,0)\\c&HFFFFFF&}}{fin[1]}",
        ]
    else:
        lignes += [
            f"Dialogue: 1,{ts(0)},{ts(dur - 4)},Petit,,0,0,0,,{{\\pos(540,1700)}}LE FILM COMPLET SUR LA CHAÎNE",
            f"Dialogue: 2,{ts(dur - 4)},{ts(dur)},Mot,,0,0,0,,{{\\pos(540,1650)\\fad(250,0)\\c&H001E96FF&}}LE FILM COMPLET\\NSUR LA CHAÎNE",
        ]
    off = 0.0
    for bloc, d, f, voix in S["segments"]:
        B = Bloc(bloc)
        mj = json.load(open(FILM / bloc / "mots.json"))
        for v in voix:
            t0 = B.t(v)
            mots = [w for w in mj[v] if d <= t0 + w["start"] and t0 + w["end"] <= f + 0.15]
            gs = list(morceaux(mots))
            for i, g in enumerate(gs):
                a = t0 + g[0]["start"] - d
                b = t0 + (gs[i + 1][0]["start"] if i + 1 < len(gs) else g[-1]["end"] + 0.3) - d
                b = min(b, t0 + g[-1]["end"] - d + 0.6, f - d)
                txt = " ".join(w["w"] for w in g).upper()
                lignes.append(f"Dialogue: 0,{ts(off + a)},{ts(off + b)},Mot,,0,0,0,,{{\\pos(540,1395)}}{txt}")
        off += f - d
    p = ICI / f"{nom}.ass"
    p.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    return p


def rendre(nom):
    S = SHORTS[nom]
    sub = ass(nom, S)
    dur = duree(S)
    w_img = round(H_IMG * 16 / 9 / 2) * 2
    entrees, fc, n = [], "", len(S["segments"])
    for k, (bloc, d, f, _) in enumerate(S["segments"]):
        entrees += ["-ss", str(d), "-t", f"{f - d:.2f}", "-i", str(FILM / bloc / f"bloc{bloc[1:]}.mp4")]
        fc += (f"[{k}:v]split[a{k}][b{k}];"
               f"[a{k}]scale=-2:1920,crop=1080:1920,gblur=sigma=28,eq=brightness=-0.18:saturation=0.8[f{k}];"
               f"[b{k}]crop=1760:990:80:90,scale={w_img}:{H_IMG},crop=1080:{H_IMG}[i{k}];"   # ôte le bandeau du film
               f"[f{k}][i{k}]overlay=0:{Y_IMG},fps=30,setsar=1[v{k}];"
               f"[{k}:a]afade=t=in:st=0:d=0.03,afade=t=out:st={f - d - 0.04:.2f}:d=0.04[s{k}];")  # coupes sans clic
    fc += "".join(f"[v{k}][s{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=1[vc][sc];"
    if "carte_fin" in S:                                        # dernière image figée sous la question finale
        c = S["carte_fin"][2]
        fc += f"[vc]tpad=stop_mode=clone:stop_duration={c}[vp];[sc]apad=pad_dur={c}[sp];"
    else:
        fc += "[vc]null[vp];[sc]anull[sp];"
    fc += (f"[vp]ass={sub}:fontsdir={ICI / 'polices'},fade=t=out:st={dur - 0.4:.2f}:d=0.4[v];"
           f"[sp]afade=t=out:st={dur - 0.5:.2f}:d=0.5[s]")
    out = ICI / f"{nom}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *entrees, "-filter_complex", fc, "-map", "[v]", "-map", "[s]",
                    "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-r", "30", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print("ok", out, f"{dur:.1f} s")


if __name__ == "__main__":
    for n in (sys.argv[1:] or SHORTS):
        rendre(n)
