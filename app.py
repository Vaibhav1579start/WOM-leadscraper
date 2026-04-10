"""WoM Lead Generation & Outreach Tool v5 — run: streamlit run app.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import config
from modules import search as search_mod, database, outreach, pipeline, enrichment, validator
from modules import smart_search as smart_mod
from modules.categories import badge as cat_badge, meta as cat_meta, all_keys as all_cat_keys
from modules.contacts import extract_contacts, merge_contacts, contacts_summary, has_any

st.set_page_config(page_title="WoM Lead Tool", page_icon="🎯", layout="wide",
                   initial_sidebar_state="expanded")

if "search_results" not in st.session_state: st.session_state["search_results"] = {}
if "smart_results"  not in st.session_state: st.session_state["smart_results"]  = {}
if "confirmed"      not in st.session_state: st.session_state["confirmed"]      = {}
if "check_later"    not in st.session_state: st.session_state["check_later"]    = set()
if "enriched"       not in st.session_state: st.session_state["enriched"]       = {}

# ── helpers ────────────────────────────────────────────────────────────────

def _fmt_followers(f):
    if not f: return "unknown"
    try:
        n = int(float(f))
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.1f}K"
        return str(n)
    except: return str(f)

def _render_contacts(contacts: dict, key_prefix: str = ""):
    """Render contact chips inside a streamlit container."""
    if not contacts or not has_any(contacts):
        st.caption("📭 No contact details found in snippet")
        return
    cols_data = []
    for e in contacts.get("emails", []):
        cols_data.append(("📧", e, f"mailto:{e}"))
    for w in contacts.get("whatsapp", []):
        cols_data.append(("💬", f"WA: {w}", f"https://wa.me/{w.replace('+','')}"))
    for p in contacts.get("phones", []):
        cols_data.append(("📞", p, f"tel:{p}"))
    for lt in contacts.get("linktree", []):
        cols_data.append(("🔗", "Linktree", lt))
    if contacts.get("link_in_bio"):
        cols_data.append(("🔗", "Link in bio", None))

    for icon, label, href in cols_data[:6]:
        if href:
            st.markdown(f"{icon} [{label}]({href})")
        else:
            st.caption(f"{icon} {label}")

def _enrich_and_merge(username: str, existing_contacts: dict) -> dict:
    """Fetch IG page contacts and merge with snippet contacts."""
    cache_key = f"enrich_{username}"
    if cache_key in st.session_state["enriched"]:
        return st.session_state["enriched"][cache_key]
    with st.spinner(f"Fetching @{username} profile for contact details…"):
        profile = enrichment.fetch_profile(username, delay=1.0)
    merged = merge_contacts(existing_contacts, profile.get("contacts", {}))
    st.session_state["enriched"][cache_key] = merged
    return merged

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    serpapi_key = st.text_input("SerpAPI Key (optional)", value=config.SERPAPI_KEY, type="password")
    if serpapi_key: config.SERPAPI_KEY = serpapi_key
    openai_key = st.text_input("OpenAI Key (optional)", value=os.getenv("OPENAI_API_KEY",""), type="password")
    if openai_key: os.environ["OPENAI_API_KEY"] = openai_key
    use_ai_dm   = st.toggle("AI-Generated DMs", value=False)
    daily_limit = st.number_input("Daily DM Limit", 1, 50, config.DAILY_DM_LIMIT)
    st.divider()
    db_path = os.path.abspath(config.DB_PATH)
    st.markdown("**💾 Database**")
    st.code(db_path, language=None)
    df_sz = database.load_all()
    if not df_sz.empty:
        st.success(f"✅ {len(df_sz)} records saved")
    else:
        st.info("No records yet.")
    st.caption("v5.0 · Contact extraction · Smart Search · name-match ranked")

tabs = st.tabs(["🔍 Search by Name", "🔮 Smart Search", "✏️ Manual Entry",
                "🗄️ Database", "📤 Outreach", "📖 Guide"])
tab_search, tab_smart, tab_manual, tab_db, tab_outreach, tab_guide = tabs

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — SEARCH BY NAME
# ═══════════════════════════════════════════════════════════════════════════
with tab_search:
    st.header("🔍 Search Instagram by Celebrity / Artist Name")
    st.info("Enter names → tool runs **5 search passes** → shows **top 5 ranked profiles** with contact details → pick the right one.")

    col1, col2 = st.columns([3, 1])
    with col1:
        artist_input = st.text_area("Names (one per line)", height=130,
            placeholder="Sangram Singh\nPalak Mucchal\nThermal And A Quarter")
    with col2:
        force_refresh = st.checkbox("Force re-search")
        run_btn = st.button("🚀 Search", type="primary", use_container_width=True)

    if run_btn:
        names = [n.strip() for n in artist_input.strip().splitlines() if n.strip()]
        if not names:
            st.warning("Enter at least one name.")
        else:
            prog = st.progress(0)
            for i, name in enumerate(names):
                if not force_refresh and name in st.session_state["search_results"]:
                    prog.progress((i+1)/len(names)); continue
                with st.spinner(f"Searching {name}…"):
                    st.session_state["search_results"][name] = search_mod.find_candidates(name, delay=0.3)
                prog.progress((i+1)/len(names))
            st.success("Done! Pick the correct profile below.")

    if st.session_state["search_results"]:
        st.divider()
        st.subheader("📋 Pick the Correct Profile")

        for name, result in st.session_state["search_results"].items():
            cat_key  = result.get("category_key", "other")
            cat_conf = float(result.get("category_conf", 0))
            cands    = result.get("candidates", [])
            web_sum  = result.get("web_summary","")

            conf_dot = "🟢" if cat_conf >= 0.66 else "🟡" if cat_conf >= 0.33 else "🔴"
            with st.expander(
                f"**{name}**  ·  {cat_badge(cat_key)}  {conf_dot} {int(cat_conf*100)}% confidence",
                expanded=(name not in st.session_state["confirmed"] and
                          name not in st.session_state["check_later"])
            ):
                if web_sum:
                    st.caption(f"🌐 {web_sum[:180]}")

                oc1, _, oc3 = st.columns([2,2,1])
                with oc1:
                    override = st.selectbox("Override category", options=all_cat_keys(),
                        index=all_cat_keys().index(cat_key) if cat_key in all_cat_keys() else 0,
                        format_func=lambda k: cat_badge(k), key=f"cat_{name}")
                    if override != cat_key:
                        result["category_key"] = override; cat_key = override
                with oc3:
                    if name not in st.session_state["confirmed"]:
                        if st.button("🕐 Check Later", key=f"later_{name}", use_container_width=True):
                            st.session_state["check_later"].add(name); st.rerun()

                if name in st.session_state["confirmed"]:
                    rec = st.session_state["confirmed"][name]
                    st.success(f"✅ Confirmed: @{rec.get('username','?')} · {cat_badge(rec.get('category','other'))}")
                    st.text_area("✉️ DM Draft", value=rec.get("dm_draft",""), height=90, key=f"dm_c_{name}")
                elif name in st.session_state["check_later"]:
                    st.warning("🕐 Marked for later review")
                    if st.button("↩️ Review now", key=f"review_{name}"):
                        st.session_state["check_later"].discard(name); st.rerun()
                else:
                    if not cands:
                        st.error("❌ No profiles found. Try Manual Entry.")
                    else:
                        total = len(cands)
                        st.markdown(f"**{total} profiles found · top 5 ranked ↓**")
                        rank_icons = ["🥇","🥈","🥉","4️⃣","5️⃣"]

                        for j, cand in enumerate(cands[:5]):
                            uname     = cand.get("username","")
                            followers = cand.get("followers")
                            snippet   = cand.get("snippet","")
                            nm        = cand.get("name_match", 0)
                            contacts  = cand.get("contacts", {})
                            val       = validator.validate_candidate(name, cand, cat_key)
                            conf      = val["confidence"]
                            cbadge    = {"High":"🟢","Medium":"🟡","Low":"🟠","Rejected":"🔴"}.get(conf,"⚪")

                            with st.container(border=True):
                                r1, r2, r3 = st.columns([2, 3, 1])
                                with r1:
                                    st.markdown(f"{rank_icons[j]} **[@{uname}](https://instagram.com/{uname})**")
                                    st.caption(f"👥 {_fmt_followers(followers)} followers")
                                    st.caption(f"🔤 Name match: **{int(nm)}**/100")
                                with r2:
                                    st.caption(snippet[:140] if snippet else "*(no snippet)*")
                                    if val["reasons"]:
                                        st.caption("✔ " + "  ·  ".join(val["reasons"][:2]))
                                    # ── Contact details from snippet ──
                                    contact_sum = contacts_summary(contacts)
                                    if contact_sum:
                                        st.markdown(f"**📇 Contacts:** {contact_sum}")
                                    else:
                                        # Offer to fetch from IG page
                                        if st.button(f"🔍 Fetch contacts", key=f"fc_{name}_{j}",
                                                     help="Scrape their Instagram page for email/phone"):
                                            merged = _enrich_and_merge(uname, contacts)
                                            cand["contacts"] = merged
                                            st.rerun()
                                with r3:
                                    st.markdown(f"{cbadge} **{conf}**")
                                    if st.button("✅ Pick", key=f"pick_{name}_{j}",
                                                 use_container_width=True,
                                                 type="primary" if conf in ("High","Medium") else "secondary"):
                                        # Auto-enrich contacts before saving
                                        if not has_any(contacts):
                                            merged = _enrich_and_merge(uname, contacts)
                                            cand["contacts"] = merged
                                        with st.spinner("Saving…"):
                                            rec = pipeline.confirm_and_save(name, cand, cat_key, cat_conf, use_ai_dm)
                                        st.session_state["confirmed"][name] = rec
                                        st.session_state["check_later"].discard(name)
                                        st.rerun()

        pending = [n for n in st.session_state["check_later"] if n not in st.session_state["confirmed"]]
        if pending:
            st.divider()
            st.subheader("🕐 Pending Review")
            for n in pending: st.warning(f"• {n}")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — SMART SEARCH
# ═══════════════════════════════════════════════════════════════════════════
with tab_smart:
    st.header("🔮 Smart Search — Find Artists by Type & City")
    st.info(
        "Describe in plain English:  "
        "`I need magicians in Nagpur` · `best DJs in Mumbai` · "
        "`classical dancers in Chennai` · `motivational speakers in Delhi`"
    )

    sq1, sq2 = st.columns([4, 1])
    with sq1:
        smart_query = st.text_input("What are you looking for?",
            placeholder="e.g. I need magicians in Nagpur")
    with sq2:
        smart_btn = st.button("🔮 Search", type="primary", use_container_width=True)

    if smart_btn:
        if not smart_query.strip():
            st.warning("Please enter a query.")
        else:
            with st.spinner(f'Searching for "{smart_query}"…'):
                st.session_state["smart_results"] = smart_mod.smart_find(smart_query)

    sr = st.session_state.get("smart_results", {})
    if sr:
        intent = sr.get("intent", {})
        cands  = sr.get("candidates", [])
        rw     = intent.get("role_keyword","?")
        city   = intent.get("city") or "India (nationwide)"

        st.divider()
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("🔍 Detected Role", rw.title())
        ic2.metric("📍 Location", city)
        ic3.metric("📊 Profiles Found", len(cands))

        if not cands:
            st.error("❌ No profiles found. Try rephrasing.")
        else:
            st.subheader(f"Results for **{rw}** in **{city}**")
            rank_icons = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

            for j, cand in enumerate(cands[:10]):
                uname    = cand.get("username","")
                followers= cand.get("followers")
                snippet  = cand.get("snippet","")
                contacts = cand.get("contacts", {})
                role_hit = cand.get("role_match", 0) > 0
                city_hit = cand.get("city_match", 0) > 0
                total_sc = cand.get("total_score", 0)

                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 4, 1])
                    with c1:
                        icon = rank_icons[j] if j < len(rank_icons) else "▪️"
                        st.markdown(f"{icon} **[@{uname}](https://instagram.com/{uname})**")
                        st.caption(f"👥 {_fmt_followers(followers)}")
                        tags = []
                        if role_hit: tags.append(f"✅ {rw}")
                        if city_hit: tags.append(f"📍 {city}")
                        if tags: st.caption("  ·  ".join(tags))
                    with c2:
                        st.caption(snippet[:160] if snippet else "*(no snippet)*")
                        # Contacts
                        contact_sum = contacts_summary(contacts)
                        if contact_sum:
                            st.markdown(f"**📇** {contact_sum}")
                        else:
                            if st.button(f"🔍 Fetch contacts", key=f"sfc_{j}",
                                         help="Scrape IG page for email/phone"):
                                merged = _enrich_and_merge(uname, contacts)
                                cand["contacts"] = merged
                                st.rerun()
                    with c3:
                        st.caption(f"Score: **{int(total_sc)}**")
                        role_guess = intent.get("role","other")
                        if role_guess not in all_cat_keys(): role_guess = "other"
                        if st.button("💾 Save", key=f"ss_{j}", use_container_width=True):
                            if not has_any(contacts):
                                merged = _enrich_and_merge(uname, contacts)
                                cand["contacts"] = merged
                            pipeline.confirm_and_save(uname, cand, role_guess, 0.5, use_ai_dm)
                            st.success(f"Saved @{uname}!")
                            st.rerun()
                        st.markdown(f"[📱 Open](https://instagram.com/{uname}/)")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — MANUAL ENTRY
# ═══════════════════════════════════════════════════════════════════════════
with tab_manual:
    st.header("✏️ Manual Entry")
    mc1, mc2, mc3 = st.columns(3)
    m_name     = mc1.text_input("Person Name",        placeholder="Virat Kohli")
    m_username = mc2.text_input("Instagram Username", placeholder="virat.kohli")
    m_category = mc3.selectbox("Category", options=all_cat_keys(), format_func=lambda k: cat_badge(k))

    if st.button("✅ Validate & Add", type="primary"):
        if not m_name or not m_username:
            st.error("Fill in both Name and Username.")
        else:
            uname = m_username.lstrip("@").strip()
            cand  = {"username":uname,"profile_url":f"https://instagram.com/{uname}/",
                     "snippet":"","followers":None,"source":"manual","contacts":{}}
            with st.spinner(f"Fetching @{uname}…"):
                profile = enrichment.fetch_profile(uname, delay=1.0)
            if profile.get("raw_ok"):
                cand["snippet"]   = profile.get("bio","")
                cand["followers"] = profile.get("followers")
                cand["contacts"]  = profile.get("contacts", {})
            val = validator.validate_candidate(m_name, cand, m_category)
            cb  = {"High":"🟢","Medium":"🟡","Low":"🟠","Rejected":"🔴"}.get(val["confidence"],"⚪")
            st.success(f"{cb} {val['confidence']} — @{uname} · {cat_badge(m_category)}")
            if val["reasons"]: st.info("  ·  ".join(val["reasons"]))
            # Show contacts
            contacts = cand.get("contacts",{})
            if has_any(contacts):
                st.subheader("📇 Contact Details Found")
                _render_contacts(contacts, key_prefix=uname)
            else:
                st.info("📭 No public contact details found on their profile.")
            rec = pipeline.confirm_and_save(m_name, cand, m_category, 1.0, use_ai_dm)
            st.text_area("✉️ DM Draft", value=rec.get("dm_draft",""), height=100)
            st.markdown(f"[📱 instagram.com/{uname}](https://instagram.com/{uname}/)")
            st.success("💾 Saved!")

    st.divider()
    st.subheader("📋 Bulk Entry")
    st.caption("Format: `Name | username | category` — one per line")
    bulk = st.text_area("Bulk Input", height=120,
        placeholder="Virat Kohli | virat.kohli | cricketer\nBillie Eilish | billieeilish | singer")
    if st.button("📥 Process Bulk"):
        lines = [l.strip() for l in bulk.strip().splitlines() if "|" in l]
        if not lines:
            st.error("No valid lines.")
        else:
            prog = st.progress(0); saved = []
            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split("|")]
                n, u  = parts[0], parts[1].lstrip("@") if len(parts)>1 else ""
                cat   = parts[2].lower() if len(parts)>2 else "other"
                if cat not in all_cat_keys(): cat = "other"
                cand  = {"username":u,"profile_url":f"https://instagram.com/{u}/",
                         "snippet":"","followers":None,"source":"manual","contacts":{}}
                rec   = pipeline.confirm_and_save(n, cand, cat, 1.0, use_ai_dm)
                saved.append(rec); prog.progress((i+1)/len(lines))
            st.success(f"✅ {len(saved)} entries saved!")
            st.dataframe(pd.DataFrame(saved)[["name","username","category","confidence","status"]],
                         use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — DATABASE
# ═══════════════════════════════════════════════════════════════════════════
with tab_db:
    st.header("🗄️ Database")
    db_path = os.path.abspath(config.DB_PATH)
    st.info(f"📁 Saved at: `{db_path}`  — persists across sessions.")

    df_all = database.load_all()
    if df_all.empty:
        st.info("No records yet.")
    else:
        fc1,fc2,fc3,fc4 = st.columns(4)
        f_cat  = fc1.multiselect("Category", sorted(df_all["category"].dropna().unique()))
        f_conf = fc2.multiselect("Confidence", ["High","Medium","Low","Rejected","Unknown"], default=["High","Medium"])
        f_stat = fc3.multiselect("Status", df_all["status"].dropna().unique().tolist())
        f_kw   = fc4.text_input("Search")

        fd = df_all.copy()
        if f_cat:  fd = fd[fd["category"].isin(f_cat)]
        if f_conf: fd = fd[fd["confidence"].isin(f_conf)]
        if f_stat: fd = fd[fd["status"].isin(f_stat)]
        if f_kw:   fd = fd[fd["name"].str.contains(f_kw,case=False,na=False)|
                           fd["username"].str.contains(f_kw,case=False,na=False)]

        # Parse JSON contact columns for display
        def _flatten_list_col(val):
            if not val or str(val) in ("nan","[]",""): return ""
            try:
                lst = json.loads(val) if isinstance(val, str) else val
                return ", ".join(lst) if isinstance(lst, list) else str(val)
            except: return str(val)

        fd_disp = fd.copy()
        fd_disp.insert(2,"Cat", fd["category"].apply(lambda k: cat_badge(str(k)) if k else "⭐"))
        fd_disp["📧 Emails"]   = fd["emails"].apply(_flatten_list_col)
        fd_disp["📞 Phones"]   = fd["phones"].apply(_flatten_list_col)
        fd_disp["💬 WhatsApp"] = fd["whatsapp"].apply(_flatten_list_col)

        show_cols = ["name","username","Cat","followers","confidence","status",
                     "📧 Emails","📞 Phones","💬 WhatsApp","profile_url"]
        st.caption(f"**{len(fd)}** of **{len(df_all)}** records")
        st.dataframe(fd_disp[show_cols], use_container_width=True, height=420)

        c1,c2 = st.columns(2)
        c1.download_button("⬇️ Filtered CSV", fd.to_csv(index=False).encode(), "filtered.csv","text/csv")
        c2.download_button("⬇️ Full DB",      df_all.to_csv(index=False).encode(),"full_db.csv","text/csv")

        s1,s2,s3,s4,s5,s6 = st.columns(6)
        s1.metric("Total",       len(df_all))
        s2.metric("🟢 High",     len(df_all[df_all["confidence"]=="High"]))
        s3.metric("🟡 Medium",   len(df_all[df_all["confidence"]=="Medium"]))
        s4.metric("🔴 Rejected", len(df_all[df_all["confidence"]=="Rejected"]))
        # Count records with at least one contact
        has_contact = df_all["emails"].apply(lambda v: bool(_flatten_list_col(v))) | \
                      df_all["phones"].apply(lambda v: bool(_flatten_list_col(v))) | \
                      df_all["whatsapp"].apply(lambda v: bool(_flatten_list_col(v)))
        s5.metric("📇 With Contacts", has_contact.sum())
        s6.metric("Categories",  df_all["category"].nunique())

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — OUTREACH
# ═══════════════════════════════════════════════════════════════════════════
with tab_outreach:
    st.header("📤 Outreach Assistant")
    st.warning(f"⚠️ Send DMs **manually** only. Suggested max: **{daily_limit}/day**.")
    df_all = database.load_all()
    qual   = df_all[df_all["confidence"].isin(["High","Medium"])] if not df_all.empty else pd.DataFrame()
    if qual.empty:
        st.info("No qualified profiles yet.")
    else:
        nd = qual[~qual["status"].str.contains("Contacted",na=False,case=False)]
        st.info(f"**{len(nd)}** profiles ready · showing {daily_limit}")
        for _, row in nd.head(daily_limit).iterrows():
            u = row.get("username","?"); cat = row.get("category","other")
            conf = row.get("confidence","?")
            cb = {"High":"🟢","Medium":"🟡","Low":"🟠","Rejected":"🔴"}.get(conf,"⚪")
            with st.expander(f"{cat_badge(cat)}  **{row['name']}** — @{u}  {cb} {conf}"):
                cl, cr = st.columns([1,2])
                with cl:
                    st.markdown(f"[@{u}](https://instagram.com/{u})")
                    bio = row.get("bio") or row.get("snippet","")
                    if bio: st.caption(str(bio)[:120])
                    try:
                        f = row.get("followers")
                        if f: st.markdown(f"👥 {_fmt_followers(f)}")
                    except: pass
                    # Contacts
                    st.markdown("**📇 Contact Details**")
                    def _row_contacts(row):
                        cd = {}
                        for fld in ("emails","phones","whatsapp","linktree"):
                            v = row.get(fld,"")
                            if v and str(v) not in ("nan","[]",""):
                                try:    cd[fld] = json.loads(v) if isinstance(v,str) else v
                                except: cd[fld] = [str(v)]
                            else:
                                cd[fld] = []
                        return cd
                    rc = _row_contacts(row)
                    if has_any(rc):
                        _render_contacts(rc, key_prefix=u)
                    else:
                        if st.button(f"🔍 Fetch contacts", key=f"ofc_{u}"):
                            merged = _enrich_and_merge(u, {})
                            # Save updated contacts back
                            rec_upd = {
                                "name": row["name"], "username": u,
                                "emails":   merged.get("emails",[]),
                                "phones":   merged.get("phones",[]),
                                "whatsapp": merged.get("whatsapp",[]),
                                "linktree": merged.get("linktree",[]),
                            }
                            database.save_record(rec_upd)
                            st.rerun()
                with cr:
                    dm = row.get("dm_draft","")
                    if not dm:
                        dm = outreach.generate_dm(row["name"], cat,
                                                  {"snippet": row.get("snippet","")}, use_ai_dm)
                    st.text_area("✉️ DM", value=dm, height=120, key=f"dm_{u}")
                    st.markdown(f"[📱 Open Instagram](https://instagram.com/{u}/)")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 — GUIDE
# ═══════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.header("📖 How to Use")
    st.markdown(f"""
## 🔍 Search by Name
Enter a celebrity/artist name → 5 searches → top 5 ranked → pick the right one.

## 🔮 Smart Search *(NEW)*
Describe what you need in plain English:
- `I need magicians in Nagpur`
- `best DJs in Mumbai`
- `stand-up comedians in Bangalore`
- `motivational speakers in Delhi`

## 📇 Contact Details *(NEW)*
The tool now tries to find **Email, Phone, WhatsApp, Linktree** from:
1. **Search snippets** — automatically, as results load
2. **Instagram profile page** — click **"🔍 Fetch contacts"** on any card
3. **Auto-fetch on Pick** — when you click ✅ Pick, contacts are fetched automatically before saving

Contacts are stored in the database and visible in every tab.

## 🗄️ Database
- Saves to `wom_leads.csv` in the folder you run the app from
- Persists across sessions — never deleted unless you delete the file
- Filter by category, confidence, status; export CSV

## ⚠️ DM Safety
- Max **{daily_limit} DMs/day** (set in sidebar)
- **Manual send only** — open Instagram, copy DM, send manually
- Space 30–60 min apart

## 🏷️ Supported Categories
🎤 Singer · 🎤 Rapper · 🎸 Musician · 🎬 Actor · 🏏 Cricketer · ⚽ Footballer  
🏅 Athlete · 😂 Comedian · 💃 Dancer · 🪄 Magician · 🎧 DJ · 🎙️ Anchor  
📷 Photographer · 💃 Model · 📱 Creator · 💼 Entrepreneur · 🎨 Visual Artist  
👨‍🍳 Chef · 🧘 Yoga · 🎤 Speaker · ⭐ Other
""")
