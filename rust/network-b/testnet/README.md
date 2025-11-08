# COINjecture Network B Testnet

**Testnet Name**: coinject-testnet-b1
**Launch Date**: 2025-01-08
**Consensus**: NP-Hard Proof-of-Work (SubsetSum, SAT, TSP)
**Total Supply**: 21,000,000 BEANS
**Tokenomics**: η = 1/√2 decay model

---

## Quick Start

### Launch Validator 1 (Genesis Node)

```bash
# From rust/network-b directory
../target/release/coinject.exe \
  --data-dir ./testnet/validator1/data \
  --dev \
  --mine \
  --miner-address 0000000000000000000000000000000000000000000000000000000000000001 \
  --difficulty 2 \
  --block-time 30 \
  --chain-id coinject-testnet-b1
```

**Expected Output:**
```
╔═══════════════════════════════════════════════════════════════╗
║                    COINjecture Network B                      ║
║                    Network B - NP-Hard Consensus              ║
╚═══════════════════════════════════════════════════════════════╝

🔧 Initializing node...
📦 Loading genesis block...
   Genesis block created (height: 0)
💰 Initializing account state...
   Genesis account funded with 21000000000000000 tokens
🌐 Starting P2P network...
   Listening on /ip4/0.0.0.0/tcp/30333
   Peer ID: 12D3KooWEyoppNCUx8Yx66oV9fJnriXwCcXwDDUA2kj6vnc6iDEp
🔌 Starting JSON-RPC server...
   JSON-RPC server listening on 127.0.0.1:9933
⛏️  Mining enabled (target block time: 30s)

✅ Node started successfully!
```

### Launch Additional Validators

**Validator 2:**
```bash
../target/release/coinject.exe \
  --data-dir ./testnet/validator2/data \
  --mine \
  --miner-address 0000000000000000000000000000000000000000000000000000000000000002 \
  --difficulty 2 \
  --block-time 30 \
  --chain-id coinject-testnet-b1 \
  --p2p-addr /ip4/0.0.0.0/tcp/30334 \
  --rpc-addr 127.0.0.1:9934 \
  --bootnodes /ip4/127.0.0.1/tcp/30333/p2p/PEER_ID_FROM_VALIDATOR1
```

**Validator 3:**
```bash
../target/release/coinject.exe \
  --data-dir ./testnet/validator3/data \
  --mine \
  --miner-address 0000000000000000000000000000000000000000000000000000000000000003 \
  --difficulty 2 \
  --block-time 30 \
  --chain-id coinject-testnet-b1 \
  --p2p-addr /ip4/0.0.0.0/tcp/30335 \
  --rpc-addr 127.0.0.1:9935 \
  --bootnodes /ip4/127.0.0.1/tcp/30333/p2p/PEER_ID_FROM_VALIDATOR1
```

---

## Testnet Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Chain ID** | coinject-testnet-b1 | Network identifier |
| **Genesis Supply** | 21,000,000 BEANS | Initial token supply (with 9 decimals) |
| **Genesis Address** | 0x000...001 | Validator 1 receives initial supply |
| **Difficulty** | 2 | Leading zeros in block hash (low for testing) |
| **Block Time** | 30s | Target time between blocks |
| **Consensus** | NP-Hard PoW | SubsetSum, SAT, TSP problem solving |

---

## Validator Addresses

| Validator | Address | RPC Port | P2P Port |
|-----------|---------|----------|----------|
| **Validator 1** | 0x000...001 | 9933 | 30333 |
| **Validator 2** | 0x000...002 | 9934 | 30334 |
| **Validator 3** | 0x000...003 | 9935 | 30335 |

---

## RPC API Endpoints

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

### Get Account Balance
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

### Get Latest Block
```bash
curl -X POST http://localhost:9933 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "chain_getLatestBlock",
    "params": [],
    "id": 1
  }'
```

### Get Open Problems from Marketplace
```bash
curl -X POST http://localhost:9933 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "marketplace_getOpenProblems",
    "params": [],
    "id": 1
  }'
```

---

## Mining

Mining is enabled by default on all validators. The node will:

1. **Collect transactions** from the mempool
2. **Generate NP-hard problem** (SubsetSum, SAT, or TSP)
3. **Create commitment** (commit-reveal protocol)
4. **Solve problem** (may take time based on difficulty)
5. **Build block** with solution and reveal
6. **Gossip block** to network

**Expected Mining Output:**
```
⛏️  Mining block #1...
   Generated SubsetSum problem (16 numbers, target: 42)
   Created commitment: 0x1a2b3c...
   Solving problem... (may take up to 30s)
   ✅ Solution found! [3, 7, 12, 20]
   📦 Block #1 mined (hash: 0x00ab12..., 0 transactions)
   Broadcasting block to network...
```

---

## Monitoring

### Check Node Status
```bash
# Check if node is running
ps aux | grep coinject

# Check logs
tail -f testnet/validator1/data/node.log

# Check block height
curl -s http://localhost:9933 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"chain_getInfo","params":[],"id":1}' \
  | jq '.result.best_height'
```

### Check Network Connectivity
```bash
# Number of connected peers (should be 2 for 3-validator network)
# Via logs:
grep "Peer connected" testnet/validator1/data/node.log | wc -l
```

---

## Troubleshooting

### Node Won't Start

**Error**: `Failed to bind to address`
**Solution**: Port already in use, change `--p2p-addr` or `--rpc-addr`

**Error**: `Failed to load genesis`
**Solution**: Delete `./testnet/validator1/data` and restart

### Mining Not Producing Blocks

**Check**:
1. Is mining enabled? (`--mine` flag)
2. Is miner address set? (`--miner-address`)
3. Check logs for errors

### Peers Not Connecting

**Check**:
1. Correct peer ID in `--bootnodes`
2. Firewall not blocking ports
3. All nodes using same `--chain-id`

---

## Testnet Goals

### Week 1: Stability
- [x] Launch 3 validators
- [ ] Run for 24 hours without crashes
- [ ] Mine 100+ blocks
- [ ] Validate block propagation

### Week 2: Load Testing
- [ ] Submit 1000+ transactions
- [ ] Submit problems to marketplace
- [ ] Test large block (100+ transactions)
- [ ] Measure TPS and latency

### Week 3: Stress Testing
- [ ] Run with 10+ validators
- [ ] Network partitioning tests
- [ ] Block reorg scenarios
- [ ] Performance benchmarking

---

## Data Locations

```
testnet/
├── validator1/
│   └── data/
│       ├── chain.db/       # Block storage
│       ├── state.db/       # Account state
│       └── node.log        # Node logs
├── validator2/
│   └── data/
└── validator3/
    └── data/
```

---

## Support

**Issues**: https://github.com/Quigles1337/COINjecture1337-REFACTOR/issues
**Contact**: adz@alphx.io
**Discord**: TBD

---

**Testnet Status**: 🟢 Active
**Genesis Block**: January 8, 2025 00:00:00 UTC
