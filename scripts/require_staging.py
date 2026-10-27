"""Reject targets without a successful staging deployment, including pagination."""
import json
import os
import subprocess
import sys

def passed_staging(sha):
    repo = os.environ["GITHUB_REPOSITORY"]
    endpoint = f"repos/{repo}/actions/workflows/deploy-staging.yml/runs?head_sha={sha}&status=success&event=push&branch=main&per_page=100"
    data = json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))
    return any(run["head_sha"] == sha and run["conclusion"] == "success" and run["head_branch"] == "main" for run in data["workflow_runs"])

if __name__ == "__main__":
    if not passed_staging(sys.argv[1]):
        raise SystemExit("Target has not passed Deploy staging on main; production promotion refused")
