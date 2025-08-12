#!/usr/bin/env python3
"""
RCA Agent Storage Management System
Manages disk space to prevent system failures due to storage issues
"""

import os
import shutil
import glob
import time
import subprocess
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('storage_manager.log'),
        logging.StreamHandler()
    ]
)

class StorageManager:
    def __init__(self):
        self.error_outputs_dir = "error_outputs"
        self.logs_dir = "logs"
        self.max_error_outputs_size_gb = 2.0  # 2GB max for error outputs
        self.max_logs_size_gb = 0.5  # 500MB max for logs
        self.retention_days = 7  # Keep error reports for 7 days
        self.critical_threshold = 85  # Alert when disk usage > 85%
        self.warning_threshold = 70   # Warning when disk usage > 70%
        
    def get_disk_usage(self):
        """Get current disk usage percentage"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    usage_str = parts[4].replace('%', '')
                    return float(usage_str)
        except Exception as e:
            logging.error(f"Error getting disk usage: {e}")
        return 0
    
    def get_directory_size_gb(self, directory):
        """Get directory size in GB"""
        try:
            if not os.path.exists(directory):
                return 0
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            return total_size / (1024**3)  # Convert to GB
        except Exception as e:
            logging.error(f"Error calculating directory size for {directory}: {e}")
            return 0
    
    def get_old_error_reports(self, days_old):
        """Get error reports older than specified days"""
        old_reports = []
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            if os.path.exists(self.error_outputs_dir):
                for item in os.listdir(self.error_outputs_dir):
                    item_path = os.path.join(self.error_outputs_dir, item)
                    if os.path.isdir(item_path):
                        if os.path.getmtime(item_path) < cutoff_time:
                            old_reports.append(item_path)
        except Exception as e:
            logging.error(f"Error finding old error reports: {e}")
        
        return old_reports
    
    def cleanup_old_error_reports(self):
        """Remove error reports older than retention period"""
        old_reports = self.get_old_error_reports(self.retention_days)
        cleaned_size = 0
        
        for report_path in old_reports:
            try:
                size = self.get_directory_size_gb(report_path) * (1024**3)  # Convert back to bytes
                shutil.rmtree(report_path)
                cleaned_size += size
                logging.info(f"Removed old error report: {os.path.basename(report_path)}")
            except Exception as e:
                logging.error(f"Error removing {report_path}: {e}")
        
        return cleaned_size / (1024**3)  # Return cleaned size in GB
    
    def cleanup_large_error_reports(self, max_size_gb):
        """Remove largest error reports to stay under size limit"""
        current_size = self.get_directory_size_gb(self.error_outputs_dir)
        
        if current_size <= max_size_gb:
            return 0
        
        # Get all error reports with their sizes
        reports_with_sizes = []
        try:
            if os.path.exists(self.error_outputs_dir):
                for item in os.listdir(self.error_outputs_dir):
                    item_path = os.path.join(self.error_outputs_dir, item)
                    if os.path.isdir(item_path):
                        size = self.get_directory_size_gb(item_path)
                        reports_with_sizes.append((item_path, size))
        except Exception as e:
            logging.error(f"Error scanning error reports: {e}")
            return 0
        
        # Sort by size (largest first)
        reports_with_sizes.sort(key=lambda x: x[1], reverse=True)
        
        cleaned_size = 0
        for report_path, size in reports_with_sizes:
            if self.get_directory_size_gb(self.error_outputs_dir) <= max_size_gb:
                break
            
            try:
                shutil.rmtree(report_path)
                cleaned_size += size
                logging.info(f"Removed large error report: {os.path.basename(report_path)} ({size:.2f}GB)")
            except Exception as e:
                logging.error(f"Error removing {report_path}: {e}")
        
        return cleaned_size
    
    def cleanup_logs(self):
        """Clean up old log files"""
        cleaned_size = 0
        
        try:
            if os.path.exists(self.logs_dir):
                # Remove log files older than 3 days
                cutoff_time = time.time() - (3 * 24 * 60 * 60)
                
                for log_file in os.listdir(self.logs_dir):
                    log_path = os.path.join(self.logs_dir, log_file)
                    if os.path.isfile(log_path):
                        if os.path.getmtime(log_path) < cutoff_time:
                            size = os.path.getsize(log_path)
                            os.remove(log_path)
                            cleaned_size += size
                            logging.info(f"Removed old log file: {log_file}")
                
                # If logs are still too large, remove largest files
                current_logs_size = self.get_directory_size_gb(self.logs_dir)
                if current_logs_size > self.max_logs_size_gb:
                    log_files = []
                    for log_file in os.listdir(self.logs_dir):
                        log_path = os.path.join(self.logs_dir, log_file)
                        if os.path.isfile(log_path):
                            size = os.path.getsize(log_path)
                            log_files.append((log_path, size))
                    
                    log_files.sort(key=lambda x: x[1], reverse=True)
                    
                    for log_path, size in log_files:
                        if self.get_directory_size_gb(self.logs_dir) <= self.max_logs_size_gb:
                            break
                        
                        os.remove(log_path)
                        cleaned_size += size
                        logging.info(f"Removed large log file: {os.path.basename(log_path)}")
        except Exception as e:
            logging.error(f"Error cleaning logs: {e}")
        
        return cleaned_size / (1024**3)  # Return cleaned size in GB
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        cleaned_size = 0
        
        # Clean up Python cache files
        for root, dirs, files in os.walk('.'):
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    cache_dir = os.path.join(root, dir_name)
                    try:
                        size = sum(os.path.getsize(os.path.join(cache_dir, f)) 
                                 for f in os.listdir(cache_dir) 
                                 if os.path.isfile(os.path.join(cache_dir, f)))
                        shutil.rmtree(cache_dir)
                        cleaned_size += size
                        logging.info(f"Removed cache directory: {cache_dir}")
                    except Exception as e:
                        logging.error(f"Error removing cache directory {cache_dir}: {e}")
        
        return cleaned_size / (1024**3)  # Return cleaned size in GB
    
    def get_storage_report(self):
        """Generate comprehensive storage report"""
        disk_usage = self.get_disk_usage()
        error_outputs_size = self.get_directory_size_gb(self.error_outputs_dir)
        logs_size = self.get_directory_size_gb(self.logs_dir)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'disk_usage_percent': disk_usage,
            'error_outputs_size_gb': error_outputs_size,
            'logs_size_gb': logs_size,
            'total_error_reports': len(os.listdir(self.error_outputs_dir)) if os.path.exists(self.error_outputs_dir) else 0,
            'old_error_reports': len(self.get_old_error_reports(self.retention_days)),
            'status': 'OK'
        }
        
        if disk_usage > self.critical_threshold:
            report['status'] = 'CRITICAL'
        elif disk_usage > self.warning_threshold:
            report['status'] = 'WARNING'
        
        return report
    
    def run_cleanup(self, force=False):
        """Run complete cleanup process"""
        logging.info("Starting storage cleanup process...")
        
        # Get initial state
        initial_disk_usage = self.get_disk_usage()
        initial_error_size = self.get_directory_size_gb(self.error_outputs_dir)
        initial_logs_size = self.get_directory_size_gb(self.logs_dir)
        
        total_cleaned = 0
        
        # Clean up old error reports
        cleaned_old = self.cleanup_old_error_reports()
        total_cleaned += cleaned_old
        logging.info(f"Cleaned {cleaned_old:.2f}GB from old error reports")
        
        # Clean up large error reports if needed
        if force or self.get_directory_size_gb(self.error_outputs_dir) > self.max_error_outputs_size_gb:
            cleaned_large = self.cleanup_large_error_reports(self.max_error_outputs_size_gb)
            total_cleaned += cleaned_large
            logging.info(f"Cleaned {cleaned_large:.2f}GB from large error reports")
        
        # Clean up logs
        cleaned_logs = self.cleanup_logs()
        total_cleaned += cleaned_logs
        logging.info(f"Cleaned {cleaned_logs:.2f}GB from logs")
        
        # Clean up temp files
        cleaned_temp = self.cleanup_temp_files()
        total_cleaned += cleaned_temp
        logging.info(f"Cleaned {cleaned_temp:.2f}GB from temp files")
        
        # Final state
        final_disk_usage = self.get_disk_usage()
        final_error_size = self.get_directory_size_gb(self.error_outputs_dir)
        final_logs_size = self.get_directory_size_gb(self.logs_dir)
        
        logging.info(f"Cleanup completed. Total cleaned: {total_cleaned:.2f}GB")
        logging.info(f"Disk usage: {initial_disk_usage:.1f}% -> {final_disk_usage:.1f}%")
        logging.info(f"Error outputs: {initial_error_size:.2f}GB -> {final_error_size:.2f}GB")
        logging.info(f"Logs: {initial_logs_size:.2f}GB -> {final_logs_size:.2f}GB")
        
        return {
            'total_cleaned_gb': total_cleaned,
            'disk_usage_before': initial_disk_usage,
            'disk_usage_after': final_disk_usage,
            'error_size_before': initial_error_size,
            'error_size_after': final_error_size
        }
    
    def should_cleanup(self):
        """Check if cleanup is needed"""
        disk_usage = self.get_disk_usage()
        error_size = self.get_directory_size_gb(self.error_outputs_dir)
        
        return (disk_usage > self.warning_threshold or 
                error_size > self.max_error_outputs_size_gb)

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RCA Agent Storage Manager')
    parser.add_argument('--report', action='store_true', help='Generate storage report')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup process')
    parser.add_argument('--force', action='store_true', help='Force cleanup even if not needed')
    parser.add_argument('--monitor', action='store_true', help='Monitor storage continuously')
    
    args = parser.parse_args()
    
    manager = StorageManager()
    
    if args.report:
        report = manager.get_storage_report()
        print(json.dumps(report, indent=2))
    
    elif args.cleanup:
        result = manager.run_cleanup(force=args.force)
        print(json.dumps(result, indent=2))
    
    elif args.monitor:
        print("Starting storage monitoring...")
        while True:
            if manager.should_cleanup():
                print(f"Storage cleanup needed. Running cleanup...")
                result = manager.run_cleanup()
                print(f"Cleanup completed: {result['total_cleaned_gb']:.2f}GB cleaned")
            else:
                print("Storage status: OK")
            
            time.sleep(3600)  # Check every hour
    
    else:
        # Default: show report
        report = manager.get_storage_report()
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main() 