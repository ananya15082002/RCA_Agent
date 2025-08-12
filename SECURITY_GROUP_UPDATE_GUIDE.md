# 🔧 Security Group Update Guide for VPN Access

## 🎯 **Objective**
Update the security group to allow access from your VPN IPs so Google Chat links work properly.

## 📋 **Your VPN IPs**
- **Primary VPN IP**: `3.6.106.39/32`
- **Secondary VPN IP**: `18.61.175.16/32`

## 🌐 **Required Ports**
- **Port 22**: SSH access
- **Port 80**: HTTP access
- **Port 443**: HTTPS access
- **Port 8501**: RCA Portal
- **Port 8502**: Error Dashboard

## 🔧 **Manual Security Group Update Steps**

### **Step 1: Access AWS Console**
1. Go to [AWS Console](https://console.aws.amazon.com)
2. Navigate to **EC2 → Security Groups**
3. Find the security group attached to your instance `i-04ad00584d6bd3a89`

### **Step 2: Add Inbound Rules**

#### **For Port 8501 (RCA Portal):**
1. Click **"Edit inbound rules"**
2. Click **"Add rule"**
3. Configure:
   - **Type**: Custom TCP
   - **Protocol**: TCP
   - **Port range**: 8501
   - **Source**: `3.6.106.39/32`
   - **Description**: "VPN access for RCA Portal"

4. Click **"Add rule"** again
5. Configure:
   - **Type**: Custom TCP
   - **Protocol**: TCP
   - **Port range**: 8501
   - **Source**: `18.61.175.16/32`
   - **Description**: "VPN access for RCA Portal"

#### **For Port 8502 (Error Dashboard):**
1. Click **"Add rule"**
2. Configure:
   - **Type**: Custom TCP
   - **Protocol**: TCP
   - **Port range**: 8502
   - **Source**: `3.6.106.39/32`
   - **Description**: "VPN access for Error Dashboard"

3. Click **"Add rule"** again
4. Configure:
   - **Type**: Custom TCP
   - **Protocol**: TCP
   - **Port range**: 8502
   - **Source**: `18.61.175.16/32`
   - **Description**: "VPN access for Error Dashboard"

#### **For SSH Access (Port 22):**
1. Click **"Add rule"**
2. Configure:
   - **Type**: SSH
   - **Protocol**: TCP
   - **Port range**: 22
   - **Source**: `3.6.106.39/32`
   - **Description**: "VPN SSH access"

3. Click **"Add rule"** again
4. Configure:
   - **Type**: SSH
   - **Protocol**: TCP
   - **Port range**: 22
   - **Source**: `18.61.175.16/32`
   - **Description**: "VPN SSH access"

### **Step 3: Save Changes**
1. Click **"Save rules"**
2. Verify the rules are added correctly

## 🌐 **Test Access URLs**

After updating the security group, test these URLs:

### **RCA Portal**
- **URL**: http://3.7.67.210:8501
- **Should work** when connected to VPN

### **Error Dashboard**
- **URL**: http://3.7.67.210:8502
- **Should work** when connected to VPN

## 🔍 **Verify Security Group Rules**

Your security group should now have these rules:

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | 3.6.106.39/32 | VPN SSH access |
| SSH | TCP | 22 | 18.61.175.16/32 | VPN SSH access |
| Custom TCP | TCP | 8501 | 3.6.106.39/32 | VPN access for RCA Portal |
| Custom TCP | TCP | 8501 | 18.61.175.16/32 | VPN access for RCA Portal |
| Custom TCP | TCP | 8502 | 3.6.106.39/32 | VPN access for Error Dashboard |
| Custom TCP | TCP | 8502 | 18.61.175.16/32 | VPN access for Error Dashboard |

## 🚀 **After Security Group Update**

1. **Google Chat links should work** when you're connected to VPN
2. **Direct access to portals** should be possible
3. **SSH access** should work from VPN IPs

## 📱 **Google Chat Integration**

Once the security group is updated:
- **Links will work** when you're connected to VPN
- **Direct URLs** will be used (no more TinyURL issues)
- **Access will be secure** through VPN only

---

**Note**: Make sure you're connected to your VPN before testing the URLs! 