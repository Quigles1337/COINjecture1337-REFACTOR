# Node 1 - Bootnode & Miner
Write-Host "Starting Network B Node 1 (Bootnode + Miner)..." -ForegroundColor Cyan
Write-Host ""

# Create data directory
if (-not (Test-Path "testnet\node1")) {
    New-Item -ItemType Directory -Path "testnet\node1" | Out-Null
}

# Run node
& ".\target\release\coinject.exe" `
  --data-dir "testnet/node1" `
  --p2p-addr "/ip4/0.0.0.0/tcp/30333" `
  --rpc-addr "127.0.0.1:9933" `
  --mine `
  --difficulty 3 `
  --block-time 30
