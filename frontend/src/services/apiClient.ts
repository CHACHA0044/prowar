import { buildApiUrl, getApiBaseUrl } from "@/lib/api-client";

const BASE_URL = getApiBaseUrl();

interface ErrorEnvelope {
  error?: { message?: string };
  detail?: string;
  message?: string;
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = buildApiUrl(path);
  const hasBody = options?.body !== undefined && options?.body !== null;
  const res = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let message = `API error ${res.status}: ${res.statusText}`;
    try {
      const body = (await res.json()) as ErrorEnvelope;
      message = body.error?.message || body.detail || body.message || message;
    } catch {
      // Non-JSON error body (e.g. proxy HTML page).
    }
    throw new Error(message);
  }

  const json = await res.json();
  return json.data !== undefined ? (json.data as T) : (json as T);
}

export { BASE_URL };
