import { APP_NAME } from '../constants';

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
  </div>
);

export default About;
