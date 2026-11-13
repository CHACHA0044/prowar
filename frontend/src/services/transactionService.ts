import { apiFetch } from "./apiClient";
import { TransactionResponse, TransactionFilter, PaginatedTransactions } from "@/types/transaction";

function buildQuery(filter: TransactionFilter): string {
  const params = new URLSearchParams();
  Object.entries(filter).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") {
      params.set(k, String(v));
    }
  });
  const queryString = params.toString();
  return queryString ? `?${queryString}` : "";
}

export const transactionService = {
  list: (filter: TransactionFilter = {}) =>
    apiFetch<PaginatedTransactions>(`/api/v1/transactions${buildQuery(filter)}`),
  getById: (id: string) =>
    apiFetch<TransactionResponse>(`/api/v1/transactions/${id}`),
};
