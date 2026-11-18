import re, sys
"""Texte de la voix V13 : python3 build_v13.py Le_Dernier_Echo_Dossier_Preproduction_V12.docx texte_voix_V13.md"""
import zipfile
def lines_of(path):
    if path.endswith(".docx"):  # texte des paragraphes du dossier V12
        x = zipfile.ZipFile(path).read("word/document.xml").decode()
        paras = [re.sub("<[^>]+>", "", q) for q in re.findall(r"<w:p[ >].*?</w:p>", x)]
        return [q for q in paras if q.strip()]
    return open(path).read().split("\n")
L = lines_of(sys.argv[1])
CUTS = ["Sur les trottoirs, des centaines de personnes regardent vers le haut.","Personne ne parle.","Certains filment.",
"Il tient encore son seau en plastique.","Il regarde l’eau.","Sa mère ne répond pas immédiatement.","Parce que c’est justement ce qui rend la situation si difficile à comprendre.",
"Il regarde par la vitre.","Il prend une photographie avec le téléphone de sa mère.","Puis il ouvre celle qu’il avait prise la veille.","Il rapproche les deux images.","Sa mère regarde le ciel.",
"La Lune occupe désormais une place inhabituelle dans le ciel.","On distingue ses reliefs avec une netteté troublante.",
"Léa regarde l’écran où s’affichent les dernières mesures.","Son collègue est déjà près de la porte.","Elle ne répond pas.","Sur son téléphone, un message de sa sœur apparaît : « On est sur la route. Tu nous rejoins ? »","Léa commence à écrire une réponse.","Puis elle efface.",
"Au loin, une sirène retentit.","Puis une autre.","Les conducteurs sortent de leurs véhicules.","Quelqu’un pointe l’horizon.","La mère prend la main de son fils.","Ils abandonnent la voiture.","Et commencent à courir.",
"Elle regarde son téléphone.","Un dernier message de sa sœur : « On est arrêtés. Je ne sais pas où aller. »","Léa ferme les yeux une seconde.","Sous le message, un mot apparaît. « Écouté. »","Léa fixe l’écran.","Puis elle le pose.",
"La lumière part.","Elle atteint la Lune.","Et revient.","Sur l’écran, un nombre apparaît.",
"Puis elle se lève.","Dehors, la Lune occupe une portion immense du ciel.","Léa ne bouge plus.",
"Derrière eux, la route a disparu sous l’eau.","Devant eux, la Lune semble se déchirer.","Elle s’agenouille devant lui.","Le prend dans ses bras.","Et lui répond doucement :","Au-dessus d’eux, les fragments continuent de tomber.","Son contour est déchiré.","Elle est immense.",
"Depuis l’espace, on voit le nuage de débris s’étendre autour du point d’impact.","La surface que nous connaissons disparaît progressivement derrière une immense enveloppe de matière brûlante."]
RAC = [("D’autres restent immobiles","Certains restent immobiles"),("Elle connaît la réponse.","Sa mère connaît la réponse."),
("Et sa vitesse de rapprochement augmente.","Et la vitesse de rapprochement de la Lune augmente."),
("Puis elle enregistre un message vocal.","Elle enregistre un message vocal."),("Et retourne vers le laser.","Elle retourne vers le laser."),
("Les zones sombres qui traversent sa surface sont désormais visibles.","Les immenses fractures sont désormais visibles à l’œil nu."),
("En 1994, les astronomes ont vu une comète déchirée par Jupiter s’écraser sur la planète.","En 1994, les fragments d’une comète déchirée par Jupiter se sont écrasés sur la planète."),
("il faut revenir cinq jours en arrière. À un moment où personne, sur Terre, ne se doutait de rien.","il faut revenir quatre jours en arrière. À un moment où personne, sur Terre, ne se doutait encore de rien."),
("C’est tout ce qu’il reste avant que la Lune percute la Terre.","C’est la durée totale de sa chute, jusqu’à l’impact.")]
W = lambda s: len(re.findall(r"[\wÀ-ÿ’'-]+", re.sub(r'\b(NARR|GARÇON|MÈRE|LÉA|COLLÈGUE) :', '', re.sub(r'\[[^\]]*\]', '', s))))
used_c, used_r = set(), set()
out, tot0, tot1, cur = [], 0, 0, None
for l in L:
    h = re.match(r'(\d\d:\d\d–\d\d:\d\d) \| (.*)', l)
    if h: out.append(f"\n## {h[1]} · {h[2].capitalize()}\n"); continue
    m = re.match(r'(\d\d):(\d\d)–(\d\d):(\d\d) • (.*)', l)
    if m: cur = (l[:11], (int(m[3])*60+int(m[4]))-(int(m[1])*60+int(m[2]))); continue
    if cur and l.startswith('VOIX / TEXTE : '):
        t0 = l[15:]; t = t0
        for c in CUTS:
            if c in t: t = t.replace(c, ''); used_c.add(c)
        for a, b in RAC:
            if a in t: t = t.replace(a, '⟦' + b + '⟧'); used_r.add(a)
        t = re.sub(r'\s+', ' ', t).strip()
        t = re.sub(r'NARR :\s*(?=(GARÇON|MÈRE|LÉA|COLLÈGUE|NARR) :|$)', '', t).strip()   # narration vidée
        w0, w1 = W(t0), W(t.replace('⟦','').replace('⟧',''))
        tot0 += w0; tot1 += w1
        lines = re.split(r'\s*(?=\b(?:NARR|GARÇON|MÈRE|LÉA|COLLÈGUE) :)', t)
        body = '\n\n'.join(x.strip() for x in lines if x.strip())
        body = re.sub(r'⟦(.*?)⟧', r'**\1**', body)
        need = w1 / 154 * 60
        out.append(f"**{cur[0]}** · {w1} mots (V12 : {w0}) · environ {need:.0f} s pour un créneau de {cur[1]} s\n\n{body or '*(sans voix)*'}\n")
assert len(used_c) == len(CUTS), set(CUTS) - used_c
assert len(used_r) == len(RAC), set(a for a, _ in RAC) - used_r
head = f"""# Le Dernier Écho : texte de la voix, version V13

Texte du dossier V12, avec les coupes et les raccords de `plan_rendu_v2.md` (section 2) appliqués. C'est la version à
relire d'un bloc avant de générer la voix. **Aucune réplique n'est modifiée.** Les mots en gras sont les 9 phrases
réécrites : 5 raccords après coupe, le retour en arrière (00:42 : quatre jours, comme la carte), le compte à rebours (02:00 : 4 j 20 h est la durée totale de la chute), la comète
de 1994 (08:31 : ce sont ses fragments qui frappent Jupiter en 1994) et les fractures (09:48 : on parle des fractures,
pas des zones sombres naturelles de la Lune). Une autre correction est une coupe (« Et lui répond doucement : », à
10:47). Les SMS de la sœur et le statut
« Écouté » ne sont plus lus : ils sont écrits à l'écran.

Total : **{tot1} mots** (V12 : {tot0}), soit environ **{int(tot1/154)} min {tot1/154*60%60:02.0f} s** de voix à 154 mots/min (même compteur que
`compare_voices.py`, sans la ponctuation ni les noms des voix), pour 12:40 avec les silences et le noir final. Les durées par bloc sont des estimations : le montage les recale.
Statut : **validé le 5 novembre 2026** (feu vert pour le prototype puis pour la génération des voix, bloc par bloc).
"""
open(sys.argv[2], 'w').write(head + '\n'.join(out))
print(tot0, tot1)
