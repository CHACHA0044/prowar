# System Architecture & Technical Specifications

**Project:** Sentinel.AML — AI-Powered Financial Fraud Detection & AML Security Platform  
**Target:** PromptWars 2026 Hackathon Prototype  
**Phase:** Phase 1 Foundation  

---

## 1. High-Level Architectural Vision

Sentinel.AML is designed as an enterprise-grade financial security surveillance platform. Rather than relying solely on brittle heuristic thresholds (e.g. `amount > 50,000 INR`), the architecture unifies three complementary analytical intelligence engines into an ensemble risk scoring framework:

```
[Synthetic Transaction Stream]
             │
             ▼
[Feature Engineering Pipeline (Rolling Z-Scores, Velocity, Graphs)]
             │
   ┌─────────┼────────────────────────┐
   │         │                        │
   ▼         ▼                        ▼
[Layer 1] [Layer 2]               [Layer 3]
Supervised Behavioral             Directed AML
Fraud ML   Anomaly Outliers       Graph Typologies
(LightGBM) (IsolationForest)      (NetworkX Cycles/Hubs)
   │         │                        │
   └─────────┼────────────────────────┘
             ▼
[Ensemble Risk Engine (0-100 Score + Override Rules)]
             │
             ▼
[Explainable AI Layer (SHAP Values + Reason Codes)]
             │
             ▼
[Security Alerts Queue & Analyst Dashboard]
```

---

## 2. Component Subsystems

### 2.1 Backend Core (FastAPI)
- **Path:** `backend/app/`
- **Framework:** FastAPI with Python 3.12+, Uvicorn ASGI server.
- **Protocol:** RESTful JSON APIs mounted under `/api/v1`.
- **Validation:** Pydantic v2 strict models for incoming requests and outgoing responses.
- **Error Handling:** Centralized exception handlers preventing raw stack trace leakage; standard error payload schema (`{ success: false, error: { code, message, details } }`).
- **CORS:** Controlled origin whitelisting configured via `ALLOWED_ORIGINS` environment variable.
- **Logging:** Structured logging preventing sensitive account number exposure.

### 2.2 Database & Persistence Layer
- **Path:** `backend/app/database/` & `backend/app/models/`
- **ORM:** SQLAlchemy 2.0 with Declarative Mapping.
- **Engine:** SQLite (`sqlite:///./financial_fraud_aml.db`) with `check_same_thread=False` and `pool_pre_ping=True` for local development, maintaining a 100% compatible migration path to PostgreSQL for production deployment.
- **Tables Initialized:**
  - `accounts`: Account metadata, tiering, and operational status.
  - `transactions`: Immutable payment records with multi-channel and location indexing.
  - `security_alerts`: Security incidents with severity tiers, risk scores, and review status.

### 2.3 Detection Subsystem Interfaces (Planned for Phases 2–6)

#### Layer 1: Supervised Fraud Classifier (Department 3)
- **Objective:** Detect point-in-time fraudulent payment signatures.
- **Models:** LightGBM / XGBoost with class-imbalance weighting (handling 1–3% fraud prevalence) and Logistic Regression baseline.
- **Validation:** Time-based train/test splits (avoiding temporal leakage); evaluated on Precision-Recall AUC (PR-AUC) and F1 rather than raw accuracy.
- **Interface:** `POST /api/v1/fraud/evaluate`

#### Layer 2: Behavioral Anomaly Detector (Department 4)
- **Objective:** Catch previously unseen attack vectors deviating from historical baselines.
- **Models:** IsolationForest and rolling statistical z-scores (amount, frequency, hour-of-day).
- **Interface:** `GET /api/v1/anomaly/status`

#### Layer 3: AML Graph Typologies (Department 5)
- **Objective:** Detect multi-account coordinated money laundering schemes.
- **Models:** NetworkX directed multigraphs detecting:
  1. **Structuring / Smurfing:** Rapid sequences of transfers just under reporting thresholds (e.g. ₹49,000 × 10).
  2. **Circular Flows:** Directed cycles ($A \rightarrow B \rightarrow C \rightarrow A$).
  3. **Fan-In / Fan-Out:** Money mule aggregation hubs.
  4. **Rapid Pass-Through:** Inflow and outflow within short time windows.
- **Interface:** `GET /api/v1/aml/status`

#### Layer 4: Ensemble Risk Engine (Department 6)
- **Scoring Formulation:**
  $$\text{Risk Score} = 0.45 \cdot P_{\text{fraud}} + 0.25 \cdot S_{\text{anomaly}} + 0.30 \cdot S_{\text{aml}}$$
- **Rule Overrides:** Hard circuit breakers (e.g. detection of an active cycle forces tier `CRITICAL`).
- **Tiers:**
  - `LOW` (0–29)
  - `MEDIUM` (30–59)
  - `HIGH` (60–84)
  - `CRITICAL` (85–100)

### 2.4 Frontend Dashboard (Next.js 15)
- **Path:** `frontend/src/`
- **Architecture:** Next.js App Router, React 19, strict TypeScript mode.
- **Styling:** Tailwind CSS with custom fintech SOC color tokens (deep navy `#080c14`, slate surfaces `#0f172a`, subtle borders `#1e293b`).
- **Telemetry Integration:** Live heartbeat polling against `GET /api/v1/health` with visual pulse indicators.
- **Accessibility & Responsiveness:** Fluid layouts adapting down to mobile screen sizes (360px+) with drawer navigation and full keyboard focus accessibility.

---

## 3. Data Flow

1. **Ingestion:** Transactions are received via `POST /api/v1/transactions` or generated by the stream simulator.
2. **Feature Extraction:** Features (velocity, z-scores, graph nodes) are computed deterministically.
3. **Inference:** The three detectors evaluate the transaction in parallel.
4. **Scoring:** The ensemble risk engine computes the final score (0–100) and assigns an actionable tier.
5. **Alerting:** If score exceeds threshold (or critical override fires), a `SecurityAlert` is persisted and surfaced to the analyst queue.
6. **Triage:** Analyst reviews SHAP explanations, confirms or dismisses the alert (human-in-the-loop).

