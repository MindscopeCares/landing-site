import DOMPurify from "dompurify";

// Model output and uploaded documents are untrusted. Permit presentation text
// and inline layout only; no scripts, navigation, forms, frames, or resources.
export function safeSlideDocument(html: string): string {
  if (typeof html !== "string" || html.length > 100_000) throw new Error("A slide is too large to render safely.");
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ["div", "section", "p", "h1", "h2", "h3", "h4", "ul", "ol", "li", "span", "strong", "em", "br", "table", "thead", "tbody", "tr", "td", "th"],
    ALLOWED_ATTR: ["style", "class"],
    ALLOW_DATA_ATTR: false,
  });
  return `<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"><style>body{margin:0;width:1280px;min-height:720px;font-family:Arial,sans-serif}</style></head><body>${clean}</body></html>`;
}
