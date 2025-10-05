import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import './index.css';
import { APP_NAME } from './constants';
import logoSrc from './assets/logo.png';
import About from './pages/About';
import MapPage from './pages/Map';
import Home from './pages/Home';

const App = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <NavLink to="/" className="flex items-center" aria-label={APP_NAME}>
              <img src={logoSrc} alt="SkyDashboard logo" className="h-8 w-auto" />
            </NavLink>
            <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `rounded-full px-3 py-1 transition-colors hover:text-indigo-600 ${
                    isActive ? 'bg-indigo-50 text-indigo-600' : ''
                  }`
                }
              >
                Home
              </NavLink>
              <NavLink
                to="/about"
                className={({ isActive }) =>
                  `rounded-full px-3 py-1 transition-colors hover:text-indigo-600 ${
                    isActive ? 'bg-indigo-50 text-indigo-600' : ''
                  }`
                }
              >
                About
              </NavLink>
              <NavLink
                to="/map"
                className={({ isActive }) =>
                  `rounded-full px-3 py-1 transition-colors hover:text-indigo-600 ${
                    isActive ? 'bg-indigo-50 text-indigo-600' : ''
                  }`
                }
              >
                Map
              </NavLink>
            </nav>
          </div>
        </header>
        <main className="mx-auto flex max-w-6xl flex-1 flex-col px-6 py-10">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/map" element={<MapPage />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto flex max-w-6xl flex-col gap-1 px-6 py-4 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
            <span>© {new Date().getFullYear()} {APP_NAME}</span>
            <span>Building air quality insights for everyone.</span>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
