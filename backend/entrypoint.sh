#!/bin/sh
set -e

echo "Esperando que la base de datos este lista..."
python -c "
import time, os, sys
import psycopg2

# psycopg2 no acepta 'postgresql+psycopg2://', necesita 'postgresql://'
url = os.environ.get('DATABASE_URL', '').replace('postgresql+psycopg2://', 'postgresql://')

for i in range(30):
    try:
        psycopg2.connect(url)
        print('Base de datos lista.')
        sys.exit(0)
    except Exception as e:
        print(f'Intento {i+1}/30 - esperando... ({e})')
        time.sleep(2)

print('ERROR: No se pudo conectar a la base de datos.')
sys.exit(1)
"

echo "Verificando estado de migraciones..."
python -c "
import os, sys
import psycopg2

url = os.environ.get('DATABASE_URL', '').replace('postgresql+psycopg2://', 'postgresql://')
conn = psycopg2.connect(url)
cur = conn.cursor()

# Check if transactions table exists (indicates schema was already created manually)
cur.execute(\"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='transactions')\")
tables_exist = cur.fetchone()[0]

# Check if alembic_version table exists
cur.execute(\"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')\")
alembic_exists = cur.fetchone()[0]

if tables_exist and not alembic_exists:
    # Tables exist but no alembic tracking — stamp as initial so only new migrations run
    print('Tablas existentes sin alembic_version. Marcando migracion inicial...')
    cur.execute(\"CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))\")
    cur.execute(\"INSERT INTO alembic_version VALUES ('001_initial')\")
    conn.commit()
    print('Marcado como 001_initial.')
elif tables_exist and alembic_exists:
    cur.execute('SELECT version_num FROM alembic_version')
    row = cur.fetchone()
    current = row[0] if row else None
    print(f'Revision actual en BD: {current}')
    # If the stored revision is not in our known chain, stamp to initial
    known = {'001_initial', '002_currency', '003_exchange_rate', '004_debit_card_currency', '005_installment_payment_tracking', '006_add_transfers', '007_reimbursement_income', '008_add_savings_cards', '009_expand_transfers_for_savings', '010_credit_limit_to_numeric'}
    if current and current not in known:
        print(f'Revision {current} no reconocida. Marcando como 001_initial...')
        cur.execute('UPDATE alembic_version SET version_num = %s', ('001_initial',))
        conn.commit()
        print('Listo.')

cur.close()
conn.close()
"

echo "Corriendo migraciones..."
alembic upgrade head

echo "Iniciando servidor..."
exec "$@"
