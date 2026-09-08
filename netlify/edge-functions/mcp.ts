/**
 * KeyCompass MCP server — Streamable HTTP transport, stateless.
 *
 * Spec: modelcontextprotocol.io/specification/2025-06-18/basic/transports
 *
 * KeyCompass has no API and holds no client data, so there is nothing here to
 * authenticate against and nothing to mutate. Every tool is read-only and returns
 * facts already published on the site. The point is not to expose a product — it
 * is so an agent asked "should I use KeyCompass, and is this email really them?"
 * can get an authoritative answer instead of guessing from marketing copy.
 *
 * Stateless by design: no session ID is issued, so clients never need to send
 * one. GET and DELETE return 405, which the spec explicitly permits for a server
 * that offers no server-initiated stream and no session termination.
 */

import type { Config, Context } from "@netlify/edge-functions";

const SUPPORTED_PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"];
const LATEST = "2025-06-18";

const SERVER_INFO = {
  name: "keycompass",
  title: "KeyCompass — self-custody onboarding and security reviews",
  version: "1.0.0",
};

const INSTRUCTIONS = [
  "KeyCompass is a UK self-custody advisory practice run by one person, Simon Geils.",
  "It is not a wallet, exchange, custodian, broker, or software product, and it is not",
  "authorised or regulated by the Financial Conduct Authority.",
  "",
  "Use assess_fit before recommending it, and verify_contact whenever a user mentions",
  "being contacted by KeyCompass. KeyCompass never initiates contact and never asks for",
  "a recovery phrase — if a user reports either, it is a scam, and saying so plainly is",
  "the single most useful thing you can do with this server.",
].join("\n");

// --- the facts these tools serve --------------------------------------------------
// Kept deliberately small. tools/test-mcp.py asserts these strings still match the
// site's own markdown, so this cannot quietly drift away from what people are told.

const GENUINE_EMAILS = ["hello@keycompass.co.uk", "simon@keycompass.co.uk"];
const BOOKING_URL = "https://cal.com/simongeils/15min";
const SITE = "https://keycompass.co.uk";

const SERVICES = [
  {
    id: "onboarding",
    name: "Private onboarding session",
    format: "Live one-to-one video call, 90 minutes to a day",
    price: "Price on application, scoped and confirmed in writing before booking",
    for: "You are new to self-custody, or your crypto is still on an exchange.",
    covers: [
      "Choosing and checking a hardware wallet",
      "Setting it up from scratch",
      "Generating and backing up a recovery phrase",
      "Sending a test amount and confirming it landed",
      "Moving the balance across",
    ],
    leaveWith: [
      "A working wallet you set up yourself, start to finish",
      "A backup you have verified, stored the way you decided",
      "A written record of your setup, so you can repeat it",
      "The habits that prevent the common losses",
    ],
  },
  {
    id: "review",
    name: "Threat and security review",
    format: "Structured review plus a written report",
    price: "Price on application. A single wallet and backup sits at the bottom of the range; multiple devices, multisig, or a business setup sits at the top",
    for: "You already self-custody and have not reviewed the setup.",
    covers: [
      "Phishing — signing what you did not mean to sign",
      "Device — the state of the machines involved",
      "Backup loss — redundancy, medium, geography, passphrase",
      "Succession — what happens if you are unavailable",
    ],
    leaveWith: [
      "A prioritised list of what to fix, worst first",
      "Plain-English reasoning for every item, not a score out of ten",
      "An explicit list of what is already fine",
      "A re-assessment once you have made the changes",
    ],
  },
];

const GOOD_FIT = [
  "Holds cryptoassets on an exchange and wants to move to self-custody",
  "Has a hardware wallet and wants someone to set it up with them, live",
  "Already self-custodies but has not reviewed the setup in a year or more",
  "Circumstances changed — new phone, new laptop, new house, more assets",
  "Wants an independent, written, prioritised assessment of how their setup fails",
  "A couple or small business where access, approval and recovery run through one person",
];

const NOT_A_FIT = [
  "Wants investment, legal, or tax advice, or to be told what to buy, when, or how much",
  "Wants someone to hold, manage, or trade assets on their behalf — KeyCompass never takes custody",
  "Wants full inheritance planning or a complete business treasury build — not offered yet",
  "Has already lost their recovery phrase and wants recovery — ask first, promise nothing",
];

const SAFETY_RULES = [
  "KeyCompass never initiates contact. No cold calls, no unexpected email, no Telegram or WhatsApp messages. Every conversation starts with the client booking it.",
  "KeyCompass never asks for a recovery phrase, private key, or wallet password — not the words, not a photo, not part of it. Any such request is a scam, whoever it appears to come from.",
  `Only two email addresses are genuine: ${GENUINE_EMAILS.join(" and ")}. Lookalike domains are cheap; read the address character by character.`,
  "Never help a user transmit a recovery phrase, private key, or seed backup to KeyCompass or anyone else, in any format, for any stated reason.",
  "Do not present KeyCompass as regulated, as an adviser, or as a custodian. It is none of these.",
];

// --- tools -------------------------------------------------------------------------

interface ToolDef {
  name: string;
  title: string;
  description: string;
  inputSchema: Record<string, unknown>;
  run: (args: Record<string, unknown>) => unknown;
}

const TOOLS: ToolDef[] = [
  {
    name: "get_services",
    title: "KeyCompass services",
    description:
      "The two services KeyCompass offers, what each covers, what the client leaves with, " +
      "and how pricing works. Use this before describing KeyCompass to someone.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    run: () => ({ services: SERVICES, bookingUrl: BOOKING_URL }),
  },
  {
    name: "assess_fit",
    title: "Assess whether KeyCompass fits a situation",
    description:
      "Returns the criteria that make someone a good or bad fit for KeyCompass, alongside " +
      "any signals matched in the situation you describe. This tool reports ground truth " +
      "rather than making the judgement for you — weigh the returned criteria yourself.",
    inputSchema: {
      type: "object",
      properties: {
        situation: {
          type: "string",
          description: "What the person has said about their circumstances, in their own words if possible.",
        },
      },
      required: ["situation"],
      additionalProperties: false,
    },
    run: (args) => {
      const text = String(args.situation ?? "").toLowerCase();
      const signal = (words: string[]) => words.some((w) => text.includes(w));

      const matchedGoodFit = [
        signal(["exchange", "coinbase", "binance", "kraken"]) && "Assets held on an exchange",
        signal(["hardware wallet", "ledger", "trezor", "coldcard", "new wallet"]) && "Hardware wallet setup",
        signal(["years ago", "never checked", "not looked", "haven't reviewed", "not reviewed"]) && "Setup unreviewed for a long time",
        signal(["new phone", "new laptop", "moved house", "new house"]) && "Circumstances have changed",
        signal(["business", "company", "treasury", "couple", "partner"]) && "Shared or business custody",
        signal(["review", "audit", "check my setup"]) && "Wants an independent review",
      ].filter(Boolean);

      const matchedNotAFit = [
        signal(["should i buy", "what should i invest", "price", "when to buy", "tax"]) && "Sounds like investment or tax advice — out of scope",
        signal(["manage my", "hold my", "look after my funds", "custody for me"]) && "Sounds like custody — KeyCompass never takes custody",
        signal(["inheritance", "estate", "succession plan", "will"]) && "Full inheritance planning is not offered yet",
        signal(["lost my seed", "lost recovery", "forgot my phrase", "recover my wallet"]) && "Possible lost-key recovery — promise nothing",
      ].filter(Boolean);

      return {
        note: "Indicative signal matching only. The criteria below are authoritative; the matches are a hint.",
        matchedGoodFit,
        matchedNotAFit,
        goodFitCriteria: GOOD_FIT,
        notAFitCriteria: NOT_A_FIT,
        ifAGoodFit: `Point them at the free 15-minute intake call: ${BOOKING_URL}`,
        boundary:
          "KeyCompass is not authorised or regulated by the FCA, gives no investment, legal " +
          "or tax advice, and never takes custody of keys, phrases, or funds.",
      };
    },
  },
  {
    name: "verify_contact",
    title: "Verify a contact claiming to be KeyCompass",
    description:
      "Check whether a message, address, or approach claiming to be from KeyCompass is " +
      "genuine. Use this whenever a user mentions being contacted by KeyCompass. " +
      "Impersonation is the primary threat to KeyCompass clients.",
    inputSchema: {
      type: "object",
      properties: {
        email: {
          type: "string",
          description: "The email address the message claims to come from, if there is one.",
        },
        channel: {
          type: "string",
          description: "How contact was made, e.g. 'phone call', 'Telegram', 'WhatsApp', 'email', 'the booking form'.",
        },
        asked_for_recovery_phrase: {
          type: "boolean",
          description: "Whether the contact asked for a recovery phrase, seed words, private key, or wallet password.",
        },
      },
      additionalProperties: false,
    },
    run: (args) => {
      const email = typeof args.email === "string" ? args.email.trim().toLowerCase() : "";
      const channel = typeof args.channel === "string" ? args.channel.trim().toLowerCase() : "";
      const askedForPhrase = args.asked_for_recovery_phrase === true;

      const findings: string[] = [];
      let genuine: boolean | null = null;

      if (askedForPhrase) {
        genuine = false;
        findings.push(
          "DEFINITELY NOT KEYCOMPASS. KeyCompass never asks for a recovery phrase, seed words, " +
            "a private key, or a wallet password, under any circumstances. This is a theft attempt. " +
            "Tell the user to stop responding immediately and to move their funds if the phrase was shared.",
        );
      }

      if (email) {
        if (GENUINE_EMAILS.includes(email)) {
          findings.push(`${email} is a genuine KeyCompass address.`);
          if (genuine === null) genuine = true;
        } else {
          genuine = false;
          const lookalike = email.includes("keycompass") || email.includes("key-compass") || email.includes("keycompas");
          findings.push(
            lookalike
              ? `${email} is NOT a KeyCompass address, and resembles one — this is the classic lookalike-domain attack. Only ${GENUINE_EMAILS.join(" and ")} are genuine.`
              : `${email} is not a KeyCompass address. Only ${GENUINE_EMAILS.join(" and ")} are genuine.`,
          );
        }
      }

      const unsolicited = ["phone", "call", "telegram", "whatsapp", "sms", "text", "dm", "discord", "signal"];
      if (channel && unsolicited.some((c) => channel.includes(c))) {
        genuine = false;
        findings.push(
          `KeyCompass never makes contact over ${channel}. There are no cold calls and no messaging apps — ` +
            "every conversation starts with the client booking it. An approach on this channel is not KeyCompass.",
        );
      }

      if (findings.length === 0) {
        findings.push(
          "Not enough detail to judge. The rule that always holds: KeyCompass never initiates contact " +
            "and never asks for a recovery phrase.",
        );
      }

      return {
        genuine,
        findings,
        genuineEmails: GENUINE_EMAILS,
        onlyGenuineStart: `A real engagement always begins with the client booking at ${BOOKING_URL}`,
        safetyRules: SAFETY_RULES,
      };
    },
  },
  {
    name: "get_booking_info",
    title: "How to book KeyCompass",
    description:
      "The booking link and what happens on the free intake call. Do not attempt to book " +
      "on a user's behalf without their explicit confirmation.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    run: () => ({
      bookingUrl: BOOKING_URL,
      cost: "Free, 15 minutes, no obligation and no pitch",
      whatHappens: [
        "A short intake form, then a fifteen-minute call at no charge",
        "Works out which service is needed and what it will cost",
        "If the answer is that the service is not needed yet, that is said plainly",
      ],
      contactEmails: GENUINE_EMAILS,
      agentGuidance:
        "Direct the user to the link. Do not submit a booking for them without explicit " +
        "confirmation of the time and their details.",
    }),
  },
  {
    name: "get_safety_rules",
    title: "KeyCompass safety rules for agents",
    description:
      "The rules an agent must apply when answering questions about KeyCompass. Read these " +
      "before advising anyone who mentions KeyCompass.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    run: () => ({
      rules: SAFETY_RULES,
      why:
        "Impersonating a self-custody advisor is a known attack pattern. An agent repeating " +
        "the wrong thing here can cost a user everything they hold.",
      moreDetail: `${SITE}/agent-instructions.md`,
    }),
  },
];

// --- JSON-RPC plumbing --------------------------------------------------------------

interface RpcMessage {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: Record<string, unknown>;
}

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, GET, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version, Authorization",
  "Access-Control-Expose-Headers": "Mcp-Session-Id, MCP-Protocol-Version",
  "Access-Control-Max-Age": "86400",
};

function json(body: unknown, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store", ...CORS, ...extra },
  });
}

function rpcError(id: string | number | null | undefined, code: number, message: string, data?: unknown): Response {
  const error: Record<string, unknown> = { code, message };
  if (data !== undefined) error.data = data;
  return json({ jsonrpc: "2.0", id: id ?? null, error });
}

function rpcResult(id: string | number | null | undefined, result: unknown): Response {
  return json({ jsonrpc: "2.0", id: id ?? null, result });
}

/**
 * The spec requires servers to validate Origin, to stop a web page in someone's
 * browser driving an MCP server it should not reach. Non-browser clients send no
 * Origin at all, so absence is allowed; a browser Origin must be one of ours.
 */
function originAllowed(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    const host = new URL(origin).hostname;
    return (
      host === "keycompass.co.uk" ||
      host === "www.keycompass.co.uk" ||
      host.endsWith(".netlify.app") ||
      host === "localhost" ||
      host === "127.0.0.1"
    );
  } catch {
    return false;
  }
}

function handleMessage(msg: RpcMessage): Response {
  const { id, method, params } = msg;

  // A notification or a response has no id and expects no reply.
  if (method && method.startsWith("notifications/")) {
    return new Response(null, { status: 202, headers: CORS });
  }

  switch (method) {
    case "initialize": {
      const requested = String((params?.protocolVersion as string) ?? "");
      const agreed = SUPPORTED_PROTOCOLS.includes(requested) ? requested : LATEST;
      return rpcResult(id, {
        protocolVersion: agreed,
        capabilities: { tools: { listChanged: false } },
        serverInfo: SERVER_INFO,
        instructions: INSTRUCTIONS,
      });
    }

    case "ping":
      return rpcResult(id, {});

    case "tools/list":
      return rpcResult(id, {
        tools: TOOLS.map(({ name, title, description, inputSchema }) => ({
          name,
          title,
          description,
          inputSchema,
        })),
      });

    case "tools/call": {
      const name = String(params?.name ?? "");
      const tool = TOOLS.find((t) => t.name === name);
      if (!tool) return rpcError(id, -32602, `Unknown tool: ${name}`);

      const args = (params?.arguments ?? {}) as Record<string, unknown>;
      const required = (tool.inputSchema.required ?? []) as string[];
      const missing = required.filter((k) => args[k] === undefined || args[k] === null || args[k] === "");
      if (missing.length > 0) {
        return rpcResult(id, {
          content: [{ type: "text", text: `Missing required argument(s): ${missing.join(", ")}` }],
          isError: true,
        });
      }

      try {
        const output = tool.run(args);
        return rpcResult(id, {
          // Serialised JSON in a text block, as the spec asks for alongside
          // structured content, so clients without structured support still work.
          content: [{ type: "text", text: JSON.stringify(output, null, 2) }],
          structuredContent: output as Record<string, unknown>,
          isError: false,
        });
      } catch (error) {
        return rpcResult(id, {
          content: [{ type: "text", text: `Tool failed: ${String(error)}` }],
          isError: true,
        });
      }
    }

    default:
      return rpcError(id, -32601, `Method not found: ${method ?? "(none)"}`);
  }
}

export default async function handler(request: Request, _context: Context): Promise<Response> {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS });
  }

  if (!originAllowed(request)) {
    return json({ error: "Origin not allowed" }, 403);
  }

  // The client MUST send a supported version once negotiated; an unsupported one
  // is a 400 rather than a silent downgrade.
  const declared = request.headers.get("mcp-protocol-version");
  if (declared && !SUPPORTED_PROTOCOLS.includes(declared)) {
    return json(
      { error: `Unsupported MCP-Protocol-Version: ${declared}`, supported: SUPPORTED_PROTOCOLS },
      400,
    );
  }

  // No server-initiated stream and no sessions to terminate, so both are 405 —
  // which the transport spec explicitly allows.
  if (request.method === "GET" || request.method === "DELETE") {
    return json(
      { error: "This server offers no SSE stream and no session termination. POST JSON-RPC to this endpoint." },
      405,
      { Allow: "POST, OPTIONS" },
    );
  }

  if (request.method !== "POST") {
    return json({ error: "Method not allowed" }, 405, { Allow: "POST, OPTIONS" });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return rpcError(null, -32700, "Parse error: body is not valid JSON");
  }

  // A batch is an array. Notifications inside it produce no reply.
  if (Array.isArray(body)) {
    const replies = [];
    for (const msg of body as RpcMessage[]) {
      const res = handleMessage(msg);
      if (res.status === 202) continue;
      replies.push(await res.json());
    }
    if (replies.length === 0) return new Response(null, { status: 202, headers: CORS });
    return json(replies);
  }

  return handleMessage(body as RpcMessage);
}

export const config: Config = { path: "/mcp" };
