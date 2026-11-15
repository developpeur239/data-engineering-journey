"""Détection de signaux d'intention : offres commerciales publiées par un cabinet pour son propre compte.

Sources interrogées (pages publiques de recherche, sans clé d'API) :
  - HelloWork  : recherche par nom de cabinet, détail de l'offre via JSON-LD (datePosted, description)
  - France Travail (candidat.francetravail.fr) : recherche par nom, extrait + « Publié il y a N jours »
Indeed / LinkedIn renvoient 403 (Cloudflare) et ne sont pas interrogés.
"""
import html, json, re, time, unicodedata, urllib.parse, urllib.request
from datetime import date, datetime, timedelta

TODAY = date(2026, 11, 15)
WINDOW = TODAY - timedelta(days=90)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

ROLE = re.compile(r"charg[ée]e?s? d.affaires|business ?develop|business ?manager|consultant[e]?s? (?:en |\(?e\)? )?recrutement|"
                  r"d[ée]veloppeu?r(?:se)? commercial|\bsdr\b|sales development|ing[ée]nieur d.affaires|"
                  r"consultant[e]? recruteu?r|talent (?:acquisition )?consultant|recruteu?r(?:se)? (?:consultant|business)|"
                  r"responsable d[ée]veloppement commercial|chasseu?r de t[êe]te", re.I)
# Indices « pour son propre compte » vs « pour un client »
OWN = re.compile(r"rejoin\w* (?:notre|l.)(?: |\w)*(?:cabinet|[ée]quipe|aventure)|au sein de notre (?:cabinet|[ée]quipe|agence)|"
                 r"renforcer notre [ée]quipe|notre cabinet (?:recrute|recherche|se d[ée]veloppe|est en croissance)|"
                 r"pour notre propre compte|en interne|nous recrutons notre|recrute son|recrute sa|recrute un\(?e?\)? consultant|"
                 r"vous d[ée]velopperez (?:un|votre) portefeuille|d[ée]velopper le portefeuille clients? du cabinet", re.I)
CLIENT = re.compile(r"(?:pour|de) (?:l.un|l.une|un|une) de nos clients|notre client|pour le compte d|nous recherchons pour|"
                    r"client (?:final|industriel)|pour son client|mission pour", re.I)


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "fr-FR,fr;q=0.9"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception:
            time.sleep(1.5 * (i + 1))
    return ""


def text(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def brand_keys(nom):
    """Mots distinctifs du nom (marque entre parenthèses prioritaire) pour matcher l'employeur."""
    stop = {"recrutement", "conseil", "conseils", "consulting", "search", "sarl", "sas", "groupe", "group", "rh",
            "the", "les", "and", "cabinet", "talent", "talents", "selection", "solutions"}
    inner = re.findall(r"\(([^)]+)\)", nom)
    base = inner[-1] if inner else re.sub(r"\(.*?\)", "", nom)
    words = [w for w in re.split(r"[^a-z0-9]+", norm(base)) if len(w) > 2 and w not in stop]
    if not words:  # nom générique (ex. « NC RH ») : on garde tout
        words = [w for w in re.split(r"[^a-z0-9]+", norm(base)) if w]
    return words, base.strip()


def employer_match(employer, nom):
    words, base = brand_keys(nom)
    legal = {"sarl", "sas", "sasu", "eurl", "sa", "france", ""}
    e = set(re.split(r"[^a-z0-9]+", norm(employer))) - legal
    full = set(re.split(r"[^a-z0-9]+", norm(base))) - legal
    if not words or not e:
        return False
    stop = {"recrutement", "conseil", "conseils", "consulting", "search", "groupe", "group", "rh", "cabinet"}
    # 1) l'employeur contient toute la marque ; 2) ou ses mots distinctifs sont tous dans la marque
    return full <= e or ((e - stop) <= full and set(words) <= e)


def classify(title, desc):
    """Renvoie (propre_compte: bool|None, raison)."""
    d = norm(desc)
    own, cli = bool(OWN.search(d)), bool(CLIENT.search(d))
    t = norm(title)
    if re.search(r"consultant[e]?s? (?:en )?recrutement|chasseu?r de tete|recruteu?r", t) and not cli:
        return True, "intitulé métier du cabinet (consultant recrutement)"
    if own and not cli:
        return True, "description : recrutement interne"
    if re.search(r"secteur du recrutement|en cabinet de recrutement|cabinet de recrutement", d) and not cli:
        return True, "description : poste commercial dans le cabinet"
    if cli and not own:
        return False, "description : pour un client"
    if own and cli:
        return None, "ambigu (indices interne + client)"
    return False, "par défaut : offre pour un client (aucun indice de recrutement interne)"


# ---------------------------------------------------------------- HelloWork
def hellowork(nom, max_pages=4):
    words, base = brand_keys(nom)
    q = base if len(base) > 3 else nom
    out, seen = [], set()
    for p in range(1, max_pages + 1):
        h = get("https://www.hellowork.com/fr-fr/emploi/recherche.html?" + urllib.parse.urlencode({"k": q, "p": p}))
        items = re.findall(r'name="offerId" value="(\d+)">\s*<input type="hidden" name="title" value="([^"]+)">\s*'
                           r'<input type="hidden" name="company" value="([^"]+)"', h)
        mine = [(i, html.unescape(t), html.unescape(c)) for i, t, c in items if employer_match(html.unescape(c), nom)]
        for i, t, c in mine:
            if i in seen:
                continue
            seen.add(i)
            out.append({"source": "HelloWork", "id": i, "titre": t, "employeur": c,
                        "url": f"https://www.hellowork.com/fr-fr/emplois/{i}.html"})
        if not mine or len(items) < 20:
            break
        time.sleep(0.5)
    return out


def hellowork_detail(o):
    h = get(o["url"])
    for m in re.finditer(r'<script type="application/ld(?:\+|&#x2B;)json">\s*(.*?)\s*</script>', h, re.S):
        try:
            j = json.loads(m.group(1), strict=False)
        except Exception:
            continue
        if isinstance(j, dict) and j.get("@type") == "JobPosting":
            o["date"] = (j.get("datePosted") or "")[:10]
            o["description"] = text(j.get("description", ""))
            o["lieu"] = json.dumps(j.get("jobLocation", ""), ensure_ascii=False)[:200]
            return o
    m = re.search(r'"datePosted"\s*:\s*"([^"]+)"', h)
    o["date"] = m.group(1)[:10] if m else ""
    o["description"] = ""
    return o


# ---------------------------------------------------------------- France Travail
def francetravail(nom, max_pages=2):
    words, base = brand_keys(nom)
    q = base if len(base) > 3 else nom
    out = []
    for p in range(max_pages):
        h = get("https://candidat.francetravail.fr/offres/recherche?" + urllib.parse.urlencode(
            {"motsCles": q, "offresPartenaires": "true", "range": f"{p*20}-{p*20+19}", "tri": "0"}))
        blocks = re.split(r'(?=<li data-id-offre=)', h)[1:]
        if not blocks:
            break
        for b in blocks:
            mid = re.search(r"/offres/recherche/detail/(\w+)", b)
            tt = re.search(r'<h2[^>]*>(.*?)</h2>', b, re.S)
            sub = re.search(r'<p class="subtext">(.*?)</p>', b, re.S)
            desc = re.search(r'<p class="description">(.*?)</p>', b, re.S)
            dt = re.search(r'<p class="date">(.*?)</p>', b, re.S)
            if not (mid and tt):
                continue
            emp = text(sub.group(1)).split(" - ")[0].strip() if sub else ""
            if not employer_match(emp, nom):
                continue
            dtxt = text(dt.group(1)) if dt else ""
            out.append({"source": "France Travail", "id": mid.group(1), "titre": text(tt.group(1)), "employeur": emp,
                        "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{mid.group(1)}",
                        "date": ft_date(dtxt), "date_txt": dtxt, "description": text(desc.group(1)) if desc else ""})
        if len(blocks) < 20:
            break
    return out


def ft_date(s):
    s = norm(s)
    m = re.search(r"il y a (\d+) jour", s)
    if m:
        return (TODAY - timedelta(days=int(m.group(1)))).isoformat()
    if "aujourd" in s:
        return TODAY.isoformat()
    if "hier" in s:
        return (TODAY - timedelta(days=1)).isoformat()
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    if re.search(r"plus de 30 jours", s):
        return "30j+"
    return ""


def recent(d):
    if not d or d == "30j+":
        return d == "30j+"  # « plus de 30 jours » : potentiellement dans la fenêtre de 90 j, on garde en le signalant
    try:
        return date.fromisoformat(d[:10]) >= WINDOW
    except ValueError:
        return False


def job_signals(nom):
    """Offres commerciales récentes publiées par le cabinet, classées propre compte / client."""
    found = []
    for o in hellowork(nom):
        if ROLE.search(o["titre"]):
            found.append(hellowork_detail(o))
    for o in francetravail(nom):
        if ROLE.search(o["titre"]):
            found.append(o)
    res = []
    for o in found:
        own, why = classify(o["titre"], o.get("description", ""))
        o.update(propre_compte=own, raison=why, recente=recent(o.get("date", "")))
        res.append(o)
    return res


# ---------------------------------------------------------------- Site du cabinet : actualités / carrières
NEWS = re.compile(r"(?:ouverture|ouvre|inaugur\w*|nouvelle? (?:agence|bureau|implantation)|s.install\w* [àa]|"
                  r"nouvel(?:le)? associ[ée]e?|rejoint le cabinet|devient associ[ée]|lancement|lance (?:son|sa|notre)|"
                  r"cr[ée]ation du cabinet|nous recrutons|rejoignez[- ]nous|on recrute)", re.I)
DATE = re.compile(r"\b(?:\d{1,2}[/.]\d{1,2}[/.]20\d{2}|\d{1,2} (?:janv|f[ée]vr|mars|avr|mai|juin|juil|ao[uû]t|sept|oct|nov|d[ée]c)\w* 20\d{2}|20\d{2}-\d{2}-\d{2})\b", re.I)


def site_signals(url, max_pages=10):
    if not url:
        return []
    h = get(url)
    if not h:
        return []
    host = urllib.parse.urlparse(url).netloc
    links = [url]
    for l in re.findall(r'href="([^"#]+)"', h):
        a = urllib.parse.urljoin(url, l)
        if urllib.parse.urlparse(a).netloc == host and re.search(
                r"actu|news|blog|presse|rejoindre|recrut|carriere|join|equipe|team|about|propos|histoire", a, re.I) \
                and a not in links and not re.search(r"\.(pdf|jpe?g|png|webp)$", a, re.I):
            links.append(a)
    hits = []
    for a in links[:max_pages]:
        t = text(get(a) if a != url else h)
        for m in NEWS.finditer(t):
            ctx = t[max(0, m.start() - 160): m.end() + 200]
            dm = DATE.search(ctx)
            hits.append({"page": a, "extrait": ctx.strip(), "date": dm.group(0) if dm else ""})
    # dédoublonnage par extrait
    uniq, seen = [], set()
    for x in hits:
        k = x["extrait"][100:220]
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq[:12]


# ---------------------------------------------------------------- France Travail : balayage par métier
FT_ROLES = ["consultant recrutement", "chargé d'affaires recrutement", "business developer", "business manager",
            "développeur commercial", "sales development representative", "chargé d'affaires", "ingénieur d'affaires"]


def ft_sweep(dept, roles=FT_ROLES, per_query=450):
    """Toutes les offres France Travail des métiers commerciaux d'un département (code '33')."""
    out = {}
    for q in roles:
        for start in range(0, per_query, 150):
            h = get("https://candidat.francetravail.fr/offres/recherche?" + urllib.parse.urlencode(
                {"motsCles": q, "lieux": f"{dept}D", "offresPartenaires": "true", "range": f"{start}-{start+149}", "tri": "1"}))
            blocks = re.split(r'(?=<li data-id-offre=)', h)[1:]
            for b in blocks:
                mid = re.search(r'data-id-offre="(\w+)"', b)
                tt = re.search(r'media-heading-title">(.*?)</span>', b, re.S)
                sub = re.search(r'<p translate="no" class="subtext">(.*?)</p>', b, re.S)
                desc = re.search(r'<p class="description">(.*?)</p>', b, re.S)
                dt = re.search(r'<p class="date">(.*?)</p>', b, re.S)
                if not (mid and tt):
                    continue
                st = text(sub.group(1)) if sub else ""
                parts = [p.strip() for p in st.split(" - ")]
                emp = parts[0] if len(parts) >= 3 else ""   # « EMPLOYEUR - 33 - Ville » (employeur parfois masqué)
                dtxt = text(dt.group(1)) if dt else ""
                out[mid.group(1)] = {"source": "France Travail", "id": mid.group(1), "titre": text(tt.group(1)),
                                     "employeur": emp, "lieu": " - ".join(parts[-2:]), "date": ft_date(dtxt), "date_txt": dtxt,
                                     "description": text(desc.group(1)) if desc else "", "requete": q,
                                     "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{mid.group(1)}"}
            if len(blocks) < 150:
                break
            time.sleep(0.4)
    return list(out.values())


# ---------------------------------------------------------------- Parcours des fondateurs (pages « à propos »)
BIG = re.compile(r"michael page|page personnel|page group|\bhays\b|robert walters|walters people|robert half|adecco|randstad|"
                 r"manpower|expectra|\bspring\b|fed (?:group|finance|legal|supply)|harry hope|morgan philips|badenoch|lhh|"
                 r"kelly services|synergie|hudson|grafton|lincoln|spencer stuart|korn ferry|egon zehnder|russell reynolds|"
                 r"proman|crit\b|samsic|start people|side\b|hunteed|alten|altran|akkodis|assystem|"
                 r"cabinet (?:leader|international)|grand cabinet|grands cabinets", re.I)


def founder_signals(url, max_pages=8):
    if not url:
        return []
    h = get(url)
    if not h:
        return []
    host = urllib.parse.urlparse(url).netloc
    links = [url] + [a for a in dict.fromkeys(urllib.parse.urljoin(url, l) for l in re.findall(r'href="([^"#]+)"', h))
                     if urllib.parse.urlparse(a).netloc == host and re.search(
                         r"propos|about|equipe|team|histoire|qui-sommes|fondat|cabinet|notre-", a, re.I)]
    out, seen = [], set()
    for a in links[:max_pages]:
        t = text(h if a == url else get(a))
        for m in BIG.finditer(t):
            ctx = t[max(0, m.start() - 220): m.end() + 160].strip()
            if ctx[150:260] in seen:
                continue
            seen.add(ctx[150:260])
            out.append({"page": a, "cabinet_cite": m.group(0), "extrait": ctx})
    return out[:6]
