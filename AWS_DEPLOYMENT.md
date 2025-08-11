# 🚀 AWS Deployment Guide for 5xx Error RCA System

This guide will help you deploy the 5xx Error RCA System on AWS EC2 for public access.

## 📋 Prerequisites

- AWS Account with EC2 access
- AWS CLI configured
- SSH key pair for EC2 access
- Domain name (optional, for custom URL)

## 🏗️ AWS Infrastructure Setup

### 1. Create EC2 Instance

```bash
# Launch Ubuntu 22.04 LTS instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --subnet-id subnet-xxxxxxxxx \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=5xx-RCA-System}]'
```

### 2. Security Group Configuration

Create a security group with the following rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | 0.0.0.0/0 | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP access |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS access |
| Custom TCP | TCP | 8501 | 0.0.0.0/0 | Streamlit Portal |
| Custom TCP | TCP | 8502 | 0.0.0.0/0 | Error Dashboard |

### 3. Elastic IP (Optional)

```bash
# Allocate Elastic IP for static public IP
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id i-xxxxxxxxx --allocation-id eipalloc-xxxxxxxxx
```

## 🚀 Deployment Steps

### Step 1: Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Update System and Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Install additional system dependencies
sudo apt install -y git curl wget unzip

# Install Node.js (for some Streamlit components)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Step 3: Clone Repository

```bash
# Clone the repository
git clone https://github.com/ananya15082002/RCA_Agent.git
cd RCA_Agent

# Copy 5xx system files
cp -r 5xx/* ./
rm -rf 5xx/
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional system packages
sudo apt install -y python3-dev build-essential
```

### Step 5: Configure System

```bash
# Create necessary directories
mkdir -p error_outputs logs

# Set proper permissions
chmod +x *.sh

# Create systemd service files (optional)
sudo tee /etc/systemd/system/rca-pipeline.service > /dev/null <<EOF
[Unit]
Description=5xx RCA Pipeline
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RCA_Agent
Environment=PATH=/home/ubuntu/RCA_Agent/venv/bin
ExecStart=/home/ubuntu/RCA_Agent/venv/bin/python rca_pipeline.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/streamlit-portal.service > /dev/null <<EOF
[Unit]
Description=Streamlit Portal
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RCA_Agent
Environment=PATH=/home/ubuntu/RCA_Agent/venv/bin
ExecStart=/home/ubuntu/RCA_Agent/venv/bin/streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/error-dashboard.service > /dev/null <<EOF
[Unit]
Description=Error Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RCA_Agent
Environment=PATH=/home/ubuntu/RCA_Agent/venv/bin
ExecStart=/home/ubuntu/RCA_Agent/venv/bin/streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable rca-pipeline streamlit-portal error-dashboard
sudo systemctl start rca-pipeline streamlit-portal error-dashboard
```

### Step 6: Setup Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install -y nginx

# Configure Nginx
sudo tee /etc/nginx/sites-available/rca-system > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

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

### Step 7: Setup SSL Certificate (Optional)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```bash
# Create environment file
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

### Update Configuration in Code

Edit the following files to update URLs and endpoints:

1. `rca_pipeline.py` - Update CubeAPM URLs and webhook URLs
2. `streamlit_portal.py` - Update any hardcoded URLs
3. `error_dashboard.py` - Update any hardcoded URLs

## 🚀 Quick Start Script

Create a quick start script:

```bash
cat > deploy.sh <<'EOF'
#!/bin/bash

echo "🚀 Deploying 5xx RCA System on AWS..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create directories
mkdir -p error_outputs logs

# Set permissions
chmod +x *.sh

# Start system
./start_system.sh

echo "✅ Deployment complete!"
echo "🌐 Access URLs:"
echo "   Portal: http://$(curl -s ifconfig.me):8501"
echo "   Dashboard: http://$(curl -s ifconfig.me):8502"
EOF

chmod +x deploy.sh
```

## 📊 Monitoring and Maintenance

### Check System Status

```bash
# Check service status
sudo systemctl status rca-pipeline streamlit-portal error-dashboard

# Check logs
tail -f logs/rca_pipeline.log
tail -f logs/streamlit_portal.log
tail -f logs/error_dashboard.log

# Check system resources
htop
df -h
```

### Backup and Recovery

```bash
# Create backup script
cat > backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup configuration and data
cp -r error_outputs $BACKUP_DIR/
cp -r logs $BACKUP_DIR/
cp *.py $BACKUP_DIR/
cp *.sh $BACKUP_DIR/
cp requirements.txt $BACKUP_DIR/

echo "Backup created: $BACKUP_DIR"
EOF

chmod +x backup.sh
```

## 🔒 Security Considerations

1. **Firewall**: Configure security groups properly
2. **SSL**: Use HTTPS for production
3. **Authentication**: Consider adding authentication to Streamlit apps
4. **Monitoring**: Set up CloudWatch for monitoring
5. **Backup**: Regular backups of configuration and data

## 🌐 Public Access URLs

After deployment, your system will be accessible at:

- **RCA Portal**: `http://your-ec2-public-ip:8501`
- **Error Dashboard**: `http://your-ec2-public-ip:8502`

If using a domain with Nginx:
- **RCA Portal**: `https://your-domain.com`
- **Error Dashboard**: `https://your-domain.com/dashboard`

## 🆘 Troubleshooting

### Common Issues

1. **Port not accessible**: Check security group rules
2. **Service not starting**: Check logs and dependencies
3. **Memory issues**: Consider upgrading instance type
4. **SSL issues**: Verify certificate configuration

### Useful Commands

```bash
# Check if ports are listening
sudo netstat -tlnp | grep :850

# Check service logs
sudo journalctl -u rca-pipeline -f
sudo journalctl -u streamlit-portal -f
sudo journalctl -u error-dashboard -f

# Restart services
sudo systemctl restart rca-pipeline streamlit-portal error-dashboard
```

## 📞 Support

For issues or questions:
1. Check the logs in `/home/ubuntu/RCA_Agent/logs/`
2. Review system status with `./status_streamlit.sh`
3. Check service status with `sudo systemctl status` 