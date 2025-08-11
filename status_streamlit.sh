#!/bin/bash

echo "🚨 Error RCA System Status (Streamlit)"
echo "==========================================="
echo ""

# Check Streamlit Portal
echo "🌐 Streamlit Portal Status:"
if curl -s -I http://localhost:8501 > /dev/null; then
    echo "✅ RUNNING - http://localhost:8501"
else
    echo "❌ NOT RUNNING"
fi
echo ""

# Check Streamlit Dashboard
echo "📊 Streamlit Dashboard Status:"
if curl -s -I http://localhost:8502 > /dev/null; then
    echo "✅ RUNNING - http://localhost:8502"
else
    echo "❌ NOT RUNNING"
fi
echo ""

# Check Error Data
echo "📊 Data Status:"
ERROR_COUNT=$(ls -1 error_outputs/error_* 2>/dev/null | wc -l)
echo "📁 Error Reports: $ERROR_COUNT"
echo ""

# Show Process Status
echo "🔄 Process Status:"
STREAMLIT_PORTAL_PID=$(ps aux | grep "streamlit.*streamlit_portal.py" | grep -v grep | awk '{print $2}' | head -1)
STREAMLIT_DASHBOARD_PID=$(ps aux | grep "streamlit.*error_dashboard.py" | grep -v grep | awk '{print $2}' | head -1)
PIPELINE_PID=$(ps aux | grep "python rca_pipeline.py" | grep -v grep | awk '{print $2}' | head -1)

if [ -n "$STREAMLIT_PORTAL_PID" ]; then
    echo "✅ Streamlit Portal PID: $STREAMLIT_PORTAL_PID"
else
    echo "❌ Streamlit Portal: Not running"
fi

if [ -n "$STREAMLIT_DASHBOARD_PID" ]; then
    echo "✅ Streamlit Dashboard PID: $STREAMLIT_DASHBOARD_PID"
else
    echo "❌ Streamlit Dashboard: Not running"
fi

if [ -n "$PIPELINE_PID" ]; then
    echo "✅ RCA Pipeline PID: $PIPELINE_PID"
else
    echo "❌ RCA Pipeline: Not running"
fi
echo ""

echo "🌐 Access URLs:"
echo "   RCA Portal: http://localhost:8501"
echo "   Error Dashboard: http://localhost:8502"
echo "   Network Access: http://10.45.249.4:8501 (Portal)"
echo "   Network Access: http://10.45.249.4:8502 (Dashboard)"
echo ""
echo "📋 Management Commands:"
echo "   View portal logs: tail -f logs/streamlit_portal.log"
echo "   View dashboard logs: tail -f logs/error_dashboard.log"
echo "   View pipeline logs: tail -f logs/rca_pipeline.log"
echo ""
echo "🎯 Google Chat Integration:"
echo "   ✅ Alerts will link to Streamlit Portal"
echo "   ✅ Direct access to error reports"
echo "   ✅ Real-time error detection active"
echo "   ✅ Clean text-based alerts (no charts due to size limits)" 