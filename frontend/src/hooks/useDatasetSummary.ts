"use client";

import { useEffect, useState, useCallback } from "react";
import { DatasetSummaryResponse } from "@/types/dataset";
import { datasetService } from "@/services/datasetService";

export function useDatasetSummary() {
  const [data, setData] = useState<DatasetSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    datasetService
      .getSummary()
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load dataset summary");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
