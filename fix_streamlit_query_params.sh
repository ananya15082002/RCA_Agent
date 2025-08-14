#!/bin/bash

echo "🔧 Fixing Streamlit Query Params Issue..."
echo "=========================================="

# Stop all Streamlit processes
echo "🛑 Stopping all Streamlit processes..."
pkill -f "streamlit.*streamlit_portal" 2>/dev/null || true
pkill -f "streamlit.*error_dashboard" 2>/dev/null || true
pkill -f "python.*rca_pipeline" 2>/dev/null || true
sleep 3

# Clear Streamlit cache
echo "🧹 Clearing Streamlit cache..."
rm -rf ~/.streamlit/cache 2>/dev/null || true

# Navigate to RCA_Agent directory
cd ~/RCA_Agent

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Check for experimental usage
echo "🔍 Checking for deprecated experimental usage..."
if grep -r "experimental_get_query_params\|experimental_set_query_params" .; then
    echo "❌ Found deprecated experimental usage!"
    echo "📝 Replacing with st.query_params..."
    
    # Replace experimental_get_query_params with st.query_params
    find . -name "*.py" -exec sed -i 's/st\.experimental_get_query_params/st.query_params/g' {} \;
    find . -name "*.py" -exec sed -i 's/st\.experimental_set_query_params/st.query_params/g' {} \;
    
    echo "✅ Replaced deprecated API calls"
else
    echo "✅ No deprecated experimental usage found"
fi

# Verify current usage
echo "🔍 Verifying current query params usage..."
grep -r "st\.query_params" . || echo "No st.query_params usage found"

# Activate virtual environment and restart services
echo "🔄 Restarting services..."
source venv/bin/activate

# Start RCA Pipeline
echo "🔧 Starting RCA Pipeline..."
nohup python rca_pipeline.py > logs/rca_pipeline.log 2>&1 &
echo $! > rca_pipeline.pid
echo "✅ RCA Pipeline started with PID: $(cat rca_pipeline.pid)"

# Start Streamlit Portal
echo "🌐 Starting Streamlit Portal..."
nohup streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit_portal.log 2>&1 &
echo $! > streamlit_portal.pid
echo "✅ Streamlit Portal started with PID: $(cat streamlit_portal.pid)"

# Start Error Dashboard
echo "📊 Starting Error Dashboard..."
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
echo $! > error_dashboard.pid
echo "✅ Error Dashboard started with PID: $(cat error_dashboard.pid)"

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo "🔍 Checking service status..."
if [ -f "rca_pipeline.pid" ] && ps -p $(cat rca_pipeline.pid) > /dev/null; then
    echo "✅ RCA Pipeline: RUNNING"
else
    echo "❌ RCA Pipeline: FAILED"
fi

if [ -f "streamlit_portal.pid" ] && ps -p $(cat streamlit_portal.pid) > /dev/null; then
    echo "✅ Streamlit Portal: RUNNING"
else
    echo "❌ Streamlit Portal: FAILED"
fi

if [ -f "error_dashboard.pid" ] && ps -p $(cat error_dashboard.pid) > /dev/null; then
    echo "✅ Error Dashboard: RUNNING"
else
    echo "❌ Error Dashboard: FAILED"
fi

echo ""
echo "🎯 Services Updated:"
echo "==================="
echo "🌐 RCA Portal: http://3.7.67.210:8501"
echo "📈 Error Dashboard: http://3.7.67.210:8502"
echo ""
echo "✅ Streamlit query params issue should be resolved!"
echo "💡 Try accessing: http://3.7.67.210:8501/?error_dir=error_1_2025-08-14_102900_IST" 