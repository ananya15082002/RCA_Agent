#!/bin/bash

echo "🚀 SETTING UP AUTO START FOR ERROR DASHBOARD"
echo "============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Navigate to RCA_Agent directory
cd /home/ec2-user/RCA_Agent || {
    echo "❌ Failed to navigate to RCA_Agent directory"
    exit 1
}

echo ""
echo "📁 Current directory: $(pwd)"

# Make scripts executable
chmod +x auto_start_dashboard.sh
chmod +x restart_dashboard.sh

# Copy service file to systemd directory
echo "Installing systemd service..."
cp error-dashboard.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable error-dashboard.service

# Start the service
echo "Starting error dashboard service..."
systemctl start error-dashboard.service

# Wait a moment
sleep 5

# Check service status
echo ""
echo "🔍 SERVICE STATUS"
echo "-----------------"
systemctl status error-dashboard.service --no-pager

# Check if port is listening
echo ""
echo "🔍 PORT STATUS"
echo "--------------"
if netstat -tlnp 2>/dev/null | grep -q ":8502 "; then
    echo "✅ Error Dashboard is listening on port 8502"
else
    echo "❌ Error Dashboard is not listening on port 8502"
fi

# Show recent logs
echo ""
echo "📋 RECENT LOGS"
echo "--------------"
tail -10 logs/error_dashboard.log 2>/dev/null || echo "No log file found"

echo ""
echo "🌐 ACCESS URLs"
echo "-------------"
echo "📊 Error Dashboard: http://3.7.67.210:8502"
echo "🔍 RCA Portal: http://3.7.67.210:8501"

echo ""
echo "🔧 USEFUL COMMANDS"
echo "------------------"
echo "Check status: sudo systemctl status error-dashboard"
echo "Start service: sudo systemctl start error-dashboard"
echo "Stop service: sudo systemctl stop error-dashboard"
echo "Restart service: sudo systemctl restart error-dashboard"
echo "View logs: sudo journalctl -u error-dashboard -f"

echo ""
echo "✨ AUTO START SETUP COMPLETE"
echo "============================" 