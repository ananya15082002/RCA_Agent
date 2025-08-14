#!/bin/bash

echo "=== FIXING ERROR DASHBOARD ==="
echo ""

# Update code
echo "1. Updating code..."
git pull origin main
echo "✅ Code updated"
echo ""

# Stop current error dashboard
echo "2. Stopping current error dashboard..."
pkill -f error_dashboard.py
sleep 3
echo "✅ Stopped"
echo ""

# Clear cache
echo "3. Clearing cache..."
rm -rf ~/.streamlit/cache/* 2>/dev/null || true
rm -rf ~/.cache/streamlit/* 2>/dev/null || true
echo "✅ Cache cleared"
echo ""

# Replace error dashboard with minimal version
echo "4. Replacing error dashboard with minimal version..."
cp minimal_dashboard.py error_dashboard.py
echo "✅ Replaced"
echo ""

# Start error dashboard
echo "5. Starting error dashboard..."
source venv/bin/activate
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false > logs/error_dashboard.log 2>&1 &
echo $! > error_dashboard.pid
echo "✅ Error Dashboard started with PID: $(cat error_dashboard.pid)"
echo ""

# Wait and check
echo "6. Waiting for startup..."
sleep 10

# Check status
echo "7. Checking status..."
echo "   Process:"
ps -p $(cat error_dashboard.pid) > /dev/null && echo "   ✅ RUNNING (PID: $(cat error_dashboard.pid))" || echo "   ❌ NOT RUNNING"
echo "   Port:"
netstat -tlnp 2>/dev/null | grep :8502 && echo "   ✅ Port 8502 listening" || echo "   ❌ Port 8502 not listening"
echo ""

echo "🎯 FIX APPLIED:"
echo "   ✅ Replaced problematic error dashboard with minimal version"
echo "   ✅ Cleared all cache"
echo "   ✅ Fresh startup"
echo ""
echo "📊 Error Dashboard: http://3.7.67.210:8502"
echo "🔍 RCA Portal: http://3.7.67.210:8501" 