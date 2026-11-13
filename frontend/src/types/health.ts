export interface ComponentHealth {
  status: "healthy" | "unhealthy" | "degraded";
  message?: string;
  details?: Record<string, unknown>;
}

export interface SystemHealthResponse {
  status: "healthy" | "unhealthy" | "degraded";
  environment: string;
  timestamp: string;
  version: string;
  components: {
    api_gateway?: ComponentHealth;
    database?: ComponentHealth;
    ml_engine?: ComponentHealth;
    [key: string]: ComponentHealth | undefined;
  };
}

export interface DatabaseHealthResponse {
  status: string;
  connected: boolean;
  dialect: string;
  url_type: string;
  message: string;
  timestamp: string;
}

