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

1. Install dependencies:
```bash
uv pip install -e .
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:
```bash
alembic upgrade head
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Development

- Run tests: `pytest`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`
