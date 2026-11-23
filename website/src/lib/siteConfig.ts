/** Public site settings. Swap these when the domain and inbox are ready. */
export const PROCESS_URL =
  "https://disabilityai-855875950632.us-east1.run.app";
export const CONTACT_EMAIL = "contact@mindscopecares.com";

export const TAVILY_API_KEY = "";
/** Prefer VITE_GOOGLE_PLACES_API_KEY in website/.env (never commit the real key). */
export const GOOGLE_PLACES_API_KEY =
  import.meta.env.VITE_GOOGLE_PLACES_API_KEY?.trim() ?? "";

