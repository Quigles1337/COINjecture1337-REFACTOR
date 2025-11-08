# Quick Start: 3-Node Testnet

## Step 1: Build the Node

```bash
cargo build --release
```

Wait for the build to complete (~2-5 minutes).

## Step 2: Start the Nodes

**IMPORTANT:** Use **PowerShell** or **CMD**, NOT Git Bash (Git Bash converts `/ip4` paths incorrectly on Windows)

Open **3 separate PowerShell windows** and run:

### Terminal 1 - Node 1 (Bootnode + Miner)
```powershell
.\test-node1.ps1
```
Or with CMD:
```cmd
test-node1.bat
```

### Terminal 2 - Node 2 (Miner)
```powershell
.\test-node2.ps1
```
Or with CMD:
```cmd
test-node2.bat
```

### Terminal 3 - Node 3 (Validator)
```powershell
.\test-node3.ps1
```
Or with CMD:
```cmd
test-node3.bat
```

## Step 3: Watch for Success Indicators

### Within 10 seconds, you should see:

**Peer Discovery:**
```
mDNS discovered peer: <PeerId> at /ip4/...
Connection established with peer: <PeerId>
🤝 Peer connected: <PeerId>
```

**Status Broadcasting (every 10 seconds):**
```
📊 Status update from <PeerId>: height X (ours: Y)
```

**Mining (every ~30 seconds on nodes 1 & 2):**
```
⛏️  Mining block 1...
🎉 Mined new block 1!
📡 Broadcasted block to network
```

**Block Propagation:**
```
📥 Received block 1 from <PeerId>
✅ Block accepted and applied to chain
```

**Chain Synchronization:**
```
🔄 Peer is ahead! Requesting blocks X-Y for sync
📮 Blocks requested by <PeerId>: heights X-Y
📤 Sent N blocks in response to sync request
```

## Step 4: Verify Consensus

After 2-3 minutes, all nodes should:
- Have the same chain height
- Be connected to 2 peers each
- Show block propagation messages

### Check Chain Info (RPC)

```bash
# Check Node 1
curl -X POST http://127.0.0.1:9933 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"chain_getInfo\",\"params\":[],\"id\":1}"

# Check Node 2
curl -X POST http://127.0.0.1:9934 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"chain_getInfo\",\"params\":[],\"id\":1}"

# Check Node 3
curl -X POST http://127.0.0.1:9935 -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"chain_getInfo\",\"params\":[],\"id\":1}"
```

All should show the same `best_height`.

## Step 5: Test Transaction Broadcasting (Optional)

### Create Accounts
```bash
target\release\coinject-wallet.exe account new --name alice
target\release\coinject-wallet.exe account new --name bob
```

### Get Genesis Address Balance
The genesis account has initial tokens. Check balance:
```bash
target\release\coinject-wallet.exe --rpc http://127.0.0.1:9933 account balance <genesis-address>
```

### Send Transaction
```bash
target\release\coinject-wallet.exe --rpc http://127.0.0.1:9933 transaction send --from <account> --to <bob-address> --amount 1000
```

Watch all node terminals for:
```
📨 Received transaction <hash> from <PeerId>
✅ Added transaction <hash> to pool
```

## Step 6: Stop the Testnet

Press `Ctrl+C` in each terminal window.

## Step 7: Clean Up

```bash
clean-testnet.bat
```

This removes all testnet data.

## What Success Looks Like

✅ **All nodes discover each other** (< 10 seconds)
✅ **Status broadcasts every 10 seconds** from all peers
✅ **Miners produce blocks** (~30 seconds apart)
✅ **Blocks propagate** to all nodes
✅ **All nodes stay synchronized** (same height)
✅ **Late-joining nodes sync** from peers
✅ **Transactions broadcast** to all nodes (if tested)

## Common Issues

### Nodes not discovering each other
- Wait 10-15 seconds (mDNS can be slow)
- Check firewall isn't blocking ports 30333-30335
- Ensure no other processes using those ports

### Build fails
- Make sure Rust is up to date: `rustup update`
- Clean and rebuild: `cargo clean && cargo build --release`

### Mining too slow
- Lower difficulty: change `--difficulty 3` to `--difficulty 2` in scripts
- Lower block time: change `--block-time 30` to `--block-time 20`

## Next Steps After Successful Test

1. ✅ Confirm P2P networking works
2. ✅ Validate consensus mechanism
3. 🚀 Ready for COINjecture backend integration!
