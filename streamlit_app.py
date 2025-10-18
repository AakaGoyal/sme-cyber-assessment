"""
Streamlit SME Cybersecurity Self‑Assessment Tool

How to run locally:
  1) pip install streamlit pandas plotly pyyaml
  2) streamlit run streamlit_app.py

Notes:
  • This is a first cut: domain list, questions, and recommendations are opinionated defaults.
  • Tweak the YAML-like STRUCTURE at the bottom (QUESTIONS & RECOMMENDATIONS) to match your framework.
  • Nothing here stores data externally. All state stays in the Streamlit session unless the user downloads a file.
"""

from __future__ import annotations
import io
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------------
# App Config
# -----------------------------
st.set_page_config(
    page_title="SME Cybersecurity Self‑Assessment",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Data Models
# -----------------------------
MATURITY_LABELS = [
    "0 — Not Implemented",
    "1 — Ad Hoc / Informal",
    "2 — Repeatable (Basic)",
    "3 — Defined / Documented",
    "4 — Managed & Measured",
    "5 — Optimized / Continuous",
]

@dataclass
class Question:
    id: str
    text: str
    weight: float = 1.0  # relative weight inside the domain

@dataclass
class Domain:
    id: str
    name: str
    framework_map: str  # e.g., NIST CSF / ISO27001 linkage
    questions: List[Question]

# -----------------------------
# Domain / Question Bank (edit freely)
# -----------------------------
DOMAINS: List[Domain] = [
    Domain(
        id="governance",
        name="Governance & Risk",
        framework_map="NIST ID.GV / ISO 5,8",
        questions=[
            Question("gov1", "We have defined cybersecurity roles, responsibilities, and policy owners."),
            Question("gov2", "We perform risk assessments at least annually (incl. asset, threat, and control review)."),
            Question("gov3", "We maintain a risk register with owners, treatments, and review dates.", weight=1.2),
        ],
    ),
    Domain(
        id="asset",
        name="Asset Management",
        framework_map="NIST ID.AM / ISO 8",
        questions=[
            Question("am1", "We maintain an up‑to‑date inventory of hardware assets (incl. ownership & criticality)."),
            Question("am2", "We maintain an up‑to‑date inventory of software/SaaS with license and data classification."),
            Question("am3", "Shadow IT is monitored and onboarded or blocked via a defined process.", weight=1.1),
        ],
    ),
    Domain(
        id="access",
        name="Identity & Access Management",
        framework_map="NIST PR.AC / ISO 5,8",
        questions=[
            Question("ac1", "MFA is enforced for admin and remote access; strong auth for all SaaS where feasible.", weight=1.2),
            Question("ac2", "Joiner‑Mover‑Leaver process is defined and automated (JML)."),
            Question("ac3", "Privileged access is time‑bound and reviewed regularly (PAM/least privilege)."),
        ],
    ),
    Domain(
        id="vuln",
        name="Vulnerability & Patch Mgmt",
        framework_map="NIST PR.IP / ISO 8",
        questions=[
            Question("vm1", "Automated vulnerability scanning covers servers, endpoints, and key apps."),
            Question("vm2", "Critical patches are deployed within business‑defined SLAs (e.g., 7/14/30 days).", weight=1.2),
            Question("vm3", "We track remediation to closure and report aging/exceptions to leadership."),
        ],
    ),
    Domain(
        id="ir",
        name="Incident Response",
        framework_map="NIST RS / ISO 6,16",
        questions=[
            Question("ir1", "There is a documented, tested incident response plan with roles and contacts."),
            Question("ir2", "We have 24×7 detection/alerting for high‑impact threats (EDR/SIEM/MDR).", weight=1.2),
            Question("ir3", "We conduct post‑incident reviews and feed lessons into improvements."),
        ],
    ),
    Domain(
        id="backup",
        name="Backup & Recovery",
        framework_map="NIST PR.IP / ISO 8,17",
        questions=[
            Question("bu1", "Critical systems and data are backed up per RPO/RTO, with immutable copies."),
            Question("bu2", "We test restores regularly (incl. ransomware scenarios).", weight=1.2),
            Question("bu3", "Backups are segregated (network/identity) and access is least‑privileged."),
        ],
    ),
    Domain(
        id="awareness",
        name="Awareness & Training",
        framework_map="NIST PR.AT / ISO 6,7",
        questions=[
            Question("at1", "All staff receive role‑based security training at least annually."),
            Question("at2", "Phishing simulations and follow‑ups are conducted routinely."),
            Question("at3", "Developers/admins get specialized secure‑coding/ops training."),
        ],
    ),
    Domain(
        id="tprm",
        name="Third‑Party & SaaS Risk",
        framework_map="NIST ID.SC / ISO 15",
        questions=[
            Question("tp1", "Vendors are risk‑assessed before onboarding; DPAs/SCCs are in place."),
            Question("tp2", "Critical vendors are monitored with defined triggers and re‑assessments."),
            Question("tp3", "We maintain a current list of data processors and sub‑processors."),
        ],
    ),
    Domain(
        id="devsec",
        name="Secure Development & Change",
        framework_map="NIST PR.IP / ISO 8,12",
        questions=[
            Question("sd1", "Code is reviewed and scanned (SAST/DAST/SCA) with tracked findings."),
            Question("sd2", "Dependencies and containers are updated via a defined pipeline (SBOM).", weight=1.1),
            Question("sd3", "Changes follow peer review, testing, and approvals (change Mgmt/DevOps)."),
        ],
    ),
    Domain(
        id="logging",
        name="Monitoring & Logging",
        framework_map="NIST DE / ISO 8",
        questions=[
            Question("lg1", "Security‑relevant logs are centralized and retained per policy."),
            Question("lg2", "Use cases and alerts exist for key risks; triage is documented.", weight=1.1),
            Question("lg3", "Clock sync, integrity, and access controls protect log quality."),
        ],
    ),
    Domain(
        id="dataprot",
        name="Data Protection & Privacy",
        framework_map="NIST PR.DS / ISO 5,8; GDPR",
        questions=[
            Question("dp1", "Data is classified; sensitive data is encrypted in transit and at rest."),
            Question("dp2", "Access to personal data is limited and audited (least privilege).", weight=1.1),
            Question("dp3", "Data lifecycle (collection → deletion) is governed and evidenced."),
        ],
    ),
    Domain(
        id="bcp",
        name="Business Continuity",
        framework_map="NIST ID.BE / ISO 17",
        questions=[
            Question("bc1", "BCP exists, with scenario tests that include cyber incidents."),
            Question("bc2", "Critical process owners know RTO/RPO and workarounds."),
            Question("bc3", "BCM roles, communications, and crisis war‑room are defined."),
        ],
    ),
]

# Domain-level recommendation snippets (edit as needed)
RECOMMENDATIONS: Dict[str, List[str]] = {
    "governance": [
        "Define policy owners and review cadence (e.g., semiannual).",
        "Establish a lightweight risk committee with action tracking.",
        "Stand up a living risk register with ownership and due dates.",
    ],
    "asset": [
        "Automate discovery via EDR/MDM/SaaS inventory connectors.",
        "Tag critical assets and assign owners in the CMDB or inventory.",
        "Set a quarterly Shadow‑IT sweep and onboarding playbook.",
    ],
    "access": [
        "Enforce MFA broadly; prioritize admins and remote access first.",
        "Automate JML via HRIS/IdP; run quarterly access reviews.",
        "Introduce PAM for standing privileges with time‑bound elevation.",
    ],
    "vuln": [
        "Roll out scheduled scanning; fix criticals within defined SLAs.",
        "Patch management reporting with aging and exception governance.",
        "Include app and container scans in CI/CD.",
    ],
    "ir": [
        "Document and test IR plan; include contact trees and alt comms.",
        "Add 24×7 detection via MDR or tuned SIEM/EDR.",
        "Run post‑incident reviews with tracked improvements.",
    ],
    "backup": [
        "Adopt immutable backups and periodic restore tests.",
        "Network/identity isolate backup infra; audit access.",
        "Define RTO/RPO per critical system and validate.",
    ],
    "awareness": [
        "Annual role‑based training with targeted modules.",
        "Run phishing simulations with just‑in‑time coaching.",
        "Provide secure‑coding training to devs and admins.",
    ],
    "tprm": [
        "Standardize vendor intake with risk tiers and DPAs/SCCs.",
        "Track critical vendors; set re‑assessment cadence.",
        "Publish and maintain processor/sub‑processor list.",
    ],
    "devsec": [
        "Integrate SAST/DAST/SCA into CI; track findings.",
        "Manage SBOM and dependency hygiene; sign releases.",
        "Peer review + approvals for changes; automate checks.",
    ],
    "logging": [
        "Centralize logs, set retention; monitor ingestion health.",
        "Define/maintain alert use cases with runbooks.",
        "Protect log integrity with access control and time sync.",
    ],
    "dataprot": [
        "Classify data; enforce encrypt‑in‑transit/at‑rest defaults.",
        "Limit and review access to personal/sensitive data.",
        "Define deletion/retention and evidence execution.",
    ],
    "bcp": [
        "Document BCP with cyber scenarios and comms templates.",
        "Set RTO/RPO per process and test workarounds.",
        "Run tabletop exercises and track corrective actions.",
    ],
}

# -----------------------------
# Utility Functions
# -----------------------------
def weighted_average(scores: List[int], weights: List[float]) -> float:
    if not scores:
        return 0.0
    wsum = sum(weights)
    if wsum == 0:
        return 0.0
    return sum(s * w for s, w in zip(scores, weights)) / wsum


def domain_score(domain: Domain, answers: Dict[str, int]) -> float:
    scores, weights = [], []
    for q in domain.questions:
        scores.append(answers.get(q.id, 0))
        weights.append(q.weight)
    return weighted_average(scores, weights)


def maturity_to_risk(score: float) -> float:
    """Convert maturity (0–5) to a simple inverse 'risk' (0–100).
    5.0 -> 0 risk, 0.0 -> 100 risk.
    """
    return max(0.0, min(100.0, (5.0 - score) * 20.0))


def make_markdown_report(company: str, overall: float, dframe: pd.DataFrame, gaps: List[Tuple[str, float]]) -> str:
    lines = [
        f"# SME Cybersecurity Self‑Assessment — {company or 'Unnamed Org'}",
        "",
        f"**Overall maturity:** {overall:.2f} / 5.00",
        "",
        "## Domain Scores",
    ]
    for _, row in dframe.iterrows():
        lines.append(f"- **{row['Domain']}**: {row['Maturity']:.2f}/5  (Risk≈{row['Risk (0–100)']:.0f})")
    if gaps:
        lines.append("\n## Top Gaps (lowest maturity)")
        for name, score in gaps:
            lines.append(f"- {name}: {score:.2f}/5")
    lines.append("\n## Recommendations")
    for _, row in dframe.sort_values("Maturity").iterrows():
        dom_id = row["Domain ID"]
        recs = RECOMMENDATIONS.get(dom_id, [])
        if not recs:
            continue
        lines.append(f"\n### {row['Domain']}")
        for r in recs:
            lines.append(f"- {r}")
    return "\n".join(lines)


# -----------------------------
# Sidebar — Org & Navigation
# -----------------------------
st.sidebar.title("🛡️ SME Cybersecurity Self‑Assessment")
st.sidebar.caption("Lightweight maturity model for SMEs. Map to NIST/ISO at a high level.")

company_name = st.sidebar.text_input("Organization name", placeholder="Acme GmbH")
assessor = st.sidebar.text_input("Your name (optional)")

view = st.sidebar.radio(
    "Navigate",
    ["📋 Assessment", "📊 Results & Recommendations", "ℹ️ About"],
    index=0,
)

# Initialize session state for answers
if "answers" not in st.session_state:
    st.session_state.answers = {}

# -----------------------------
# View: Assessment
# -----------------------------
if view.startswith("📋"):
    st.title("SME Cybersecurity Self‑Assessment")
    st.write(
        "Answer each statement according to your current state. Use the maturity scale from **0 (Not Implemented)** to **5 (Optimized)**."
    )

    for dom in DOMAINS:
        with st.expander(f"{dom.name}  ·  _{dom.framework_map}_", expanded=False):
            for q in dom.questions:
                key = f"ans_{dom.id}_{q.id}"
                default = st.session_state.answers.get(q.id, 0)
                choice = st.select_slider(
                    label=q.text,
                    options=list(range(0, 6)),
                    value=default,
                    help="0=Not Implemented … 5=Optimized",
                    key=key,
                )
                st.session_state.answers[q.id] = choice

    st.success("Responses captured. Switch to **Results & Recommendations** for insights.")

# -----------------------------
# View: Results & Recommendations
# -----------------------------
elif view.startswith("📊"):
    st.title("Results & Recommendations")

    # Build domain scores
    rows = []
    for dom in DOMAINS:
        sc = domain_score(dom, st.session_state.answers)
        risk = maturity_to_risk(sc)
        rows.append({
            "Domain ID": dom.id,
            "Domain": dom.name,
            "Maturity": sc,
            "Risk (0–100)": risk,
            "Framework": dom.framework_map,
        })

    df = pd.DataFrame(rows).sort_values("Domain").reset_index(drop=True)

    overall = df["Maturity"].mean() if not df.empty else 0.0

    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("Overall Maturity")
        st.metric(label="Weighted Average (0–5)", value=f"{overall:.2f}")

        st.subheader("Domain Scores")
        st.dataframe(
            df[["Domain", "Maturity", "Risk (0–100)", "Framework"]]
            .style.format({"Maturity": "{:.2f}", "Risk (0–100)": "{:.0f}"}),
            use_container_width=True,
        )

    with c2:
        st.subheader("Bar Chart — Maturity by Domain")
        fig = px.bar(
            df.sort_values("Maturity"),
            x="Maturity",
            y="Domain",
            orientation="h",
            range_x=[0, 5],
            title="",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Bubble — Inverse Risk (bigger = higher risk)")
        fig2 = px.scatter(
            df,
            x="Maturity",
            y="Domain",
            size="Risk (0–100)",
            hover_name="Domain",
            size_max=40,
            range_x=[0, 5],
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Top gaps
    gaps_df = df.sort_values("Maturity").head(3)
    st.markdown("### Top Gaps")
    if not gaps_df.empty:
        for _, r in gaps_df.iterrows():
            st.write(f"- **{r['Domain']}** — {r['Maturity']:.2f}/5  (Risk≈{r['Risk (0–100)']:.0f})")
    else:
        st.info("No data yet — complete the assessment first.")

    # Recommendations per domain
    st.markdown("### Targeted Recommendations")
    for _, r in df.sort_values("Maturity").iterrows():
        dom_id = r["Domain ID"]
        recs = RECOMMENDATIONS.get(dom_id, [])
        with st.expander(f"{r['Domain']} — suggestions", expanded=False):
            if recs:
                for tip in recs:
                    st.write(f"- {tip}")
            else:
                st.write("No suggestions configured yet (customize RECOMMENDATIONS).")

    # Downloads
    st.markdown("### Export")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV (domain scores)",
        data=csv_bytes,
        file_name=f"{company_name or 'org'}_cyber_assessment_scores.csv",
        mime="text/csv",
    )

    md_report = make_markdown_report(
        company=company_name,
        overall=overall,
        dframe=df,
        gaps=[(row["Domain"], row["Maturity"]) for _, row in gaps_df.iterrows()],
    )
    st.download_button(
        label="⬇️ Download Markdown Report",
        data=md_report.encode("utf-8"),
        file_name=f"{company_name or 'org'}_cyber_assessment_report.md",
        mime="text/markdown",
    )

# -----------------------------
# View: About
# -----------------------------
else:
    st.title("About This Tool")
    st.write(
        """
        This lightweight self‑assessment helps small and mid‑sized organizations gauge their cybersecurity maturity
        across common domains. It loosely maps to **NIST CSF** and **ISO/IEC 27001** control families and emphasizes
        practical next steps over exhaustive audits.

        ### Scoring
        * Each question is rated 0–5. Domain maturity is a weighted average of its questions.
        * Overall maturity is the mean of domain maturities.
        * "Inverse Risk" is a simple complement (lower maturity ⇒ higher risk). Use with judgment.

        ### Customize
        * Edit domain questions and weights in the code.
        * Extend with detailed frameworks, control catalogs, or evidence checklists.
        * Replace the RECOMMENDATIONS with your organization‑specific playbooks.

        ### Disclaimer
        This is not legal advice or a substitute for a formal assessment. Use responsibly.
        """
    )

    st.markdown("— Built with ❤️ using Streamlit, pandas, and Plotly.")
