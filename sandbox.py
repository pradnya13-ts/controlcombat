"""AcmeCorp's fake systems: read-only access to the sandbox data in data/.

Both tools.py (files mode) and mock_api.py (api mode) use these functions,
so the agents see exactly the same data either way.
"""
import json

from config import BASE, DATA

# Systems that may hold customer personal data (searched by search_systems)
CUSTOMER_SYSTEMS = ["users.json", "analytics.json", "backup_2026_10.json", "app.log"]


def _load(name):
    return json.loads((DATA / name).read_text())


def read_policy():
    return (BASE / "policy.md").read_text()


def list_customers():
    return _load("users.json")


def list_closed_accounts():
    return [u for u in _load("users.json") if u.get("status") == "closed"]


def list_deletion_requests():
    return _load("deletion_requests.json")


def list_analytics_customers():
    return _load("analytics.json")


def list_backup_customers():
    return _load("backup_2026_10.json")


def read_logs(limit=200):
    lines = (DATA / "app.log").read_text().splitlines()
    start = max(0, len(lines) - int(limit))
    return [{"line": i + 1, "text": lines[i]} for i in range(start, len(lines))]


def search_systems(text):
    """Find every record or log line, in every customer system, containing the text."""
    needle = str(text).lower().strip()
    if not needle:
        return {"error": "search text is empty"}
    hits = []
    for name in CUSTOMER_SYSTEMS:
        path = DATA / name
        if not path.exists():
            continue
        if name.endswith(".json"):
            for i, record in enumerate(json.loads(path.read_text())):
                if needle in json.dumps(record).lower():
                    hits.append({"system": name, "record": i + 1, "data": record})
        else:
            for i, line in enumerate(path.read_text().splitlines()):
                if needle in line.lower():
                    hits.append({"system": name, "line": i + 1, "text": line.strip()})
    return hits


def list_staff_accounts():
    return _load("idp_users.json")


def list_leavers():
    return _load("hr_leavers.json")
