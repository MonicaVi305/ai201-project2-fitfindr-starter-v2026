"""
Structured request log for serve.py.  ← CAPSTONE (Shape C)

One JSON object per line, appended to logs/requests.jsonl. Every request that
reaches POST /ask leaves a record — successes, empty searches, model outages,
rejected input and crashes alike. A failure that shows up only as a missing
line is a failure nobody finds.

Fields (all present on every record; unknown values are null):

    ts              UTC time the request finished, ISO 8601
    request_id      short random id, also returned to the caller
    status_code     HTTP status returned
    outcome         ok | no_results | model_unavailable | bad_request | server_error
    query           what came in (truncated to 300 chars)
    wardrobe        "example" | "custom:<n items>" | "invalid"
    selected_item   listing id the agent picked, or null
    fit_card        what came out, first 200 chars, or null
    error           the message returned to the caller, or null
    duration_ms     wall time of the whole request, queueing included
    queue_wait_ms   how long it waited for the one-at-a-time lock
    model_calls     real (non-cached) model requests this run made
    prompt_tokens   tokens sent, as reported by the service
    output_tokens   tokens received, as reported by the service

Writing a log line must never break a request, so every failure in here is
swallowed (and reported once on stderr).
"""

import json
import sys
import threading
from datetime import datetime, timezone

import config

LOG_DIR = config.ROOT / "logs"
LOG_FILE = LOG_DIR / "requests.jsonl"

_write_lock = threading.Lock()
_warned = False

FIELDS = (
    "ts", "request_id", "status_code", "outcome", "query", "wardrobe",
    "selected_item", "fit_card", "error", "duration_ms", "queue_wait_ms",
    "model_calls", "prompt_tokens", "output_tokens",
)


def _clip(text, limit):
    if text is None:
        return None
    text = str(text)
    return text if len(text) <= limit else text[:limit] + "…"


def log_request(**fields) -> None:
    """Append one record. Missing fields become null; extras are dropped."""
    global _warned
    record = {name: fields.get(name) for name in FIELDS}
    record["ts"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    record["query"] = _clip(record["query"], 300)
    record["fit_card"] = _clip(record["fit_card"], 200)
    record["error"] = _clip(record["error"], 300)
    try:
        with _write_lock:
            LOG_DIR.mkdir(exist_ok=True)
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # noqa: BLE001 — logging must never break a request
        if not _warned:
            _warned = True
            print(f"  [request_log] could not write {LOG_FILE}: {exc}", file=sys.stderr)


def read_log(path=LOG_FILE) -> list[dict]:
    """Read the log back as a list of dicts. Skips unparseable lines."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
