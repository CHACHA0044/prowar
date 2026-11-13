import { apiFetch } from "./apiClient";
import { SimulatorStatus } from "@/types/simulator";
import { getApiBaseUrl } from "@/lib/api-client";

export const simulatorService = {
  getStatus: () => apiFetch<SimulatorStatus>("/api/v1/simulator/status"),
  start: () => apiFetch<SimulatorStatus>("/api/v1/simulator/start", { method: "POST" }),
  pause: () => apiFetch<SimulatorStatus>("/api/v1/simulator/pause", { method: "POST" }),
  reset: () => apiFetch<SimulatorStatus>("/api/v1/simulator/reset", { method: "POST" }),
  setSpeed: (speed: number) =>
    apiFetch<SimulatorStatus>("/api/v1/simulator/speed", {
      method: "PATCH",
      body: JSON.stringify({ speed }),
    }),
  getStreamUrl: () => `${getApiBaseUrl()}/api/v1/simulator/stream`,
};
