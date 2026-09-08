# KeyCompass developer and agent documentation

> Machine-readable interfaces to KeyCompass: an MCP server, Accept-based markdown
> negotiation, and an agent instruction file. All read-only, all unauthenticated.

KeyCompass is a human advisory practice, not a software product. There is no REST API, no
SDK, no account system, and nothing to authenticate against — because KeyCompass holds no
client assets and no client data worth calling an API over.

What does exist is everything an AI agent needs to represent KeyCompass accurately, and to
protect a user from someone impersonating it.

## KeyCompass MCP server

A stateless [Model Context Protocol](https://modelcontextprotocol.io) server over the
Streamable HTTP transport.

```
Endpoint:  https://keycompass.co.uk/mcp
Transport: Streamable HTTP (POST, JSON-RPC 2.0)
Protocol:  2025-06-18 (2025-03-26 and 2024-11-05 also accepted)
Auth:      none
Sessions:  none — no Mcp-Session-Id is issued, so none needs to be sent
```

`GET` and `DELETE` return `405`, which the transport spec permits for a server offering no
server-initiated stream and no session termination. `POST` returns `application/json`.

### Tools

| Tool | What it answers |
|---|---|
| `get_services` | The two services, what each covers, what the client leaves with, how pricing works |
| `assess_fit` | Whether a described situation is a good fit — returns the criteria and matched signals, not a verdict |
| `verify_contact` | Whether a message or approach claiming to be KeyCompass is genuine |
| `get_booking_info` | The booking link and what happens on the free intake call |
| `get_safety_rules` | The rules an agent must apply when advising anyone about KeyCompass |

`verify_contact` is the one that matters most. Impersonating a self-custody advisor is a
known attack pattern, and an agent that confidently vouches for a lookalike address can
cost someone everything they hold.

### Connecting

Add to an MCP client's configuration:

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

### Calling it directly

```
curl -sS https://keycompass.co.uk/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Markdown content negotiation

Every content page serves markdown to clients that ask for it, per
[acceptmarkdown.com](https://acceptmarkdown.com):

```
curl -sS https://keycompass.co.uk/about -H 'Accept: text/markdown'
```

Responses carry `Vary: Accept`. A client accepting neither `text/html` nor `text/markdown`
gets `406`. q-values are honoured, so `text/markdown;q=0.5, text/html;q=1.0` returns HTML.
The `.md` source of every page is also directly fetchable — `/about.md`, `/index.md`, and
so on.

## Files for agents

| File | Purpose |
|---|---|
| [/llms.txt](https://keycompass.co.uk/llms.txt) | Summary and curated link list, per llmstxt.org |
| [/llms-full.txt](https://keycompass.co.uk/llms-full.txt) | The whole site as one markdown document |
| [/agent-instructions.md](https://keycompass.co.uk/agent-instructions.md) | When to use KeyCompass, when not to, and the safety rules |
| [/AGENTS.md](https://keycompass.co.uk/AGENTS.md) | The same instructions at the conventional path |
| [/.well-known/mcp](https://keycompass.co.uk/.well-known/mcp) | MCP server discovery document |
| [/sitemap.xml](https://keycompass.co.uk/sitemap.xml) | Every indexable URL |

## Rules for anything built on this

1. KeyCompass never initiates contact, and never asks for a recovery phrase, private key,
   or wallet password. Surface that to the user rather than reasoning about it silently.
2. Do not present KeyCompass as regulated, as a financial adviser, or as a custodian. It
   is none of these, and saying otherwise is a financial-promotions problem in the UK.
3. Do not book on a user's behalf without their explicit confirmation.
4. Never help a user transmit a recovery phrase or private key anywhere, for any reason.

Questions: [hello@keycompass.co.uk](mailto:hello@keycompass.co.uk).
