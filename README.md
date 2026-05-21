# Finanzas - Personal Finance Management System

A full-stack personal finance application for couples/households to manage shared expenses, budgets, and reimbursements.

## ✨ Features

- 📊 Track income and expenses with detailed categorization
- 💰 Set and monitor monthly budgets (planned vs actual)
- 💳 Manage credit card purchases with installment tracking
- 🤝 Calculate shared expense reimbursements (customizable splits)
- 🔮 Simulate future purchase impacts on cash flow
- 📥 Import transactions from Google Forms CSV
- 📈 Generate financial statements (Income Statement, Cash Flow, Balance Sheet)
- 👥 Multi-participant support with configurable reimbursement percentages

## 🚀 Quick Start

Get up and running in 5 minutes:

```bash
# 1. Start PostgreSQL
docker-compose up -d

# 2. Load categories
cd backend && python load_seeds.py

# 3. Create test data
python create_test_data.py

# 4. Start backend (Terminal 1)
../.venv/bin/python -m uvicorn app.main:app --reload

# 5. Start frontend (Terminal 2)
cd ../frontend && npm run dev

# 6. Open http://localhost:5173
```

**📖 See [QUICKSTART.md](QUICKSTART.md) for detailed instructions**

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Complete testing scenarios
- **[CLAUDE.md](CLAUDE.md)** - Architecture and commands
- **[AGENT.md](AGENT.md)** - Detailed backend specifications
- **[Goals.md](Goals.md)** - Development progress tracker

## 🛠️ Tech Stack

- **Backend:** Python 3.9+, FastAPI, SQLAlchemy, PostgreSQL, Pydantic
- **Frontend:** React 18, Vite, Recharts, React Router, Lucide Icons
- **Infrastructure:** Docker, Docker Compose
- **Testing:** Pytest (backend), API integration tests

## 📁 Project Structure

```
finanzas/
├── backend/           # FastAPI backend
│   ├── app/          # Main application
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   ├── routers/      # API endpoints
│   ├── seeds/        # Database seeds
│   ├── tests/        # Test suite
│   ├── load_seeds.py         # Load categories
│   ├── create_test_data.py   # Generate test data
│   └── test_api_flows.py     # API integration tests
├── frontend/          # React frontend
│   ├── src/
│   │   ├── pages/    # Page components
│   │   ├── components/ # Reusable components
│   │   ├── services/ # API client
│   │   └── utils/    # Helper functions
│   └── vite.config.js
└── docker-compose.yml # PostgreSQL container
```

## 🧪 Testing

### Backend API Tests
```bash
cd backend
python test_api_flows.py
```

### Manual Testing
```bash
# API Documentation
open http://localhost:8000/docs

# Test CSV Import
curl -X POST "http://localhost:8000/csv/import" \
  -F "file=@your_file.csv"
```

## 🎨 Design System

- **Primary Color:** #569B85 (Teal Green)
- **Secondary Color:** #FFC145 (Warm Yellow)
- **Accent Color:** #E78484 (Soft Red)
- **Background:** #D9F2ED (Light Mint)
- **Fonts:** Inter, Plus Jakarta Sans

## 📊 Current Status

✅ **Backend:** 100% Complete (11/11 modules)
✅ **Frontend:** 100% Complete (6/6 pages)
✅ **Integration:** All pages connected to API
🧪 **Testing:** Ready for end-to-end testing

See [Goals.md](Goals.md) for detailed progress.

## 🔧 Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose

### Backend Setup
```bash
# Create virtual environment
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt

# Start PostgreSQL
docker-compose up -d

# Load seeds and test data
cd backend
python load_seeds.py
python create_test_data.py

# Run server
../.venv/bin/python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📋 Environment Configuration

Copy `.env.example` to `.env` and adjust:

**Backend:** Database connection (defaults provided)
**Frontend:** `VITE_API_BASE_URL=http://localhost:8000`

## 🎯 Key Workflows

### Import Transactions from CSV
```bash
curl -X POST "http://localhost:8000/csv/import" \
  -F "file=@transactions.csv"
```

### Calculate Monthly Reimbursements
```bash
MONTH=$(date +%Y-%m)
curl -X POST "http://localhost:8000/reimbursements/calculate/$MONTH"
```

### Add a Transaction
```bash
curl -X POST "http://localhost:8000/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-02-11",
    "description": "Supermercado",
    "amount": 150.50,
    "category_id": 1,
    "participant_id": 1,
    "payment_method": "debit"
  }'
```

## 📝 License

MIT

## 🤝 Contributing

This is a personal project. Feel free to fork and adapt for your own use!
