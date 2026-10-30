import argparse, yaml
from . import normalise, prioritise, fix_agent, audit

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", required=True)
    ap.add_argument("--app", required=True, help="path to the application folder")
    ap.add_argument("--name", help="application name in config/apps.yaml (default: folder name)")
    ap.add_argument("--config", default="config/apps.yaml")
    ap.add_argument("--apply", action="store_true", help="commit to a new branch (default is dry-run)")
    ap.add_argument("--open-pr", action="store_true", help="push and open a DRAFT pull request")
    a = ap.parse_args()
    name = a.name or a.app.rstrip("/").split("/")[-1]
    cfg = yaml.safe_load(open(a.config))["apps"][name]
    findings = prioritise.rank(normalise.from_trivy(a.scan, name), cfg)
    audit.log("scan_loaded", app=name, findings=len(findings))
    print(f"{len(findings)} findings for {name} (exposure={cfg['exposure']}, criticality={cfg['criticality']})\n")
    print(f"{'SCORE':<6}{'SEV':<10}{'PACKAGE':<10}{'FIX':<8}ID")
    for f in findings:
        print(f"{f['score']:<6}{f['severity']:<10}{f['package']:<10}{f['fixed'] or '-':<8}{f['cve']}")
    print("\nProposed change:\n")
    print(fix_agent.run(name, cfg, a.app, findings, a.apply, a.open_pr))

if __name__ == "__main__":
    main()
