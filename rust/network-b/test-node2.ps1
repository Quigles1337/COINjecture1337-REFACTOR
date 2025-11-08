# Node 2 - Miner
Write-Host "Starting Network B Node 2 (Miner)..." -ForegroundColor Cyan
Write-Host ""

# Create data directory
if (-not (Test-Path "testnet\node2")) {
    New-Item -ItemType Directory -Path "testnet\node2" | Out-Null
}

# Run node
& ".\target\release\coinject.exe" `
  --data-dir "testnet/node2" `
  --p2p-addr "/ip4/0.0.0.0/tcp/30334" `
  --rpc-addr "127.0.0.1:9934" `
  --mine `
  --difficulty 3 `
  --block-time 30
