#!/usr/bin/env python3
"""Watch Certificate Transparency logs for certificates issued for keycompass.co.uk.

Every certificate a public CA issues is published to CT logs. If someone hijacks
the domain or the DNS and gets their own certificate, it shows up here — usually
within minutes, and before anyone would notice by other means.

    python3 tools/ct-monitor.py --init    establish the baseline (first run)
    python3 tools/ct-monitor.py           check for anything new

Exit status: 0 nothing new, 1 NEW CERTIFICATES, 2 could not reach any log source.
State lives in ~/.keycompass-security/ct-baseline.json, outside the repo.
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request

DOMAIN = "keycompass.co.uk"
STATE = os.path.expanduser("~/.keycompass-security/ct-baseline.json")
TIMEOUT = 45
UA = "keycompass-ct-monitor"

# Certificates we expect to exist. An issuer outside this set is not proof of
# anything wrong — Netlify could change CA — but it deserves a look.
EXPECTED_ISSUERS = ("Let's Encrypt", "DigiCert", "Google Trust Services")


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT,
                                context=ssl.create_default_context()) as r:
        return json.loads(r.read().decode("utf-8"))


def from_certspotter():
    """Primary source. Free tier is rate-limited, which weekly polling stays under."""
    url = ("https://api.certspotter.com/v1/issuances?domain=" + DOMAIN +
           "&include_subdomains=true&expand=dns_names&expand=issuer")
    out = {}
    for e in _get(url):
        out[e["cert_sha256"]] = {
            "sha256": e["cert_sha256"],
            "names": sorted(e.get("dns_names", [])),
            "issuer": (e.get("issuer") or {}).get("friendly_name", "?"),
            "not_before": e.get("not_before", "?"),
            "not_after": e.get("not_after", "?"),
        }
    return out


def from_crtsh():
    """Fallback. Frequently returns 502 under load, hence the ordering."""
    url = "https://crt.sh/?q=" + DOMAIN + "&output=json"
    out = {}
    for e in _get(url):
        key = str(e.get("serial_number") or e.get("id"))
        out[key] = {
            "sha256": key,
            "names": sorted(set((e.get("name_value") or "").split("\n"))),
            "issuer": (e.get("issuer_name") or "?")[:60],
            "not_before": e.get("not_before", "?"),
            "not_after": e.get("not_after", "?"),
        }
    return out


def fetch():
    errors = []
    for name, fn in (("certspotter", from_certspotter), ("crt.sh", from_crtsh)):
        try:
            certs = fn()
            if certs:
                return certs, name
            errors.append(name + ": returned nothing")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError) as exc:
            errors.append("%s: %s" % (name, exc))
    print("Could not reach any CT source:", file=sys.stderr)
    for e in errors:
        print("  " + e, file=sys.stderr)
    return None, None


def show(c, indent="    "):
    flag = "" if any(i in c["issuer"] for i in EXPECTED_ISSUERS) else "   <-- UNEXPECTED ISSUER"
    print("%s%s" % (indent, ", ".join(c["names"])))
    print("%s  issued %s by %s%s" % (indent, c["not_before"][:10], c["issuer"], flag))


def main():
    init = "--init" in sys.argv
    certs, source = fetch()
    if certs is None:
        return 2

    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    known = {}
    if os.path.exists(STATE) and not init:
        with open(STATE) as f:
            known = json.load(f).get("certs", {})

    new = {k: v for k, v in certs.items() if k not in known}

    print("%s — %d certificate(s) in CT logs (source: %s)" % (DOMAIN, len(certs), source))

    if init or not known:
        print("\nBaseline recorded. These are now treated as known-good:\n")
        for c in sorted(certs.values(), key=lambda c: c["not_before"]):
            show(c)
        rc = 0
    elif new:
        print("\n*** %d NEW CERTIFICATE(S) SINCE LAST CHECK ***\n" % len(new))
        for c in sorted(new.values(), key=lambda c: c["not_before"]):
            show(c)
        print("\nIf you did not expect these, treat it as a possible domain or DNS")
        print("compromise: check the registrar and Netlify accounts NOW, before")
        print("assuming it was a routine renewal.")
        rc = 1
    else:
        print("No new certificates. Nothing to do.")
        rc = 0

    with open(STATE, "w") as f:
        json.dump({"domain": DOMAIN, "certs": certs}, f, indent=2)
    return rc


if __name__ == "__main__":
    sys.exit(main())
