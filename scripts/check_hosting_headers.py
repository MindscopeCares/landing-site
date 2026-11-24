"""Fail if the Firebase Hosting config for the main site drops a security header."""
import json
import sys

REQUIRED = {"x-content-type-options", "referrer-policy", "strict-transport-security",
            "x-frame-options", "content-security-policy", "permissions-policy"}

config = json.load(open(sys.argv[1]))
site = next(h for h in config["hosting"] if h.get("target") == "mindscopecares")
everywhere = next((r for r in site.get("headers", []) if r.get("source") == "**"), {"headers": []})
have = {h["key"].lower() for h in everywhere["headers"]}
missing = sorted(REQUIRED - have)
if missing:
    sys.exit(f"Security headers missing from firebase.json: {', '.join(missing)}")
print("All security headers present")
