import re, time
from modules.categories import detect_category
from modules.contacts import extract_contacts, contacts_summary

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

FOLLOWER_RE = re.compile(r'([\d,.]+[KkMm]?)\s*(?:followers|Followers)')
IG_USER_RE  = re.compile(r'instagram\.com/([A-Za-z0-9_.]+)')

def _parse_followers(text):
    m = FOLLOWER_RE.search(text)
    if not m: return 0
    v = m.group(1).replace(',','')
    if v[-1] in 'Kk': return int(float(v[:-1])*1000)
    if v[-1] in 'Mm': return int(float(v[:-1])*1_000_000)
    return int(v)

def follower_tier(n):
    if n >= 1_000_000: return "🌟 Mega (1M+)"
    if n >= 100_000:   return "⭐ Macro (100K+)"
    if n >= 10_000:    return "✨ Mid (10K+)"
    if n >= 1_000:     return "🔹 Micro (1K+)"
    return "🔸 Nano (<1K)"

def search_instagram_artists(query: str, city: str = "", category: str = "") -> list:
    results = []
    if not HAS_DDGS:
        return [{"error": "ddgs not installed. Run: pip install ddgs"}]

    queries = [
        f'site:instagram.com {query} {city} {category}',
        f'instagram {query} {city} performer',
        f'instagram.com "{category}" "{city}" artist',
        f'instagram {category} artist {city} India booking',
        f'{query} instagram followers {city}',
    ]

    seen = set()
    with DDGS() as ddgs:
        for q in queries:
            try:
                for r in ddgs.text(q, max_results=5):
                    username = ""
                    m = IG_USER_RE.search(r.get("href","") + " " + r.get("body",""))
                    if m:
                        username = m.group(1)
                        if username in ("p","reel","stories","explore","accounts","") or username in seen:
                            continue
                        seen.add(username)

                    snippet = r.get("body","")
                    contacts = extract_contacts(snippet)
                    followers = _parse_followers(snippet)
                    cat = detect_category(snippet) if not category else category

                    results.append({
                        "username": username or r.get("title","")[:30],
                        "full_name": r.get("title","").split("|")[0].strip(),
                        "bio": snippet[:200],
                        "followers": followers,
                        "follower_tier": follower_tier(followers),
                        "category": cat,
                        "city": city,
                        "url": r.get("href",""),
                        "emails": ", ".join(contacts.get("emails",[])),
                        "phones": ", ".join(contacts.get("phones",[])),
                        "whatsapp": ", ".join(contacts.get("whatsapp",[])),
                        "linktree": ", ".join(contacts.get("linktree",[])),
                        "contacts_summary": contacts_summary(contacts),
                        "source": "ddgs",
                    })
                time.sleep(0.3)
            except Exception:
                continue

    results.sort(key=lambda x: x["followers"], reverse=True)
    return results
