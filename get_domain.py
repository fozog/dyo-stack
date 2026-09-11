#!/usr/bin/python3
import socket

def get_local_ip():
    """Determine the active local IP address across OS platforms."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connects to an external IP without sending actual packets
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def get_dns_domain_and_ptr():
    """Perform reverse DNS lookup and extract domain info portably."""
    ip = get_local_ip()
    #print(f"Local IP: {ip}")
    
    try:
        # socket.gethostbyaddr handles the PTR/reverse lookup natively
        hostname, aliases, ipaddrs = socket.gethostbyaddr(ip)
        
        # Extract domain suffix by splitting off the first component
        parts = hostname.split('.')
        if len(parts) > 1:
            domain = '.'.join(parts[1:])
            print(f"{domain}")
        else:
            print("No domain suffix found in hostname.")
            
    except socket.herror as e:
        print(f"PTR lookup failed: {e}")

if __name__ == "__main__":
    get_dns_domain_and_ptr()
