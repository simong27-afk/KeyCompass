#!/usr/bin/env python3
"""Read-only Google Search Console access for keycompass.co.uk.

First time, on your Mac (opens a browser to sign in):
    python3 tools/gsc.py auth

Then, from anywhere with network access to Google's APIs:
    python3 tools/gsc.py check                      # confirm access, list properties
    python3 tools/gsc.py queries [days]             # top search queries
    python3 tools/gsc.py pages [days]               # top pages
    python3 tools/gsc.py inspect /guides/crypto-scams-uk   # indexing status of one URL
    python3 tools/gsc.py sitemaps                   # submitted sitemaps and their status

Credentials stay in .secrets/ (git-ignored). The scope is read-only: this script
cannot change anything in Search Console.
"""
import json, os, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, ".secrets")
CLIENT = os.path.join(SECRETS, "gsc-client.json")
TOKEN = os.path.join(SECRETS, "gsc-token.json")
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
SITE_CANDIDATES = ["https://keycompass.co.uk/", "sc-domain:keycompass.co.uk"]

def need(mod, pkg):
    try:
        return __import__(mod)
    except ImportError:
        sys.exit(f"Missing library. Run: python3 -m pip install --user {pkg}")

def auth():
    need("google_auth_oauthlib", "google-auth-oauthlib google-api-python-client")
    from google_auth_oauthlib.flow import InstalledAppFlow
    if not os.path.exists(CLIENT):
        sys.exit(f"Put the downloaded OAuth client file at {CLIENT} first.")
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    os.makedirs(SECRETS, exist_ok=True)
    with open(TOKEN, "w") as f:
        f.write(creds.to_json())
    os.chmod(TOKEN, 0o600)
    print("Signed in. Token saved to .secrets/gsc-token.json (never share or commit it).")

def service():
    need("googleapiclient", "google-api-python-client google-auth")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    if not os.path.exists(TOKEN):
        sys.exit("Not signed in yet. On your Mac run: python3 tools/gsc.py auth")
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)

def site(svc):
    have = [s["siteUrl"] for s in svc.sites().list().execute().get("siteEntry", [])]
    for c in SITE_CANDIDATES:
        if c in have:
            return c
    sys.exit(f"No keycompass.co.uk property for this account. It can see: {have or 'nothing'}")

def report(dimension, days):
    svc = service(); s = site(svc)
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=days - 1)
    body = {"startDate": str(start), "endDate": str(end), "dimensions": [dimension], "rowLimit": 50}
    rows = svc.searchanalytics().query(siteUrl=s, body=body).execute().get("rows", [])
    print(f"{dimension} for {s}, {start} to {end}")
    print(f"{'clicks':>6} {'impr':>6} {'ctr':>6} {'pos':>5}  {dimension}")
    for r in rows:
        print(f"{r['clicks']:>6.0f} {r['impressions']:>6.0f} {r['ctr']*100:>5.1f}% {r['position']:>5.1f}  {r['keys'][0]}")
    if not rows:
        print("(no data for this period)")

def inspect(path):
    svc = service(); s = site(svc)
    url = path if path.startswith("http") else "https://keycompass.co.uk" + ("" if path.startswith("/") else "/") + path
    res = svc.urlInspection().index().inspect(body={"inspectionUrl": url, "siteUrl": s}).execute()
    r = res.get("inspectionResult", {}).get("indexStatusResult", {})
    for k in ("verdict", "coverageState", "lastCrawlTime", "googleCanonical", "pageFetchState", "robotsTxtState"):
        print(f"{k}: {r.get(k)}")

def sitemaps():
    svc = service(); s = site(svc)
    for m in svc.sitemaps().list(siteUrl=s).execute().get("sitemap", []):
        print(m.get("path"), "| last downloaded:", m.get("lastDownloaded"), "| errors:", m.get("errors"), "| warnings:", m.get("warnings"))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "auth": auth()
    elif cmd == "check":
        svc = service(); print("Properties:", [x["siteUrl"] for x in svc.sites().list().execute().get("siteEntry", [])]); print("Using:", site(svc))
    elif cmd == "queries": report("query", int(arg or 28))
    elif cmd == "pages": report("page", int(arg or 28))
    elif cmd == "inspect": inspect(arg or "/")
    elif cmd == "sitemaps": sitemaps()
    else: sys.exit(__doc__)
