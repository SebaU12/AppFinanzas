#!/bin/sh
set -e

echo "Esperando que la base de datos este lista..."
python -c "
import time, os, sys
import psycopg2

url = os.environ.get('DATABASE_URL', '')
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

echo "Corriendo migraciones..."
alembic upgrade head

echo "Iniciando servidor..."
exec "$@"
