# sme_assessment_app.py — one-file SME Cybersecurity Self-Assessment
# Run: streamlit run sme_assessment_app.py

import streamlit as st
from typing import List, Dict, Set, Literal, Tuple

# ─────────────────────────────────────────────────────────────
# Page setup & styles (INLINE CSS)
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="SME Cybersecurity Self-Assessment", layout="wide")

STYLES = """
<style>
  .block-container {max-width: 1160px; padding-top: 2.25rem !important;}
  h1 {font-size: 2.10rem !important;}
  h2 {font-size: 1.55rem !important;}
  h3 {font-size: 1.25rem !important;}
  .lead {color:#374151; margin:.35rem 0 .9rem; font-size:1.05rem}
  .q {font-size: 1.08rem; font-weight: 600; color:#111827; margin:.35rem 0 .35rem}
  .hint {color:#374151; font-size:.96rem; margin:.2rem 0 .7rem; font-style:italic}
  .chip {display:inline-flex;align-items:center;gap:.35rem;border-radius:999px;padding:.18rem .6rem;border:1px solid #e5e7eb;margin-right:.35rem;font-weight:600}
  .green{background:#e8f7ee;color:#0f5132;border-color:#cceedd}
  .amber{background:#fff5d6;color:#8a6d00;border-color:#ffe7ad}
  .red{background:#ffe5e5;color:#842029;border-color:#ffcccc}
  .card {border:1px solid #e6e8ec;border-radius:12px;padding:12px;background:#fff}
  .pill {display:inline-block;border-radius:999px;padding:.18rem .55rem;border:1px solid #e5e7eb;font-size:.9rem;color:#1f2937;background:#fff}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Inline Data (domains/questions + phishing scenarios)
# ─────────────────────────────────────────────────────────────
SECTIONS = [
    {"id":"Access & Identity","title":"Access & Identity","questions":[
      {"id":"ai_pw","text":"🔑 Are strong passwords required for all accounts?","hint":"Use at least 10–12 characters, avoid reuse. A password manager helps.","weight":1.0},
      {"id":"ai_mfa","text":"🛡️ Is Multi-Factor Authentication (MFA) enabled for key accounts?","hint":"Start with email, admin and finance; use an authenticator app or security key.","weight":1.0},
      {"id":"ai_admin","text":"🧰 Are admin rights limited to only those who need them?","hint":"Grant temporarily, review quarterly, monitor admin sign-ins.","weight":1.0},
      {"id":"ai_shared","text":"👥 Are shared accounts avoided or controlled?","hint":"Prefer named accounts; if shared, rotate passwords and log usage.","weight":1.0},
      {"id":"ai_leavers","text":"🚪 Are old or unused accounts removed promptly?","hint":"Disable the same day a person leaves; reclaim devices and keys.","weight":1.0},
    ]},
    {"id":"Device & Data","title":"Device & Data","questions":[
      {"id":"dd_lock","text":"🔒 Are all laptops/phones protected with a password or PIN?","hint":"Also enable auto-lock (≤10 minutes) and find-my-device.","weight":1.0},
      {"id":"dd_fde","text":"💽 Is full-disk encryption enabled on laptops and mobiles?","hint":"Windows BitLocker, macOS FileVault, Android/iOS device encryption.","weight":1.0},
      {"id":"dd_edr","text":"🧿 Is reputable antivirus/EDR installed and active on all devices?","hint":"Examples: Microsoft Defender, CrowdStrike, SentinelOne.","weight":1.0},
      {"id":"dd_backup","text":"📦 Are important business files backed up regularly?","hint":"3-2-1 rule: 3 copies, 2 media, 1 offsite (cloud counts).","weight":1.0},
      {"id":"dd_restore","text":"🧪 Are backups tested so you know restore works?","hint":"Try restoring one file/VM quarterly; script it if possible.","weight":1.0},
      {"id":"dd_usb","text":"🧰 Are staff trained to handle suspicious files/USBs?","hint":"Block unknown USBs; preview links before clicking.","weight":1.0},
      {"id":"dd_wifi","text":"📶 Are company devices separated from personal ones on Wi-Fi?","hint":"Use separate SSIDs (Corp vs Guest); VLANs where possible.","weight":1.0},
    ]},
    {"id":"System & Software Updates","title":"System & Software Updates","questions":[
      {"id":"su_os_auto","text":"♻️ Are operating systems kept up to date automatically?","hint":"Turn on auto-update in Windows/macOS; MDM helps enforce.","weight":1.0},
      {"id":"su_apps","text":"🧩 Are business apps updated regularly?","hint":"Browsers, accounting, CRM, PoS; prefer auto-update channels.","weight":1.0},
      {"id":"su_unsupported","text":"⛔ Any devices running unsupported/outdated systems?","hint":"Replace/upgrade old OS versions; isolate until replaced.","weight":1.0},
      {"id":"su_review","text":"🗓️ Do you have a monthly reminder to review updates?","hint":"Calendar task, RMM/MSP report, or patch-tuesday checklist.","weight":1.0},
    ]},
    {"id":"Incident Preparedness","title":"Incident Preparedness","questions":[
      {"id":"ip_report","text":"📣 Do employees know how to report incidents or suspicious activity?","hint":"Phishing mailbox (phish@), Slack ‘#security’, service desk.","weight":1.0},
      {"id":"ip_plan","text":"📝 Do you have a simple incident response plan?","hint":"1-page checklist: who to call, what to collect, who to notify.","weight":1.0},
      {"id":"ip_log","text":"🧾 Are incident details recorded when they occur?","hint":"What/when/who/impact; template in your ticketing system helps.","weight":1.0},
      {"id":"ip_contacts","text":"📇 Are key contacts known for emergencies?","hint":"Internal IT, MSP, cyber insurer, legal, data-protection contact.","weight":1.0},
      {"id":"ip_test","text":"🎯 Have you tested or simulated a cyber incident?","hint":"30-minute tabletop twice a year; refine the plan afterwards.","weight":1.0},
    ]},
    {"id":"Vendor & Cloud","title":"Vendor & Cloud","questions":[
      {"id":"vc_cloud","text":"☁️ Do you use cloud tools to store company data?","hint":"M365, Google Workspace, Dropbox, sector SaaS (ERP, EHR, PoS).","weight":1.0},
      {"id":"vc_mfa","text":"🔐 Are cloud accounts protected with MFA and strong passwords?","hint":"Enforce tenant-wide MFA; require it for all admins.","weight":1.0},
      {"id":"vc_review","text":"🔎 Do you review how vendors protect your data?","hint":"Check DPA, data location, certifications (ISO 27001, SOC 2).","weight":1.0},
      {"id":"vc_access","text":"📜 Do you track which suppliers have access to systems/data?","hint":"Maintain a shared list; remove unused integrations.","weight":1.0},
      {"id":"vc_notify","text":"🚨 Will vendors notify you promptly if they have a breach?","hint":"Breach-notification clause + contact path tested once a year.","weight":1.0},
    ]},
    {"id":"Awareness & Training","title":"Awareness & Training","questions":[
      {"id":"at_training","text":"🎓 Have employees received any cybersecurity training?","hint":"Short e-learning or live session; track completion.","weight":1.0},
      {"id":"at_phish","text":"🐟 Do staff know how to spot phishing or scam emails?","hint":"Check sender, link URL, urgency, attachments; report quickly.","weight":1.0},
      {"id":"at_onboard","text":"🧭 Are new employees briefed during onboarding?","hint":"Add a 15-minute security starter; include password manager.","weight":1.0},
      {"id":"at_reminders","text":"📢 Do you share posters, reminders, or tips?","hint":"Monthly internal post: MFA, updates, phishing examples.","weight":1.0},
      {"id":"at_lead","text":"🤝 Does management actively promote cybersecurity?","hint":"Leaders mention it in all-hands; ask for MFA completion.","weight":1.0},
    ]},
    {"id":"Governance","title":"Governance","questions":[
      {"id":"gov_roles","text":"🏛️ Are cybersecurity roles and responsibilities clearly assigned?","hint":"One person (or partner) accountable for security oversight.","weight":1.0},
      {"id":"gov_policy","text":"📜 Do you have a basic information-security policy?","hint":"A 1–2 page policy covering access, acceptable use, and data protection.","weight":1.0},
      {"id":"gov_review","text":"📆 Is cybersecurity reviewed at least once a year by management?","hint":"Add it to your annual planning calendar.","weight":1.0},
      {"id":"gov_risk","text":"⚖️ Do you assess and log key security risks or incidents?","hint":"Even a short spreadsheet or helpdesk category helps track issues.","weight":1.0},
      {"id":"gov_comms","text":"📣 Do you communicate cyber updates or lessons learned to staff?","hint":"Mention it in all-hands; build a culture of improvement.","weight":1.0},
    ]},
]

PHISH_SCENARIOS = [
    {
      "id":"payroll_urgent",
      "subject":"Urgent: Verify your payroll account before 5PM",
      "sender_display":"HR Department",
      "sender_email":"hr@payroll-update-secure.com",
      "body":[
        "We’re finalising payroll today. Please verify your account immediately.",
        "Failure to act will result in payment delay.",
        "Click below to confirm your details."
      ],
      "flags":[
        {"label":"Urgent tone / deadline","why":"Pressure tactics reduce critical thinking."},
        {"label":"Suspicious link domain","why":"External domain spoofing a payroll system."},
        {"label":"Generic greeting","why":"No personalisation or internal reference."},
      ],
      "distractors":[{"label":"Missing company logo"}]
    }
]

# ─────────────────────────────────────────────────────────────
# Helpers: state & inputs
# ─────────────────────────────────────────────────────────────
def progress(step: int, total: int = 4, label: str = ""):
    pct = max(0, min(step, total)) / total
    st.progress(pct, text=label or f"Step {step} of {total}")

def radio_emoji(prompt: str, key: str, *, horizontal=True):
    choices = [("Yes","✅ Yes"), ("Partially","🟡 Partially"), ("No","❌ No"), ("Not sure","🤔 Not sure")]
    plain = [p for p,_ in choices]
    pretty = [d for _,d in choices]
    cur = st.session_state.get(key, "Partially")
    idx = plain.index(cur) if cur in plain else 1
    picked_pretty = st.radio(prompt, pretty, index=idx, horizontal=horizontal, key=f"pretty__{key}")
    st.session_state[key] = next(p for p,d in choices if d == picked_pretty)

# ─────────────────────────────────────────────────────────────
# Risk scoring & badges
# ─────────────────────────────────────────────────────────────
RISK_MAP = {"Yes":0.0, "Partially":1.0, "Not sure":1.0, "No":2.0}

def section_score(vals: List[str], weights: List[float] | None=None) -> float:
    if not vals: return 0.0
    w = weights or [1.0]*len(vals)
    num = sum(RISK_MAP.get(v,1.0)*wi for v,wi in zip(vals,w))
    den = sum(w)
    return round(num/den, 2) if den else 0.0

def section_light(sc: float) -> Tuple[str,str,str]:
    if sc < 0.5: return ("🟢","Low","green")
    if sc < 1.2: return ("🟡","Medium","amber")
    return ("🔴","High","red")

# ─────────────────────────────────────────────────────────────
# Tags & selection
# ─────────────────────────────────────────────────────────────
BASELINE_IDS = {"Access & Identity","Device & Data","System & Software Updates","Awareness & Training"}
ORDER = ["Access & Identity","Device & Data","System & Software Updates","Incident Preparedness","Vendor & Cloud","Awareness & Training","Governance"]

def compute_tags(state: Dict) -> Set[str]:
    tags:set[str]=set()
    tags.add(f"size:{state.get('derived_size','Small')}")
    industry_tag = state.get("industry_tag","other")
    tags.add(f"industry:{industry_tag}")
    tags.add(f"geo:{state.get('region_tag','eu')}")
    env = state.get("primary_work_env","Cloud apps")
    tags.add("infra:cloud" if env=="Cloud apps" else "infra:onprem" if env=="Local servers" else "infra:hybrid")
    for d in state.get("data_types",[]):
        dl=d.lower()
        if "customer" in dl: tags.add("data:pii")
        if "employee" in dl: tags.add("data:employee")
        if "health" in dl: tags.add("data:health")
        if "financial" in dl: tags.add("data:financial")
    if (state.get("bp_card_payments","No").lower()=="yes"): tags.add("payments:card")
    return tags

def pick_active_sections(tags: Set[str]) -> List[str]:
    active=set(BASELINE_IDS)
    if any(t in tags for t in ["size:Small","size:Medium"]):
        active.add("Incident Preparedness"); active.add("Governance")
    if any(t in tags for t in ["infra:cloud","system:pos","geo:crossborder"]):
        active.add("Vendor & Cloud")
    return [sid for sid in ORDER if sid in active]

# ─────────────────────────────────────────────────────────────
# Action Plan rules
# ─────────────────────────────────────────────────────────────
def governance_rules(score: float, tags: Set[str]):
    quick: List[str]=[]; foundations: List[str]=[]; nextlvl: List[str]=[]
    if score >= 1.2:
        quick += ["🏛️ Assign a clear cybersecurity lead (internal or MSP).",
                  "📜 Publish a 1-page information-security policy approved by management."]
    elif score >= 0.6:
        foundations += ["📆 Add cybersecurity to your annual planning/board agenda.",
                        "⚖️ Maintain a simple risk/incident log reviewed quarterly."]
    else:
        nextlvl += ["📈 Integrate cyber metrics (incidents, MFA adoption) into leadership dashboards."]
    if "size:Micro" in tags and score >= 1.2:
        quick.append("🏪 For micro orgs, the owner can be the named security contact.")
    return {"quick":quick, "foundations":foundations, "nextlvl":nextlvl}

def baseline_hooks(state: Dict) -> List[str]:
    q: List[str]=[]
    if state.get("df_website")=="Yes" and state.get("df_https")!="Yes":
        q.append("🔒 Enable HTTPS and force redirect (HTTP→HTTPS).")
    if state.get("df_email") in ("No","Partially"):
        q.append("📧 Move to business email (M365/Google) and enforce MFA for all users.")
    if state.get("bp_inventory") not in ("Yes","Partially"):
        q.append("📋 Start a simple device inventory (sheet or MDM export).")
    if state.get("bp_byod") in ("Yes","Sometimes"):
        q.append("📱 Publish a BYOD rule of 5: screen lock, updates, disk encryption, MFA for email, approved apps.")
    return q

def tag_hooks(tags: Set[str]) -> Dict[str,List[str]]:
    f = ["🧩 Turn on automatic OS & app updates; remove unsupported systems.",
         "🗄️ Automate backups and test a restore quarterly."]
    n: List[str]=[]
    if any(t in tags for t in ["infra:cloud","system:pos","geo:crossborder"]):
        n.append("🤝 Review key vendor contracts: breach notification, data location/transfer, and admin MFA.")
    if "payments:card" in tags:
        n.append("💳 Confirm PCI DSS responsibilities with your PoS/PSP (often most of the burden is on the provider).")
    if any(t in tags for t in ["geo:eu","geo:uk"]):
        n.append("📘 Document GDPR basics: Records of Processing, DPAs, and a contact for data requests.")
    return {"foundations":f, "nextlvl":n}

def build_plan(detailed_scores: Dict[str,float], tags: Set[str], state: Dict | None=None) -> Dict[str,List[str]]:
    Q: List[str]=[]; F: List[str]=[]; N: List[str]=[]
    g = detailed_scores.get("Governance")
    if g is not None:
        gp = governance_rules(g, tags)
        Q += gp["quick"]; F += gp["foundations"]; N += gp["nextlvl"]
    if state: Q += baseline_hooks(state)
    tn = tag_hooks(tags); F += tn["foundations"]; N += tn["nextlvl"]
    return {"quick": Q or ["No urgent quick wins detected."], "foundations": F, "nextlvl": N}

# ─────────────────────────────────────────────────────────────
# Export (Markdown + optional PDF)
# ─────────────────────────────────────────────────────────────
try:
    from fpdf import FPDF
except Exception:
    FPDF = None

def _latin(s: str) -> str:
    return s.encode("latin-1","ignore").decode("latin-1")

def build_markdown_report(state: dict, plan: dict, scores: dict) -> str:
    lines=[]
    lines.append("# SME Cybersecurity Self-Assessment — Summary & Action Plan")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- Business: {state.get('company_name','—')}")
    lines.append(f"- Region: {state.get('business_region','—')}")
    lines.append(f"- Industry: {state.get('industry','—')}")
    lines.append(f"- Size (derived): {state.get('derived_size','—')}")
    lines.append("")
    if scores:
        lines.append("## Section status")
        for sid, sc in scores.items():
            level = 'Low' if sc < 0.5 else 'Medium' if sc < 1.2 else 'High'
            lines.append(f"- {sid}: {level} (score {sc})")
        lines.append("")
    lines.append("## Action plan")
    lines.append("### Quick wins"); [lines.append(f"- {x}") for x in plan.get("quick",[])]
    lines.append("### Foundations"); [lines.append(f"- {x}") for x in plan.get("foundations",[])]
    lines.append("### Next-level / compliance"); [lines.append(f"- {x}") for x in plan.get("nextlvl",[])]
    return "\n".join(lines)

def build_pdf_from_markdown(md_text: str) -> bytes | None:
    if FPDF is None: return None
    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    def h1(t): pdf.set_font("Helvetica","B",16); pdf.multi_cell(0,8,_latin(t)); pdf.ln(2)
    def h2(t): pdf.set_font("Helvetica","B",14); pdf.multi_cell(0,7,_latin(t)); pdf.ln(1)
    def p(t, sz=12): pdf.set_font("Helvetica","",sz); pdf.multi_cell(0,6,_latin(t))
    for line in md_text.splitlines():
        if line.startswith("# "): h1(line[2:])
        elif line.startswith("## "): h2(line[3:])
        elif line.startswith("### "): pdf.set_font("Helvetica","B",12); pdf.multi_cell(0,6,_latin(line[4:]))
        elif line.startswith("- "): pdf.set_font("Helvetica","",12); pdf.multi_cell(0,6,_latin(line))
        elif line.strip()=="": pdf.ln(1)
        else: p(line)
    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1","ignore")

# ─────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────
def page_landing():
    progress(0)
    st.markdown("# 🛡️ SME Cybersecurity Self-Assessment")
    st.markdown("<div class='lead'>Assess · Understand · Act — in under 15 minutes.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write("• 🗣️ Plain-language questions")
        st.write("• 📚 Traceable to NIST/ISO")
    with c2:
        st.write("• ⏱️ 10–15 minutes")
        st.write("• 🧪 Safe demos of common scams")
    if st.button("Start ➜", type="primary"):
        st.session_state.page="Step 1"

def page_step1():
    progress(1, label="Business basics")
    st.markdown("## 🧭 Tell us about the business")
    st.session_state["company_name"] = st.text_input("Business name *", value=st.session_state.get("company_name",""))
    st.session_state["business_region"] = st.selectbox("🌍 Business location / region *", ["EU / EEA","UK","United States","Other / Multi-region"], index=0)
    st.session_state["industry"] = st.selectbox("🏷️ Industry / service *", [
        "Retail & Hospitality","Professional / Consulting / Legal / Accounting","Manufacturing / Logistics",
        "Creative / Marketing / IT Services","Health / Wellness / Education","Public sector / Non-profit","Other"
    ], index=0)
    st.session_state["derived_size"] = st.selectbox("Derived size (for demo)", ["Micro","Small","Medium"], index=1)
    if st.button("Continue ➜", type="primary"):
        st.session_state.page="Step 2"

def page_step2():
    progress(2, label="Current practices & setup")
    st.markdown("## 🧪 Your current practices & setup")
    # Quick checks
    radio_emoji("🗂️ Do you keep a device list (asset inventory)?", key="bp_inventory")
    radio_emoji("🔐 Do you handle sensitive customer or financial data?", key="bp_sensitive")
    # Digital footprint
    st.radio("🕸️ Do you have a public website?", ["Yes","No"], key="df_website", horizontal=True)
    radio_emoji("🔒 Is your website HTTPS (padlock)?", key="df_https")
    radio_emoji("✉️ Do you use business email addresses?", key="df_email")
    # BYOD
    radio_emoji("📱 Do people use personal devices for work (BYOD)?", key="bp_byod")
    if st.button("Continue ➜", type="primary"):
        st.session_state.page="Summary"

def area_rag():
    inv=(st.session_state.get("bp_inventory","")).lower()
    sys=("🟢 Good","green") if inv=="yes" else ("🟡 Partial","amber") if inv=="partially" else ("🔴 At risk","red") if inv in {"no","not sure"} else ("⚪ Unknown","")
    byod=(st.session_state.get("bp_byod","")).lower(); email=(st.session_state.get("df_email","")).lower()
    if byod=="no" and email=="yes": ppl=("🟢 Safe","green")
    elif email=="no": ppl=("🔴 At risk","red")
    elif byod in {"yes","sometimes"} or email=="partially": ppl=("🟡 Mixed","amber")
    else: ppl=("⚪ Unknown","")
    web=(st.session_state.get("df_website","")).lower(); https=(st.session_state.get("df_https","")).lower()
    if web=="yes" and https=="yes": net=("🟢 Protected","green")
    elif web=="yes" and https=="no": net=("🔴 Exposed","red")
    elif web=="yes" and https=="not sure": net=("🟡 Check","amber")
    elif web=="no": net=("🟢 Low","green")
    else: net=("⚪ Unknown","")
    return sys,ppl,net

def page_summary():
    progress(3, label="Initial assessment summary")
    st.markdown("## 📊 Initial Assessment Summary")
    sys,ppl,net = area_rag()
    st.markdown(f"<span class='chip {sys[1]}'>🖥️ Systems · {sys[0]}</span>"
                f"<span class='chip {ppl[1]}'>👥 People · {ppl[0]}</span>"
                f"<span class='chip {net[1]}'>🌐 Exposure · {net[0]}</span>", unsafe_allow_html=True)
    hints=[]
    if st.session_state.get("bp_inventory") not in ("Yes","Partially"): hints.append("📝 Add/finish your device list.")
    if st.session_state.get("df_website")=='Yes' and st.session_state.get("df_https")!='Yes': hints.append("🔒 Enable HTTPS for your website.")
    if st.session_state.get("bp_byod") in ("Yes","Sometimes"): hints.append("📱 Set simple BYOD + MFA rules.")
    if hints: st.caption(" · ".join(hints))
    if st.button("Continue to detailed assessment ➜", type="primary"):
        st.session_state.page="Detailed"

def page_detailed():
    st.markdown("## 🧩 Detailed Assessment")
    # derive tags
    state = {
        "derived_size": st.session_state.get("derived_size","Small"),
        "industry_tag": st.session_state.get("industry","other"),
        "region_tag": "eu",
        "primary_work_env": st.session_state.get("primary_work_env","Cloud apps"),
        "data_types": st.session_state.get("data_types",[]),
        "bp_card_payments": st.session_state.get("bp_card_payments","No"),
    }
    tags = compute_tags(state)
    active_ids = set(pick_active_sections(tags)) or set(s["title"] for s in SECTIONS)
    st.session_state["detailed_scores"] = {}
    for sec in SECTIONS:
        if sec["title"] not in active_ids: continue
        with st.expander(sec["title"], expanded=True):
            answers=[]; weights=[]
            for q in sec["questions"]:
                radio_emoji(q["text"], key=q["id"])
                answers.append(st.session_state.get(q["id"], "Partially"))
                weights.append(q.get("weight",1.0))
            st.session_state["detailed_scores"][sec["title"]] = section_score(answers, weights)
    if st.button("Finish & see action plan ➜", type="primary"):
        st.session_state.page="Report"

def page_report():
    st.markdown("## 🗺️ Action Plan & Section Status")
    scores = st.session_state.get("detailed_scores", {})
    # display section cards
    cols = st.columns(min(len(scores) or 1, 4))
    for i,(sid, sc) in enumerate(scores.items()):
        emoji,label,klass = section_light(sc)
        with cols[i % len(cols)]:
            st.markdown(f"<div class='card'><b>{sid}</b><div class='hint'>Status: "
                        f"<span class='pill {klass}'>{emoji} {label}</span></div></div>", unsafe_allow_html=True)
    # plan
    baseline_state = {
        "df_website": st.session_state.get("df_website"),
        "df_https": st.session_state.get("df_https"),
        "df_email": st.session_state.get("df_email"),
        "bp_inventory": st.session_state.get("bp_inventory"),
        "bp_byod": st.session_state.get("bp_byod"),
    }
    state_for_tags = {
        "company_name": st.session_state.get("company_name","—"),
        "business_region": st.session_state.get("business_region","—"),
        "industry": st.session_state.get("industry","—"),
        "derived_size": st.session_state.get("derived_size","Small"),
        "industry_tag": st.session_state.get("industry","other"),
        "region_tag": "eu",
        "primary_work_env": st.session_state.get("primary_work_env","Cloud apps"),
        "data_types": st.session_state.get("data_types",[]),
        "bp_card_payments": st.session_state.get("bp_card_payments","No"),
        **baseline_state
    }
    tags = compute_tags(state_for_tags)
    plan = build_plan(scores, tags, state_for_tags)
    st.subheader("⚡ Quick wins"); [st.markdown(f"- {x}") for x in plan["quick"]]
    st.subheader("🧱 Foundations"); [st.markdown(f"- {x}") for x in plan["foundations"]]
    st.subheader("🚀 Next-level / compliance"); [st.markdown(f"- {x}") for x in plan["nextlvl"]]
    md = build_markdown_report(state_for_tags, plan, scores)
    st.download_button("📄 Download summary (Markdown)", data=md.encode("utf-8"), file_name="cyber-assessment.md")
    pdf = build_pdf_from_markdown(md)
    if pdf:
        st.download_button("📘 Download summary (PDF)", data=pdf, file_name="cyber-assessment.pdf", mime="application/pdf")
    else:
        st.caption("PDF engine not available — using Markdown export.")

def page_phish():
    st.markdown("## 🎣 Phish-Preview Simulation")
    ids = [s["id"] for s in PHISH_SCENARIOS]
    sid = st.selectbox("Choose scenario", ids)
    s = next(x for x in PHISH_SCENARIOS if x["id"]==sid)
    st.markdown(f"**Subject:** {s['subject']}")
    st.markdown(f"**From:** {s['sender_display']} <{s['sender_email']}>")
    st.write("\n".join(s["body"]))
    st.button("Open (disabled)", disabled=True)
    options = [f["label"] for f in (s["flags"] + s.get("distractors",[]))]
    picks = st.multiselect("What looks suspicious? (select all that apply)", options)
    true_flags = {f["label"] for f in s["flags"]}
    correct = [p for p in picks if p in true_flags]
    distract = [p for p in picks if p not in true_flags]
    if picks:
        if correct: st.success("Good catch! " + ", ".join(correct))
        if distract: st.info("Note: logos/signatures can be faked. Focus on domain, urgency, request type.")
    else:
        st.caption("Hint: check the sender domain and any urgent requests.")

# ─────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────
NAV = {
    "🏁 Landing": page_landing,
    "🧭 Step 1": page_step1,
    "🔎 Step 2": page_step2,
    "📊 Summary": page_summary,
    "🧩 Detailed": page_detailed,
    "🗺️ Report": page_report,
    "🎣 Phish Demo": page_phish,
}
choice = st.sidebar.radio("Navigate", list(NAV.keys()), index=list(NAV.keys()).index(st.session_state.get("page","🏁 Landing")))
NAV[choice]()
st.session_state["page"] = choice
