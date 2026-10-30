"""Convert scanner output into one common finding format.
Add an adapter per scanner; every adapter returns a list of Finding dicts."""
import json

def from_trivy(path, app):
    data = json.load(open(path))
    out = []
    for res in data.get("Results", []):
        for v in res.get("Vulnerabilities") or []:
            out.append({
                "id": f'{v["VulnerabilityID"]}:{v["PkgName"]}',
                "app": app,
                "source": "trivy",
                "type": "dependency",
                "file": res.get("Target", ""),
                "package": v["PkgName"],
                "installed": v["InstalledVersion"],
                "fixed": v.get("FixedVersion") or "",
                "severity": v.get("Severity", "UNKNOWN").upper(),
                "title": v.get("Title", v["VulnerabilityID"]),
                "cve": v["VulnerabilityID"],
            })
    return dedupe(out)

def dedupe(findings):
    seen, out = set(), []
    for f in findings:
        if f["id"] not in seen:
            seen.add(f["id"]); out.append(f)
    return out
