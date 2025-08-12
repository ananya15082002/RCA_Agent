# 🚀 RCA Agent Quick Access Guide

## 🌐 **System URLs**

### **RCA Portal (Main Interface)**
- **URL**: `http://3.7.67.210:8501`
- **Purpose**: View detailed error reports and RCA analysis
- **Access**: VPN + Office IPs only

### **Error Dashboard**
- **URL**: `http://3.7.67.210:8502`
- **Purpose**: Overview of all errors and trends
- **Access**: VPN + Office IPs only

## 🔐 **Access Methods**

### **✅ VPN Access (Recommended)**
```
VPN IP 1: 3.6.106.39
VPN IP 2: 18.61.175.16
```
- **Connect to VPN first**
- **Then access the URLs above**
- **Most secure method**

### **✅ Office Access (Direct)**
- **Access from any company office location**
- **No VPN required when in office**
- **All 9 office locations supported**

### **❌ Personal Networks**
- **Access blocked from personal networks**
- **Must use VPN or office network**

## 📱 **Google Chat Alerts**

### **Alert Format**
- **Clickable buttons** with TinyURL links
- **Direct access** to specific error reports
- **No more HTTPS conversion issues**

### **Test Channel**
- **Webhook**: `AAQAsi2-pJQ` (test channel)
- **Main Channel**: `AAQADdrSRHs` (production)

## 🛠️ **System Status**

### **Current Status**
- **✅ RCA Pipeline**: Running (PID: 2997)
- **✅ Streamlit Portal**: Running (PID: 3002)
- **✅ Error Dashboard**: Running (PID: 3009)
- **✅ Error Reports**: 26,424 total

### **Error Filtering**
- **5xx errors EXCEPT 500** (501, 502, 503, etc.)
- **Real-time detection** every 5 minutes
- **Automatic Google Chat alerts**

## 🔧 **Management Commands**

### **Check Status**
```bash
ssh -i rca-agent-key.pem ec2-user@3.7.67.210
cd RCA_Agent
./status_streamlit.sh
```

### **View Logs**
```bash
# RCA Pipeline logs
tail -f logs/rca_pipeline.log

# Portal logs
tail -f logs/streamlit_portal.log

# Dashboard logs
tail -f logs/error_dashboard.log
```

### **Stop System**
```bash
./stop_system.sh
```

### **Start System**
```bash
./start_system.sh
```

## 🚨 **Troubleshooting**

### **Can't Access Portal?**
1. **Check VPN connection**
2. **Verify you're on authorized IP**
3. **Try office network if available**
4. **Contact IT if VPN issues**

### **Alerts Not Working?**
1. **Check system status**
2. **Verify webhook configuration**
3. **Check error filtering settings**

### **Links Not Opening?**
1. **Use VPN connection**
2. **Copy-paste URL manually**
3. **Check browser cache**

## 📞 **Support**

- **IT Support**: VPN issues
- **Network Team**: Office IP changes
- **Security Team**: Access violations

---

**Last Updated**: August 12, 2025  
**System Version**: 2.0  
**Security**: Enterprise-grade with office IP restrictions 