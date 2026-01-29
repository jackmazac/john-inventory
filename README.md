# Fox Hardware Inventory Management System

Internal hardware inventory management web application for Fox Corporation. Tracks IT hardware assets (laptops, desktops, monitors, peripherals) across a 3-year refresh cycle.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTMX + Jinja2 templates
- **Database**: SQLite (MVP), designed for easy migration to PostgreSQL
- **Styling**: TailwindCSS with dark theme

## Features

- Excel file ingestion with column mapping and validation
- Asset tracking with lifecycle management
- Manager verification campaigns
- Reporting and export capabilities
- Delta detection for imports
- Audit trail and history tracking

## Setup

1. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize database:
```bash
alembic upgrade head
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## Quick Start (Full Setup with Data Import)

**Option 1: Use the startup script (recommended):**

**macOS/Linux/WSL:**
```bash
./start.sh
```

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Option 2: Manual startup:**
```bash
# Start server in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 3

# Run the import script
uv run python import_data.py

# Server will continue running in background
# Access the application at: http://localhost:8000
# To stop the server: kill $SERVER_PID
```

**Option 3: Single command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & sleep 3 && uv run python import_data.py && echo "✓ Server running at http://localhost:8000" && wait
```

The startup script will:
- Start the FastAPI server on port 8000
- Wait for the server to be ready
- Import data from `WJBK Computer invetory list 2025.xlsx`
- Display the server URL and process information

## Development

- Run tests: `pytest`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
