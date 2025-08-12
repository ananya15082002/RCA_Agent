#!/bin/bash

# RCA Agent Automated Storage Cleanup Script
# This script runs daily to prevent storage issues

echo "🧹 RCA Agent Automated Storage Cleanup"
echo "======================================"
echo "📅 Date: $(date)"
echo ""

# Change to RCA Agent directory
cd /home/ec2-user/RCA_Agent

# Check current storage status
echo "📊 Current Storage Status:"
echo "-------------------------"
df -h /
echo ""

# Run storage manager report
echo "📋 Storage Report:"
echo "-----------------"
python3 storage_manager.py --report
echo ""

# Check if cleanup is needed
echo "🔍 Checking if cleanup is needed..."
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
    
    echo "⚠️  Cleanup is needed. Running cleanup process..."
    echo ""
    
    # Run cleanup
    python3 storage_manager.py --cleanup
    
    echo ""
    echo "✅ Cleanup completed!"
    echo ""
    
    # Show final status
    echo "📊 Final Storage Status:"
    echo "----------------------"
    df -h /
    echo ""
    
    # Send notification if significant space was freed
    CLEANED_SIZE=$(python3 -c "
import sys
sys.path.append('.')
from storage_manager import StorageManager
manager = StorageManager()
result = manager.run_cleanup()
print(result['total_cleaned_gb'])
" 2>/dev/null)
    
    if [ ! -z "$CLEANED_SIZE" ] && [ "$CLEANED_SIZE" != "0.0" ]; then
        echo "📢 Significant cleanup performed: ${CLEANED_SIZE}GB freed"
    fi
    
else
    echo "✅ No cleanup needed. Storage is healthy."
fi

echo ""
echo "🏁 Cleanup check completed at $(date)" 