import re

def validate_username(username: str) -> tuple:
    username = username.strip().lstrip("@").split("/")[-1].split("?")[0]
    if not re.match(r'^[A-Za-z0-9_.]{1,30}$', username):
        return False, "Invalid Instagram username format"
    return True, username

def validate_lead(lead: dict) -> tuple:
    errors = []
    if not lead.get("username"): errors.append("Username is required")
    if not lead.get("category"): errors.append("Category is required")
    return len(errors)==0, errors
