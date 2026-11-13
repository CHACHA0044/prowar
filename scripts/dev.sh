#!/usr/bin/env bash
set -e

echo "Starting Sentinel.AML Platform..."

# Start Backend in background
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

trap "kill $BACKEND_PID" EXIT

echo "Backend running on http://127.0.0.1:8000"
echo "Starting Frontend on http://localhost:3000..."

npm run --prefix frontend dev
