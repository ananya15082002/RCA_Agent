#!/bin/bash

# 🔧 Security Group Update Script for RCA Agent
# This script updates the security group to allow access from VPN IPs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VPN_IPS=("3.6.106.39/32" "18.61.175.16/32")
PORTS=(22 80 443 8501 8502)
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

# Function to get security group ID
get_security_group_id() {
    print_status "Getting security group ID for instance..."
    
    # Get the security group ID from the instance
    SG_ID=$(aws ec2 describe-instances \
        --instance-ids i-04ad00584d6bd3a89 \
        --region $REGION \
        --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)
    
    if [ $? -eq 0 ] && [ "$SG_ID" != "None" ]; then
        print_success "Found security group: $SG_ID"
        echo $SG_ID
    else
        print_error "Failed to get security group ID"
        return 1
    fi
}

# Function to add security group rules
add_security_group_rules() {
    local sg_id=$1
    
    print_status "Adding security group rules for VPN access..."
    
    for ip in "${VPN_IPS[@]}"; do
        for port in "${PORTS[@]}"; do
            case $port in
                22)
                    rule_type="SSH"
                    ;;
                80)
                    rule_type="HTTP"
                    ;;
                443)
                    rule_type="HTTPS"
                    ;;
                *)
                    rule_type="Custom TCP"
                    ;;
            esac
            
            print_status "Adding $rule_type rule for $ip on port $port..."
            
            aws ec2 authorize-security-group-ingress \
                --group-id $sg_id \
                --protocol tcp \
                --port $port \
                --cidr $ip \
                --region $REGION \
                --description "VPN access for RCA Agent" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                print_success "Added $rule_type rule for $ip on port $port"
            else
                print_warning "Rule for $ip on port $port may already exist"
            fi
        done
    done
}

# Function to show current rules
show_current_rules() {
    local sg_id=$1
    
    print_status "Current security group rules:"
    aws ec2 describe-security-groups \
        --group-ids $sg_id \
        --region $REGION \
        --query 'SecurityGroups[0].IpPermissions[?IpProtocol==`tcp`].[FromPort,ToPort,IpRanges[0].CidrIp,Description]' \
        --output table
}

# Main execution
main() {
    print_status "Starting security group update for RCA Agent..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Get security group ID
    SG_ID=$(get_security_group_id)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Show current rules
    show_current_rules $SG_ID
    
    # Add new rules
    add_security_group_rules $SG_ID
    
    # Show updated rules
    print_status "Updated security group rules:"
    show_current_rules $SG_ID
    
    print_success "Security group update completed!"
    print_status "VPN IPs configured: ${VPN_IPS[*]}"
    print_status "Ports configured: ${PORTS[*]}"
    
    echo ""
    print_status "Access URLs:"
    echo "   RCA Portal: http://3.7.67.210:8501"
    echo "   Error Dashboard: http://3.7.67.210:8502"
    echo ""
    print_warning "Note: Access requires VPN connection from configured IPs"
}

# Run main function
main "$@" 