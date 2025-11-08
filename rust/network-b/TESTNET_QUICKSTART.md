# COINjecture Network B Testnet - Quick Start

**Status**: 🟢 LIVE
**Launch**: January 8, 2025
**Testnet ID**: coinject-testnet-b1

---

## 🚀 Launch Validator 1 (Genesis Node) NOW!

### Option 1: Windows Batch Script (Easiest)

```bash
cd rust/network-b/testnet
start-validator1.bat
```

### Option 2: Command Line

```bash
cd rust/network-b
target/release/coinject.exe \
  --data-dir testnet/validator1/data \
  --dev \
  --mine \
  --miner-address 0000000000000000000000000000000000000000000000000000000000000001 \
  --difficulty 2 \
  --block-time 30 \
  --chain-id coinject-testnet-b1 \
  -v
```

---

## ✅ Expected Output

```
╔═══════════════════════════════════════════════════════════════╗
║                    COINjecture Network B                      ║
║                    Network B - NP-Hard Consensus              ║
╚═══════════════════════════════════════════════════════════════╝

🚀 Initializing COINjecture Network B Node...

📦 Loading genesis block...
   Genesis hash: Hash(3fadfa4fa4b6d8d7)

⛓️  Initializing blockchain state...
   Best height: 0

💰 Initializing account state...
   Applying genesis block to state...
   Genesis account funded with 21000000000000000 tokens

⛏️  Initializing miner...
   Miner address: 0000000000000000000000000000000000000000000000000000000000000001

🌐 Starting P2P network...
Network node PeerID: 12D3KooWJqWxV8RuUkJMr1MSySrwQBaVe6phJm4otG8tMDTrgxtK
   Listening on: /ip4/0.0.0.0/tcp/30333

🔌 Starting JSON-RPC server...
   RPC listening on: 127.0.0.1:9933

✅ Node is ready!

⛏️  Mining block 1...
Generated problem: TSP { cities: 11, distances: [...] }
Solved in 4.6µs using 88 bytes
Work score: 0.0007762
```

---

## 🎯 Testnet Info

**You just launched the genesis validator!**

- **Genesis Supply**: 21,000,000 BEANS (all credited to validator 1)
- **Your Address**: `0x0000000000000000000000000000000000000000000000000000000000000001`
- **RPC Endpoint**: http://localhost:9933
- **Peer ID**: Copy from your console output above

---

## 📡 Test the RPC API

### Get Your Balance

```bash
curl -X POST http://localhost:9933 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "account_getBalance",
    "params": ["0000000000000000000000000000000000000000000000000000000000000001"],
    "id": 1
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": 21000000000000000
}
```

### Get Chain Info

```bash
curl -X POST http://localhost:9933 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "chain_getInfo",
    "params": [],
    "id": 1
  }'
```

---

## 🌐 Add More Validators

### Step 1: Copy Your Peer ID

From validator 1 output, find the line:
```
Network node PeerId: 12D3KooWJqWxV8RuUkJMr1MSySrwQBaVe6phJm4otG8tMDTrgxtK
```

### Step 2: Update start-validator2.bat

Edit `testnet/start-validator2.bat`:
```batch
REM Replace PEER_ID_1 with your actual peer ID:
set BOOTNODE=/ip4/127.0.0.1/tcp/30333/p2p/12D3KooWJqWxV8RuUkJMr1MSySrwQBaVe6phJm4otG8tMDTrgxtK
```

### Step 3: Launch Validator 2

Open a NEW terminal window:
```bash
cd rust/network-b/testnet
start-validator2.bat
```

You should see:
```
🤝 Peer connected: 12D3KooW...   (Validator 1)
```

---

## 🎮 What's Happening?

1. **Genesis Block**: Created at height 0 with 21M BEANS
2. **Mining**: Your node is solving NP-hard problems (SAT, TSP, SubsetSum)
3. **Blocks**: New block every ~30 seconds
4. **P2P**: Waiting for peers to connect (bootnodes or manual)
5. **RPC**: API server ready for wallet integration

---

## 🔥 Next Steps

1. **Let it run** for a few minutes to mine some blocks
2. **Check the RPC** to verify it's working
3. **Launch validator 2** to create a real network
4. **Submit transactions** via RPC (see [testnet/README.md](testnet/README.md))
5. **Use the marketplace** to submit bounty problems

---

## 📊 Monitor Your Node

```bash
# Watch block height increase
watch -n 5 'curl -s -X POST http://localhost:9933 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"chain_getInfo\",\"params\":[],\"id\":1}" | jq ".result.best_height"'
```

---

## 🛑 Stop the Node

Press `Ctrl+C` in the terminal running the node.

---

## 🐛 Troubleshooting

**Node won't start:**
- Check if port 30333 (P2P) or 9933 (RPC) is already in use
- Delete `testnet/validator1/data` and try again

**No blocks being mined:**
- This is normal! NP-hard problems can take time to solve
- Wait up to 60 seconds for the first block

**RPC not responding:**
- Make sure the node started successfully
- Check firewall isn't blocking port 9933

---

## 📚 Full Documentation

See [testnet/README.md](testnet/README.md) for:
- Complete RPC API reference
- Multi-validator setup guide
- Transaction submission examples
- Marketplace usage
- Troubleshooting guide

---

**Testnet Status**: 🟢 Active
**Support**: https://github.com/Quigles1337/COINjecture1337-REFACTOR/issues
