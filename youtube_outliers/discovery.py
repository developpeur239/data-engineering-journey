"""Transform du mode découverte : faire émerger les niches à partir des titres.

Au lieu de deviner le mot-clé d'une niche, on regarde ce que les chaînes qui explosent
ont en commun dans LEURS titres :
    1. signature d'une chaîne = mots et paires de mots présents dans au moins 30 % de ses titres
       (c'est son format : « tungsten rod », « what if », « bodycam »…)
    2. les termes trop répandus parmi toutes les chaînes trouvées sont retirés (trop génériques)
    3. concurrence d'une chaîne = 1 + nombre d'autres chaînes trouvées qui partagent un terme
       de sa signature
"""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS = set(
    """
    a an the and or but if of to in on at by for with from into onto over under about after before
    is are was were be been being am do does did done has have had this that these those it its
    i you he she we they me him her us them my your his our their what which who whom whose why how
    when where there here than then so too very just can could will would should may might must
    not no yes all any each every some most more less many much few one two three first last
    new vs via get got make made like out up down off again ever never only also still even
    le la les un une des du de et ou mais en dans sur pour par avec sans ce cette ces qui que quoi
    est sont il elle ils elles nous vous je tu son sa ses leur leurs au aux pas plus
    el los las y o del por con para una que es
    shorts short video videos youtube viral trending fyp foryou subscribe official full part episode ep
    """.split()
)
_WORD_RE = re.compile(r"[a-z0-9à-ÿ]+(?:'[a-z]+)?")


def tokenize(title: str) -> list[str]:
    words = _WORD_RE.findall(title.lower())
    return [w for w in words if w not in STOPWORDS and len(w) >= 3 and not w.isdigit()]


def title_terms(title: str) -> set[str]:
    """Mots + paires de mots consécutifs (après retrait des mots vides)."""
    tokens = tokenize(title)
    return set(tokens) | {f"{a} {b}" for a, b in zip(tokens, tokens[1:])}


def channel_signature(titles: list[str], min_share: float = 0.3, top: int = 5) -> list[str]:
    """Termes qui reviennent dans au moins `min_share` des titres (et au moins 2 titres)."""
    if not titles:
        return []
    counts = Counter(term for title in titles for term in title_terms(title))
    floor = max(2, min_share * len(titles))
    candidates = [t for t, n in counts.items() if n >= floor]
    # les paires d'abord (plus précises), puis par fréquence
    candidates.sort(key=lambda t: (-counts[t], -(" " in t), t))
    kept: list[str] = []
    for term in candidates:
        if " " not in term and any(term in k.split() for k in kept):
            continue  # « tungsten » est déjà couvert par « tungsten rod »
        kept.append(term)
        if len(kept) == top:
            break
    return kept


def drop_generic_terms(
    signatures: dict[str, list[str]], max_share: float = 0.3, min_channels: int = 10
) -> dict[str, list[str]]:
    """Retire les termes présents dans plus de `max_share` des signatures (s'il y a assez de chaînes)."""
    if len(signatures) < min_channels:
        return signatures
    freq = Counter(term for sig in signatures.values() for term in set(sig))
    limit = max_share * len(signatures)
    return {cid: [t for t in sig if freq[t] <= limit] for cid, sig in signatures.items()}


def niche_label(signature: list[str]) -> str:
    return " · ".join(signature[:2]) if signature else "(titres variés)"


def competition_by_terms(signatures: dict[str, list[str]]) -> dict[str, int]:
    """1 + nombre d'autres chaînes partageant au moins un terme de signature.

    Une chaîne sans signature (titres variés, pas de format clair) reçoit 2 : on ne peut
    pas affirmer qu'elle est seule.
    """
    result = {}
    for cid, sig in signatures.items():
        if not sig:
            result[cid] = 2
            continue
        terms = set(sig)
        result[cid] = 1 + sum(1 for other, osig in signatures.items() if other != cid and terms & set(osig))
    return result
