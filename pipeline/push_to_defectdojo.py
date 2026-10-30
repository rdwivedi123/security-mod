"""Upload a Trivy JSON report to DefectDojo (creates the product and engagement if needed)."""
import argparse, os, datetime, requests

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("report"); ap.add_argument("--product", required=True)
    a = ap.parse_args()
    url, tok = os.environ["DD_URL"].rstrip("/"), os.environ["DD_TOKEN"]
    files = {"file": open(a.report, "rb")}
    data = {"scan_type": "Trivy Scan", "product_name": a.product, "engagement_name": "AppSec POC",
            "auto_create_context": "true", "active": "true", "verified": "false",
            "scan_date": datetime.date.today().isoformat()}
    r = requests.post(f"{url}/api/v2/import-scan/", headers={"Authorization": f"Token {tok}"}, files=files, data=data, timeout=120)
    r.raise_for_status()
    print("Imported:", r.json().get("test"))

if __name__ == "__main__":
    main()
