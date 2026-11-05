"""Answer key in code: checks every rule with plain Python, no AI.

Use it to confirm the data has the planted mistakes, and to check the
agents' verdicts. The dashboard shows whether each agent verdict matches.

Run:  python ground_truth.py
"""
import datetime
import re

import sandbox
from config import audit_date

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def _date(s):
    return datetime.date.fromisoformat(s) if s else None


def check_deletion():
    findings = []
    for req in sandbox.list_deletion_requests():
        if req.get("status") != "completed":
            continue
        places = set()
        for key in (req.get("user_id"), req.get("email")):
            for hit in sandbox.search_systems(key) if key else []:
                places.add(hit["system"])
        if places:
            findings.append(f"{req['name']} ({req['user_id']}) marked deleted but still in: "
                            + ", ".join(sorted(places)))
    return findings


def check_logs():
    return [f"app.log line {row['line']}: {email}"
            for row in sandbox.read_logs(limit=100000)
            for email in EMAIL.findall(row["text"])]


def check_retention():
    today = audit_date()
    try:
        cutoff = today.replace(year=today.year - 2)
    except ValueError:  # 29 February
        cutoff = today.replace(year=today.year - 2, day=28)
    return [f"{u['name']} ({u['id']}) closed {u['closed_date']}, older than 2 years"
            for u in sandbox.list_closed_accounts()
            if _date(u.get("closed_date")) and _date(u["closed_date"]) < cutoff]


def check_admin_mfa():
    return [f"{a['email']} is an admin without MFA"
            for a in sandbox.list_staff_accounts()
            if a.get("role") == "admin" and not a.get("mfa_enabled") and not a.get("disabled")]


def check_leavers():
    accounts = {a["email"]: a for a in sandbox.list_staff_accounts()}
    findings = []
    for person in sandbox.list_leavers():
        left = _date(person["left_on"])
        acc = accounts.get(person["email"])
        if acc is None:
            continue
        problems = []
        if not acc.get("disabled"):
            problems.append("account still enabled")
        elif _date(acc.get("disabled_date")) and _date(acc["disabled_date"]) > left + datetime.timedelta(days=1):
            problems.append(f"disabled late on {acc['disabled_date']}")
        if _date(acc.get("last_sign_in")) and _date(acc["last_sign_in"]) > left:
            problems.append(f"signed in on {acc['last_sign_in']} after leaving")
        if problems:
            findings.append(f"{person['name']} left {person['left_on']}: " + "; ".join(problems))
    return findings


CHECKS = {"deletion": check_deletion, "logs": check_logs, "retention": check_retention,
          "admin_mfa": check_admin_mfa, "leavers": check_leavers}


def expected():
    """{rule_id: {"verdict": PASS/FAIL, "findings": [...]}}"""
    out = {}
    for rule_id, check in CHECKS.items():
        findings = check()
        out[rule_id] = {"verdict": "FAIL" if findings else "PASS", "findings": findings}
    return out


if __name__ == "__main__":
    print(f"Answer key as of {audit_date()}\n")
    for rule_id, result in expected().items():
        print(f"[{result['verdict']}] {rule_id}")
        for f in result["findings"]:
            print(f"   - {f}")
