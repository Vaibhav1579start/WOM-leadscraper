import re

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_RE = re.compile(r'(?:\+91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}')
WA_RE    = re.compile(r'(?:wa\.me/|whatsapp[:\s]+)(\+?[0-9\s\-]{10,15})', re.I)
LTREE_RE = re.compile(r'linktr\.ee/[\w\-]+', re.I)
BIO_RE   = re.compile(r'link in bio', re.I)

def extract_contacts(text: str) -> dict:
    text = text or ""
    emails   = list({e.lower() for e in EMAIL_RE.findall(text)})
    wa_nums  = [''.join(filter(str.isdigit, m)) for m in WA_RE.findall(text)]
    all_ph   = [''.join(filter(str.isdigit, p)) for p in PHONE_RE.findall(text)]
    phones   = [p for p in all_ph if p not in wa_nums]
    linktree = LTREE_RE.findall(text)
    link_bio = bool(BIO_RE.search(text))
    return dict(emails=emails, phones=phones, whatsapp=wa_nums,
                linktree=[f"https://{l}" for l in linktree], link_in_bio=link_bio)

def merge_contacts(a: dict, b: dict) -> dict:
    def uniq(x, y): return list(dict.fromkeys((x or []) + (y or [])))
    return dict(
        emails   = uniq(a.get("emails"), b.get("emails")),
        phones   = uniq(a.get("phones"), b.get("phones")),
        whatsapp = uniq(a.get("whatsapp"), b.get("whatsapp")),
        linktree = uniq(a.get("linktree"), b.get("linktree")),
        link_in_bio = a.get("link_in_bio") or b.get("link_in_bio"),
    )

def has_any(c: dict) -> bool:
    return bool(c.get("emails") or c.get("phones") or c.get("whatsapp") or c.get("linktree"))

def contacts_summary(c: dict) -> str:
    parts = []
    for e in (c.get("emails") or []):   parts.append(f"📧 {e}")
    for p in (c.get("phones") or []):   parts.append(f"📞 {p}")
    for w in (c.get("whatsapp") or []): parts.append(f"💬 WA: {w}")
    for l in (c.get("linktree") or []): parts.append(f"🔗 {l}")
    if c.get("link_in_bio"):            parts.append("🔗 Link in bio")
    return "  ·  ".join(parts)
