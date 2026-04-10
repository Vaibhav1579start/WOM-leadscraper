CATEGORY_KEYWORDS = {
    "DJ": ["dj","disc jockey","deejay","mixing","edm","club night","dj set"],
    "Singer": ["singer","vocalist","playback","cover song","original song","music artist"],
    "Musician": ["musician","guitarist","pianist","drummer","bassist","tabla","flute","violin"],
    "Magician": ["magician","magic","illusionist","mentalist","card trick","sleight of hand"],
    "Comedian": ["comedian","stand-up","comedy","jokes","open mic","humour"],
    "Dancer": ["dancer","dance","choreographer","choreography","bhangra","kathak","hip hop dance"],
    "Anchor": ["anchor","emcee","mc","host","event anchor","compere","master of ceremonies"],
    "Band": ["band","live band","music band","rock band","jazz band","fusion band"],
    "Photographer": ["photographer","photography","candid","wedding photo","portrait"],
    "Videographer": ["videographer","videography","filmmaker","cinematographer"],
    "Decorator": ["decorator","decoration","event decor","floral design","balloon"],
    "Caterer": ["caterer","catering","food","chef","cuisine","menu"],
}

def detect_category(text: str) -> str:
    text = text.lower()
    scores = {}
    for cat, kws in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in kws if kw in text)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"

def category_score(text: str, category: str) -> int:
    text = text.lower()
    kws = CATEGORY_KEYWORDS.get(category, [])
    return sum(1 for kw in kws if kw in text)
