"""Proposes dependency upgrades as a reviewable change. Never merges, never deploys.
Handles pinned lines in requirements.txt (pkg==version). Other fix types stay human-led."""
import os, re, subprocess, difflib
from packaging.version import Version, InvalidVersion
from . import audit

def _v(s):
    try: return Version(s)
    except InvalidVersion: return Version("0")

def best_target(findings):
    """For each package choose the lowest version that fixes every finding for it."""
    targets = {}
    for f in findings:
        if f["type"] != "dependency" or not f["fixed"]:
            continue
        # a finding may list several fixed versions separated by commas; take the highest
        cand = max((x.strip() for x in f["fixed"].split(",")), key=_v)
        cur = targets.get(f["package"])
        if cur is None or _v(cand) > _v(cur["to"]):
            targets[f["package"]] = {"to": cand, "from": f["installed"], "cves": []}
        targets[f["package"]]["cves"].append(f["cve"])
    for f in findings:
        t = targets.get(f["package"])
        if t and f["cve"] not in t["cves"] and f["fixed"] and _v(t["to"]) >= _v(f["fixed"].split(",")[-1].strip()):
            t["cves"].append(f["cve"])
    return targets

def propose(req_path, targets):
    old = open(req_path).read().splitlines()
    new, changes = [], []
    for line in old:
        m = re.match(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([^\s#;]+)(.*)$", line)
        if m and m.group(1).lower() in targets:
            t = targets[m.group(1).lower()]
            new.append(f"{m.group(1)}=={t['to']}{m.group(3)}")
            changes.append((m.group(1), m.group(2), t["to"], t["cves"]))
        else:
            new.append(line)
    diff = "\n".join(difflib.unified_diff(old, new, req_path, req_path + " (proposed)", lineterm=""))
    return new, changes, diff

def pr_text(app, changes):
    base = "\n".join(f"- {p}: {a} -> {b} (fixes {', '.join(c)})" for p, a, b, c in changes)
    body = f"Automated dependency security update for {app}.\n\n{base}\n\nReview checklist: CI green, re-scan clean, release notes checked for breaking changes. This pull request was proposed by the remediation agent and must be approved by the code owner."
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return body
    try:  # optional AI step: only finding metadata is sent, never source code
        import requests
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=30,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": os.environ.get("AI_MODEL", "claude-sonnet-5-5"), "max_tokens": 600,
                  "messages": [{"role": "user", "content": "Write a concise pull request description for developers. List risk of breaking changes per upgrade and what to test. Changes:\n" + base}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"] + "\n\n" + body.split("\n\n")[-1]
    except Exception as e:
        audit.log("ai_description_failed", error=str(e))
        return body

def run(app, app_cfg, app_dir, findings, apply=False, open_pr=False):
    req = os.path.join(app_dir, "requirements.txt")
    if not app_cfg.get("has_tests", False):
        audit.log("skipped_no_tests", app=app)
        return "Skipped: no automated tests, suggestion-only."
    targets = best_target(findings)
    new, changes, diff = propose(req, targets)
    if not changes:
        return "No automatable dependency fixes."
    audit.log("fix_proposed", app=app, changes=[c[:3] for c in changes])
    if not apply:
        return diff
    branch = "security/auto-fix-" + app
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    open(req, "w").write("\n".join(new) + "\n")
    subprocess.run(["git", "add", req], check=True)
    subprocess.run(["git", "commit", "-m", f"security: upgrade vulnerable dependencies in {app}"], check=True)
    audit.log("committed", branch=branch)
    if open_pr:
        subprocess.run(["git", "push", "-u", "origin", branch], check=True)
        subprocess.run(["gh", "pr", "create", "--title", f"Security: dependency upgrades for {app}",
                        "--body", pr_text(app, changes), "--draft"], check=True)
        audit.log("pr_opened", branch=branch)
    return diff
