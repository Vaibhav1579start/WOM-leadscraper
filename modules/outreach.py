from datetime import datetime

TEMPLATES = {
    "DJ": "Hey {name}! 👋 Love your DJ sets. We'd love to feature you for upcoming events in {city}. Interested in collaborations? 🎧",
    "Singer": "Hi {name}! 🎤 Your voice is amazing. We're looking for talented singers for events in {city}. Would love to connect!",
    "Magician": "Hey {name}! 🪄 Your magic is incredible! We have events in {city} looking for performers like you. Let's talk!",
    "Comedian": "Hi {name}! 😂 Your comedy is gold. We're booking stand-up acts for events in {city}. Interested?",
    "Dancer": "Hey {name}! 💃 Your performances are stunning. We'd love to have you at events in {city}. Let's connect!",
    "Musician": "Hi {name}! 🎵 Your music is beautiful. We're looking for live musicians for events in {city}. Interested?",
    "Anchor": "Hey {name}! 🎙️ You're a fantastic host. We have anchoring opportunities for events in {city}. Let's connect!",
    "default": "Hey {name}! 👋 We came across your profile and love your work! We have exciting event opportunities in {city}. Would love to connect and discuss collaborations! 🌟",
}

def generate_dm(lead: dict) -> str:
    category = lead.get("category", "default")
    template = TEMPLATES.get(category, TEMPLATES["default"])
    return template.format(
        name=lead.get("full_name", "").split()[0] if lead.get("full_name") else "there",
        city=lead.get("city", "your city"),
    )

def log_outreach(username: str, message: str, channel: str = "DM"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {"username": username, "channel": channel, "message": message, "sent_at": timestamp}
