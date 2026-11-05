"""The read-only tools the agents can call.

DATA_SOURCE=files (default): tools read the sandbox files directly.
DATA_SOURCE=api: tools call the mock AcmeCorp API over HTTP (run mock_api.py first).
At a real company you would point ACME_API_URL at real systems; the agents don't change.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

import sandbox
from config import API_URL, DATA_SOURCE

NO_INPUT = {"type": "object", "properties": {}}

# What Claude is told about each tool
TOOLS = [
    {"name": "read_policy",
     "description": "Read AcmeCorp's written privacy and security policy.",
     "input_schema": NO_INPUT},
    {"name": "list_customers",
     "description": "List all customers in the main customer database (id, name, email, status, closed_date).",
     "input_schema": NO_INPUT},
    {"name": "list_closed_accounts",
     "description": "List closed customer accounts from the main database, with their closing dates.",
     "input_schema": NO_INPUT},
    {"name": "list_deletion_requests",
     "description": "List customers who asked to be deleted, with the status and completion date AcmeCorp recorded.",
     "input_schema": NO_INPUT},
    {"name": "list_analytics_customers",
     "description": "List customer records held in the analytics system.",
     "input_schema": NO_INPUT},
    {"name": "list_backup_customers",
     "description": "List customer records held in the October 2026 backup.",
     "input_schema": NO_INPUT},
    {"name": "read_logs",
     "description": "Read the most recent application log lines, with line numbers.",
     "input_schema": {"type": "object", "properties": {
         "limit": {"type": "integer", "description": "How many recent lines (default 200)"}}}},
    {"name": "search_systems",
     "description": "Search every customer data system (main database, analytics, backup, logs) for a "
                    "name, email or customer id. Returns each system and record/line where it appears.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}},
                      "required": ["text"]}},
    {"name": "list_staff_accounts",
     "description": "List staff accounts from the identity provider: email, role (admin/staff), "
                    "MFA status, last sign-in date, disabled flag and disabled date.",
     "input_schema": NO_INPUT},
    {"name": "list_leavers",
     "description": "List staff who have left the company, from the HR system, with leaving dates.",
     "input_schema": NO_INPUT},
]

# files mode: tool name -> sandbox function
FUNCTIONS = {t["name"]: getattr(sandbox, t["name"]) for t in TOOLS}

# api mode: tool name -> (endpoint, how to turn tool input into query params)
ENDPOINTS = {
    "read_policy": ("/policy", None),
    "list_customers": ("/customers", None),
    "list_closed_accounts": ("/customers", lambda a: {"status": "closed"}),
    "list_deletion_requests": ("/deletion-requests", None),
    "list_analytics_customers": ("/analytics/customers", None),
    "list_backup_customers": ("/backups/2026-10/customers", None),
    "read_logs": ("/logs", lambda a: {"limit": a.get("limit", 200)}),
    "search_systems": ("/search", lambda a: {"q": a.get("text", "")}),
    "list_staff_accounts": ("/idp/users", None),
    "list_leavers": ("/hr/leavers", None),
}


def _call_api(name, args):
    path, to_params = ENDPOINTS[name]
    params = to_params(args) if to_params else {}
    url = API_URL + path + ("?" + urllib.parse.urlencode(params) if params else "")
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"error": f"AcmeCorp API not reachable at {API_URL} ({e}). Is mock_api.py running?"}


def run_tool(name, args):
    """Run one tool. Only tools in the allowlist above can ever be called."""
    if name not in FUNCTIONS:
        return {"error": f"Unknown tool: {name}"}
    args = args or {}
    try:
        if DATA_SOURCE == "api":
            return _call_api(name, args)
        return FUNCTIONS[name](**args)
    except Exception as e:  # give the error back to Claude instead of crashing
        return {"error": f"{type(e).__name__}: {e}"}
