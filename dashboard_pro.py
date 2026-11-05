"""ControlCombat Pro: 3D security-operations dashboard.

Run:  python -m streamlit run dashboard_pro.py
(The original dashboard.py still works as a simple backup.)
"""
import datetime
import html
import json
import math
import time

import plotly.graph_objects as go
import streamlit as st

from config import BASE, DATA, DATA_SOURCE, MODEL, audit_date
from controls import ANNEX_A, THEMES, control_compliance

st.set_page_config(page_title="ControlCombat Pro", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ design tokens (dark)
SURFACE, PAGE = "#1a1a19", "#0d0d0d"
INK, INK2, MUTED = "#f0efec", "#c3c2b7", "#898781"
GRID, AXIS, BORDER = "#2c2c2a", "#383835", "rgba(255,255,255,0.10)"
GOOD, WARN, CRIT, IDLE = "#0ca30c", "#fab219", "#d03b3b", "#4a4945"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

# Agent identity = categorical slots 1-3 (blue, orange, aqua), always labelled
AGENTS = {
    "red": {"name": "Red agent", "role": "Attacker · hunts for violations", "color": "#d95926", "icon": "🗡️"},
    "blue": {"name": "Blue agent", "role": "Defender · checks evidence", "color": "#3987e5", "icon": "🛡️"},
    "judge": {"name": "Judge agent", "role": "Auditor · decides the verdict", "color": "#199e70", "icon": "⚖️"},
}

# Rule verdicts and control statuses: status colour + icon + label, never colour alone
VERDICT = {
    "PASS": (GOOD, "✓", "Pass"), "WEAK": (WARN, "◐", "Weak"), "FAIL": (CRIT, "✕", "Fail"),
    "RUNNING": (INK2, "⏳", "Running"), "WAITING": (MUTED, "⏸", "Waiting"),
    "NOT RUN": (MUTED, "○", "Not run"), "UNVERIFIED": (MUTED, "?", "Unverified"),
    "ERROR": (WARN, "!", "Error"),
}
CONTROL_STATUS = {
    "Non-compliant": (CRIT, "✕"), "Partially compliant": (WARN, "◐"),
    "Compliant": (GOOD, "✓"), "Pending": (INK2, "⏳"), "Not tested": (IDLE, "○"),
}

# Which AcmeCorp system each tool reads (for the agent network)
TOOL_SYSTEMS = {
    "read_policy": ["Policy"],
    "list_customers": ["Customer DB"], "list_closed_accounts": ["Customer DB"],
    "list_deletion_requests": ["Customer DB"],
    "list_analytics_customers": ["Analytics"], "list_backup_customers": ["Backups"],
    "read_logs": ["App logs"],
    "search_systems": ["Customer DB", "Analytics", "Backups", "App logs"],
    "list_staff_accounts": ["Identity provider"], "list_leavers": ["HR system"],
}

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1560px; }}
h1, h2, h3, h4 {{ letter-spacing: -0.01em; }}
.cc-head {{ display:flex; align-items:center; gap:14px; }}
.cc-logo {{ width:44px; height:44px; border-radius:12px; display:grid; place-items:center;
           background:{SURFACE}; border:1px solid {BORDER}; font-size:24px; }}
.cc-title {{ font-size:1.7rem; font-weight:650; color:{INK}; line-height:1.1; }}
.cc-sub {{ color:{MUTED}; font-size:.86rem; margin-top:2px; }}
.cc-pill {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px;
           border:1px solid {BORDER}; background:{SURFACE}; color:{INK}; font-size:.8rem; font-weight:600;
           letter-spacing:.05em; }}
.cc-dot {{ width:9px; height:9px; border-radius:50%; display:inline-block; }}
.cc-live .cc-dot {{ animation: ccpulse 1.2s ease-in-out infinite; }}
@keyframes ccpulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:.25 }} }}
.cc-kpi {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:14px; padding:16px 18px; min-height:142px; }}
.cc-kpi .lab {{ color:{MUTED}; font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; }}
.cc-kpi .val {{ color:{INK}; font-size:2.15rem; font-weight:650; line-height:1.15; margin-top:6px; }}
.cc-kpi .val small {{ font-size:1rem; color:{INK2}; font-weight:500; }}
.cc-kpi .sub {{ color:{INK2}; font-size:.8rem; margin-top:4px; }}
.cc-bar {{ height:6px; border-radius:4px; background:{AXIS}; margin-top:10px; overflow:hidden; }}
.cc-bar > div {{ height:100%; border-radius:4px; }}
.cc-sec {{ color:{INK}; font-weight:600; font-size:1.02rem; margin:4px 0 2px; }}
.cc-sec span {{ color:{MUTED}; font-weight:400; font-size:.85rem; }}
.cc-rule {{ display:flex; align-items:center; gap:12px; padding:11px 12px; border-radius:12px;
           border:1px solid {BORDER}; background:{SURFACE}; margin-bottom:8px; }}
.cc-badge {{ min-width:30px; height:30px; border-radius:9px; display:grid; place-items:center;
            font-weight:700; color:#fff; font-size:.95rem; }}
.cc-rule .nm {{ color:{INK}; font-size:.9rem; font-weight:550; line-height:1.25; }}
.cc-rule .mt {{ color:{MUTED}; font-size:.76rem; margin-top:2px; }}
.cc-rule .rt {{ margin-left:auto; text-align:right; color:{INK2}; font-size:.78rem; white-space:nowrap; }}
.cc-chip {{ display:inline-block; padding:2px 8px; margin:2px 4px 2px 0; border-radius:6px;
           background:{PAGE}; border:1px solid {BORDER}; color:{INK2}; font-size:.74rem;
           font-family: ui-monospace, Menlo, Consolas, monospace; }}
.cc-agent-h {{ display:flex; align-items:center; gap:10px; }}
.cc-agent-h .sw {{ width:12px; height:12px; border-radius:3px; }}
.cc-agent-h .nm {{ color:{INK}; font-weight:600; font-size:1rem; }}
.cc-agent-h .rl {{ color:{MUTED}; font-size:.78rem; }}
.cc-stat {{ color:{INK2}; font-size:.8rem; margin:6px 0 4px; }}
.cc-verdict {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:10px;
              color:#fff; font-weight:700; letter-spacing:.04em; }}
.cc-note {{ color:{MUTED}; font-size:.78rem; }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
def load(name):
    try:
        return json.loads((BASE / name).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def esc(text):
    return html.escape(str(text))


def ts(value):
    try:
        return datetime.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


results = load("results.json") or []
live = load("live_status.json")
drift = load("drift_event.json")
running = any(r["verdict"] in ("RUNNING", "WAITING") for r in results)
is_sample = bool(results) and all(r.get("sample") for r in results)

try:
    from ground_truth import expected
    answer_key = expected() if DATA.exists() else {}
except Exception:
    answer_key = {}

# ------------------------------------------------------------------ header
h1, h2 = st.columns([5, 2], vertical_alignment="center")
h1.markdown(f"""
<div class="cc-head">
  <div class="cc-logo">🛡️</div>
  <div>
    <div class="cc-title">ControlCombat</div>
    <div class="cc-sub">AcmeCorp · ISO 27001:2022 continuous control testing · audit date {audit_date()}
      · data: {esc(DATA_SOURCE)} · model: {esc(MODEL)}</div>
  </div>
</div>""", unsafe_allow_html=True)

if running:
    pill = f'<span class="cc-pill cc-live"><span class="cc-dot" style="background:{WARN}"></span>LIVE · AGENTS WORKING</span>'
elif is_sample:
    pill = f'<span class="cc-pill"><span class="cc-dot" style="background:{MUTED}"></span>SAMPLE DATA</span>'
elif results:
    pill = f'<span class="cc-pill"><span class="cc-dot" style="background:{GOOD}"></span>AUDIT COMPLETE</span>'
else:
    pill = f'<span class="cc-pill"><span class="cc-dot" style="background:{MUTED}"></span>NO RESULTS</span>'
with h2:
    p1, p2 = st.columns([3, 2], vertical_alignment="center")
    p1.markdown(f'<div style="text-align:right">{pill}</div>', unsafe_allow_html=True)
    auto = p2.toggle("Auto-refresh", value=bool(running or (drift and drift.get("seconds_to_detect") is None)))

if not results:
    st.info("No results yet. Run `python run.py` in a terminal, or `python run.py --sample` to preview.")
    if auto:
        time.sleep(2)
        st.rerun()
    st.stop()

if is_sample:
    st.warning("Showing **sample results**. Run `python reset.py` then `python run.py` to see the real agents.")

if live and running:
    a = AGENTS.get(live.get("agent"), {"icon": "🤖", "name": live.get("agent", "Agent")})
    detail = f" · `{live['detail']}`" if live.get("detail") else ""
    st.info(f"{a['icon']} **{a['name']}** is {live.get('action')}{detail}  \n"
            f"Rule: *{live.get('rule_name')}*")

# ------------------------------------------------------------------ KPIs
rows = control_compliance(results)
tested = [r for r in rows if r["Compliance"] is not None]
overall = round(sum(r["Compliance"] for r in tested) / len(tested)) if tested else None
n_status = {s: sum(r["_status"] == s for r in rows) for s in CONTROL_STATUS}
violations = sum(len(r.get("evidence") or []) for r in results if r["verdict"] in ("FAIL", "WEAK"))
tool_log = [(r, t) for r in results for t in (r.get("tool_log") or [])]
graded = [r for r in results if r["verdict"] in ("PASS", "WEAK", "FAIL") and r["id"] in answer_key]
matches = sum((r["verdict"] != "PASS") == (answer_key[r["id"]]["verdict"] == "FAIL") for r in graded)


def kpi(col, label, value, sub="", bar=None, bar_color=INK2):
    bar_html = (f'<div class="cc-bar"><div style="width:{bar}%;background:{bar_color}"></div></div>'
                if bar is not None else "")
    col.markdown(f'<div class="cc-kpi"><div class="lab">{label}</div><div class="val">{value}</div>'
                 f'<div class="sub">{sub}</div>{bar_html}</div>', unsafe_allow_html=True)


k = st.columns(6)
comp_color = GOOD if (overall or 0) >= 80 else WARN if (overall or 0) >= 50 else CRIT
kpi(k[0], "Overall compliance", f"{overall}%" if overall is not None else "–",
    f"across {len(tested)} tested controls", bar=overall or 0, bar_color=comp_color)
kpi(k[1], "Non-compliant controls", f"{n_status['Non-compliant']}<small> / {len(tested) or 0}</small>",
    f"✕ {n_status['Non-compliant']} broken · ◐ {n_status['Partially compliant']} partial · ✓ {n_status['Compliant']} ok")
kpi(k[2], "Violations found", violations, "each backed by tool evidence")
kpi(k[3], "Controls auto-tested", f"{len(ANNEX_A) - n_status['Not tested']}<small> / {len(ANNEX_A)}</small>",
    "ISO 27001 Annex A coverage",
    bar=round(100 * (len(ANNEX_A) - n_status["Not tested"]) / len(ANNEX_A)), bar_color="#3987e5")
kpi(k[4], "Agent tool calls", len(tool_log),
    f"{sum(1 for _, t in tool_log if t.get('agent') == 'red')} red · "
    f"{sum(1 for _, t in tool_log if t.get('agent') == 'blue')} blue")
if drift and drift.get("seconds_to_detect") is not None:
    kpi(k[5], "Drift caught in", f"{drift['seconds_to_detect']}<small> s</small>", "a yearly audit: up to 12 months")
elif drift:
    kpi(k[5], "Drift attacker", "Active", "waiting for agents to notice…")
else:
    kpi(k[5], "Answer key match", f"{matches}<small> / {len(graded)}</small>" if graded else "–",
        "agent verdicts vs plain-Python checks")

st.write("")


# ------------------------------------------------------------------ 3D: control landscape
def base_layout(height):
    return dict(height=height, paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
                font=dict(family=FONT, color=INK2, size=12), margin=dict(l=0, r=0, t=8, b=0),
                hoverlabel=dict(bgcolor=PAGE, bordercolor=AXIS, font=dict(color=INK, family=FONT)),
                legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, font=dict(color=INK2),
                            bgcolor="rgba(0,0,0,0)"),
                uirevision="keep")


def landscape_figure(rows):
    """93 controls as a city: one block per ISO theme, tower height = violations found."""
    gap = 2.0
    by_theme = {t: [r for r in rows if r["Theme"] == t] for t in THEMES.values()}
    widths = {t: min(10, len(items)) for t, items in by_theme.items()}
    offsets, x0 = {}, 0.0
    for theme in THEMES.values():
        offsets[theme] = x0
        x0 += widths[theme] + gap

    meshes = {s: {"x": [], "y": [], "z": [], "i": [], "j": [], "k": [], "text": []} for s in CONTROL_STATUS}
    labels_x, labels_y, labels_z, labels_t = [], [], [], []
    faces = [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    for theme, items in by_theme.items():
        width = widths[theme]
        for n, r in enumerate(items):
            cx = offsets[theme] + n % width
            cy = n // width
            status = r["_status"]
            findings = r["Findings"] or 0
            h = {"Not tested": 0.12, "Pending": 0.5, "Compliant": 0.6}.get(status, 0.6 + 0.9 * findings)
            m, s = meshes[status], 0.39
            base = len(m["x"])
            for (px, py, pz) in [(cx - s, cy - s, 0), (cx + s, cy - s, 0), (cx + s, cy + s, 0), (cx - s, cy + s, 0),
                                 (cx - s, cy - s, h), (cx + s, cy - s, h), (cx + s, cy + s, h), (cx - s, cy + s, h)]:
                m["x"].append(px)
                m["y"].append(py)
                m["z"].append(pz)
            for a, b, c in faces:
                m["i"].append(base + a)
                m["j"].append(base + b)
                m["k"].append(base + c)
            comp = f"{r['Compliance']}%" if r["Compliance"] is not None else "–"
            tip = (f"<b>{r['Control']} · {esc(r['Title'])}</b><br>{CONTROL_STATUS[status][1]} {status}"
                   f" · compliance {comp}<br>Violations: {findings}<br>"
                   f"{esc(r['Tested by']) if r['Tested by'] != '-' else esc(r['How evidenced'])}")
            m["text"].extend([tip] * 8)
            if status != "Not tested":
                labels_x.append(cx)
                labels_y.append(cy)
                labels_z.append(h + 0.45)
                labels_t.append(r["Control"])

    fig = go.Figure()
    for status, m in meshes.items():
        if not m["x"]:
            continue
        color, icon = CONTROL_STATUS[status]
        count = sum(r["_status"] == status for r in rows)
        fig.add_trace(go.Mesh3d(
            x=m["x"], y=m["y"], z=m["z"], i=m["i"], j=m["j"], k=m["k"], color=color, flatshading=True,
            opacity=1.0, name=f"{icon} {status} ({count})", showlegend=True, text=m["text"],
            hovertemplate="%{text}<extra></extra>",
            lighting=dict(ambient=0.85, diffuse=0.55, specular=0.08, roughness=0.8, fresnel=0.02),
            lightposition=dict(x=-30000, y=-100000, z=60000)))
    fig.add_trace(go.Scatter3d(x=labels_x, y=labels_y, z=labels_z, mode="text", text=labels_t,
                               textfont=dict(color=INK, size=11, family=FONT), hoverinfo="skip",
                               showlegend=False))
    fig.add_trace(go.Scatter3d(
        x=[offsets[t] + (widths[t] - 1) / 2 for t in THEMES.values()], y=[-1.5] * len(THEMES), z=[0] * len(THEMES),
        mode="text", text=[f"{t} ({len(by_theme[t])})" for t in THEMES.values()],
        textfont=dict(color=INK2, size=12, family=FONT), hoverinfo="skip", showlegend=False))
    hidden = dict(visible=False, showbackground=False, showgrid=False, zeroline=False)
    fig.update_layout(**base_layout(500), scene=dict(
        xaxis=hidden, yaxis=hidden, zaxis=hidden, bgcolor=SURFACE, aspectmode="manual",
        aspectratio=dict(x=3.55, y=0.9, z=0.85),
        camera=dict(projection=dict(type="orthographic"), eye=dict(x=0.14, y=-0.88, z=0.56),
                    center=dict(x=0, y=0, z=-0.06))))
    return fig


# ------------------------------------------------------------------ 3D: agent network
def network_figure(results):
    counts = {}
    for r in results:
        for t in r.get("tool_log") or []:
            key = (t.get("agent"), t.get("tool"))
            counts[key] = counts.get(key, 0) + 1
    tools = list(TOOL_SYSTEMS)
    systems = ["Policy", "Customer DB", "Analytics", "Backups", "App logs", "Identity provider", "HR system"]

    pos = {"judge": (0, 0, 4.4), "red": (-2.6, 0, 3.0), "blue": (2.6, 0, 3.0)}
    for n, tool in enumerate(tools):
        ang = 2 * math.pi * n / len(tools)
        pos[tool] = (5.0 * math.cos(ang), 5.0 * math.sin(ang), 1.0)
    for sysname in systems:
        angs = [2 * math.pi * tools.index(t) / len(tools) for t, ss in TOOL_SYSTEMS.items()
                if sysname in ss and t != "search_systems"]
        ang = math.atan2(sum(map(math.sin, angs)), sum(map(math.cos, angs)))
        pos[sysname] = (3.0 * math.cos(ang), 3.0 * math.sin(ang), -1.4)

    fig = go.Figure()
    biggest = max(counts.values(), default=1)
    for (agent, tool), c in sorted(counts.items(), key=lambda kv: kv[1]):
        if agent not in AGENTS or tool not in pos:
            continue
        (x1, y1, z1), (x2, y2, z2) = pos[agent], pos[tool]
        fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode="lines", showlegend=False,
                                   hoverinfo="skip",
                                   line=dict(color=AGENTS[agent]["color"], width=2 + 9 * c / biggest)))
    for tool, ss in TOOL_SYSTEMS.items():
        for sysname in ss:
            (x1, y1, z1), (x2, y2, z2) = pos[tool], pos[sysname]
            fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode="lines", showlegend=False,
                                       hoverinfo="skip", line=dict(color=AXIS, width=2)))
    for src in ("red", "blue"):
        (x1, y1, z1), (x2, y2, z2) = pos[src], pos["judge"]
        fig.add_trace(go.Scatter3d(x=[x1, x2], y=[y1, y2], z=[z1, z2], mode="lines", showlegend=False,
                                   hoverinfo="skip", line=dict(color=INK2, width=3, dash="dash")))

    tool_tot = {t: sum(c for (a, tt), c in counts.items() if tt == t) for t in tools}
    fig.add_trace(go.Scatter3d(
        x=[pos[t][0] for t in tools], y=[pos[t][1] for t in tools], z=[pos[t][2] for t in tools],
        mode="markers+text", text=tools, textposition="top center", name="Tools (read-only)",
        textfont=dict(color=INK2, size=10, family=FONT),
        marker=dict(size=[7 + 13 * tool_tot[t] / max(max(tool_tot.values()), 1) for t in tools],
                    color=INK2, line=dict(color=SURFACE, width=2)),
        customdata=[[tool_tot[t], counts.get(("red", t), 0), counts.get(("blue", t), 0)] for t in tools],
        hovertemplate="<b>%{text}</b><br>%{customdata[0]} calls · red %{customdata[1]} · "
                      "blue %{customdata[2]}<extra></extra>"))
    fig.add_trace(go.Scatter3d(
        x=[pos[s][0] for s in systems], y=[pos[s][1] for s in systems], z=[pos[s][2] for s in systems],
        mode="markers+text", text=systems, textposition="bottom center", name="AcmeCorp systems",
        textfont=dict(color=MUTED, size=10, family=FONT),
        marker=dict(size=9, symbol="diamond", color=MUTED, line=dict(color=SURFACE, width=2)),
        hovertemplate="<b>%{text}</b><br>AcmeCorp system (sandbox)<extra></extra>"))
    for key, a in AGENTS.items():
        calls = sum(c for (ag, _), c in counts.items() if ag == key)
        fig.add_trace(go.Scatter3d(
            x=[pos[key][0]], y=[pos[key][1]], z=[pos[key][2]], mode="markers+text",
            text=[a["name"]], textposition="top center", name=a["name"],
            textfont=dict(color=INK, size=12, family=FONT),
            marker=dict(size=16, color=a["color"], line=dict(color=SURFACE, width=3)),
            hovertemplate=f"<b>{a['name']}</b><br>{a['role']}<br>"
                          + (f"{calls} tool calls" if key != "judge" else "Reads red and blue reports; no tools")
                          + "<extra></extra>"))
    hidden = dict(visible=False, showbackground=False, showgrid=False, zeroline=False)
    fig.update_layout(**base_layout(460), scene=dict(
        xaxis=hidden, yaxis=hidden, zaxis=hidden, bgcolor=SURFACE, aspectmode="data",
        camera=dict(eye=dict(x=0.85, y=-1.1, z=0.5), center=dict(x=0, y=0, z=-0.08))))
    return fig


# ------------------------------------------------------------------ 2D: agent timeline
def timeline_figure(results):
    fig = go.Figure()
    order = ["judge", "blue", "red"]
    for key in order:
        a = AGENTS[key]
        if key == "judge":
            pts = [(ts((r.get("agents") or {}).get("judge", {}).get("finished_at")), r) for r in results]
            pts = [(t, r) for t, r in pts if t]
            hover = [f"<b>Verdict: {r['verdict']}</b><br>{esc(r['name'])}" for _, r in pts]
            symbols = ["diamond"] * len(pts)
        else:
            pts = [(ts(t.get("at")), r, t) for r in results for t in (r.get("tool_log") or [])
                   if t.get("agent") == key]
            pts = [p for p in pts if p[0]]
            hover = [f"<b>{esc(t['tool'])}</b>({esc(json.dumps(t.get('input')))})<br>{esc(r['name'])}"
                     for _, r, t in pts]
            symbols = ["circle"] * len(pts)
        fig.add_trace(go.Scatter(
            x=[p[0] for p in pts], y=[a["name"]] * len(pts), mode="markers", name=a["name"],
            marker=dict(size=11, color=a["color"], symbol=symbols, line=dict(color=SURFACE, width=2)),
            text=hover, hovertemplate="%{text}<br>%{x|%H:%M:%S}<extra></extra>"))
    fig.update_layout(**base_layout(300), showlegend=False)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, linecolor=AXIS, tickfont=dict(color=MUTED),
                     tickformat="%H:%M:%S")
    fig.update_yaxes(showgrid=False, linecolor=AXIS, tickfont=dict(color=INK2, size=12),
                     categoryorder="array", categoryarray=[AGENTS[k]["name"] for k in order])
    fig.update_layout(margin=dict(l=8, r=8, t=8, b=8))
    return fig


PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["toImage", "lasso2d", "select2d"]}

# ------------------------------------------------------------------ row: landscape + rule verdicts
left, right = st.columns([2.3, 1], gap="medium")
with left:
    st.markdown('<div class="cc-sec">Control landscape <span>· all 93 ISO 27001 controls · '
                'tower height = violations found · drag to rotate</span></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.plotly_chart(landscape_figure(rows), config=PLOT_CONFIG, key="landscape")
with right:
    st.markdown('<div class="cc-sec">Rule verdicts <span>· red vs blue, judged</span></div>',
                unsafe_allow_html=True)
    cards = []
    for r in results:
        color, icon, label = VERDICT.get(r["verdict"], (MUTED, "?", r["verdict"]))
        ev = len(r.get("evidence") or [])
        key = answer_key.get(r["id"])
        match = ""
        if key and r["verdict"] in ("PASS", "WEAK", "FAIL"):
            ok = (r["verdict"] != "PASS") == (key["verdict"] == "FAIL")
            match = "✓ matches key" if ok else "✕ key disagrees"
        text_color = PAGE if color in (WARN,) else "#fff"
        cards.append(
            f'<div class="cc-rule"><div class="cc-badge" style="background:{color};color:{text_color}">{icon}</div>'
            f'<div><div class="nm">{esc(r["name"])}</div><div class="mt">ISO {esc(r.get("iso", "-"))}'
            f' · {label}</div></div><div class="rt">{ev} violation{"s" if ev != 1 else ""}'
            f'<br><span style="color:{MUTED}">{match}</span></div></div>')
    st.markdown("".join(cards), unsafe_allow_html=True)
    st.markdown('<div class="cc-note">Every verdict is checked against a plain-Python answer key '
                '(no AI) to prove the agents got it right.</div>', unsafe_allow_html=True)

st.write("")

# ------------------------------------------------------------------ row: network + timeline
n1, n2 = st.columns([1.25, 1], gap="medium")
with n1:
    st.markdown('<div class="cc-sec">Agent network <span>· who called which tool, on which system · '
                'line width = number of calls</span></div>', unsafe_allow_html=True)
    with st.container(border=True):
        if tool_log:
            st.plotly_chart(network_figure(results), config=PLOT_CONFIG, key="network")
        else:
            st.caption("No tool calls yet.")
with n2:
    st.markdown('<div class="cc-sec">Agent timeline <span>· every tool call and verdict, in order</span></div>',
                unsafe_allow_html=True)
    with st.container(border=True):
        if tool_log:
            st.plotly_chart(timeline_figure(results), config=PLOT_CONFIG, key="timeline")
        else:
            st.caption("No activity yet.")
    agent_cols = st.columns(3)
    for col, (key, a) in zip(agent_cols, AGENTS.items()):
        infos = [r["agents"][key] for r in results if (r.get("agents") or {}).get(key)]
        secs = sum(i.get("seconds", 0) for i in infos)
        toks = sum((i.get("input_tokens") or 0) + (i.get("output_tokens") or 0) for i in infos)
        calls = sum(i.get("tool_calls", 0) for i in infos)
        col.markdown(
            f'<div class="cc-kpi" style="padding:12px 14px;min-height:0"><div class="cc-agent-h">'
            f'<span class="sw" style="background:{a["color"]}"></span><span class="nm">{a["name"]}</span></div>'
            f'<div class="cc-stat">{len(infos)} rules · {calls if key != "judge" else len(infos)} '
            f'{"tool calls" if key != "judge" else "verdicts"}<br>{secs:.0f} s'
            f'{f" · {toks:,} tokens" if toks else ""}</div></div>', unsafe_allow_html=True)

st.write("")

# ------------------------------------------------------------------ rule inspector
st.markdown('<div class="cc-sec">Rule inspector <span>· what each agent did and why</span></div>',
            unsafe_allow_html=True)
SHORT = {"deletion": "Deletion requests", "logs": "Data in logs", "retention": "Data retention",
         "admin_mfa": "Admin MFA", "leavers": "Leavers' access"}
labels = {r["id"]: f"{VERDICT.get(r['verdict'], (0, '?'))[1]} {SHORT.get(r['id'], r['name'])}" for r in results}
default = next((r["id"] for r in results if r["verdict"] == "FAIL"), results[0]["id"])
picked = st.segmented_control("Rule", list(labels), format_func=labels.get, default=default,
                              label_visibility="collapsed") or default
rule = next(r for r in results if r["id"] == picked)

with st.container(border=True):
    color, icon, label = VERDICT.get(rule["verdict"], (MUTED, "?", rule["verdict"]))
    top1, top2 = st.columns([4, 1], vertical_alignment="center")
    top1.markdown(f"#### {esc(rule['name'])}")
    top1.caption(f"ISO 27001 {rule.get('iso', '-')} · GDPR {rule.get('gdpr', '-')}"
                 + (f" · checked {rule['checked_at']}" if rule.get("checked_at") else ""))
    text_color = PAGE if color == WARN else "#fff"
    top2.markdown(f'<div style="text-align:right"><span class="cc-verdict" style="background:{color};'
                  f'color:{text_color}">{icon} {label.upper()}</span></div>', unsafe_allow_html=True)

    cols = st.columns(3, gap="medium")
    for col, (key, a) in zip(cols, AGENTS.items()):
        info = (rule.get("agents") or {}).get(key)
        with col:
            st.markdown(f'<div class="cc-agent-h"><span class="sw" style="background:{a["color"]}"></span>'
                        f'<span class="nm">{a["icon"]} {a["name"]}</span></div>'
                        f'<div class="cc-agent-h"><span class="rl">{a["role"]}</span></div>',
                        unsafe_allow_html=True)
            if info:
                toks = (info.get("input_tokens") or 0) + (info.get("output_tokens") or 0)
                st.markdown(f'<div class="cc-stat">{info.get("tool_calls", 0)} tool calls · '
                            f'{info.get("seconds", 0)} s{f" · {toks:,} tokens" if toks else ""}</div>'
                            + "".join(f'<span class="cc-chip">{esc(t)}</span>' for t in info.get("tools_used", [])),
                            unsafe_allow_html=True)
            elif rule["verdict"] == "RUNNING":
                now_working = live and live.get("rule_id") == rule["id"] and live.get("agent") == key
                st.caption("⏳ Working now…" if now_working else "⏸ Waiting for its turn")
            if key == "judge":
                if rule.get("summary"):
                    st.write(rule["summary"])
                if rule.get("evidence"):
                    st.markdown("**Evidence**\n" + "\n".join(f"- {e}" for e in rule["evidence"]))
                if rule.get("fixes"):
                    st.markdown("**Fixes**\n" + "\n".join(f"- {f}" for f in rule["fixes"]))
            else:
                text = info["output"] if info else rule.get(key, "")
                if text:
                    with st.container(height=320, border=False):
                        st.markdown(text)

    calls = rule.get("tool_log") or []
    if calls:
        with st.expander(f"Audit trail · {len(calls)} tool calls for this rule"):
            st.dataframe([{"time": t.get("at"), "agent": AGENTS.get(t.get("agent"), {}).get("name", t.get("agent")),
                           "tool": t.get("tool"), "input": json.dumps(t.get("input")),
                           "result": (f"{len(t['output'])} results" if isinstance(t.get("output"), list)
                                      else str(t.get("output"))[:120])} for t in calls],
                         hide_index=True, width="stretch")

# ------------------------------------------------------------------ full controls table
with st.expander(f"All {len(ANNEX_A)} ISO 27001 controls · compliance table"):
    status_pick = st.multiselect("Status", list(CONTROL_STATUS), placeholder="All statuses")
    order = {"Non-compliant": 0, "Partially compliant": 1, "Pending": 2, "Compliant": 3, "Not tested": 4}
    shown = sorted([r for r in rows if not status_pick or r["_status"] in status_pick],
                   key=lambda r: order[r["_status"]])
    st.dataframe([{k: v for k, v in r.items() if not k.startswith("_")} for r in shown],
                 hide_index=True, width="stretch", height=460,
                 column_config={"Compliance": st.column_config.ProgressColumn(
                     "Compliance", format="%d%%", min_value=0, max_value=100),
                     "Title": st.column_config.TextColumn("Title", width="large")})

if auto:
    time.sleep(2)
    st.rerun()
