import { Link } from 'react-router-dom';

import { APP_NAME } from '../constants';

const FEATURE_CARDS: Array<{
  title: string;
  description: string;
  to: string;
  cta: string;
  emoji: string;
}> = [
  {
    title: 'Live AQI Dashboard',
    description: 'View real-time air quality readings across the GTA and search any city worldwide.',
    to: '/aqi',
    cta: 'Open AQI monitor',
    emoji: '🌤️',
  },
  {
    title: 'Geospatial Map',
    description: 'Explore aggregated sensors and satellite overlays to understand spatial patterns.',
    to: '/map',
    cta: 'Explore the map',
    emoji: '🗺️',
  },
  {
    title: 'Personalization Quiz',
    description: 'Tell us about your sensitivities and interests so alerts and visuals match your needs.',
    to: '/quiz',
    cta: 'Take the quiz',
    emoji: '🧠',
  },
];

const Home = () => (
  <div className="mx-auto flex max-w-5xl flex-col gap-10 py-6 text-center sm:text-left">
    <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
      <h1 className="text-4xl font-semibold text-slate-900">Welcome to {APP_NAME}</h1>
      <p className="mt-4 text-lg text-slate-600">
        SkyDashboard unifies satellite feeds, surface measurements, and weather forecasts so you can understand and act on
        local air quality in seconds.
      </p>
      <p className="mt-3 text-base text-slate-500">
        Jump into a live AQI feed, inspect the sensor map, or tailor alerts with our personalization quiz.
      </p>
    </section>

    <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {FEATURE_CARDS.map((card) => (
        <article key={card.to} className="flex h-full flex-col justify-between gap-4 rounded-3xl border border-slate-200 bg-white p-6 text-left shadow-sm">
          <div className="space-y-3">
            <div className="text-4xl" aria-hidden>
              {card.emoji}
            </div>
            <h2 className="text-xl font-semibold text-slate-900">{card.title}</h2>
            <p className="text-sm text-slate-600">{card.description}</p>
          </div>
          <Link
            to={card.to}
            className="inline-flex w-fit items-center justify-center rounded-xl bg-indigo-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
          >
            {card.cta}
          </Link>
        </article>
      ))}
    </section>

    <section className="rounded-3xl border border-slate-200 bg-slate-50/70 p-6 text-left shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">What&apos;s in our stack?</h2>
      <ul className="mt-3 space-y-2 text-sm text-slate-600">
        <li>• OpenAQ and NASA TEMPO data pipelines power trustworthy AQI and pollutant trends.</li>
        <li>• Open-Meteo gives hyperlocal weather context for interpreting air quality changes.</li>
        <li>• FastAPI and React enable the customizable experiences you&apos;ll see across the app.</li>
      </ul>
    </section>
  </div>
);

export default Home;
