#!/bin/bash
# Start the Sales Intelligence System backend
cd "$(dirname "$0")/../sales-intelligence/backend"
source venv/bin/activate
echo "Starting Sales Intelligence API on http://localhost:8000"
echo "Press Ctrl+C to stop"
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1
