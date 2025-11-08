@echo off
REM COINjecture Network B - Validator 2 Startup Script
REM IMPORTANT: Replace PEER_ID_1 below with actual peer ID from validator 1 logs

echo ====================================
echo COINjecture Network B - Validator 2
echo Testnet B1
echo ====================================
echo.
echo IMPORTANT: Update PEER_ID_1 in this script with the actual peer ID from validator 1!
echo.

cd /d "%~dp0.."

echo Starting validator 2...
echo Data directory: testnet\validator2\data
echo RPC endpoint: http://localhost:9934
echo P2P endpoint: tcp://0.0.0.0:30334
echo.

REM TODO: Replace PEER_ID_1 with the actual peer ID from validator 1 logs
set BOOTNODE=/ip4/127.0.0.1/tcp/30333/p2p/PEER_ID_1

target\release\coinject.exe ^
  --data-dir testnet/validator2/data ^
  --mine ^
  --miner-address 0000000000000000000000000000000000000000000000000000000000000002 ^
  --difficulty 2 ^
  --block-time 30 ^
  --chain-id coinject-testnet-b1 ^
  --p2p-addr /ip4/0.0.0.0/tcp/30334 ^
  --rpc-addr 127.0.0.1:9934 ^
  --bootnodes %BOOTNODE% ^
  -v

echo.
echo Validator 2 stopped.
pause
