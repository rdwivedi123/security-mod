# AppSec Remediation POC Kit

Scan -> consolidate -> prioritise -> AI-assisted fix pull request -> validate.
Guardrails: dry-run by default, the agent can only open pull requests, it has no merge or deploy rights, every action is written to `out/audit.log`.

## What is in the kit
| Path | Purpose |
|---|---|
| `scripts/setup_defectdojo.sh` | Starts DefectDojo (single source of truth) from the official repo with Docker |
| `.github/workflows/scan.yml` | CI: Trivy scan, then pipeline, then fix pull request (manual approval step) |
| `pipeline/normalise.py` | Trivy JSON -> one common finding format (add more scanners as adapters) |
| `pipeline/prioritise.py` | Ranks findings using severity, exposure, criticality, fix availability |
| `pipeline/fix_agent.py` | Proposes dependency upgrades; optional AI-written PR description |
| `pipeline/push_to_defectdojo.py` | Uploads scan results to DefectDojo |
| `config/apps.yaml` | Application register: owner, exposure, criticality (fill in with client) |
| `sample-app/` | Deliberately outdated app used for the demo |
| `sample-data/` | Synthetic scan output (IDs are fake) so the POC runs without any scanner |

## 1. Quick local demo (no network, no scanner needed)
```bash
pip install -r requirements.txt
python -m pipeline.run --scan sample-data/trivy-sample.json --app sample-app
```
Prints the ranked list and the proposed fixes as a diff. Nothing is changed.

## 2. Real scan on the sample app
```bash
trivy fs --format json --output out/trivy.json sample-app
python -m pipeline.run --scan out/trivy.json --app sample-app
```

## 3. Single source of truth (DefectDojo)
```bash
bash scripts/setup_defectdojo.sh          # then open http://localhost:8080
export DD_URL=http://localhost:8080 DD_TOKEN=<api token from your profile>
python -m pipeline.push_to_defectdojo out/trivy.json --product "sample-app"
```

## 4. Open a fix pull request (human reviews and merges)
```bash
python -m pipeline.run --scan out/trivy.json --app sample-app --apply --open-pr
```
Needs a git repo with a remote and the GitHub CLI (`gh auth login`). Optional AI-written PR text: `export ANTHROPIC_API_KEY=...` (model via `AI_MODEL`, default `claude-sonnet-5-5`). Without a key a template description is used. Only finding metadata is sent to the model, not source code.

## 5. Tests
```bash
python -m pytest -q
```

## Before the client POC starts
- Fill `config/apps.yaml` for the 3 to 5 shortlisted applications.
- Confirm the approved AI service and data-handling policy with client security.
- Branch protection on the client repos: pull request reviews required, tests required, no bypass for the agent.
- Prioritisation weights in `prioritise.py` are illustrative. Tune them with the client's AppSec team after the baseline.
- Extend `normalise.py` with adapters for the client's scanners (SAST, secrets, container).
