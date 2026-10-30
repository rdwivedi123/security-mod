"""Illustrative risk score. Tune weights with the client AppSec team after the baseline.
score = severity weight x exposure x criticality (+ small bonus when a fix exists)."""
SEV = {"CRITICAL": 10, "HIGH": 7, "MEDIUM": 4, "LOW": 1, "UNKNOWN": 2}
EXPOSURE = {"internet": 1.5, "internal": 1.0}
CRIT = {"high": 1.3, "medium": 1.0, "low": 0.8}

def score(f, app_cfg):
    s = SEV.get(f["severity"], 2)
    s *= EXPOSURE.get(app_cfg.get("exposure", "internal"), 1.0)
    s *= CRIT.get(app_cfg.get("criticality", "medium"), 1.0)
    if f.get("fixed"):
        s += 0.5
    return round(s, 1)

def rank(findings, app_cfg):
    for f in findings:
        f["score"] = score(f, app_cfg)
    return sorted(findings, key=lambda f: f["score"], reverse=True)
