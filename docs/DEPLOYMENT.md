# Deployment Guide — Sentinel.AML

This document describes the production deployment configuration for the Sentinel.AML platform.

## Overview

- **Frontend**: Vercel (Next.js)
- **Backend**: Render (FastAPI)
- **Database**: Supabase PostgreSQL (managed)
- **Dataset**: 129,675 synthetic transactions (CSV import via CLI)

All Phase 2 functionality is preserved. No ML models (Phase 3) are included.

---

## A. Vercel Configuration

### Repository
- GitHub: `CHACHA0044/prowar`
- Frontend directory: `frontend/`

### Build Configuration
- Framework: Next.js (App Router)
- Build command: `next build`
- Start command: `next start --port 3000`
- Environment: Production (Node.js 18+)

### Environment Variables (Vercel Dashboard)

| Variable | Required | Description |
| `NEXT_PUBLIC_API_URL` | **Yes** | Render backend URL, e.g. `https://sentinel-aml-api.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | **No** | Reserved for future authentication (Phase 2.5) |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | **No** | Reserved for future authentication |

**Development**: Set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` for local testing.

### Production URL
- Live: `https://prowar-rho.vercel.app`

### Vercel Analytics & Speed Insights
- Install: `npm install @vercel/analytics @vercel/speed-insights`
- Integrate in `frontend/src/app/layout.tsx`:
  ```tsx
  import { Analytics } from "@vercel/analytics/next";
  import { SpeedInsights } from "@vercel/speed-insights/next";
  ```
- **Note**: Monitoring is only active after enabling in the Vercel dashboard.

---

## B. Render Configuration

### Repository
- GitHub: `CHACHA0044/prowar`
- Backend directory: `backend/`

### Runtime
- Python 3.12
- Framework: FastAPI

### Build Command
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.  --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips="*"
```

**Why single worker**: The simulator is a process‑wide singleton with database‑backed checkpoint. Multi‑instance replay requires external queue/worker (see Troubleshooting).

### Health‑Check Path
- `/api/v1/health/ready` (Render uses this for readiness probe)

### Environment Variables (Render Dashboard)

| Variable | Required | Value |
|----------|----------|-------|
| `DATABASE_URL` | **Yes** | Direct Supabase connection (see below) |
| `CONTROL_API_TOKEN` | **Optional** | Shared token for simulator control endpoints (X-Control-Token) |
| `ENVIRONMENT` | **Yes** | `production` |
| `DEBUG` | **Yes** | `False` |
| `LOG_LEVEL` | **Yes** | `INFO` |
| `DB_SSL_MODE` | **Yes** | `require` |
| `DB_POOL_SIZE` | **Yes** | `5` |
| `DB_MAX_OVERFLOW` | **Yes**, `5` |
| `DB_POOL_RECYCLE` | **Yes** | `1800` |
| `DB_POOL_TIMEOUT` | **Yes** | `30` |
| `DB_CONNECT_TIMEOUT` | **Yes** | `10` |
| `ALLOWED_ORIGINS` | **Yes** | `https://prowar-rho.vercel.app` |
| `AUTO_CREATE_SCHEMA` | **Yes** | `False` (migrations via Alembic) |

### Database URL Options (Supabase)

**Option 1 — Direct connection (IPv6‑capable networks):**
```
postgresql+psycopg2://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
```

**Option 2 — Session pooler (recommended for Render IPv4 compatibility):**
```
postgresql+psycopg2://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require
```

**Never commit credentials** — use Render’s `sync: false` env vars.

---

## C. Supabase Configuration

### PostgreSQL Project Setup
- Create a Supabase PostgreSQL project.
- Enable **Session Pooler** (recommended for Render).
- Copy the connection string (direct or pooler).

### Connection Pooling
- Render’s IPv4 environment benefits from Supabase session pooler.
- Use the pooler URL in `DATABASE_URL`.

### Database Migration
1. **Alembic is already configured** (`backend/alembic/`).
2. In production (`ENVIRONMENT=production`, `AUTO_CREATE_SCHEMA=False`), run:
   ```bash
   alembic upgrade head
   ```
3. Verify migration success with `alembic check`.

**Never run destructive migrations in production.**

### Dataset Import
1. The CSV file (`data/transactions.csv`) is included in the repo.
2. Use the backend CLI:
   ```bash
   cd backend
   python -m app.cli import-dataset --file ../data/transactions.csv
   ```
3. **Options**:
   - `--force`: Clear existing data before import.
   - `--chunk-size`: Rows per batch (default 5000).
   - `--strict`: Fail if any transaction lacks ground‑truth rows.
   - `--expected-checksum`: Verify CSV integrity.

4. **Verification**:
   ```bash
   python -m app.cli verify-dataset
   ```

5. **Safety**:
   - Import runs inside a single transaction; incomplete imports roll back.
   - Duplicate `txn_id`s are skipped.
   - Ground‑truth labels are preserved and linked via foreign key.
   - No ground‑truth labels are exposed through operational APIs.

---

## D. Local Development

### Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run Migrations (SQLite)
```bash
cd backend
alembic upgrade head
```

### Import Dataset (SQLite)
```bash
cd backend
python -m app.cli import-dataset --file ../data/transactions.csv
```

### Environment Files
- `backend/.env.example` → copy to `backend/.env` for local dev.
- `frontend/.env.example` → copy to `frontend/.env.local` for local dev.

---

## E. Troubleshooting

### CORS Errors
- **Symptom**: Browser console shows CORS policy violation.
- **Fix**: Ensure `ALLOWED_ORIGINS` in Render matches Vercel URL (`https://prowar-rho.vercel.app`).
- **Development**: Add `http://localhost:3000` to `ALLOWED_ORIGINS`.

### Database Connection Failures
- **Render**: Verify `DATABASE_URL` uses session pooler and `sslmode=require`.
- **Supabase**: Ensure IP whitelist includes Render’s CIDR.
- **Alembic**: Run `alembic check` after credentials change.

### Missing Environment Variables
- Render/Vercel dashboards show `sync: false` for secrets; populate them in the UI.
- Never hardcode credentials in source code.

### Render Cold Starts
- Simulator checkpoint is persisted in the database; replay resumes from last offset.
- If replay hangs, check `CONTROL_API_TOKEN` and `X-Control-Token` header.

### SSE Disconnections
- Frontend reconnects automatically (EventSource retry).
- Simulator heartbeats every 15 seconds; disconnect after 30 seconds of no activity.

### Vercel Build Failures
- Verify `NEXT_PUBLIC_API_URL` is set in Vercel env vars.
- Ensure `@vercel/analytics` and `@vercel/speed-insights` are installed.

### Simulator Multi‑Instance Issues
- Render free plan may restart the service.
- Simulator progress is checkpointed in `simulator_checkpoint` table; replay resumes.
- For reliable multi‑instance replay, consider a queue worker (outside scope of Phase  2.5).

---

## F. Security Checklist

- **No secrets in Git** – `.gitignore` excludes `.env*` and `.db` files.
- **CORS**: No wildcard (`*`) in production; explicit origins only.
- **Database**: SSL required (`sslmode=require`).
- **Simulator Controls**: Optional token (`CONTROL_API_TOKEN`) for mutations.
- **Input Validation**: FastAPI Pydantic schemas validate all request bodies.
- **Logging**: No database credentials or tokens in logs.
- **Ground‑Truth Labels**: Never exposed via operational APIs.

---

## G. React Bits Verification

- `CountUp` and `SpotlightCard` components are **custom implementations** in `frontend/src/components/ui/`.
- They are **not** official React Bits components.
- No additional React Bits packages were introduced.

---

## H. Final Verification Checklist

### Backend
- [x] All 39 pytest tests pass.
- [x] Alembic migrations valid (tested with SQLite).
- [x] Dataset ingestion CLI works (tested via test_ingestion.py).
- [x] Simulator checkpoint persistence verified.
- [x] Health endpoints (`/api/v1/health/live`, `/api/v1/health/ready`) functional.
- [x] CORS configuration validated.

### Frontend
- [x] TypeScript check passes (`tsc --noEmit`).
- [x] Production build succeeds (`next build`).
- [x] Vercel Analytics & Speed Insights installed and integrated.
- [x] API client reads `NEXT_PUBLIC_API_URL` correctly.

### Database
- [x] Migration compatibility verified (Alembic check).
- [x] Dataset import process verified (idempotent, transactional).
- [x] Ground‑truth separation preserved.

### Security
- [x] No accidental secrets in Git.
- [x] CORS configured correctly.
- [x] No service‑role key exposed.

---

## I. Remaining Manual Steps

1. Deploy backend to Render (populate `DATABASE_URL`, `CONTROL_API_TOKEN`).
2. Deploy frontend to Vercel (populate `NEXT_PUBLIC_API_URL`).
3. Enable Vercel Speed Insights and Analytics in the dashboard.
4. Run dataset import on Supabase PostgreSQL using the CLI.
5. Verify database health and simulator status after import.

---

## J. Known Limitations

- Simulator is a single‑process singleton; Render restarts preserve progress via checkpoint.
- Free Render plan may sleep; simulator will pause on cold start.
- No authentication (Supabase Auth) in Phase 2.5; admin endpoints are optionally token‑protected.
- React Bits components are custom; no external dependency.
- Alembic migrations are tested with SQLite; PostgreSQL connection requires real credentials.

---

## K. Next Phase

Phase 3 (ML models, fraud classification, AML graph algorithms) is **not** included in this deployment preparation.

---

*Document generated by deployment preparation script.*
