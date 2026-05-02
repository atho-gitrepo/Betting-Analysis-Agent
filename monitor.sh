# Create a monitoring script
#!/bin/bash

echo "=== Betting Analytics System Status ==="
echo ""

# Check if Streamlit is running
if pgrep -f "streamlit" > /dev/null; then
    echo "✅ Dashboard: RUNNING"
    echo "   URL: https://betting-analytics.up.railway.app"
else
    echo "❌ Dashboard: STOPPED"
fi

# Check if analytics process manager is running
if pgrep -f "process_manager.py" > /dev/null; then
    echo "✅ Process Manager: RUNNING"
else
    echo "❌ Process Manager: STOPPED"
fi

# Show recent logs
echo ""r
echo "=== Recent Analytics Logs ==="
tail -20 /app/logs/analytics.log 2>/dev/null || echo "No logs yet"

echo ""
echo "=== Recent Dashboard Logs ==="
tail -20 /app/logs/dashboard.log 2>/dev/null || echo "No logs yet"