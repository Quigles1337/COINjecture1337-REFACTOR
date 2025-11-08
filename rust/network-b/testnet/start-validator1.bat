@echo off
REM COINjecture Network B - Validator 1 Startup Script
REM Genesis validator for testnet-b1

echo ====================================
echo COINjecture Network B - Validator 1
echo Genesis Node for Testnet B1
echo ====================================
echo.

cd /d "%~dp0.."

echo Starting validator 1...
echo Data directory: testnet\validator1\data
echo RPC endpoint: http://localhost:9933
echo P2P endpoint: tcp://0.0.0.0:30333
echo.

target\release\coinject.exe ^
  --data-dir testnet/validator1/data ^
  --dev ^
  --mine ^
  --miner-address 0000000000000000000000000000000000000000000000000000000000000001 ^
  --difficulty 2 ^
  --block-time 30 ^
  --chain-id coinject-testnet-b1 ^
  --p2p-addr /ip4/0.0.0.0/tcp/30333 ^
  --rpc-addr 127.0.0.1:9933 ^
  -v

echo.
echo Validator 1 stopped.
pause
