#!/bin/bash

# 🛑 RCA System Stop Script
# This script stops all components of the 5xx Error RCA System

echo "🛑 Stopping 5xx Error RCA System..."

# Stop RCA Pipeline
echo "🛑 Stopping RCA Pipeline..."
if [ -f "rca_pipeline.pid" ]; then
    rca_pid=$(cat rca_pipeline.pid)
    if ps -p $rca_pid > /dev/null; then
        kill $rca_pid
        echo "✅ RCA Pipeline stopped (PID: $rca_pid)"
    else
        echo "ℹ️ RCA Pipeline was not running"
    fi
    rm -f rca_pipeline.pid
else
    pkill -f "python.*rca_pipeline" 2>/dev/null
    echo "✅ RCA Pipeline processes killed"
fi

# Stop Streamlit Portal
echo "🛑 Stopping Streamlit Portal..."
if [ -f "streamlit_portal.pid" ]; then
    portal_pid=$(cat streamlit_portal.pid)
    if ps -p $portal_pid > /dev/null; then
        kill $portal_pid
        echo "✅ Streamlit Portal stopped (PID: $portal_pid)"
    else
        echo "ℹ️ Streamlit Portal was not running"
    fi
    rm -f streamlit_portal.pid
else
    pkill -f "streamlit.*streamlit_portal" 2>/dev/null
    echo "✅ Streamlit Portal processes killed"
fi

# Stop Error Dashboard
echo "🛑 Stopping Error Dashboard..."
if [ -f "error_dashboard.pid" ]; then
    dashboard_pid=$(cat error_dashboard.pid)
    if ps -p $dashboard_pid > /dev/null; then
        kill $dashboard_pid
        echo "✅ Error Dashboard stopped (PID: $dashboard_pid)"
    else
        echo "ℹ️ Error Dashboard was not running"
    fi
    rm -f error_dashboard.pid
else
    pkill -f "streamlit.*error_dashboard" 2>/dev/null
    echo "✅ Error Dashboard processes killed"
fi

# Clean up any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "python.*rca_pipeline" 2>/dev/null
pkill -f "streamlit.*streamlit_portal" 2>/dev/null
pkill -f "streamlit.*error_dashboard" 2>/dev/null

# Wait for processes to fully stop
sleep 2

# Verify all processes are stopped
echo "🔍 Verifying all processes are stopped..."
if pgrep -f "python.*rca_pipeline" > /dev/null; then
    echo "⚠️ Some RCA Pipeline processes are still running"
else
    echo "✅ All RCA Pipeline processes stopped"
fi

if pgrep -f "streamlit.*streamlit_portal" > /dev/null; then
    echo "⚠️ Some Streamlit Portal processes are still running"
else
    echo "✅ All Streamlit Portal processes stopped"
fi

if pgrep -f "streamlit.*error_dashboard" > /dev/null; then
    echo "⚠️ Some Error Dashboard processes are still running"
else
    echo "✅ All Error Dashboard processes stopped"
fi

echo ""
echo "🛑 System stopped successfully!"
echo "💡 To restart the system, run: ./start_system.sh" 