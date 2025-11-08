# Node 3 - Validator Only
Write-Host "Starting Network B Node 3 (Validator)..." -ForegroundColor Cyan
Write-Host ""

# Create data directory
if (-not (Test-Path "testnet\node3")) {
    New-Item -ItemType Directory -Path "testnet\node3" | Out-Null
}

# Run node
& ".\target\release\coinject.exe" `
  --data-dir "testnet/node3" `
  --p2p-addr "/ip4/0.0.0.0/tcp/30335" `
  --rpc-addr "127.0.0.1:9935" `
  --difficulty 3 `
  --block-time 30
