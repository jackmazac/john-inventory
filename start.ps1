# Quick start script for Fox Hardware Inventory System (Windows PowerShell)
# Installs uv, dependencies, starts server, imports data, and opens browser

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fox Hardware Inventory - Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install uv if not already installed
Write-Host "1. Checking for uv..." -ForegroundColor Yellow
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "   Installing uv..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Verify installation
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Write-Host "   ⚠️  uv installed but not in PATH. Please restart PowerShell or add to PATH manually." -ForegroundColor Yellow
            Write-Host "   Add $env:USERPROFILE\.cargo\bin to your PATH" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "   ✓ uv installed" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed to install uv: $_" -ForegroundColor Red
        Write-Host "   Please install manually:" -ForegroundColor Yellow
        Write-Host "   powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "   ✓ uv is already installed" -ForegroundColor Green
}

# Step 2: Install project dependencies
Write-Host "2. Installing project dependencies..." -ForegroundColor Yellow
try {
    uv pip install -e . 2>&1 | Out-Null
    Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Dependencies may already be installed" -ForegroundColor Yellow
}

# Step 3: Set up environment variables if .env doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "3. Setting up environment variables..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   ✓ Created .env from .env.example" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  No .env.example found, skipping" -ForegroundColor Yellow
    }
} else {
    Write-Host "3. Environment variables already configured" -ForegroundColor Green
}

# Step 4: Initialize database
Write-Host "4. Initializing database..." -ForegroundColor Yellow
try {
    uv run alembic upgrade head 2>&1 | Out-Null
    Write-Host "   ✓ Database initialized" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Database may already be initialized" -ForegroundColor Yellow
}

# Step 5: Check if server is already running
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "5. ⚠️  Server is already running on port 8000" -ForegroundColor Yellow
    Write-Host "   Stopping existing server..." -ForegroundColor Yellow
    Get-Process | Where-Object { $_.CommandLine -like "*uvicorn app.main:app*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Step 6: Start server in background
Write-Host "5. Starting server..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Wait for server to be ready
Write-Host "6. Waiting for server to be ready..." -ForegroundColor Yellow
$maxAttempts = 15
$attempt = 0
$serverReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "   ✓ Server is ready" -ForegroundColor Green
        $serverReady = $true
        break
    } catch {
        $attempt++
        if ($attempt -eq $maxAttempts) {
            Write-Host "   ✗ Server failed to start" -ForegroundColor Red
            Stop-Job $serverJob -ErrorAction SilentlyContinue
            Remove-Job $serverJob -ErrorAction SilentlyContinue
            exit 1
        }
        Start-Sleep -Seconds 1
    }
}

# Step 7: Import data if Excel file exists
if (Test-Path "WJBK Computer invetory list 2025.xlsx") {
    Write-Host "7. Importing data from Excel file..." -ForegroundColor Yellow
    try {
        uv run python import_data.py 2>&1 | Out-Null
        Write-Host "   ✓ Data import completed" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Data import had issues (server still running)" -ForegroundColor Yellow
    }
} else {
    Write-Host "7. ⚠️  Excel file not found: WJBK Computer invetory list 2025.xlsx" -ForegroundColor Yellow
    Write-Host "   Skipping data import" -ForegroundColor Yellow
}

# Step 8: Open browser
Write-Host "8. Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
Start-Process "http://localhost:8000"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server is running at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Job ID: $($serverJob.Id)" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the server: Stop-Job $($serverJob.Id); Remove-Job $($serverJob.Id)" -ForegroundColor Yellow
Write-Host "Or run: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Yellow
Write-Host ""
