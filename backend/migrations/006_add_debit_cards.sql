-- Migration: Add debit_cards table and debit_card_id to transactions
-- This enables tracking of bank accounts and debit card balances

-- Create debit_cards table
CREATE TABLE IF NOT EXISTS debit_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    participant_id UUID NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    initial_balance NUMERIC(10, 2) NOT NULL DEFAULT 0,
    last_four_digits VARCHAR(4),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add debit_card_id column to transactions table
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS debit_card_id UUID REFERENCES debit_cards(id) ON DELETE SET NULL;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_transactions_debit_card_id ON transactions(debit_card_id);
CREATE INDEX IF NOT EXISTS idx_debit_cards_participant_id ON debit_cards(participant_id);
CREATE INDEX IF NOT EXISTS idx_debit_cards_active ON debit_cards(active);

-- Add comment explaining the purpose
COMMENT ON TABLE debit_cards IS 'Bank accounts and debit cards for tracking liquid money';
COMMENT ON COLUMN transactions.debit_card_id IS 'Optional link to debit card for DEBIT payment method transactions';
