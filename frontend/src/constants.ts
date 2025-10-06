const inferSecureFallback = () => {
  if (typeof window !== 'undefined') {
    const { protocol, host } = window.location;
    if (protocol === 'https:') {
      return `${protocol}//${host}/api`;
    }
  }
  return 'https://159.203.5.107/api';
};

export const API_BASE_URLS = [
  import.meta.env.VITE_API_PRIMARY ?? 'http://localhost:8000',
  import.meta.env.VITE_API_SECONDARY ?? 'http://159.203.5.107:8000',
  inferSecureFallback(),
] as const;

export const APP_NAME = 'SkyDashboard';
