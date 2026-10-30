"""Import a Qualys report into DefectDojo, the single source of truth for findings.

Export the report from Qualys (XML or CSV) and run this on your own machine or a private runner.
Qualys reports contain client data: never commit one to this repository.

Needs DD_URL and DD_TOKEN in the environment.
"""
import argparse
import datetime
import os

import requests

# The names below must match entries in DefectDojo's scan-type list
# (Findings > Import Scan Results); pass --scan-type to use another one.
DEFAULT_SCAN_TYPE = "Qualys Scan"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", help="path to the Qualys report export")
    ap.add_argument("--product", required=True)
    ap.add_argument("--engagement", default="AppSec POC")
    ap.add_argument("--scan-type", default=DEFAULT_SCAN_TYPE)
    a = ap.parse_args()

    url, tok = os.environ["DD_URL"].rstrip("/"), os.environ["DD_TOKEN"]
    data = {
        "scan_type": a.scan_type,
        "product_name": a.product,
        "engagement_name": a.engagement,
        "auto_create_context": "true",
        "active": "true",
        "verified": "false",
        "scan_date": datetime.date.today().isoformat(),
    }
    with open(a.report, "rb") as fh:
        r = requests.post(
            f"{url}/api/v2/import-scan/",
            headers={"Authorization": f"Token {tok}"},
            files={"file": fh},
            data=data,
            timeout=300,
        )
    r.raise_for_status()
    print("Imported:", r.json().get("test"))


if __name__ == "__main__":
    main()
