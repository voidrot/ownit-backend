#!/bin/bash
set -e

# Wait for the database to be available
echo "Waiting for postgres..."
python << END
import sys
import time
import os
import psycopg
from urllib.parse import urlparse

# Get DB config
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found, skipping wait.")
    sys.exit(0)

url = urlparse(db_url)
username = url.username
password = url.password
database = url.path[1:]
hostname = url.hostname
port = url.port

while True:
    try:
        conn = psycopg.connect(
            dbname=database,
            user=username,
            password=password,
            host=hostname,
            port=port,
            connect_timeout=3
        )
        conn.close()
        print("Postgres is ready!")
        break
    except psycopg.OperationalError as e:
        print(f"Waiting for Postgres... {e}")
        time.sleep(1)
END

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"
