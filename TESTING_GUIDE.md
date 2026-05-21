# Testing Guide - Full Stack Integration

## Prerequisites

Before testing, ensure you have:
- PostgreSQL running via Docker Compose
- Backend dependencies installed
- Frontend dependencies installed
- Database migrations applied (if using Alembic)

## Starting the Services

### 1. Start PostgreSQL

```bash
# From project root
docker-compose up -d
```

Verify it's running:
```bash
docker ps
# Should show postgres container running on port 5432
```

### 2. Start Backend

```bash
# From project root
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload

# Backend will be available at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### 3. Start Frontend

```bash
# From project root (in a new terminal)
cd frontend
npm run dev

# Frontend will be available at: http://localhost:5173
```

## Initial Data Setup

### Load Category Seeds

Create a script to load categories into the database:

```python
# backend/load_seeds.py
from app.database import SessionLocal
from models.category import Category
from seeds.categories_seed import CATEGORIES_SEED

db = SessionLocal()

try:
    # Clear existing categories (optional)
    # db.query(Category).delete()

    # Load new categories
    for cat_data in CATEGORIES_SEED:
        category = Category(**cat_data)
        db.add(category)

    db.commit()
    print(f"✅ Loaded {len(CATEGORIES_SEED)} categories successfully!")
except Exception as e:
    db.rollback()
    print(f"❌ Error loading categories: {e}")
finally:
    db.close()
```

Run it:
```bash
cd backend
../.venv/bin/python load_seeds.py
```

### Create Test Participants

Use the API docs (http://localhost:8000/docs) or create via API:

```bash
curl -X POST "http://localhost:8000/participants" \
  -H "Content-Type: application/json" \
  -d '{"name": "Lu", "default_reimbursement_percentage": 25}'

curl -X POST "http://localhost:8000/participants" \
  -H "Content-Type: application/json" \
  -d '{"name": "Chebos", "default_reimbursement_percentage": 75}'
```

## Testing Scenarios

### Test 1: Basic Transaction Flow

1. **Add a Transaction** via API:
```bash
curl -X POST "http://localhost:8000/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-02-11",
    "description": "Supermercado",
    "amount": 150.50,
    "type": "expense",
    "category_id": 1,
    "participant_id": 1,
    "payment_method": "debit"
  }'
```

2. **View in Frontend**:
   - Navigate to Dashboard (should show updated stats)
   - Go to Transactions page (should list the transaction)

### Test 2: Budget Tracking

1. **Create Monthly Budget** via API:
```bash
curl -X POST "http://localhost:8000/budget" \
  -H "Content-Type: application/json" \
  -d '{
    "month": "2024-02",
    "category_id": 1,
    "planned_amount": 800
  }'
```

2. **View in Frontend**:
   - Navigate to Budget page
   - Select current month
   - Should show planned vs actual comparison

### Test 3: CSV Import

1. **Prepare CSV** (use Google Forms export format):
```csv
Marca temporal,Fecha del movimiento,Responsable,Tipo,Monto,Descripción,Categoria ,Subcategorias Alimentacion
10/02/2024 10:30:00,10/02/2024,Copain,Gasto,150.50,Supermercado,Alimentacion,Compras Depa
```

2. **Import via API**:
```bash
curl -X POST "http://localhost:8000/csv/import" \
  -F "file=@your_transactions.csv"
```

3. **Verify** in frontend Transactions page

### Test 4: Credit Cards & Installments

1. **Create Credit Card**:
```bash
curl -X POST "http://localhost:8000/credit-cards" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Visa Banco Nacional",
    "last_four_digits": "4532",
    "participant_id": 1,
    "closing_day": 15,
    "payment_day": 5
  }'
```

2. **Create Transaction with Installments**:
```bash
curl -X POST "http://localhost:8000/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-02-11",
    "description": "Laptop",
    "amount": 1200,
    "type": "expense",
    "category_id": 10,
    "participant_id": 1,
    "payment_method": "credit",
    "credit_card_id": 1,
    "installments": 6
  }'
```

3. **View in Frontend**:
   - Credit Cards page should show card with installments
   - Should display payment schedule

### Test 5: Reimbursements

1. **Calculate Reimbursements** for current month:
```bash
curl -X POST "http://localhost:8000/reimbursements/calculate/2024-02"
```

2. **View in Frontend**:
   - Navigate to Reimbursements page
   - Should show breakdown by category
   - Display Lu (25%) and Chebos (75%) splits

### Test 6: Simulation

1. **Add Expected Purchase**:
```bash
curl -X POST "http://localhost:8000/expected-purchases" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "New Laptop",
    "total_amount": 1500,
    "category_id": 10,
    "start_month": "2024-03",
    "installments": 6
  }'
```

2. **Run Simulation**:
```bash
curl "http://localhost:8000/expected-purchases/simulate"
```

3. **View in Frontend**:
   - Navigate to Simulation page
   - Should show impact on future months

## Common Issues & Solutions

### Backend Not Starting

**Error**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Make sure you're running from `backend/` directory
- Run: `cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload`

### Database Connection Error

**Error**: `Connection refused` or `could not connect to server`
- **Solution**: Ensure PostgreSQL is running
- Check: `docker ps` and `docker-compose logs postgres`

### Frontend API Errors

**Error**: `Failed to fetch` or `CORS error`
- **Solution**: Check backend CORS configuration in `backend/app/main.py`
- Ensure frontend is using correct API URL (check `.env` file)

### Empty Dashboard

**Issue**: Dashboard shows zeros or "Using mock data"
- **Solution**: Add test data via API or CSV import
- Verify backend is running and accessible

## Next Steps

After verifying all tests pass:
1. Set up Docker networking for containerized deployment
2. Configure production environment variables
3. Set up data backup procedures
4. Document deployment process

## API Documentation

Full API documentation is available at: http://localhost:8000/docs

This includes:
- All available endpoints
- Request/response schemas
- Interactive testing interface
