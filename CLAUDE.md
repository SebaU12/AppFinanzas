# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shared personal finance system (couple/household) with business-accounting logic. Runs 100% locally. The core domain principle: **an expense occurs when consumed, not when paid** — this governs credit card handling, budget impact, and statement generation.

## Commands

### Docker (Recommended)
```bash
# Start all services (database, backend, frontend)
docker-compose up

# Start in detached mode
docker-compose up -d

# Rebuild containers after dependency changes
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f          # All services
docker-compose logs -f backend  # Backend only
docker-compose logs -f frontend # Frontend only

# Access running containers
docker exec -it finanzas-backend bash
docker exec -it finanzas-frontend sh
```

Services will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

### Local Development (Alternative)
```bash
# Start PostgreSQL only
docker-compose up -d db

# Backend (local)
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload

# Frontend (local)
cd frontend && npm install
npm run dev
```

### Environment
Copy `.env.example` to `.env`. Docker services use internal networking (`db:5432`), local development uses `localhost:5432`.

## Architecture

### Backend (Python/FastAPI + SQLAlchemy + PostgreSQL)

```
backend/
├── app/
│   ├── main.py        # FastAPI app, mounts routers
│   └── database.py    # SQLAlchemy engine, SessionLocal, Base, get_db dependency
├── models/            # SQLAlchemy ORM models
├── routers/           # API route handlers (one per domain module)
├── schemas/           # Pydantic request/response schemas
└── services/          # Business logic (reimbursement calc, statement generation, etc.)
```

Each domain module follows the pattern: **Model → Schema → Service → Router**. The modules are:

1. **Participants** — people sharing finances, each with a default reimbursement percentage
2. **Categories** — income/expense types; `is_personal` excludes from reimbursements, `allows_credit` gates credit card usage. Category names are in Spanish (intentional)
3. **Monthly Budget** — spending limits per category per month (unique on month+category)
4. **Transactions** — actual income/expenses with payment method (cash/debit/credit) and optional credit card link
5. **Credit Cards & Installments** — cards have closing/payment days; credit transactions generate `CardInstallment` rows across future months
6. **Accounts Payable/Receivable** — future obligations generated from installments and reimbursements
7. **Reimbursements** — month-end settlement of shared expenses split by configurable percentages (excludes `is_personal` categories)
8. **Expected Purchases** — simulation of future multi-month purchases showing impact on budget, cash flow, and payables without creating real transactions
9. **Accounting Statements** — Income Statement, Cash Flow, Balance Sheet generated from transaction/installment data

### Frontend (React + Vite + Recharts)

Minimal scaffolding. React 18 with Recharts for financial data visualization. No router or state management library yet.

### Infrastructure

Docker Compose orchestrates three services:
- **db**: PostgreSQL 16 (data persisted to `./data/postgres/`)
- **backend**: FastAPI app with hot-reload (port 8000)
- **frontend**: Vite dev server with HMR (port 5173)

All services connected via `finanzas-network` bridge network. Backend and frontend have volume mounts for live code updates during development.

## Key Technical Details

- Database sessions use `get_db()` dependency (yields session, auto-closes)
- `Base = declarative_base()` in `database.py` — all models inherit from this
- `DATABASE_URL` read from env var with fallback to default PostgreSQL connection string
- CSV ingestion planned via Pandas for Google Forms data import
- Frontend communicates with backend via `VITE_API_BASE_URL` env var

## Development Roadmap

See `Goals.md` for the full implementation checklist and `AGENT.md` for detailed module specifications including entity schemas and usage flows.
