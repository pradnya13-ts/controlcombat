"""Drift attacker: plays a careless developer who leaks a customer email into the logs.

It ONLY touches data/app.log inside the sandbox.

Demo:
  1. python reset.py --clean-logs
  2. python run.py --rule logs --watch 30      (in one terminal; shows PASS)
  3. python drift.py                           (in another terminal)
  4. watch the dashboard turn red and show the time to detect
"""
import datetime
import json
import urllib.request

from config import API_URL, BASE, DATA, DATA_SOURCE

if DATA_SOURCE == "api":
    req = urllib.request.Request(API_URL + "/drift/leak-email", method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Drift introduced through the AcmeCorp API:", json.loads(resp.read())["description"])
else:
    now = datetime.datetime.now()
    with (DATA / "app.log").open("a") as f:
        f.write(f"{now:%Y-%m-%d %H:%M:%S} DEBUG new signup welcome email sent to jane.doe@example.com\n")
    (BASE / "drift_event.json").write_text(json.dumps({
        "rule": "logs",
        "description": "Debug line writes a customer email to the logs",
        "introduced_at": now.isoformat(timespec="seconds"),
    }, indent=2))
    print("Drift introduced: a customer email was written to data/app.log")
