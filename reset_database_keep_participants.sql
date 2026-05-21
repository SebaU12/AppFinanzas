-- Reset Database Script (Keep Participants)
-- This script deletes all transactional data while keeping categories, subcategories, AND participants
-- Run this with: docker exec -i finanzas-db psql -U finanzas_user -d finanzas < reset_database_keep_participants.sql

\echo '==================================='
\echo 'Starting database reset...'
\echo 'Keeping: Categories and Participants'
\echo '==================================='

-- Show current counts before deletion
\echo ''
\echo 'Current data counts:'
SELECT
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM monthly_budgets) as budgets,
  (SELECT COUNT(*) FROM credit_cards) as credit_cards,
  (SELECT COUNT(*) FROM debit_cards) as debit_cards,
  (SELECT COUNT(*) FROM card_installments) as installments,
  (SELECT COUNT(*) FROM participants) as participants,
  (SELECT COUNT(*) FROM categories) as categories;

\echo ''
\echo 'Deleting data in correct order...'

-- Delete in correct order to avoid foreign key violations
DELETE FROM reimbursement_details;
\echo '✓ Deleted reimbursement_details'

DELETE FROM monthly_reimbursements;
\echo '✓ Deleted monthly_reimbursements'

DELETE FROM accounts_payable;
\echo '✓ Deleted accounts_payable'

DELETE FROM accounts_receivable;
\echo '✓ Deleted accounts_receivable'

DELETE FROM card_installments;
\echo '✓ Deleted card_installments'

DELETE FROM expected_purchases;
\echo '✓ Deleted expected_purchases'

DELETE FROM transactions;
\echo '✓ Deleted transactions'

DELETE FROM monthly_budgets;
\echo '✓ Deleted monthly_budgets'

DELETE FROM credit_cards;
\echo '✓ Deleted credit_cards'

DELETE FROM debit_cards;
\echo '✓ Deleted debit_cards'

-- Verify categories and participants are still there
\echo ''
\echo 'Verifying preserved data...'
SELECT
  COUNT(*) as total_categories,
  COUNT(*) FILTER (WHERE parent_id IS NULL) as parent_categories,
  COUNT(*) FILTER (WHERE parent_id IS NOT NULL) as subcategories
FROM categories;

\echo ''
\echo 'Participants:'
SELECT id, name, default_percentage FROM participants;

-- Show final counts
\echo ''
\echo 'Final data counts:'
SELECT
  (SELECT COUNT(*) FROM transactions) as transactions,
  (SELECT COUNT(*) FROM monthly_budgets) as budgets,
  (SELECT COUNT(*) FROM credit_cards) as credit_cards,
  (SELECT COUNT(*) FROM debit_cards) as debit_cards,
  (SELECT COUNT(*) FROM card_installments) as installments,
  (SELECT COUNT(*) FROM participants) as participants,
  (SELECT COUNT(*) FROM categories) as categories;

\echo ''
\echo '==================================='
\echo 'Database reset complete!'
\echo 'Categories, subcategories, and participants preserved.'
\echo '==================================='
