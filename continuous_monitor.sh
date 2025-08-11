#!/bin/bash

# 🔄 Continuous System Monitor
# This script monitors and restarts failed components automatically

echo "🔄 Starting Continuous System Monitor..."
echo "📊 Monitoring all components every 30 seconds..."
echo ""

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Checking system status..."
    
    # Check RCA Pipeline
    if ! pgrep -f "python.*rca_pipeline" > /dev/null; then
        echo "❌ RCA Pipeline stopped, restarting..."
        source venv/bin/activate
        nohup python rca_pipeline.py > logs/rca_pipeline.log 2>&1 &
        echo "✅ RCA Pipeline restarted"
    else
        echo "✅ RCA Pipeline running"
    fi
    
    # Check Streamlit Portal
    if ! pgrep -f "streamlit.*streamlit_portal" > /dev/null; then
        echo "❌ Streamlit Portal stopped, restarting..."
        source venv/bin/activate
        nohup streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit_portal.log 2>&1 &
        echo "✅ Streamlit Portal restarted"
    else
        echo "✅ Streamlit Portal running"
    fi
    
    # Check Error Dashboard
    if ! pgrep -f "streamlit.*error_dashboard" > /dev/null; then
        echo "❌ Error Dashboard stopped, restarting..."
        source venv/bin/activate
        nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
        echo "✅ Error Dashboard restarted"
    else
        echo "✅ Error Dashboard running"
    fi
    
    # Check web services
    if ! curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8501 | grep -q "200"; then
        echo "⚠️ Streamlit Portal web service not responding"
    else
        echo "✅ Streamlit Portal web service OK"
    fi
    
    if ! curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8502 | grep -q "200"; then
        echo "⚠️ Error Dashboard web service not responding"
    else
        echo "✅ Error Dashboard web service OK"
    fi
    
    # Show recent activity
    recent_errors=$(find error_outputs -name "error_*" -type d -mtime -1 2>/dev/null | wc -l)
    echo "📁 Recent errors: $recent_errors in last 24 hours"
    
    echo "----------------------------------------"
    sleep 30
done 