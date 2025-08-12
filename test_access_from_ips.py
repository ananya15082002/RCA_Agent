#!/usr/bin/env python3
"""
RCA Agent Access Testing Script
Tests access from different IPs and shows security group configuration
"""

import requests
import subprocess
import json
import time
from datetime import datetime

# Test IPs
TEST_IPS = {
    "VPN_IPs": [
        "3.6.106.39",
        "18.61.175.16"
    ],
    "Office_IPs": {
        "Hyderabad_HQ_Office": [
            "61.246.30.216",
            "103.169.83.208", 
            "49.249.85.140"
        ],
        "Bangalore_HQ_Office": [
            "49.249.94.0",
            "223.30.76.72",
            "106.51.87.26",
            "157.20.187.178",
            "125.21.109.114"
        ],
        "GGN_HQ63": [
            "113.30.146.18",
            "14.194.65.0"
        ],
        "Goa_HQ_Office": [
            "125.17.193.232",
            "119.226.233.136",
            "194.195.114.89",
            "136.233.219.64"
        ],
        "Goa_HQ2_Office": [
            "122.186.172.40",
            "113.30.144.146",
            "1.6.255.168"
        ],
        "Mumbai_Hq_Office": [
            "123.252.244.6",
            "103.124.123.210",
            "202.191.205.16",
            "124.155.241.2"
        ],
        "GGN_HQ04": [
            "119.82.74.0",
            "49.249.22.72"
        ],
        "GGN_HQ05": [
            "110.172.159.0",
            "14.99.236.0",
            "122.185.53.50",
            "202.191.229.24"
        ],
        "Noida_Sector62_RO": [
            "115.241.73.74",
            "103.178.58.250",
            "14.195.46.82",
            "45.115.179.242"
        ]
    },
    "Personal_Network_IPs": [
        "8.8.8.8",           # Google DNS (public)
        "1.1.1.1",           # Cloudflare DNS (public)
        "192.168.1.1",       # Common home router
        "10.0.0.1",          # Common home network
        "172.16.0.1"         # Common private network
    ]
}

# RCA Agent URLs
RCA_URLS = {
    "portal": "http://3.7.67.210:8501",
    "dashboard": "http://3.7.67.210:8502"
}

def get_current_ip():
    """Get current public IP"""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        return response.json()['ip']
    except:
        return "Unknown"

def test_url_access(url, ip=None):
    """Test access to a URL from a specific IP (simulated)"""
    try:
        headers = {'User-Agent': 'RCA-Agent-Test/1.0'}
        if ip:
            headers['X-Forwarded-For'] = ip
            headers['X-Real-IP'] = ip
        
        response = requests.get(url, headers=headers, timeout=10)
        return {
            'status_code': response.status_code,
            'accessible': response.status_code == 200,
            'response_time': response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        return {
            'status_code': None,
            'accessible': False,
            'error': str(e)
        }

def print_security_group_config():
    """Print the security group configuration"""
    print("🔒 AWS Security Group Configuration")
    print("=" * 50)
    print()
    
    # SSH Rules (VPN only)
    print("📋 Port 22 (SSH) - VPN Only:")
    print("-" * 30)
    for ip in TEST_IPS["VPN_IPs"]:
        print(f"  Type: SSH")
        print(f"  Protocol: TCP")
        print(f"  Port: 22")
        print(f"  Source: {ip}/32")
        print(f"  Description: VPN SSH Access")
        print()
    
    # Portal and Dashboard Rules
    for port, service in [("8501", "RCA Portal"), ("8502", "Error Dashboard")]:
        print(f"📋 Port {port} ({service}) - VPN + Office:")
        print("-" * 40)
        
        # VPN IPs
        for ip in TEST_IPS["VPN_IPs"]:
            print(f"  Type: Custom TCP")
            print(f"  Protocol: TCP")
            print(f"  Port: {port}")
            print(f"  Source: {ip}/32")
            print(f"  Description: Office/VPN Access")
            print()
        
        # Office IPs
        for location, ips in TEST_IPS["Office_IPs"].items():
            for ip in ips:
                print(f"  Type: Custom TCP")
                print(f"  Protocol: TCP")
                print(f"  Port: {port}")
                print(f"  Source: {ip}/32")
                print(f"  Description: Office Access - {location}")
                print()

def test_current_access():
    """Test current access from this machine"""
    print("🌐 Testing Current Access")
    print("=" * 30)
    
    current_ip = get_current_ip()
    print(f"📍 Current IP: {current_ip}")
    print()
    
    for service, url in RCA_URLS.items():
        print(f"🔍 Testing {service.upper()} ({url}):")
        result = test_url_access(url)
        
        if result['accessible']:
            print(f"  ✅ ACCESSIBLE - Status: {result['status_code']}")
            print(f"  ⏱️  Response Time: {result['response_time']:.2f}s")
        else:
            print(f"  ❌ NOT ACCESSIBLE")
            if 'error' in result:
                print(f"  🔍 Error: {result['error']}")
        print()

def simulate_ip_tests():
    """Simulate tests from different IPs"""
    print("🧪 Simulating Access Tests from Different IPs")
    print("=" * 50)
    print()
    
    # Test VPN IPs
    print("🔐 VPN IPs (Should be accessible):")
    print("-" * 30)
    for ip in TEST_IPS["VPN_IPs"]:
        print(f"📍 Testing from VPN IP: {ip}")
        for service, url in RCA_URLS.items():
            result = test_url_access(url, ip)
            status = "✅ ACCESSIBLE" if result['accessible'] else "❌ BLOCKED"
            print(f"  {service.upper()}: {status}")
        print()
    
    # Test Office IPs (sample)
    print("🏢 Office IPs (Sample - Should be accessible):")
    print("-" * 40)
    for location, ips in list(TEST_IPS["Office_IPs"].items())[:3]:  # Test first 3 locations
        for ip in ips[:2]:  # Test first 2 IPs per location
            print(f"📍 Testing from {location}: {ip}")
            for service, url in RCA_URLS.items():
                result = test_url_access(url, ip)
                status = "✅ ACCESSIBLE" if result['accessible'] else "❌ BLOCKED"
                print(f"  {service.upper()}: {status}")
            print()
    
    # Test Personal Network IPs
    print("🏠 Personal Network IPs (Should be blocked):")
    print("-" * 40)
    for ip in TEST_IPS["Personal_Network_IPs"]:
        print(f"📍 Testing from Personal IP: {ip}")
        for service, url in RCA_URLS.items():
            result = test_url_access(url, ip)
            status = "❌ BLOCKED" if not result['accessible'] else "⚠️  ACCESSIBLE (Security Issue!)"
            print(f"  {service.upper()}: {status}")
        print()

def generate_aws_cli_commands():
    """Generate AWS CLI commands for security group update"""
    print("🚀 AWS CLI Commands for Security Group Update")
    print("=" * 50)
    print()
    print("⚠️  Replace 'sg-xxxxxxxxx' with your actual security group ID")
    print()
    
    sg_id = "sg-xxxxxxxxx"  # Replace with actual SG ID
    
    # SSH rules
    print("# SSH Rules (VPN only)")
    for ip in TEST_IPS["VPN_IPs"]:
        print(f"aws ec2 authorize-security-group-ingress \\")
        print(f"  --group-id {sg_id} \\")
        print(f"  --protocol tcp \\")
        print(f"  --port 22 \\")
        print(f"  --cidr {ip}/32 \\")
        print(f"  --description 'RCA Agent - VPN SSH Access'")
        print()
    
    # Portal and Dashboard rules
    for port, service in [("8501", "RCA Portal"), ("8502", "Error Dashboard")]:
        print(f"# {service} Rules (VPN + Office)")
        
        # VPN IPs
        for ip in TEST_IPS["VPN_IPs"]:
            print(f"aws ec2 authorize-security-group-ingress \\")
            print(f"  --group-id {sg_id} \\")
            print(f"  --protocol tcp \\")
            print(f"  --port {port} \\")
            print(f"  --cidr {ip}/32 \\")
            print(f"  --description 'RCA Agent - {service} Access'")
            print()
        
        # Office IPs
        for location, ips in TEST_IPS["Office_IPs"].items():
            for ip in ips:
                print(f"aws ec2 authorize-security-group-ingress \\")
                print(f"  --group-id {sg_id} \\")
                print(f"  --protocol tcp \\")
                print(f"  --port {port} \\")
                print(f"  --cidr {ip}/32 \\")
                print(f"  --description 'RCA Agent - {service} - {location}'")
                print()

def main():
    """Main function"""
    print("🔒 RCA Agent Security Group Testing & Configuration")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test current access
    test_current_access()
    print()
    
    # Show security group configuration
    print_security_group_config()
    print()
    
    # Simulate IP tests
    simulate_ip_tests()
    print()
    
    # Generate AWS CLI commands
    generate_aws_cli_commands()
    print()
    
    print("🎯 Summary:")
    print("✅ VPN IPs should have full access (SSH + Portal + Dashboard)")
    print("✅ Office IPs should have portal/dashboard access only")
    print("❌ Personal network IPs should be completely blocked")
    print()
    print("📋 Next Steps:")
    print("1. Update AWS security group with the provided rules")
    print("2. Test access from VPN and office locations")
    print("3. Verify personal networks are blocked")
    print("4. Monitor access logs for security")

if __name__ == "__main__":
    main() 