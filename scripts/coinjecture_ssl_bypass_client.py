#!/usr/bin/env python3
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
