# 🎭 WoM Lead Generation & Outreach Tool

A Streamlit app to find, save, and reach out to Instagram artists for events.

## Features
- 🧠 **Smart Search** — Natural language search ("I need a DJ in Mumbai")
- 🔍 **Instagram Search** — Scrape artists by keyword, city, category
- 📇 **Contact Extraction** — Auto-extracts emails, phone, WhatsApp, Linktree
- 🗄️ **Database** — SQLite persistence, filter, export CSV
- 📤 **Outreach** — Auto-generated DM templates per category

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure
```
wom_tool/
├── app.py                  # Main Streamlit UI
├── config.py               # API keys & settings
├── requirements.txt
└── modules/
    ├── smart_search.py     # NLP query parser
    ├── search.py           # DuckDuckGo Instagram scraper
    ├── database.py         # SQLite lead storage
    ├── contacts.py         # Email/phone/WA extractor
    ├── outreach.py         # DM templates
    ├── pipeline.py         # Save + enrich flow
    ├── categories.py       # Category detection
    ├── enrichment.py       # Instagram bio fetcher
    └── validator.py        # Input validation
```
