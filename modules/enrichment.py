import requests, re

def fetch_instagram_bio(username: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        r = requests.get(url, headers=headers, timeout=8)
        data = r.json()
        user = data.get("graphql",{}).get("user") or data.get("data",{}).get("user",{})
        return {
            "full_name": user.get("full_name",""),
            "bio": user.get("biography",""),
            "followers": user.get("edge_followed_by",{}).get("count",0),
            "email": user.get("public_email",""),
            "phone": user.get("public_phone_number",""),
        }
    except:
        return {}
