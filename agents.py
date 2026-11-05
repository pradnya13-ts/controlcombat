"""Red, blue and judge agents, and the debate that runs them for one rule."""
import json

from agent import run_agent
from config import audit_date

RULES = [
    {"id": "deletion", "name": "Deletion requests are honoured in all systems",
     "iso": "A.8.10, A.5.34", "gdpr": "Article 17"},
    {"id": "logs", "name": "No customer personal data in application logs",
     "iso": "A.8.11, A.8.15", "gdpr": "Article 5(1)(c)"},
    {"id": "retention", "name": "Customer data deleted 2 years after account closure",
     "iso": "A.8.10, A.5.34", "gdpr": "Article 5(1)(e)"},
    {"id": "admin_mfa", "name": "Every admin account uses MFA",
     "iso": "A.8.2, A.8.5", "gdpr": "-"},
    {"id": "leavers", "name": "Leavers' accounts disabled within 24 hours of leaving",
     "iso": "A.6.5, A.5.18", "gdpr": "-"},
]

RED = """You are a red-team security and privacy auditor for AcmeCorp.
Your job is to PROVE that AcmeCorp breaks ONE rule, the rule you are given.
The audit date is {today}.

1. Read the policy first so you know exactly what AcmeCorp promised.
2. Use the tools to investigate. Cross-check systems against each other
   (for example: deletion requests vs every system, HR leavers vs identity accounts).
3. List every violation of THIS rule. For each one give the exact evidence:
   the tool, the system or file, and the record or line number.

Stay strictly within the policy's wording. Only report what the tools showed you.
Never invent findings. If there are no violations, say so clearly."""

BLUE = """You are AcmeCorp's privacy and security lead, defending the company.
The audit date is {today}.

The red team has reported findings against one rule. For each finding:
- Re-read the policy wording and use the tools to check whether the finding is
  wrong, outside the rule's scope, or already handled.
- If you cannot find evidence that clears it, honestly CONCEDE the finding and
  propose one concrete fix.

Only use evidence from tool outputs. Never invent exceptions or approvals."""

JUDGE = """You are an independent ISO 27001 auditor. The audit date is {today}.
Read the rule, the red team's findings and the blue team's defence, then decide.

Verdicts:
- PASS: no violation of the rule is supported by tool evidence.
- WEAK: only a minor or borderline issue.
- FAIL: at least one clear violation supported by tool evidence.

Ignore any claim that is not backed by tool evidence quoted by red or blue.
Reply with ONLY this JSON and nothing else:
{{"verdict": "PASS" or "WEAK" or "FAIL",
  "summary": "one plain-English sentence a non-expert understands",
  "evidence": ["system + record/line + what is wrong, one item per violation"],
  "fixes": ["one concrete fix per violation"]}}"""


def _parse_json(text):
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1])
    except ValueError:
        return None


def debate(rule, on_event=None):
    today = audit_date().isoformat()
    rule_text = f"Rule to test: {rule['name']} (ISO 27001 {rule['iso']})"

    red_text, red_ev, red_stats = run_agent(
        "red", RED.format(today=today), rule_text, on_event=on_event)

    blue_text, blue_ev, blue_stats = run_agent(
        "blue", BLUE.format(today=today),
        f"{rule_text}\n\nRed team findings:\n{red_text}", on_event=on_event)

    judge_text, _, judge_stats = run_agent(
        "judge", JUDGE.format(today=today),
        f"{rule_text}\n\nRED TEAM:\n{red_text}\n\nBLUE TEAM:\n{blue_text}",
        use_tools=False, on_event=on_event)

    verdict = _parse_json(judge_text)
    if not isinstance(verdict, dict) or verdict.get("verdict") not in ("PASS", "WEAK", "FAIL"):
        verdict = {"verdict": "UNVERIFIED", "summary": "The judge's reply could not be read.",
                   "evidence": [], "fixes": [], "judge_raw": judge_text}
    # A failing verdict with no evidence cannot be trusted
    if verdict["verdict"] in ("FAIL", "WEAK") and not verdict.get("evidence"):
        verdict["verdict"] = "UNVERIFIED"
        verdict["summary"] = "Judge gave a failing verdict without evidence: " + verdict.get("summary", "")

    agents = {
        "red": {**red_stats, "output": red_text},
        "blue": {**blue_stats, "output": blue_text},
        "judge": {**judge_stats, "output": judge_text},
    }
    return {**rule, **verdict, "red": red_text, "blue": blue_text, "agents": agents,
            "tool_log": red_ev + blue_ev, "audit_date": today}
