<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0b1020,45:12355b,100:0f766e&height=230&section=header&text=ControlCombat&fontSize=62&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI%20Agents%20That%20Test%20ISO%2027001%20Controls%20%7C%20Red%20vs%20Blue%20vs%20Judge&descAlignY=60&descSize=18&descColor=d1fae5" width="100%"/>

### *Audits check the paperwork. ControlCombat checks reality.*

**A GRC engineering project: three Claude-powered AI agents attack, defend and judge a company's security and privacy controls, then map every verdict to ISO 27001 and GDPR, with a full audit trail.**

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude_API-Tool_Use-D97757?style=for-the-badge&logo=anthropic&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3D_Views-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Mock_API-009688?style=for-the-badge&logo=fastapi&logoColor=white)

![ISO 27001](https://img.shields.io/badge/ISO_27001-2022_Annex_A-0f766e?style=for-the-badge)
![GDPR](https://img.shields.io/badge/GDPR-Mapped-1d4ed8?style=for-the-badge)
![GRC Engineering](https://img.shields.io/badge/GRC-Engineering-7c3aed?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Hackathon_Prototype-success?style=for-the-badge)

<br/>

> 🚢 *The Titanic was fully compliant. It carried more lifeboats than the law required. It still sank.*
> *Compliance on paper is not safety in practice.*

</div>

---

## ✨ What Is ControlCombat?

Companies prove compliance by showing that a rule is **written down**, usually with screenshots collected once a year. Almost nobody proves the rule is **actually followed**.

ControlCombat closes that gap. AI agents continuously test each control against the company's real systems, argue about the evidence, and produce an auditor-ready verdict.

```
📜 Policy says:   "Every admin account must use MFA."
🗡️ Red agent:     Finds ben@acme.example.com is an admin with MFA off.
🛡️ Blue agent:    Searches for an exception or compensating control. None found. Concedes.
⚖️ Judge agent:   FAIL · ISO 27001 A.8.2, A.8.5 · evidence: identity provider record
📊 Dashboard:     Control turns red, with the evidence, the fix and the full audit trail.
```

![ControlCombat dashboard](screenshot.png)

---

## 🔥 The Problem

| Pain point | Evidence |
|------------|----------|
| 🐢 Manual compliance slows teams down | 83% of organisations report moderate or major delays from manual compliance work ¹ |
| 👤 Evidence collection eats a full-time job | 53% dedicate the equivalent of one full-time employee to evidence collection ¹ |
| 📅 Controls are checked too rarely | 72% still rely on periodic assessments instead of real-time checks ² |
| ❌ Programmes fall short | Only 29% say their compliance consistently meets internal and external standards ³ |

**Audits check once a year. Attackers check every day.**

---

## ⚔️ How It Works: A Courtroom for Controls

| Agent | Role | What it does | Permissions |
|-------|------|--------------|-------------|
| 🗡️ **Red agent** | Prosecutor | Reads the policy, cross-checks systems, and hunts for violations with exact evidence | Read-only tools |
| 🛡️ **Blue agent** | Defence | Re-checks every finding, looks for exceptions, and concedes when it can't clear it | Read-only tools |
| ⚖️ **Judge agent** | Independent auditor | Weighs both sides and returns PASS / WEAK / FAIL, accepting only claims backed by tool output | No tools |
| 💥 **Drift attacker** | Careless developer | Introduces a realistic misconfiguration, then measures time-to-detect | Sandbox log file only |

> **Why three agents?** Separation of duties. An agent that finds, defends *and* grades its own findings is marking its own homework. In GRC, that isn't evidence.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    AcmeCorp (fictional sandbox)                  │
│                                                                  │
│  📜 Policy   🗄️ Customer DB   📈 Analytics   💾 Backups          │
│  📝 App logs   🔐 Identity provider   👥 HR system               │
└───────────────────────────────┬──────────────────────────────────┘
                                │  read-only, allowlisted tools
                                │  (files or mock REST API)
┌───────────────────────────────▼──────────────────────────────────┐
│                 ControlCombat engine (Python)                    │
│                                                                  │
│   🗡️ Red agent ──────► findings ──────┐                          │
│        ▲                              ▼                          │
│        │ Claude API tool use     🛡️ Blue agent ──► defence       │
│        │                              │                          │
│        └────────── evidence log ◄─────┘                          │
│                                       ▼                          │
│                              ⚖️ Judge agent                       │
│                     verdict + evidence + fixes                   │
│                     mapped to ISO 27001 / GDPR                   │
└───────────────────────────────┬──────────────────────────────────┘
                                │  results.json + audit trail
┌───────────────────────────────▼──────────────────────────────────┐
│  📊 Live dashboards                                              │
│  3D control landscape · agent network · verdicts · audit trail   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Control Mapping

| # | Rule tested | ISO 27001:2022 | GDPR | Planted mistake |
|---|-------------|----------------|------|-----------------|
| 1 | Deletion requests honoured in all systems | A.8.10 · A.5.34 | Art. 17 | Sarah Lin "deleted" but still in analytics and backup |
| 2 | No customer personal data in logs | A.8.11 · A.8.15 | Art. 5(1)(c) | 2 customer emails in `app.log` |
| 3 | Data deleted 2 years after account closure | A.8.10 · A.5.34 | Art. 5(1)(e) | 3 ex-customers kept too long |
| 4 | Every admin account uses MFA | A.8.2 · A.8.5 | – | Ben is an admin without MFA |
| 5 | Leavers disabled within 24 hours | A.6.5 · A.5.18 | – | George left but his account is active and was used |

**Coverage:** 8 of 93 Annex A controls tested automatically. The dashboard shows all 93 and marks each untested one as *automatable later* (needs another system connected) or *manual evidence* (policy, people or physical controls).

---

## 📊 Results (real run, Claude API)

| Metric | Result |
|--------|--------|
| ✅ Agent verdicts matching the rule-based answer key | **5 / 5** |
| 🔴 Tested controls found non-compliant | **8 / 8** (every rule had a planted mistake) |
| 🔎 Tool calls made by the agents | **~60**, every one logged with a timestamp |
| 🎯 Trick cases handled correctly | Staff (not admin) without MFA ignored · leaver disabled on time passed · fully deleted customer passed |
| 🆕 Finding we did not plant | A closed customer copied into a **new backup after his deletion deadline** |

> The answer key is plain Python with no AI (`ground_truth.py`), so agent accuracy is checked independently, not self-reported.

---

## 🖥️ Dashboards

| Dashboard | Run | What you get |
|-----------|-----|--------------|
| 🌐 **Pro dashboard** | `python -m streamlit run dashboard_pro.py` | Dark SOC-style view: 3D control landscape (tower height = violations), 3D agent network, agent timeline, rule inspector, all 93 controls |
| 🧊 **3D web dashboard** | `python pro_dashboard.py` → http://localhost:8600 | Three.js landscape of all 93 controls (drag to rotate, click a pillar), red/blue/judge results and activity log; works offline |
| 📋 **Classic dashboard** | `python -m streamlit run dashboard.py` | Simple tabs: ISO 27001 controls, agent tests, agent activity |

All three read the same `results.json` and refresh live while the agents run.

---

## 🚀 Quick Start

### Step 1: Install

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Mac / Linux
pip install -r requirements.txt
```

### Step 2: Add your API key

```bash
copy .env.example .env            # Windows  (cp on Mac / Linux)
```

Open `.env` and paste your Anthropic API key after `ANTHROPIC_API_KEY=`. Also set `AUDIT_DATE=2026-11-04` so results match the answer key.

> 🔐 Put the key in **`.env`**, never in `.env.example`. `.env` is git-ignored; `.env.example` is published.

### Step 3: Preview with sample data (free)

```bash
python reset.py
python run.py --sample
python -m streamlit run dashboard_pro.py
```

### Step 4: Run the real agents (second terminal)

```bash
python run.py --rule deletion     # one rule first
python run.py                     # all 5 rules
python ground_truth.py            # compare against the answer key
```

---

## 💥 Demo: The Drift Attacker

Measures how fast a new mistake is caught, compared with a yearly audit.

```bash
python reset.py --clean-logs              # logs start clean
python run.py --rule logs --watch 30      # terminal 2: re-checks every 30 s, shows PASS
python drift.py                           # terminal 3: a developer leaks a customer email into logs
```

The logs control turns red and the dashboard shows **Drift caught in X s**.

---

## 🛡️ GRC Design Principles

| Principle | How ControlCombat applies it |
|-----------|------------------------------|
| ⚖️ **Separation of duties** | Attacker, defender and judge are separate agents; the judge has no tools |
| 🧾 **Evidence-based assurance** | Every FAIL must cite tool output; a FAIL without evidence is downgraded to UNVERIFIED |
| 🔒 **Least privilege** | Agents can only call an allowlist of read-only tools; only the drift attacker writes, and only inside the sandbox |
| 📉 **Data minimisation (A.8.11)** | Collects settings and metadata (roles, MFA status, dates), not business content |
| 🕵️ **Audit trail** | Every tool call is logged with agent, input, output and timestamp |
| 🎯 **Honest coverage** | Untested controls are shown as untested, never as passing |
| 🪪 **Production identity** | In production, each agent would run under its own Microsoft Entra Agent ID with least-privilege access and sign-in logs ⁴ |

---

## 📁 Project Structure

```
controlcombat/
├── 📜 policy.md               # AcmeCorp's written promises (the 5 rules)
├── 🗄️ data_clean/             # Fictional data with planted mistakes
├── 🧾 answer_key.txt          # Every planted mistake, written out
├── ⚙️ config.py               # Settings, read from .env
├── 🏢 sandbox.py              # Read-only access to AcmeCorp's systems
├── 🧰 tools.py                # Allowlisted tools Claude can call (files or API)
├── 🌐 mock_api.py             # FastAPI server pretending to be AcmeCorp
├── 🤖 agent.py                # Claude tool-use loop + evidence logging
├── ⚔️ agents.py               # Red, blue and judge prompts + debate
├── ▶️ run.py                  # Runs the rules, writes results.json
├── ✅ ground_truth.py         # Answer key in code (no AI)
├── 🗺️ controls.py             # All 93 ISO 27001 Annex A controls + scoring
├── 💥 drift.py                # Drift attacker (sandbox log only)
├── 🔄 reset.py                # Restore the sandbox before each demo
├── 🌐 dashboard_pro.py        # Pro Streamlit dashboard (3D)
├── 🧊 pro_dashboard.py        # 3D web dashboard (Three.js, port 8600)
├── 📋 dashboard.py            # Classic Streamlit dashboard
├── 🎨 static/                 # Front-end for the 3D web dashboard
├── 🎛️ .streamlit/config.toml  # Dark theme
└── 📖 README.md               # You are here
```

---

## 🧭 Going Live

The agents never change. Only the inside of the tools does.

| Today (sandbox) | Production |
|-----------------|------------|
| `idp_users.json` | Microsoft Entra ID / Okta |
| `hr_leavers.json` | HR system (Workday, BambooHR) |
| `users.json`, `analytics.json`, backups | Real databases and data warehouse |
| `app.log` | SIEM / log platform |
| Manual run | Scheduled daily, or on every change |
| Dashboard | Plus tickets in Jira and alerts in Slack |

---

## 🛣️ Roadmap

- [ ] Connect a real Entra ID test tenant for the MFA and leaver rules
- [ ] Add cloud controls (storage access, encryption, firewall: A.8.3, A.8.20, A.8.24)
- [ ] Crosswalk to SOC 2 and ISO 27701
- [ ] Auto-create remediation tickets in Jira
- [ ] Export an auditor-ready evidence pack (PDF)

---

## ⚠️ Known Limitations

- 🧪 **Prototype:** tested on a fictional company with planted mistakes, not production systems.
- 📏 **Coverage:** 8 of 93 controls are tested automatically; policy, people and physical controls still need human evidence.
- 🎓 **Not a certification:** ISO 27001 certification needs a full management system and an accredited auditor. ControlCombat automates technical control evidence.
- 🤖 **AI can be wrong:** verdicts are checked against a rule-based answer key here; in production, a human should review FAIL findings.

---

## 📚 GRC Glossary

| Term | Plain meaning |
|------|---------------|
| **GRC** | Governance, Risk and Compliance: how a company sets rules, manages risk and proves it follows them |
| **Control** | A specific security or privacy rule, e.g. "every admin uses MFA" |
| **Evidence** | Proof a control works: a log, a record, a system export |
| **ISO 27001** | International standard for information security; Annex A lists 93 controls |
| **Drift** | When a system slowly stops matching its rules |
| **Red / blue team** | Attackers vs defenders, borrowed from security exercises |

---

## 👥 Created by

| Name | Role | What they built |
|------|------|-----------------|
| 👩‍💻 Pradnya Bhakare | GRC & AI Engineer | *[describe your part: e.g. agent design, control mapping, dashboards, demo]* |
| 👤 *[Teammate]* | *[Role]* | *[What they built]* |

Built at *[hackathon name]*, November 2026.

---

## 🔗 Sources

1. [2026 State of Continuous Controls Monitoring Report](https://business.mammothtimes.com/mammothtimes/article/bizwire-2026-1-20-2026-state-of-ccm-report-resource-constraints-drive-85-of-organizations-to-rethink-traditional-grc-approaches)
2. [RegScale 2026 State of CCM Report (PDF)](https://discover.regscale.com/hubfs/Resource%20Files/2026%20State%20of%20Continuous%20Controls%20Monitoring%20Report%20%7C%20RegScale.pdf)
3. [Help Net Security: Compliance weighs heavily on security and GRC teams](https://www.helpnetsecurity.com/2025/04/22/security-grc-teams-compliance/)
4. [What is Microsoft Entra Agent ID? (Microsoft Learn)](https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id)

> All names, emails and companies in this project are fictional test data.

---

<div align="center">

**Built with ❤️ and a healthy distrust of checkboxes**

*Claude API · ISO 27001:2022 · GDPR · GRC Engineering*

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f766e,50:12355b,100:0b1020&height=120&section=footer" width="100%"/>

</div>
