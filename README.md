# WoM Lead Generation Tool v3

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

## What it does
- Enter any public figure's name
- Runs 5 search queries (pages 1-5) via DuckDuckGo
- Ranks results by name-match score + follower count
- Shows top 5 profiles — you pick the right one
- Saves to SQLite DB with category badge
- Generates DM drafts
