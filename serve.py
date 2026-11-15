#!/usr/bin/env python3
"""
FitFindr over HTTP. ← UNIT 9

    python serve.py                       run it on your machine
    gunicorn serve:app                    run it the way a host runs it

Everything else in this repo exits after one command. A host has nothing to
keep running, so a command line cannot be deployed. This file is the smallest
thing that can: it starts a web server, waits, and hands each request to the
same `run_agent()` your CLI calls. **No new agent logic lives here.** If your
loop works from `python app.py ask`, it works from here; if it doesn't, fix it
there, not in this file.

Two routes:

    POST /ask       {"query": "vintage graphic tee under $30",
                     "wardrobe": {...}}     ← wardrobe is optional
    GET  /health    is it awake?

`/ask` returns the session dict from `run_agent()` as JSON, unchanged — the
same keys you print from the command line, including `error`. Read
`session["error"]` first, exactly as you do everywhere else.

It runs **one request at a time**, and one route is deliberately slower than a
web server has to be. The reason is worth reading before you deploy: see the
note above `_one_at_a_time` below — it also decides which gunicorn worker you
can use.

CAPSTONE: this file is now instrumented. Every POST /ask writes one JSON line
to logs/requests.jsonl (see request_log.py for the fields) and returns a
`request_id`. Bad input gets a 400 that names the problem; a crash gets a 500
and still leaves a record.
"""

import os
import sys
import threading
import time
import uuid

# config first, and before anything that talks to the model: it loads your .env
# and fixes the Windows console encoding for every module that imports it.
import config  # noqa: F401

from flask import Flask, jsonify, request

import generate
from agent import run_agent
from request_log import log_request
from utils.data_loader import get_example_wardrobe

MAX_QUERY_CHARS = 300

app = Flask(__name__)


# ── one request at a time ─────────────────────────────────────────────────────
# Here's why this exists.
#
# A web server will happily run two requests at once. Two things in this repo
# assume otherwise:
#
#   • If you moved a tool onto MCP in unit 4, `mcp_client.call_tool` starts
#     `mcp_server.py` as a separate process over stdio, one per call. Two
#     overlapping requests means two extra Python interpreters, and the free
#     tier you're deploying to has 512 MB for all of it. That is the reason
#     that would still be here even if everything else were perfect.
#   • `generate.py`'s pacing window and its call counter are plain module
#     globals — deliberately, because that file is teaching pacing and quota,
#     not locking. Two threads sharing them means the per-minute limiter is
#     counting something that isn't true.
#
# What the lock covers is exactly the agent run: the part that spawns
# processes and calls the model. Reading the request, rejecting a bad one, and
# turning the answer into JSON all happen outside it — so a request with a
# malformed body comes straight back with a 400 instead of queueing behind
# somebody else's agent.
#
# Serialising the runs costs you nothing here — this is one user asking one
# question — and it keeps the deployed behaviour identical to the CLI's. When
# that stops being an acceptable trade, the fix is a real queue, not a bigger
# lock.
#
# The same constraint decides your start command, and this is the part that
# bites in deployment rather than on your machine. `mcp_client.call_tool`
# wraps `asyncio.run()`, and `asyncio.run()` refuses to start when an event
# loop is already running. An async worker always has one running. So under
# `gunicorn -k gevent` (or `-k eventlet`, or `serve:app` wrapped for an ASGI
# server like uvicorn) EVERY MCP call fails with "asyncio.run() cannot be
# called from a running event loop" — not some of them under load, all of
# them, every time, in a place your laptop never showed you.
#
#     gunicorn serve:app              ← right: the DEFAULT sync worker
#     gunicorn -k gevent serve:app    ← breaks every MCP call you make

_one_at_a_time = threading.Lock()


@app.get("/health")
def health():
    """Is the server awake? A host pings something like this to find out."""
    return jsonify({"status": "ok"})


def _validate(payload):
    """
    Returns (query, wardrobe, wardrobe_label, None) or (query, None, label, message).
    """
    if not isinstance(payload, dict):
        return None, None, None, (
            "Send a JSON object, e.g. "
            '{"query": "vintage graphic tee under $30"}'
        )
    raw = payload.get("query")
    if not isinstance(raw, str) or not raw.strip():
        return None, None, None, (
            "Send JSON with a non-empty string 'query' field, e.g. "
            '{"query": "vintage graphic tee under $30"}'
        )
    query = raw.strip()
    if len(query) > MAX_QUERY_CHARS:
        return query, None, None, (
            f"'query' is {len(query)} characters; the limit is {MAX_QUERY_CHARS}."
        )
    wardrobe = payload.get("wardrobe")
    if wardrobe is None:
        return query, get_example_wardrobe(), "example", None
    if not isinstance(wardrobe, dict) or not isinstance(wardrobe.get("items"), list):
        return query, None, "invalid", (
            "'wardrobe' must be an object with an 'items' list, or be left out."
        )
    return query, wardrobe, f"custom:{len(wardrobe['items'])} items", None


def _outcome(session):
    error = session.get("error")
    if not error:
        return "ok"
    if error.startswith("No listings matched"):
        return "no_results"
    return "model_unavailable"


@app.post("/ask")
def ask():
    """
    Run the agent on one query.

    In:   {"query": "...", "wardrobe": {...}}   wardrobe optional — leave it
                                                out and you get the same
                                                example wardrobe the CLI uses.
    Out:  the session dict from run_agent(), as JSON, plus a `request_id`.
    """
    started = time.perf_counter()
    request_id = uuid.uuid4().hex[:8]
    log = {"request_id": request_id}

    payload = request.get_json(silent=True)
    query, wardrobe, label, problem = _validate(payload)
    log.update(query=query if query is not None else
               (payload.get("query") if isinstance(payload, dict) else None),
               wardrobe=label)

    if problem:
        # 400 rather than a stack trace: the caller can act on this one.
        log_request(**log, status_code=400, outcome="bad_request", error=problem,
                    duration_ms=round((time.perf_counter() - started) * 1000))
        return jsonify({"error": problem, "request_id": request_id}), 400

    # A queued request should look like a queued request.
    if _one_at_a_time.locked():
        print(
            "  [serve] another request is still running. This one is waiting "
            "its turn — serve.py handles one at a time, on purpose.",
            file=sys.stderr,
            flush=True,
        )

    failure = None
    session = None
    wait_started = time.perf_counter()
    with _one_at_a_time:
        queue_wait_ms = round((time.perf_counter() - wait_started) * 1000)
        # Counters in generate.py are process-wide; inside the lock the
        # difference is this run's own spend.
        calls_before = generate.call_count()
        tokens_before = generate.token_counts()
        try:
            session = run_agent(query, wardrobe)
        except Exception as exc:  # noqa: BLE001 — a 500 with a sentence beats a hang
            failure = f"{type(exc).__name__}: {exc}"
        calls = generate.call_count() - calls_before
        tokens_after = generate.token_counts()

    log.update(
        queue_wait_ms=queue_wait_ms,
        model_calls=calls,
        prompt_tokens=tokens_after["prompt"] - tokens_before["prompt"],
        output_tokens=tokens_after["output"] - tokens_before["output"],
    )

    # Outside the lock: building a response is not work the next caller should
    # be waiting on.
    if failure is not None:
        log_request(**log, status_code=500, outcome="server_error", error=failure,
                    duration_ms=round((time.perf_counter() - started) * 1000))
        return jsonify({"error": failure, "request_id": request_id}), 500

    selected = session.get("selected_item") or {}
    log_request(
        **log,
        status_code=200,
        outcome=_outcome(session),
        selected_item=selected.get("id"),
        fit_card=session.get("fit_card"),
        error=session.get("error"),
        duration_ms=round((time.perf_counter() - started) * 1000),
    )
    return jsonify({**session, "request_id": request_id})


if __name__ == "__main__":
    # PORT and 0.0.0.0 are not decoration. A host tells you which port to
    # listen on through PORT, and it reaches your process from outside the
    # container — bind 127.0.0.1 and nothing but the container itself can
    # connect, which looks exactly like a broken app from the browser.
    port = int(os.getenv("PORT", "5000"))

    # Never on by default. Flask's debugger executes code typed into a browser,
    # and a deployed app with it on is a stranger's shell. Set AI201_DEBUG=1 in
    # your own terminal when you want the reloader.
    debug = os.getenv("AI201_DEBUG", "0") == "1"

    print(f"\nFitFindr is listening on http://localhost:{port}")
    print("It runs one request at a time — a second one waits for the first.")
    print("Ask it something (single quotes, as always):\n")
    print(
        f"  curl -X POST http://localhost:{port}/ask \\\n"
        f"    -H 'Content-Type: application/json' \\\n"
        f"    -d '{{\"query\": \"vintage graphic tee under $30\"}}'\n"
    )
    print("Ctrl-C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=debug)
