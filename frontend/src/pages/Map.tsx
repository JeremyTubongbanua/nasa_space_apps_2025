import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import { Map, Marker, ZoomControl, type Bounds } from 'pigeon-maps';
import Modal from '../components/Modal';
import { API_BASE_URL } from '../constants';

type LocationRecord = {
  latitude: number;
  longitude: number;
  files: string[];
  location_name?: string | null;
};

type Location = LocationRecord & { id: string };

type MeasurementRecord = {
  location_id?: number;
  location_name?: string | null;
  parameter?: string | null;
  value?: number | null;
  unit?: string | null;
  datetimeUtc?: string | null;
  datetimeLocal?: string | null;
  timezone?: string | null;
  provider?: string | null;
  owner_name?: string | null;
  [key: string]: unknown;
};

const DEFAULT_CENTER: [number, number] = [43.6532, -79.3832];
const DEFAULT_ZOOM = 4;
const PREVIEW_LIMIT = 10;
const MAX_PARAMETERS_IN_PREVIEW = 8;

type SensorSource = 'openaq' | 'openmeteo' | 'tempo' | 'unknown';

const SENSOR_SOURCE_COLORS: Record<SensorSource, string> = {
  openaq: '#7c3aed',
  openmeteo: '#facc15',
  tempo: '#38bdf8',
  unknown: '#94a3b8',
};

const SENSOR_SOURCE_LABELS: Record<SensorSource, string> = {
  openaq: 'OpenAQ',
  openmeteo: 'Open-Meteo',
  tempo: 'NASA TEMPO',
  unknown: 'Other',
};

const SENSOR_SOURCE_KEY_ORDER: SensorSource[] = ['openaq', 'openmeteo', 'tempo'];
const SENSOR_LEGEND_LINK = '#';

const getMeasurementCacheKey = (locationId: string, parameter: string, scope: string = 'all') =>
  `${locationId}:${parameter}:${scope}`;

const inferSourceFromMetadata = (locationId: string, files: string[]): SensorSource => {
  const lowerId = locationId.toLowerCase();
  const filesBlob = files.join(' ').toLowerCase();

  if (lowerId.startsWith('tempo') || filesBlob.includes('tempo')) {
    return 'tempo';
  }
  if (lowerId.startsWith('openmeteo') || filesBlob.includes('openmeteo')) {
    return 'openmeteo';
  }
  if (lowerId.startsWith('openaq') || filesBlob.includes('openaq')) {
    return 'openaq';
  }

  return 'openaq';
};

const inferSourceFromRecords = (records: MeasurementRecord[]): SensorSource | undefined => {
  for (const record of records) {
    const provider = (record.provider ?? '').toString().toLowerCase();
    const owner = (record.owner_name ?? '').toString().toLowerCase();

    if (provider.includes('tempo') || owner.includes('tempo')) {
      return 'tempo';
    }
    if (provider.includes('open-meteo') || provider.includes('openmeteo') || owner.includes('open-meteo')) {
      return 'openmeteo';
    }
    if (
      provider.includes('openaq') ||
      owner.includes('openaq') ||
      provider.includes('airnow') ||
      owner.includes('airnow')
    ) {
      return 'openaq';
    }
  }
  return undefined;
};

const GRANULARITY_OPTIONS: Array<{ id: 'hourly' | 'daily' | 'weekly'; label: string }> = [
  { id: 'hourly', label: 'Hourly' },
  { id: 'daily', label: 'Daily' },
  { id: 'weekly', label: 'Weekly' },
];

type AggregatedPoint = {
  timestamp: number;
  label: string;
  value: number;
};

const formatISODate = (date: Date) => date.toISOString().slice(0, 10);

const getBucketStart = (date: Date, granularity: 'hourly' | 'daily' | 'weekly') => {
  const bucket = new Date(date.getTime());
  if (granularity === 'hourly') {
    bucket.setMinutes(0, 0, 0);
    return bucket;
  }
  if (granularity === 'daily') {
    bucket.setHours(0, 0, 0, 0);
    return bucket;
  }
  // weekly: align to Monday
  const day = bucket.getDay();
  const diff = (day + 6) % 7; // number of days since Monday
  bucket.setHours(0, 0, 0, 0);
  bucket.setDate(bucket.getDate() - diff);
  return bucket;
};

const formatBucketLabel = (date: Date, granularity: 'hourly' | 'daily' | 'weekly') => {
  if (granularity === 'hourly') {
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  if (granularity === 'daily') {
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  }
  const endOfWeek = new Date(date.getTime());
  endOfWeek.setDate(endOfWeek.getDate() + 6);
  return `${date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} – ${endOfWeek.toLocaleDateString(
    undefined,
    { month: 'short', day: 'numeric' },
  )}`;
};

const aggregateMeasurements = (records: MeasurementRecord[], granularity: 'hourly' | 'daily' | 'weekly') => {
  const buckets = new Map<number, { sum: number; count: number; label: string }>();

  records.forEach((record) => {
    const value = record.value != null ? Number(record.value) : null;
    if (value == null || Number.isNaN(value)) {
      return;
    }
    const timestampStr = record.datetimeLocal ?? record.datetimeUtc;
    if (!timestampStr) {
      return;
    }
    const date = new Date(timestampStr);
    if (Number.isNaN(date.getTime())) {
      return;
    }
    const bucket = getBucketStart(date, granularity);
    const bucketKey = bucket.getTime();
    const entry = buckets.get(bucketKey) ?? { sum: 0, count: 0, label: formatBucketLabel(bucket, granularity) };
    entry.sum += value;
    entry.count += 1;
    buckets.set(bucketKey, entry);
  });

  return Array.from(buckets.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([timestamp, entry]) => ({ timestamp, label: entry.label, value: entry.sum / entry.count })) as AggregatedPoint[];
};

const MapPage = () => {
  const [locationCache, setLocationCache] = useState<Record<string, LocationRecord>>({});
  const [locationIds, setLocationIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [center, setCenter] = useState<[number, number]>(DEFAULT_CENTER);
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [selectedLocationId, setSelectedLocationId] = useState<string | null>(null);
  const [selectedParameter, setSelectedParameter] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [granularity, setGranularity] = useState<'hourly' | 'daily' | 'weekly'>('hourly');
  const [bounds, setBounds] = useState<Bounds | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [locationNames, setLocationNames] = useState<Record<string, string>>({});
  const locationNamesRef = useRef(locationNames);
  const [locationSources, setLocationSources] = useState<Record<string, SensorSource>>({});
  const locationSourcesRef = useRef(locationSources);
  const [locationParameters, setLocationParameters] = useState<Record<string, string[]>>({});
  const [measurementsCache, setMeasurementsCache] = useState<Record<string, MeasurementRecord[]>>({});
  const [activeMeasurements, setActiveMeasurements] = useState<MeasurementRecord[]>([]);
  const [parameterLoading, setParameterLoading] = useState(false);
  const [measurementLoading, setMeasurementLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const fetchedLocationIds = useRef(new Set<string>());
  const isMountedRef = useRef(true);

  useEffect(() => {
    locationNamesRef.current = locationNames;
  }, [locationNames]);

  useEffect(() => {
    locationSourcesRef.current = locationSources;
  }, [locationSources]);

  useEffect(() => () => {
    isMountedRef.current = false;
  }, []);

  const fetchParameterList = async (locationId: string) => {
    if (locationParameters[locationId]) {
      return locationParameters[locationId];
    }

    const response = await fetch(`${API_BASE_URL}/locations/${locationId}`);
    if (!response.ok) {
      throw new Error(`Failed to load parameters (status ${response.status})`);
    }

    const payload: unknown = await response.json();
    if (Array.isArray(payload)) {
      const parameters = payload.filter((item): item is string => typeof item === 'string');
      setLocationParameters((prev) => ({ ...prev, [locationId]: parameters }));
      return parameters;
    }

    if (payload && typeof payload === 'object' && 'error' in payload) {
      throw new Error(String((payload as { error?: unknown }).error ?? 'Parameter lookup failed'));
    }

    throw new Error('Unexpected parameter response');
  };

  const fetchMeasurements = async (locationId: string, parameter: string) => {
    const cacheKey = getMeasurementCacheKey(locationId, parameter);
    const cached = measurementsCache[cacheKey];
    if (cached) {
      return cached;
    }

    const endpoint = `${API_BASE_URL}/locations/${locationId}/${parameter}`;

    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`Failed to load measurements (status ${response.status})`);
    }

    const payload: unknown = await response.json();
    if (Array.isArray(payload)) {
      const records = payload.filter(
        (entry): entry is MeasurementRecord => Boolean(entry) && typeof entry === 'object' && !Array.isArray(entry),
      );
      setMeasurementsCache((prev) => ({ ...prev, [cacheKey]: records }));
      return records;
    }

    if (payload && typeof payload === 'object' && 'error' in payload) {
      throw new Error(String((payload as { error?: unknown }).error ?? 'Measurement lookup failed'));
    }

    throw new Error('Unexpected measurement response');
  };

  const syncSourceFromRecords = (locationId: string, records: MeasurementRecord[]) => {
    const derived = inferSourceFromRecords(records);
    if (derived && locationSourcesRef.current[locationId] !== derived) {
      setLocationSources((prev) => ({ ...prev, [locationId]: derived }));
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    const fetchLocations = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/locations`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Failed with status ${response.status}`);
        }
        const data: Record<string, LocationRecord> = await response.json();
        setLocationCache(data);
        setLocationIds(Object.keys(data));
        setLocationNames((prev) => {
          const next = { ...prev };
          Object.entries(data).forEach(([id, location]) => {
            if (location.location_name) {
              next[id] = location.location_name;
            }
          });
          return next;
        });
        setLocationSources((prev) => {
          const next = { ...prev };
          Object.entries(data).forEach(([id, location]) => {
            if (!next[id]) {
              next[id] = inferSourceFromMetadata(id, location.files ?? []);
            }
          });
          return next;
        });
        const firstEntry = Object.entries(data)[0];
        if (firstEntry) {
          const [, location] = firstEntry;
          setCenter([location.latitude, location.longitude]);
        }
        setError(null);
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          return;
        }
        setError('We could not load monitoring locations. Please verify the API is running and try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchLocations();

    return () => controller.abort();
  }, []);

  const visibleLocations = useMemo(() => {
    const allLocations: Location[] = locationIds
      .map((id) => {
        const record = locationCache[id];
        return record ? { id, ...record } : null;
      })
      .filter((record): record is Location => Boolean(record));

    if (!bounds) {
      return allLocations;
    }

    const {
      ne: [maxLat, maxLng],
      sw: [minLat, minLng],
    } = bounds;

    const longitudeInBounds = (longitude: number) => {
      if (minLng <= maxLng) {
        return longitude >= minLng && longitude <= maxLng;
      }
      // Handle bounding boxes that cross the antimeridian.
      return longitude >= minLng || longitude <= maxLng;
    };

    return allLocations.filter((location) => {
      const { latitude, longitude } = location;
      return latitude >= minLat && latitude <= maxLat && longitudeInBounds(longitude);
    });
  }, [bounds, locationIds, locationCache]);

  useEffect(() => {
    const idsNeedingNames = visibleLocations
      .filter((location) => !locationNamesRef.current[location.id] && !fetchedLocationIds.current.has(location.id))
      .map((location) => location.id);

    idsNeedingNames.forEach((id) => {
      fetchedLocationIds.current.add(id);

      (async () => {
        let derivedName = locationNamesRef.current[id] ?? `Location ${id}`;

        try {
          const parameters = await fetchParameterList(id);

            if (parameters.length > 0) {
              try {
                const measurements = await fetchMeasurements(id, parameters[0]);
                const withName = measurements.find(
                  (record) => typeof record.location_name === 'string' && record.location_name && record.location_name.trim().length > 0,
                );
                if (withName?.location_name) {
                  derivedName = withName.location_name;
                }
                syncSourceFromRecords(id, measurements);
              } catch {
                // Swallow measurement errors; fallback name will be used.
              }
            }

          if (isMountedRef.current) {
            setLocationNames((prev) => ({ ...prev, [id]: derivedName }));
          }
        } catch {
          if (isMountedRef.current) {
            setLocationNames((prev) => ({ ...prev, [id]: 'Name unavailable' }));
          }
          fetchedLocationIds.current.delete(id);
        }
      })();
    });
  }, [visibleLocations]);

  useEffect(() => {
    const idsMissingParameters = visibleLocations
      .filter((location) => !locationParameters[location.id])
      .map((location) => location.id);

    if (idsMissingParameters.length === 0) {
      return;
    }

    let cancelled = false;

    const loadParameters = async () => {
      await Promise.all(
        idsMissingParameters.map(async (id) => {
          try {
            const parameters = await fetchParameterList(id);
            if (!cancelled) {
              setLocationParameters((prev) => ({ ...prev, [id]: parameters }));
            }
          } catch {
            // Ignore missing parameter errors; sidebar keeps placeholder.
          }
        }),
      );
    };

    void loadParameters();

    return () => {
      cancelled = true;
    };
  }, [visibleLocations, locationParameters]);

  useEffect(() => {
    if (!selectedLocationId) {
      setSelectedParameter(null);
      setActiveMeasurements([]);
      setModalError(null);
      setDateFrom('');
      setDateTo('');
      return;
    }

    let cancelled = false;
    setActiveMeasurements([]);
    setModalError(null);
    setParameterLoading(true);

    const initialiseParameters = async () => {
      try {
        const parameters = await fetchParameterList(selectedLocationId);
        if (cancelled) {
          return;
        }

        if (parameters.length === 0) {
          setSelectedParameter(null);
          return;
        }

        setSelectedParameter((prev) => (prev && parameters.includes(prev) ? prev : parameters[0] || null));
      } catch {
        if (!cancelled) {
          setSelectedParameter(null);
          setModalError('We could not load sensor parameters. Please try again.');
        }
      } finally {
        if (!cancelled) {
          setParameterLoading(false);
        }
      }
    };

    void initialiseParameters();

    return () => {
      cancelled = true;
    };
  }, [selectedLocationId]);

  useEffect(() => {
    if (!selectedLocationId || !selectedParameter) {
      setActiveMeasurements([]);
      setMeasurementLoading(false);
      return;
    }

    const cacheKey = getMeasurementCacheKey(selectedLocationId, selectedParameter);
    const cached = measurementsCache[cacheKey];

    if (cached) {
      setActiveMeasurements(cached);
      setMeasurementLoading(false);
      syncSourceFromRecords(selectedLocationId, cached);
      return;
    }

    let cancelled = false;
    setMeasurementLoading(true);
    setModalError(null);

    const loadMeasurementsForModal = async () => {
      try {
        const records = await fetchMeasurements(selectedLocationId, selectedParameter);
        if (!cancelled && isMountedRef.current) {
          setActiveMeasurements(records);

          syncSourceFromRecords(selectedLocationId, records);

          if (!locationNamesRef.current[selectedLocationId]) {
            const withName = records.find(
              (record) => typeof record.location_name === 'string' && record.location_name && record.location_name.trim().length > 0,
            );

            if (withName?.location_name) {
              setLocationNames((prev) => ({ ...prev, [selectedLocationId]: withName.location_name as string }));
            }
          }
        }
      } catch {
        if (!cancelled && isMountedRef.current) {
          setActiveMeasurements([]);
          setModalError('We could not load measurements for this selection.');
        }
      } finally {
        if (!cancelled && isMountedRef.current) {
          setMeasurementLoading(false);
        }
      }
    };

    void loadMeasurementsForModal();

    return () => {
      cancelled = true;
    };
  }, [selectedLocationId, selectedParameter, measurementsCache]);
  useEffect(() => {
    if (activeMeasurements.length === 0) {
      return;
    }

    const timestamps = activeMeasurements
      .map((record) => Date.parse(record.datetimeLocal ?? record.datetimeUtc ?? ''))
      .filter((value) => !Number.isNaN(value))
      .sort((a, b) => a - b);

    if (timestamps.length === 0) {
      return;
    }

    if (!dateFrom) {
      setDateFrom(formatISODate(new Date(timestamps[0])));
    }
    if (!dateTo) {
      setDateTo(formatISODate(new Date(timestamps[timestamps.length - 1])));
    }
  }, [activeMeasurements, dateFrom, dateTo]);

  const formatCoordinate = (value: number) => value.toFixed(4);
  const totalLocations = locationIds.length;
  const visibleCount = visibleLocations.length;
  const parameterOptions = selectedLocationId ? locationParameters[selectedLocationId] ?? [] : [];

  const findLocation = (id: string | null): Location | null => {
    if (!id) {
      return null;
    }
    const record = locationCache[id];
    return record ? { id, ...record } : null;
  };
  const selectedLocation = findLocation(selectedLocationId);
  const selectedLocationName =
    (selectedLocationId && locationNames[selectedLocationId]) ??
    selectedLocation?.location_name ??
    (selectedLocationId ? `Location ${selectedLocationId}` : '');
  const getLocationSource = (locationId: string): SensorSource => locationSources[locationId] ?? 'unknown';
  const getLocationColor = (locationId: string) => SENSOR_SOURCE_COLORS[getLocationSource(locationId)];
  const getLocationSourceLabel = (locationId: string) => SENSOR_SOURCE_LABELS[getLocationSource(locationId)];
  const selectedLocationSourceLabel = selectedLocationId ? getLocationSourceLabel(selectedLocationId) : '';
  const selectedLocationSourceColor = selectedLocationId
    ? getLocationColor(selectedLocationId)
    : SENSOR_SOURCE_COLORS.unknown;
  const filteredMeasurements = useMemo(() => {
    if (activeMeasurements.length === 0) {
      return [] as MeasurementRecord[];
    }

    const fromTimestamp = dateFrom ? new Date(`${dateFrom}T00:00:00`).getTime() : null;
    const toTimestamp = dateTo ? new Date(`${dateTo}T23:59:59`).getTime() : null;

    return activeMeasurements.filter((record) => {
      const timestamp = Date.parse(record.datetimeLocal ?? record.datetimeUtc ?? '');
      if (Number.isNaN(timestamp)) {
        return false;
      }
      if (fromTimestamp && timestamp < fromTimestamp) {
        return false;
      }
      if (toTimestamp && timestamp > toTimestamp) {
        return false;
      }
      return true;
    });
  }, [activeMeasurements, dateFrom, dateTo]);

  const aggregatedSeries = useMemo(
    () => aggregateMeasurements(filteredMeasurements, granularity),
    [filteredMeasurements, granularity],
  );

  const aggregatedPreview = useMemo(
    () => (aggregatedSeries.length > 12 ? aggregatedSeries.slice(-12) : aggregatedSeries),
    [aggregatedSeries],
  );

  const measurementUnit = useMemo(() => {
    const recordWithUnit = filteredMeasurements.find((record) => record.unit);
    return recordWithUnit?.unit ?? activeMeasurements.find((record) => record.unit)?.unit ?? '';
  }, [filteredMeasurements, activeMeasurements]);

  const handleLocationSelect = (locationId: string) => {
    setSelectedLocationId(locationId);
    setSelectedParameter(null);
    setDateFrom('');
    setDateTo('');
    setActiveMeasurements([]);
    setModalError(null);
  };

  const handleParameterChange = (parameter: string) => {
    setSelectedParameter(parameter);
  };

  const handleDateFromChange = (event: ChangeEvent<HTMLInputElement>) => {
    setDateFrom(event.target.value);
  };

  const handleDateToChange = (event: ChangeEvent<HTMLInputElement>) => {
    setDateTo(event.target.value);
  };

  const handleClearDateRange = () => {
    setDateFrom('');
    setDateTo('');
  };

  const handleGranularityChange = (next: 'hourly' | 'daily' | 'weekly') => {
    setGranularity(next);
  };

  const handleModalClose = () => {
    setSelectedLocationId(null);
    setSelectedParameter(null);
    setDateFrom('');
    setDateTo('');
    setActiveMeasurements([]);
    setModalError(null);
    setParameterLoading(false);
    setMeasurementLoading(false);
  };

  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchError('Enter a city or address to search.');
      return;
    }

    setSearchLoading(true);
    setSearchError(null);

    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`);
      if (!response.ok) {
        throw new Error(`Geocoding failed with status ${response.status}`);
      }
      const payload = (await response.json()) as Array<{ lat: string; lon: string }>;
      if (payload.length === 0) {
        setSearchError('No results found for that location.');
        return;
      }

      const { lat, lon } = payload[0];
      const latNum = Number(lat);
      const lonNum = Number(lon);

      if (Number.isFinite(latNum) && Number.isFinite(lonNum)) {
        setCenter([latNum, lonNum]);
        setZoom(12);
      }
    } catch (error) {
      setSearchError((error as Error).message || 'We could not search for that location right now.');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void performSearch(searchQuery);
  };

  return (
    <div className="flex flex-1 flex-col gap-6 py-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex w-full max-w-xl flex-col gap-3">
          <h1 className="text-3xl font-semibold text-slate-900">Map</h1>
          <p className="text-sm text-slate-500">
            Explore locations currently ingested by the aggregator. Click a point to inspect the parameters available and
            preview recent measurements.
          </p>
          <form className="flex flex-col gap-2 sm:flex-row" onSubmit={handleSearchSubmit}>
            <label className="flex-1">
              <span className="sr-only">Search for a location</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  if (searchError) {
                    setSearchError(null);
                  }
                }}
                placeholder="Search for a city, address, or coordinates"
                className="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                autoComplete="off"
              />
            </label>
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              disabled={searchLoading}
            >
              {searchLoading ? 'Searching…' : 'Go'}
            </button>
          </form>
          {searchError && (
            <p className="text-sm text-red-500">{searchError}</p>
          )}
        </div>
        <a
          href={SENSOR_LEGEND_LINK}
          className="inline-flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm transition hover:border-indigo-200 hover:text-indigo-600"
        >
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">Legend</span>
          <div className="flex flex-col gap-2">
            {SENSOR_SOURCE_KEY_ORDER.map((source) => (
              <div key={source} className="flex items-center gap-3">
                <span
                  className="inline-flex h-3 w-3 rounded-full"
                  style={{ backgroundColor: SENSOR_SOURCE_COLORS[source] }}
                  aria-hidden
                />
                <span className="text-sm font-medium text-slate-600">{SENSOR_SOURCE_LABELS[source]}</span>
              </div>
            ))}
          </div>
        </a>
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-medium text-slate-700">Locations map</h2>
          </div>
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-600">
            Viewing {visibleCount} / {totalLocations}
          </span>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row">
          <aside className="max-h-[480px] w-full max-w-sm overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Visible sensors</h3>
              <span className="text-xs font-medium text-slate-400">{visibleCount}</span>
            </div>
            {visibleLocations.length === 0 ? (
              <p className="text-sm text-slate-500">Pan or zoom the map to reveal monitoring points.</p>
            ) : (
              <ul className="flex flex-col gap-3">
                {visibleLocations.map((location) => {
                  const displayName =
                    locationNames[location.id] ?? location.location_name ?? `Location ${location.id}`;
                  const sourceColor = getLocationColor(location.id);
                  const sourceLabel = getLocationSourceLabel(location.id);
                  const parametersForLocation = locationParameters[location.id];
                  return (
                    <li key={location.id}>
                      <button
                        type="button"
                        onClick={() => handleLocationSelect(location.id)}
                        className="w-full rounded-2xl border border-transparent border-l-4 bg-white px-4 py-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                        style={{ borderLeftColor: sourceColor }}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: sourceColor }}
                            aria-hidden
                          />
                          <p className="text-sm font-semibold text-slate-700">{displayName}</p>
                        </div>
                        <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-400">{sourceLabel}</p>
                        {parametersForLocation ? (
                          parametersForLocation.length > 0 ? (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {parametersForLocation.slice(0, MAX_PARAMETERS_IN_PREVIEW).map((parameter) => (
                                <span
                                  key={parameter}
                                  className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-600"
                                >
                                  {parameter}
                                </span>
                              ))}
                              {parametersForLocation.length > MAX_PARAMETERS_IN_PREVIEW && (
                                <span className="text-xs font-medium text-slate-400">
                                  +{parametersForLocation.length - MAX_PARAMETERS_IN_PREVIEW} more
                                </span>
                              )}
                            </div>
                          ) : (
                            <p className="mt-2 text-xs text-slate-400">No parameters available yet.</p>
                          )
                        ) : (
                          <p className="mt-2 text-xs text-slate-400">Loading parameters…</p>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-200">
            <Map
              center={center}
              zoom={zoom}
              minZoom={2}
              height={480}
              onBoundsChanged={({ center: newCenter, zoom: newZoom, bounds: newBounds }) => {
                setCenter(newCenter);
                setZoom(newZoom);
                setBounds(newBounds);
              }}
              metaWheelZoom
            >
              <ZoomControl />
              {visibleLocations.map((location) => (
                <Marker
                  key={location.id}
                  anchor={[location.latitude, location.longitude]}
                  width={32}
                  color={getLocationColor(location.id)}
                  onClick={() => handleLocationSelect(location.id)}
                />
              ))}
            </Map>
            {loading && (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-white/70 text-sm font-medium text-slate-500">
                Loading locations…
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {!loading && totalLocations === 0 && !error && (
          <p className="mt-4 text-sm text-slate-500">No locations available yet.</p>
        )}
      </section>

      <Modal open={Boolean(selectedLocationId)} onClose={handleModalClose}>
        {selectedLocationId ? (
          <div className="flex flex-col gap-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-800">{selectedLocationName}</h2>
              <p className="text-sm text-slate-500">Sensor ID: {selectedLocationId}</p>
              <div className="mt-1 flex items-center gap-2 text-xs font-medium text-slate-500">
                <span
                  className="inline-flex h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: selectedLocationSourceColor }}
                  aria-hidden
                />
                <span>{selectedLocationSourceLabel}</span>
              </div>
            </div>

            {selectedLocation && (
              <dl className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-3 text-xs text-slate-500">
                <div className="flex flex-col gap-1">
                  <dt className="font-semibold uppercase tracking-wide text-slate-400">Latitude</dt>
                  <dd className="text-sm font-medium text-slate-700">{formatCoordinate(selectedLocation.latitude)}</dd>
                </div>
                <div className="flex flex-col gap-1">
                  <dt className="font-semibold uppercase tracking-wide text-slate-400">Longitude</dt>
                  <dd className="text-sm font-medium text-slate-700">{formatCoordinate(selectedLocation.longitude)}</dd>
                </div>
                <div className="col-span-2 flex flex-col gap-1">
                  <dt className="font-semibold uppercase tracking-wide text-slate-400">Sensor ID</dt>
                  <dd className="text-sm font-medium text-slate-700">{selectedLocation.id}</dd>
                </div>
              </dl>
            )}

            {modalError && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                {modalError}
              </div>
            )}

            {parameterLoading ? (
              <p className="text-sm text-slate-500">Loading parameters…</p>
            ) : parameterOptions.length === 0 ? (
              <p className="text-sm text-slate-500">No parameters available for this sensor yet.</p>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="flex flex-wrap gap-2">
                  {parameterOptions.map((parameter) => {
                    const active = parameter === selectedParameter;
                    return (
                      <button
                        key={parameter}
                        type="button"
                        onClick={() => handleParameterChange(parameter)}
                        className={`rounded-full border px-3 py-1 text-sm font-medium transition ${
                          active
                            ? 'border-indigo-500 bg-indigo-500 text-white shadow-sm'
                            : 'border-slate-200 bg-white text-slate-600 hover:border-indigo-200 hover:text-indigo-600'
                        }`}
                      >
                        {parameter}
                      </button>
                    );
                  })}
                </div>

                <div className="flex flex-col gap-3">
                  <div className="flex flex-wrap items-center gap-3 text-sm">
                    <label className="flex items-center gap-2 text-slate-600">
                      <span className="font-medium text-slate-500">From</span>
                      <input
                        type="date"
                        value={dateFrom}
                        onChange={handleDateFromChange}
                        className="rounded-lg border border-slate-200 px-2 py-1 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                      />
                    </label>
                    <label className="flex items-center gap-2 text-slate-600">
                      <span className="font-medium text-slate-500">To</span>
                      <input
                        type="date"
                        value={dateTo}
                        onChange={handleDateToChange}
                        className="rounded-lg border border-slate-200 px-2 py-1 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                      />
                    </label>
                    {(dateFrom || dateTo) && (
                      <button
                        type="button"
                        onClick={handleClearDateRange}
                        className="rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-500 transition hover:border-slate-300 hover:text-slate-700"
                      >
                        Clear
                      </button>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500">
                    <span className="uppercase tracking-wide text-slate-400">View as</span>
                    {GRANULARITY_OPTIONS.map((option) => {
                      const active = option.id === granularity;
                      return (
                        <button
                          key={option.id}
                          type="button"
                          onClick={() => handleGranularityChange(option.id)}
                          className={`rounded-full border px-3 py-1 transition ${
                            active
                              ? 'border-indigo-500 bg-indigo-500 text-white shadow-sm'
                              : 'border-slate-200 bg-white text-slate-600 hover:border-indigo-200 hover:text-indigo-600'
                          }`}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-3 text-sm text-slate-600">
                  <p className="font-medium text-slate-500">
                    Measurements · {GRANULARITY_OPTIONS.find((item) => item.id === granularity)?.label}
                    {measurementUnit ? ` (${measurementUnit})` : ''}
                  </p>
                  {measurementLoading ? (
                    <p className="mt-2 text-slate-500">Loading measurements…</p>
                  ) : filteredMeasurements.length === 0 ? (
                    <p className="mt-2 text-slate-500">No measurements match the current filters.</p>
                  ) : (
                    <div className="mt-2 space-y-3">
                      {aggregatedSeries.length > 0 && (
                        <div className="rounded-xl border border-slate-200 bg-white p-3">
                          <svg viewBox="0 0 100 100" className="h-40 w-full text-indigo-500">
                            {(() => {
                              const values = aggregatedSeries.map((point) => point.value);
                              const maxValue = Math.max(...values);
                              const minValue = Math.min(...values);
                              const range = maxValue - minValue || 1;
                              const chartHeight = 80;
                              const chartTop = 10;
                              const polylinePoints = aggregatedSeries
                                .map((point, index) => {
                                  const x =
                                    aggregatedSeries.length === 1
                                      ? 50
                                      : (index / (aggregatedSeries.length - 1)) * 100;
                                  const yValue = ((point.value - minValue) / range) * chartHeight;
                                  const y = chartTop + chartHeight - yValue;
                                  return `${x},${y}`;
                                })
                                .join(' ');
                              return (
                                <>
                                  <polyline
                                    points={polylinePoints}
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth={2}
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                  />
                                  {aggregatedSeries.map((point, index) => {
                                    const x =
                                      aggregatedSeries.length === 1
                                        ? 50
                                        : (index / (aggregatedSeries.length - 1)) * 100;
                                    const yValue = ((point.value - minValue) / range) * chartHeight;
                                    const y = chartTop + chartHeight - yValue;
                                    return <circle key={point.timestamp} cx={x} cy={y} r={1.8} fill="currentColor" />;
                                  })}
                                </>
                              );
                            })()}
                          </svg>
                          <div className="mt-2 grid gap-1 text-xs text-slate-500 sm:grid-cols-2">
                            {aggregatedPreview.map((point) => (
                              <div key={point.timestamp} className="flex items-center justify-between gap-2">
                                <span className="truncate">{point.label}</span>
                                <span className="font-semibold text-slate-700">{point.value.toFixed(2)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                        <p className="text-xs text-slate-500">
                          Showing {Math.min(filteredMeasurements.length, PREVIEW_LIMIT)} of {filteredMeasurements.length} filtered
                          records.
                        </p>
                        <table className="w-full table-fixed text-left text-xs">
                          <thead className="text-slate-400">
                            <tr>
                              <th className="w-40 px-2 py-1">Local Time</th>
                              <th className="w-24 px-2 py-1">Value</th>
                              <th className="w-20 px-2 py-1">Unit</th>
                              <th className="px-2 py-1">Source</th>
                            </tr>
                          </thead>
                          <tbody className="text-slate-600">
                            {filteredMeasurements.slice(0, PREVIEW_LIMIT).map((record, index) => (
                              <tr key={`${record.datetimeLocal ?? index}-${index}`} className="odd:bg-white even:bg-slate-100/80">
                                <td className="truncate px-2 py-1">{record.datetimeLocal ?? '—'}</td>
                                <td className="px-2 py-1 font-medium">{record.value ?? '—'}</td>
                                <td className="px-2 py-1">{record.unit ?? '—'}</td>
                                <td className="truncate px-2 py-1">{record.provider ?? '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  );
};

export default MapPage;
