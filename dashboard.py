"""ControlCombat live dashboard.  Run:  python -m streamlit run dashboard.py"""
import datetime
import json
import time

import pandas as pd
import streamlit as st

from config import BASE, DATA, DATA_SOURCE, audit_date
from controls import ANNEX_A, THEMES, control_compliance

st.set_page_config(page_title="ControlCombat", page_icon="🛡️", layout="wide")

STATUS = {
    "PASS": ("🟢", "green", "Control works"),
    "WEAK": ("🟠", "orange", "Weak"),
    "FAIL": ("🔴", "red", "Control broken"),
    "RUNNING": ("⏳", "blue", "Agents working..."),
    "WAITING": ("⏸️", "gray", "Waiting"),
    "NOT RUN": ("⚪", "gray", "Not run yet"),
    "UNVERIFIED": ("⚪", "gray", "Unverified"),
    "ERROR": ("⚠️", "orange", "Error"),
}
AGENTS = {
    "red": ("🔴", "Red agent", "Attacker: hunts for violations"),
    "blue": ("🔵", "Blue agent", "Defender: checks evidence, concedes or clears"),
    "judge": ("⚖️", "Judge agent", "Auditor: decides the verdict"),
}


def load(name):
    try:
        return json.loads((BASE / name).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def preview(output):
    """Short, readable summary of a tool's raw output."""
    if isinstance(output, dict) and "error" in output:
        return f"error: {output['error']}"
    if isinstance(output, list):
        if not output:
            return "0 results"
        return f"{len(output)} results · first: {json.dumps(output[0], default=str)[:120]}"
    return str(output).replace("\n", " ")[:150]


st.title("🛡️ ControlCombat")
st.caption(f"AI agents testing whether AcmeCorp's ISO 27001 controls actually work · "
           f"audit date {audit_date()} · data source: {DATA_SOURCE}")

results = load("results.json")
if not results:
    st.info("No results yet. In a terminal run `python run.py` (or `python run.py --sample` "
            "to try the dashboard without an API key).")
    if st.toggle("Live refresh", value=True):
        time.sleep(2)
        st.rerun()
    st.stop()

if all(r.get("sample") for r in results):
    st.warning("You are looking at **sample results**. Run `python reset.py` then `python run.py` "
               "to see the real agents at work.")

# Live banner: which agent is working right now
live = load("live_status.json")
running = any(r["verdict"] == "RUNNING" for r in results)
if live and running:
    icon, title, _ = AGENTS.get(live.get("agent"), ("🤖", live.get("agent"), ""))
    detail = f": `{live['detail']}`" if live.get("detail") else ""
    st.info(f"**{icon} {title}** is {live.get('action')}{detail}  \n"
            f"Rule: *{live.get('rule_name')}* · {live.get('at', '')}")

# Answer key (plain Python checks) to show whether the agents got it right
try:
    from ground_truth import expected
    answer_key = expected() if DATA.exists() else {}
except Exception:
    answer_key = {}

done = [r for r in results if r["verdict"] in ("PASS", "WEAK", "FAIL", "UNVERIFIED", "ERROR")]
passed = sum(r["verdict"] == "PASS" for r in results)
findings = sum(len(r.get("evidence") or []) for r in results if r["verdict"] in ("FAIL", "WEAK"))
tool_calls = sum(len(r.get("tool_log") or []) for r in results)
drift = load("drift_event.json")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rules passing", f"{passed} of {len(results)}")
c2.metric("Violations found", findings)
c3.metric("Rules tested", f"{len(done)} of {len(results)}")
c4.metric("Agent tool calls", tool_calls)
if drift and drift.get("seconds_to_detect") is not None:
    c5.metric("Drift caught in", f"{drift['seconds_to_detect']} s",
              help="A yearly audit could take up to 12 months to notice.")
elif drift:
    c5.metric("Drift attacker", "Undetected...", help=drift.get("description", ""))
else:
    c5.metric("Drift attacker", "Not active")

tab_controls, tab_rules, tab_activity = st.tabs(
    ["📋 ISO 27001 controls", "⚔️ Agent tests", "🤖 Agent activity"])

# ---------------------------------------------------------------- controls tab
with tab_controls:
    rows = control_compliance(results)
    tested = [r for r in rows if r["Compliance"] is not None]
    counts = {s: sum(r["_status"] == s for r in rows)
              for s in ("Compliant", "Partially compliant", "Non-compliant", "Pending", "Not tested")}
    overall = round(sum(r["Compliance"] for r in tested) / len(tested)) if tested else None

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Overall compliance", f"{overall}%" if overall is not None else "-",
              help="Average compliance across the controls the agents have tested.")
    m2.metric("🟢 Compliant", counts["Compliant"])
    m3.metric("🟠 Partially compliant", counts["Partially compliant"])
    m4.metric("🔴 Non-compliant", counts["Non-compliant"])
    m5.metric("Automatically tested", f"{len(rows) - counts['Not tested']} of {len(ANNEX_A)}",
              help="Controls covered by the agents' rules. The rest need other systems or manual evidence.")

    st.markdown("**Coverage and compliance by theme**")
    theme_cols = st.columns(len(THEMES))
    for col, theme in zip(theme_cols, THEMES.values()):
        in_theme = [r for r in rows if r["Theme"] == theme]
        scored = [r["Compliance"] for r in in_theme if r["Compliance"] is not None]
        covered = sum(r["_status"] != "Not tested" for r in in_theme)
        col.progress(covered / len(in_theme),
                     text=f"{theme}: {covered}/{len(in_theme)} tested"
                     + (f" · {round(sum(scored) / len(scored))}% compliant" if scored else ""))

    f1, f2, f3 = st.columns([2, 2, 1])
    themes = f1.multiselect("Theme", list(THEMES.values()), placeholder="All themes")
    statuses = f2.multiselect("Status", list(counts), placeholder="All statuses")
    only_tested = f3.toggle("Only tested", value=False)

    shown = [r for r in rows
             if (not themes or r["Theme"] in themes)
             and (not statuses or r["_status"] in statuses)
             and (not only_tested or r["_status"] != "Not tested")]
    order = {"Non-compliant": 0, "Partially compliant": 1, "Pending": 2, "Compliant": 3, "Not tested": 4}
    shown.sort(key=lambda r: order[r["_status"]])

    st.dataframe(
        [{k: v for k, v in r.items() if not k.startswith("_")} for r in shown],
        hide_index=True, width="stretch", height=520,
        column_config={
            "Compliance": st.column_config.ProgressColumn(
                "Compliance", format="%d%%", min_value=0, max_value=100),
            "Title": st.column_config.TextColumn("Title", width="large"),
            "Tested by": st.column_config.TextColumn("Tested by (rules)", width="large"),
        })
    st.caption(f"Showing {len(shown)} of {len(rows)} ISO 27001:2022 Annex A controls. "
               "Policy, people and physical controls need human evidence; "
               "'Automatable later' controls need another system connected.")


# ---------------------------------------------------------------- agent tests tab
def agent_panel(col, key, rule):
    icon, title, role = AGENTS[key]
    info = (rule.get("agents") or {}).get(key)
    text = info["output"] if info else rule.get(key, "")
    with col.container(border=True):
        st.markdown(f"#### {icon} {title}")
        st.caption(role)

        if info:
            st.markdown(":green[✅ Finished]" if info.get("status") == "completed"
                        else ":orange[⚠️ Stopped early]")
            tokens = (info.get("input_tokens") or 0) + (info.get("output_tokens") or 0)
            st.caption(f"🔧 {info.get('tool_calls', 0)} tool calls · ⏱️ {info.get('seconds', 0)} s"
                       + (f" · 🔤 {tokens:,} tokens" if tokens else ""))
            if info.get("tools_used"):
                st.caption("Tools: " + " ".join(f"`{t}`" for t in info["tools_used"]))
        elif rule["verdict"] == "RUNNING":
            working = live and live.get("rule_id") == rule["id"] and live.get("agent") == key
            st.markdown(":blue[⏳ Working now...]" if working else ":gray[⏸️ Waiting for its turn]")
        elif text:
            st.markdown(":green[✅ Finished]")
        else:
            st.markdown(":gray[⚪ Not run yet]")

        if key == "judge" and rule["verdict"] in STATUS and (info or rule.get("summary")):
            v_icon, v_colour, v_label = STATUS[rule["verdict"]]
            st.markdown(f"**Verdict:** :{v_colour}[{v_icon} {rule['verdict']}]")
            if rule.get("summary"):
                st.write(rule["summary"])
            if info and info.get("output"):
                with st.expander("Judge's raw reply"):
                    st.code(info["output"], language="json")
        elif text:
            with st.container(height=280):
                st.markdown(text)


with tab_rules:
    for r in results:
        icon, colour, label = STATUS.get(r["verdict"], ("⚪", "gray", r["verdict"]))
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.subheader(f"{icon} {r['name']}")
            left.caption(f"ISO 27001 {r.get('iso', '-')}  ·  GDPR {r.get('gdpr', '-')}"
                         + (f"  ·  checked {r['checked_at']}" if r.get("checked_at") else ""))
            right.markdown(f"### :{colour}[{label}]")

            key = answer_key.get(r["id"])
            if key and r["verdict"] in ("PASS", "FAIL", "WEAK"):
                agent_says_broken = r["verdict"] in ("FAIL", "WEAK")
                if agent_says_broken == (key["verdict"] == "FAIL"):
                    right.caption("✅ Matches answer key")
                else:
                    right.caption(f"❌ Answer key says {key['verdict']}")

            # Red -> Blue -> Judge, side by side
            if r["verdict"] not in ("NOT RUN", "WAITING"):
                cols = st.columns(3)
                for col, agent_key in zip(cols, AGENTS):
                    agent_panel(col, agent_key, r)

            cols = st.columns(2)
            if r.get("evidence"):
                cols[0].markdown("**Evidence**\n" + "\n".join(f"- {e}" for e in r["evidence"]))
            if r.get("fixes"):
                cols[1].markdown("**Fixes**\n" + "\n".join(f"- {f}" for f in r["fixes"]))

            if r.get("tool_log"):
                with st.expander(f"Audit trail: {len(r['tool_log'])} tool calls"):
                    st.dataframe(
                        [{"when": t.get("at"), "agent": AGENTS.get(t.get("agent"), ("", t.get("agent")))[0]
                          + " " + str(t.get("agent")), "tool": t.get("tool"),
                          "input": json.dumps(t.get("input")), "result": preview(t.get("output"))}
                         for t in r["tool_log"]],
                        width="stretch", hide_index=True)

# ---------------------------------------------------------------- agent activity tab
with tab_activity:
    st.markdown("**What each agent did across all rules**")
    a_cols = st.columns(3)
    for col, key in zip(a_cols, AGENTS):
        icon, title, role = AGENTS[key]
        infos = [r["agents"][key] for r in results if r.get("agents", {}).get(key)]
        with col.container(border=True):
            st.markdown(f"#### {icon} {title}")
            st.caption(role)
            x, y = st.columns(2)
            x.metric("Rules worked on", len(infos))
            if key == "judge":
                verdicts = [r["verdict"] for r in results if r.get("agents", {}).get("judge")]
                y.metric("Verdicts given", len(verdicts))
                if verdicts:
                    st.caption(" · ".join(f"{STATUS[v][0]} {v}: {verdicts.count(v)}"
                                          for v in ("PASS", "WEAK", "FAIL", "UNVERIFIED")
                                          if verdicts.count(v)))
            else:
                y.metric("Tool calls", sum(i.get("tool_calls", 0) for i in infos))
            seconds = sum(i.get("seconds", 0) for i in infos)
            tokens = sum((i.get("input_tokens") or 0) + (i.get("output_tokens") or 0) for i in infos)
            st.caption(f"⏱️ {seconds:.1f} s total" + (f" · 🔤 {tokens:,} tokens" if tokens else ""))

    log = [{"when": t.get("at"), "rule": r["name"], "agent": t.get("agent"), "tool": t.get("tool"),
            "input": json.dumps(t.get("input")), "result": preview(t.get("output"))}
           for r in results for t in (r.get("tool_log") or [])]

    if log:
        st.markdown("**Tool calls per rule**")
        chart = pd.DataFrame(log).groupby(["rule", "agent"]).size().unstack(fill_value=0)
        for agent_key in ("red", "blue"):
            if agent_key not in chart.columns:
                chart[agent_key] = 0
        st.bar_chart(chart[["red", "blue"]], color=["#d64545", "#3b82f6"], horizontal=True,
                     height=260)

        st.markdown("**Full activity log** (every tool call, newest first)")
        g1, g2 = st.columns(2)
        pick_agents = g1.multiselect("Agent", ["red", "blue"], placeholder="All agents")
        pick_rules = g2.multiselect("Rule", sorted({row["rule"] for row in log}), placeholder="All rules")
        rows = [row for row in log
                if (not pick_agents or row["agent"] in pick_agents)
                and (not pick_rules or row["rule"] in pick_rules)]
        rows.sort(key=lambda row: row["when"] or "", reverse=True)
        for row in rows:
            row["agent"] = f"{AGENTS[row['agent']][0]} {row['agent']}" if row["agent"] in AGENTS else row["agent"]
        st.dataframe(rows, width="stretch", hide_index=True, height=420)
        st.caption("The judge does not call tools: it only weighs the evidence red and blue collected.")
    else:
        st.info("No agent activity yet. Run `python run.py` to see the agents at work.")

busy = running or (drift and drift.get("seconds_to_detect") is None)
if st.sidebar.toggle("Live refresh", value=bool(busy)):
    time.sleep(2)
    st.rerun()
st.sidebar.markdown("**Commands**\n\n`python run.py`\n\n`python run.py --rule deletion`\n\n"
                    "`python reset.py`\n\n`python drift.py`")
