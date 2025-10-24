"""
SME Self-Assessment Wizard — Scenario Edition
- Stage 1: Intake + Initial Assessment (context)
- Stage 2: Micro-simulations (choose actions & cues; confidence)
- Results: Domain traffic-lights, strengths, fixes, and export

Run:
  pip install streamlit pandas
  streamlit run app.py
"""

from io import StringIO
import json
from typing import Dict, Any, List, Tuple

import pandas as pd
import streamlit as st

# =========================================================
# Page & Styles
# =========================================================
st.set_page_config(page_title="SME Assessment Wizard", page_icon="🧭", layout="wide")

CSS = """
<style>
.card{border:1px solid #eaeaea;border-radius:14px;padding:16px;background:#fff}
.qtitle{font-size:1.1rem;font-weight:600;margin:0 0 6px 0}
.small{font-size:.9rem;color:#666}
.badge{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:600}
.red{background:#ffe7e7;border:1px solid #ffd0d0;color:#b10000}
.amber{background:#fff3cd;border:1px solid #ffe59a;color:#7a5b00}
.green{background:#e6f7e6;border:1px solid #c9efc9;color:#0d6b0d}
.kpi{border-radius:12px;border:1px solid #eee;padding:14px;background:#fafafa}
.kpi h4{margin:.1rem 0 .4rem 0}
ul.tight>li{margin-bottom:.3rem}
.evidence{background:#fafafa;border:1px dashed #e3e3e3;border-radius:10px;padding:10px;margin:6px 0}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================================================
# Session init
# =========================================================
def ss_init() -> None:
    if "stage" not in st.session_state:
        # intake -> qa -> done_initial -> sim_qa -> sim_results
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
    if "answers" not in st.session_state:  # stage 1 answers
        st.session_state.answers: Dict[str, Any] = {}
    if "idx" not in st.session_state:
        st.session_state.idx = 0
    if "sim_idx" not in st.session_state:
        st.session_state.sim_idx = 0
    if "sim_answers" not in st.session_state:  # scenario responses
        st.session_state.sim_answers: Dict[str, Any] = {}

def reset_all() -> None:
    for k in ["stage","profile","answers","idx","sim_idx","sim_answers"]:
        if k in st.session_state: del st.session_state[k]
    ss_init()

ss_init()

# =========================================================
# Stage 1 — Initial Context Questions
# =========================================================
QUESTIONS: List[Dict[str, Any]] = [
    # Digital Footprint
    {
        "id": "sell_online",
        "phase": "Digital Footprint",
        "text": "Do you sell products or deliver services online?",
        "type": "choice",
        "choices": ["Yes – on my own website","Yes – via marketplaces (Amazon/Etsy)","No – mostly offline"],
        "tip": "Helps estimate online exposure and dependencies."
    },
    {
        "id": "data_types",
        "phase": "Digital Footprint",
        "text": "Do you store customer or employee information (e.g., emails, invoices, payment info)?",
        "type": "choice",
        "choices": ["Yes","No"],
        "tip": "Personal data handling increases duty of care and regulatory exposure."
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
        "tip": "Locates critical processes and information."
    },
    # IT Ownership
    {"id":"website_owner","phase":"IT Ownership","text":"Who looks after your website and online systems?","type":"choice",
     "choices":["I do it myself","Someone on my team","An external company or freelancer"]},
    {"id":"it_support","phase":"IT Ownership","text":"Who takes care of computers, email and systems when something needs setup/fixing?","type":"choice",
     "choices":["I do","A friend/freelancer","An IT company","In-house IT team"]},
    {"id":"setup_by","phase":"IT Ownership","text":"Did you personally set up your main systems (email, website, backups)?","type":"choice",
     "choices":["Yes, mostly me","Shared effort","Someone else handled it"]},
    {"id":"asset_list","phase":"IT Ownership","text":"Do you have a clear list of systems, accounts and devices you use?","type":"choice",
     "choices":["Yes, documented","Rough idea","Not really"]},
    # Partners
    {"id":"third_parties","phase":"Partners","text":"Do external partners handle your data/systems (host, accountant, logistics, marketing tools)?","type":"choice","choices":["Yes","No"]},
    {"id":"partner_count","phase":"Partners","text":"How many key partners do you rely on?","type":"choice","choices":["0–2","3–5","6+"]},
    {"id":"breach_contact","phase":"Partners","text":"If a main partner had a breach, would you know who to contact and what to do?","type":"choice","choices":["Yes – I know who to reach","Not really sure"]},
    # Confidence
    {"id":"confidence","phase":"Confidence","text":"How prepared would you feel if a cyberattack or data loss hit tomorrow?","type":"choice",
     "choices":["Not at all","Somewhat","Fairly confident","Very confident"]},
    {"id":"past_incidents","phase":"Confidence","text":"Have you experienced a cybersecurity issue before (e.g., phishing, data loss, locked computer)?","type":"choice",
     "choices":["Yes","No","Not sure"]},
    {"id":"know_who_to_call","phase":"Confidence","text":"Do you know who to call or where to get help if something happened?","type":"choice","choices":["Yes","No"]},
]
TOTAL = len(QUESTIONS)

def digital_dependency_score(ans: Dict[str, Any]) -> int:
    s = 0
    if ans.get("sell_online","").startswith("Yes"): s += 2
    if ans.get("data_types") == "Yes": s += 1
    s += min(len(ans.get("tools_regular", [])), 4)
    return s

def dd_text(v:int) -> str:
    return "Low" if v <= 2 else ("Medium" if v <= 5 else "High")

# =========================================================
# Stage 2 — Scenarios (micro-simulations)
# =========================================================
# Each option has text, tag, and weight (risk/benefit). max_select limits choices.
SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "s1_invoice",
        "title": "Supplier invoice change",
        "narrative": "A supplier emails to 'update their bank details' for an unpaid invoice. There's a 'View invoice' button.",
        "evidence": [
            "Reply-To: acme-billing@acme-supplies.co (display name: Acme Supplies)",
            "Link preview: acme-support-billing.com/invoices/...",
            "Tone: polite, a little urgent; mentions late fees"
        ],
        "tasks": {
            "cues": {
                "prompt": "Which details make you pause? (pick up to 3)",
                "options": [
                    {"text":"New bank details + urgency","tag":"cue_new_iban","weight":2},
                    {"text":"Reply-To differs from display name","tag":"cue_replyto","weight":2},
                    {"text":"Link domain not the usual portal","tag":"cue_domain","weight":2},
                    {"text":"Looks fine to me","tag":"cue_none","weight":-2},
                ],
                "max_select": 3
            },
            "actions": {
                "prompt": "What would you do first? (pick up to 2)",
                "options": [
                    {"text":"Call supplier via number in finance contacts","tag":"oob_verify","weight":3},
                    {"text":"Reply to the email to confirm","tag":"reply_email","weight":-2},
                    {"text":"Ask finance to cross-check IBAN in ERP","tag":"crosscheck_iban","weight":2},
                    {"text":"Click the button and log in to verify","tag":"click_link","weight":-3},
                    {"text":"Hold the payment and open a ticket","tag":"hold_and_ticket","weight":2},
                ],
                "max_select": 2
            },
            "confidence": {"prompt":"How confident are you?", "range":[0,100], "default":60}
        },
        "domain_map": {"Email & Awareness":0.5,"Response & Continuity":0.5},
        "hint_fix": "Maintain a verified supplier contact list and require two-channel verification for bank detail changes."
    },
    {
        "id": "s2_ceo",
        "title": "CEO urgent payment request",
        "narrative": "A late-evening message from a senior exec asks you to make a confidential, urgent transfer and to bypass the usual approvals.",
        "evidence": [
            "Sent from: gmail.com address; signature looks copied",
            "‘Handle personally’ and ‘urgent’ language",
            "Mentions a supplier you recognise"
        ],
        "tasks": {
            "cues": {
                "prompt":"What looks off? (pick up to 3)",
                "options":[
                    {"text":"Non-corporate sender address","tag":"cue_sender","weight":2},
                    {"text":"Bypass normal approvals","tag":"cue_bypass","weight":2},
                    {"text":"Unusual time and secrecy","tag":"cue_timesecrecy","weight":2},
                    {"text":"Nothing stands out","tag":"cue_none","weight":-2},
                ],
                "max_select":3
            },
            "actions":{
                "prompt":"What do you do? (pick up to 2)",
                "options":[
                    {"text":"Verify via known company channel","tag":"oob_verify","weight":3},
                    {"text":"Proceed due to authority","tag":"comply_authority","weight":-3},
                    {"text":"Log the event and notify finance lead","tag":"log_and_notify","weight":2},
                    {"text":"Ask for details by replying to the same email","tag":"reply_email","weight":-2},
                ],
                "max_select":2
            },
            "confidence":{"prompt":"How confident are you?", "range":[0,100], "default":65}
        },
        "domain_map":{"Governance":0.3,"Response & Continuity":0.7},
        "hint_fix":"Document payment approvals; never bypass without two approvers and an out-of-band check."
    },
    {
        "id": "s3_reset",
        "title": "Password-reset alert",
        "narrative": "You receive a ‘reset your password’ alert after ‘unusual sign-in activity’.",
        "evidence": [
            "Shortened URL; padlock icon; generic greeting",
            "Domain looks close to your vendor but isn’t exact"
        ],
        "tasks":{
            "cues":{
                "prompt":"Spot the cues (pick up to 3)",
                "options":[
                    {"text":"Shortened or mismatched URL","tag":"cue_url","weight":2},
                    {"text":"Generic greeting / odd branding","tag":"cue_generic","weight":2},
                    {"text":"Time pressure to click","tag":"cue_pressure","weight":2},
                    {"text":"Looks legit","tag":"cue_none","weight":-2},
                ],
                "max_select":3
            },
            "actions":{
                "prompt":"What’s your move? (pick up to 2)",
                "options":[
                    {"text":"Navigate to the site yourself (no link)","tag":"nav_direct","weight":3},
                    {"text":"Use the report-phish button","tag":"report_button","weight":2},
                    {"text":"Click the link and log in to check","tag":"click_link","weight":-3},
                    {"text":"Reply asking if this is real","tag":"reply_email","weight":-2},
                ],
                "max_select":2
            },
            "confidence":{"prompt":"How confident are you?", "range":[0,100], "default":70}
        },
        "domain_map":{"Access & Accounts":0.5,"Email & Awareness":0.5},
        "hint_fix":"Teach ‘navigate, don’t click’; enable an easy report button."
    },
    {
        "id": "s4_laptop",
        "title": "Laptop lost on the train",
        "narrative": "A staff laptop is left on a train during a business trip.",
        "evidence": [
            "The device holds email and synced files",
            "Unsure whether disk encryption is on"
        ],
        "tasks":{
            "cues":{
                "prompt":"What matters most here? (pick up to 2)",
                "options":[
                    {"text":"Data may be accessible if not encrypted","tag":"cue_encrypt","weight":2},
                    {"text":"Tokens/sessions may still be valid","tag":"cue_tokens","weight":2},
                    {"text":"We can probably ignore if it’s passworded","tag":"cue_ignore","weight":-2},
                ],
                "max_select":2
            },
            "actions":{
                "prompt":"What do you do first? (pick up to 2)",
                "options":[
                    {"text":"Trigger remote wipe / lock","tag":"remote_wipe","weight":3},
                    {"text":"Revoke tokens & reset credentials","tag":"revoke_tokens","weight":2},
                    {"text":"Wait a week to see if it turns up","tag":"wait_and_see","weight":-3},
                    {"text":"Log the incident and notify insurer","tag":"log_and_notify","weight":2},
                ],
                "max_select":2
            },
            "confidence":{"prompt":"How confident are you?", "range":[0,100], "default":60}
        },
        "domain_map":{"Devices":0.6,"Response & Continuity":0.4},
        "hint_fix":"Enforce full-disk encryption and keep MDM ready for remote lock/wipe."
    },
    {
        "id":"s5_share",
        "title":"Cloud sharing mishap",
        "narrative":"A public link to a cloud folder with recent invoices was shared with a client by mistake.",
        "evidence":[
            "Link has no expiry; folder contains customer details",
            "Default sharing allows ‘Anyone with the link’"
        ],
        "tasks":{
            "cues":{
                "prompt":"What’s risky here? (pick up to 3)",
                "options":[
                    {"text":"Public link and no expiry","tag":"cue_public","weight":2},
                    {"text":"Sensitive data present","tag":"cue_sensitive","weight":2},
                    {"text":"Default ‘Anyone’ sharing","tag":"cue_default","weight":2},
                    {"text":"No obvious risk","tag":"cue_none","weight":-2},
                ],
                "max_select":3
            },
            "actions":{
                "prompt":"What would you do now? (pick up to 2)",
                "options":[
                    {"text":"Remove public access / rotate link","tag":"remove_public","weight":3},
                    {"text":"Notify affected team and document","tag":"log_and_notify","weight":2},
                    {"text":"Leave as is but monitor","tag":"do_nothing","weight":-3},
                    {"text":"Review sharing defaults for the workspace","tag":"review_defaults","weight":2},
                ],
                "max_select":2
            },
            "confidence":{"prompt":"How confident are you?", "range":[0,100], "default":65}
        },
        "domain_map":{"Data & Backups":0.6,"Governance":0.4},
        "hint_fix":"Set workspace sharing defaults; require expiry and least-privilege links."
    },
]
SIM_TOTAL = len(SCENARIOS)

DOMAINS = ["Access & Accounts","Devices","Data & Backups","Email & Awareness","Response & Continuity","Governance"]

# ---------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------
def traffic_light(pct: float) -> Tuple[str, str]:
    if pct >= 75: return ("green","Good")
    if pct >= 40: return ("amber","Needs work")
    return ("red","At risk")

def score_selection(options: List[Dict[str,Any]], selected: List[str], max_select: int) -> float:
    """Normalize to 0–100 by best possible positive picks."""
    # score actual
    score = 0
    for s in selected:
        for opt in options:
            if opt["text"] == s:
                score += opt["weight"]
                break
    # compute best possible
    positives = sorted([max(0, opt["weight"]) for opt in options], reverse=True)
    max_pos = sum(positives[:max_select]) if positives else 0
    if max_pos <= 0:  # avoid div-by-zero; if all <=0 treat as 100 if no risky choices selected
        return 100.0 if score >= 0 else 0.0
    norm = max(0.0, score) / max_pos * 100.0
    return max(0.0, min(100.0, norm))

def evaluate_scenario(scn: Dict[str,Any], sel_cues: List[str], sel_actions: List[str], confidence: int):
    cues_cfg = scn["tasks"]["cues"]; act_cfg = scn["tasks"]["actions"]
    cues_score = score_selection(cues_cfg["options"], sel_cues, cues_cfg["max_select"])
    act_score  = score_selection(act_cfg["options"],  sel_actions, act_cfg["max_select"])
    base = (cues_score + act_score) / 2.0

    # calibration: confident + wrong slightly penalises Awareness; confident + right slightly boosts
    calib = 0.0
    if base < 40 and confidence >= 70:
        calib = -5.0
    elif base >= 60 and confidence >= 70:
        calib = +5.0

    contrib = {d: base * p for d, p in scn["domain_map"].items()}
    # apply calibration to a reasonable domain if present
    if "Email & Awareness" in contrib:
        contrib["Email & Awareness"] += calib

    # build feedback
    def pick(optlist, selected, good=True):
        return [o["text"] for o in optlist if (o["text"] in selected and (o["weight"] > 0) == good)]
    good_actions  = pick(act_cfg["options"], sel_actions, good=True)
    risky_actions = pick(act_cfg["options"], sel_actions, good=False)
    # missed top cues
    pos_cues = [o for o in cues_cfg["options"] if o["weight"] > 0]
    missed = [o["text"] for o in pos_cues if o["text"] not in sel_cues][:2]

    # selected tags for later strengths/fixes
    sel_tags = []
    for txt in sel_actions:
        for o in act_cfg["options"]:
            if o["text"] == txt:
                sel_tags.append(o["tag"])
    return {
        "cues_score": round(cues_score,1),
        "actions_score": round(act_score,1),
        "base": round(base,1),
        "contrib": contrib,
        "good_actions": good_actions,
        "risky_actions": risky_actions,
        "missed_cues": missed,
        "hint_fix": scn.get("hint_fix",""),
        "selected_tags": sel_tags
    }

def compute_domain_scores_from_sims(sim_answers: Dict[str,Any]) -> Dict[str, Dict[str, Any]]:
    # domain_max is sum of 100*proportion per scenario answered
    domain_max: Dict[str,float] = {}
    domain_sum: Dict[str,float] = {d:0.0 for d in DOMAINS}

    for scn in SCENARIOS:
        # get selections; if unanswered, skip (max still counts to keep scale consistent? We'll only count answered)
        resp = sim_answers.get(scn["id"])
        # always count max so finished subset compares consistently across respondents
        for d,p in scn["domain_map"].items():
            domain_max[d] = domain_max.get(d,0.0) + 100.0 * p

        if not resp:  # unanswered scenario: contributes zero
            continue
        ev = evaluate_scenario(scn, resp["cues"], resp["actions"], resp["confidence"])
        for d, val in ev["contrib"].items():
            domain_sum[d] = domain_sum.get(d,0.0) + max(0.0, val)

    # generate traffic lights 0–100 per domain
    results: Dict[str, Dict[str, Any]] = {}
    for d in DOMAINS:
        maxv = domain_max.get(d, 0.0)
        pct = (domain_sum[d] / maxv * 100.0) if maxv > 0 else 0.0
        colour, label = traffic_light(pct)
        results[d] = {"score": round(pct), "colour": colour, "label": label}
    return results

def overall_score(domain_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    vals = [v["score"] for v in domain_scores.values() if v["score"] is not None]
    if not vals:
        return {"score":0,"colour":"red","label":"At risk"}
    avg = sum(vals)/len(vals)
    colour, label = traffic_light(avg)
    return {"score": round(avg), "colour": colour, "label": label}

# Strengths / Fixes from selected action tags
def strengths_and_fixes(sim_answers: Dict[str,Any]) -> Tuple[List[str], List[str]]:
    strengths, fixes = set(), set()
    for scn in SCENARIOS:
        resp = sim_answers.get(scn["id"])
        if not resp: continue
        tags = []
        for t in scn["tasks"]["actions"]["options"]:
            if t["text"] in resp["actions"]:
                tags.append(t["tag"])

        # Strengths
        if "oob_verify" in tags:
            strengths.add("Uses out-of-band verification before money/account changes.")
        if "hold_and_ticket" in tags or "log_and_notify" in tags:
            strengths.add("Logs incidents and involves the right team quickly.")
        if "nav_direct" in tags or "report_button" in tags:
            strengths.add("Avoids risky links and uses the report-phish route.")
        if "remote_wipe" in tags or "revoke_tokens" in tags:
            strengths.add("Can contain device loss (remote wipe / token revocation).")
        if "remove_public" in tags or "review_defaults" in tags:
            strengths.add("Manages cloud sharing (remove public access, sensible defaults).")

        # Fixes (risky or missing good practice)
        risky_map = {
            "click_link":"Don’t verify via links in alerts; navigate directly.",
            "reply_email":"Don’t confirm via the same thread; attackers control replies.",
            "comply_authority":"Don’t bypass approvals due to urgency/authority.",
            "wait_and_see":"Act immediately on lost devices (lock/wipe, revoke).",
            "do_nothing":"Remove public access; rotate links and review defaults."
        }
        for t in tags:
            if t in risky_map: fixes.add(risky_map[t])
        if "oob_verify" not in tags and scn["id"] in ("s1_invoice","s2_ceo"):
            fixes.add("Introduce two-channel verification for payments and account changes.")
        if scn["id"] == "s4_laptop" and not ({"remote_wipe","revoke_tokens"} & set(tags)):
            fixes.add("Ensure MDM can remote-lock/wipe and revoke sessions quickly.")
        if scn["id"] == "s3_reset" and not ({"nav_direct","report_button"} & set(tags)):
            fixes.add("Enable an easy ‘report phishing’ button and teach ‘navigate, don’t click’.")
        if scn["id"] == "s5_share" and "remove_public" not in tags:
            fixes.add("Require expiring, least-privilege cloud links; disable ‘Anyone with link’.")
    return sorted(list(strengths))[:8], sorted(list(fixes))[:10]

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
        f"**Work mode:** {p.get('work_mode') or '—'}"
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
# Stage 1: Initial Assessment (one per page)
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
            st.session_state.idx = max(idx - 1, 0); st.rerun()
    with col_skip:
        if st.button("Skip", use_container_width=True):
            next_idx = idx + 1
            if next_idx >= TOTAL: st.session_state.stage = "done_initial"
            else: st.session_state.idx = next_idx
            st.rerun()
    with col_next:
        if st.button("Save & Next →", type="primary", use_container_width=True):
            next_idx = idx + 1
            if next_idx >= TOTAL: st.session_state.stage = "done_initial"
            else: st.session_state.idx = next_idx
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
        for h in highlights: st.markdown(f"- {h}")

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
        for b in blindspots: st.markdown(f"- {b}")

    st.info("Next: short, safe simulations that test instincts and controls.")
    if st.button("→ Continue to Simulations", type="primary"):
        st.session_state.stage = "sim_qa"
        st.session_state.sim_idx = 0
        st.rerun()

# =========================================================
# Stage 2: Simulation Wizard
# =========================================================
def render_scenario(i: int):
    scn = SCENARIOS[i]
    st.progress(i / max(SIM_TOTAL,1), text=f"Simulation • {scn['title']} • {i+1}/{SIM_TOTAL}")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(scn["title"])
    st.write(scn["narrative"])
    if scn.get("evidence"):
        st.markdown('<div class="evidence">', unsafe_allow_html=True)
        for e in scn["evidence"]:
            st.markdown(f"- {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # selections (persist with unique keys)
    cues_cfg, act_cfg = scn["tasks"]["cues"], scn["tasks"]["actions"]
    sel_cues = st.multiselect(cues_cfg["prompt"], [o["text"] for o in cues_cfg["options"]],
                              default=st.session_state.sim_answers.get(scn["id"],{}).get("cues", []),
                              max_selections=cues_cfg["max_select"], key=f"cues_{scn['id']}")
    sel_actions = st.multiselect(act_cfg["prompt"], [o["text"] for o in act_cfg["options"]],
                                 default=st.session_state.sim_answers.get(scn["id"],{}).get("actions", []),
                                 max_selections=act_cfg["max_select"], key=f"actions_{scn['id']}")
    conf_rng = scn["tasks"]["confidence"]["range"]
    conf_default = scn["tasks"]["confidence"]["default"]
    confidence = st.slider(scn["tasks"]["confidence"]["prompt"], conf_rng[0], conf_rng[1],
                           value=st.session_state.sim_answers.get(scn["id"],{}).get("confidence", conf_default),
                           key=f"conf_{scn['id']}")

    # live feedback
    ev = evaluate_scenario(scn, sel_cues, sel_actions, confidence)
    with st.expander("Debrief (preview)"):
        st.markdown(f"**Scores:** cues {ev['cues_score']} • actions {ev['actions_score']} • combined {ev['base']}")
        if ev["good_actions"]:
            st.markdown("**Good moves**")
            st.markdown("<ul class='tight'>" + "".join([f"<li>{g}</li>" for g in ev["good_actions"]]) + "</ul>", unsafe_allow_html=True)
        if ev["risky_actions"]:
            st.markdown("**Risky choices**")
            st.markdown("<ul class='tight'>" + "".join([f"<li>{g}</li>" for g in ev["risky_actions"]]) + "</ul>", unsafe_allow_html=True)
        if ev["missed_cues"]:
            st.markdown(f"**Cues you may have missed:** {', '.join(ev['missed_cues'])}")
        if scn.get("hint_fix"): st.caption("Hint: " + scn["hint_fix"])

    st.markdown('</div>', unsafe_allow_html=True)
    return scn, sel_cues, sel_actions, confidence

if st.session_state.stage == "sim_qa":
    i = st.session_state.sim_idx
    scn, sel_cues, sel_actions, confidence = render_scenario(i)

    col_prev, col_skip, col_next = st.columns([1,1,1])
    with col_prev:
        if st.button("← Back", use_container_width=True, disabled=(i == 0)):
            st.session_state.sim_idx = max(i - 1, 0); st.rerun()
    with col_skip:
        if st.button("Skip", use_container_width=True):
            st.session_state.sim_answers.pop(scn["id"], None)
            nxt = i + 1
            if nxt >= SIM_TOTAL: st.session_state.stage = "sim_results"
            else: st.session_state.sim_idx = nxt
            st.rerun()
    with col_next:
        if st.button("Save & Next →", type="primary", use_container_width=True):
            st.session_state.sim_answers[scn["id"]] = {
                "cues": sel_cues,
                "actions": sel_actions,
                "confidence": confidence
            }
            nxt = i + 1
            if nxt >= SIM_TOTAL: st.session_state.stage = "sim_results"
            else: st.session_state.sim_idx = nxt
            st.rerun()

# =========================================================
# Results — Traffic Lights + Behaviour + Export
# =========================================================
def badge(colour: str, text: str) -> str:
    return f'<span class="badge {colour}">{text}</span>'

if st.session_state.stage == "sim_results":
    st.success("Simulations complete.")
    scores = compute_domain_scores_from_sims(st.session_state.sim_answers)
    overall = overall_score(scores)
    strengths, fixes = strengths_and_fixes(st.session_state.sim_answers)

    # Overall KPI
    st.markdown('<div class="kpi">', unsafe_allow_html=True)
    st.markdown(
        f"#### Overall posture: {badge(overall['colour'], overall['label'])}  •  **{overall['score']}%**",
        unsafe_allow_html=True
    )
    st.caption("Scores reflect choices in scenarios and are intended to guide priorities, not replace audits.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Domain KPIs
    dcols = st.columns(3)
    for idx, dom in enumerate(DOMAINS):
        data = scores.get(dom, {"score":0,"colour":"red","label":"At risk"})
        with dcols[idx % 3]:
            st.markdown('<div class="kpi">', unsafe_allow_html=True)
            st.markdown(f"**{dom}**")
            st.markdown(f"{badge(data['colour'], data['label'])} • **{data['score']}%**", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    colA, colB = st.columns(2)
    with colA:
        st.markdown("### ✅ What you’re doing well")
        if strengths:
            st.markdown("<ul class='tight'>" + "".join([f"<li>{g}</li>" for g in strengths]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("We didn’t detect specific strengths yet — once you apply the fixes below, this list will grow.")
    with colB:
        st.markdown("### 🛠 Top recommended fixes")
        if fixes:
            st.markdown("<ul class='tight'>" + "".join([f"<li>{f}</li>" for f in fixes]) + "</ul>", unsafe_allow_html=True)
        else:
            st.write("Great baseline! Keep processes current and review quarterly.")

    # Export
    st.markdown("---")
    st.info("Download results for your records.")
    export_payload = {
        "profile": st.session_state.profile,
        "initial_answers": st.session_state.answers,
        "sim_answers": st.session_state.sim_answers,
        "domain_scores": scores,
        "overall": overall,
        "strengths": strengths,
        "fixes": fixes
    }
    st.download_button("⬇️ Download JSON", data=json.dumps(export_payload, indent=2),
                       file_name="sme_sim_results.json", mime="application/json")

    df = pd.DataFrame([{"Domain": d, "Score": v["score"], "Label": v["label"]} for d, v in scores.items()])
    csv_buf = StringIO(); df.to_csv(csv_buf, index=False)
    st.download_button("⬇️ Download CSV (domain scores)", data=csv_buf.getvalue(),
                       file_name="sme_domain_scores.csv", mime="text/csv")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("← Review scenarios"):
            st.session_state.stage = "sim_qa"; st.session_state.sim_idx = 0; st.rerun()
    with c2:
        if st.button("Restart whole assessment"):
            reset_all(); st.rerun()
