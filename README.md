# Sentinel.AML — AI-Powered Financial Fraud Detection & AML System

> **PromptWars 2026 AI Challenge Hackathon**  
> Organized at Integral University, Lucknow • Powered by Google for Developers × Hack2Skill  
> **Status:** Phase 2.6 Static CSV Architecture & Cloud Deployment Ready<br>
> **Frontend:** [https://prowar-rho.vercel.app](https://prowar-rho.vercel.app) (Vercel)<br>
> **Backend:** Render (FastAPI + Static CSV In-Memory Analytics)

---

## 1. Project Overview & Problem Statement

Digital financial ecosystems (UPI, instantaneous card rails, mobile banking) process millions of transactions per minute. Traditional rule-based surveillance engines relying on simplistic, static thresholds (e.g. *"flag any transfer > ₹50,000"*) fail to stop sophisticated modern financial crime:
1. **High False Positive Rates:** Legitimate high-value payments trigger unnecessary friction and manual review costs.
2. **Evasion:** Money laundering syndicates exploit static thresholds through *structuring* (smurfing transfers at ₹49,000) and multi-hop circular flows.
3. **Zero-Day Vectors:** Account takeover and novel fraud techniques cannot be flagged by backward-looking static rules.

**Sentinel.AML** is an AI-powered surveillance platform combining:
- **Supervised Fraud Detection:** Point-in-time machine learning (LightGBM/XGBoost) trained on behavioural feature vectors.
- **Behavioral Anomaly Monitoring:** Unsupervised IsolationForest models detecting spending velocity and baseline deviations.
- **Anti-Money Laundering (AML) Graph Typologies:** NetworkX directed multigraphs isolating circular laundering cycles, smurfing, and fan-out mule syndicates.
- **Ensemble Risk Scoring:** Calibrated 0–100 risk scoring with regulatory rule overrides.
- **Explainable AI (XAI):** SHAP value feature attributions translated into clear, human-readable reason codes for security analysts.
- **Human-in-the-Loop Analyst Workstation:** Dark-first financial security operations center (SOC) dashboard.

> **Disclaimer:** This prototype uses synthetic, privacy-preserving transactional datasets. No real customer PII or banking credentials are used or stored.

---

## 2. Technology Stack

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Library:** React 19
- **Language:** TypeScript 5.7+ (Strict Mode enabled)
- **Styling:** Tailwind CSS with custom fintech SOC dark theme
- **Icons:** Lucide React
- **Analytics Ready:** Recharts

### Backend
- **Framework:** FastAPI with Uvicorn ASGI
- **Language:** Python 3.12 (managed via `uv`)
- **Data Validation:** Pydantic v2
- **Data Layer:** Static in-memory indexed CSV (`data/transactions.csv`, 129,675 synthetic transactions) — zero external database dependencies
- **Persistence (Optional/Legacy):** SQLAlchemy 2.0 with in-memory SQLite fallback
- **Testing:** Pytest (36/36 tests passing) & FastAPI TestClient

---

## 3. Project Architecture

```text
promwar/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes/
│   │   │       │   ├── health.py         # /health and /health/database
│   │   │       │   ├── transactions.py   # Ingestion and querying
│   │   │       │   ├── fraud.py          # Supervised ML status & scoring
│   │   │       │   ├── anomaly.py        # Unsupervised outlier detector
│   │   │       │   ├── aml.py            # Graph typology analysis
│   │   │       │   ├── risk.py           # Ensemble scoring & tiers
│   │   │       │   ├── alerts.py         # Incident queue & review
│   │   │       │   └── analytics.py      # Validation metrics & KPIs
│   │   │       └── router.py             # Route aggregator
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic Settings & env
│   │   │   ├── exceptions.py             # Standardized error handlers
│   │   │   └── logging.py                # Structured, PII-safe logging
│   │   ├── database/
│   │   │   ├── base.py                   # SQLAlchemy Declarative Base
│   │   │   └── session.py                # Engine & session lifecycle
│   │   ├── models/                       # ORM Models (Account, Transaction, Alert)
│   │   ├── schemas/                      # Pydantic Data Contracts
│   │   ├── services/                     # Business logic contracts
│   │   ├── utils/                        # Privacy masking & UTC helpers
│   │   └── main.py                       # FastAPI application entrypoint
│   ├── tests/                            # Pytest suite (17 passing tests)
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/                          # Next.js App Router pages
│   │   │   ├── layout.tsx                # Dark SOC theme shell
│   │   │   ├── page.tsx                  # Platform Overview & Health
│   │   │   ├── transactions/             # Transaction Stream Monitor
│   │   │   ├── fraud/                    # Supervised Fraud Engine
│   │   │   ├── anomaly/                  # Behavioral Anomaly Monitor
│   │   │   ├── aml/                      # AML Graph Investigation
│   │   │   ├── risk/                     # Multi-Model Risk Scorer
│   │   │   ├── alerts/                   # Security Alerts Queue
│   │   │   └── analytics/                # Performance KPIs & SAR Reports
│   │   ├── components/
│   │   │   ├── layout/                   # Sidebar, TopNav, MobileNav, AppShell
│   │   │   └── ui/                       # Card, Badge, Button, EmptyState, StatusDot
│   │   ├── lib/                          # Centralized ApiClient & Masking utilities
│   │   ├── services/                     # Health & data services
│   │   ├── styles/                       # Tailwind globals
│   │   └── types/                        # TypeScript Interfaces
│   ├── package.json
│   ├── tsconfig.json                     # Strict TypeScript config
│   └── tailwind.config.ts
│
├── docs/
│   ├── ARCHITECTURE.md                   # Complete architectural specification
│   ├── API.md                            # Comprehensive REST API contracts
│   └── DEVELOPMENT.md                    # Contributor guide & setup
│
├── scripts/
│   ├── dev.ps1                           # PowerShell launch script
│   ├── setup.ps1                         # PowerShell installation script
│   ├── dev.sh                            # Bash launch script
│   └── setup.sh                          # Bash installation script
│
├── .env.example                          # Environment variable template
├── .gitignore                            # Secret, venv, and artifact exclusions
├── AGENTS.md                             # Agent directives & engineering rules
└── README.md
```

---

## 3. Deployment Architecture

Sentinel.AML is production‑ready with the following deployment configuration:

- **Frontend:** Vercel (Next.js) – Live at `https://prowar-rho.vercel.app`
- **Backend:** Render (FastAPI) – Repository: `CHACHA0044/prowar`, Runtime: Python 3.12
- **Database:** Supabase PostgreSQL (managed) – Session pooler recommended for Render IPv4 compatibility

### Vercel Configuration
- Repository: `CHACHA0044/prowar`
- Root directory: `frontend/`
- Build command: `next build`
- Start command: `next start --port 3000`
- Required environment variable: `NEXT_PUBLIC_API_URL` (Render backend URL)

### Render Configuration
- Repository: `CHACHA0044/prowar`
- Root directory: `backend/`
- Build command: `pip install --upgrade pip && pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips="*"`
- Required environment variables: `DATABASE_URL` (Supabase), `CONTROL_API_TOKEN` (optional)

### Database Migration & Dataset Import
- Alembic migrations are pre‑configured (`backend/alembic/`); run `alembic upgrade head` in production.
- Dataset import via CLI: `python -m app.cli import-dataset --file ../data/transactions.csv`
- All 129,675 synthetic transactions are imported with ground‑truth labels preserved.

### Security & CORS
- Production CORS: Explicit origins only (`https://prowar-rho.vercel.app`)
- No wildcard origins in production.
- Optional token (`CONTROL_API_TOKEN`) for simulator control mutations.

### Monitoring
- Vercel Analytics & Speed Insights integrated in `frontend/src/app/layout.tsx`.

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.11+ and `uv`
- Node.js 18.18+ / 22+ and npm 10+

### Option A: One-Command Automated Setup

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1
```

**Linux / macOS:**
```bash
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/dev.sh
```

---

### Option B: Manual Startup

#### 1. Backend Service
```bash
# Set up venv and install dependencies
uv venv backend/.venv
uv pip install -r backend/requirements.txt --python backend/.venv

# Run the FastAPI server
backend/.venv/Scripts/uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- Swagger UI Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

#### 2. Frontend Application
```bash
cd frontend
npm install
npm run dev
```
- Interactive Dashboard: [http://localhost:3000](http://localhost:3000)

---

## 5. Verification & Test Execution

### Backend Automated Test Suite
```bash
backend/.venv/Scripts/pytest.exe backend/tests -v
```
**Results:** `17 passed in 1.18s`
- Root & health check endpoints (`/api/v1/health`, `/api/v1/health/database`)
- Configuration and CORS origin parsing
- Data contract validation (Transaction, Account, Alert)
- Placeholder router status codes & responses

### Frontend Quality & Build Verification
```bash
npm run --prefix frontend typecheck
npm run --prefix frontend build
```
**Results:**
- Strict TypeScript: `0 errors`
- Next.js Production Build: `Compiled successfully in 14.9s` (All 8 pages static prerendered)

---

## 6. Security & Responsible AI Standards

- **Synthetic Data Compliance:** Strictly synthetic and anonymized financial records.
- **Account Masking:** Sensitive identifiers are automatically masked in user interfaces (`ACC_****1234`).
- **No Hardcoded Credentials:** Zero secrets in codebase; environment variables loaded from `.env`.
- **Safe Error Handling:** Production mode masks internal database and framework stack traces.
- **Human-in-the-Loop:** System produces explainable recommendations; human analysts make all final enforcement decisions.

---

## 7. Next Steps (Subsequent Phases)

- **Phase 2:** Synthetic data generation & streaming simulator (Department 1 & 8).
- **Phase 3:** Feature engineering & LightGBM supervised model training (Department 2 & 3).
- **Phase 4:** IsolationForest behavioral anomaly detection & baseline profiling (Department 4).
- **Phase 5:** NetworkX AML graph analytics & typology discovery (Department 5).
- **Phase 6:** Ensemble risk scoring & SHAP explainability layer (Department 6 & 7).
- **Phase 7:** Interactive visualization integration & SAR export generation (Department 9).

