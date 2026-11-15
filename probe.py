"""
Send requests to a running serve.py and summarise what the log recorded.  ← CAPSTONE

    python serve.py                                   (other terminal; AI201_CACHE=0 for real costs)
    python probe.py --n 10 --query 'vintage graphic tee under $30'
    python probe.py --raw '{"query": 5}'              send a deliberately bad body

Every request's numbers come from the server's own log record (matched by the
request_id the server returns), not from a stopwatch on this side.
"""
import argparse
import json
import statistics
import time
import urllib.error
import urllib.request

import request_log


def post(url, body: bytes):
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read()), time.perf_counter() - started
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), time.perf_counter() - started


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:5000/ask")
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--query", default="vintage graphic tee under $30")
    ap.add_argument("--raw", help="send this string as the request body instead of a query")
    args = ap.parse_args()

    body = args.raw.encode() if args.raw is not None else json.dumps({"query": args.query}).encode()
    by_id = {r["request_id"]: r for r in request_log.read_log()}
    rows = []
    for i in range(args.n):
        status, data, secs = post(args.url, body)
        rid = data.get("request_id")
        rec = {r["request_id"]: r for r in request_log.read_log()}.get(rid)
        rows.append((status, secs, rec))
        print(f"{i+1:>2}. HTTP {status}  client {secs*1000:7.0f} ms  "
              f"logged: {'yes' if rec else 'NO'}  "
              f"{(rec or {}).get('outcome')}  calls={(rec or {}).get('model_calls')}  "
              f"tokens={(rec or {}).get('prompt_tokens')}+{(rec or {}).get('output_tokens')}")

    recs = [r for _, _, r in rows if r]
    print(f"\n{len(recs)}/{len(rows)} requests have a log record")
    ms = [r["duration_ms"] for r in recs if r.get("duration_ms") is not None]
    if ms:
        print(f"duration_ms  mean {statistics.mean(ms):.0f}  min {min(ms)}  max {max(ms)}")
    paid = [r for r in recs if r.get("model_calls")]
    if paid:
        print(f"model_calls  mean {statistics.mean(r['model_calls'] for r in paid):.1f}   "
              f"prompt_tokens mean {statistics.mean(r['prompt_tokens'] for r in paid):.0f}   "
              f"output_tokens mean {statistics.mean(r['output_tokens'] for r in paid):.0f}")


if __name__ == "__main__":
    main()
