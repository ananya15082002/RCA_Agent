#!/bin/bash

echo "=== STARTING ERROR DASHBOARD WITH UI CHANGES ==="

# Navigate to RCA_Agent directory
cd ~/RCA_Agent

# Kill any existing error dashboard processes
echo "Stopping existing processes..."
pkill -f error_dashboard.py
sleep 3

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start error dashboard with new UI
echo "Starting error dashboard..."
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
echo $! > error_dashboard.pid

echo "✅ Error Dashboard started with PID: $(cat error_dashboard.pid)"

# Wait and check status
sleep 5
echo ""
echo "=== STATUS CHECK ==="

if ps -p $(cat error_dashboard.pid) > /dev/null; then
    echo "✅ Process is running"
else
    echo "❌ Process failed to start"
    echo "Check logs: tail -20 logs/error_dashboard.log"
fi

echo ""
echo "Port check:"
netstat -tlnp 2>/dev/null | grep :8502 || echo "❌ Port not listening"

echo ""
echo "=== NEW UI FEATURES ==="
echo "🎨 Uniform theme system implemented"
echo "🌙 Dark/Light theme switching"
echo "🎯 Consistent colors across all elements"
echo "⚡ Dynamic theme changes without reload"

echo ""
echo "📊 Error Dashboard: http://3.7.67.210:8502"
echo "🔍 RCA Portal: http://3.7.67.210:8501"

echo ""
echo "=== HOW TO TEST THEMES ==="
echo "1. Open http://3.7.67.210:8502"
echo "2. Look for 'Theme Settings' in the left sidebar"
echo "3. Change between 'Light' and 'Dark' themes"
echo "4. See the entire dashboard switch themes uniformly" 