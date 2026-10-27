import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ReleaseTests(unittest.TestCase):
    def test_requires_successful_exact_main_commit(self):
        staging = load("require_staging")
        for rows, expected in [([], False), ([{"head_sha": "other", "conclusion": "success", "head_branch": "main"}], False), ([{"head_sha": "abc", "conclusion": "failure", "head_branch": "main"}], False), ([{"head_sha": "abc", "conclusion": "success", "head_branch": "feature"}], False), ([{"head_sha": "abc", "conclusion": "success", "head_branch": "main"}], True)]:
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": "org/repo"}), patch.object(staging.subprocess, "check_output", return_value=json.dumps({"workflow_runs": rows})):
                self.assertEqual(staging.passed_staging("abc"), expected)

    def test_unreviewed_or_direct_push_rejected(self):
        policy = load("release_policy")
        with patch.object(policy, "gh", return_value=[]):
            self.assertIn("direct push", policy.check_commit("org/repo", "abc", True)[0])
        pr = {"number": 1, "merged_at": "now", "head": {"sha": "abc"}, "base": {"ref": "main"}, "merge_commit_sha": "abc"}
        with patch.object(policy, "gh", side_effect=[[pr], {"check_runs": [{"conclusion": "success"}]}, {"check_runs": []}, []]):
            self.assertIn("approval", policy.check_commit("org/repo", "abc", True)[0])

    def test_canary_network_failure_rejects_promotion(self):
        gate = load("canary_gate")
        with patch.object(gate.urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertFalse(gate.probe("https://preview.invalid", "abc")[0])

    def test_first_release_fails_without_a_deployed_baseline(self):
        policy = load("release_policy")
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            policy.commits_in_range("abc")
