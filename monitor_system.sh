#!/bin/bash

# 📊 RCA System Monitor Script
# This script monitors the status of all components

echo "📊 5xx Error RCA System Monitor"
echo "================================"
echo ""

# Check RCA Pipeline
echo "🔧 RCA Pipeline Status:"
if [ -f "rca_pipeline.pid" ]; then
    rca_pid=$(cat rca_pipeline.pid)
    if ps -p $rca_pid > /dev/null; then
        echo "✅ RUNNING (PID: $rca_pid)"
        echo "📋 Process Info:"
        ps -p $rca_pid -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING (PID file exists but process dead)"
    fi
else
    if pgrep -f "python.*rca_pipeline" > /dev/null; then
        echo "⚠️ RUNNING (No PID file, but process exists)"
        pgrep -f "python.*rca_pipeline" | head -1 | xargs ps -p -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING"
    fi
fi

echo ""

# Check Streamlit Portal
echo "🌐 Streamlit Portal Status:"
if [ -f "streamlit_portal.pid" ]; then
    portal_pid=$(cat streamlit_portal.pid)
    if ps -p $portal_pid > /dev/null; then
        echo "✅ RUNNING (PID: $portal_pid)"
        echo "📋 Process Info:"
        ps -p $portal_pid -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING (PID file exists but process dead)"
    fi
else
    if pgrep -f "streamlit.*streamlit_portal" > /dev/null; then
        echo "⚠️ RUNNING (No PID file, but process exists)"
        pgrep -f "streamlit.*streamlit_portal" | head -1 | xargs ps -p -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING"
    fi
fi

echo ""

# Check Error Dashboard
echo "📊 Error Dashboard Status:"
if [ -f "error_dashboard.pid" ]; then
    dashboard_pid=$(cat error_dashboard.pid)
    if ps -p $dashboard_pid > /dev/null; then
        echo "✅ RUNNING (PID: $dashboard_pid)"
        echo "📋 Process Info:"
        ps -p $dashboard_pid -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING (PID file exists but process dead)"
    fi
else
    if pgrep -f "streamlit.*error_dashboard" > /dev/null; then
        echo "⚠️ RUNNING (No PID file, but process exists)"
        pgrep -f "streamlit.*error_dashboard" | head -1 | xargs ps -p -o pid,ppid,cmd,etime
    else
        echo "❌ NOT RUNNING"
    fi
fi

echo ""

# Test web services
echo "🌐 Web Service Status:"
echo "======================"

# Test Streamlit Portal
echo -n "🌐 Streamlit Portal (http://10.1.223.229:8501): "
if curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8501 | grep -q "200"; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

# Test Error Dashboard
echo -n "📊 Error Dashboard (http://10.1.223.229:8502): "
if curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8502 | grep -q "200"; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE"
fi

echo ""

# Check recent activity
echo "📈 Recent Activity:"
echo "=================="

# Check recent error outputs
echo -n "📁 Recent Error Outputs: "
recent_errors=$(find error_outputs -name "error_*" -type d -mtime -1 2>/dev/null | wc -l)
echo "$recent_errors in last 24 hours"

# Check log files
echo -n "📋 RCA Pipeline Log: "
if [ -f "logs/rca_pipeline.log" ]; then
    last_log=$(tail -1 logs/rca_pipeline.log 2>/dev/null | cut -c1-50)
    if [ -n "$last_log" ]; then
        echo "✅ Active - $last_log"
    else
        echo "⚠️ Empty log file"
    fi
else
    echo "❌ Log file not found"
fi

echo ""

# System resources
echo "💻 System Resources:"
echo "==================="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h . | tail -1 | awk '{print $5}')"

echo ""

# Quick actions
echo "🚀 Quick Actions:"
echo "================"
echo "📊 View RCA logs: tail -f logs/rca_pipeline.log"
echo "🌐 View Portal logs: tail -f logs/streamlit_portal.log"
echo "📈 View Dashboard logs: tail -f logs/error_dashboard.log"
echo "🔄 Restart system: ./start_system.sh"
echo "🛑 Stop system: ./stop_system.sh"
echo "📁 View recent errors: ls -la error_outputs/ | tail -5" 