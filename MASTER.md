7. Master brief to paste to your agents

Project: Intelligent Financial Fraud Detection and Anti-Money Laundering System (hackathon prototype, solo, must be deployed with a public demo link and GitHub repo).

Goal: Build an AI-powered system that ingests synthetic transaction data (UPI, cards, transfers), detects fraud, anomalies, and AML patterns (structuring, circular flows, fan-in/fan-out, rapid pass-through), assigns risk scores (0–100, tiers Low/Medium/High/Critical), generates alerts in near real time, explains every flag (SHAP plus human-readable reason codes), and presents everything in an interactive dashboard.

Constraints: Synthetic data only. No real credentials or data. Mask account IDs in the UI. Human-in-the-loop (the system recommends, an analyst decides). Document limitations, privacy, and scalability. Python stack: pandas, scikit-learn, LightGBM, NetworkX, SHAP, Streamlit, Plotly.

Architecture: data generator → feature engineering → three detectors (supervised fraud model, IsolationForest anomaly model, graph/rule-based AML detectors) → weighted risk engine with rule overrides → explanation layer → stream simulator → dashboard.

Contracts: Use the transaction schema and scoring output schema above. The code layout is above. Every module must expose a clean function interface so modules can be built in parallel.

Quality bar: Report precision, recall, F1 and PR-AUC (not just accuracy). Seeded and reproducible. The app must start with one command and load instantly from pre-trained artifacts. Everything must work end to end before polishing.