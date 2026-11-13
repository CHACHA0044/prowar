/**
 * Centralized API Client.
 * Handles environment-based backend base URL, timeouts, and structured error responses.
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

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl =
      process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";
  }

  public getBaseUrl(): string {
    return this.baseUrl;
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
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          Accept: "application/json",
          ...(options.headers || {}),
        },
        cache: "no-store",
      });

      if (!response.ok) {
        let errorData: { error?: ApiError; message?: string } | null = null;
        try {
          errorData = await response.json();
        } catch {
          // Response was not JSON
        }

        const message =
          errorData?.error?.message ||
          errorData?.message ||
          `HTTP Error ${response.status}: ${response.statusText}`;

        throw new Error(message);
      }

      return (await response.json()) as T;
    } catch (err) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error("An unexpected network error occurred while connecting to backend.");
    }
  }
}

export const apiClient = new ApiClient();

