import sqlite3, json, csv, io
from datetime import datetime
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            category TEXT,
            followers INTEGER,
            city TEXT,
            bio TEXT,
            emails TEXT,
            phones TEXT,
            whatsapp TEXT,
            linktree TEXT,
            source TEXT,
            status TEXT DEFAULT 'new',
            notes TEXT,
            added_at TEXT
        )
    """)
    conn.commit(); conn.close()

def save_lead(lead: dict):
    init_db()
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR REPLACE INTO leads
            (username,full_name,category,followers,city,bio,emails,phones,whatsapp,linktree,source,status,notes,added_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            lead.get("username",""),
            lead.get("full_name",""),
            lead.get("category",""),
            lead.get("followers",0),
            lead.get("city",""),
            lead.get("bio",""),
            lead.get("emails",""),
            lead.get("phones",""),
            lead.get("whatsapp",""),
            lead.get("linktree",""),
            lead.get("source","search"),
            lead.get("status","new"),
            lead.get("notes",""),
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ))
        conn.commit()
        return True
    except Exception as e:
        return str(e)
    finally:
        conn.close()

def get_all_leads(status_filter=None, category_filter=None, search_q=None):
    init_db()
    conn = get_conn()
    q = "SELECT * FROM leads WHERE 1=1"
    params = []
    if status_filter and status_filter != "All":
        q += " AND status=?"; params.append(status_filter)
    if category_filter and category_filter != "All":
        q += " AND category=?"; params.append(category_filter)
    if search_q:
        q += " AND (username LIKE ? OR full_name LIKE ? OR city LIKE ?)"
        params += [f"%{search_q}%"]*3
    q += " ORDER BY added_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_lead_status(username, status, notes=""):
    init_db()
    conn = get_conn()
    conn.execute("UPDATE leads SET status=?, notes=? WHERE username=?", (status, notes, username))
    conn.commit(); conn.close()

def delete_lead(username):
    init_db()
    conn = get_conn()
    conn.execute("DELETE FROM leads WHERE username=?", (username,))
    conn.commit(); conn.close()

def leads_to_csv(leads):
    if not leads: return ""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=leads[0].keys())
    w.writeheader(); w.writerows(leads)
    return out.getvalue()
