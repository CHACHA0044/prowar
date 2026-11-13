#!/usr/bin/env bash
set -e

echo "Setting up Sentinel.AML Development Environment..."

echo ""
echo "[1/2] Setting up Python backend..."
if [ ! -d "backend/.venv" ]; then
    uv venv backend/.venv
fi
uv pip install -r backend/requirements.txt --python backend/.venv
echo "Backend dependencies installed."

echo ""
echo "[2/2] Setting up Next.js frontend..."
npm install --prefix frontend
echo "Frontend dependencies installed."

echo ""
echo "Setup complete! Run ./scripts/dev.sh to start services."

