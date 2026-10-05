#!/usr/bin/env python3
"""Tell Bing (and every other IndexNow search engine) that pages have changed.

Run this AFTER a change has been pushed and Netlify has finished deploying:

    python3 tools/indexnow.py            # submit every URL in sitemap.xml
    python3 tools/indexnow.py /pricing   # submit just these paths

IndexNow is how a new or updated page reaches Bing within hours instead of waiting
for the next crawl, and ChatGPT search leans heavily on Bing's index. The key is
public by design: search engines confirm it by fetching /<key>.txt from the site.
"""
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "keycompass.co.uk"
SITE = "https://" + HOST
KEY = "98fca7124cf786079f30464b08afe901"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    text = io.open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    return re.findall(r"<loc>([^<]+)</loc>", text)


def main(argv):
    if not os.path.exists(os.path.join(ROOT, KEY + ".txt")):
        sys.exit("Key file %s.txt is missing from the site root." % KEY)
    urls = [SITE + p if p.startswith("/") else p for p in argv] or sitemap_urls()
    body = json.dumps({"host": HOST, "key": KEY,
                       "keyLocation": "%s/%s.txt" % (SITE, KEY),
                       "urlList": urls}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    meaning = {200: "accepted", 202: "accepted, key still being checked",
               400: "bad request", 403: "key not found on the site yet (has the deploy finished?)",
               422: "URLs do not belong to this host", 429: "too many requests, try later"}
    print("Submitted %d URL(s): HTTP %d — %s" % (len(urls), code, meaning.get(code, "unexpected")))
    for u in urls:
        print("  " + u)
    return 0 if code in (200, 202) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
