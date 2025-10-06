export const API_BASE_URLS = [
  import.meta.env.VITE_API_PRIMARY ?? 'http://localhost:8000',
  import.meta.env.VITE_API_SECONDARY ?? 'http://159.203.5.107:8000',
] as const;

export const APP_NAME = 'SkyDashboard';
