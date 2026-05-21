# Quick Start Guide

Get your Finanzas app up and running in 5 minutes!

## Prerequisites

- Python 3.9+ with virtual environment at `.venv/`
- Node.js 18+ and npm
- Docker and Docker Compose
- PostgreSQL (via Docker)

## 🚀 Setup Steps

### 1. Start PostgreSQL

```bash
# From project root
docker-compose up -d

# Verify it's running
docker ps
# Should show postgres container on port 5432
```

### 2. Load Categories

```bash
cd backend
python load_seeds.py
```

**Expected output:**
```
🌱 Loading category seeds...
✅ Successfully loaded 47 categories!

📊 Category Summary:
   - Income categories: 5
   - Expense categories: 42
   - Personal expenses: 15
   - Credit card allowed: 30
```

### 3. Create Test Data

```bash
# Still in backend/
python create_test_data.py
```

**Expected output:**
```
✅ Test data created successfully!

You can now:
  1. Start the backend
  2. Start the frontend
  3. Visit http://localhost:5173
```

### 4. Start the Backend

```bash
# Terminal 1 - from backend/
../.venv/bin/python -m uvicorn app.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

🔗 API Docs: http://localhost:8000/docs

### 5. Start the Frontend

```bash
# Terminal 2 - from frontend/
npm run dev
```

**You should see:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

🌐 App: http://localhost:5173

## ✅ Verify Everything Works

### Option A: Visual Check (Frontend)

1. Open http://localhost:5173
2. Check **Dashboard** - Should show:
   - Income/Expense stats (not zeros)
   - Charts with real data
   - No "Using mock data" warnings

3. Check **Transactions** page:
   - Should list ~10 transactions
   - Filter by type should work
   - Should show Lu and Chebos

4. Check **Budget** page:
   - Select current month
   - Should show planned vs actual
   - Charts should display

### Option B: API Testing (Backend)

```bash
# From backend/
python test_api_flows.py
```

**Expected output:**
```
🧪 Testing API Flows
📊 Database Status:
   Participants: 2
   Categories: 47
   Transactions: 10+

✅ PASS - Transaction Flow
✅ PASS - Budget Comparison
✅ PASS - Reimbursement Calculation
✅ PASS - Credit Card Flow
✅ PASS - Monthly Summary

Total: 5/5 tests passed
🎉 All tests passed!
```

## 📊 Test the Key Features

### 1. View Transactions

**Frontend:**
- Navigate to Transactions page
- Should see transactions from Lu and Chebos
- Try filtering by type (Income/Expense)

**API:**
```bash
curl http://localhost:8000/transactions | jq
```

### 2. Check Budget Status

**Frontend:**
- Go to Budget page
- Select current month (YYYY-MM format)
- See planned vs actual comparison

**API:**
```bash
MONTH=$(date +%Y-%m)
curl "http://localhost:8000/budget/month/$MONTH" | jq
```

### 3. Calculate Reimbursements

**Frontend:**
- Go to Reimbursements page
- Click "Calculate" button
- Should show Lu (25%) and Chebos (75%) split

**API:**
```bash
MONTH=$(date +%Y-%m)
curl -X POST "http://localhost:8000/reimbursements/calculate/$MONTH" | jq
```

### 4. View Credit Cards

**Frontend:**
- Go to Credit Cards page
- Should show 2 credit cards
- Click a card to see installments

**API:**
```bash
curl http://localhost:8000/credit-cards | jq
```

## 🧪 Test CSV Import

### Create Test CSV

```bash
# Create test CSV file
cat > test_import.csv << 'EOF'
Marca temporal,Fecha del movimiento,Responsable,Tipo,Monto,Descripción,Categoria ,Subcategorias Alimentacion
11/02/2024 10:30:00,10/02/2024,Copain,Gasto,99.99,Test CSV Import,Alimentacion,Compras Depa
EOF
```

### Import via API

```bash
curl -X POST "http://localhost:8000/csv/import" \
  -F "file=@test_import.csv"
```

**Expected:**
```json
{
  "message": "CSV import completed",
  "statistics": {
    "total": 1,
    "success": 1,
    "errors": []
  }
}
```

### Verify in Frontend

1. Go to Transactions page
2. Should see new transaction: "Test CSV Import"
3. Amount: $99.99
4. Participant: Lu (mapped from "Copain")

## 🔧 Troubleshooting

### Backend won't start

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
# Must be run FROM backend/ directory
```

### Database connection error

**Error:** `could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL is running
docker ps

# If not running, start it
docker-compose up -d

# Check logs
docker-compose logs postgres
```

### Frontend shows "Using mock data"

**Possible causes:**
1. Backend not running → Start backend first
2. Wrong API URL → Check `frontend/.env`
3. CORS issue → Check backend CORS settings in `main.py`

**Verify API connection:**
```bash
curl http://localhost:8000/transactions
# Should return JSON, not an error
```

### Empty Dashboard

**Cause:** No data in database

**Solution:**
```bash
cd backend
python create_test_data.py
```

Refresh the frontend page.

## 📝 Next Steps

Now that everything is working:

1. **Explore the API** - Visit http://localhost:8000/docs
2. **Add your own data** - Use the API or CSV import
3. **Try reimbursement calculations** - Calculate splits for the month
4. **Set up credit card purchases** - Create installment plans
5. **Run simulations** - Plan future purchases

## 🎯 Common Use Cases

### Add a New Transaction

```bash
curl -X POST "http://localhost:8000/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-02-11",
    "description": "Grocery Shopping",
    "amount": 125.50,
    "category_id": 1,
    "participant_id": 1,
    "payment_method": "debit"
  }'
```

### Create Monthly Budget

```bash
MONTH=$(date +%Y-%m)
curl -X POST "http://localhost:8000/budget" \
  -H "Content-Type: application/json" \
  -d "{
    \"month\": \"$MONTH\",
    \"category_id\": 1,
    \"planned_amount\": 800
  }"
```

### Calculate Month Reimbursements

```bash
MONTH=$(date +%Y-%m)
curl -X POST "http://localhost:8000/reimbursements/calculate/$MONTH"
```

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Testing Guide:** See `TESTING_GUIDE.md`
- **Architecture Details:** See `AGENT.md`
- **Project Overview:** See `CLAUDE.md`

---

**Need help?** Check the troubleshooting section or review the error messages in the terminal.
