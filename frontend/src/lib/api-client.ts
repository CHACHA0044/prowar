/**
 * Centralized API client.
 *
 * The backend base URL is read exclusively from NEXT_PUBLIC_API_URL. In
 * development it falls back to the local FastAPI server; in production a
 * missing variable produces a clear error instead of silently calling
 * localhost from the browser.
 */

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

const DEV_FALLBACK = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 30_000;

export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, "");
  }
  if (process.env.NODE_ENV === "production") {
    return "";
  }
  return DEV_FALLBACK;
}

export function buildApiUrl(path: string): string {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not configured. Set it to the Render backend URL in Vercel."
    );
  }
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

class ApiClient {
  public getBaseUrl(): string {
    return getApiBaseUrl();
  }

  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  async post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  private async request<T>(endpoint: string, options: RequestInit): Promise<T> {
    const url = buildApiUrl(endpoint);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          Accept: "application/json",
          ...(options.headers || {}),
        },
        cache: "no-store",
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorData: { error?: ApiError; message?: string; detail?: string } | null = null;
        try {
          errorData = await response.json();
        } catch {
          // Response was not JSON.
        }

        const message =
          errorData?.error?.message ||
          errorData?.detail ||
          errorData?.message ||
          `HTTP Error ${response.status}: ${response.statusText}`;

        throw new Error(message);
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new Error("The backend request timed out. Please retry.");
      }
      if (err instanceof Error) {
        throw err;
      }
      throw new Error("An unexpected network error occurred while connecting to the backend.");
    } finally {
      clearTimeout(timeout);
    }
  }
}

export const apiClient = new ApiClient();
