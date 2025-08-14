#!/bin/bash

echo "🚀 AUTO STARTING ERROR DASHBOARD"
echo "=================================="

# Function to check if a process is running
check_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "✅ $process_name is running (PID: $pid)"
            return 0
        else
            echo "❌ $process_name is not running (stale PID file)"
            return 1
        fi
    else
        echo "❌ $process_name is not running (no PID file)"
        return 1
    fi
}

# Function to check if a port is listening
check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "✅ $service_name is listening on port $port"
        return 0
    else
        echo "❌ $service_name is not listening on port $port"
        return 1
    fi
}

# Navigate to RCA_Agent directory
cd ~/RCA_Agent || {
    echo "❌ Failed to navigate to RCA_Agent directory"
    exit 1
}

echo ""
echo "📁 Current directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please set up the environment first."
    exit 1
fi

# Check if error_dashboard.py exists
if [ ! -f "error_dashboard.py" ]; then
    echo "❌ error_dashboard.py not found"
    exit 1
fi

echo ""
echo "🔍 CHECKING CURRENT STATUS"
echo "---------------------------"

# Check current processes
check_process "error_dashboard.pid" "Error Dashboard"
check_process "streamlit_portal.pid" "Streamlit Portal"
check_process "rca_pipeline.pid" "RCA Pipeline"

echo ""
# Check current ports
check_port "8502" "Error Dashboard"
check_port "8501" "Streamlit Portal"

echo ""
echo "🔄 RESTARTING ERROR DASHBOARD"
echo "-----------------------------"

# Kill any existing error dashboard processes
echo "Stopping existing error dashboard processes..."
pkill -f error_dashboard.py
sleep 3

# Clear any stale PID files
if [ -f "error_dashboard.pid" ]; then
    rm -f error_dashboard.pid
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Test import
echo "Testing error_dashboard.py import..."
python3 -c "import error_dashboard; print('✅ Import successful')" 2>&1 || {
    echo "❌ Import failed. Check the error above."
    exit 1
}

# Start error dashboard
echo "Starting error dashboard..."
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
echo $! > error_dashboard.pid

echo "✅ Error Dashboard started with PID: $(cat error_dashboard.pid)"

# Wait for startup
echo "Waiting for startup..."
sleep 10

echo ""
echo "🔍 FINAL STATUS CHECK"
echo "--------------------"

# Check if process is running
check_process "error_dashboard.pid" "Error Dashboard"

# Check if port is listening
check_port "8502" "Error Dashboard"

# Show recent logs
echo ""
echo "📋 RECENT LOGS"
echo "--------------"
tail -5 logs/error_dashboard.log 2>/dev/null || echo "No log file found"

echo ""
echo "🌐 ACCESS URLs"
echo "-------------"
echo "📊 Error Dashboard: http://3.7.67.210:8502"
echo "🔍 RCA Portal: http://3.7.67.210:8501"

echo ""
echo "✨ AUTO START COMPLETE"
echo "======================" 