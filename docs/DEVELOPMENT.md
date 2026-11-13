# Developer Guide & Local Setup

**Project:** Sentinel.AML — Financial Fraud & AML Intelligence Platform  
**Target:** PromptWars 2026 Hackathon  

---

## 1. Prerequisites

Ensure you have the following installed on your workstation:
- **Python:** Version 3.11 or 3.12 (CPython recommended)
- **uv:** Fast Python package and virtual environment manager (`uv.exe`)
- **Node.js:** Version 18.18+ or 20+ / 22+ (tested with v22.13.0)
- **npm:** Version 9+ or 10+ (tested with v11.6.2)

---

## 2. Fast Setup (Single Command)

We provide dedicated startup scripts in the `scripts/` directory:

### Windows (PowerShell):
```powershell
# Set up both backend and frontend environments
.\scripts\setup.ps1

# Run both backend and frontend simultaneously
.\scripts\dev.ps1
```

### Linux / macOS:
```bash
# Setup
chmod +x scripts/*.sh
./scripts/setup.sh

# Run
./scripts/dev.sh
```

---

## 3. Manual Step-by-Step Setup

### 3.1 Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment using `uv` (recommended):
   ```bash
   uv venv .venv
   uv pip install -r requirements.txt --python .venv
   ```

3. Run the backend development server:
   ```bash
   .venv/Scripts/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *(On Linux/macOS: `.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`)*

4. Verify backend health:
   ```bash
   curl http://127.0.0.1:8000/api/v1/health
   curl http://127.0.0.1:8000/api/v1/health/database
   ```

### 3.2 Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 4. Testing & Verification

### Running Backend Pytest Suite:
```bash
# From workspace root
backend/.venv/Scripts/pytest.exe backend/tests -v
```

### Running Frontend Typecheck & Build:
```bash
# From workspace root
npm run --prefix frontend typecheck
npm run --prefix frontend build
```

---

## 5. Security & Development Directives

- **Synthetic Data Only:** Never import real customer PII, debit card numbers, or live banking credentials.
- **Account Masking:** In all user-facing UI and response formats, mask account numbers (`maskAccountId("ACC_12345678")` -> `"ACC_****5678"`).
- **Environment Isolation:** Never commit `.env` files. Maintain `.env.example` as the canonical reference.
- **Interface Contracts:** Any changes to Pydantic schemas in `backend/app/schemas/` must be synchronized with TypeScript interfaces in `frontend/src/types/`.

