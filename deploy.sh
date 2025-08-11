#!/bin/bash

# 🚀 Quick AWS Deployment Script for 5xx RCA System
# This script automates the deployment process on AWS EC2

set -e  # Exit on any error

echo "🚀 Starting 5xx RCA System AWS Deployment..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. Use a regular user with sudo privileges."
    exit 1
fi

# Step 1: Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated successfully"

# Step 2: Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip build-essential python3-dev
print_success "System dependencies installed"

# Step 3: Install Node.js (for Streamlit components)
print_status "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
print_success "Node.js installed"

# Step 4: Setup Python virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
print_success "Virtual environment created"

# Step 5: Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Step 6: Create necessary directories
print_status "Creating necessary directories..."
mkdir -p error_outputs logs
print_success "Directories created"

# Step 7: Set proper permissions
print_status "Setting file permissions..."
chmod +x *.sh
print_success "Permissions set"

# Step 8: Create systemd services
print_status "Creating systemd services..."
sudo tee /etc/systemd/system/rca-pipeline.service > /dev/null <<EOF
[Unit]
Description=5xx RCA Pipeline
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python rca_pipeline.py
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/logs/rca_pipeline.log
StandardError=append:$(pwd)/logs/rca_pipeline.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/streamlit-portal.service > /dev/null <<EOF
[Unit]
Description=Streamlit Portal
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/streamlit run streamlit_portal.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/logs/streamlit_portal.log
StandardError=append:$(pwd)/logs/streamlit_portal.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/error-dashboard.service > /dev/null <<EOF
[Unit]
Description=Error Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/streamlit run error_dashboard.py --server.port 8502 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:$(pwd)/logs/error_dashboard.log
StandardError=append:$(pwd)/logs/error_dashboard.log

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd services created"

# Step 9: Enable and start services
print_status "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable rca-pipeline streamlit-portal error-dashboard
sudo systemctl start rca-pipeline streamlit-portal error-dashboard
print_success "Services started"

# Step 10: Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Step 11: Check service status
print_status "Checking service status..."
echo ""
echo "Service Status:"
echo "==============="

check_service() {
    local service_name=$1
    if sudo systemctl is-active --quiet $service_name; then
        print_success "$service_name: RUNNING"
    else
        print_error "$service_name: FAILED"
        sudo systemctl status $service_name --no-pager -l
    fi
}

check_service rca-pipeline
check_service streamlit-portal
check_service error-dashboard

# Step 12: Check if ports are listening
print_status "Checking if ports are listening..."
if netstat -tlnp 2>/dev/null | grep -q ":8501"; then
    print_success "Port 8501 (Streamlit Portal): LISTENING"
else
    print_warning "Port 8501 (Streamlit Portal): NOT LISTENING"
fi

if netstat -tlnp 2>/dev/null | grep -q ":8502"; then
    print_success "Port 8502 (Error Dashboard): LISTENING"
else
    print_warning "Port 8502 (Error Dashboard): NOT LISTENING"
fi

# Step 13: Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")

# Step 14: Display access information
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
print_success "Your 5xx RCA System is now deployed and running!"
echo ""
echo "🌐 Access URLs:"
echo "   RCA Portal: http://$PUBLIC_IP:8501"
echo "   Error Dashboard: http://$PUBLIC_IP:8502"
echo ""
echo "📋 Management Commands:"
echo "   Check status: ./status_streamlit.sh"
echo "   View logs: tail -f logs/rca_pipeline.log"
echo "   Stop system: ./stop_system.sh"
echo "   Start system: ./start_system.sh"
echo ""
echo "🔧 Service Management:"
echo "   Check services: sudo systemctl status rca-pipeline streamlit-portal error-dashboard"
echo "   Restart services: sudo systemctl restart rca-pipeline streamlit-portal error-dashboard"
echo "   View service logs: sudo journalctl -u rca-pipeline -f"
echo ""
echo "⚠️  Important Notes:"
echo "   1. Make sure your AWS security group allows traffic on ports 8501 and 8502"
echo "   2. Update the configuration in rca_pipeline.py with your CubeAPM and Google Chat details"
echo "   3. Consider setting up a domain and SSL certificate for production use"
echo ""
print_success "Deployment completed successfully!" 