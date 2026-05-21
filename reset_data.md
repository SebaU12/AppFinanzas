# Reset Database Guide

This guide explains how to reset the database, removing all transactional data while keeping categories and subcategories.

## What Gets Deleted

- ✅ All transactions
- ✅ All budgets
- ✅ All credit cards
- ✅ All debit cards
- ✅ All installments
- ✅ All reimbursements
- ✅ All accounts payable/receivable
- ✅ All expected purchases
- ✅ All participants (optional - see below)

## What Gets Kept

- ✅ Categories and subcategories structure

---

## Option 1: Using Docker (Recommended)

### Reset Database Keeping Categories Only

```bash
# Connect to the PostgreSQL container
docker exec -it finanzas-db psql -U finanzas_user -d finanzas

# Run the cleanup SQL
DELETE FROM reimbursement_details;
DELETE FROM monthly_reimbursements;
DELETE FROM accounts_payable;
DELETE FROM accounts_receivable;
DELETE FROM card_installments;
DELETE FROM expected_purchases;
DELETE FROM transactions;
DELETE FROM monthly_budgets;
DELETE FROM credit_cards;
DELETE FROM debit_cards;
DELETE FROM participants;

# Exit psql
\q
```

### Reset Database Keeping Categories AND Participants

```bash
# Connect to the PostgreSQL container
docker exec -it finanzas-db psql -U finanzas_user -d finanzas

# Run the cleanup SQL (without deleting participants)
DELETE FROM reimbursement_details;
DELETE FROM monthly_reimbursements;
DELETE FROM accounts_payable;
DELETE FROM accounts_receivable;
DELETE FROM card_installments;
DELETE FROM expected_purchases;
DELETE FROM transactions;
DELETE FROM monthly_budgets;
DELETE FROM credit_cards;
DELETE FROM debit_cards;

# Exit psql
\q
```

---

## Option 2: Using SQL Script File

### 1. Create the SQL Script

Create a file `reset_database.sql`:

```sql
-- Reset all transactional data, keep categories and subcategories
-- Order matters due to foreign key constraints

-- Delete in correct order to avoid FK violations
DELETE FROM reimbursement_details;
DELETE FROM monthly_reimbursements;
DELETE FROM account_payable;
DELETE FROM account_receivable;
DELETE FROM card_installments;
DELETE FROM expected_purchases;
DELETE FROM transactions;
DELETE FROM monthly_budgets;
DELETE FROM credit_cards;
DELETE FROM debit_cards;

-- Uncomment the line below if you also want to delete participants
-- DELETE FROM participants;

-- Verify categories are still there
SELECT COUNT(*) as total_categories FROM categories;
SELECT COUNT(*) as parent_categories FROM categories WHERE parent_id IS NULL;
SELECT COUNT(*) as subcategories FROM categories WHERE parent_id IS NOT NULL;

-- Show remaining data
SELECT
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM monthly_budgets) as budgets,
  (SELECT COUNT(*) FROM credit_cards) as credit_cards,
  (SELECT COUNT(*) FROM debit_cards) as debit_cards,
  (SELECT COUNT(*) FROM participants) as participants,
  (SELECT COUNT(*) FROM categories) as categories;
```

### 2. Execute the Script

```bash
# Using Docker
docker exec -i finanzas-db psql -U finanzas_user -d finanzas < reset_database.sql

# Or connect and run manually
docker exec -it finanzas-db psql -U finanzas_user -d finanzas -f /path/to/reset_database.sql
```

---

## Option 3: Complete Database Reset (Start Fresh)

If you want to completely reset everything including categories:

```bash
# Stop containers
docker compose down

# Remove the database volume
docker volume rm finanzas_db_data
# or
sudo rm -rf ./data/postgres

# Restart containers (will recreate database)
docker compose up -d

# Wait for database to initialize
sleep 5

# Run migrations if you have them, or manually create tables
```

---

## Verify the Reset

After resetting, verify the data:

```bash
# Connect to database
docker exec -it finanzas-db psql -U finanzas_user -d finanzas

# Check what's left
SELECT
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM monthly_budgets) as budgets,
  (SELECT COUNT(*) FROM credit_cards) as credit_cards,
  (SELECT COUNT(*) FROM debit_cards) as debit_cards,
  (SELECT COUNT(*) FROM participants) as participants,
  (SELECT COUNT(*) FROM categories) as categories;

# List all categories
SELECT
  c1.name as parent_category,
  c2.name as subcategory
FROM categories c1
LEFT JOIN categories c2 ON c2.parent_id = c1.id
WHERE c1.parent_id IS NULL
ORDER BY c1.name, c2.name;

\q
```

---

## Quick One-Line Reset Commands

### Keep Categories Only
```bash
docker exec -it finanzas-db psql -U finanzas_user -d finanzas -c "DELETE FROM reimbursement_details; DELETE FROM monthly_reimbursements; DELETE FROM accounts_payable; DELETE FROM accounts_receivable; DELETE FROM card_installments; DELETE FROM expected_purchases; DELETE FROM transactions; DELETE FROM monthly_budgets; DELETE FROM credit_cards; DELETE FROM debit_cards; DELETE FROM participants;"
```

### Keep Categories and Participants
```bash
docker exec -it finanzas-db psql -U finanzas_user -d finanzas -c "DELETE FROM reimbursement_details; DELETE FROM monthly_reimbursements; DELETE FROM accounts_payable; DELETE FROM accounts_receivable; DELETE FROM card_installments; DELETE FROM expected_purchases; DELETE FROM transactions; DELETE FROM monthly_budgets; DELETE FROM credit_cards; DELETE FROM debit_cards;"
```

---

## Troubleshooting

### Foreign Key Constraint Errors

If you get foreign key constraint errors, make sure to delete in this order:
1. reimbursement_details (depends on monthly_reimbursements)
2. monthly_reimbursements
3. account_payable
4. account_receivable
5. card_installments (depends on credit_cards and transactions)
6. expected_purchases
7. transactions (depends on categories, participants, cards)
8. monthly_budgets (depends on categories)
9. credit_cards (depends on participants)
10. debit_cards (depends on participants)
11. participants (last, if desired)

### Database Connection Issues

```bash
# Check if database is running
docker compose ps

# Check database logs
docker compose logs db

# Restart database
docker compose restart db
```

---

## Notes

- **Backup First**: If you have important data, create a backup before resetting:
  ```bash
  docker exec finanzas-db pg_dump -U finanzas_user finanzas_db > backup_$(date +%Y%m%d).sql
  ```

- **Categories**: Your category structure (parent categories and subcategories) will be preserved and ready to use.

- **Participants**: Decide whether to keep or delete participants based on whether you want to recreate user accounts.

- **No Undo**: These operations cannot be undone without a backup. Make sure you really want to delete the data.
