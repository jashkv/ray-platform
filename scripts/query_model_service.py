#!/usr/bin/env python3
"""
CLI Test Client for Corporate Revenue Prediction Model Deployment.
Sends inference queries for unforeseen companies to the running Ray Serve / FastAPI service.
"""

import sys
import json
import argparse
import urllib.request
import urllib.error

DEFAULT_SERVICE_URL = "http://localhost:8000"

SAMPLE_UNFORESEEN_COMPANIES = [
    {
        "company_name": "Valence BioSystems GmbH",
        "employee_count": 180,
        "founded_year": 2014,
        "industry_sector": "Healthcare",
        "country": "DE"
    },
    {
        "company_name": "Hyperion Cloud Solutions Inc",
        "employee_count": 850,
        "founded_year": 2008,
        "industry_sector": "Technology",
        "country": "US"
    },
    {
        "company_name": "Nordic Precision Robotics A/S",
        "employee_count": 45,
        "founded_year": 2021,
        "industry_sector": "Manufacturing",
        "country": "NL"
    },
    {
        "company_name": "Summit Petrochemical Logistics Ltd",
        "employee_count": 1200,
        "founded_year": 1985,
        "industry_sector": "Energy",
        "country": "GB"
    }
]

def query_prediction(url: str, payload: dict) -> dict:
    req_url = f"{url.rstrip('/')}/predict"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        req_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Error querying prediction service at {req_url}: {e}", file=sys.stderr)
        return {"error": str(e)}

def query_health(url: str) -> dict:
    req_url = f"{url.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(req_url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Query Corporate Revenue Prediction Model")
    parser.add_argument("--url", default=DEFAULT_SERVICE_URL, help="Model service endpoint")
    parser.add_argument("--health", action="store_true", help="Check health status only")
    parser.add_argument("--name", help="Company name")
    parser.add_argument("--employees", type=int, help="Employee headcount")
    parser.add_argument("--year", type=int, default=2015, help="Founded year")
    parser.add_argument("--sector", default="Technology", help="Industry sector")
    parser.add_argument("--country", default="US", help="Country code")
    args = parser.parse_args()

    if args.health:
        print(json.dumps(query_health(args.url), indent=2))
        return

    if args.name and args.employees:
        payload = {
            "company_name": args.name,
            "employee_count": args.employees,
            "founded_year": args.year,
            "industry_sector": args.sector,
            "country": args.country
        }
        print(f"\nQuerying prediction for unforeseen company: {args.name}")
        res = query_prediction(args.url, payload)
        print(json.dumps(res, indent=2))
    else:
        print("=" * 70)
        print("Running batch inference for 4 unforeseen enterprise samples:")
        print("=" * 70)
        for comp in SAMPLE_UNFORESEEN_COMPANIES:
            res = query_prediction(args.url, comp)
            print(f"\nCompany:  {comp['company_name']} ({comp['country']} | {comp['industry_sector']})")
            print(f"Headcount: {comp['employee_count']} employees | Founded: {comp['founded_year']}")
            if "predicted_revenue_formatted" in res:
                print(f"Predicted Revenue: {res['predicted_revenue_formatted']} (Tier: {res.get('firm_size_tier')})")
            else:
                print(f"Response: {res}")
        print("=" * 70)

if __name__ == "__main__":
    main()
