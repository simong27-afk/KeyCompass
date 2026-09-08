/**
 * Accept-based content negotiation, per acceptmarkdown.com.
 *
 * Netlify's static hosting cannot vary a response on a request header, so the
 * negotiation has to happen at the edge. For the four content pages this serves
 * the .md source when the client asks for text/markdown, the normal HTML page
 * otherwise, and 406 when the client will accept neither.
 *
 * Every response this touches carries `Vary: Accept`, without which a CDN can
 * hand the cached HTML to an agent that asked for markdown (or the reverse),
 * depending only on which variant happened to be cached first.
 *
 * Safety: any unexpected error falls through to the normal response. A bug in
 * here must never be able to take the site down.
 */

import type { Config, Context } from "@netlify/edge-functions";

/** Clean URL -> markdown source. Netlify redirects /about.html to /about, so
 *  only the clean spelling needs an entry here. */
const VARIANTS: Record<string, string> = {
  "/": "/index.md",
  "/about": "/about.md",
  "/contact": "/contact.md",
  "/privacy": "/privacy.md",
};

const MARKDOWN = "text/markdown";
const HTML = "text/html";
const MD_CONTENT_TYPE = "text/markdown; charset=utf-8";

interface AcceptEntry {
  media: string;
  q: number;
}

function parseAccept(header: string): AcceptEntry[] {
  return header
    .split(",")
    .map((part) => {
      const bits = part.trim().split(";");
      const media = (bits.shift() || "").trim().toLowerCase();
      let q = 1;
      for (const p of bits) {
        const [k, v] = p.split("=");
        if (k && k.trim().toLowerCase() === "q") {
          const parsed = Number.parseFloat(v);
          if (!Number.isNaN(parsed)) q = parsed;
        }
      }
      return { media, q };
    })
    .filter((e) => e.media.length > 0);
}

/**
 * The q-value that applies to one media type, honouring RFC 9110 precedence:
 * an exact match beats `type/*`, which beats `*​/*`, regardless of q. That is
 * what makes `Accept: *​/*, text/markdown;q=0` correctly mean "not markdown".
 */
function qualityFor(entries: AcceptEntry[], type: string): number {
  const [group] = type.split("/");
  let bestSpecificity = -1;
  let bestQ = 0;

  for (const e of entries) {
    const specificity = e.media === type ? 2 : e.media === `${group}/*` ? 1 : e.media === "*/*" ? 0 : -1;
    if (specificity < 0) continue;
    if (specificity > bestSpecificity || (specificity === bestSpecificity && e.q > bestQ)) {
      bestSpecificity = specificity;
      bestQ = e.q;
    }
  }
  return bestSpecificity < 0 ? 0 : bestQ;
}

type Choice = "markdown" | "html" | "none";

export function chooseVariant(acceptHeader: string | null): Choice {
  if (!acceptHeader || !acceptHeader.trim()) return "html";

  const entries = parseAccept(acceptHeader);
  if (entries.length === 0) return "html";

  const qMarkdown = qualityFor(entries, MARKDOWN);
  const qHtml = qualityFor(entries, HTML);
  const namedMarkdown = entries.some((e) => e.media === MARKDOWN && e.q > 0);

  // Only an explicit `text/markdown` flips the default. A bare `*​/*` — what
  // curl and most crawlers send — must keep returning HTML.
  if (namedMarkdown && qMarkdown > 0 && qMarkdown >= qHtml) return "markdown";
  if (qHtml > 0) return "html";
  if (qMarkdown > 0) return "markdown";
  return "none";
}

function withVary(response: Response): Response {
  const headers = new Headers(response.headers);
  const existing = headers.get("Vary");
  const parts = existing ? existing.split(",").map((s) => s.trim()) : [];
  if (!parts.some((p) => p.toLowerCase() === "accept")) parts.push("Accept");
  headers.set("Vary", parts.join(", "));
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

async function markdownResponse(request: Request, path: string, status: number): Promise<Response | null> {
  const source = await fetch(new URL(path, request.url));
  if (!source.ok) return null;
  const body = await source.text();
  return new Response(body, {
    status,
    headers: {
      "Content-Type": MD_CONTENT_TYPE,
      "Vary": "Accept",
      "X-Content-Type-Options": "nosniff",
      "Cache-Control": "public, max-age=0, must-revalidate",
      "Link": '<https://keycompass.co.uk/llms.txt>; rel="alternate"; type="text/plain"',
    },
  });
}

/**
 * Static assets, matched on the path itself rather than relying on the glob
 * semantics of `excludedPath`. Belt and braces: if a pattern there does not mean
 * what it appears to mean, this still keeps the function off asset requests and
 * prevents the .md subrequest below from re-entering the function.
 */
const STATIC_EXTENSION = /\.(md|txt|xml|json|webmanifest|css|js|map|png|jpe?g|gif|svg|ico|webp|avif|woff2?|ttf|otf|pdf|zip)$/i;

export default async function handler(request: Request, context: Context): Promise<Response> {
  try {
    const url = new URL(request.url);
    if (STATIC_EXTENSION.test(url.pathname)) return context.next();

    const accept = request.headers.get("accept");
    const variant = VARIANTS[url.pathname];

    if (variant) {
      const choice = chooseVariant(accept);

      if (choice === "markdown") {
        const md = await markdownResponse(request, variant, 200);
        if (md) return md;
        return withVary(await context.next());
      }

      if (choice === "none") {
        return new Response(
          "406 Not Acceptable\n\n" +
            "This URL can be served as text/html or text/markdown.\n" +
            "Retry with:  Accept: text/markdown\n" +
            "Machine-readable index: https://keycompass.co.uk/llms.txt\n",
          {
            status: 406,
            headers: {
              "Content-Type": "text/plain; charset=utf-8",
              "Vary": "Accept",
            },
          },
        );
      }

      return withVary(await context.next());
    }

    // Not a negotiable path. Only special-case a 404 asked for as markdown, so
    // an agent that guessed a URL gets a recoverable answer instead of a page
    // of HTML chrome.
    const response = await context.next();
    if (response.status === 404 && chooseVariant(accept) === "markdown") {
      const md = await markdownResponse(request, "/404.md", 404);
      if (md) return md;
    }
    return response;
  } catch (_error) {
    return context.next();
  }
}

export const config: Config = {
  path: "/*",
  excludedPath: [
    "/assets/*",
    "/brand/*",
    "/export/*",
    "/tools/*",
    "/.netlify/*",
    "/*.md",
    "/*.txt",
    "/*.xml",
    "/*.json",
    "/*.webmanifest",
    "/*.png",
    "/*.svg",
    "/*.woff2",
    "/*.ico",
  ],
};
