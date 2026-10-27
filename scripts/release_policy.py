#!/usr/bin/env python3
"""Release policy gate: enforces the merge process at ship time.

GitHub's Free plan can't block merges into a private repo's `main`, so the
rules are enforced where they matter, before production. For every commit in
(last release tag, target SHA] this checks that:

  1. the commit arrived through a merged pull request (no direct pushes),
  2. that PR's head passed CI (`ci-ok` succeeded), and
  3. when REQUIRE_APPROVAL=true, the PR's approval-gate check passed (a
     required reviewer, e.g. @AJEgwu, approved; see approval-gate.yml).

Any violation fails the release, listing the offending commits. Pass
--report-only to print violations without failing (used by main-guard.yml to
flag a bad merge the moment it lands).

Needs GH_TOKEN and GITHUB_REPOSITORY; uses the gh CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def gh(*args: str) -> object:
    out = subprocess.check_output(["gh", "api", *args], text=True)
    return json.loads(out) if out.strip() else None


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def commits_in_range(target: str) -> list[str]:
    # Use the currently serving revision, not a tag that may have been cut
    # for a failed release. Legacy services need an explicit first baseline.
    baseline = os.environ.get("RELEASE_BASELINE_SHA", "")
    if not baseline:
        raise SystemExit("Set RELEASE_BASELINE_SHA to the currently deployed full commit for the first promotion")
    baseline = git("rev-parse", "--verify", "--end-of-options", baseline + "^{commit}")
    subprocess.check_call(["git", "merge-base", "--is-ancestor", baseline, target])
    commits = git("rev-list", "--first-parent", f"{baseline}..{target}").split()
    if not commits:
        raise SystemExit("No new commits to release")
    return commits


EXCEPTION_LABEL = "cto-approved"


def approved_after_merge(repo: str, num: int) -> bool:
    """Break-glass: a required reviewer added the cto-approved label to the PR."""
    required = {r.strip().lower() for r in os.environ.get("REQUIRED_REVIEWERS", "AJEgwu").split(",") if r.strip()}
    events = gh(f"repos/{repo}/issues/{num}/events?per_page=100") or []
    return any(
        e.get("event") == "labeled"
        and e.get("label", {}).get("name") == EXCEPTION_LABEL
        and (e.get("actor") or {}).get("login", "").lower() in required
        for e in events
    )


def check_commit(repo: str, sha: str, require_approval: bool) -> list[str]:
    problems: list[str] = []
    pulls = [p for p in gh(f"repos/{repo}/commits/{sha}/pulls") or [] if p.get("merged_at")]
    if not pulls:
        return [f"{sha[:7]}: not merged through a pull request (direct push to main)"]
    pr = next((pull for pull in pulls if pull["base"]["ref"] == "main" and pull.get("merge_commit_sha") == sha), None)
    if not pr:
        return [f"{sha[:7]}: no matching merged PR into main"]
    num = pr["number"]
    head = pr["head"]["sha"]
    runs = gh(f"repos/{repo}/commits/{head}/check-runs?check_name=ci-ok&per_page=20")
    checks = (runs or {}).get("check_runs", [])
    latest_ci = max(checks, key=lambda run: run.get("id", 0), default=None)
    if latest_ci is None or latest_ci["conclusion"] != "success":
        problems.append(f"{sha[:7]} (PR #{num}): merged without a passing ci-ok check")
    if require_approval:
        # The approval-gate workflow encodes who must approve (REQUIRED_REVIEWERS);
        # its latest run on the merged head must have passed.
        gate = gh(f"repos/{repo}/commits/{head}/check-runs?check_name=approval-gate&per_page=50")
        runs = sorted((gate or {}).get("check_runs", []), key=lambda r: r.get("id", 0))
        if (not runs or runs[-1]["conclusion"] != "success") and not approved_after_merge(repo, num):
            problems.append(
                f"{sha[:7]} (PR #{num}): merged without the required approval (approval-gate). "
                f"A required reviewer can approve it after the fact by adding the `{EXCEPTION_LABEL}` label."
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="commit SHA being released or pushed")
    ap.add_argument("--commits", nargs="*", help="explicit commits to check (default: since last release)")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    repo = os.environ["GITHUB_REPOSITORY"]
    require_approval = os.environ.get("REQUIRE_APPROVAL", "false").lower() == "true"
    commits = args.commits or commits_in_range(args.target)

    problems: list[str] = []
    for sha in commits:
        problems += check_commit(repo, sha, require_approval)

    lines = [f"### Release policy: {'FAIL' if problems else 'PASS'}",
             f"- {len(commits)} commit(s) checked; approvals {'required' if require_approval else 'not required'}"]
    lines += [f"- **{p}**" for p in problems]
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(report + "\n")
    if problems and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write("violations<<EOF\n" + "\n".join(problems) + "\nEOF\n")
    return 1 if problems and not args.report_only else 0


if __name__ == "__main__":
    sys.exit(main())
