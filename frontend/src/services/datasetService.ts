import { apiFetch } from "./apiClient";
import { DatasetStatusResponse, DatasetSummaryResponse } from "@/types/dataset";

export const datasetService = {
  getStatus: () => apiFetch<DatasetStatusResponse>("/api/v1/dataset/status"),
  getSummary: () => apiFetch<DatasetSummaryResponse>("/api/v1/dataset/summary"),
};
