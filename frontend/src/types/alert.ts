export type AlertSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type AlertStatus = "OPEN" | "UNDER_REVIEW" | "RESOLVED" | "DISMISSED";

export interface SecurityAlert {
  alert_id: string;
  transaction_id?: string;
  account_id: string;
  alert_type: string;
  severity: AlertSeverity;
  risk_score: number;
  explanation: string;
  created_at: string;
  status: AlertStatus;
}

