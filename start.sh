#!/bin/bash
# Quick start script for Fox Hardware Inventory System
# Installs uv, dependencies, starts server, imports data, and opens browser

set -e

echo "=========================================="
echo "Fox Hardware Inventory - Quick Start"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ -n "$WINDIR" ]] || [[ "$OS" == "Windows_NT" ]]; then
    IS_WINDOWS=true
else
    IS_WINDOWS=false
fi

# Step 1: Install uv if not already installed
echo "1. Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "   Installing uv..."
    if [ "$IS_WINDOWS" = true ]; then
        # Windows installation via PowerShell
        echo "   Detected Windows - using PowerShell installer..."
        if command -v powershell.exe &> /dev/null; then
            powershell.exe -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
            # Add to PATH for current session
            export PATH="$USERPROFILE/.cargo/bin:$PATH"
            # Refresh PATH in current shell
            if [ -d "$USERPROFILE/.cargo/bin" ]; then
                export PATH="$USERPROFILE/.cargo/bin:$PATH"
            fi
        else
            echo "   ✗ PowerShell not found. Please install uv manually:"
            echo "     powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\""
            exit 1
        fi
    else
        # Unix-like installation
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo "   ⚠️  uv installed but not in PATH. Please restart your terminal or add to PATH manually."
        if [ "$IS_WINDOWS" = true ]; then
            echo "   Windows: Add $USERPROFILE\\.cargo\\bin to your PATH"
        else
            echo "   Unix: Add $HOME/.cargo/bin to your PATH"
        fi
        exit 1
    fi
    echo "   ✓ uv installed"
else
    echo "   ✓ uv is already installed"
fi

# Step 2: Install project dependencies
echo "2. Installing project dependencies..."
if uv pip install -e . > /dev/null 2>&1; then
    echo "   ✓ Dependencies installed"
else
    echo "   ⚠️  Dependencies may already be installed"
fi

# Step 3: Set up environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "3. Setting up environment variables..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "   ✓ Created .env from .env.example"
    else
        echo "   ⚠️  No .env.example found, skipping"
    fi
else
    echo "3. Environment variables already configured"
fi

# Step 4: Initialize database
echo "4. Initializing database..."
if uv run alembic upgrade head > /dev/null 2>&1; then
    echo "   ✓ Database initialized"
else
    echo "   ⚠️  Database may already be initialized"
fi

# Step 5: Check if server is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "5. ⚠️  Server is already running on port 8000"
    echo "   Stopping existing server..."
    pkill -f "uvicorn app.main:app" || true
    sleep 2
fi

# Step 6: Start server in background
echo "5. Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
echo "6. Waiting for server to be ready..."
for i in {1..15}; do
    if curl -s http://localhost:8000 > /dev/null 2>&1; then
        echo "   ✓ Server is ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ✗ Server failed to start"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Step 7: Import data if Excel file exists
if [ -f "WJBK Computer invetory list 2025.xlsx" ]; then
    echo "7. Importing data from Excel file..."
    if uv run python import_data.py > /dev/null 2>&1; then
        echo "   ✓ Data import completed"
    else
        echo "   ⚠️  Data import had issues (server still running)"
    fi
else
    echo "7. ⚠️  Excel file not found: WJBK Computer invetory list 2025.xlsx"
    echo "   Skipping data import"
fi

# Step 8: Open browser
echo "8. Opening browser..."
sleep 1
if command -v open &> /dev/null; then
    # macOS
    open http://localhost:8000
elif command -v xdg-open &> /dev/null; then
    # Linux
    xdg-open http://localhost:8000
elif command -v start &> /dev/null; then
    # Windows (Git Bash)
    start http://localhost:8000
else
    echo "   ⚠️  Could not auto-open browser"
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Server is running at: http://localhost:8000"
echo "Process ID: $SERVER_PID"
echo ""
echo "To stop the server: kill $SERVER_PID"
echo "Or run: pkill -f 'uvicorn app.main:app'"
echo ""
