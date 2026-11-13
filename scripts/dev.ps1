Write-Host "Starting Sentinel.AML Platform (Backend + Frontend)..." -ForegroundColor Cyan

# Start Backend
$backendProcess = Start-Process -FilePath "backend\.venv\Scripts\uvicorn.exe" -ArgumentList "backend.app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" -PassThru -NoNewWindow

Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Backend running on http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)" -ForegroundColor Green
Write-Host "Starting Frontend on http://localhost:3000..." -ForegroundColor Cyan

try {
    npm run --prefix frontend dev
}
finally {
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Write-Host "Stopping backend process..." -ForegroundColor Yellow
        Stop-Process -Id $backendProcess.Id -Force
    }
}

