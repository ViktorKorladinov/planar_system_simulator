#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Attempting to start Docker Desktop..."
  open -a Docker
  echo "Waiting for Docker to start (this may take a minute)..."
  while ! docker info > /dev/null 2>&1; do
    sleep 3
  done
  echo "Docker is now running!"
fi

echo "Starting Databases (PostgreSQL and Redis)..."
cd backend && docker compose up -d && cd ..

echo "Starting Celery worker..."
(cd backend && source .venv/bin/activate && celery -A core.celery_app worker --loglevel=info -P solo) &
CELERY_PID=$!

echo "Starting FastAPI backend..."
(cd backend && source .venv/bin/activate && python main.py) &
API_PID=$!

echo "Starting Frontend..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "Starting Simulator..."
(cd simulator && npm run dev) &
SIMULATOR_PID=$!

echo ""
echo "========================================================"
echo "✅ All services are starting up!"
echo "   - Frontend App:   http://localhost:5173"
echo "   - Simulator App:  http://localhost:3000"
echo "   - Backend API:    http://localhost:8000/docs"
echo "========================================================"
echo "Press [CTRL+C] to stop all services."
echo ""

# Trap Ctrl+C (SIGINT) to clean up background processes
trap "echo 'Stopping all services...'; kill $CELERY_PID $API_PID $FRONTEND_PID $SIMULATOR_PID; docker compose -f backend/docker-compose.yml stop; exit" INT TERM

# Wait indefinitely until interrupted
wait
