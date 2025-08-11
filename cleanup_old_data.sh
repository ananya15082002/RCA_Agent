#!/bin/bash

# Data Cleanup Script for Error RCA System
# This script runs every 24 hours to clean up old error data and refresh the portal

echo "🧹 Starting daily data cleanup for Error RCA System..."
echo "=================================================="

# Get current timestamp
CLEANUP_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "🕐 Cleanup started at: $CLEANUP_TIME"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if we're in the right directory
if [ ! -f "rca_pipeline.py" ]; then
    log_message "❌ ERROR: Not in the correct directory. Please run from the 5xx directory."
    exit 1
fi

# 1. Stop the RCA pipeline temporarily to prevent new data generation during cleanup
log_message "🛑 Temporarily stopping RCA pipeline for cleanup..."
pkill -f "python rca_pipeline.py" 2>/dev/null
sleep 3

# 2. Count current error reports before cleanup
OLD_COUNT=$(find error_outputs/ -maxdepth 1 -type d -name "error_*" | wc -l)
log_message "📊 Found $OLD_COUNT error reports before cleanup"

# 3. Keep only the last 100 error reports (most recent)
log_message "🗑️ Removing old error reports (keeping last 100)..."
cd error_outputs/

# Get list of all error directories sorted by modification time (newest first)
ERROR_DIRS=$(find . -maxdepth 1 -type d -name "error_*" -printf '%T@ %p\n' | sort -nr | cut -d' ' -f2-)

# Count total directories
TOTAL_DIRS=$(echo "$ERROR_DIRS" | wc -l)

if [ "$TOTAL_DIRS" -gt 100 ]; then
    # Keep only the first 100 (most recent) directories
    KEEP_DIRS=$(echo "$ERROR_DIRS" | head -100)
    REMOVE_DIRS=$(echo "$ERROR_DIRS" | tail -n +101)
    
    # Remove old directories
    for dir in $REMOVE_DIRS; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log_message "🗑️ Removed: $dir"
        fi
    done
    
    REMOVED_COUNT=$((TOTAL_DIRS - 100))
    log_message "✅ Removed $REMOVED_COUNT old error reports"
else
    log_message "ℹ️ No cleanup needed - only $TOTAL_DIRS error reports found (under 100 limit)"
fi

cd ..

# 4. Clean up old log files (keep last 7 days)
log_message "📝 Cleaning up old log files..."
find logs/ -name "*.log" -type f -mtime +7 -delete 2>/dev/null
log_message "✅ Cleaned up log files older than 7 days"

# 5. Clean up any temporary files
log_message "🧹 Cleaning up temporary files..."
rm -f *.pid 2>/dev/null
rm -f __pycache__/*.pyc 2>/dev/null
log_message "✅ Cleaned up temporary files"

# 6. Count error reports after cleanup
NEW_COUNT=$(find error_outputs/ -maxdepth 1 -type d -name "error_*" | wc -l)
log_message "📊 Error reports after cleanup: $NEW_COUNT"

# 7. Restart the RCA pipeline
log_message "🔄 Restarting RCA pipeline..."
source venv/bin/activate
nohup python rca_pipeline.py > logs/rca_pipeline.log 2>&1 &
sleep 3

# 8. Verify pipeline is running
if pgrep -f "python rca_pipeline.py" > /dev/null; then
    PIPELINE_PID=$(pgrep -f "python rca_pipeline.py")
    log_message "✅ RCA Pipeline restarted successfully (PID: $PIPELINE_PID)"
else
    log_message "❌ ERROR: Failed to restart RCA pipeline"
fi

# 9. Restart Streamlit portal to refresh data
log_message "🌐 Restarting Streamlit portal to refresh data..."
pkill -f "streamlit run streamlit_portal.py" 2>/dev/null
sleep 3
nohup streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit_portal.log 2>&1 &
sleep 5

# 10. Restart Error Dashboard
log_message "📊 Restarting Error Dashboard..."
pkill -f "streamlit run error_dashboard.py" 2>/dev/null
sleep 3
nohup streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0 > logs/error_dashboard.log 2>&1 &
sleep 5

# 11. Final status check
log_message "🔍 Performing final status check..."
sleep 10

echo ""
echo "🎯 CLEANUP SUMMARY:"
echo "=================="
echo "📊 Error reports before: $OLD_COUNT"
echo "📊 Error reports after: $NEW_COUNT"
echo "🗑️ Reports removed: $((OLD_COUNT - NEW_COUNT))"
echo "🕐 Cleanup completed at: $(date '+%Y-%m-%d %H:%M:%S')"

# Check if all services are running
echo ""
echo "🔍 SERVICE STATUS:"
echo "=================="
if pgrep -f "python rca_pipeline.py" > /dev/null; then
    echo "✅ RCA Pipeline: RUNNING"
else
    echo "❌ RCA Pipeline: NOT RUNNING"
fi

if pgrep -f "streamlit run streamlit_portal.py" > /dev/null; then
    echo "✅ Streamlit Portal: RUNNING"
else
    echo "❌ Streamlit Portal: NOT RUNNING"
fi

if pgrep -f "streamlit run error_dashboard.py" > /dev/null; then
    echo "✅ Error Dashboard: RUNNING"
else
    echo "❌ Error Dashboard: NOT RUNNING"
fi

echo ""
echo "🌐 Access URLs:"
echo "   Portal: http://localhost:8501"
echo "   Dashboard: http://localhost:8502"
echo "   Network: http://10.45.249.4:8501 (Portal)"
echo "   Network: http://10.45.249.4:8502 (Dashboard)"

log_message "🎉 Daily cleanup completed successfully!"
echo ""
echo "💡 Next cleanup will run in 24 hours"
echo "📋 To run cleanup manually: ./cleanup_old_data.sh" 