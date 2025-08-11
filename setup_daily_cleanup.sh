#!/bin/bash

# Setup Daily Cleanup Cron Job for Error RCA System
# This script sets up automatic cleanup every 24 hours

echo "🕐 Setting up daily cleanup cron job for Error RCA System..."
echo "=========================================================="

# Get the absolute path to the cleanup script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup_old_data.sh"

# Check if cleanup script exists
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "❌ ERROR: Cleanup script not found at $CLEANUP_SCRIPT"
    exit 1
fi

echo "📁 Cleanup script location: $CLEANUP_SCRIPT"

# Create a wrapper script that changes to the correct directory
WRAPPER_SCRIPT="$SCRIPT_DIR/run_cleanup_wrapper.sh"

cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Wrapper script to run cleanup from the correct directory
cd "$SCRIPT_DIR"
export PATH="/usr/local/bin:/usr/bin:/bin:\$PATH"
export HOME="\$HOME"
export USER="\$USER"
export SHELL="/bin/bash"

# Run the cleanup script
"$CLEANUP_SCRIPT" >> "$SCRIPT_DIR/logs/cleanup.log" 2>&1
EOF

chmod +x "$WRAPPER_SCRIPT"

echo "📝 Created wrapper script: $WRAPPER_SCRIPT"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if cron job already exists
EXISTING_CRON=$(crontab -l 2>/dev/null | grep "run_cleanup_wrapper.sh")

if [ -n "$EXISTING_CRON" ]; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "run_cleanup_wrapper.sh" | crontab -
fi

# Add new cron job to run every day at 2:00 AM
(crontab -l 2>/dev/null; echo "0 2 * * * $WRAPPER_SCRIPT") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 Cron Job Details:"
echo "==================="
echo "⏰ Schedule: Every day at 2:00 AM"
echo "📁 Script: $WRAPPER_SCRIPT"
echo "📝 Logs: $SCRIPT_DIR/logs/cleanup.log"
echo ""

# Show current crontab
echo "🔍 Current crontab entries:"
echo "=========================="
crontab -l 2>/dev/null | grep -E "(run_cleanup|cleanup)" || echo "No cleanup cron jobs found"

echo ""
echo "🎯 Setup Complete!"
echo "=================="
echo "✅ Daily cleanup will run automatically at 2:00 AM every day"
echo "✅ Old error reports will be cleaned up (keeping last 100)"
echo "✅ Log files older than 7 days will be removed"
echo "✅ Portal and dashboard will be refreshed after cleanup"
echo ""
echo "📋 Manual Commands:"
echo "=================="
echo "🔄 Run cleanup now: ./cleanup_old_data.sh"
echo "📊 Check cleanup logs: tail -f logs/cleanup.log"
echo "🗑️ Remove cron job: crontab -e (then delete the line)"
echo "📋 View cron jobs: crontab -l"
echo ""
echo "💡 The system will now automatically maintain itself!" 