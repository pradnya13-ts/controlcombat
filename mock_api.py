"""Mock AcmeCorp API: pretends to be the company's real systems over HTTP.

Run:   python mock_api.py          (then open http://127.0.0.1:8000/docs)
Use:   set DATA_SOURCE=api in .env so the agents call this API instead of reading files.
"""
import datetime
import json

from fastapi import FastAPI

import sandbox
from config import BASE, DATA

app = FastAPI(title="AcmeCorp mock API",
              description="Fake company systems for the ControlCombat sandbox. Fictional data only.")


@app.get("/policy", tags=["policy"])
def policy():
    return sandbox.read_policy()


@app.get("/customers", tags=["customer database"])
def customers(status: str | None = None):
    rows = sandbox.list_customers()
    return [r for r in rows if r.get("status") == status] if status else rows


@app.get("/deletion-requests", tags=["customer database"])
def deletion_requests():
    return sandbox.list_deletion_requests()


@app.get("/analytics/customers", tags=["analytics"])
def analytics_customers():
    return sandbox.list_analytics_customers()


@app.get("/backups/2026-10/customers", tags=["backups"])
def backup_customers():
    return sandbox.list_backup_customers()


@app.get("/logs", tags=["logging"])
def logs(limit: int = 200):
    return sandbox.read_logs(limit)


@app.get("/search", tags=["customer database"])
def search(q: str):
    return sandbox.search_systems(q)


@app.get("/idp/users", tags=["identity provider"])
def idp_users():
    return sandbox.list_staff_accounts()


@app.get("/hr/leavers", tags=["hr"])
def hr_leavers():
    return sandbox.list_leavers()


@app.post("/drift/leak-email", tags=["drift attacker (sandbox only)"])
def drift_leak_email():
    """Simulates a developer adding a debug line that writes a customer email to the logs."""
    now = datetime.datetime.now()
    with (DATA / "app.log").open("a") as f:
        f.write(f"{now:%Y-%m-%d %H:%M:%S} DEBUG new signup welcome email sent to jane.doe@example.com\n")
    event = {"rule": "logs", "description": "Debug line writes a customer email to the logs",
             "introduced_at": now.isoformat(timespec="seconds")}
    (BASE / "drift_event.json").write_text(json.dumps(event, indent=2))
    return event


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
