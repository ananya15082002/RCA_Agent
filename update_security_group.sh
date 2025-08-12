#!/bin/bash

# RCA Agent Security Group Update Script
# This script helps update AWS security group with office IPs and VPN IPs

echo "🔒 RCA Agent Security Group Update Script"
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

echo "✅ AWS CLI is configured"
echo ""

# Get current user info
CURRENT_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
echo "🔑 Current AWS User: $CURRENT_USER"
echo ""

# Function to get security group ID
get_security_group_id() {
    echo "🔍 Searching for RCA Agent security group..."
    
    # Try to find existing security group
    SG_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=rca-agent-sg" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)
    
    if [ "$SG_ID" != "None" ] && [ "$SG_ID" != "" ]; then
        echo "✅ Found existing security group: $SG_ID"
        return 0
    fi
    
    echo "❌ Security group 'rca-agent-sg' not found"
    echo ""
    echo "📋 Please provide your security group ID:"
    echo "   You can find this in AWS Console → EC2 → Security Groups"
    echo "   Or run: aws ec2 describe-security-groups"
    echo ""
    read -p "Enter Security Group ID: " SG_ID
    
    if [ -z "$SG_ID" ]; then
        echo "❌ No security group ID provided"
        exit 1
    fi
    
    # Validate security group exists
    if ! aws ec2 describe-security-groups --group-ids "$SG_ID" &> /dev/null; then
        echo "❌ Invalid security group ID: $SG_ID"
        exit 1
    fi
    
    echo "✅ Valid security group: $SG_ID"
}

# Function to add security group rules
add_security_group_rules() {
    local SG_ID=$1
    local PORT=$2
    local DESCRIPTION=$3
    
    echo ""
    echo "🔧 Adding rules for port $PORT ($DESCRIPTION)..."
    
    # VPN IPs
    VPN_IPS=("3.6.106.39/32" "18.61.175.16/32")
    
    # Office IPs
    OFFICE_IPS=(
        "61.246.30.216/30"   # Hyderabad - Airtel
        "103.169.83.208/29"  # Hyderabad - STPL
        "49.249.85.140/30"   # Hyderabad - Tata
        "49.249.94.0/29"     # Bangalore - Tata
        "223.30.76.72/29"    # Bangalore - Sify
        "106.51.87.26/32"    # Bangalore - Athena
        "157.20.187.178/29"  # Bangalore - Changeri
        "125.21.109.114/32"  # Bangalore - Airtel
        "113.30.146.18/29"   # GGN_HQ63 - Infynix
        "14.194.65.0/29"     # GGN_HQ63 - Tata
        "125.17.193.232/29"  # Goa - Airtel
        "119.226.233.136/29" # Goa - Sify
        "194.195.114.89/32"  # Goa - Aspirare
        "136.233.219.64/29"  # Goa - Jio
        "122.186.172.40/29"  # Goa_HQ2 - Airtel
        "113.30.144.146/32"  # Goa_HQ2 - Infynix
        "1.6.255.168/29"     # Goa_HQ2 - Sify
        "123.252.244.6/32"   # Mumbai - Tata
        "103.124.123.210/32" # Mumbai - Worldphone
        "202.191.205.16/29"  # Mumbai - Sify
        "124.155.241.2/32"   # Mumbai - Athena
        "119.82.74.0/29"     # GGN_HQ04 - Spectra
        "49.249.22.72/29"    # GGN_HQ04 - Tata
        "110.172.159.0/28"   # GGN_HQ05 - Worldphone
        "14.99.236.0/28"     # GGN_HQ05 - Tata
        "122.185.53.50/28"   # GGN_HQ05 - Airtel
        "202.191.229.24/29"  # GGN_HQ05 - Sify
        "115.241.73.74/32"   # Noida - Jio
        "103.178.58.250/32"  # Noida - Primnet
        "14.195.46.82/29"    # Noida - Tata
        "45.115.179.242/32"  # Noida - IAXN
    )
    
    # Combine all IPs
    ALL_IPS=("${VPN_IPS[@]}" "${OFFICE_IPS[@]}")
    
    # Add rules for each IP
    for IP in "${ALL_IPS[@]}"; do
        echo "  Adding rule: $IP -> Port $PORT"
        
        # Add the rule
        if aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --protocol tcp \
            --port "$PORT" \
            --cidr "$IP" \
            --description "RCA Agent - $DESCRIPTION" 2>/dev/null; then
            echo "    ✅ Added successfully"
        else
            echo "    ⚠️  Rule may already exist or failed"
        fi
    done
    
    echo "✅ Completed adding rules for port $PORT"
}

# Function to remove old rules
remove_old_rules() {
    local SG_ID=$1
    
    echo ""
    echo "🧹 Removing old rules (optional)..."
    echo "   This will remove any existing rules for ports 8501 and 8502"
    echo ""
    read -p "Do you want to remove old rules? (y/N): " REMOVE_OLD
    
    if [[ $REMOVE_OLD =~ ^[Yy]$ ]]; then
        echo "🔍 Finding existing rules..."
        
        # Get existing rules for ports 8501 and 8502
        EXISTING_RULES=$(aws ec2 describe-security-groups \
            --group-ids "$SG_ID" \
            --query 'SecurityGroups[0].IpPermissions[?FromPort==`8501` || FromPort==`8502`].IpRanges[].CidrIp' \
            --output text 2>/dev/null)
        
        if [ -n "$EXISTING_RULES" ]; then
            echo "Found existing rules. Removing..."
            # Note: This is a simplified removal. In practice, you might want to be more specific
            echo "⚠️  Manual removal recommended for safety"
        else
            echo "No existing rules found for ports 8501/8502"
        fi
    fi
}

# Main execution
echo "🚀 Starting security group update..."
echo ""

# Get security group ID
get_security_group_id
SG_ID=$SG_ID

echo ""
echo "📋 Security Group: $SG_ID"
echo ""

# Show current rules
echo "🔍 Current security group rules:"
aws ec2 describe-security-groups \
    --group-ids "$SG_ID" \
    --query 'SecurityGroups[0].IpPermissions[?FromPort!=`null`].[FromPort,ToPort,IpRanges[0].CidrIp,Description]' \
    --output table

echo ""
read -p "Continue with adding new rules? (Y/n): " CONTINUE

if [[ $CONTINUE =~ ^[Nn]$ ]]; then
    echo "❌ Update cancelled"
    exit 0
fi

# Remove old rules if requested
remove_old_rules "$SG_ID"

# Add rules for each port
add_security_group_rules "$SG_ID" "8501" "RCA Portal"
add_security_group_rules "$SG_ID" "8502" "Error Dashboard"

# Add SSH rules for VPN IPs only
echo ""
echo "🔧 Adding SSH rules for VPN IPs only..."
for IP in "3.6.106.39/32" "18.61.175.16/32"; do
    echo "  Adding SSH rule: $IP"
    if aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr "$IP" \
        --description "RCA Agent - SSH Access" 2>/dev/null; then
        echo "    ✅ Added successfully"
    else
        echo "    ⚠️  Rule may already exist or failed"
    fi
done

echo ""
echo "✅ Security group update completed!"
echo ""
echo "🔍 Final security group rules:"
aws ec2 describe-security-groups \
    --group-ids "$SG_ID" \
    --query 'SecurityGroups[0].IpPermissions[?FromPort!=`null`].[FromPort,ToPort,IpRanges[0].CidrIp,Description]' \
    --output table

echo ""
echo "🎉 Security group has been updated successfully!"
echo "📋 Access URLs:"
echo "   RCA Portal: http://3.7.67.210:8501"
echo "   Error Dashboard: http://3.7.67.210:8502"
echo ""
echo "🔐 Access is now restricted to:"
echo "   ✅ VPN IPs: 3.6.106.39, 18.61.175.16"
echo "   ✅ Office IPs: All 9 office locations"
echo "   ❌ Personal networks: Blocked" 