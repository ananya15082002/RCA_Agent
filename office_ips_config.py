#!/usr/bin/env python3
"""
Office IPs Configuration for RCA Agent Security Groups
This file contains all authorized office IPs and VPN IPs for secure access
"""

# VPN IPs (Primary access)
VPN_IPS = [
    "3.6.106.39/32",    # VPN IP 1
    "18.61.175.16/32"   # VPN IP 2
]

# Office IPs by location
OFFICE_IPS = {
    "Hyderabad_HQ_Office": [
        "61.246.30.216/30",   # Airtel
        "103.169.83.208/29",  # STPL
        "49.249.85.140/30"    # Tata
    ],
    "Bangalore_HQ_Office": [
        "49.249.94.0/29",     # Tata
        "223.30.76.72/29",    # Sify
        "106.51.87.26/32",    # Athena (ACT)
        "157.20.187.178/29",  # Changeri
        "125.21.109.114/32"   # Airtel
    ],
    "GGN_HQ63": [
        "113.30.146.18/29",   # Infynix
        "14.194.65.0/29"      # Tata
    ],
    "Goa_HQ_Office": [
        "125.17.193.232/29",  # Airtel
        "119.226.233.136/29", # Sify
        "194.195.114.89/32",  # Aspirare
        "136.233.219.64/29"   # Jio
    ],
    "Goa_HQ2_Office": [
        "122.186.172.40/29",  # Airtel
        "113.30.144.146/32",  # Infynix
        "1.6.255.168/29"      # Sify
    ],
    "Mumbai_Hq_Office": [
        "123.252.244.6/32",   # Tata
        "103.124.123.210/32", # Worldphone
        "202.191.205.16/29",  # Sify
        "124.155.241.2/32"    # Athena
    ],
    "GGN_HQ04": [
        "119.82.74.0/29",     # Spectra
        "49.249.22.72/29"     # Tata
    ],
    "GGN_HQ05": [
        "110.172.159.0/28",   # Worldphone
        "14.99.236.0/28",     # Tata
        "122.185.53.50/28",   # Airtel
        "202.191.229.24/29"   # Sify
    ],
    "Noida_Sector62_RO": [
        "115.241.73.74/32",   # Jio
        "103.178.58.250/32",  # Primnet
        "14.195.46.82/29",    # Tata
        "45.115.179.242/32"   # IAXN
    ]
}

def get_all_authorized_ips():
    """Get all authorized IPs (VPN + Office)"""
    all_ips = VPN_IPS.copy()
    for location, ips in OFFICE_IPS.items():
        all_ips.extend(ips)
    return all_ips

def get_ips_by_location(location):
    """Get IPs for a specific office location"""
    return OFFICE_IPS.get(location, [])

def get_vpn_ips():
    """Get VPN IPs only"""
    return VPN_IPS.copy()

def print_security_group_rules():
    """Print AWS security group rules for easy copy-paste"""
    print("🔒 AWS Security Group Rules for RCA Agent")
    print("=" * 50)
    print()
    
    # Port 8501 (RCA Portal)
    print("📋 Port 8501 (RCA Portal) Rules:")
    print("-" * 30)
    for ip in get_all_authorized_ips():
        print(f"  - Type: Custom TCP")
        print(f"    Protocol: TCP")
        print(f"    Port: 8501")
        print(f"    Source: {ip}")
        print(f"    Description: Office/VPN Access")
        print()
    
    # Port 8502 (Error Dashboard)
    print("📋 Port 8502 (Error Dashboard) Rules:")
    print("-" * 30)
    for ip in get_all_authorized_ips():
        print(f"  - Type: Custom TCP")
        print(f"    Protocol: TCP")
        print(f"    Port: 8502")
        print(f"    Source: {ip}")
        print(f"    Description: Office/VPN Access")
        print()
    
    # SSH Access (Port 22) - VPN only
    print("📋 Port 22 (SSH) Rules:")
    print("-" * 30)
    for ip in get_vpn_ips():
        print(f"  - Type: SSH")
        print(f"    Protocol: TCP")
        print(f"    Port: 22")
        print(f"    Source: {ip}")
        print(f"    Description: VPN SSH Access")
        print()

if __name__ == "__main__":
    print_security_group_rules() 