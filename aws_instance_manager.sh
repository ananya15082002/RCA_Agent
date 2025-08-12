#!/bin/bash

# 🚀 AWS Instance Manager for 5xx RCA System
# This script helps manage the AWS EC2 instance for the RCA Agent

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTANCE_ID="i-04ad00584d6bd3a89"
ELASTIC_IP="3.7.67.210"
REGION="ap-south-1"

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

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
}

# Function to check instance status
check_instance_status() {
    print_status "Checking instance status..."
    local status=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        case $status in
            "running")
                print_success "Instance is RUNNING"
                return 0
                ;;
            "stopped")
                print_warning "Instance is STOPPED"
                return 1
                ;;
            "stopping")
                print_warning "Instance is STOPPING"
                return 2
                ;;
            "pending")
                print_warning "Instance is STARTING"
                return 3
                ;;
            *)
                print_error "Instance status: $status"
                return 4
                ;;
        esac
    else
        print_error "Failed to get instance status"
        return 5
    fi
}

# Function to start instance
start_instance() {
    print_status "Starting instance $INSTANCE_ID..."
    aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION
    
    if [ $? -eq 0 ]; then
        print_success "Instance start command sent successfully"
        print_status "Waiting for instance to be running..."
        
        # Wait for instance to be running
        while true; do
            sleep 10
            check_instance_status
            if [ $? -eq 0 ]; then
                print_success "Instance is now running!"
                break
            fi
        done
    else
        print_error "Failed to start instance"
        return 1
    fi
}

# Function to stop instance
stop_instance() {
    print_status "Stopping instance $INSTANCE_ID..."
    aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION
    
    if [ $? -eq 0 ]; then
        print_success "Instance stop command sent successfully"
    else
        print_error "Failed to stop instance"
        return 1
    fi
}

# Function to check system health
check_system_health() {
    print_status "Checking system health..."
    
    # Check if instance is running
    check_instance_status
    if [ $? -ne 0 ]; then
        print_error "Instance is not running. Cannot check system health."
        return 1
    fi
    
    # Check if services are accessible
    print_status "Checking RCA Portal (port 8501)..."
    if curl -s -I http://$ELASTIC_IP:8501 > /dev/null 2>&1; then
        print_success "RCA Portal is accessible at http://$ELASTIC_IP:8501"
    else
        print_error "RCA Portal is not accessible"
    fi
    
    print_status "Checking Error Dashboard (port 8502)..."
    if curl -s -I http://$ELASTIC_IP:8502 > /dev/null 2>&1; then
        print_success "Error Dashboard is accessible at http://$ELASTIC_IP:8502"
    else
        print_error "Error Dashboard is not accessible"
    fi
    
    # Check SSH access
    print_status "Checking SSH access..."
    if nc -z $ELASTIC_IP 22 2>/dev/null; then
        print_success "SSH access is available"
    else
        print_error "SSH access is not available"
    fi
}

# Function to show instance details
show_instance_details() {
    print_status "Instance Details:"
    echo "Instance ID: $INSTANCE_ID"
    echo "Elastic IP: $ELASTIC_IP"
    echo "Region: $REGION"
    echo ""
    
    # Get instance details from AWS
    print_status "Getting detailed instance information..."
    aws ec2 describe-instances --instance-ids $INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0]' --output table
}

# Function to show security group rules
show_security_groups() {
    print_status "Security Group Rules:"
    echo "Based on your configuration, the following ports should be open:"
    echo "• Port 22 (SSH) - for administrative access"
    echo "• Port 80 (HTTP) - for web access"
    echo "• Port 443 (HTTPS) - for secure web access"
    echo "• Port 8501 (RCA Portal) - for Streamlit portal"
    echo "• Port 8502 (Error Dashboard) - for error dashboard"
    echo ""
    print_status "To view security group rules in AWS Console:"
    echo "1. Go to EC2 Dashboard"
    echo "2. Click on 'Security Groups'"
    echo "3. Find the security group attached to your instance"
    echo "4. Check the 'Inbound rules' tab"
}

# Function to show access URLs
show_access_urls() {
    print_status "Access URLs:"
    echo "🌐 RCA Portal: http://$ELASTIC_IP:8501"
    echo "📊 Error Dashboard: http://$ELASTIC_IP:8502"
    echo "🔧 SSH Access: ssh ec2-user@$ELASTIC_IP"
    echo ""
    print_warning "Note: Access requires VPN connection as per security configuration"
}

# Main menu
show_menu() {
    echo ""
    echo "🚀 AWS Instance Manager for 5xx RCA System"
    echo "=========================================="
    echo "1. Check instance status"
    echo "2. Start instance"
    echo "3. Stop instance"
    echo "4. Check system health"
    echo "5. Show instance details"
    echo "6. Show security group info"
    echo "7. Show access URLs"
    echo "8. Exit"
    echo ""
}

# Main script logic
main() {
    check_aws_cli
    
    while true; do
        show_menu
        read -p "Select an option (1-8): " choice
        
        case $choice in
            1)
                check_instance_status
                ;;
            2)
                start_instance
                ;;
            3)
                stop_instance
                ;;
            4)
                check_system_health
                ;;
            5)
                show_instance_details
                ;;
            6)
                show_security_groups
                ;;
            7)
                show_access_urls
                ;;
            8)
                print_success "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please select 1-8."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 