# 🔒 RCA Agent Security Group Configuration

## 📋 Overview
This document provides the complete security group configuration for the RCA Agent system to ensure secure access from authorized office locations and VPN IPs only.

## 🎯 Access Control Strategy

### **✅ Authorized Access:**
- **VPN IPs**: Primary secure access
- **Office IPs**: Direct access from company offices
- **All other IPs**: **BLOCKED** (personal networks, external access)

### **🛡️ Security Levels:**
1. **SSH (Port 22)**: VPN IPs only
2. **RCA Portal (Port 8501)**: VPN + Office IPs
3. **Error Dashboard (Port 8502)**: VPN + Office IPs

## 🌐 Authorized IP Addresses

### **🔐 VPN IPs (Primary Access)**
```
3.6.106.39/32    # VPN IP 1
18.61.175.16/32  # VPN IP 2
```

### **🏢 Office IPs by Location**

#### **Hyderabad HQ Office**
```
61.246.30.216/30   # Airtel
103.169.83.208/29  # STPL
49.249.85.140/30   # Tata
```

#### **Bangalore HQ Office**
```
49.249.94.0/29     # Tata
223.30.76.72/29    # Sify
106.51.87.26/32    # Athena (ACT)
157.20.187.178/29  # Changeri
125.21.109.114/32  # Airtel
```

#### **GGN HQ63**
```
113.30.146.18/29   # Infynix
14.194.65.0/29     # Tata
```

#### **Goa HQ Office**
```
125.17.193.232/29  # Airtel
119.226.233.136/29 # Sify
194.195.114.89/32  # Aspirare
136.233.219.64/29  # Jio
```

#### **Goa HQ2 Office**
```
122.186.172.40/29  # Airtel
113.30.144.146/32  # Infynix
1.6.255.168/29     # Sify
```

#### **Mumbai HQ Office**
```
123.252.244.6/32   # Tata
103.124.123.210/32 # Worldphone
202.191.205.16/29  # Sify
124.155.241.2/32   # Athena
```

#### **GGN HQ04**
```
119.82.74.0/29     # Spectra
49.249.22.72/29    # Tata
```

#### **GGN HQ05**
```
110.172.159.0/28   # Worldphone
14.99.236.0/28     # Tata
122.185.53.50/28   # Airtel
202.191.229.24/29  # Sify
```

#### **Noida Sector 62 RO**
```
115.241.73.74/32   # Jio
103.178.58.250/32  # Primnet
14.195.46.82/29    # Tata
45.115.179.242/32  # IAXN
```

## 🔧 AWS Security Group Configuration

### **Step 1: Create Security Group**
1. Go to AWS Console → EC2 → Security Groups
2. Create new security group: `rca-agent-sg`
3. Description: `Security group for RCA Agent system`

### **Step 2: Configure Inbound Rules**

#### **Port 22 (SSH) - VPN Only**
```
Type: SSH
Protocol: TCP
Port: 22
Source: 3.6.106.39/32
Description: VPN SSH Access

Type: SSH
Protocol: TCP
Port: 22
Source: 18.61.175.16/32
Description: VPN SSH Access
```

#### **Port 8501 (RCA Portal) - VPN + Office**
Add rules for all authorized IPs:
```
Type: Custom TCP
Protocol: TCP
Port: 8501
Source: [Each authorized IP from list above]
Description: Office/VPN Access
```

#### **Port 8502 (Error Dashboard) - VPN + Office**
Add rules for all authorized IPs:
```
Type: Custom TCP
Protocol: TCP
Port: 8502
Source: [Each authorized IP from list above]
Description: Office/VPN Access
```

### **Step 3: Outbound Rules**
```
Type: All traffic
Protocol: All
Port: All
Destination: 0.0.0.0/0
Description: Allow all outbound traffic
```

## 🚨 Security Best Practices

### **✅ Do's:**
- ✅ Use VPN for remote access
- ✅ Access from authorized office locations only
- ✅ Keep security group rules updated
- ✅ Monitor access logs regularly
- ✅ Use strong SSH keys

### **❌ Don'ts:**
- ❌ Don't allow 0.0.0.0/0 access to any port
- ❌ Don't share VPN credentials
- ❌ Don't access from personal networks
- ❌ Don't bypass security controls

## 📊 Access Summary

| Service | Port | VPN Access | Office Access | Personal Networks |
|---------|------|------------|---------------|-------------------|
| **SSH** | 22 | ✅ Yes | ❌ No | ❌ No |
| **RCA Portal** | 8501 | ✅ Yes | ✅ Yes | ❌ No |
| **Error Dashboard** | 8502 | ✅ Yes | ✅ Yes | ❌ No |

## 🔍 Monitoring & Maintenance

### **Regular Tasks:**
1. **Weekly**: Review access logs
2. **Monthly**: Update office IPs if needed
3. **Quarterly**: Security group audit
4. **As needed**: Add new office locations

### **Access Logs:**
- Monitor SSH access attempts
- Track portal access patterns
- Alert on unauthorized access attempts

## 🆘 Emergency Access

### **If VPN is down:**
1. Use office IPs for direct access
2. Contact IT for VPN restoration
3. Monitor for unusual access patterns

### **If office IPs change:**
1. Update security group rules immediately
2. Test access from new IPs
3. Remove old IP rules

## 📞 Support Contacts

- **IT Support**: For VPN issues
- **Network Team**: For office IP changes
- **Security Team**: For access violations

---

**Last Updated**: August 12, 2025  
**Version**: 1.0  
**Author**: RCA Agent Team 