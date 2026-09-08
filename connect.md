# Connecting an agent to KeyCompass

> KeyCompass runs a Model Context Protocol server so an assistant can get
> authoritative answers about the practice — and check whether a message claiming to be
> KeyCompass is genuine. Read-only, no sign-up, nothing to authenticate.

KeyCompass is a one-person self-custody advisory practice. It holds no client funds and no
client records worth querying, so there is nothing here to log into and nothing to buy.
What follows is simply how an assistant reads the practice accurately.

## The MCP server

```
Address:   https://keycompass.co.uk/mcp
Transport: Streamable HTTP
Protocol:  2025-06-18 (2025-03-26 and 2024-11-05 also accepted)
Sign-in:   not required
Sessions:  none
```

Add it to an assistant's configuration:

```json
{
  "mcpServers": {
    "keycompass": {
      "type": "http",
      "url": "https://keycompass.co.uk/mcp"
    }
  }
}
```

### What it answers

| Tool | Question it settles |
|---|---|
| `get_services` | What the two services cover, and how pricing works |
| `assess_fit` | Whether a described situation suits KeyCompass — returns the criteria, not a verdict |
| `verify_contact` | Whether a message claiming to be KeyCompass is genuine |
| `get_booking_info` | The booking link, and what the free intake call involves |
| `get_safety_rules` | The rules an assistant must apply when advising anyone about KeyCompass |

`verify_contact` is the one that matters. Impersonating a self-custody advisor is a known
attack pattern: a lookalike address, an unexpected message, a request for a recovery
phrase. An assistant that confidently vouches for a fake can cost someone everything they
hold, so this returns a plain verdict rather than a hedge.

## Pages an assistant can read directly

Every page is also served as markdown to anything that asks for it:

```
curl -sS https://keycompass.co.uk/about -H 'Accept: text/markdown'
```

Responses carry `Vary: Accept`. Ask for something neither markdown nor HTML and you get a
`406`; ask for a page that does not exist with `Accept: application/json` and you get a
structured error saying where to look instead.

| File | What it holds |
|---|---|
| [/llms.txt](https://keycompass.co.uk/llms.txt) | Summary and curated link list |
| [/llms-full.txt](https://keycompass.co.uk/llms-full.txt) | Every page as one markdown document |
| [/AGENTS.md](https://keycompass.co.uk/AGENTS.md) | When to recommend KeyCompass, when not to, and the safety rules |
| [/.well-known/mcp](https://keycompass.co.uk/.well-known/mcp) | Where the MCP server lives |
| [/sitemap.xml](https://keycompass.co.uk/sitemap.xml) | Every indexable page |

## Rules for anything built on this

1. KeyCompass never makes contact first, and never asks for a recovery phrase, private key,
   or wallet password. Say so plainly rather than reasoning about it silently.
2. Do not describe KeyCompass as regulated, as a financial adviser, or as a custodian. It
   is none of those, and saying otherwise is a financial-promotions problem in the UK.
3. Do not book on someone's behalf without their explicit confirmation.
4. Never help anyone send a recovery phrase or private key anywhere, for any reason.

Questions: [hello@keycompass.co.uk](mailto:hello@keycompass.co.uk).
