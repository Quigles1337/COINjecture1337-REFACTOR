#!/usr/bin/env python3
"""
Network API Fallback System
Provides reliable API access when production API has SSL issues
"""

import requests
import json
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class NetworkAPIFallback:
    def __init__(self):
        self.primary_api = "https://api.coinjecture.com"  # SSL issues
        self.remote_api = "http://167.172.213.70:12346"   # Working
        self.session = self._create_session()
        
    def _create_session(self):
        """Create robust session with retry logic"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': 'COINjecture-Fallback/1.0',
            'Accept': 'application/json'
        })
        
        return session
    
    def get_health(self):
        """Get health status with fallback"""
        print("🔍 Getting API health...")
        
        # Try remote API first (reliable)
        try:
            response = self.session.get(f"{self.remote_api}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Remote API Health: {data.get('status', 'unknown')}")
                print(f"   📊 Peers Connected: {data.get('peers_connected', 0)}")
                print(f"   📊 Latest Block: {data.get('latest_block_height', 0)}")
                return data
        except Exception as e:
            print(f"❌ Remote API failed: {e}")
        
        # Try production API (has SSL issues)
        try:
            response = self.session.get(f"{self.primary_api}/health", timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Production API Health: {data.get('status', 'unknown')}")
                return data
        except Exception as e:
            print(f"❌ Production API failed: {e}")
        
        return None
    
    def get_peers(self):
        """Get network peers with fallback"""
        print("\n🔍 Getting network peers...")
        
        # Try remote API first
        try:
            response = self.session.get(f"{self.remote_api}/v1/network/peers", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Remote API Peers: {data.get('total_peers', 0)} total")
                print("   📋 Active Peers:")
                for peer in data.get('peers', []):
                    print(f"     - {peer.get('address', 'unknown')} ({peer.get('status', 'unknown')})")
                return data
        except Exception as e:
            print(f"❌ Remote API peers failed: {e}")
        
        # Try production API
        try:
            response = self.session.get(f"{self.primary_api}/v1/network/peers", timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Production API Peers: {data.get('total_peers', 0)} total")
                return data
        except Exception as e:
            print(f"❌ Production API peers failed: {e}")
        
        return None
    
    def get_latest_block(self):
        """Get latest block with fallback"""
        print("\n🔍 Getting latest block...")
        
        # Try remote API first
        try:
            response = self.session.get(f"{self.remote_api}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    block = data['data']
                    print(f"✅ Remote API Latest Block:")
                    print(f"   📦 Index: {block.get('index', 'unknown')}")
                    print(f"   🔗 Hash: {block.get('block_hash', 'unknown')[:16]}...")
                    print(f"   ⚡ Work Score: {block.get('work_score', 'unknown')}")
                    print(f"   💰 Reward: {block.get('reward', 'unknown')}")
                    return data
        except Exception as e:
            print(f"❌ Remote API latest block failed: {e}")
        
        # Try production API
        try:
            response = self.session.get(f"{self.primary_api}/v1/data/block/latest", timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Production API Latest Block: {data.get('data', {}).get('index', 'unknown')}")
                return data
        except Exception as e:
            print(f"❌ Production API latest block failed: {e}")
        
        return None
    
    def get_network_summary(self):
        """Get comprehensive network summary"""
        print("\n📊 Network Summary:")
        print("=" * 40)
        
        # Get all data
        health = self.get_health()
        peers = self.get_peers()
        block = self.get_latest_block()
        
        # Summary
        print("\n📋 Summary:")
        print("=" * 20)
        
        if health:
            print(f"✅ API Status: {health.get('status', 'unknown')}")
            print(f"✅ Database: {health.get('database', 'unknown')}")
            print(f"✅ Network ID: {health.get('network_id', 'unknown')}")
            print(f"✅ Peers Connected: {health.get('peers_connected', 0)}")
            print(f"✅ Latest Block: {health.get('latest_block_height', 0)}")
        else:
            print("❌ API Status: Unavailable")
        
        if peers:
            print(f"✅ Active Peers: {peers.get('total_peers', 0)}")
        else:
            print("❌ Active Peers: Unavailable")
        
        if block and 'data' in block:
            block_data = block['data']
            print(f"✅ Latest Block: {block_data.get('index', 'unknown')}")
            print(f"✅ Work Score: {block_data.get('work_score', 'unknown')}")
        else:
            print("❌ Latest Block: Unavailable")
        
        return {
            'health': health,
            'peers': peers,
            'block': block
        }
    
    def run_diagnostics(self):
        """Run complete network diagnostics"""
        print("🌐 COINjecture Network API Fallback System")
        print("=" * 50)
        
        # Test all endpoints
        results = self.get_network_summary()
        
        # Determine working API
        working_api = None
        if results['health']:
            if 'peers_connected' in results['health']:
                working_api = "Remote API (167.172.213.70:12346)"
            else:
                working_api = "Production API (api.coinjecture.com)"
        
        print(f"\n🎯 Working API: {working_api if working_api else 'None'}")
        
        if not working_api:
            print("\n🚨 All APIs Failed!")
            print("   - Remote API: Connection issues")
            print("   - Production API: SSL handshake failures")
            print("   - Check network connectivity")
        else:
            print(f"\n✅ Network Status: Healthy via {working_api}")
        
        return results

def main():
    """Main function"""
    fallback = NetworkAPIFallback()
    results = fallback.run_diagnostics()
    
    print(f"\n🎯 Final Status: {'✅ Working' if results['health'] else '❌ Failed'}")

if __name__ == "__main__":
    main()
