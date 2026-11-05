"""Run the agents against the rules and save results.json for the dashboard.

  python run.py                          # test all 5 rules
  python run.py --rule deletion          # test one rule (cheaper, good for first try)
  python run.py --rule logs --watch 30   # re-test logs every 30s (drift demo)
  python run.py --sample                 # no API key needed: load sample results to try the dashboard
"""
import argparse
import datetime
import json
import shutil

from config import BASE, DATA, CLEAN_DATA, audit_date

RESULTS = BASE / "results.json"
DRIFT = BASE / "drift_event.json"
LIVE = BASE / "live_status.json"
RULE_IDS = ["deletion", "logs", "retention", "admin_mfa", "leavers"]


def save(results):
    tmp = RESULTS.with_suffix(".tmp")
    tmp.write_text(json.dumps(results, indent=2, default=str))
    tmp.replace(RESULTS)  # atomic, so the dashboard never reads half a file


def load_results(rules):
    try:
        old = {r["id"]: r for r in json.loads(RESULTS.read_text())}
    except (FileNotFoundError, json.JSONDecodeError):
        old = {}
    return [old.get(r["id"], {**r, "verdict": "NOT RUN"}) for r in rules]


def test_rule(rule, results):
    from agents import debate
    i = next(n for n, r in enumerate(results) if r["id"] == rule["id"])
    results[i] = {**rule, "verdict": "RUNNING"}
    save(results)
    print(f"Testing: {rule['name']} ...", flush=True)

    def on_event(event):  # shows "which agent is doing what" on the dashboard
        status = {"rule_id": rule["id"], "rule_name": rule["name"], **event,
                  "at": datetime.datetime.now().isoformat(timespec="seconds")}
        tmp = LIVE.with_suffix(".tmp")
        tmp.write_text(json.dumps(status))
        tmp.replace(LIVE)
        if event["action"] == "calling tool":
            print(f"   [{event['agent']}] {event['detail'][:100]}", flush=True)

    try:
        result = debate(rule, on_event=on_event)
    except SystemExit:
        raise
    except Exception as e:  # keep going if one rule fails (network, rate limit...)
        result = {**rule, "verdict": "ERROR", "summary": f"{type(e).__name__}: {e}"}
        print(f"  !! {result['summary']}")
    result["checked_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    results[i] = result
    save(results)
    LIVE.unlink(missing_ok=True)
    print(f"  -> {result['verdict']}: {result.get('summary', '')}")
    return result


def check_drift(result):
    """If the drift attacker introduced a problem and this check caught it, record the time."""
    if not DRIFT.exists() or result["verdict"] not in ("FAIL", "WEAK"):
        return False
    event = json.loads(DRIFT.read_text())
    if event.get("rule") != result["id"] or event.get("detected_at"):
        return False
    t1 = datetime.datetime.fromisoformat(event["introduced_at"])
    t2 = datetime.datetime.fromisoformat(result["checked_at"])
    event["detected_at"] = result["checked_at"]
    event["seconds_to_detect"] = max(0, int((t2 - t1).total_seconds()))
    DRIFT.write_text(json.dumps(event, indent=2))
    print(f"  DRIFT CAUGHT in {event['seconds_to_detect']} seconds")
    return True


def main():
    parser = argparse.ArgumentParser(description="ControlCombat runner")
    parser.add_argument("--rule", choices=RULE_IDS, help="only test this rule")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="repeat every N seconds")
    parser.add_argument("--sample", action="store_true", help="load sample results (no API key)")
    args = parser.parse_args()

    if not DATA.exists():
        shutil.copytree(CLEAN_DATA, DATA)
        print("Created data/ from data_clean/.")

    if args.sample:
        shutil.copy(BASE / "sample_results.json", RESULTS)
        print("Loaded sample results. Now run: streamlit run dashboard.py")
        return

    from agents import RULES
    from agent import get_client
    get_client()  # fail fast with a clear message if the API key is missing

    rules = [r for r in RULES if not args.rule or r["id"] == args.rule]
    results = load_results(RULES)
    for r in rules:
        results[[x["id"] for x in results].index(r["id"])] = {**r, "verdict": "WAITING"}
    save(results)
    print(f"Audit date: {audit_date()}\n")

    while True:
        for rule in rules:
            result = test_rule(rule, results)
            if check_drift(result) and args.watch:
                print("Drift detected. Stopping watch.")
                return
        if not args.watch:
            break
        print(f"Next check in {args.watch}s (Ctrl+C to stop)...")
        try:
            import time
            time.sleep(args.watch)
        except KeyboardInterrupt:
            return

    passed = sum(r["verdict"] == "PASS" for r in results)
    print(f"\nDone. {passed} of {len(results)} controls passed. See the dashboard.")


if __name__ == "__main__":
    main()
