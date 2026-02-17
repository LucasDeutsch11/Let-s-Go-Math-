#!/usr/bin/env bash
set -euo pipefail

# Usage: ./start_server.sh [PORT]
# Default port: 5003

PORT=${1:-5003}

echo "Preparing to start Flask on port $PORT"

# Find and kill any process using the port
PIDS=$(lsof -t -i:"$PORT" || true)
if [ -n "$PIDS" ]; then
  echo "Killing processes on port $PORT: $PIDS"
  kill $PIDS || kill -9 $PIDS || true
  sleep 0.5
fi

# Activate virtualenv if present
if [ -f venv/bin/activate ]; then
  echo "Activating virtualenv venv"
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

echo "Starting Flask app (foreground). Use Ctrl+C to stop."
python3 app.py
