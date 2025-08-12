# 🔒 AWS Console Security Group Setup Guide

## 📋 Manual AWS Console Steps

### **Step 1: Access AWS Console**
1. Go to [AWS Console](https://console.aws.amazon.com)
2. Navigate to **EC2** → **Security Groups**
3. Find your RCA Agent security group (or create a new one)

### **Step 2: Create Security Group (if needed)**
1. Click **"Create Security Group"**
2. **Name**: `rca-agent-sg`
3. **Description**: `Security group for RCA Agent system`
4. **VPC**: Select your EC2 instance's VPC
5. Click **"Create Security Group"**

### **Step 3: Add Inbound Rules**

#### **Port 22 (SSH) - VPN Only**
Add these rules for SSH access:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | 3.6.106.39/32 | VPN SSH Access |
| SSH | TCP | 22 | 18.61.175.16/32 | VPN SSH Access |

#### **Port 8501 (RCA Portal) - VPN + Office**
Add these rules for RCA Portal access:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| Custom TCP | TCP | 8501 | 3.6.106.39/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 18.61.175.16/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 61.246.30.216/30 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 103.169.83.208/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 49.249.85.140/30 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 49.249.94.0/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 223.30.76.72/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 106.51.87.26/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 157.20.187.178/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 125.21.109.114/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 113.30.146.18/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 14.194.65.0/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 125.17.193.232/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 119.226.233.136/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 194.195.114.89/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 136.233.219.64/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 122.186.172.40/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 113.30.144.146/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 1.6.255.168/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 123.252.244.6/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 103.124.123.210/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 202.191.205.16/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 124.155.241.2/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 119.82.74.0/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 49.249.22.72/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 110.172.159.0/28 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 14.99.236.0/28 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 122.185.53.50/28 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 202.191.229.24/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 115.241.73.74/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 103.178.58.250/32 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 14.195.46.82/29 | Office/VPN Access |
| Custom TCP | TCP | 8501 | 45.115.179.242/32 | Office/VPN Access |

#### **Port 8502 (Error Dashboard) - VPN + Office**
Add the same rules as above but for port 8502:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| Custom TCP | TCP | 8502 | [Same IPs as above] | Office/VPN Access |

### **Step 4: Add Outbound Rules**
Keep the default outbound rule:
- **Type**: All traffic
- **Protocol**: All
- **Port**: All
- **Destination**: 0.0.0.0/0
- **Description**: Allow all outbound traffic

### **Step 5: Attach to EC2 Instance**
1. Go to **EC2** → **Instances**
2. Select your RCA Agent instance
3. Click **"Actions"** → **"Security"** → **"Change Security Groups"**
4. Add the `rca-agent-sg` security group
5. Click **"Add Security Group"** → **"Save"**

## 🚀 Automated Script Option

If you prefer to use the automated script:

```bash
# Make sure you have AWS CLI configured
aws configure

# Run the automated script
./update_security_group.sh
```

## ✅ Verification Steps

### **Test VPN Access**
```bash
# Test SSH access
ssh -i rca-agent-key.pem ec2-user@3.7.67.210

# Test portal access
curl -I http://3.7.67.210:8501
curl -I http://3.7.67.210:8502
```

### **Test Office Access**
From any office location, try accessing:
- `http://3.7.67.210:8501`
- `http://3.7.67.210:8502`

### **Verify Personal Network Blocked**
From a personal network, access should be blocked.

## 🚨 Important Notes

1. **Remove any existing 0.0.0.0/0 rules** for ports 8501 and 8502
2. **Keep only the authorized IPs** listed above
3. **Test access** from VPN and office locations
4. **Monitor access logs** for unauthorized attempts

## 📞 Support

If you encounter issues:
1. Check that your EC2 instance is running
2. Verify the security group is attached to the instance
3. Test from different office locations
4. Contact IT for VPN access issues

---

**Security Group Setup Complete!** 🎉 