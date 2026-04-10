from modules.database import save_lead
from modules.enrichment import fetch_instagram_bio
from modules.contacts import extract_contacts, merge_contacts, contacts_summary
from modules.categories import detect_category
from modules.validator import validate_username

def process_and_save(lead: dict) -> dict:
    valid, username = validate_username(lead.get("username",""))
    if not valid:
        return {"success": False, "error": username}
    lead["username"] = username

    bio_data = fetch_instagram_bio(username)
    if bio_data:
        lead.setdefault("full_name", bio_data.get("full_name",""))
        lead.setdefault("bio", bio_data.get("bio",""))
        lead.setdefault("followers", bio_data.get("followers",0))
        if not lead.get("category"):
            lead["category"] = detect_category(lead.get("bio",""))

    bio_text = lead.get("bio","")
    snippet_contacts = extract_contacts(bio_text)
    bio_contacts = extract_contacts(bio_data.get("email","") + " " + bio_data.get("phone",""))
    merged = merge_contacts(snippet_contacts, bio_contacts)
    lead["emails"]   = ", ".join(merged.get("emails",[]))
    lead["phones"]   = ", ".join(merged.get("phones",[]))
    lead["whatsapp"] = ", ".join(merged.get("whatsapp",[]))
    lead["linktree"] = ", ".join(merged.get("linktree",[]))

    result = save_lead(lead)
    return {"success": True, "lead": lead} if result is True else {"success": False, "error": result}
