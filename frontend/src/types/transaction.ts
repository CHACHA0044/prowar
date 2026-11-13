export type TransactionType = "UPI" | "NEFT" | "RTGS" | "CARD" | "ATM" | "TRANSFER";

export type TransactionStatus = "COMPLETED" | "PENDING" | "FAILED" | "BLOCKED";

export interface Transaction {
  transaction_id: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  transaction_type: TransactionType;
  timestamp: string;
  channel: string;
  location: string;
  transaction_status: TransactionStatus;
}

