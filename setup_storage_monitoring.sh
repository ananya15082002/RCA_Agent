#!/bin/bash

# RCA Agent Storage Monitoring Setup Script
# This script sets up automated storage monitoring and cleanup

echo "🔧 Setting up RCA Agent Storage Monitoring"
echo "=========================================="
echo ""

# Make scripts executable
chmod +x storage_manager.py
chmod +x automated_cleanup.sh
chmod +x cleanup_old_data.sh

echo "✅ Made scripts executable"
echo ""

# Create cron job for daily cleanup
echo "📅 Setting up daily cleanup cron job..."
CRON_JOB="0 2 * * * /home/ec2-user/RCA_Agent/automated_cleanup.sh >> /home/ec2-user/RCA_Agent/logs/cleanup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "automated_cleanup.sh"; then
    echo "ℹ️  Cron job already exists"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Added daily cleanup cron job (runs at 2 AM daily)"
fi

echo ""

# Create hourly monitoring script
echo "⏰ Setting up hourly storage monitoring..."
MONITOR_SCRIPT="/home/ec2-user/RCA_Agent/monitor_storage.sh"

cat > "$MONITOR_SCRIPT" << 'EOF'
#!/bin/bash

# Hourly storage monitoring script
cd /home/ec2-user/RCA_Agent

# Check if cleanup is needed
if python3 -c "
import sys
sys.path.append('.')
from storage_manager import StorageManager
manager = StorageManager()
if manager.should_cleanup():
    print('CLEANUP_NEEDED')
else:
    print('CLEANUP_NOT_NEEDED')
" | grep -q "CLEANUP_NEEDED"; then
    
    echo "[$(date)] Storage cleanup needed. Running cleanup..." >> logs/storage_monitor.log
    python3 storage_manager.py --cleanup >> logs/storage_monitor.log 2>&1
else
    echo "[$(date)] Storage status: OK" >> logs/storage_monitor.log
fi
EOF

chmod +x "$MONITOR_SCRIPT"

# Add hourly monitoring cron job
MONITOR_CRON="0 * * * * $MONITOR_SCRIPT"
if crontab -l 2>/dev/null | grep -q "monitor_storage.sh"; then
    echo "ℹ️  Monitoring cron job already exists"
else
    (crontab -l 2>/dev/null; echo "$MONITOR_CRON") | crontab -
    echo "✅ Added hourly monitoring cron job"
fi

echo ""

# Create storage alert script
echo "🚨 Setting up storage alerts..."
ALERT_SCRIPT="/home/ec2-user/RCA_Agent/storage_alert.sh"

cat > "$ALERT_SCRIPT" << 'EOF'
#!/bin/bash

# Storage alert script
cd /home/ec2-user/RCA_Agent

# Get storage report
REPORT=$(python3 storage_manager.py --report 2>/dev/null)

# Check if disk usage is critical
DISK_USAGE=$(echo "$REPORT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('disk_usage_percent', 0))
")

if [ "$DISK_USAGE" -gt 85 ]; then
    echo "[$(date)] CRITICAL: Disk usage is ${DISK_USAGE}%" >> logs/storage_alerts.log
    echo "🚨 CRITICAL: Disk usage is ${DISK_USAGE}%" >> logs/storage_alerts.log
elif [ "$DISK_USAGE" -gt 70 ]; then
    echo "[$(date)] WARNING: Disk usage is ${DISK_USAGE}%" >> logs/storage_alerts.log
    echo "⚠️  WARNING: Disk usage is ${DISK_USAGE}%" >> logs/storage_alerts.log
fi
EOF

chmod +x "$ALERT_SCRIPT"

# Add alert cron job (every 30 minutes)
ALERT_CRON="*/30 * * * * $ALERT_SCRIPT"
if crontab -l 2>/dev/null | grep -q "storage_alert.sh"; then
    echo "ℹ️  Alert cron job already exists"
else
    (crontab -l 2>/dev/null; echo "$ALERT_CRON") | crontab -
    echo "✅ Added storage alert cron job (every 30 minutes)"
fi

echo ""

# Show current cron jobs
echo "📋 Current cron jobs:"
echo "-------------------"
crontab -l 2>/dev/null | grep -E "(cleanup|monitor|alert)" || echo "No cron jobs found"

echo ""

# Test storage manager
echo "🧪 Testing storage manager..."
python3 storage_manager.py --report

echo ""

# Create storage management guide
echo "📖 Creating storage management guide..."
cat > "STORAGE_MANAGEMENT.md" << 'EOF'
# 🗄️ RCA Agent Storage Management

## 📊 Storage Limits
- **Error Outputs**: Max 2GB
- **Logs**: Max 500MB
- **Retention**: 7 days for error reports, 3 days for logs
- **Warning Threshold**: 70% disk usage
- **Critical Threshold**: 85% disk usage

## 🔧 Manual Commands

### Check Storage Status
```bash
python3 storage_manager.py --report
```

### Run Cleanup
```bash
python3 storage_manager.py --cleanup
```

### Force Cleanup
```bash
python3 storage_manager.py --cleanup --force
```

### Monitor Continuously
```bash
python3 storage_manager.py --monitor
```

## ⏰ Automated Tasks

### Daily Cleanup (2 AM)
- Removes old error reports (>7 days)
- Cleans up old logs (>3 days)
- Removes temp files

### Hourly Monitoring
- Checks if cleanup is needed
- Runs cleanup automatically if required

### Storage Alerts (Every 30 minutes)
- Monitors disk usage
- Logs warnings and critical alerts

## 📁 Storage Structure
```
RCA_Agent/
├── error_outputs/     # Error reports (max 2GB)
├── logs/             # Application logs (max 500MB)
├── venv/             # Python virtual environment
└── storage_manager.py # Storage management system
```

## 🚨 Troubleshooting

### If System Stops Due to Storage
1. Run immediate cleanup: `python3 storage_manager.py --cleanup --force`
2. Check storage status: `python3 storage_manager.py --report`
3. Restart system: `./start_system.sh`

### Manual Cleanup
```bash
# Remove old error reports
find error_outputs/ -type d -name "error_*" -mtime +7 -exec rm -rf {} \;

# Remove old logs
find logs/ -type f -name "*.log" -mtime +3 -delete

# Clean temp files
find . -type d -name "__pycache__" -exec rm -rf {} \;
```

## 📞 Support
- Check logs: `tail -f logs/storage_monitor.log`
- Check alerts: `tail -f logs/storage_alerts.log`
- Check cleanup: `tail -f logs/cleanup.log`
EOF

echo "✅ Created storage management guide"

echo ""
echo "🎉 Storage monitoring setup completed!"
echo ""
echo "📋 Summary:"
echo "✅ Daily cleanup at 2 AM"
echo "✅ Hourly monitoring"
echo "✅ Storage alerts every 30 minutes"
echo "✅ Storage management guide created"
echo ""
echo "📖 View guide: cat STORAGE_MANAGEMENT.md"
echo "📊 Check status: python3 storage_manager.py --report"
echo "🧹 Manual cleanup: python3 storage_manager.py --cleanup" 