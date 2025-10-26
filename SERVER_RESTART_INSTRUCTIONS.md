# Server Restart Instructions for CID Generation Fix

## 🎯 Current Status

✅ **Local Development**: All CID generation fixes implemented and tested
✅ **API Code**: New `/v1/ipfs/<cid>` endpoint added
✅ **Frontend**: Download functionality implemented
✅ **Dependencies**: base58 library added to requirements.txt

❌ **Server**: Needs restart to load new code
❌ **CIDs**: Still using old invalid format until restart

## 🚀 Required Actions

### 1. Deploy Updated Code to Server

The following files need to be deployed to the server:

```bash
# Core blockchain CID generation fixes
src/core/blockchain.py

# CLI CID generation fixes  
src/cli.py

# New API endpoint
src/api/faucet_server_cors_fixed.py

# Updated dependencies
requirements.txt

# Frontend download functionality
web/app.js
```

### 2. Install Dependencies on Server

```bash
# SSH to server
ssh root@167.172.213.70

# Install base58 library
pip install base58>=2.1.1

# Or update requirements
pip install -r requirements.txt
```

### 3. Restart API Server

```bash
# Stop current server
pkill -f "python.*faucet_server_cors_fixed.py"

# Start server with new code
cd /path/to/coinjecture
python3 src/api/faucet_server_cors_fixed.py &

# Verify server is running
curl http://167.172.213.70:12346/health
```

### 4. Test New System

After restart, run the test script:

```bash
python3 scripts/test_complete_system.py
```

Expected results:
- ✅ CID Generation: PASS
- ✅ API Health: PASS  
- ✅ IPFS Endpoint: PASS (new endpoint working)
- ✅ CID Format: PASS (new CIDs generated)
- ✅ Fresh Export: PASS

## 🔧 What Will Happen After Restart

### New CID Generation
- All new blocks will have valid base58btc CIDs (46 characters)
- CIDs will be properly formatted for IPFS
- Old invalid CIDs will remain in historical data

### New API Endpoint
- `/v1/ipfs/<cid>` will serve proof bundle JSON
- Returns complete block data with problem/solution data
- CORS enabled for frontend access

### Frontend Download
- CID links will download JSON instead of opening IPFS gateway
- Users can download proof bundle data directly
- Better user experience for researchers

### Kaggle Export
- Fresh export will capture new valid CIDs
- Dataset will be ready for research
- All CIDs will be valid base58btc format

## 📊 Expected Results

After server restart:

1. **New Blocks**: Will have valid CIDs like `Qmb8AoHc21bb9g5NEHbCHXEqq4u6a4wndV7tMCf1FotsDs`
2. **API Endpoint**: `/v1/ipfs/<cid>` will return proof bundle JSON
3. **Frontend**: CID clicks will download JSON files
4. **Export**: Fresh Kaggle dataset with valid CIDs

## 🎯 Next Steps

1. **Deploy Code**: Upload updated files to server
2. **Install Dependencies**: Install base58 library
3. **Restart Server**: Restart API server to load new code
4. **Test System**: Run complete system test
5. **Export Data**: Create fresh Kaggle export with valid CIDs
6. **Verify Frontend**: Test download functionality

## 🚨 Important Notes

- **Historical Data**: Old blocks will keep their invalid CIDs
- **New Blocks**: Only new blocks will have valid CIDs
- **IPFS Ready**: System ready for real IPFS when daemon available
- **Backward Compatible**: Old CIDs will still work in existing system

The system is ready for production once the server is restarted! 🚀
