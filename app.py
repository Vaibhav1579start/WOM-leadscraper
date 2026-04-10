import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from config import DAILY_DM_LIMIT
from modules.database import get_all_leads, save_lead, update_lead_status, delete_lead, leads_to_csv, init_db
from modules.search import search_instagram_artists
from modules.smart_search import smart_search, parse_query
from modules.outreach import generate_dm
from modules.pipeline import process_and_save
from modules.contacts import contacts_summary, extract_contacts

st.set_page_config(page_title="WoM Lead Tool", page_icon="🎭", layout="wide")
init_db()

st.title("🎭 WoM Lead Generation & Outreach Tool")
tabs = st.tabs(["🧠 Smart Search", "🔍 Search & Pick", "✍️ Manual Entry", "🗄️ Database", "📤 Outreach", "📖 Guide"])

# ─── SMART SEARCH ────────────────────────────────────────────────────────────
with tabs[0]:
    st.header("🧠 Smart Search — Natural Language")
    st.caption("Type naturally, e.g. *'I need a magician in Nagpur'* or *'find DJs in Mumbai for a wedding'*")
    
    col1, col2 = st.columns([4,1])
    with col1:
        smart_q = st.text_input("Your request:", placeholder="I need a singer in Pune for a birthday party", key="smart_q")
    with col2:
        smart_btn = st.button("🔍 Search", key="smart_search_btn", use_container_width=True)

    if smart_btn and smart_q:
        with st.spinner("🤖 Parsing your request and searching..."):
            out = smart_search(smart_q)
        parsed = out["parsed"]
        results = out["results"]
        
        st.info(f"🧠 Detected: **Role** = `{parsed['role']}` | **City** = `{parsed['city'] or 'Any'}` | **Search query** = `{parsed['rewrite']}`")
        st.success(f"✅ Found **{len(results)}** results")

        for r in results:
            with st.expander(f"{'@'+r['username'] if r.get('username') else r.get('full_name','?')} — {r.get('follower_tier','')} — {r.get('category','')}"):
                c1, c2 = st.columns([3,1])
                with c1:
                    st.markdown(f"**Bio:** {r.get('bio','')[:200]}")
                    if r.get("contacts_summary"):
                        st.markdown(f"📇 **Contacts:** {r['contacts_summary']}")
                    st.caption(f"🔗 {r.get('url','')}")
                with c2:
                    st.metric("Followers", r.get("followers",0))
                    if st.button("✅ Pick", key=f"smart_pick_{r.get('username','')}"):
                        result = process_and_save({**r, "source":"smart_search"})
                        if result["success"]:
                            st.success("✅ Saved to database!")
                        else:
                            st.error(f"Error: {result['error']}")

# ─── SEARCH & PICK ───────────────────────────────────────────────────────────
with tabs[1]:
    st.header("🔍 Instagram Artist Search")
    col1, col2, col3 = st.columns(3)
    with col1:
        s_query = st.text_input("Search query", placeholder="wedding DJ Mumbai")
    with col2:
        s_city = st.text_input("City", placeholder="Mumbai")
    with col3:
        s_category = st.selectbox("Category", ["","DJ","Singer","Musician","Magician","Comedian","Dancer","Anchor","Band","Photographer","Videographer","Decorator","Caterer"])

    if st.button("🔍 Search Instagram", use_container_width=True):
        with st.spinner("Searching..."):
            results = search_instagram_artists(s_query, s_city, s_category)
        st.success(f"Found {len(results)} results")
        st.session_state["search_results"] = results

    for r in st.session_state.get("search_results", []):
        with st.expander(f"@{r.get('username','?')} — {r.get('follower_tier','')} — {r.get('category','')}"):
            c1, c2 = st.columns([3,1])
            with c1:
                st.markdown(f"**Bio:** {r.get('bio','')[:200]}")
                if r.get("contacts_summary"):
                    st.markdown(f"📇 {r['contacts_summary']}")
                st.caption(r.get("url",""))
            with c2:
                st.metric("Followers", r.get("followers",0))
                if st.button("✅ Pick", key=f"pick_{r.get('username','')}"):
                    result = process_and_save({**r, "source":"search"})
                    st.success("Saved!" if result["success"] else f"Error: {result['error']}")

# ─── MANUAL ENTRY ────────────────────────────────────────────────────────────
with tabs[2]:
    st.header("✍️ Manual Lead Entry")
    with st.form("manual_form"):
        c1, c2 = st.columns(2)
        with c1:
            m_user = st.text_input("Instagram Username *")
            m_name = st.text_input("Full Name")
            m_cat  = st.selectbox("Category *", ["DJ","Singer","Musician","Magician","Comedian","Dancer","Anchor","Band","Photographer","Videographer","Decorator","Caterer","Other"])
            m_city = st.text_input("City")
        with c2:
            m_followers = st.number_input("Followers", min_value=0, value=0)
            m_email = st.text_input("Email")
            m_phone = st.text_input("Phone")
            m_notes = st.text_area("Notes")
        submitted = st.form_submit_button("💾 Save Lead")
        if submitted and m_user:
            lead = {"username":m_user,"full_name":m_name,"category":m_cat,"city":m_city,
                    "followers":m_followers,"emails":m_email,"phones":m_phone,"notes":m_notes,"source":"manual"}
            result = process_and_save(lead)
            st.success("✅ Lead saved!" if result["success"] else f"❌ {result['error']}")

# ─── DATABASE ────────────────────────────────────────────────────────────────
with tabs[3]:
    st.header("🗄️ Lead Database")
    col1, col2, col3 = st.columns(3)
    with col1:
        f_status = st.selectbox("Filter Status", ["All","new","contacted","interested","not_interested","booked"])
    with col2:
        f_cat = st.selectbox("Filter Category", ["All","DJ","Singer","Musician","Magician","Comedian","Dancer","Anchor","Other"])
    with col3:
        f_q = st.text_input("Search name/city")

    leads = get_all_leads(f_status, f_cat, f_q)
    st.metric("Total Leads", len(leads))

    if leads:
        df = pd.DataFrame(leads)
        st.dataframe(df, use_container_width=True, height=400)
        csv_data = leads_to_csv(leads)
        st.download_button("📥 Export CSV", csv_data, "leads.csv", "text/csv")

        st.divider()
        st.subheader("Update Lead Status")
        usernames = [l["username"] for l in leads]
        sel_user = st.selectbox("Select Lead", usernames)
        new_status = st.selectbox("New Status", ["new","contacted","interested","not_interested","booked"])
        new_notes = st.text_area("Notes")
        if st.button("💾 Update"):
            update_lead_status(sel_user, new_status, new_notes)
            st.success("✅ Updated!")
        if st.button("🗑️ Delete Lead", type="secondary"):
            delete_lead(sel_user)
            st.warning("Lead deleted.")
    else:
        st.info("No leads yet. Use Search or Smart Search to find and pick artists.")

# ─── OUTREACH ────────────────────────────────────────────────────────────────
with tabs[4]:
    st.header("📤 Outreach Manager")
    leads = get_all_leads(status_filter="new")
    st.metric("Leads Ready for Outreach", len(leads))
    
    if leads:
        for lead in leads[:DAILY_DM_LIMIT]:
            with st.expander(f"@{lead['username']} — {lead['category']} — {lead.get('city','')}"):
                dm = generate_dm(lead)
                st.text_area("DM Message", dm, key=f"dm_{lead['username']}", height=100)
                contacts = []
                if lead.get("emails"):    contacts.append(f"📧 {lead['emails']}")
                if lead.get("phones"):    contacts.append(f"📞 {lead['phones']}")
                if lead.get("whatsapp"): contacts.append(f"💬 WA: {lead['whatsapp']}")
                if contacts:
                    st.info("Contacts: " + " | ".join(contacts))
                if st.button(f"✅ Mark as Contacted", key=f"contact_{lead['username']}"):
                    update_lead_status(lead["username"], "contacted")
                    st.success("Marked as contacted!")
    else:
        st.info("No new leads. Add leads via Search tabs.")

# ─── GUIDE ───────────────────────────────────────────────────────────────────
with tabs[5]:
    st.header("📖 How to Use WoM Lead Tool")
    st.markdown("""
### 🚀 Quick Start
1. **🧠 Smart Search** — Type naturally: *"I need a DJ in Mumbai"*
2. **🔍 Search & Pick** — Manual keyword search with filters
3. **✅ Pick** — Saves artist to database with contact details
4. **🗄️ Database** — View, filter, export all saved leads
5. **📤 Outreach** — Auto-generate DMs, mark as contacted

### 📇 Contact Extraction
The tool automatically extracts:
- 📧 Emails from bios and snippets
- 📞 Phone numbers (Indian + international formats)
- 💬 WhatsApp numbers
- 🔗 Linktree links

### 💡 Tips
- Use the Smart Search for fastest results
- Export CSV for CRM import
- Daily DM limit is set to avoid spam flags
- All data is saved locally in `leads.db` (SQLite)
    """)
