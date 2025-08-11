# 🚀 AWS Terminal Deployment Guide for 5xx RCA System

This guide provides step-by-step instructions to deploy your 5xx Error RCA System on AWS EC2 using the AWS terminal.

## 📋 Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **SSH key pair** created in AWS
3. **Security group** with proper rules
4. **VPC and subnet** configured

## 🏗️ Step 1: Create AWS Infrastructure

### 1.1 Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
    --group-name 5xx-rca-security-group \
    --description "Security group for 5xx RCA System"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
    --group-names 5xx-rca-security-group \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

echo "Security Group ID: $SG_ID"
```

### 1.2 Add Security Group Rules

```bash
# Allow SSH access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Allow HTTP access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow HTTPS access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow Streamlit Portal access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8501 \
    --cidr 0.0.0.0/0

# Allow Error Dashboard access
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 8502 \
    --cidr 0.0.0.0/0
```

### 1.3 Get VPC and Subnet Information

```bash
# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text)

echo "VPC ID: $VPC_ID"

# Get default subnet ID
SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[0].SubnetId' \
    --output text)

echo "Subnet ID: $SUBNET_ID"
```

### 1.4 Create EC2 Instance

```bash
# Launch EC2 instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair-name \
    --security-group-ids $SG_ID \
    --subnet-id $SUBNET_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=5xx-RCA-System}]' \
    --user-data '#!/bin/bash
sudo apt update
sudo apt install -y git curl wget
cd /home/ubuntu
git clone https://github.com/ananya15082002/RCA_Agent.git
cd RCA_Agent
chmod +x deploy.sh
./deploy.sh'

# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=5xx-RCA-System" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

echo "Instance ID: $INSTANCE_ID"
```

### 1.5 Allocate Elastic IP (Optional but Recommended)

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Get allocation ID
ALLOCATION_ID=$(aws ec2 describe-addresses \
    --query 'Addresses[0].AllocationId' \
    --output text)

echo "Allocation ID: $ALLOCATION_ID"

# Associate Elastic IP with instance
aws ec2 associate-address \
    --instance-id $INSTANCE_ID \
    --allocation-id $ALLOCATION_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-addresses \
    --allocation-ids $ALLOCATION_ID \
    --query 'Addresses[0].PublicIp' \
    --output text)

echo "Public IP: $PUBLIC_IP"
```

## 🔧 Step 2: Connect and Deploy

### 2.1 Connect to EC2 Instance

```bash
# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Connect to instance (replace with your key file path)
ssh -i /path/to/your-key.pem ubuntu@$PUBLIC_IP
```

### 2.2 Manual Deployment (if user-data didn't work)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Clone repository
git clone https://github.com/ananya15082002/RCA_Agent.git
cd RCA_Agent

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

## 🌐 Step 3: Access Your Application

After deployment, your application will be accessible at:

- **RCA Portal**: `http://$PUBLIC_IP:8501`
- **Error Dashboard**: `http://$PUBLIC_IP:8502`

## 🔧 Step 4: Configuration

### 4.1 Update Configuration Files

Edit the following files on your EC2 instance:

```bash
# Edit rca_pipeline.py to update URLs and webhooks
nano rca_pipeline.py

# Update these variables:
# - CUBEAPM_BASE_URL
# - GOOGLE_CHAT_WEBHOOK_URL
# - Any other environment-specific URLs
```

### 4.2 Create Environment File

```bash
# Create .env file
cat > .env <<EOF
# CubeAPM Configuration
CUBEAPM_URL=your_cubeapm_url
CUBEAPM_API_KEY=your_api_key

# Google Chat Webhook
GOOGLE_CHAT_WEBHOOK=your_webhook_url

# System Configuration
LOG_LEVEL=INFO
CLEANUP_INTERVAL=86400
MAX_ERROR_REPORTS=100
EOF
```

## 📊 Step 5: Monitoring and Management

### 5.1 Check System Status

```bash
# Check service status
sudo systemctl status rca-pipeline streamlit-portal error-dashboard

# Check logs
tail -f logs/rca_pipeline.log
tail -f logs/streamlit_portal.log
tail -f logs/error_dashboard.log

# Check if ports are listening
sudo netstat -tlnp | grep :850
```

### 5.2 Management Commands

```bash
# Restart services
sudo systemctl restart rca-pipeline streamlit-portal error-dashboard

# Stop services
sudo systemctl stop rca-pipeline streamlit-portal error-dashboard

# Start services
sudo systemctl start rca-pipeline streamlit-portal error-dashboard

# Enable services to start on boot
sudo systemctl enable rca-pipeline streamlit-portal error-dashboard
```

## 🔒 Step 6: Security and SSL (Optional)

### 6.1 Setup Domain and SSL

```bash
# Install Nginx
sudo apt install -y nginx

# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

### 6.2 Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/rca-system > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /dashboard {
        proxy_pass http://localhost:8502;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/rca-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🆘 Step 7: Troubleshooting

### 7.1 Common Issues

```bash
# Check if services are running
sudo systemctl is-active rca-pipeline streamlit-portal error-dashboard

# Check service logs
sudo journalctl -u rca-pipeline -f
sudo journalctl -u streamlit-portal -f
sudo journalctl -u error-dashboard -f

# Check system resources
htop
df -h
free -h

# Check network connectivity
curl -I http://localhost:8501
curl -I http://localhost:8502
```

### 7.2 Useful AWS Commands

```bash
# Get instance status
aws ec2 describe-instances --instance-ids $INSTANCE_ID

# Get instance public IP
aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text

# Stop instance
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID

# Terminate instance (be careful!)
aws ec2 terminate-instances --instance-ids $INSTANCE_ID
```

## 📋 Step 8: Complete Deployment Checklist

- [ ] Security group created with proper rules
- [ ] EC2 instance launched with correct AMI
- [ ] Elastic IP allocated and associated
- [ ] Repository cloned on EC2
- [ ] Dependencies installed
- [ ] Services configured and running
- [ ] Ports accessible from internet
- [ ] Configuration files updated
- [ ] SSL certificate installed (optional)
- [ ] Domain configured (optional)
- [ ] Monitoring setup
- [ ] Backup strategy implemented

## 🎉 Success!

Your 5xx Error RCA System is now deployed and accessible to everyone at:

- **RCA Portal**: `http://$PUBLIC_IP:8501`
- **Error Dashboard**: `http://$PUBLIC_IP:8502`

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f logs/rca_pipeline.log`
2. Verify services: `sudo systemctl status`
3. Check network: `curl -I http://localhost:8501`
4. Review AWS security group rules
5. Check instance status in AWS console 