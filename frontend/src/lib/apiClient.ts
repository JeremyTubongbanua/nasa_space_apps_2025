import { API_BASE_URLS } from '../constants';

type NonEmptyArray<T> = [T, ...T[]];

const normalizeBase = (value: string | undefined | null): string | null => {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.replace(/\/+$/, '');
};

const pageProtocol = typeof window !== 'undefined' ? window.location.protocol : null;

const configuredBases = Array.from(
  new Set(
    (API_BASE_URLS as readonly string[])
      .map((base) => normalizeBase(base))
      .filter((base): base is string => typeof base === 'string' && base.length > 0)
      .filter((base) => !(pageProtocol === 'https:' && base.startsWith('http://'))),
  ),
);

if (configuredBases.length === 0) {
  throw new Error('No API base URLs are configured. Set VITE_API_PRIMARY or check constants.ts.');
}

const API_BASES: NonEmptyArray<string> = configuredBases as NonEmptyArray<string>;

let cachedBase: string | null = null;

const RETRYABLE_STATUS = new Set([502, 503, 504]);

const buildUrl = (base: string, path: string) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
};

const cloneInit = (init?: RequestInit) => {
  if (!init) {
    return undefined;
  }
  const cloned: RequestInit = { ...init };
  const { headers } = init;
  if (headers instanceof Headers) {
    cloned.headers = new Headers(headers);
  } else if (Array.isArray(headers)) {
    cloned.headers = [...headers];
  } else if (headers && typeof headers === 'object') {
    cloned.headers = { ...headers } as HeadersInit;
  }
  return cloned;
};

const resolveAttemptOrder = (): NonEmptyArray<string> => {
  if (cachedBase && API_BASES.includes(cachedBase)) {
    const otherHosts = API_BASES.filter((base) => base !== cachedBase);
    return [cachedBase, ...otherHosts] as NonEmptyArray<string>;
  }
  return API_BASES;
};

export const apiFetch = async (path: string, init?: RequestInit) => {
  const errors: string[] = [];
  const attempts = resolveAttemptOrder();

  for (const base of attempts) {
    const url = buildUrl(base, path);
    try {
      const response = await fetch(url, cloneInit(init));
      if (RETRYABLE_STATUS.has(response.status)) {
        errors.push(`HTTP ${response.status} from ${url}`);
        continue;
      }
      cachedBase = base;
      return response;
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw error;
      }
      errors.push(`${url}: ${(error as Error).message}`);
    }
  }

  throw new Error(`All API hosts failed: ${errors.join('; ')}`);
};

export const getActiveApiBase = () => cachedBase ?? API_BASES[0];
