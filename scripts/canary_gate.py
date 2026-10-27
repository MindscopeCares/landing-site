#!/usr/bin/env python3
"""Canary health gate for Cloud Run releases.

Soaks a canary revision for N minutes, then decides PASS/FAIL:

1. Synthetic probes: GET <probe-url>/api/health every 15s on the canary's
   tagged URL. Any failure (non-200 or wrong version) fails the gate.
2. Real traffic: Cloud Monitoring request counts for the soak window, split
   by revision and response class. Fails when the canary's 5xx ratio exceeds
   max(2%, 2x the stable revisions' ratio + 0.5pt). Below MIN_REQUESTS of
   canary traffic the comparison is skipped (reported, not failed): small
   user bases often send a 10% slice only a handful of requests.

Exit code 0 = promote, 1 = roll back. Writes a summary to
$GITHUB_STEP_SUMMARY when present. Stdlib only; auth via gcloud.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta

MIN_REQUESTS = 50
PROBE_INTERVAL_S = 15


def token() -> str:
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


def probe(url: str, expect_version: str) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url.rstrip('/') + "/health", timeout=10) as r:
            if r.status != 200:
                return False, f"HTTP {r.status}"
            raw = r.read().decode()
        if os.environ.get("VERSION_PATH"):
            with urllib.request.urlopen(url.rstrip('/') + os.environ["VERSION_PATH"], timeout=10) as r:
                version = r.read().decode().strip()
        else:
            version = str(json.loads(raw).get("version", ""))
        if expect_version and version != expect_version:
            return False, f"version {version!r} != {expect_version!r}"
            return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:200]


def request_counts(project: str, service: str, start: datetime, end: datetime) -> dict[str, dict[str, int]]:
    """{revision: {response_code_class: count}} for the window."""
    flt = (
        'metric.type="run.googleapis.com/request_count" '
        'AND resource.type="cloud_run_revision" '
        f'AND resource.labels.service_name="{service}"'
    )
    seconds = max(60, int((end - start).total_seconds()))
    params = [
        ("filter", flt),
        ("interval.startTime", start.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("interval.endTime", end.strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("aggregation.alignmentPeriod", f"{seconds}s"),
        ("aggregation.perSeriesAligner", "ALIGN_DELTA"),
        ("aggregation.crossSeriesReducer", "REDUCE_SUM"),
        ("aggregation.groupByFields", "resource.labels.revision_name"),
        ("aggregation.groupByFields", "metric.labels.response_code_class"),
    ]
    url = f"https://monitoring.googleapis.com/v3/projects/{project}/timeSeries?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token()}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    out: dict[str, dict[str, int]] = {}
    for ts in data.get("timeSeries", []):
        rev = ts["resource"]["labels"]["revision_name"]
        cls = ts["metric"]["labels"].get("response_code_class", "?")
        total = sum(int(p["value"].get("int64Value", 0)) for p in ts.get("points", []))
        out.setdefault(rev, {}).setdefault(cls, 0)
        out[rev][cls] += total
    return out


def ratio_5xx(counts: dict[str, int]) -> tuple[int, float]:
    total = sum(counts.values())
    return total, (counts.get("5xx", 0) / total if total else 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--service", required=True)
    ap.add_argument("--revision", required=True, help="canary revision name")
    ap.add_argument("--probe-url", required=True, help="canary tagged URL")
    ap.add_argument("--expect-version", default="", help="substring of /api/health version, e.g. the short SHA")
    ap.add_argument("--minutes", type=float, default=10)
    args = ap.parse_args()

    start = datetime.now(UTC)
    deadline = time.monotonic() + args.minutes * 60
    probes = failures = 0
    last_err = ""
    while True:
        ok, msg = probe(args.probe_url, args.expect_version)
        probes += 1
        if not ok:
            failures += 1
            last_err = msg
            print(f"probe FAILED: {msg}", flush=True)
        if time.monotonic() >= deadline:
            break
        time.sleep(PROBE_INTERVAL_S)
    end = datetime.now(UTC)

    reasons: list[str] = []
    notes: list[str] = []
    if failures:
        reasons.append(f"{failures}/{probes} health probes failed (last: {last_err})")

    try:
        # Monitoring lags ~2-3 minutes; widen the window's end accordingly.
        time.sleep(90)
        counts = request_counts(args.project, args.service, start - timedelta(minutes=1), datetime.now(UTC))
        canary = counts.get(args.revision, {})
        stable: dict[str, int] = {}
        for rev, c in counts.items():
            if rev != args.revision:
                for k, v in c.items():
                    stable[k] = stable.get(k, 0) + v
        c_total, c_ratio = ratio_5xx(canary)
        s_total, s_ratio = ratio_5xx(stable)
        notes.append(f"canary: {c_total} requests, 5xx {c_ratio:.2%}; stable: {s_total} requests, 5xx {s_ratio:.2%}")
        threshold = max(0.02, 2 * s_ratio + 0.005)
        if c_total < MIN_REQUESTS:
            notes.append(f"canary traffic below {MIN_REQUESTS} requests; error-rate comparison skipped")
        elif c_ratio > threshold:
            reasons.append(f"canary 5xx ratio {c_ratio:.2%} > threshold {threshold:.2%}")
    except Exception as e:  # noqa: BLE001
        reasons.append(f"monitoring query failed ({str(e)[:200]}); promotion refused")

    verdict = "FAIL" if reasons else "PASS"
    lines = [f"### Canary gate: {verdict}", f"- revision `{args.revision}`, soak {args.minutes:g} min, {probes} probes"]
    lines += [f"- {n}" for n in notes] + [f"- **{r}**" for r in reasons]
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(report + "\n")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
