import { FormEvent, useState } from 'react';

import { apiFetch } from '../lib/apiClient';

type RegionResolution = {
  name: string;
  latitude: number;
  longitude: number;
};

type AqiSnapshot = {
  location_name?: string;
  latitude?: number;
  longitude?: number;
};

type InsightPayload = {
  status?: string;
  headline?: string;
  callouts?: string[];
  evidence?: string[];
  metrics?: Array<{ pollutant: string; severity?: string; value: number | null; unit?: string | null; timestamp?: string | null }>;
  context?: string[];
  advice?: string[];
  interest?: string[];
  footers?: string[];
  best_window?: string;
  overall_severity?: string;
  dominant_pollutant?: string | null;
  sensor?: {
    id: string;
    location_name?: string | null;
    latitude?: number;
    longitude?: number;
    measurements?: Record<string, { value: number | null; unit?: string | null; timestamp?: string | null }>;
  };
  sources?: Array<{ label: string; url: string }>;
  message?: string;
};

type QuizSubmissionResponse = {
  sms?: { status?: string; reason?: string };
  insights?: InsightPayload | null;
};

const QuizPage = () => {
  const [healthSensitivities, setHealthSensitivities] = useState<string[]>([]);
  const [activityType, setActivityType] = useState<string | null>(null);
  const [audience, setAudience] = useState<string | null>(null);
  const [interests, setInterests] = useState<string[]>([]);
  const [region, setRegion] = useState('');
  const [regionValidation, setRegionValidation] = useState<RegionResolution | null>(null);
  const [regionConfirmed, setRegionConfirmed] = useState<RegionResolution | null>(null);
  const [regionValidating, setRegionValidating] = useState(false);
  const [regionValidationError, setRegionValidationError] = useState<string | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [quizFeedback, setQuizFeedback] = useState<string | null>(null);
  const [insights, setInsights] = useState<InsightPayload | null>(null);
  const [submittedPayload, setSubmittedPayload] = useState<Record<string, unknown> | null>(null);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [subscriptionStatus, setSubscriptionStatus] = useState<string | null>(null);
  const [subscriptionSubmitting, setSubscriptionSubmitting] = useState(false);

  const toggleHealthSensitivity = (value: string) => {
    setInsights(null);
    setHealthSensitivities((prev) => {
      if (value === 'none') {
        return prev.includes('none') ? [] : ['none'];
      }
      const withoutNone = prev.filter((item) => item !== 'none');
      return withoutNone.includes(value)
        ? withoutNone.filter((item) => item !== value)
        : [...withoutNone, value];
    });
  };

  const toggleInterest = (value: string) => {
    setInsights(null);
    setInterests((prev) =>
      prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value],
    );
  };

  const selectActivityType = (value: string) => {
    setInsights(null);
    setActivityType(value);
  };

  const selectAudience = (value: string) => {
    setInsights(null);
    setAudience(value);
  };

  const handleRegionInputChange = (value: string) => {
    setRegion(value);
    setRegionValidation(null);
    setRegionConfirmed(null);
    setRegionValidationError(null);
    setInsights(null);
  };

  const performRegionValidation = async () => {
    const query = region.trim();
    if (!query) {
      setRegionValidation(null);
      setRegionConfirmed(null);
      setRegionValidationError('Enter a city or region before validating.');
      return;
    }

    setRegionValidating(true);
    setRegionValidationError(null);
    setRegionValidation(null);
    setRegionConfirmed(null);

    try {
      const response = await apiFetch(`/aqi/current?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        setRegionValidationError(payload?.detail ?? 'We could not validate that location.');
        return;
      }
      const payload = (await response.json()) as AqiSnapshot;
      if (typeof payload.latitude !== 'number' || typeof payload.longitude !== 'number') {
        setRegionValidationError('We could not find precise coordinates for that location.');
        return;
      }
      const name = payload.location_name && payload.location_name.trim().length > 0 ? payload.location_name : query;
      setRegionValidation({ name, latitude: payload.latitude, longitude: payload.longitude });
    } catch (error) {
      setRegionValidationError('We could not validate that location right now.');
    } finally {
      setRegionValidating(false);
    }
  };

  const handleRegionConfirm = () => {
    if (regionValidation) {
      setRegionConfirmed(regionValidation);
      setRegionValidationError(null);
    }
  };

  const handleRegionReject = () => {
    setRegionValidation(null);
    setRegionConfirmed(null);
    setRegionValidationError('Try refining the city or adding a country / province.');
  };

  const handleQuizSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setQuizFeedback(null);
    setInsights(null);

    if (healthSensitivities.length === 0) {
      setQuizFeedback('Select at least one health sensitivity (or choose None).');
      return;
    }

    if (!activityType) {
      setQuizFeedback('Select how you usually spend time outdoors.');
      return;
    }

    if (!audience) {
      setQuizFeedback('Tell us who you are checking air quality for.');
      return;
    }

    if (interests.length === 0) {
      setQuizFeedback('Pick at least one focus area for your insights.');
      return;
    }

    if (!region.trim()) {
      setQuizFeedback('Enter the city or region you care about.');
      return;
    }

    if (!regionConfirmed) {
      setQuizFeedback('Validate and confirm your region so we have accurate coordinates.');
      return;
    }

    const basePayload: Record<string, unknown> = {
      healthSensitivities,
      activityType,
      audience,
      interests,
      region: regionConfirmed.name,
      locationName: regionConfirmed.name,
      latitude: regionConfirmed.latitude,
      longitude: regionConfirmed.longitude,
    };

    setQuizSubmitting(true);
    try {
      const response = await apiFetch('/quiz/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(basePayload),
      });
      if (!response.ok) {
        const errorPayload = (await response.json().catch(() => null)) as { detail?: string } | null;
        setQuizFeedback(errorPayload?.detail ?? 'We could not save your responses right now.');
        setInsights(null);
        return;
      }
      const apiResponse = (await response.json().catch(() => null)) as QuizSubmissionResponse | null;
      setInsights(apiResponse?.insights ?? null);
      if (apiResponse?.sms?.status === 'sent') {
        setQuizFeedback('Thanks! You are subscribed — expect SMS updates when air quality changes.');
      } else if (apiResponse?.sms?.status === 'skipped') {
        setQuizFeedback(`Preferences saved. ${apiResponse.sms.reason ?? 'SMS delivery is temporarily disabled.'}`);
      } else {
        setQuizFeedback('Thanks! Your preferences are logged and will shape future recommendations.');
      }
      setSubmittedPayload(basePayload);
      setSubscriptionStatus(null);
      setPhoneNumber('');
    } catch (error) {
      setQuizFeedback('We could not save your responses right now.');
      setInsights(null);
      setSubmittedPayload(null);
    } finally {
      setQuizSubmitting(false);
    }
  };

  const handleSubscriptionSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!submittedPayload) {
      setSubscriptionStatus('Complete the quiz first.');
      return;
    }
    const trimmed = phoneNumber.trim();
    if (!trimmed) {
      setSubscriptionStatus('Enter a phone number to subscribe.');
      return;
    }
    setSubscriptionSubmitting(true);
    setSubscriptionStatus(null);

    try {
      const payload = { ...submittedPayload, phoneNumber: trimmed };
      const response = await apiFetch('/quiz/responses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorPayload = (await response.json().catch(() => null)) as { detail?: string } | null;
        setSubscriptionStatus(errorPayload?.detail ?? 'We could not save your subscription right now.');
        return;
      }
      const apiResponse = (await response.json().catch(() => null)) as QuizSubmissionResponse | null;
      if (apiResponse?.sms?.status === 'sent') {
        setSubscriptionStatus('Subscribed! You will receive real-time personalized AQ alerts when conditions change.');
      } else {
        setSubscriptionStatus(
          `Subscription saved. ${apiResponse?.sms?.reason ?? 'SMS delivery is temporarily disabled.'}`,
        );
      }
    } catch (error) {
      setSubscriptionStatus('We could not save your subscription right now.');
    } finally {
      setSubscriptionSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <header className="text-center">
        <h1 className="text-4xl font-semibold text-slate-900">Personalize Your Alerts</h1>
        <p className="mt-3 text-lg text-slate-600">
          Answer a few quick questions so we can tailor AQI insights and notification timing for you.
        </p>
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <form className="space-y-6" onSubmit={handleQuizSubmit}>
          <fieldset className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <legend className="text-lg font-semibold text-slate-800">Do you have any health sensitivities?</legend>
            <p className="text-sm text-slate-500">Affects how cautious the advice is.</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {[
                { id: 'asthma', label: 'Asthma / breathing issues' },
                { id: 'allergies', label: 'Allergies' },
                { id: 'heart_condition', label: 'Heart condition' },
                { id: 'none', label: 'None' },
              ].map((option) => {
                const checked = healthSensitivities.includes(option.id);
                return (
                  <label
                    key={option.id}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                      checked
                        ? 'border-indigo-500 bg-white text-slate-800 shadow-sm'
                        : 'border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-200'
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                      checked={checked}
                      onChange={() => toggleHealthSensitivity(option.id)}
                    />
                    <span>{option.label}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <fieldset className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <legend className="text-lg font-semibold text-slate-800">How do you usually spend your time outdoors?</legend>
            <p className="text-sm text-slate-500">Affects physical activity recommendations.</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {[
                { id: 'jogging', label: 'Jogging / running' },
                { id: 'cycling', label: 'Cycling / commuting' },
                { id: 'walking', label: 'Walking / casual outdoor time' },
                { id: 'work_outdoors', label: 'Work outdoors' },
                { id: 'mostly_indoors', label: 'Mostly indoors' },
              ].map((option) => (
                <label
                  key={option.id}
                  className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                    activityType === option.id
                      ? 'border-indigo-500 bg-white text-slate-800 shadow-sm'
                      : 'border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="activity_type"
                    className="mt-1 h-4 w-4 border-slate-300 text-indigo-500 focus:ring-indigo-500"
                    checked={activityType === option.id}
                    onChange={() => selectActivityType(option.id)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <legend className="text-lg font-semibold text-slate-800">Who are you checking the air quality for?</legend>
            <p className="text-sm text-slate-500">Adjusts tone and focus.</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {[
                { id: 'myself', label: 'Myself' },
                { id: 'family', label: 'My family / children' },
                { id: 'students', label: 'Students / group' },
                { id: 'awareness', label: 'General awareness' },
              ].map((option) => (
                <label
                  key={option.id}
                  className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                    audience === option.id
                      ? 'border-indigo-500 bg-white text-slate-800 shadow-sm'
                      : 'border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-200'
                  }`}
                >
                  <input
                    type="radio"
                    name="audience"
                    className="mt-1 h-4 w-4 border-slate-300 text-indigo-500 focus:ring-indigo-500"
                    checked={audience === option.id}
                    onChange={() => selectAudience(option.id)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <legend className="text-lg font-semibold text-slate-800">What do you want to know?</legend>
            <p className="text-sm text-slate-500">Choose the data emphasis for visuals & text.</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {[
                { id: 'health_alerts', label: 'Health and safety alerts' },
                { id: 'best_time_outdoors', label: 'Best time to go outdoors' },
                { id: 'trends', label: 'Weather + air trends' },
                { id: 'pollution_sources', label: 'Pollution sources and causes' },
              ].map((option) => {
                const checked = interests.includes(option.id);
                return (
                  <label
                    key={option.id}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border px-3 py-2 text-left text-sm transition ${
                      checked
                        ? 'border-indigo-500 bg-white text-slate-800 shadow-sm'
                        : 'border-slate-200 bg-white/70 text-slate-600 hover:border-indigo-200'
                    }`}
                  >
                    <input
                      type="checkbox"
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                      checked={checked}
                      onChange={() => toggleInterest(option.id)}
                    />
                    <span>{option.label}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <label className="flex flex-col gap-2 text-sm text-slate-600">
              <span className="text-base font-semibold text-slate-800">Which city or region should we track?</span>
              <input
                type="text"
                value={region}
                onChange={(event) => handleRegionInputChange(event.target.value)}
                placeholder="e.g. Toronto, North York"
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              />
            </label>
            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <button
                type="button"
                onClick={performRegionValidation}
                className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                disabled={regionValidating}
              >
                {regionValidating ? 'Validating…' : 'Validate location'}
              </button>
              {regionConfirmed && (
                <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-600">
                  <span>Confirmed</span>
                  <span>{regionConfirmed.name}</span>
                </span>
              )}
            </div>
            {regionValidationError && (
              <p className="mt-2 text-sm text-red-500">{regionValidationError}</p>
            )}
            {regionValidation && !regionConfirmed && !regionValidationError && (
              <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                <p className="font-semibold text-slate-800">Is this the right place?</p>
                <p className="mt-1 text-sm text-slate-600">{regionValidation.name}</p>
                <p className="text-xs text-slate-500">
                  Latitude {regionValidation.latitude.toFixed(4)}, Longitude {regionValidation.longitude.toFixed(4)}
                </p>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    onClick={handleRegionConfirm}
                    className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500"
                  >
                    Yes, use this location
                  </button>
                  <button
                    type="button"
                    onClick={handleRegionReject}
                    className="inline-flex items-center justify-center rounded-xl border border-slate-300 px-4 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-red-200 hover:text-red-500"
                  >
                    No, refine search
                  </button>
                </div>
              </div>
            )}
          </div>

          {typeof quizFeedback === 'string' && (
            <p
              className={`text-sm ${
                quizFeedback.startsWith('Thanks')
                  ? 'text-emerald-600'
                  : quizFeedback.startsWith('Preferences saved')
                    ? 'text-amber-600'
                    : 'text-red-500'
              }`}
            >
              {quizFeedback}
            </p>
          )}

          <button
            type="submit"
            className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            disabled={quizSubmitting}
          >
            {quizSubmitting ? 'Submitting…' : 'Submit Preferences'}
          </button>
        </form>
      </section>

      {insights && insights.status === 'ok' && (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50/60 p-6 shadow-sm">
          <h2 className="text-2xl font-semibold text-emerald-700">Your air quality briefing</h2>
          {insights.headline && <p className="mt-2 text-lg text-emerald-800">{insights.headline}</p>}
          <div className="mt-3 flex flex-wrap gap-3 text-xs font-semibold uppercase tracking-wide text-emerald-700">
            {insights.overall_severity && (
              <span className="rounded-full border border-emerald-300 bg-white px-3 py-1">
                Severity: {insights.overall_severity.replace('_', ' ')}
              </span>
            )}
            {insights.dominant_pollutant && (
              <span className="rounded-full border border-emerald-300 bg-white px-3 py-1">
                Dominant pollutant: {insights.dominant_pollutant}
              </span>
            )}
            {insights.best_window && (
              <span className="rounded-full border border-emerald-300 bg-white px-3 py-1">
                Best time outside: {insights.best_window}
              </span>
            )}
          </div>
          {insights.callouts && insights.callouts.length > 0 && (
            <div className="mt-4 space-y-2 text-sm text-emerald-900">
              {insights.callouts.map((entry, index) => (
                <p key={`callout-${index}`}>• {entry}</p>
              ))}
            </div>
          )}
          {insights.evidence && insights.evidence.length > 0 && (
            <div className="mt-4 space-y-2 rounded-2xl border border-emerald-200 bg-white p-4 text-sm text-emerald-900">
              <p className="font-semibold text-emerald-700">Why these results?</p>
              {insights.evidence.map((entry, index) => (
                <p key={`evidence-${index}`}>• {entry}</p>
              ))}
            </div>
          )}
          {insights.context && insights.context.length > 0 && (
            <div className="mt-4 space-y-2 rounded-2xl border border-emerald-200 bg-emerald-50/80 p-4 text-sm text-emerald-900">
              <p className="font-semibold text-emerald-700">Supporting metrics</p>
              {insights.context.map((entry, index) => (
                <p key={`context-${index}`}>• {entry}</p>
              ))}
            </div>
          )}
          {insights.metrics && insights.metrics.length > 0 && (
            <div className="mt-4 overflow-hidden rounded-2xl border border-emerald-200 bg-white text-sm">
              <table className="w-full table-fixed">
                <thead className="bg-emerald-100 text-emerald-800">
                  <tr>
                    <th className="px-3 py-2 text-left">Pollutant</th>
                    <th className="px-3 py-2 text-left">Value</th>
                    <th className="px-3 py-2 text-left">Severity</th>
                    <th className="px-3 py-2 text-left">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {insights.metrics.map((row, index) => (
                    <tr key={`metric-${index}`} className={index % 2 === 0 ? 'bg-white' : 'bg-emerald-50/70'}>
                      <td className="px-3 py-2 font-semibold text-emerald-800">{row.pollutant}</td>
                      <td className="px-3 py-2 text-emerald-700">
                        {row.value != null ? `${row.value.toFixed(1)} ${row.unit ?? ''}`.trim() : '—'}
                      </td>
                      <td className="px-3 py-2 text-emerald-700">{row.severity?.replace('_', ' ') ?? '—'}</td>
                      <td className="px-3 py-2 text-emerald-600 text-xs">{row.timestamp ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {insights.advice && insights.advice.length > 0 && (
            <div className="mt-4 space-y-2 text-sm text-emerald-900">
              {insights.advice.map((entry, index) => (
                <p key={`advice-${index}`}>• {entry}</p>
              ))}
            </div>
          )}
          {insights.interest && insights.interest.length > 0 && (
            <div className="mt-4 space-y-2 text-sm text-emerald-900">
              {insights.interest.map((entry, index) => (
                <p key={`interest-${index}`}>• {entry}</p>
              ))}
            </div>
          )}
          <div className="mt-4 space-y-2 text-xs text-emerald-900">
            {insights.footers?.map((entry, index) => (
              <p key={`footer-${index}`}>{entry}</p>
            ))}
          </div>
          {insights.sensor && (
            <div className="mt-6 flex flex-col gap-2 rounded-2xl border border-emerald-200 bg-white p-4 text-sm text-emerald-900">
              <p className="font-semibold text-emerald-700">Sensor reference</p>
              <p>
                {insights.sensor.location_name || 'Nearest sensor'} (ID {insights.sensor.id}) —
                {insights.sensor.latitude != null && insights.sensor.longitude != null
                  ? ` ${insights.sensor.latitude.toFixed(4)}, ${insights.sensor.longitude.toFixed(4)}`
                  : ''}
              </p>
              <a
                href={`/map?sensor=${encodeURIComponent(insights.sensor.id)}`}
                className="inline-flex w-fit items-center rounded-xl border border-emerald-400 px-3 py-1 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100"
              >
                View on map
              </a>
            </div>
          )}
          {insights.sources && (
            <div className="mt-4 space-y-1 text-xs text-emerald-700">
              <p className="font-semibold">Sources</p>
              {insights.sources.map((source) => (
                <a
                  key={source.label}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block text-emerald-600 hover:text-emerald-500"
                >
                  {source.label}
                </a>
              ))}
            </div>
          )}
        </section>
      )}
      {insights && insights.status !== 'ok' && insights.message && (
        <section className="rounded-3xl border border-amber-200 bg-amber-50/70 p-6 shadow-sm">
          <p className="text-sm text-amber-700">{insights.message}</p>
        </section>
      )}

      {insights && insights.status === 'ok' && (
        <section className="rounded-3xl border border-indigo-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Subscribe to alerts</h2>
          <p className="mt-2 text-sm text-slate-600">
            Subscribing to real time personalized notifications regarding air quality in your area.
          </p>
          <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubscriptionSubmit}>
            <label className="flex-1 text-sm text-slate-600">
              <span className="sr-only">Phone number</span>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(event) => setPhoneNumber(event.target.value)}
                placeholder="e.g. +1 555 555 1234"
                className="w-full rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 shadow-sm focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200"
              />
            </label>
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              disabled={subscriptionSubmitting}
            >
              {subscriptionSubmitting ? 'Subscribing…' : 'Subscribe'}
            </button>
          </form>
          {subscriptionStatus && (
            <p className="mt-2 text-sm text-indigo-600">{subscriptionStatus}</p>
          )}
        </section>
      )}
    </div>
  );
};

export default QuizPage;
