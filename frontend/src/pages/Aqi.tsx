import { FormEvent, useEffect, useMemo, useState } from 'react';

import { API_BASE_URL } from '../constants';

type AqiSnapshot = {
  slug?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  us_aqi?: number;
  timestamp?: string | null;
  units?: string | null;
  source?: string | null;
  error?: string;
};

type AqiBand = {
  label: string;
  range: string;
  description: string;
  badgeClass: string;
  backgroundColor: string;
};

type AqiSegment = AqiBand & { width: number };

const PRESET_LOCATIONS: string[] = ['ajax', 'north_york', 'oshawa', 'scarborough', 'toronto'];

const formatTimestamp = (timestamp?: string | null) => {
  if (!timestamp) {
    return '—';
  }
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) {
    return timestamp;
  }
  return parsed.toLocaleString();
};

const AQI_BANDS: Array<{ max: number; label: string; range: string; description: string; badgeClass: string }> = [
  {
    max: 50,
    label: 'Good',
    range: '0 – 50',
    description: 'Air quality poses little or no risk.',
    badgeClass: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
    backgroundColor: '#d1fae5',
  },
  {
    max: 100,
    label: 'Moderate',
    range: '51 – 100',
    description: 'Acceptable; some pollutants may affect sensitive individuals.',
    badgeClass: 'bg-amber-100 text-amber-700 border border-amber-200',
    backgroundColor: '#fef3c7',
  },
  {
    max: 150,
    label: 'Unhealthy for Sensitive Groups',
    range: '101 – 150',
    description: 'Members of sensitive groups may experience health effects.',
    badgeClass: 'bg-orange-100 text-orange-700 border border-orange-200',
    backgroundColor: '#ffedd5',
  },
  {
    max: 200,
    label: 'Unhealthy',
    range: '151 – 200',
    description: 'Everyone may begin to experience health effects.',
    badgeClass: 'bg-red-100 text-red-700 border border-red-200',
    backgroundColor: '#fee2e2',
  },
  {
    max: 300,
    label: 'Very Unhealthy',
    range: '201 – 300',
    description: 'Emergency conditions; health warnings of emergency conditions.',
    badgeClass: 'bg-purple-100 text-purple-700 border border-purple-200',
    backgroundColor: '#ede9fe',
  },
];

const HAZARDOUS_BAND: AqiBand = {
  label: 'Hazardous',
  range: '301+',
  description: 'Serious health effects; everyone should avoid outdoor exposure.',
  badgeClass: 'bg-rose-200 text-rose-800 border border-rose-300',
  backgroundColor: '#fecdd3',
};

const UNKNOWN_BAND: AqiBand = {
  label: 'Unknown',
  range: '—',
  description: 'No recent reading available.',
  badgeClass: 'bg-slate-200 text-slate-600 border border-slate-300',
  backgroundColor: '#e2e8f0',
};

const ALL_AQI_BANDS: AqiBand[] = [...AQI_BANDS, HAZARDOUS_BAND];

const buildMeterSegments = (): AqiSegment[] => {
  const segments: AqiSegment[] = [];
  const total = 500;
  let previous = 0;
  AQI_BANDS.forEach((band) => {
    const span = Math.max(band.max - previous, 0);
    segments.push({ ...band, width: span / total });
    previous = band.max;
  });
  const remaining = Math.max(total - previous, 0);
  segments.push({ ...HAZARDOUS_BAND, width: remaining / total });
  return segments;
};

const AQI_METER_SEGMENTS = buildMeterSegments();

const GOOD_AQI_TARGET = 50;

const resolveAqiBand = (value?: number): AqiBand => {
  if (value == null || Number.isNaN(value)) {
    return UNKNOWN_BAND;
  }
  for (const band of AQI_BANDS) {
    if (value <= band.max) {
      return band;
    }
  }
  return HAZARDOUS_BAND;
};

const AqiPage = () => {
  const [snapshots, setSnapshots] = useState<AqiSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<AqiSnapshot | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const loadSnapshots = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/aqi/current/preset`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Failed to load AQI snapshots (status ${response.status})`);
        }
        const payload: unknown = await response.json();
        if (Array.isArray(payload)) {
          setSnapshots(payload);
          setError(null);
        } else {
          throw new Error('Unexpected AQI payload shape');
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }
        setError('We could not load current AQI values. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadSnapshots();
    return () => controller.abort();
  }, []);

  const processedSnapshots = useMemo(() => {
    const bySlug = new Map<string, AqiSnapshot>();
    snapshots.forEach((snapshot) => {
      if (snapshot.slug) {
        bySlug.set(snapshot.slug, snapshot);
      }
    });
    return PRESET_LOCATIONS.map((slug) => {
      const entry = bySlug.get(slug);
      if (entry) {
        return entry;
      }
      return { slug, error: 'No data available yet.' };
    });
  }, [snapshots]);

  const handleSearchSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = searchQuery.trim();
    if (!query) {
      setSearchError('Enter a city or region to search.');
      setSearchResult(null);
      return;
    }

    setSearchLoading(true);
    setSearchError(null);
    setSearchResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/aqi/current?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        const message = payload?.detail ?? `Search failed with status ${response.status}`;
        setSearchError(message);
        return;
      }
      const payload = (await response.json()) as AqiSnapshot;
      setSearchResult(payload);
    } catch (err) {
      setSearchError('We could not search for that location right now.');
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <header className="text-center">
        <h1 className="text-4xl font-semibold text-slate-900">Air Quality Monitor</h1>
        <p className="mt-3 text-lg text-slate-600">
          Track real-time US AQI readings for the Greater Toronto Area and explore conditions anywhere in the world.
        </p>
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left">
            <div>
              <h2 className="text-2xl font-semibold text-slate-800">Target healthy air</h2>
              <p className="text-sm text-slate-500">
                Aim to keep your local Air Quality Index below <span className="font-semibold text-emerald-600">{GOOD_AQI_TARGET}</span>.
                Values above that start to affect sensitive groups.
              </p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
              <span>Good AQI target</span>
              <span className="text-[11px] font-medium opacity-70">0 – {GOOD_AQI_TARGET}</span>
            </span>
          </div>
          <div className="relative h-16 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
            <div className="absolute inset-0 flex">
              {AQI_METER_SEGMENTS.map((band) => (
                <div
                  key={band.label}
                  className="flex-none border-r border-white/60 first:rounded-l-2xl last:rounded-r-2xl"
                  style={{ backgroundColor: band.backgroundColor, width: `${band.width * 100}%` }}
                />
              ))}
            </div>
            <div className="absolute left-0 top-1/2 flex -translate-y-1/2 items-center gap-2 px-4">
              <span className="text-xs font-semibold text-slate-600">0</span>
            </div>
            <div className="absolute right-0 top-1/2 flex -translate-y-1/2 items-center gap-2 px-4">
              <span className="text-xs font-semibold text-slate-600">500</span>
            </div>
            <div className="absolute top-0 h-full border-l-2 border-emerald-600" style={{ left: `${(GOOD_AQI_TARGET / 500) * 100}%` }}>
              <span className="absolute -top-6 left-1/2 -translate-x-1/2 rounded-full bg-white px-2 py-0.5 text-[11px] font-medium text-emerald-600 shadow-sm">
                Target
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-800">Current AQI — GTA Focus</h2>
            <p className="text-sm text-slate-500">Live readings powered by Open-Meteo&apos;s air-quality API.</p>
          </div>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Loading current AQI data…</p>
        ) : error ? (
          <p className="mt-6 text-sm text-red-500">{error}</p>
        ) : (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {processedSnapshots.map((snapshot) => {
              const label = snapshot.location_name ?? snapshot.slug ?? 'Unknown location';
              const aqiValue = snapshot.us_aqi;
              const band = resolveAqiBand(aqiValue);
              return (
                <article
                  key={snapshot.slug ?? label}
                  className="flex h-full flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4"
                >
                  <div>
                    <h3 className="text-lg font-semibold text-slate-800">{label}</h3>
                    {snapshot.error ? (
                      <p className="mt-1 text-sm text-red-500">{snapshot.error}</p>
                    ) : (
                      <span className={`mt-2 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${band.badgeClass}`}>
                        <span>{band.label}</span>
                        <span className="text-[11px] font-medium opacity-80">{band.range}</span>
                      </span>
                    )}
                  </div>
                  {!snapshot.error && (
                    <>
                      <div className="flex items-baseline gap-2">
                        <span className="text-4xl font-bold text-indigo-600">{aqiValue ?? '—'}</span>
                        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          {snapshot.units ?? 'US AQI'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500">{band.description}</p>
                      <p className="text-xs text-slate-500">Updated {formatTimestamp(snapshot.timestamp)}</p>
                    </>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-800">Search Any Region</h2>
            <p className="text-sm text-slate-500">Use the Open-Meteo geocoder to pull a live AQI reading by city or region.</p>
          </div>
        </div>

        <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={handleSearchSubmit}>
          <label className="flex-1">
            <span className="sr-only">Search for AQI by location</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.target.value);
                if (searchError) {
                  setSearchError(null);
                }
              }}
              placeholder="Try New York, Paris, Manila, …"
              className="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              autoComplete="off"
            />
          </label>
          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            disabled={searchLoading}
          >
            {searchLoading ? 'Searching…' : 'Search'}
          </button>
        </form>
        {searchError && <p className="mt-2 text-sm text-red-500">{searchError}</p>}

        {searchResult && !searchResult.error && (
          <article className="mt-4 flex flex-col gap-2 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4">
            {(() => {
              const band = resolveAqiBand(searchResult.us_aqi);
              return (
                <>
                  <h3 className="text-lg font-semibold text-slate-800">
                    {searchResult.location_name ?? 'Resolved location'}
                  </h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-indigo-600">{searchResult.us_aqi ?? '—'}</span>
                    <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                      {searchResult.units ?? 'US AQI'}
                    </span>
                  </div>
                  <span className={`inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${band.badgeClass}`}>
                    <span>{band.label}</span>
                    <span className="text-[11px] font-medium opacity-80">{band.range}</span>
                  </span>
                  <p className="text-sm text-slate-500">{band.description}</p>
                  <p className="text-xs text-slate-500">Updated {formatTimestamp(searchResult.timestamp)}</p>
                </>
              );
            })()}
          </article>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3">
          <h2 className="text-2xl font-semibold text-slate-800">What does US AQI mean?</h2>
          <p className="text-sm text-slate-600">
            The US Air Quality Index translates pollutant concentrations into a simple 0–500 scale. Lower values indicate
            cleaner air; higher values signal more health risks. Each band corresponds to guidance from the US EPA.
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {ALL_AQI_BANDS.map((band) => (
              <div key={band.label} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${band.badgeClass}`}>
                  <span>{band.label}</span>
                  <span className="text-[11px] font-medium opacity-80">{band.range}</span>
                </span>
                <p className="mt-2 text-sm text-slate-600">{band.description}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400">
            US AQI measurements on SkyDashboard are sourced from the Open-Meteo Air Quality API.
          </p>
        </div>
      </section>
    </div>
  );
};

export default AqiPage;
