#!/bin/bash
# Starbucks Birthday Offer Watch - Automated Daily Refresh Script
# Runs at midnight (00:00) to check for updates to Starbucks rewards terms
# If changes detected, updates the database automatically

set -e

PROJECT_ROOT="/Users/sunny/Birthday_Freebies"
BACKEND_DIR="$PROJECT_ROOT/backend"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/starbucks-watch.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Add timestamp to log
echo "========================================" >> "$LOG_FILE"
echo "Starbucks watch started at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# Navigate to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment
source "$PROJECT_ROOT/.venv/bin/activate"

# Set environment variables for watch service
export STARBUCKS_INGEST_REGION="bay_area"
export STARBUCKS_WATCH_MAX_RETRIES="3"
export STARBUCKS_WATCH_BACKOFF_SECONDS="60,300,900"
export STARBUCKS_WATCH_STALE_AFTER_MINUTES="30"
export STARBUCKS_WATCH_ALERT_FAILURE_THRESHOLD="2"
# Optional: Set webhook URL for alerts if needed
# export STARBUCKS_ALERT_WEBHOOK_URL="https://your-webhook-url"

# Run the watch command
echo "Running: npm run watch:starbucks" >> "$LOG_FILE"
PYTHONPATH=. npm run watch:starbucks >> "$LOG_FILE" 2>&1 || {
    EXIT_CODE=$?
    echo "Watch failed with exit code: $EXIT_CODE" >> "$LOG_FILE"
    # Don't exit on failure; log it and continue
}

# Log completion
echo "Starbucks watch completed at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

exit 0
