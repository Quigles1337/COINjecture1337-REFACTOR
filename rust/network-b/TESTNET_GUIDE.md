# Network B Multi-Node Testnet Guide

## Overview

This guide explains how to run a local multi-node testnet for COINjecture Network B to test P2P networking, consensus, and transaction propagation.

## Prerequisites

```bash
# Build the node in release mode
cd rust/network-b
cargo build --release
```

The compiled binaries will be in `target/release/`:
- `coinject` - Node binary
- `coinject-wallet` - Wallet CLI

## Quick Start: 3-Node Testnet

### Node 1 (Bootnode & Miner)

```bash
./target/release/coinject \
  --data-dir ./testnet/node1 \
  --p2p-addr "/ip4/0.0.0.0/tcp/30333" \
  --rpc-addr "127.0.0.1:9933" \
  --mine \
  --difficulty 3 \
  --block-time 30
```

### Node 2 (Miner)

```bash
./target/release/coinject \
  --data-dir ./testnet/node2 \
  --p2p-addr "/ip4/0.0.0.0/tcp/30334" \
  --rpc-addr "127.0.0.1:9934" \
  --mine \
  --difficulty 3 \
  --block-time 30
```

### Node 3 (Validator Only)

```bash
./target/release/coinject \
  --data-dir ./testnet/node3 \
  --p2p-addr "/ip4/0.0.0.0/tcp/30335" \
  --rpc-addr "127.0.0.1:9935" \
  --difficulty 3 \
  --block-time 30
```

## Peer Discovery

Nodes automatically discover each other via:
- **mDNS** - Local network peer discovery (automatic on same machine/LAN)
- **Kademlia DHT** - Distributed peer routing
- **Gossipsub** - Message propagation

On the same machine, nodes will discover each other automatically via mDNS within seconds.

## Configuration Options

| Flag | Description | Default |
|------|-------------|---------|
| `--data-dir` | Blockchain data directory | `./data` |
| `--p2p-addr` | P2P listen address (multiaddr) | `/ip4/0.0.0.0/tcp/30333` |
| `--rpc-addr` | JSON-RPC listen address | `127.0.0.1:9933` |
| `--mine` | Enable mining | `false` |
| `--miner-address` | Miner reward address (hex, 64 chars) | Uses genesis address |
| `--difficulty` | Mining difficulty (1-64) | `4` |
| `--block-time` | Target block time (seconds) | `60` |
| `--chain-id` | Chain identifier | `coinject-network-b` |
| `--max-peers` | Maximum peer connections | `50` |
| `--verbose` | Enable verbose logging | `false` |

## Monitoring the Testnet

### View Node Status

Each node exposes a JSON-RPC API. Use the wallet CLI or curl:

```bash
# Get chain info (replace port for different nodes)
curl -X POST http://127.0.0.1:9933 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"chain_getInfo","params":[],"id":1}'

# Get latest block
curl -X POST http://127.0.0.1:9933 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"chain_getLatestBlock","params":[],"id":1}'
```

### Using the Wallet CLI

```bash
# Get chain info
./target/release/coinject-wallet --rpc http://127.0.0.1:9933 chain info

# Get latest block
./target/release/coinject-wallet --rpc http://127.0.0.1:9933 chain latest

# Get block by height
./target/release/coinject-wallet --rpc http://127.0.0.1:9933 chain block 10

# Create new account
./target/release/coinject-wallet account new --name alice

# Check balance
./target/release/coinject-wallet --rpc http://127.0.0.1:9933 account balance <address>
```

## What to Observe

### Expected Behavior

1. **Peer Discovery** (< 10 seconds)
   - Nodes should discover each other via mDNS
   - Console shows: `mDNS discovered peer: <PeerId> at <Address>`
   - Console shows: `Connection established with peer: <PeerId>`

2. **Status Broadcasting** (every 10 seconds)
   - Nodes broadcast their chain height
   - Console shows: `📊 Status update from <PeerId>: height X (ours: Y)`

3. **Chain Synchronization**
   - When a node is behind, it requests missing blocks
   - Console shows: `🔄 Peer is ahead! Requesting blocks X-Y for sync`
   - Console shows: `📥 Received block N from <PeerId>`
   - Console shows: `✅ Block accepted and applied to chain`

4. **Mining** (if --mine enabled)
   - Miners produce blocks every ~30 seconds (with difficulty 3)
   - Console shows: `⛏️  Mining block N...`
   - Console shows: `🎉 Mined new block N!`
   - Console shows: `📡 Broadcasted block to network`

5. **Block Propagation**
   - Mined blocks broadcast to all peers
   - Peers validate and add blocks to chain
   - All nodes converge on same chain height

6. **Transaction Propagation** (when transactions submitted)
   - Transactions broadcast via gossipsub
   - Console shows: `📨 Received transaction <hash> from <PeerId>`
   - Transactions added to mempool
   - Miners include transactions in next block

## Testing Scenarios

### Scenario 1: Basic Consensus

1. Start Node 1 (mining)
2. Let it mine 5-10 blocks
3. Start Node 2 (mining)
4. Observe:
   - Node 2 syncs blocks from Node 1
   - Both nodes continue mining
   - Chain heights stay synchronized

### Scenario 2: Late Joiner Sync

1. Start Node 1 & 2 (both mining)
2. Let them mine 20+ blocks
3. Start Node 3 (non-mining)
4. Observe:
   - Node 3 discovers peers
   - Node 3 requests missing blocks
   - Node 3 syncs to current height
   - Node 3 validates incoming blocks

### Scenario 3: Transaction Propagation

1. Start 3 nodes (at least 1 mining)
2. Create accounts using wallet:
   ```bash
   ./target/release/coinject-wallet account new --name alice
   ./target/release/coinject-wallet account new --name bob
   ```
3. Send transaction from node with funds:
   ```bash
   ./target/release/coinject-wallet --rpc http://127.0.0.1:9933 \
     transaction send \
     --from alice \
     --to <bob-address> \
     --amount 1000
   ```
4. Observe:
   - Transaction broadcasts to all nodes
   - Miners include in next block
   - All nodes apply transaction to state

### Scenario 4: Network Partition Recovery

1. Start 3 nodes (all mining)
2. Stop Node 2 (Ctrl+C)
3. Let Node 1 & 3 mine 10 blocks
4. Restart Node 2
5. Observe:
   - Node 2 rejoins network
   - Node 2 syncs missed blocks
   - All nodes converge to same height

## Troubleshooting

### Nodes not discovering each other

- **Check ports**: Ensure P2P ports don't conflict
- **Check firewall**: Allow TCP connections on P2P ports
- **Check logs**: Look for `mDNS discovered peer` messages
- **Wait**: mDNS discovery can take 5-10 seconds

### Nodes not syncing

- **Check status broadcasts**: Should see `📊 Status update` every 10 seconds
- **Check peer connections**: Look for `Connection established` messages
- **Check logs**: Look for `🔄 Requesting blocks` messages
- **Restart nodes**: Sometimes helps reset network state

### Mining not working

- **Check --mine flag**: Must be enabled
- **Check difficulty**: Lower difficulty (2-3) for faster testing
- **Check block time**: Lower to 20-30 seconds for faster testing
- **Wait**: Mining is probabilistic, may take time

### RPC not responding

- **Check RPC address**: Each node needs unique port
- **Check RPC is listening**: Look for `RPC listening on:` in logs
- **Try curl**: Test with raw JSON-RPC calls

## Performance Tuning

For faster testing:
```bash
--difficulty 2 \
--block-time 20 \
--verbose
```

For production-like testing:
```bash
--difficulty 8 \
--block-time 60 \
--max-peers 100
```

## Clean Up

Remove testnet data:
```bash
rm -rf ./testnet/
```

## Advanced: 5-Node Testnet

Run 5 nodes simultaneously for more realistic network testing:

```bash
# Terminal 1
./target/release/coinject --data-dir ./testnet/node1 --p2p-addr "/ip4/0.0.0.0/tcp/30333" --rpc-addr "127.0.0.1:9933" --mine --difficulty 3 --block-time 30

# Terminal 2
./target/release/coinject --data-dir ./testnet/node2 --p2p-addr "/ip4/0.0.0.0/tcp/30334" --rpc-addr "127.0.0.1:9934" --mine --difficulty 3 --block-time 30

# Terminal 3
./target/release/coinject --data-dir ./testnet/node3 --p2p-addr "/ip4/0.0.0.0/tcp/30335" --rpc-addr "127.0.0.1:9935" --mine --difficulty 3 --block-time 30

# Terminal 4
./target/release/coinject --data-dir ./testnet/node4 --p2p-addr "/ip4/0.0.0.0/tcp/30336" --rpc-addr "127.0.0.1:9936" --difficulty 3 --block-time 30

# Terminal 5
./target/release/coinject --data-dir ./testnet/node5 --p2p-addr "/ip4/0.0.0.0/tcp/30337" --rpc-addr "127.0.0.1:9937" --difficulty 3 --block-time 30
```

## Network Features Tested

- ✅ **P2P Networking** - libp2p gossipsub, mDNS, Kademlia DHT
- ✅ **Block Broadcasting** - Mined blocks propagate to all peers
- ✅ **Transaction Broadcasting** - Transactions propagate to all peers
- ✅ **Chain Synchronization** - New nodes sync from peers
- ✅ **Status Announcements** - Periodic height broadcasting
- ✅ **Longest Chain Rule** - Nodes converge on highest chain
- ✅ **Transaction Pool** - Fee-based prioritization
- ✅ **State Management** - Account balances, nonces, transfers
- ✅ **Consensus** - NP-hard proof-of-work mining

## Production Deployment Notes

For production deployment:
1. Use proper miner addresses (generate with wallet)
2. Increase difficulty to 12-16 for security
3. Set realistic block time (60-600 seconds)
4. Configure bootnodes for cross-network discovery
5. Enable firewall rules for P2P ports
6. Use dedicated servers with static IPs
7. Monitor via metrics/Prometheus (future enhancement)
8. Set up log aggregation
9. Configure automated restarts
10. Implement backup strategies

## Next Steps

After successful testnet:
1. Integrate with COINjecture backend
2. Connect marketplace problem submission
3. Add D3 bounty distribution
4. Implement dimensional reward calculation
5. Deploy to public testnet
6. Mainnet launch preparation
