"""Shared settings. Values come from the .env file (see .env.example)."""
import datetime
import os
import pathlib

BASE = pathlib.Path(__file__).parent


def _load_env():
    env = BASE / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()

DATA = BASE / "data"
CLEAN_DATA = BASE / "data_clean"

# Which Claude model the agents use
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

# "files" = tools read data/ directly; "api" = tools call the mock AcmeCorp API
DATA_SOURCE = os.environ.get("DATA_SOURCE", "files").lower()
API_URL = os.environ.get("ACME_API_URL", "http://127.0.0.1:8000").rstrip("/")


def audit_date():
    """The date the audit runs 'as of'. Set AUDIT_DATE=2026-11-04 in .env to freeze it."""
    value = os.environ.get("AUDIT_DATE", "").strip()
    return datetime.date.fromisoformat(value) if value else datetime.date.today()
