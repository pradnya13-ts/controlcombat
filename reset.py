"""Reset the sandbox before each demo run.

  python reset.py               # restore AcmeCorp data with all planted mistakes
  python reset.py --clean-logs  # same, but remove email lines from the logs (for the drift demo)
"""
import re
import shutil
import sys

from config import BASE, CLEAN_DATA, DATA

shutil.rmtree(DATA, ignore_errors=True)
shutil.copytree(CLEAN_DATA, DATA)

for name in ("results.json", "drift_event.json", "live_status.json"):
    (BASE / name).unlink(missing_ok=True)

if "--clean-logs" in sys.argv:
    log = DATA / "app.log"
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    kept = [line for line in log.read_text().splitlines() if not email.search(line)]
    log.write_text("\n".join(kept) + "\n")
    print("Sandbox reset. Logs cleaned, ready for the drift demo.")
else:
    print("Sandbox reset with all planted mistakes.")
