#!/bin/bash

# 🚀 RCA System Startup Script
# This script starts all components of the 5xx Error RCA System

echo "🚀 Starting 5xx Error RCA System..."

# Kill any existing processes
echo "🛑 Stopping existing processes..."
pkill -f "python.*rca_pipeline" 2>/dev/null
pkill -f "streamlit.*streamlit_portal" 2>/dev/null
pkill -f "streamlit.*error_dashboard" 2>/dev/null
sleep 3

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p error_outputs
mkdir -p logs

# Function to start a service with monitoring
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3
    
    echo "🟢 Starting $service_name..."
    nohup $command > $log_file 2>&1 &
    local pid=$!
    echo "✅ $service_name started with PID: $pid"
    echo $pid > "${service_name}.pid"
    
    # Wait a moment and check if it's running
    sleep 2
    if ps -p $pid > /dev/null; then
        echo "✅ $service_name is running successfully"
    else
        echo "❌ $service_name failed to start"
        return 1
    fi
}

# Start RCA Pipeline
echo "🔧 Starting RCA Pipeline..."
start_service "rca_pipeline" "python rca_pipeline.py" "logs/rca_pipeline.log"

# Start Streamlit Portal
echo "🌐 Starting Streamlit Portal..."
start_service "streamlit_portal" "streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false" "logs/streamlit_portal.log"

# Start Error Dashboard
echo "📊 Starting Error Dashboard..."
start_service "error_dashboard" "streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false" "logs/error_dashboard.log"

# Chart server removed - Google Chat has image limitations

# Wait for services to fully start
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo "🔍 Checking service status..."

# Check RCA Pipeline
if [ -f "rca_pipeline.pid" ]; then
    rca_pid=$(cat rca_pipeline.pid)
    if ps -p $rca_pid > /dev/null; then
        echo "✅ RCA Pipeline: RUNNING (PID: $rca_pid)"
    else
        echo "❌ RCA Pipeline: FAILED"
    fi
else
    echo "❌ RCA Pipeline: PID file not found"
fi

# Check Streamlit Portal
if [ -f "streamlit_portal.pid" ]; then
    portal_pid=$(cat streamlit_portal.pid)
    if ps -p $portal_pid > /dev/null; then
        echo "✅ Streamlit Portal: RUNNING (PID: $portal_pid)"
    else
        echo "❌ Streamlit Portal: FAILED"
    fi
else
    echo "❌ Streamlit Portal: PID file not found"
fi

# Check Error Dashboard
if [ -f "error_dashboard.pid" ]; then
    dashboard_pid=$(cat error_dashboard.pid)
    if ps -p $dashboard_pid > /dev/null; then
        echo "✅ Error Dashboard: RUNNING (PID: $dashboard_pid)"
    else
        echo "❌ Error Dashboard: FAILED"
    fi
else
    echo "❌ Error Dashboard: PID file not found"
fi

# Test web services
echo "🌐 Testing web services..."

# Test Streamlit Portal
if curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8501 | grep -q "200"; then
    echo "✅ Streamlit Portal: HTTP 200 (Accessible)"
else
    echo "❌ Streamlit Portal: Not accessible"
fi

# Test Error Dashboard
if curl -s -o /dev/null -w "%{http_code}" http://10.1.223.229:8502 | grep -q "200"; then
    echo "✅ Error Dashboard: HTTP 200 (Accessible)"
else
    echo "❌ Error Dashboard: Not accessible"
fi

# Chart server removed - using text-only Google Chat alerts

echo ""
echo "🎯 SYSTEM STATUS:"
echo "=================="
echo "📊 RCA Pipeline: Processing 5xx errors continuously"
echo "🌐 Streamlit Portal: http://10.1.223.229:8501"
echo "📈 Error Dashboard: http://10.1.223.229:8502"
echo ""
echo "📋 Monitoring Commands:"
echo "======================="
echo "📊 Check processes: ps aux | grep -E '(rca_pipeline|streamlit)'"
echo "📋 View RCA logs: tail -f logs/rca_pipeline.log"
echo "🌐 View Portal logs: tail -f logs/streamlit_portal.log"
echo "📈 View Dashboard logs: tail -f logs/error_dashboard.log"
echo "🛑 Stop system: ./stop_system.sh"
echo ""
echo "🚀 System is now running continuously!"
echo "💡 The RCA pipeline will automatically detect and process 5xx errors"
echo "📱 Google Chat alerts will be sent for each error detected" 