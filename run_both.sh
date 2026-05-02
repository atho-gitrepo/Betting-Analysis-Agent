#!/bin/bash

# Script to run both Analytics Service and Streamlit Dashboard in one container

echo "🚀 Starting Betting Analytics System"
echo "====================================="

# Set up logging
LOG_DIR="/app/logs"
mkdir -p $LOG_DIR

# Function to check if service is healthy
check_service() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Start Streamlit Dashboard in background
echo "📊 Starting Streamlit Dashboard..."
streamlit run dashboard.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --logger.level=info \
    2>&1 | tee -a $LOG_DIR/dashboard.log &

DASHBOARD_PID=$!
echo "✅ Dashboard started (PID: $DASHBOARD_PID)"

# Wait for dashboard to initialize
sleep 5

# Run analytics service (will exit after completion)
echo "🤖 Running Analytics Service..."
python analytics_service.py 2>&1 | tee -a $LOG_DIR/analytics.log
ANALYTICS_EXIT=$?

echo "✅ Analytics service completed with exit code: $ANALYTICS_EXIT"

# Setup cron-like behavior using while loop
echo "🔄 Setting up periodic analytics (every 6 hours)..."
while true; do
    echo "Waiting 6 hours for next analytics run..."
    sleep 21600  # 6 hours in seconds
    
    echo "Running scheduled analytics at $(date)..."
    python analytics_service.py 2>&1 | tee -a $LOG_DIR/analytics.log
    echo "Scheduled analytics completed at $(date)"
done &

CRON_PID=$!

# Keep the container running and monitor services
echo "====================================="
echo "🎯 All services are running!"
echo "📊 Dashboard: http://localhost:8501"
echo "📝 Logs: $LOG_DIR/"
echo "====================================="

# Monitor processes and restart if needed
while true; do
    if ! check_service "streamlit"; then
        echo "⚠️ Dashboard crashed! Restarting..."
        streamlit run dashboard.py \
            --server.port=8501 \
            --server.address=0.0.0.0 \
            --server.headless=true \
            --server.enableCORS=false \
            --server.enableXsrfProtection=false \
            2>&1 | tee -a $LOG_DIR/dashboard.log &
        DASHBOARD_PID=$!
        echo "✅ Dashboard restarted (PID: $DASHBOARD_PID)"
    fi
    
    sleep 30
done