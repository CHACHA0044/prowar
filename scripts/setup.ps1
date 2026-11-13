Write-Host "Setting up Sentinel.AML Development Environment..." -ForegroundColor Cyan

# Backend setup
Write-Host "`n[1/2] Setting up Python backend..." -ForegroundColor Yellow
if (-not (Test-Path "backend\.venv")) {
    uv venv backend\.venv
}
uv pip install -r backend\requirements.txt --python backend\.venv
Write-Host "Backend dependencies installed successfully." -ForegroundColor Green

# Frontend setup
Write-Host "`n[2/2] Setting up Next.js frontend..." -ForegroundColor Yellow
npm install --prefix frontend
Write-Host "Frontend dependencies installed successfully." -ForegroundColor Green

Write-Host "`nSetup complete! Run .\scripts\dev.ps1 to start services." -ForegroundColor Cyan

