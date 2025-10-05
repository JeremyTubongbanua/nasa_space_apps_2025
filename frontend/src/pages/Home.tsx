import { APP_NAME } from '../constants';

const Home = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6 text-center">
    <h1 className="text-4xl font-semibold text-slate-900">Welcome to {APP_NAME}</h1>
    <p className="max-w-2xl text-balance text-lg text-slate-600">
      SkyDashboard brings air quality, satellite, and local weather insights into a single
      place. Sign in, configure alerts, and stay informed about the air you breathe.
    </p>
  </div>
);

export default Home;
