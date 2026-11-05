# ControlCombat

AI agents that test whether a company's ISO 27001 controls actually work, instead of trusting the paperwork.
A red agent attacks each rule, a blue agent defends it with evidence, and a judge agent decides PASS / WEAK / FAIL.
Everything runs against **AcmeCorp**, a fictional company with deliberately planted mistakes.

## Quick start (about 10 minutes)

You need Python 3.11+ and an Anthropic API key.

**1. Open this folder in VS Code, then open a terminal** (`` Ctrl+` ``).

**2. Create a virtual environment and install the libraries**

Mac / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.

**3. Add your API key**

Copy `.env.example` to a new file called `.env`, and paste your key after `ANTHROPIC_API_KEY=`.
Tip: also set `AUDIT_DATE=2026-11-04` so results always match the answer key.

**4. Try the dashboard first (no API credits used)**
```bash
python reset.py
python run.py --sample
streamlit run dashboard.py
```
A browser tab opens with the dashboard. Leave it open.

**5. Run the real agents** (in a second terminal, with the venv activated)
```bash
python run.py --rule deletion     # one rule first, to check everything works
python run.py                     # then all 5 rules
```
Watch the dashboard cards change from ⏸️ to ⏳ to 🔴 or 🟢. Each card shows whether the agents' verdict **matches the answer key**.

## 3D dashboard (for demos)

```bash
python pro_dashboard.py
```
Open http://localhost:8600. It shows all 93 ISO 27001 controls as a 3D landscape (drag to rotate, click a pillar),
plus the red/blue/judge results and the full agent activity log. It reads the same `results.json`, so keep
`python run.py` in another terminal and the page updates every 2 seconds. Works offline.

## Pro dashboard (3D)

```bash
pip install -r requirements.txt          # adds plotly
python -m streamlit run dashboard_pro.py
```
A dark, security-operations style dashboard with:
- **Control landscape (3D):** all 93 ISO 27001 controls as a city, one block per theme; tower height = violations found
- **Agent network (3D):** which agent called which tool on which AcmeCorp system; drag to rotate
- **Agent timeline**, rule verdicts with answer-key checks, a rule inspector (red vs blue vs judge) and the full controls table

Drag the 3D views to rotate them, scroll to zoom, and hover for details. The simple `dashboard.py` still works as a backup.
The `.streamlit/config.toml` file switches both dashboards to the dark theme.

## The 5 rules

| Rule | ISO 27001 | GDPR | Planted mistake |
| --- | --- | --- | --- |
| Deletion requests honoured in all systems | A.8.10, A.5.34 | Art. 17 | Sarah Lin "deleted" but still in analytics and backup |
| No customer personal data in logs | A.8.11, A.8.15 | Art. 5(1)(c) | 2 customer emails in app.log |
| Data deleted 2 years after closure | A.8.10, A.5.34 | Art. 5(1)(e) | Marcus Chen, David Kim, Oliver Grant kept too long |
| Every admin uses MFA | A.8.2, A.8.5 | - | Ben is an admin without MFA |
| Leavers disabled within 24 hours | A.6.5, A.5.18 | - | George left but his account is active and was used |

Check the expected answers any time with `python ground_truth.py` (plain Python, no AI).

## Demo: the drift attacker

Shows how fast the agents catch a new mistake.
```bash
python reset.py --clean-logs              # logs start clean
python run.py --rule logs --watch 30      # terminal 2: re-checks logs every 30s, shows PASS
python drift.py                           # terminal 3: a "careless developer" leaks an email into the logs
```
The logs card turns red and the dashboard shows **Drift caught in X s**.

## Optional: use the mock AcmeCorp API instead of files

```bash
python mock_api.py          # terminal 1: open http://127.0.0.1:8000/docs to see the endpoints
```
Set `DATA_SOURCE=api` in `.env`, then run `python run.py` as normal. The agents now get their data over HTTP,
exactly as they would from a real company's systems. Going live means pointing `ACME_API_URL` at real systems;
the agents don't change.

## Files

| File | What it does |
| --- | --- |
| `policy.md` | AcmeCorp's written promises (the 5 rules) |
| `data_clean/` | The original fake data with planted mistakes. `reset.py` copies it to `data/` |
| `answer_key.txt` | Every planted mistake, written out |
| `config.py` | Settings, read from `.env` |
| `sandbox.py` | Read-only access to AcmeCorp's fake systems |
| `tools.py` | The tools Claude can call (allowlisted, read-only), via files or the API |
| `mock_api.py` | Optional FastAPI server pretending to be AcmeCorp's systems |
| `agent.py` | The Claude tool-use loop; logs every tool call as audit evidence |
| `agents.py` | Red, blue and judge prompts, and the debate for one rule |
| `run.py` | Runs the rules and writes `results.json` |
| `dashboard.py` | Streamlit dashboard |
| `drift.py` | Drift attacker (only touches `data/app.log`) |
| `ground_truth.py` | Answer key in code, no AI |
| `reset.py` | Restore the sandbox before each demo |

## Troubleshooting

- **"No ANTHROPIC_API_KEY found"**: create `.env` from `.env.example` and paste your key.
- **Model not found error**: set `CLAUDE_MODEL=` in `.env` to a model your key can use (see the Claude Console).
- **Rate limit or timeout**: run one rule at a time with `--rule`. A failed rule shows ⚠️ Error; just run it again.
- **Results look wrong**: run `python reset.py` to restore the data, and set `AUDIT_DATE=2026-11-04`.
- **Dashboard not updating**: turn on "Live refresh" in the sidebar.

All names, emails and companies in this project are fictional.
