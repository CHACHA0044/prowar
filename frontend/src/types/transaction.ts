export interface TransactionResponse {
  transaction_id: string;
  timestamp: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  channel: string;
  merchant_category: string;
  device_id?: string | null;
  location?: string | null;
  sender_balance_before?: number | null;
  transaction_status: string;
}

export interface TransactionFilter {
  search?: string;
  sender_id?: string;
  receiver_id?: string;
  channel?: string;
  merchant_category?: string;
  min_amount?: number;
  max_amount?: number;
  start_date?: string;
  end_date?: string;
  sort_by?: "timestamp" | "amount" | "transaction_id";
  sort_order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface PaginatedTransactions {
  items: TransactionResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
