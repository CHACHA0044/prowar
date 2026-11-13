import { apiClient } from "@/lib/api-client";
import { SystemHealthResponse, DatabaseHealthResponse } from "@/types/health";

export const healthService = {
  async getSystemHealth(): Promise<SystemHealthResponse> {
    return apiClient.get<SystemHealthResponse>("/api/v1/health");
  },

  async getDatabaseHealth(): Promise<DatabaseHealthResponse> {
    return apiClient.get<DatabaseHealthResponse>("/api/v1/health/database");
  },
};

