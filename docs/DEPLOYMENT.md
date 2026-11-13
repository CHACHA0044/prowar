# Deployment Guide — Sentinel.AML (Static CSV Architecture)

This document provides the exact deployment settings and operational guide for the Sentinel.AML financial fraud surveillance and AML platform.

## Architecture Summary

- **Frontend**: Vercel (Next.js 15 App Router)
- **Backend**: Render (FastAPI + Python 3.12)
- **Data Source**: Embedded static CSV (`data/transactions.csv` — 129,675 synthetic transactions)
- **Database**: **NOT REQUIRED** (In-memory indexed dataset loaded at startup)
- **Production Frontend URL**: `https://prowar-rho.vercel.app`
- **Production Backend URL**: Supplied after Render web service provisioning (e.g. `https://sentinel-aml-api.onrender.com`)

---

## A. Render Deployment Configuration (Backend)

### Service Details
- **Repository**: `CHACHA0044/prowar`
- **Environment**: Web Service
- **Root Directory**: `backend`
- **Runtime**: `Python 3.12`
- **Branch**: `main`

### Commands
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips="*"
  ```
- **Health Check Path**:
  ```text
  /api/v1/health/ready
  ```

### Render Environment Variables

| Variable | Required? | Recommended Value | Purpose |
|---|---|---|---|
| `PYTHON_VERSION` | **Yes** | `3.12.8` | Enforces Python 3.12 runtime on Render |
| `ENVIRONMENT` | **Yes** | `production` | Enables production security and disables development logs |
| `ALLOWED_ORIGINS` | **Yes** | `https://prowar-rho.vercel.app` | Explicit CORS allowlist for Vercel production frontend |
| `DEBUG` | Optional | `False` | Disables debug mode and verbose tracebacks |
| `LOG_LEVEL` | Optional | `INFO` | Standard application logging level |
| `CONTROL_API_TOKEN` | Optional | `<random-secret-token>` | Protects simulator mutation endpoints (`/start`, `/pause`, `/reset`, `/speed`) via `X-Control-Token` header |
| `DATASET_PATH` | Optional | Unset | Auto-discovered at `../data/transactions.csv` |

*(Note: `DATABASE_URL` is **not** required. The application starts and serves all APIs without any database).*

---

## B. Vercel Deployment Configuration (Frontend)

### Project Details
- **Repository**: `CHACHA0044/prowar`
- **Root Directory**: `frontend`
- **Framework Preset**: `Next.js`
- **Production URL**: `https://prowar-rho.vercel.app`

### Build & Output Settings
- **Build Command**: `next build` (default)
- **Output Directory**: `.next` (default)
- **Install Command**: `npm install` (default)

### Vercel Environment Variables

| Variable | Required? | Value | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | **Yes** | `https://<your-render-service>.onrender.com` | Base URL of deployed Render backend API |

*Replace `<your-render-service>.onrender.com` with the actual public URL assigned by Render after your backend web service deploys.*

### Vercel Speed Insights & Analytics
- The application already includes `@vercel/analytics` and `@vercel/speed-insights` in `frontend/src/app/layout.tsx`.
- Enable both features directly from the Vercel Dashboard under **Analytics** and **Speed Insights** tabs with a single click.

---

## C. Step-by-Step Deployment Guide

### Step 1: Deploy Backend on Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** > **Web Service**.
3. Connect your GitHub repository `CHACHA0044/prowar`.
4. Configure service settings:
   - **Name**: `sentinel-aml-api` (or preferred name)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --proxy-headers --forwarded-allow-ips="*"`
   - **Health Check Path**: `/api/v1/health/ready`
5. Add Environment Variables:
   - `PYTHON_VERSION`: `3.12.8`
   - `ENVIRONMENT`: `production`
   - `ALLOWED_ORIGINS`: `https://prowar-rho.vercel.app`
6. Click **Create Web Service**.
7. Once deployed, copy your service URL (e.g. `https://sentinel-aml-api.onrender.com`).

### Step 2: Configure Frontend on Vercel
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Open your project for `prowar` (live at `https://prowar-rho.vercel.app`).
3. Navigate to **Settings** > **Environment Variables**.
4. Add or update:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://<your-render-service>.onrender.com` (from Step 1)
   - **Target**: Production, Preview, Development
5. Navigate to **Deployments** and click **Redeploy** on the latest commit.

---

## D. Local Development

### Backend
```powershell
cd backend
.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```
Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
Health Check: [http://127.0.0.1:8000/api/v1/health/ready](http://127.0.0.1:8000/api/v1/health/ready)

### Frontend
```powershell
cd frontend
npm run dev
```
Dashboard: [http://localhost:3000](http://localhost:3000)

---

## E. Troubleshooting

- **Render Cold Starts**: Render free tier spins down after 15 minutes of inactivity. First request can take ~30-50s to wake up.
- **CORS Errors**: Confirm `ALLOWED_ORIGINS` on Render contains the exact frontend URL without trailing slashes (`https://prowar-rho.vercel.app`).
- **SSE Stream Disconnects**: Proxies and free instances terminate idle connections. The simulator sends automatic heartbeats every 15s to keep connections alive, and the frontend hook auto-reconnects with exponential backoff.
