# Sentinel.AML — Financial Transaction Data Pipeline

## 1. Source Dataset Overview

- **Source File**: `data/transactions.csv` (13.5 MB)
- **Record Count**: 129,675 transactions
- **Timeframe**: October 1, 2026 to November 14, 2026 (~45 calendar days)
- **Currency**: INR (₹)
- **Data Integrity SHA-256**: `440f6be969bc4f700f179f2be3acf25de96dc9dcfd1504d4c6274e5302a066a5`

## 2. Structural Schema & Field Mapping

| Source CSV Column | Database Field | Table | Type | Operational vs Ground-Truth |
|---|---|---|---|---|
| `txn_id` | `transaction_id` | `transactions` | String(64) | Operational |
| `timestamp` | `timestamp` | `transactions` | DateTime | Operational |
| `sender_id` | `sender_account_id` | `transactions` | String(64) | Operational |
| `receiver_id` | `receiver_account_id` | `transactions` | String(64) | Operational |
| `amount` | `amount` | `transactions` | Numeric(14,2) | Operational |
| `currency` | `currency` | `transactions` | String(3) | Operational |
| `channel` | `channel` | `transactions` | String(32) | Operational |
| `merchant_category` | `merchant_category` | `transactions` | String(64) | Operational |
| `device_id` | `device_id` | `transactions` | String(64) | Operational (Nullable) |
| `location` | `location` | `transactions` | String(64) | Operational (Nullable) |
| `sender_balance_before` | `sender_balance_before` | `transactions` | Numeric(14,2) | Operational (Nullable) |
| `is_fraud` | `is_fraud` | `transaction_ground_truth` | Integer | Ground Truth (Isolated) |
| `is_aml_pattern` | `is_aml_pattern` | `transaction_ground_truth` | Integer | Ground Truth (Isolated) |
| `pattern_type` | `pattern_type` | `transaction_ground_truth` | String(64) | Ground Truth (Isolated) |
| `scenario_id` | `scenario_id` | `transaction_ground_truth` | String(64) | Ground Truth (Isolated) |
| `is_edge_case` | `is_edge_case` | `transaction_ground_truth` | Integer | Ground Truth (Isolated) |
| `edge_case_type` | `edge_case_type` | `transaction_ground_truth` | String(64) | Ground Truth (Isolated) |

## 3. Strict Separation of Concerns (No Label Leakage)

1. **Operational Scope (`transactions` table)**:
   - Contains exclusively transaction attributes knowable at transaction execution time.
   - Served via `/api/v1/transactions` and `/api/v1/simulator/stream`.
   - Never exposes ground-truth fraud or AML indicators.

2. **Evaluation Scope (`transaction_ground_truth` table)**:
   - Stores labels, synthetic scenarios, and edge case typologies.
   - Accessible only through administrative and model benchmark endpoints (e.g. `/api/v1/dataset/summary`).
   - Serves as the benchmark validation set for Phase 3 (ML models) and Phase 4 (Graph typologies).

## 4. Ingestion Pipeline & Verification

- **CLI Tool**: `python -m app.cli import-dataset --file data/transactions.csv`
- **Idempotency**: Checked via SHA-256 hash comparison in `dataset_imports`.
- **Bulk Chunking**: Ingested in 5,000-record transactions.
- **Duplicate Prevention**: Idempotency guard prevents double insertion.
