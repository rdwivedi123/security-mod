from pipeline import normalise, prioritise, fix_agent
CFG = {"exposure": "internet", "criticality": "high", "has_tests": True}
def load(): return normalise.from_trivy("sample-data/trivy-sample.json", "sample-app")

def test_normalise_and_dedupe():
    f = load(); assert len(f) == 5 and len({x["id"] for x in f}) == 5

def test_ranking_puts_critical_first():
    r = prioritise.rank(load(), CFG); assert r[0]["severity"] == "CRITICAL"
    assert r[-1]["severity"] == "LOW"

def test_exposure_raises_score():
    f = load()[0]
    assert prioritise.score(f, {"exposure": "internet"}) > prioritise.score(f, {"exposure": "internal"})

def test_picks_highest_fixing_version_per_package():
    t = fix_agent.best_target(load())
    assert t["pyyaml"]["to"] == "6.0.1" and set(t["pyyaml"]["cves"]) == {"CVE-SAMPLE-0003", "CVE-SAMPLE-0004"}
    assert "jinja2" not in t   # no fix available -> stays with humans

def test_dry_run_changes_nothing():
    before = open("sample-app/requirements.txt").read()
    out = fix_agent.run("sample-app", CFG, "sample-app", prioritise.rank(load(), CFG))
    assert "pyyaml==6.0.1" in out and open("sample-app/requirements.txt").read() == before

def test_no_tests_means_suggestion_only():
    out = fix_agent.run("sample-app", {**CFG, "has_tests": False}, "sample-app", load())
    assert out.startswith("Skipped")
