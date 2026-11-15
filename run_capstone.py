"""
Run the capstone trials against a freshly started serve.py.   ← CAPSTONE

    python run_capstone.py --label before --trials 3

One trial = 10 matching + 5 impossible + 6 malformed requests (see criteria.md),
then a read-back of logs/requests.jsonl. Writes results/capstone_<label>.json
(every request and its verdicts) and results/capstone_<label>.md (the table).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import request_log
from request_log import FIELDS

ROOT = Path(__file__).parent
PORT = 5100
BASE = f"http://127.0.0.1:{PORT}"
MATCH = "vintage graphic tee under $30"
IMPOSSIBLE = "designer ballgown size XXS under $5"
MALFORMED = [
    b"not json",
    b"[1,2]",
    json.dumps({"query": 5}).encode(),
    json.dumps({"query": ""}).encode(),
    json.dumps({"query": "x" * 400}).encode(),
    json.dumps({"query": "tee", "wardrobe": "nope"}).encode(),
]


def post(body: bytes):
    req = urllib.request.Request(BASE + "/ask", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw.decode("utf-8", "replace")[:200]}


def start_server():
    env = dict(os.environ, AI201_CACHE="0", PORT=str(PORT))
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    proc = subprocess.Popen([str(py if py.exists() else sys.executable), "serve.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(BASE + "/health", timeout=2).read()
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    raise RuntimeError("server did not start")


def trial():
    sent = []  # (kind, status, response)
    for _ in range(10):
        sent.append(("match", *post(json.dumps({"query": MATCH}).encode())))
    for _ in range(5):
        sent.append(("impossible", *post(json.dumps({"query": IMPOSSIBLE}).encode())))
    for body in MALFORMED:
        sent.append(("malformed", *post(body)))
    log = {r["request_id"]: r for r in request_log.read_log()}

    c1 = c2 = c3 = c4 = c5 = 0
    detail = []
    for kind, status, resp in sent:
        rec = log.get(resp.get("request_id"))
        ok1 = bool(rec) and all(f in rec for f in FIELDS)
        c1 += ok1
        row = {"kind": kind, "status": status, "request_id": resp.get("request_id"), "logged_complete": ok1,
               "duration_ms": (rec or {}).get("duration_ms")}
        if kind == "malformed":
            ok2 = status == 400 and bool(resp.get("error")) and (rec or {}).get("outcome") == "bad_request"
            c2 += ok2; row["c2"] = ok2
        elif kind == "match":
            ok3 = bool(rec) and (rec.get("model_calls") or 0) >= 2 and (rec.get("prompt_tokens") or 0) > 0 \
                and (rec.get("output_tokens") or 0) > 0
            ok4 = bool(rec) and (rec.get("duration_ms") or 10**9) < 6000
            ok5 = status == 200 and resp.get("error") is None and bool(resp.get("fit_card")) \
                and bool(resp.get("selected_item"))
            c3 += ok3; c4 += ok4; c5 += ok5
            row.update(c3=ok3, c4=ok4, c5=ok5, model_calls=rec and rec.get("model_calls"))
        else:
            ok3 = bool(rec) and rec.get("model_calls") == 0 and rec.get("prompt_tokens") == 0 \
                and rec.get("output_tokens") == 0
            ok5 = status == 200 and resp.get("fit_card") is None and "broader description" in (resp.get("error") or "")
            c3 += ok3; c5 += ok5
            row.update(c3=ok3, c5=ok5)
        detail.append(row)
    return {"c1": f"{c1}/21", "c2": f"{c2}/6", "c3": f"{c3}/15", "c4": f"{c4}/10", "c5": f"{c5}/15",
            "n": [c1, c2, c3, c4, c5], "detail": detail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--trials", type=int, default=3)
    args = ap.parse_args()
    results = []
    for i in range(args.trials):
        proc = start_server()
        try:
            t0 = time.time()
            r = trial()
            r["trial_seconds"] = round(time.time() - t0)
        finally:
            proc.kill()
        results.append(r)
        print(f"trial {i+1}: c1 {r['c1']}  c2 {r['c2']}  c3 {r['c3']}  c4 {r['c4']}  c5 {r['c5']}  ({r['trial_seconds']}s)", flush=True)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"capstone_{args.label}.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    names = ["1. Every request has a complete log record (21)", "2. Malformed input gets 400, logged (6)",
             "3. Cost fields right for paid and free runs (15)", "4. Matching run under 6000 ms (10)",
             "5. Original agent still works (15)"]
    lines = ["| Criterion | " + " | ".join(f"Run {i+1}" for i in range(len(results))) + " |",
             "|---|" + "---|" * len(results)]
    for k, name in enumerate(names):
        lines.append(f"| {name} | " + " | ".join(r[f"c{k+1}"] for r in results) + " |")
    (ROOT / "results" / f"capstone_{args.label}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
