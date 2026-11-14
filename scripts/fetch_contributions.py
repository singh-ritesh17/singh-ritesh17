#!/usr/bin/env python3
"""Pulls the last 365 days of contributions into data/contributions.json."""
import json, os, sys, urllib.request, datetime as dt
from pathlib import Path

USER = os.environ.get("GH_USER", "singh-ritesh17")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
QUERY = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions
weeks{contributionDays{date contributionCount}}}}}}"""

if not TOKEN:
    sys.exit("No GH_TOKEN / GITHUB_TOKEN set; keeping the existing data file.")

now = dt.datetime.now(dt.timezone.utc)
vars_ = {"login": USER,
         "from": (now - dt.timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z"),
         "to": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
req = urllib.request.Request("https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": vars_}).encode(),
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
res = json.load(urllib.request.urlopen(req, timeout=30))
if "errors" in res or not res.get("data", {}).get("user"):
    sys.exit(f"GraphQL error: {res}")
cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [{"date": d["date"], "count": d["contributionCount"]}
        for w in cal["weeks"] for d in w["contributionDays"]]
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps({"login": USER, "total": cal["totalContributions"], "days": days}))
print("saved", len(days), "days,", cal["totalContributions"], "contributions")
