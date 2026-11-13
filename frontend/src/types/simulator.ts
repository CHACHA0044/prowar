import { TransactionResponse } from "./transaction";

export interface SimulatorStatus {
  state: "IDLE" | "RUNNING" | "PAUSED" | "COMPLETED";
  speed_multiplier: number;
  current_replay_time?: string | null;
  processed_count: number;
  remaining_count: number;
  total_count: number;
  progress_percentage: number;
  started_at?: string | null;
  mode?: string;
}

export interface SimulatorEvent {
  event_type: "TRANSACTION" | "HEARTBEAT" | "STATE_CHANGE" | "COMPLETE";
  timestamp: string;
  data?: TransactionResponse;
  status?: SimulatorStatus;
  message?: string;
}
