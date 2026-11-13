export interface DatasetStatusResponse {
  import_status: "PENDING" | "COMPLETED" | "FAILED" | "EMPTY" | string;
  dataset_id?: string;
  source_filename?: string;
  checksum_sha256?: string;
  imported_at?: string;
  total_rows: number;
  imported_rows: number;
  skipped_rows: number;
  date_range_start?: string;
  date_range_end?: string;
  duration_seconds?: number;
}

export interface ChannelMetric {
  channel: string;
  count: number;
  volume: number;
  percentage: number;
}

export interface CategoryMetric {
  category: string;
  count: number;
  volume: number;
  percentage: number;
}

export interface DailyVolumeMetric {
  date: string;
  count: number;
  volume: number;
}

export interface AmountBucketMetric {
  bucket: string;
  min_val: number;
  max_val: number;
  count: number;
  percentage: number;
}

export interface GroundTruthEvaluationSummary {
  total_evaluated_rows: number;
  ground_truth_fraud_count: number;
  ground_truth_fraud_rate: number;
  ground_truth_aml_count: number;
  ground_truth_aml_rate: number;
  ground_truth_edge_cases_count: number;
  pattern_breakdown: Record<string, number>;
}

export interface DatasetSummaryResponse {
  total_transactions: number;
  total_volume_inr: number;
  avg_transaction_inr: number;
  min_transaction_inr: number;
  max_transaction_inr: number;
  unique_senders: number;
  unique_receivers: number;
  unique_accounts_total: number;
  date_range: { start?: string | null; end?: string | null };
  channel_distribution: ChannelMetric[];
  category_distribution: CategoryMetric[];
  daily_volume: DailyVolumeMetric[];
  amount_buckets: AmountBucketMetric[];
  missing_metadata_counts: Record<string, number>;
  ground_truth_evaluation: GroundTruthEvaluationSummary;
}
