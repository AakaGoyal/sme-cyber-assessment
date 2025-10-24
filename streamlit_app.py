import json
from io import StringIO
from typing import Dict, Any, List, Tuple

import pandas as pd
import streamlit as st

# =========================================================
# Page & global styles
# =========================================================
st.set_page_config(page_title="SME Assessment Wizard", page_icon="🧭", layout="wide")

CSS = """
<style>
.card{border:1px solid #eaeaea;border-radius:14px;padding:16px;background:#fff}
.qtitle{font-size:1.1rem;font-weight:600;margin:0 0 6px 0}
.qtip{font-size:.9rem;color:#666;margin-top:4px}
.small{font-size:.9rem;color:#666}
.footer{display:flex;gap:8px}
.footer .stButton>button{width:100%;border-radius:10px}
.header-phase{color:#555;font-weight:500}
.badge{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:600}
.red{background:#ffe7e7;border:1px solid #ffd0d0;color:#b10000}
.amber{background:#fff3cd;border:1px solid #ffe59a;color:#7a5b00}
.green{background:#e6f7e6;border:1px solid #c9efc9;color:#0d6b0d}
.kpi{border-radius:12px;border:1px solid #eee;padding:14px;background:#fafafa}
.kpi h4{margin:.1rem 0 .4rem 0}
ul.tight>li{margin-bottom:.3rem}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================================================
# Session init
# =========================================================
def ss_init():
    if stage"" not in st.session_state:"
        # intake -> qa -> done_initial -> cyber_qa -> cyber_results
        st.session_state.stage = "intake"
    if "profile" not in st.session_state:
        st.session_state.profile = {
            "contact_name": "",
            "business_name": "",
            "industry": "",
            "years": "",
            "headcount": "",
            "turnover": "",
            "work_mode": "",
        }
    if "answers" not in st.session_state:
        st.session_state.answers: Dict[str, Any] = {}
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "cyber_answers" not in st.session_state:
        st.session_state.cyber_answers: Dict[str, Any] = {}
    if "cyber_idx" not in st.session_state:
        st.session_state.cyber_idx = 0

ss_init()

# =========================================================
# Initial Assessment – Question Bank (Stage 1)
# =========================================================
QUESTIONS: List[Dict[str, Any]] = [
    # Digital Footprint
    {
        "id": "sell_online",
        "phase": "Digital Footprint",
        "text": "Do you sell products or deliver services online?",
        "type": "choice",
        "choices": ["Yes – on my own website","Yes – via marketplaces (Amazon/Etsy)","No – mostly offline"],
        "tip": "This helps us understand your online exposure and dependencies."
    },
    {
        "id": "data_types",
        "phase": "Digital Footprint",
        "text": "Do you store customer or employee information (e.g., emails, invoices, payment info)?",
        "type": "choice",
        "choices": ["Yes","No"],
        "tip": "Handling personal data increases your duty of care and regulatory exposure."
    },
    {
        "id": "tools_regular",
        "phase": "Digital Footprint",
        "text": "Which of these do you rely on daily?",
        "type": "multi",
        "choices": [
            "Email","Accounting/finance software","CRM or client database",
            "Cloud storage (Google Drive/OneDrive etc.)","Online payment system","Website or webshop"
        ],
        "tip": "This identifies where your critical information and daily operations live."
    },
    # IT Ownership
    {
        "id": "website_owner",
        "phase": "IT Ownership",
        "text": "Who looks after your website and online systems?",
        "type": "choice",
        "choices": ["I do it myself","Someone on my team","An external company or freelancer"]
    },
    {
        "id": "it_support",
        "phase": "IT Ownership",
        "text": "Who takes care of your computers, email and systems when something needs setup/fixing?",
        "type": "choice",
        "choices": ["I do","A friend/freelancer","An IT company","In-house IT team"]
    },
    {
        "id": "setup_by",
        "phase": "IT Ownership",
        "text": "Did you personally set up your main systems (email, website, backups)?",
        "type": "choice",
        "choices": ["Yes, mostly me","Shared effort","Someone else handled it"]
    },
    {
        "id": "asset_list",
        "phase": "IT Ownership",
        "text": "Do you have a clear list of systems, accounts and devices you use?",
        "type": "choice",
        "choices": ["Yes, documented","Rough idea","Not really"]
    },
    # Partners
    {
        "id": "third_parties",
        "phase": "Partners",
        "text": "Do you work with external partners who handle your data or systems (host, accountant, logistics, marketing tools)?",
        "type": "choice",
        "choices": ["Yes","No"]
    },
    {
        "id": "partner_count",
        "phase": "Partners",
        "text": "How many key partners or providers do you rely on?",
        "type": "choice",
        "choices": ["0–2","3–5","6+"]
    },
    {
        "id": "breach_contact",
        "phase": "Partners",
        "text": "If a main partner had a breach, would you know who to contact and what to do?",
        "type": "choice",
        "choices": ["Yes – I know who to reach","Not really sure"]
    },
    # Confidence
    {
        "id": "confidence",
        "phase": "Confidence",
        "text": "How prepared would you feel if a cyberattack or data loss hit tomorrow?",
        "type": "choice",
        "choices": ["Not at all","Somewhat","Fairly confident","Very confident"]
    },
    {
        "id": "past_incidents",
        "phase": "Confidence",
        "text": "Have you experienced a cybersecurity issue before (e.g., phishing, data loss, locked computer)?",
        "type": "choice",
        "choices": ["Yes","No","Not sure"]
    },
    {
        "id": "know_who_to_call",
        "phase": "Confidence",
        "text": "Do you know who to call or where to get help if something happened?",
        "type": "choice",
        "choices": ["Yes","No"]
    },
]
TOTAL = len(QUESTIONS)

# =========================================================
# Cybersecurity Posture – Question Bank (Stage 2)
# =========================================================
CYBER_QUESTIONS: List[Dict[str, Any]] = [
    # Access & Accounts
    {
        "id":"mfa_all",
        "domain":"Access & Accounts",
        "text":"Do all important accounts (email, admin portals, cloud storage, payment) use MFA?",
        "type":"choice",
        "choices":["Yes, for all important accounts","Yes, for some","No / not sure"],
        "weights":[2,1,0],
        "tip":"MFA blocks >95% of account-takeover attempts."
    },
    {
        "id":"shared_accounts",
        "domain":"Access & Accounts",
        "text":"Do people share logins, or does everyone have their own account?",
        "type":"choice",
        "choices":["Everyone has their own","Some shared accounts","Mostly shared accounts"],
        "weights":[2,1,0]
    },
    {
        "id":"admin_rights",
        "domain":"Access & Accounts",
        "text":"Are admin rights limited (used only when needed) and audited?",
        "type":"choice",
        "choices":["Yes, limited & reviewed","Partly","No / not sure"],
        "weights":[2,1,0]
    },

    # Devices
    {
        "id":"device_lock",
        "domain":"Devices",
        "text":"Are all laptops/phones protected with password/biometrics + auto-lock?",
        "type":"choice",
        "choices":["Yes, all","Most","No / not sure"],
        "weights":[2,1,0]
    },
    {
        "id":"disk_encryption",
        "domain":"Devices",
        "text":"Is full-disk encryption enabled on business laptops/desktops?",
        "type":"choice",
        "choices":["Yes, on all","Some / in progress","No / not sure"],
        "weights":[2,1,0]
    },

    # Data & Backups
    {
        "id":"backup_frequency",
        "domain":"Data & Backups",
        "text":"How often are business-critical files backed up?",
        "type":"choice",
        "choices":["Daily or continuous","Weekly","Rarely / never / not sure"],
        "weights":[2,1,0],
        "tip":"Follow 3-2-1: 3 copies, 2 media, 1 offsite/immutable."
    },
    {
        "id":"backup_restore_test",
        "domain":"Data & Backups",
        "text":"Do you periodically test restoring backups?",
        "type":"choice",
        "choices":["Yes, tested in last 6 months","Longer than 6 months","Never / not sure"],
        "weights":[2,1,0]
    },

    # Email & Awareness
    {
        "id":"phishing_training",
        "domain":"Email & Awareness",
        "text":"Do staff have regular phishing/security awareness training?",
        "type":"choice",
        "choices":["Yes, at least yearly","Ad-hoc / once","No / not sure"],
        "weights":[2,1,0]
    },
    {
        "id":"email_filters",
        "domain":"Email & Awareness",
        "text":"Do you have spam/malware filtering and link protection on email?",
        "type":"choice",
        "choices":["Yes, managed controls","Basic filtering only","No / not sure"],
        "weights":[2,1,0]
    },

    # Updates & AV
    {
        "id":"patching",
        "domain":"Updates & AV",
        "text":"Are operating systems and apps patched automatically within ~14 days?",
        "type":"choice",
        "choices":["Yes, automated","Partly manual","No / not sure"],
        "weights":[2,1,0]
    },
    {
        "id":"av_edr",
        "domain":"Updates & AV",
        "text":"Is reputable antivirus/EDR installed and centrally monitored?",
        "type":"choice",
        "choices":["Yes, on all devices","Some devices","No / not sure"],
        "weights":[2,1,0]
    },

    # Response & Continuity
    {
        "id":"ir_contacts",
        "domain":"Response & Continuity",
        "text":"If something goes wrong, do you have a simple incident checklist and contacts?",
        "type":"choice",
        "choices":["Yes, documented","Partial / informal","No / not sure"],
        "weights":[2,1,0]
    },
    {
        "id":"vendor_breach_flow",
        "domain":"Response & Continuity",
        "text":"If a vendor is breached, do you know their contact & steps to take?",
        "type":"choice",
        "choices":["Yes, clear contacts","Some idea","No / not sure"],
        "weights":[2,1,0]
    },
]
CYBER_TOTAL = len(CYBER_QUESTIONS)

# =========================================================
# Helpers
# =========================================================
def digital_dependency_score(ans: Dict[str, Any]) -> int:
    s = 0
    if ans.get("sell_online","").startswith("Yes"): s += 2
    if ans.get("data_types") == "Yes": s += 1
    s += min(len(ans.get("tools_regular", [])), 4)
    return s

def dd_text(v:int) -> str:
    return "Low" if v <= 2 else ("Medium" if v <= 5 else "High")

def reset_all():
    for k in ["stage","profile","answers","idx","cyber_answers","cyber_idx"]:
        if k in st.session_state: del st.session_state[k]
    ss_init()

def traffic_light(pct: float) -> Tuple[str, str]:
    if pct >= 75: return ("green","Good")
    if pct >= 40: return ("amber","Needs work")
    return ("red","At risk")

def compute_domain_scores(cyber_ans: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    domain_max: Dict[str,int] = {}
    domain_sum: Dict[str,int] = {}
    for q in CYBER_QUESTIONS:
        dom = q["domain"]
        domain_max[dom] = domain_max.get(dom, 0) + max(q["weights"])
        sel = cyber_ans.get(q["id"])
        if sel in q["choices"]:
            idx = q["choices"].index(sel)
            w = q["weights"][idx]
        else:
            w = 0
        domain_sum[dom] = domain_sum.get(dom, 0) + w

    results: Dict[str, Dict[str, Any]] = {}
    for dom in domain_max:
        pct = (domain_sum[dom] / domain_max[dom]) * 100 if domain_max[dom] else 0
        colour, label = traffic_light(pct)
        results[dom] = {"score": round(pct), "colour": colour, "label": label}
    return results

def overall_score(domain_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not domain_scores:
        return {"score": 0, "colour": "red", "label": "At risk"}
    avg = sum(v["score"] for v in domain_scores.values()) / len(domain_scores)
    colour, label = traffic_light(avg)
    return {"score": round(avg), "colour": colour, "label": label}

def add_action_cards(initial: Dict[str, Any], cyber: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Produce 'What you're doing well' and 'Top fixes' bullets from answers."""
    good, fixes = [], []
    A = cyber

    def chose(id_, i):
        q = next(q for q in CYBER_QUESTIONS if q["id"] == id_)
        sel = A.get(id_, "")
        return q["choices"].index(sel) == i if sel in q["choices"] else False

    # Strengths
    if chose("mfa_all", 0): good.append("MFA enabled on important accounts.")
    if chose("disk_encryption", 0): good.append("Full-disk encryption on devices.")
    if chose("backup_frequency", 0): good.append("Frequent (daily/continuous) backups.")
    if chose("backup_restore_test", 0): good.append("Backups are restore-tested.")
    if chose("patching", 0): good.append("Automated patching is in place.")
    if chose("av_edr", 0): good.append("AV/EDR deployed across devices.")
    if chose("phishing_training", 0): good.append("Regular phishing/security training.")
    if chose("ir_contacts", 0): good.append("Incident contacts/checklist documented.")

    # Fixes (ordered by risk)
    if not chose("mfa_all", 0):
        fixes.append("Turn on **MFA** for email, cloud storage, accounting, and admin portals (today).")
    if not chose("backup_frequency", 0):
        fixes.append("Implement **3-2-1 backups** with at least one **immutable/offsite** copy.")
    if not chose("disk_encryption", 0):
        fixes.append("Enable **full-disk encryption** (BitLocker/FileVault) on all laptops/desktops.")
    if not chose("patching", 0):
        fixes.append("Enable **automatic updates** for OS and key apps; patch within ~14 days.")
    if not chose("av_edr", 0):
        fixes.append("Deploy **reputable AV/EDR** on all devices and ensure it’s updating.")
    if not chose("ir_contacts", 0):
        fixes.append("Create a **one-page incident checklist** with internal & vendor contacts.")
    if not chose("phishing_training", 0):
        fixes.append("Schedule **annual phishing/awareness training** (15–30 minutes).")
    if not chose("email_filters", 0):
        fixes.append("Enable **advanced email filtering** (malware/link protection) in your mail suite.")
    if not chose("shared_accounts", 0):
        fixes.append("Stop using **shared accounts**; give each person their own login.")
    if not chose("admin_rights", 0):
        fixes.append("Restrict **admin rights**; use separate admin accounts and review quarterly.")

    # Tweak with Initial Assessment context
    if initial.get("breach_contact") == "Not really sure" and \
       "Create a **one-page incident checklist** with internal & vendor contacts." not in fixes:
        fixes.insert(0, "Add **vendor breach contacts** to your incident checklist (host, payments, accountant).")

    return good[:8], fixes[:10]

# =========================================================
# Sidebar (live snapshot)
# =========================================================
with st.sidebar:
    st.markdown("### Snapshot")
    p = st.session_state.profile
    st.markdown(
        f"**Business:** {p.get('business_name') or '—'}  \n"
        f"**Industry:** {p.get('industry') or '—'}  \n"
        f"**People:** {p.get('headcount') or '—'}  •  **Years:** {p.get('years') or '—'}  •  **Turnover:** {p.get('turnover') or '—'}  \n"
        f"**Work mode:** {p.get('work_mode') or '—'}  \n"
    )
    st.markdown("---")
    dd = dd_text(digital_dependency_score(st.session_state.answers))
    st.markdown(f"**Digital dependency (derived):** {dd}")
    st.caption("Derived from online sales, data handling, and daily tools.")
    if st.button("🔁 Restart"):
        reset_all()
        st.rerun()

# =========================================================
# Header
# =========================================================
st.title("🧭 SME Self-Assessment Wizard")

# =========================================================
# Stage 1: Intake
# =========================================================
if st.session_state.stage == "intake":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("First, tell us a bit about the business (≈2 minutes)")
    col1, col2 = st.columns(2)
    with col1:
        contact = st.text_input("Your name", value=st.session_state.profile.get("contact_name",""))
        bname   = st.text_input("Business name", value=st.session_state.profile.get("business_name",""))
        industry= st.text_input("Industry / core service (e.g., retail, consulting)")
    with col2:
        years    = st.selectbox("How long in business?", ["<1 year","1–3 years","3–10 years","10+ years"])
        headcount= st.selectbox("How many people (incl. contractors)?", ["Just me","2–5","6–20","21–100","100+"])
        turnover = st.selectbox("Approx. annual turnover", ["<€100k","€100k–500k","€500k–2M",">€2M"])
    work_mode = st.radio("Would you describe your business as mostly…", ["Local & in-person","Online/remote","A mix of both"], horizontal=True)

    c1, c2 = st.columns([1,2])
    with c1:
        proceed = st.button("Start Initial Assessment", type="primary", use_container_width=True)
    with c2:
        st.caption("We’ll tailor the next questions based on this.")
    st.markdown('</div>', unsafe_allow_html=True)

    if proceed:
        st.session_state.profile.update({
            "contact_name": contact.strip(),
            "business_name": bname.strip(),
            "industry": industry.strip(),
            "years": years,
            "headcount": headcount,
            "turnover": turnover,
            "work_mode": work_mode
        })
        st.session_state.stage = "qa"
        st.session_state.idx = 0
        st.rerun()

# =========================================================
# Stage 1: One-question-per-page (Initial Assessment)
# =========================================================
if st.session_state.stage == "qa":
    idx = st.session_state.idx
    q = QUESTIONS[idx]

    st.progress(idx / max(TOTAL, 1), text=f"Initial Assessment • {q['phase']} • {idx+1}/{TOTAL}")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="qtitle">{q["text"]}</div>', unsafe_allow_html=True)
    if q.get("tip"):
        with st.expander("Why this matters"):
            st.markdown(q["tip"])

    curr_val = st.session_state.answers.get(q["id"])

    if q["type"] == "choice":
        answer = st.radio("Select one:", q["choices"],
                          index=(q["choices"].index(curr_val) if curr_val in q["choices"] else 0),
                          key=f"radio_{q['id']}")
        st.session_state.answers[q["id"]] = answer
    elif q["type"] == "multi":
        sel = set(curr_val or [])
        cols = st.columns(2)
        updated = []
        for i, opt in enumerate(q["choices"]):
            with cols[i % 2]:
                if st.checkbox(opt, value=(opt in sel), key=f"chk_{q['id']}_{i}"):
                    updated.append(opt)
        st.session_state.answers[q["id"]] = updated
    else:
        txt = st.text_input("Your answer", value=curr_val or "")
        st.session_state.answers[q["id"]] = txt

    st.markdown('</div>', unsafe_allow_html=True)

    col_prev, col_skip, col_next = st.columns([1,1,1])
    with col_prev:
        if st.button("← Back", use_container_width=True, disabled=(idx == 0)):
            st.session_state.idx = max(idx - 1, 0)
            st.rerun()
    with col_skip:
        if st.button("Skip", use_container_width=True):
            next_idx = idx + 1
            if next_idx >= TOTAL:
                st.session_state.stage = "done_initial"
            else:
                st.session_state.idx = next_idx
            st.rerun()
    with col_next:
        if st.button("Save & Next →", type="primary", use_container_width=True):
            next_idx = idx + 1
            if next_idx >= TOTAL:
                st.session_state.stage = "done_initial"
            else:
                st.session_state.idx = next_idx
            st.rerun()

# =========================================================
# Stage 1: Summary + Continue
# =========================================================
if st.session_state.stage == "done_initial":
    st.success("Initial Assessment complete.")
    p, a = st.session_state.profile, st.session_state.answers
    dd = dd_text(digital_dependency_score(a))

    st.markdown("### Quick Summary")
    st.markdown(
        f"**Business:** {p.get('business_name') or '—'}  \n"
        f"**Industry:** {p.get('industry') or '—'}  \n"
        f"**People:** {p.get('headcount') or '—'} • **Years:** {p.get('years') or '—'} • **Turnover:** {p.get('turnover') or '—'}  \n"
        f"**Work mode:** {p.get('work_mode') or '—'}  \n\n"
        f"**Digital dependency (derived):** {dd}"
    )

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Highlights**")
        highlights = []
        if a.get("sell_online","").startswith("Yes"):
            highlights.append("Online sales increase reliance on website uptime and payment security.")
        if "Cloud storage (Google Drive/OneDrive etc.)" in a.get("tools_regular", []):
            highlights.append("Cloud storage is central — access controls and backups matter.")
        if a.get("data_types") == "Yes":
            highlights.append("You handle personal data — consider privacy and retention basics.")
        if not highlights:
            highlights.append("Operational footprint looks light; next step focuses on essential hygiene.")
        for h in highlights:
            st.markdown(f"- {h}")

    with colB:
        st.markdown("**Potential blind spots**")
        blindspots = []
        if a.get("asset_list") in ["Rough idea","Not really"]:
            blindspots.append("No clear list of systems/accounts — hard to secure what you can’t see.")
        if a.get("breach_contact") == "Not really sure":
            blindspots.append("No partner-breach playbook — clarify contacts and escalation.")
        if a.get("confidence") in ["Not at all","Somewhat"]:
            blindspots.append("Low confidence — training and basic controls will lift resilience quickly.")
        if not blindspots:
            blindspots.append("Solid baseline. Next, validate backups, MFA, and incident basics.")
        for b in blindspots:
            st.markdown(f"- {b}")

    st.info("Next: Cybersecurity Posture (controls like MFA, backups, patching, awareness, incident response).")
    if st.button("→ Continue to Cybersecurity Posture", type="primary"):
        st.session_state.stage = "cyber_qa"
        st.session_state.cyber_idx = 0
        st.rerun()

# =========================================================
# Stage 2: Cybersecurity Posture – Wizard
# =========================================================
if st.session_state.stage == "cyber_qa":
    i = st.session_state.cyber_idx
    q = CYBER_QUESTIONS[i]
    st.progress(i / max(CYBER_TOTAL, 1), text=f"Cybersecurity Posture • {q['domain']} • {i+1}/{CYBER_TOTAL}")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="qtitle">{q["text"]}</div>', unsafe_allow_html=True)
    if q.get("tip"):
        with st.expander("Why this matters"):
            st.markdown(q["tip"])

    curr = st.session_state.cyber_answers.get(q["id"])
    answer = st.radio("Select one:", q["choices"],
                      index=(q["choices"].index(curr) if curr in q["choices"] else 0),
                      key=f"cy_radio_{q['id']}")
    st.session_state.cyber_answers[q["id"]] = answer
    st.markdown('</div>', unsafe_allow_html=True)

    col_prev, col_skip, col_next = st.columns([1,1,1])
    with col_prev:
        if st.button("← Back", use_container_width=True, disabled=(i == 0)):
            st.session_state.cyber_idx = max(i - 1, 0)
            st.rerun()
    with col_skip:
        if st.button("Skip", use_container_width=True):
            next_i = i + 1
            if next_i >= CYBER_TOTAL:
                st.session_state.stage = "cyber_results"
            else:
                st.session_state.cyber_idx = next_i
            st.rerun()
    with col_next:
        if st.button("Save & Next →", type="primary", use_container_width=True):
            next_i = i + 1
            if next_i >= CYBER_TOTAL:
                st.session_state.stage = "cyber_results"
            else:
                st.session_state.cyber_idx = next_i
            st.rerun()

# =========================================================
# Stage 2: Results – Traffic Lights + Action Cards
# =========================================================
if st.session_state.stage == "cyber_results":
    st.success("Cybersecurity Posture assessment complete.")
    scores = compute_domain_scores(st.session_state.cyber_answers)
    overall = overall_score(scores)

    def badge(colour, text):
        return f'<span class="badge {colour}">{text}</span>'

    # Overall KPI
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.markdown(
        f"#### Overall posture: {badge(overall['colour'], overall['label'])}  •  **{overall['score']}%**",
        unsafe_allow_html=True
    )
    st.caption("Scores reflect practical control coverage and are intended to guide priorities, not replace audits.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Domain KPIs
    dcols = st.columns(3)
    for idx, (dom, data) in enumerate(scores.items()):
        with dcols[idx % 3]:
            st.markdown('<div class="kpi">', unsafe_allow_html=True)
            st.markdown(f"**{dom}**")
            st.markdown(f"{badge(data['colour'], data['label'])} • **{data['score']}%**", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    good, fixes = add_action_cards(st.session_state.answers, st.session_state.cyber_answers)

    colA, colB = st.columns(2)
    with colA:
        st.markdown("### ✅ What you’re doing well")
        if good:
            st.markdown("<ul class='tight'>" + "".join([f"<li>{g}</li>" for g in good]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("We didn’t detect specific strengths yet — once you implement the fixes below, this list will grow.")

    with colB:
        st.markdown("### 🛠 Top recommended fixes")
        if fixes:
            st.markdown("<ul class='tight'>" + "".join([f"<li>{f}</li>" for f in fixes]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("Great baseline! Keep policies current and review quarterly.")

    # -------- Export (JSON / CSV) ----------
    st.markdown("---")
    st.info("Tip: capture this page as PDF for your records, or download JSON/CSV below.")
    export_payload = {
        "profile": st.session_state.profile,
        "initial_answers": st.session_state.answers,
        "cyber_answers": st.session_state.cyber_answers,
        "domain_scores": scores,
        "overall": overall,
        "strengths": good,
        "fixes": fixes
    }
    st.download_button("⬇️ Download JSON", data=json.dumps(export_payload, indent=2),
                       file_name="sme_assessment_results.json", mime="application/json")

    # CSV (domain scores only)
    df = pd.DataFrame([{"Domain": d, "Score": v["score"], "Label": v["label"]} for d, v in scores.items()])
    csv_buf = StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button("⬇️ Download CSV (domain scores)", data=csv_buf.getvalue(),
                       file_name="sme_domain_scores.csv", mime="text/csv")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("← Review answers"):
            st.session_state.stage = "cyber_qa"
            st.session_state.cyber_idx = 0
            st.rerun()
    with c2:
        if st.button("Restart whole assessment"):
            reset_all()
            st.rerun()
