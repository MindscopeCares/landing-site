import { PROCESS_URL } from "./siteConfig";

function processEndpoint(): string {
  // Dev: Vite proxies /api/process → Cloud Run /
  // Prod: call Cloud Run directly (CORS enabled on the function)
  if (import.meta.env.DEV) {
    return "/api/process";
  }
  return PROCESS_URL;
}

function functionError(text: string): string {
  try {
    const parsed = JSON.parse(text) as { error?: string };
    return parsed.error ?? "";
  } catch {
    return "";
  }
}

export type ProcessFeature = "iep-analyzer" | "research-to-pptx";

/** Call the Cloud Run function for IEP analysis or research slides. */
export async function processFeature(feature: ProcessFeature, content: string): Promise<string> {
  const response = await fetch(processEndpoint(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feature, content }),
    signal: AbortSignal.timeout(90_000),
  });

  const text = await response.text();
  const errorMessage = functionError(text);

  if (!response.ok) {
    throw new Error(errorMessage || `Function request failed (${response.status}).`);
  }
  if (errorMessage) {
    throw new Error(errorMessage);
  }
  if (!text.trim()) {
    throw new Error("The MindScope function returned an empty response.");
  }
  return text;
}

/** Facility search still needs its own Function. */
export async function callAI(systemPrompt: string, userPrompt: string): Promise<string> {
  void systemPrompt;
  void userPrompt;
  throw new Error("Facility search is not wired yet.");
}
