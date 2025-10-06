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
  import.meta.env.VITE_API_PRIMARY,
  import.meta.env.VITE_API_SECONDARY,
  'http://localhost:8000',
  'http://127.0.0.1:8000',
  'http://159.203.5.107:8000',
  'http://159.203.5.107',
  'https://159.203.5.107:8000',
  'https://159.203.5.107',
  inferSecureFallback(),
] as const;

export const APP_NAME = 'SkyDashboard';
