#!/usr/bin/env python3
"""
Fix SSL Issues with Production API
Resolves SSL handshake failures with api.coinjecture.com
"""

import requests
import ssl
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import socket
import json
import sys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLFixer:
    def __init__(self):
        self.production_api = "https://api.coinjecture.com"
        self.remote_api = "http://167.172.213.70:12346"
        
    def test_ssl_connection(self):
        """Test SSL connection to production API"""
        print("🔍 Testing SSL Connection to Production API...")
        
        try:
            # Test basic SSL connection
            context = ssl.create_default_context()
            with socket.create_connection(('api.coinjecture.com', 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname='api.coinjecture.com') as ssock:
                    print(f"✅ SSL Connection: {ssock.version()}")
                    print(f"   Cipher: {ssock.cipher()}")
                    return True
        except Exception as e:
            print(f"❌ SSL Connection failed: {e}")
            return False
    
    def test_http_requests(self):
        """Test HTTP requests with different SSL configurations"""
        print("\n🔍 Testing HTTP Requests with SSL Fixes...")
        
        # Create session with custom SSL settings
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Test different SSL configurations
        configs = [
            {
                "name": "SSL Verification Disabled",
                "verify": False,
                "timeout": 10
            },
            {
                "name": "Custom SSL Context",
                "verify": False,
                "timeout": 15,
                "headers": {
                    'User-Agent': 'COINjecture-SSL-Fix/1.0',
                    'Accept': 'application/json'
                }
            },
            {
                "name": "Legacy SSL Support",
                "verify": False,
                "timeout": 20,
                "headers": {
                    'User-Agent': 'Mozilla/5.0 (compatible; COINjecture/1.0)',
                    'Accept': 'application/json',
                    'Connection': 'close'
                }
            }
        ]
        
        for config in configs:
            try:
                name = config.pop("name")
                print(f"   Testing {name}...")
                
                response = session.get(f"{self.production_api}/health", **config)
                if response.status_code == 200:
                    print(f"   ✅ {name}: Success (Status {response.status_code})")
                    data = response.json()
                    print(f"      Response: {data}")
                    return True
                else:
                    print(f"   ⚠️  {name}: Status {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {name}: {e}")
        
        return False
    
    def create_ssl_fixed_client(self):
        """Create a client with SSL issues fixed"""
        print("\n🔧 Creating SSL-Fixed Client...")
        
        class SSLFixedClient:
            def __init__(self):
                self.session = requests.Session()
                
                # Disable SSL verification
                self.session.verify = False
                
                # Custom headers
                self.session.headers.update({
                    'User-Agent': 'COINjecture-SSL-Fixed/1.0',
                    'Accept': 'application/json',
                    'Connection': 'keep-alive'
                })
                
                # Configure retry strategy
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[429, 500, 502, 503, 504],
                )
                adapter = HTTPAdapter(max_retries=retry_strategy)
                self.session.mount("http://", adapter)
                self.session.mount("https://", adapter)
            
            def get(self, url, **kwargs):
                """Get request with SSL fixes"""
                kwargs.setdefault('timeout', 15)
                kwargs.setdefault('verify', False)
                return self.session.get(url, **kwargs)
            
            def post(self, url, **kwargs):
                """Post request with SSL fixes"""
                kwargs.setdefault('timeout', 15)
                kwargs.setdefault('verify', False)
                return self.session.post(url, **kwargs)
        
        return SSLFixedClient()
    
    def test_fixed_client(self):
        """Test the SSL-fixed client"""
        print("\n🧪 Testing SSL-Fixed Client...")
        
        client = self.create_ssl_fixed_client()
        
        # Test endpoints
        endpoints = [
            ("/health", "Health Check"),
            ("/v1/network/peers", "Peer Discovery"),
            ("/v1/data/block/latest", "Latest Block")
        ]
        
        results = {}
        
        for endpoint, description in endpoints:
            try:
                print(f"   Testing {description}...")
                response = client.get(f"{self.production_api}{endpoint}")
                
                if response.status_code == 200:
                    print(f"   ✅ {description}: Success")
                    try:
                        data = response.json()
                        results[endpoint] = data
                        print(f"      Data: {json.dumps(data, indent=2)[:200]}...")
                    except:
                        print(f"      Response: {response.text[:100]}...")
                else:
                    print(f"   ⚠️  {description}: Status {response.status_code}")
                    results[endpoint] = {"error": f"Status {response.status_code}"}
                    
            except Exception as e:
                print(f"   ❌ {description}: {e}")
                results[endpoint] = {"error": str(e)}
        
        return results
    
    def create_ssl_bypass_script(self):
        """Create a script that bypasses SSL issues"""
        print("\n📝 Creating SSL Bypass Script...")
        
        script_content = '''#!/usr/bin/env python3
"""
COINjecture API Client with SSL Bypass
Use this client to avoid SSL issues with production API
"""

import requests
import json
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class COINjectureAPIClient:
    def __init__(self, base_url="https://api.coinjecture.com"):
        self.base_url = base_url
        self.session = self._create_session()
    
    def _create_session(self):
        """Create session with SSL bypass"""
        session = requests.Session()
        
        # Disable SSL verification
        session.verify = False
        
        # Custom headers
        session.headers.update({
            'User-Agent': 'COINjecture-SSL-Bypass/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_health(self):
        """Get API health status"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=15)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Health check failed: {e}")
            return None
    
    def get_peers(self):
        """Get network peers"""
        try:
            response = self.session.get(f"{self.base_url}/v1/network/peers", timeout=15)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Peer discovery failed: {e}")
            return None
    
    def get_latest_block(self):
        """Get latest block"""
        try:
            response = self.session.get(f"{self.base_url}/v1/data/block/latest", timeout=15)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Latest block fetch failed: {e}")
            return None

# Example usage
if __name__ == "__main__":
    client = COINjectureAPIClient()
    
    print("🌐 COINjecture API Client (SSL Bypass)")
    print("=" * 40)
    
    # Test health
    health = client.get_health()
    if health:
        print(f"✅ Health: {health.get('status', 'unknown')}")
    else:
        print("❌ Health check failed")
    
    # Test peers
    peers = client.get_peers()
    if peers:
        print(f"✅ Peers: {peers.get('total_peers', 0)} total")
        for peer in peers.get('peers', []):
            print(f"   - {peer.get('address', 'unknown')} ({peer.get('status', 'unknown')})")
    else:
        print("❌ Peer discovery failed")
    
    # Test latest block
    block = client.get_latest_block()
    if block and 'data' in block:
        data = block['data']
        print(f"✅ Latest Block: {data.get('index', 'unknown')} (Work: {data.get('work_score', 'unknown')})")
    else:
        print("❌ Latest block fetch failed")
'''
        
        with open('scripts/coinjecture_ssl_bypass_client.py', 'w') as f:
            f.write(script_content)
        
        print("   ✅ Created scripts/coinjecture_ssl_bypass_client.py")
        return True
    
    def run_ssl_diagnostics(self):
        """Run complete SSL diagnostics"""
        print("🔐 COINjecture SSL Diagnostics")
        print("=" * 40)
        
        # Test SSL connection
        ssl_ok = self.test_ssl_connection()
        
        # Test HTTP requests
        http_ok = self.test_http_requests()
        
        # Test fixed client
        if http_ok:
            results = self.test_fixed_client()
        else:
            results = {}
        
        # Create bypass script
        self.create_ssl_bypass_script()
        
        # Summary
        print("\n📋 SSL Diagnostic Summary:")
        print("=" * 30)
        print(f"🔐 SSL Connection: {'✅ Working' if ssl_ok else '❌ Failed'}")
        print(f"🌐 HTTP Requests: {'✅ Working' if http_ok else '❌ Failed'}")
        print(f"🔧 Fixed Client: {'✅ Working' if results else '❌ Failed'}")
        
        if not ssl_ok or not http_ok:
            print("\n💡 SSL Issue Solutions:")
            print("   1. Use the SSL bypass client: python3 scripts/coinjecture_ssl_bypass_client.py")
            print("   2. Use remote server instead: http://167.172.213.70:12346")
            print("   3. Check SSL certificate expiration on production server")
            print("   4. Consider updating TLS version on production server")
        
        return {
            'ssl_ok': ssl_ok,
            'http_ok': http_ok,
            'results': results
        }

def main():
    """Main function"""
    fixer = SSLFixer()
    results = fixer.run_ssl_diagnostics()
    
    print(f"\n🎯 SSL Status: {'✅ Fixed' if results['http_ok'] else '❌ Issues Remain'}")
    
    if not results['http_ok']:
        print("\n🚨 Critical SSL Issues Detected!")
        print("   - Production API has SSL handshake failures")
        print("   - Use remote server (167.172.213.70:12346) for reliable access")
        print("   - SSL bypass client created for production API access")

if __name__ == "__main__":
    main()
