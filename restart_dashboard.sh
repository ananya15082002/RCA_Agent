#!/bin/bash

echo "=== RESTARTING ERROR DASHBOARD ==="

# Kill any existing error dashboard processes
pkill -f error_dashboard.py
sleep 3

# Activate virtual environment and start error dashboard
cd ~/RCA_Agent
source venv/bin/activate

# Start error dashboard in background
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
echo $! > error_dashboard.pid

echo "✅ Error Dashboard started with PID: $(cat error_dashboard.pid)"

# Wait a moment and check if it's running
sleep 5
if ps -p $(cat error_dashboard.pid) > /dev/null; then
    echo "✅ Process is running"
else
    echo "❌ Process failed to start"
fi

# Check port
echo "Port check:"
netstat -tlnp 2>/dev/null | grep :8502 || echo "❌ Port not listening"

echo ""
echo "📊 Error Dashboard: http://3.7.67.210:8502" 