#!/usr/bin/env python3
"""Serve the site locally with the real netlify.toml headers applied.

Opening index.html from disk applies no CSP at all, so a policy that would break
the live site looks perfectly fine locally. This serves the repo on :4322 with
the headers Netlify actually sends, so CSP violations show up in the browser
console before they reach production.

    python3 tools/serve-with-csp.py     then open http://localhost:4322
"""

import functools
import http.server
import os
import re
import socketserver

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 4322


def headers_for_all_paths():
    """Pull the [[headers]] block that applies to /* out of netlify.toml."""
    toml = open(os.path.join(ROOT, "netlify.toml"), encoding="utf-8").read()
    block = re.search(
        r'\[\[headers\]\]\s*\n\s*for\s*=\s*"/\*"\s*\n\s*\[headers\.values\]\n(.*?)(?=\n\[|\Z)',
        toml, re.DOTALL)
    if not block:
        return {}
    found = {}
    for name, value in re.findall(r'^\s*([A-Za-z-]+)\s*=\s*"(.*)"\s*$',
                                  block.group(1), re.MULTILINE):
        found[name] = value
    return found


EXTRA = headers_for_all_paths()


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        for name, value in EXTRA.items():
            # HSTS over plain http would poison localhost for every other project.
            if name.lower() != "strict-transport-security":
                self.send_header(name, value)
        super().end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(Handler, directory=ROOT)
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as srv:
        print("serving %s on %d with %d header(s) from netlify.toml"
              % (ROOT, PORT, len(EXTRA)), flush=True)
        for k in EXTRA:
            print("  " + k, flush=True)
        srv.serve_forever()
