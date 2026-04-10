import re
from modules.search import search_instagram_artists

ROLE_KEYWORDS = {
    "DJ": ["dj","disc jockey","deejay"],
    "Singer": ["singer","vocalist","singer-songwriter"],
    "Magician": ["magician","magic","illusionist","mentalist"],
    "Comedian": ["comedian","comedy","stand-up","standup"],
    "Dancer": ["dancer","dance","choreographer"],
    "Musician": ["musician","guitarist","pianist","drummer","band"],
    "Anchor": ["anchor","emcee","mc","host","compere"],
    "Photographer": ["photographer","photography"],
    "Videographer": ["videographer","filmmaker"],
    "Decorator": ["decorator","decoration"],
}

CITY_RE = re.compile(
    r'\b(Mumbai|Delhi|Bangalore|Bengaluru|Hyderabad|Chennai|Kolkata|Pune|'
    r'Ahmedabad|Jaipur|Lucknow|Nagpur|Indore|Bhopal|Surat|Vadodara|'
    r'Chandigarh|Coimbatore|Kochi|Patna|Agra|Varanasi|Goa|Noida|Gurugram|'
    r'Gurgaon|Faridabad|Meerut|Nashik|Rajkot|Amritsar|Jodhpur|Raipur|'
    r'Ranchi|Dehradun|Mysuru|Mysore|Vijayawada|Visakhapatnam|Madurai)\b',
    re.I
)

def parse_query(query: str) -> dict:
    q = query.lower()
    role = None
    for r, kws in ROLE_KEYWORDS.items():
        if any(kw in q for kw in kws):
            role = r; break

    city_m = CITY_RE.search(query)
    city = city_m.group(0).title() if city_m else ""

    rewrite = query
    if role and city:
        rewrite = f"{role} in {city}"
    elif role:
        rewrite = f"{role} artist India"
    elif city:
        rewrite = f"event artist in {city}"

    return {"role": role or "Artist", "city": city, "rewrite": rewrite, "original": query}

def smart_search(query: str) -> dict:
    parsed = parse_query(query)
    results = search_instagram_artists(
        query=parsed["rewrite"],
        city=parsed["city"],
        category=parsed["role"]
    )
    return {"parsed": parsed, "results": results}
