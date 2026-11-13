# PromptWars 2026: Fraud Detection and AML System

## 1. The problem in plain words

Digital payments (UPI, wallets, cards, bank transfers) produce huge volumes of transactions. Fixed rules like "flag anything over ₹50,000" miss new fraud patterns and create many false alarms. You must build a prototype that:

1. Ingests transactions, either streamed in real time or from a dataset.
2. Detects fraud (a single transaction is bad), anomalies (behaviour is unusual for that account), and AML patterns (the money flow across many transactions looks like laundering).
3. Gives each transaction or account a risk score and generates alerts.
4. Explains why something was flagged.
5. Shows everything on an interactive dashboard.

It must use synthetic or public data only, never real banking data, and must address privacy, security, scalability, and responsible AI.

## 2. What the judges will check

| Required | Notes |
|---|---|
| Working prototype | A static UI or slides scores lower |
| AI/ML detection | Real models, not just if/else rules |
| Risk scoring and alerts | Per transaction and per account |
| Interactive dashboard | Must be usable live |
| Methodology explanation | README plus a short pitch |
| Synthetic or anonymised data | State this clearly |
| **GitHub repo link** | Mandatory |
| **Live demo link** | Mandatory |
| **LinkedIn post** | Mandatory |
| Ability to explain limitations | Judges may question you |

## 3. Recommended architecture

```
Synthetic data → Feature engineering → [Supervised fraud model]
                                       [Anomaly model         ] → Risk engine → Alerts + Explanations → Dashboard
                                       [AML graph + rules     ]
```

Three detection layers feed one risk engine. The risk engine produces a 0–100 score, a risk tier (Low/Medium/High/Critical), and reason codes, which the dashboard displays.

**Suggested stack (fast to build and deploy):** Python, pandas, scikit-learn, LightGBM or XGBoost, IsolationForest, NetworkX, SHAP, FastAPI (optional), Streamlit with Plotly (dashboard). Deploy on Streamlit Community Cloud, Hugging Face Spaces, or Google Cloud Run.

## 4. Development departments

### Dept 1: Data and Synthetic Generation
- **Mission:** Create a realistic transaction dataset with fraud and laundering patterns injected, so every detector has something to find.
- **Build:**
  - About 50k–200k transactions across about 2,000 accounts over 30–60 days.
  - Normal behaviour: salary credits, UPI payments, bill payments, merchant spends, with realistic amounts and times.
  - Injected fraud: sudden high-value transfer, new device or location, rapid-fire small debits, odd-hour spikes, account takeover.
  - Injected AML patterns:
    - **Structuring/smurfing:** many transfers just under a threshold (e.g. ₹49,000 × 10).
    - **Circular flow:** A → B → C → A.
    - **Fan-in/fan-out:** many accounts → one account → many accounts.
    - **Rapid pass-through:** money in and out within minutes.
  - Ground-truth labels: `is_fraud`, `is_aml_pattern`, `pattern_type`.
- **Output:** `transactions.csv` plus the generator script (seeded for reproducibility).
- **Done when:** Fraud rate is about 1–3%, and the AML patterns are verifiably present in the data.

### Dept 2: Feature Engineering and Behavioural Analytics
- **Mission:** Turn raw rows into signals the models can use.
- **Features:**
  - Amount vs the account's historical mean and standard deviation (z-score).
  - Transaction velocity (count and sum in the last 1 hour, 24 hours, 7 days).
  - Time-of-day and weekday deviation.
  - New beneficiary, new device, or new location flags.
  - Balance drain ratio (amount ÷ balance).
  - Near-threshold flag.
  - Ratio of incoming to outgoing funds and time-to-forward.
  - Merchant category risk.
- **Rule:** Compute features without leaking the future (rolling windows use only past data).
- **Output:** A reusable `build_features(df)` function used by both batch and real-time paths.

### Dept 3: Supervised Fraud Detection (ML)
- **Mission:** Classify each transaction as fraud or legitimate.
- **Build:** LightGBM or XGBoost with class-imbalance handling (class weights or SMOTE), a time-based train/test split, and a Logistic Regression baseline for comparison.
- **Metrics:** Precision, recall, F1, PR-AUC, and a confusion matrix. Do not report accuracy alone, because fraud is rare.
- **Output:** A saved model and a `predict_fraud_proba(txn)` function.

### Dept 4: Anomaly Detection (Unsupervised)
- **Mission:** Catch unknown or new threats that have no labels.
- **Build:** IsolationForest (primary), optionally Local Outlier Factor or an autoencoder, plus per-account behavioural baselines.
- **Output:** An anomaly score from 0 to 1 per transaction, and a flag for "deviates from this account's normal behaviour".
- **Why it matters:** This directly answers the "previously unknown threats" part of the problem statement.

### Dept 5: AML and Graph Analytics
- **Mission:** Detect laundering patterns that span multiple transactions and accounts.
- **Build:** A directed graph in NetworkX (nodes are accounts, edges are transfers) with these detectors:
  - **Cycle detection** for circular money movement.
  - **Structuring detector:** a window of N transactions just below the threshold from or to the same account.
  - **Fan-in/fan-out detector** using degree and time-window analysis.
  - **Pass-through detector** for in-and-out within a short time and with a similar amount.
  - Optionally PageRank or centrality to find mule hubs.
- **Output:** A list of suspicious account clusters with pattern type and involved transactions, plus a graph visualisation.

### Dept 6: Risk Scoring and Alert Engine
- **Mission:** Combine all signals into one decision.
- **Build:**
  - Weighted ensemble, for example `risk = 0.45·fraud_prob + 0.25·anomaly + 0.30·aml_signal`, plus rule overrides (e.g. a detected cycle forces High).
  - Tiers: Low (<30), Medium (30–60), High (60–85), Critical (85+).
  - Account-level risk as an aggregate of its recent transactions.
  - Alert object: ID, timestamp, account, score, tier, reasons, and status (open/reviewed/dismissed).
  - Alert deduplication and prioritisation.
- **Output:** `score_transaction(txn) → {risk_score, tier, reasons, alert}`.

### Dept 7: Explainable AI
- **Mission:** Every flag must be understandable by a non-technical analyst.
- **Build:**
  - SHAP values per prediction (top 3–5 contributing features).
  - Human-readable reason codes, e.g. "Amount is 14× this account's average", "9 transfers just below ₹50,000 within 2 hours", "Funds returned to origin via 3 accounts".
  - A natural-language case summary, either templated (fast and safe) or optionally LLM-generated, in the style of a Suspicious Activity Report (SAR) narrative.
  - A global feature-importance chart.
- **Output:** `explain(txn_id)` that returns the reasons and a chart.

### Dept 8: Real-Time Pipeline and API
- **Mission:** Show real-time monitoring.
- **Build:** A transaction simulator that replays data at a configurable rate (e.g. 5–20 per second) through the scoring pipeline, with optional FastAPI endpoints (`POST /score`, `GET /alerts`, `GET /account/{id}`). An in-memory queue is enough. Mention Kafka or Pub/Sub as the production path in your scalability notes.
- **Output:** A live feed where new alerts appear without a manual refresh.

### Dept 9: Dashboard and UI
- **Mission:** The part judges see first, so it must be clear and polished.
- **Views:**
  1. **Overview:** KPIs (transactions processed, alerts, high-risk count, estimated amount at risk), risk-tier distribution, and a time series of alerts.
  2. **Live Monitor:** A streaming transaction feed with colour-coded risk.
  3. **Alerts Queue:** Sortable and filterable, with a detail panel (score, reasons, SHAP chart, and review/dismiss buttons).
  4. **AML Network View:** An interactive graph of suspicious clusters (cycles and fan-out highlighted).
  5. **Account Profile:** Behaviour baseline vs current activity, and risk history.
  6. **Model Insights:** Metrics, PR curve, confusion matrix, and feature importance.
  7. **Report export:** A downloadable suspicious activity report as PDF or CSV.
- **Tech:** Streamlit and Plotly are the fastest option. Use pyvis or Plotly for the graph.

### Dept 10: Security, Privacy and Responsible AI
- **Mission:** Satisfy the constraints section explicitly.
- **Build and document:**
  - Synthetic data only, with a clear disclaimer.
  - Mask or hash account IDs in the UI.
  - No secrets in the repo (use environment variables).
  - Input validation on the API.
  - Audit log of alerts and analyst actions.
  - Human-in-the-loop: the system recommends, and an analyst decides.
  - Bias and fairness note (no use of protected attributes), false-positive cost discussion, and known limitations.
  - Scalability notes (batch vs streaming, a production architecture sketch).

### Dept 11: Integration, Deployment and Submission
- **Mission:** Make sure the mandatory items exist.
- **Build:**
  - Clean GitHub repo: `README.md` (problem, approach, architecture diagram, stack, setup, screenshots, limitations), `requirements.txt`, folder structure, and a MIT or Apache license.
  - Deploy a live demo link and test it from a different device.
  - Pre-load the demo so it works instantly (a pre-trained model and cached data).
  - A 2-minute demo script and a LinkedIn post (use the hashtags #PromptWars2026 #GoogleForDevelopers #Hack2Skill #IntegralUniversity #AI@Integral).
  - Acknowledge AI-assisted development and third-party libraries, as the guidelines require.

## 5. Shared contracts (give these to every agent)

**Transaction schema**
```json
{
  "txn_id": "T000123",
  "timestamp": "2026-11-13T14:32:10",
  "sender_id": "ACC0042",
  "receiver_id": "ACC0917",
  "amount": 49000.0,
  "channel": "UPI",
  "merchant_category": "transfer",
  "device_id": "D88",
  "location": "Lucknow",
  "sender_balance_before": 120000.0
}
```

**Scoring output schema**
```json
{
  "txn_id": "T000123",
  "fraud_prob": 0.82,
  "anomaly_score": 0.74,
  "aml_flags": ["structuring"],
  "risk_score": 87,
  "tier": "Critical",
  "reasons": ["Amount 12x account average", "8 transfers just below ₹50,000 in 3 hours"],
  "shap_top": [["velocity_1h", 0.31], ["amount_zscore", 0.22]]
}
```

**Suggested repo layout**
```
/data        generator.py, transactions.csv
/src         features.py, fraud_model.py, anomaly.py, aml_graph.py,
             risk_engine.py, explain.py, stream_sim.py, api.py
/models      saved models
/app         dashboard.py (Streamlit)
/docs        architecture.png, screenshots
README.md, requirements.txt
```

## 6. Build order (you have only a few hours)

The event runs 9:30 AM to 3:00 PM, submission opens at 12:00 PM, and evaluation is from 2:00 PM, so be strict about scope.

| Phase | Work | Depts |
|---|---|---|
| 1 | Schema, data generator, and feature function | 1, 2 |
| 2 | Fraud model, anomaly model, and AML detectors (in parallel) | 3, 4, 5 |
| 3 | Risk engine, explanations, and stream simulator | 6, 7, 8 |
| 4 | Dashboard | 9 |
| 5 | Deploy, README, LinkedIn post, demo rehearsal | 10, 11 |

**If time runs short, cut in this order:** the FastAPI layer, then the autoencoder, then the PDF export, then PageRank. **Never cut:** the dataset, the fraud model, the anomaly model, at least two AML detectors (structuring and cycles), risk scores, explanations, the dashboard, the deployed link, the GitHub repo, and the LinkedIn post.

## 7. Master brief to paste to your agents

> **Project:** Intelligent Financial Fraud Detection and Anti-Money Laundering System (hackathon prototype, solo, must be deployed with a public demo link and GitHub repo).
>
> **Goal:** Build an AI-powered system that ingests synthetic transaction data (UPI, cards, transfers), detects fraud, anomalies, and AML patterns (structuring, circular flows, fan-in/fan-out, rapid pass-through), assigns risk scores (0–100, tiers Low/Medium/High/Critical), generates alerts in near real time, explains every flag (SHAP plus human-readable reason codes), and presents everything in an interactive dashboard.
>
> **Constraints:** Synthetic data only. No real credentials or data. Mask account IDs in the UI. Human-in-the-loop (the system recommends, an analyst decides). Document limitations, privacy, and scalability. Python stack: pandas, scikit-learn, LightGBM, NetworkX, SHAP, Streamlit, Plotly.
>
> **Architecture:** data generator → feature engineering → three detectors (supervised fraud model, IsolationForest anomaly model, graph/rule-based AML detectors) → weighted risk engine with rule overrides → explanation layer → stream simulator → dashboard.
>
> **Contracts:** Use the transaction schema and scoring output schema above. The code layout is above. Every module must expose a clean function interface so modules can be built in parallel.
>
> **Quality bar:** Report precision, recall, F1 and PR-AUC (not just accuracy). Seeded and reproducible. The app must start with one command and load instantly from pre-trained artifacts. Everything must work end to end before polishing.
>
> **Your assignment:** [Insert one department's section from above here.]

Give each agent the master brief plus **one** department section so they stay focused. If you like, I can turn this into a downloadable Markdown file, or write the data generator and shared schema code first so all agents build against the same foundation.