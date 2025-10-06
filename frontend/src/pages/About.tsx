import { APP_NAME } from '../constants';
import prototypesImage from '../assets/figma_prototypes.png';
import teamMembersImage from '../assets/members.png';

const About = () => (
  <div className="mx-auto flex max-w-3xl flex-col gap-4 py-10">
    <h1 className="text-3xl font-semibold text-slate-900">About {APP_NAME}</h1>
    <p className="text-slate-600">
      {APP_NAME} aggregates air quality metrics from OpenAQ, NASA TEMPO satellite data, and
      local weather forecasts to create a unified, easy-to-understand dashboard. The
      project showcases how environmental data can be combined to power proactive alerts
      and rich visualizations.
    </p>
    <p className="text-slate-600">
      This is an early build focused on establishing the core user experience. Over time
      we will add authenticated profiles, configurable notifications, and deeper
      analytics—while keeping the interface approachable for everyone.
    </p>
    <section className="mt-2 space-y-2 text-sm text-slate-600">
      <h2 className="text-base font-semibold text-slate-800">Open data sources</h2>
      <p>
        SkyDashboard is powered entirely by openly available datasets. Explore the raw sources we rely on:
      </p>
      <ul className="list-disc space-y-1 pl-5">
        <li>
          <a
            href="https://explore.openaq.org/lists/3613"
            target="_blank"
            rel="noreferrer"
            className="text-indigo-600 hover:text-indigo-500"
          >
            OpenAQ World Air Quality Measurements
          </a>
        </li>
        <li>
          <a
            href="https://open-meteo.com/"
            target="_blank"
            rel="noreferrer"
            className="text-indigo-600 hover:text-indigo-500"
          >
            Open-Meteo Forecast & Air Quality API
          </a>
        </li>
        <li>
          <a
            href="https://worldview.earthdata.nasa.gov/"
            target="_blank"
            rel="noreferrer"
            className="text-indigo-600 hover:text-indigo-500"
          >
            NASA Worldview / TEMPO satellite layers
          </a>
        </li>
      </ul>
    </section>
    <section className="mt-4 grid gap-6">
      <figure className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <img
          src={prototypesImage}
          alt="Design prototypes showing key screens for the Sky Dashboard experience"
          className="w-full rounded-2xl object-cover"
          loading="lazy"
        />
        <figcaption className="mt-2 text-sm text-slate-500">
          Early UI explorations capture the onboarding journey, core dashboard widgets, and forecasting tiles.
        </figcaption>
      </figure>
      <figure className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <img
          src={teamMembersImage}
          alt="Team members participating in the NASA Space Apps 2025 challenge"
          className="w-full rounded-2xl object-cover"
          loading="lazy"
        />
        <figcaption className="mt-2 text-sm text-slate-500">
          Meet the crew behind the project, collaborating across design, engineering, and storytelling.
        </figcaption>
      </figure>
    </section>
  </div>
);

export default About;
