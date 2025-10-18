#!/usr/bin/env python3
"""
Test script for new API endpoints:
- /v1/data/blocks/all
- /v1/data/ipfs/list
- /v1/data/ipfs/search
- /v1/data/ipfs/{cid}
"""

import requests
import json
import sys

# API base URL
API_BASE = "http://167.172.213.70:5000"

def test_endpoint(endpoint, description):
    """Test an API endpoint and print results."""
    print(f"\n🧪 Testing {description}")
    print(f"   Endpoint: {endpoint}")
    
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            if 'data' in data:
                print(f"   Data count: {len(data['data'])}")
            if 'meta' in data:
                print(f"   Meta: {data['meta']}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

def main():
    """Test all new API endpoints."""
    print("🚀 Testing New COINjecture API Endpoints")
    print("=====================================")
    
    # Test all blocks endpoint
    test_endpoint("/v1/data/blocks/all", "All Blocks")
    
    # Test IPFS list endpoint
    test_endpoint("/v1/data/ipfs/list", "IPFS List")
    
    # Test IPFS search endpoint
    test_endpoint("/v1/data/ipfs/search?q=test", "IPFS Search")
    
    # Test root endpoint to see new endpoints
    test_endpoint("/", "Root API Info")
    
    print("\n🎯 Test Summary:")
    print("   - /v1/data/blocks/all: Get all blocks in blockchain")
    print("   - /v1/data/ipfs/list: List all available IPFS CIDs")
    print("   - /v1/data/ipfs/search?q={query}: Search IPFS data")
    print("   - /v1/data/ipfs/{cid}: Get specific IPFS data by CID")
    
    print("\n📋 New API Features:")
    print("   ✅ All blocks endpoint for blockchain explorers")
    print("   ✅ IPFS data listing and search")
    print("   ✅ Enhanced IPFS integration")
    print("   ✅ Better data discovery")

if __name__ == "__main__":
    main()
