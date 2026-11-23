export interface PlaceResult {
  id: string;
  name: string;
  address?: string;
  phone?: string;
  website?: string;
  mapsUrl?: string;
  rating?: number;
  ratingCount?: number;
  types: string[];
}

function placesKey(): string {
  const key = import.meta.env.VITE_GOOGLE_PLACES_API_KEY?.trim() ?? "";
  if (!key) {
    throw new Error(
      "Google Places is not configured. Add VITE_GOOGLE_PLACES_API_KEY to website/.env and restart the dev server.",
    );
  }
  return key;
}

/** Text Search (Places API New) — works from the browser with a referrer-restricted key. */
export async function searchPlaces(textQuery: string, maxResults = 8): Promise<PlaceResult[]> {
  const response = await fetch("https://places.googleapis.com/v1/places:searchText", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Goog-Api-Key": placesKey(),
      "X-Goog-FieldMask": [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.types",
      ].join(","),
    },
    body: JSON.stringify({
      textQuery,
      maxResultCount: Math.min(Math.max(maxResults, 1), 20),
    }),
  });

  const data = (await response.json()) as {
    error?: { message?: string; status?: string };
    places?: Array<{
      id?: string;
      displayName?: { text?: string };
      formattedAddress?: string;
      nationalPhoneNumber?: string;
      websiteUri?: string;
      googleMapsUri?: string;
      rating?: number;
      userRatingCount?: number;
      types?: string[];
    }>;
  };

  if (!response.ok) {
    throw new Error(
      data.error?.message || `Google Places request failed (${response.status}).`,
    );
  }

  return (data.places ?? [])
    .map((place, index) => ({
      id: place.id || `place-${index}`,
      name: place.displayName?.text?.trim() || "Unnamed place",
      address: place.formattedAddress,
      phone: place.nationalPhoneNumber,
      website: place.websiteUri,
      mapsUrl: place.googleMapsUri,
      rating: place.rating,
      ratingCount: place.userRatingCount,
      types: place.types ?? [],
    }))
    .filter((place) => place.name !== "Unnamed place" || place.address);
}

/** Build a local referral query from need + city/state. */
export function referralQuery(need: string, location: string): string {
  return `${need.trim()} near ${location.trim()}`;
}
