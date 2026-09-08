#!/usr/bin/env python3
"""Conformance tests for the KeyCompass MCP server.

    python3 tools/test-mcp.py --local        facts in mcp.ts still match the site
    python3 tools/test-mcp.py                against https://keycompass.co.uk/mcp
    python3 tools/test-mcp.py --url <base>   against a deploy preview

--local guards against the one failure this design invites: the server's answers
are hard-coded in TypeScript, so they can drift away from what the website tells
people. Everything else needs a deployed endpoint, because there is no Deno here.

Exit status: 0 all passed, 1 one or more failed, 2 endpoint unreachable.
"""

import io
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = "https://keycompass.co.uk"
PROTOCOL = "2025-06-18"
TIMEOUT = 30

results = []


def check(name, ok, detail=""):
    results.append((ok, name, detail))
    return ok


def rpc(endpoint, payload, headers=None, method="POST"):
    """Returns (status, headers, parsed-body-or-raw-text)."""
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "keycompass-mcp-check",
    }
    h.update(headers or {})
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(endpoint, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT,
                                    context=ssl.create_default_context()) as r:
            raw = r.read().decode("utf-8", "replace")
            try:
                return r.status, dict(r.headers), json.loads(raw) if raw else None
            except ValueError:
                return r.status, dict(r.headers), raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, dict(e.headers), json.loads(raw) if raw else None
        except ValueError:
            return e.code, dict(e.headers), raw


def local_checks():
    ts = io.open(os.path.join(ROOT, "netlify/edge-functions/mcp.ts"), encoding="utf-8").read()
    contact = io.open(os.path.join(ROOT, "contact.md"), encoding="utf-8").read()
    agents = io.open(os.path.join(ROOT, "agent-instructions.md"), encoding="utf-8").read()
    index = io.open(os.path.join(ROOT, "index.md"), encoding="utf-8").read()

    # The facts the server asserts must be the facts the site asserts.
    for email in ("hello@keycompass.co.uk", "simon@keycompass.co.uk"):
        check("server knows %s" % email, email in ts)
        check("site publishes %s" % email, email in contact)

    booking = "https://cal.com/simongeils/15min"
    check("server booking URL matches the site", booking in ts and booking in index, booking)

    for service in ("Private onboarding session", "Threat and security review"):
        check("service name matches the site: %r" % service,
              service in ts and service in index)

    # The safety rules are the whole point; they must not weaken silently.
    for phrase in ("never initiates contact", "never asks for a recovery phrase"):
        check("server states: %s" % phrase, phrase in ts)
        check("AGENTS.md states: %s" % phrase, phrase in agents.lower() or
              phrase.replace("never initiates contact", "never initiates contact") in agents)

    check("server declares no authentication", '"none"' in
          io.open(os.path.join(ROOT, ".well-known/mcp"), encoding="utf-8").read())

    # Discovery document must agree with the code about the tool list.
    disc = json.load(io.open(os.path.join(ROOT, ".well-known/mcp"), encoding="utf-8"))
    declared = set(disc["tools"])
    # Scope to the TOOLS array — serverInfo also has a `name:` field, and matching
    # that made this check fail against correct code the first time it ran.
    tools_block = ts[ts.index("const TOOLS: ToolDef[]"):ts.index("// --- JSON-RPC plumbing")]
    implemented = set(re.findall(r'^\s{4}name: "([a-z_]+)",', tools_block, re.M))
    check("discovery tool list matches the implementation",
          declared == implemented,
          "declared=%s implemented=%s" % (sorted(declared), sorted(implemented)))
    check("discovery names the right endpoint",
          disc["servers"][0]["url"] == "https://keycompass.co.uk/mcp",
          disc["servers"][0]["url"])
    check("discovery declares streamable-http",
          disc["servers"][0]["transport"] == "streamable-http")

    # AGENTS.md is generated from agent-instructions.md; they must be identical.
    a = io.open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8").read()
    check("AGENTS.md is byte-identical to agent-instructions.md", a == agents,
          "%d vs %d bytes" % (len(a), len(agents)))


def live_checks(base):
    endpoint = base.rstrip("/") + "/mcp"

    # --- initialize ---
    status, headers, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                   "clientInfo": {"name": "keycompass-check", "version": "1.0.0"}},
    })
    if not check("initialize returns 200", status == 200, "got %s" % status):
        return
    check("initialize returns application/json",
          "application/json" in headers.get("Content-Type", ""), headers.get("Content-Type"))
    result = (body or {}).get("result", {})
    check("initialize echoes the negotiated protocol version",
          result.get("protocolVersion") == PROTOCOL, result.get("protocolVersion"))
    check("initialize declares the tools capability",
          "tools" in result.get("capabilities", {}), json.dumps(result.get("capabilities")))
    check("initialize returns serverInfo with a name",
          bool(result.get("serverInfo", {}).get("name")),
          result.get("serverInfo", {}).get("name"))
    check("initialize returns instructions for the agent",
          bool(result.get("instructions")))

    # An unknown protocol version must still get a supported one back, not an error.
    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 2, "method": "initialize",
        "params": {"protocolVersion": "1999-01-01", "capabilities": {}},
    })
    check("unsupported protocolVersion negotiates down rather than failing",
          (body or {}).get("result", {}).get("protocolVersion") == PROTOCOL,
          json.dumps(body)[:80])

    # --- notifications get 202 with no body ---
    status, _, body = rpc(endpoint, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    check("initialized notification returns 202 with no body",
          status == 202 and not body, "status %s" % status)

    # --- tools/list ---
    _, _, body = rpc(endpoint, {"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    tools = (body or {}).get("result", {}).get("tools", [])
    names = [t.get("name") for t in tools]
    check("tools/list returns the five tools", len(tools) == 5, ", ".join(names))
    for expected in ("get_services", "assess_fit", "verify_contact",
                     "get_booking_info", "get_safety_rules"):
        check("tools/list includes %s" % expected, expected in names)
    check("every tool has a description and inputSchema",
          all(t.get("description") and isinstance(t.get("inputSchema"), dict) for t in tools))
    check("every inputSchema is an object schema",
          all(t["inputSchema"].get("type") == "object" for t in tools))

    # --- tools/call ---
    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"name": "get_services", "arguments": {}},
    })
    res = (body or {}).get("result", {})
    check("tools/call get_services succeeds", res.get("isError") is False)
    check("tools/call returns a text content block",
          bool(res.get("content")) and res["content"][0].get("type") == "text")
    check("tools/call returns structuredContent",
          isinstance(res.get("structuredContent"), dict))
    check("get_services returns both services",
          len(res.get("structuredContent", {}).get("services", [])) == 2)

    # verify_contact is the tool that matters; test the dangerous paths.
    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {"name": "verify_contact",
                   "arguments": {"email": "hello@keycompass.co.uk"}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("verify_contact accepts a genuine address", sc.get("genuine") is True,
          json.dumps(sc.get("findings"))[:70])

    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "verify_contact",
                   "arguments": {"email": "support@keycompass-help.com"}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("verify_contact rejects a lookalike address", sc.get("genuine") is False)
    check("verify_contact names it as a lookalike attack",
          any("lookalike" in f.lower() for f in sc.get("findings", [])))

    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "verify_contact",
                   "arguments": {"asked_for_recovery_phrase": True}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("verify_contact flags a recovery-phrase request as theft",
          sc.get("genuine") is False and
          any("NOT KEYCOMPASS" in f for f in sc.get("findings", [])))

    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 8, "method": "tools/call",
        "params": {"name": "verify_contact", "arguments": {"channel": "WhatsApp message"}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("verify_contact rejects an unsolicited messaging-app approach",
          sc.get("genuine") is False)

    # assess_fit must return criteria, not a bare verdict.
    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 9, "method": "tools/call",
        "params": {"name": "assess_fit",
                   "arguments": {"situation": "All my Bitcoin is on an exchange and it worries me"}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("assess_fit matches an exchange-holding signal",
          any("exchange" in m.lower() for m in sc.get("matchedGoodFit", [])),
          json.dumps(sc.get("matchedGoodFit")))
    check("assess_fit always returns the full criteria",
          bool(sc.get("goodFitCriteria")) and bool(sc.get("notAFitCriteria")))
    check("assess_fit always restates the FCA boundary",
          "FCA" in sc.get("boundary", ""))

    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": "assess_fit",
                   "arguments": {"situation": "What should I invest in and when should I buy?"}},
    })
    sc = (body or {}).get("result", {}).get("structuredContent", {})
    check("assess_fit flags an investment-advice request as out of scope",
          bool(sc.get("matchedNotAFit")), json.dumps(sc.get("matchedNotAFit")))

    # --- error handling ---
    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 11, "method": "tools/call",
        "params": {"name": "no_such_tool", "arguments": {}},
    })
    check("unknown tool returns JSON-RPC -32602",
          (body or {}).get("error", {}).get("code") == -32602,
          json.dumps((body or {}).get("error"))[:60])

    _, _, body = rpc(endpoint, {"jsonrpc": "2.0", "id": 12, "method": "no/such/method"})
    check("unknown method returns JSON-RPC -32601",
          (body or {}).get("error", {}).get("code") == -32601)

    _, _, body = rpc(endpoint, {
        "jsonrpc": "2.0", "id": 13, "method": "tools/call",
        "params": {"name": "assess_fit", "arguments": {}},
    })
    res = (body or {}).get("result", {})
    check("missing required argument is a tool error, not a crash",
          res.get("isError") is True)

    # --- transport rules ---
    status, headers, _ = rpc(endpoint, None, method="GET")
    check("GET returns 405 (no SSE stream offered)", status == 405, "got %s" % status)
    check("405 response advertises Allow: POST", "POST" in headers.get("Allow", ""),
          headers.get("Allow"))

    status, _, _ = rpc(endpoint, None, method="DELETE")
    check("DELETE returns 405 (stateless, no session to end)", status == 405, "got %s" % status)

    status, _, _ = rpc(endpoint, {"jsonrpc": "2.0", "id": 14, "method": "ping"},
                       headers={"MCP-Protocol-Version": "1999-01-01"})
    check("invalid MCP-Protocol-Version header returns 400", status == 400, "got %s" % status)

    status, _, body = rpc(endpoint, {"jsonrpc": "2.0", "id": 15, "method": "ping"},
                          headers={"MCP-Protocol-Version": PROTOCOL})
    check("ping with a valid protocol header succeeds",
          status == 200 and "result" in (body or {}))

    status, _, _ = rpc(endpoint, {"jsonrpc": "2.0", "id": 16, "method": "ping"},
                       headers={"Origin": "https://evil.example.com"})
    check("a foreign browser Origin is rejected", status == 403, "got %s" % status)

    # --- discovery document ---
    status, headers, body = rpc(base.rstrip("/") + "/.well-known/mcp", None, method="GET")
    check("/.well-known/mcp is served", status == 200, "got %s" % status)
    check("/.well-known/mcp is application/json",
          "application/json" in headers.get("Content-Type", ""), headers.get("Content-Type"))
    if isinstance(body, dict):
        check("discovery points at the live endpoint",
              body.get("servers", [{}])[0].get("url", "").endswith("/mcp"))


def main():
    args = sys.argv[1:]
    if "--local" in args:
        print("Checking MCP server facts against the site\n")
        local_checks()
    else:
        base = args[args.index("--url") + 1] if "--url" in args else DEFAULT
        print("Checking MCP endpoint: %s/mcp\n" % base.rstrip("/"))
        try:
            live_checks(base)
        except (urllib.error.URLError, OSError) as e:
            print("Could not reach %s: %s" % (base, e), file=sys.stderr)
            return 2

    width = max(len(n) for _, n, _ in results)
    failed = sum(1 for ok, _, _ in results if not ok)
    for ok, name, detail in results:
        print("%s %-*s %s" % ("  ok  " if ok else " FAIL ", width, name, detail))
    print("\n%d passed, %d failed, %d total" % (len(results) - failed, failed, len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
