export type AccountType = "savings" | "current" | "wallet" | "merchant" | "corporate";

export type AccountStatus = "active" | "suspended" | "flagged" | "closed";

export interface Account {
  account_id: string;
  account_type: AccountType;
  account_status: AccountStatus;
  created_at: string;
}

