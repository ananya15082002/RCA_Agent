# 🚀 Quick Deployment Guide - RCA Agent System

## 📋 Overview
This guide helps you quickly deploy and manage the 5xx RCA Agent system on AWS with the new Elastic IP `3.7.67.210`.

## 🔧 Prerequisites
- AWS CLI installed and configured
- SSH access to the EC2 instance
- VPN access for secure connections

## 🚀 Quick Start

### 1. Start the Instance
```bash
# Use the AWS Instance Manager script
./aws_instance_manager.sh

# Or use AWS CLI directly
aws ec2 start-instances --instance-ids i-04ad00584d6bd3a89 --region ap-south-1
```

### 2. SSH into the Instance
```bash
ssh ec2-user@3.7.67.210
```

### 3. Navigate to RCA Agent Directory
```bash
cd RCA_Agent
```

### 4. Start the System
```bash
# Start all services
./start_system.sh

# Check status
./status_streamlit.sh
```

## 🌐 Access URLs

### RCA Portal
- **URL**: http://3.7.67.210:8501
- **Purpose**: Main RCA portal for error analysis
- **Access**: Requires VPN connection

### Error Dashboard
- **URL**: http://3.7.67.210:8502
- **Purpose**: Real-time error monitoring dashboard
- **Access**: Requires VPN connection

### SSH Access
- **Command**: `ssh ec2-user@3.7.67.210`
- **Purpose**: Administrative access

## 🔒 Security Configuration

### Security Group Rules
Based on your configuration, the following ports are open:
- **Port 22**: SSH access
- **Port 80**: HTTP access
- **Port 443**: HTTPS access
- **Port 8501**: RCA Portal
- **Port 8502**: Error Dashboard

### VPN Access
- All web access requires VPN connection
- IP ranges configured for corporate VPN
- Secure access to error data

## 📊 Monitoring Commands

### Check System Status
```bash
./status_streamlit.sh
```

### View Logs
```bash
# RCA Pipeline logs
tail -f logs/rca_pipeline.log

# Streamlit Portal logs
tail -f logs/streamlit_portal.log

# Error Dashboard logs
tail -f logs/error_dashboard.log
```

### Monitor System Health
```bash
./monitor_system.sh
```

## 🛠️ Management Commands

### Start System
```bash
./start_system.sh
```

### Stop System
```bash
./stop_system.sh
```

### Restart System
```bash
./stop_system.sh
sleep 5
./start_system.sh
```

### Clean Old Data
```bash
./cleanup_old_data.sh
```

## 🔍 Troubleshooting

### Instance Not Starting
1. Check AWS Console for instance status
2. Verify security group rules
3. Check instance logs in AWS Console

### Services Not Accessible
1. Verify instance is running
2. Check if services are started: `./status_streamlit.sh`
3. Check firewall rules
4. Verify VPN connection

### Port Access Issues
1. Check security group inbound rules
2. Verify VPN IP ranges are whitelisted
3. Test connectivity: `curl -I http://3.7.67.210:8501`

## 📈 System Health Checks

### Automated Health Check
```bash
./aws_instance_manager.sh
# Select option 4: Check system health
```

### Manual Health Check
```bash
# Check if instance is running
aws ec2 describe-instances --instance-ids i-04ad00584d6bd3a89 --region ap-south-1

# Check service accessibility
curl -I http://3.7.67.210:8501
curl -I http://3.7.67.210:8502
```

## 🚨 Emergency Procedures

### System Down
1. Check instance status: `./aws_instance_manager.sh`
2. Start instance if stopped
3. SSH into instance and restart services
4. Check logs for errors

### Data Issues
1. Check error_outputs directory
2. Verify last_processed_epoch.txt
3. Restart RCA pipeline if needed

### Performance Issues
1. Check system resources: `htop`
2. Clean old data: `./cleanup_old_data.sh`
3. Restart services if needed

## 📞 Support Information

### System Details
- **Instance ID**: i-04ad00584d6bd3a89
- **Elastic IP**: 3.7.67.210
- **Region**: ap-south-1
- **OS**: Amazon Linux

### Contact
For issues or questions, contact the system administrator.

---

**Last Updated**: 2025-01-27  
**Version**: RCA Agent v2.0 with Elastic IP 3.7.67.210 