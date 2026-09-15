#!/bin/sh
set -e

# Wait for PostgreSQL database if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for database to be ready..."
  python - <<'EOF'
import os
import sys
import time
import psycopg2
from urllib.parse import urlparse

db_url = os.getenv("DATABASE_URL", "")
if db_url:
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port or 5432

    max_retries = 30
    retry_interval = 2
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=database,
                user=username,
                password=password,
                host=hostname,
                port=port,
                connect_timeout=3
            )
            conn.close()
            print("Database is ready!")
            sys.exit(0)
        except Exception as e:
            print(f"Waiting for database at {hostname}:{port}... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    print("Database connection timed out.")
    sys.exit(1)
EOF
fi

# Run database migrations if executing the main API server
if [ "$1" = "uvicorn" ] || [ "$1" = "python" ]; then
  echo "Applying database migrations (Alembic)..."
  alembic upgrade head || echo "Migration warning: proceeding with startup..."
fi

# Execute the given command
exec "$@"
