import { useMemo, useState } from "react";
import chronicDataFile from "../data/tavilyPrompts.json";
import { referralQuery, searchPlaces, type PlaceResult } from "../lib/googlePlaces";
import {
  ErrorNote,
  FormCard,
  PrimaryButton,
  SectionLabel,
  Spinner,
  ToolPage,
} from "../components/ToolPage";

const CONDITIONS = Object.keys(chronicDataFile);

export default function FacilitySearch() {
  const [location, setLocation] = useState("");
  const [condition, setCondition] = useState(CONDITIONS[0] ?? "ADHD");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PlaceResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searchedQuery, setSearchedQuery] = useState<string | null>(null);

  const keyword = useMemo(() => {
    const entry = (chronicDataFile as Record<string, { search_keywords: string[] }>)[condition];
    return entry?.search_keywords?.[0] ?? `${condition} support for children`;
  }, [condition]);

  const handleSearch = async () => {
    const loc = location.trim();
    if (loc.length < 3) {
      setError("Enter a city and state (at least 3 characters).");
      return;
    }
    if (loading) return;

    setLoading(true);
    setError(null);
    setResults([]);
    const query = referralQuery(keyword, loc);
    setSearchedQuery(query);

    try {
      const places = await searchPlaces(query, 8);
      setResults(places);
      if (places.length === 0) {
        setError("No local providers matched that search. Try a broader city or different need.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Facility search failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ToolPage
      current="/parents/facilities"
      eyebrow="Finding local support"
      title="Facility Search"
      description="Enter your location and your child's area of need. We'll surface nearby providers from Google Places that you can review with your counselor."
    >
      <FormCard>
        <label className="block mb-4">
          <span
            className="block text-xs font-semibold tracking-widest uppercase mb-2"
            style={{ color: "var(--muted-foreground)" }}
          >
            Location
          </span>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. Atlanta, GA"
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
            style={{
              backgroundColor: "var(--background)",
              color: "var(--foreground)",
              border: "1px solid var(--border)",
            }}
          />
        </label>

        <label className="block mb-6">
          <span
            className="block text-xs font-semibold tracking-widest uppercase mb-2"
            style={{ color: "var(--muted-foreground)" }}
          >
            Area of need
          </span>
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
            className="w-full rounded-lg px-3 py-2.5 text-sm outline-none"
            style={{
              backgroundColor: "var(--background)",
              color: "var(--foreground)",
              border: "1px solid var(--border)",
            }}
          >
            {CONDITIONS.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>

        <PrimaryButton disabled={loading || location.trim().length < 3} onClick={handleSearch}>
          {loading ? (
            <>
              <Spinner color="var(--primary-foreground)" />
              Searching nearby…
            </>
          ) : (
            "Find local providers"
          )}
        </PrimaryButton>

        {error ? <ErrorNote message={error} /> : null}
      </FormCard>

      {results.length > 0 ? (
        <div className="mt-10">
          <SectionLabel>Nearby options</SectionLabel>
          {searchedQuery ? (
            <p className="text-xs mb-4" style={{ color: "var(--muted-foreground)" }}>
              Showing Google Places results for “{searchedQuery}”
            </p>
          ) : null}
          <div className="space-y-4">
            {results.map((place) => (
              <article
                key={place.id}
                className="rounded-xl p-5"
                style={{ backgroundColor: "var(--card)", border: "1px solid var(--border)" }}
              >
                <h3 className="font-semibold text-base mb-1" style={{ color: "var(--foreground)" }}>
                  {place.name}
                </h3>
                {place.address ? (
                  <p className="text-sm mb-2" style={{ color: "var(--muted-foreground)" }}>
                    {place.address}
                  </p>
                ) : null}
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm" style={{ color: "var(--muted-foreground)" }}>
                  {place.rating != null ? (
                    <span>
                      ★ {place.rating.toFixed(1)}
                      {place.ratingCount != null ? ` (${place.ratingCount})` : ""}
                    </span>
                  ) : null}
                  {place.phone ? <span>{place.phone}</span> : null}
                </div>
                <div className="flex flex-wrap gap-3 mt-3">
                  {place.mapsUrl ? (
                    <a
                      href={place.mapsUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-semibold underline"
                      style={{ color: "var(--primary)" }}
                    >
                      Open in Maps
                    </a>
                  ) : null}
                  {place.website ? (
                    <a
                      href={place.website}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm font-semibold underline"
                      style={{ color: "var(--primary)" }}
                    >
                      Website
                    </a>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
          <p className="text-xs mt-6 leading-relaxed" style={{ color: "var(--muted-foreground)" }}>
            These listings come from Google Places and are starting points for referral conversations —
            always verify credentials, insurance, and fit with your school counselor or care team.
          </p>
        </div>
      ) : null}
    </ToolPage>
  );
}
