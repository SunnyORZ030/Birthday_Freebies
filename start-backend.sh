#!/bin/bash
# Birthday Freebies Backend Starter Script

cd "$(dirname "$0")/backend" || exit 1

# Activate virtual environment
source ../.venv/bin/activate

# Start FastAPI backend
echo "🚀 Starting Birthday Freebies Backend..."
echo "📍 API will be available at: http://localhost:3001"
echo "Press Ctrl+C to stop"
echo ""

npm run dev
