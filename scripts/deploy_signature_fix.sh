#!/bin/bash
# Deploy signature validation fix to remote server

echo "🔧 Deploying signature validation fix..."

# Copy the fixed wallet.py to remote server
echo "📤 Copying fixed wallet.py to remote server..."
scp /tmp/wallet_fixed.py coinjecture@167.172.213.70:/tmp/wallet_fixed.py

# Execute remote commands to apply the fix
echo "🚀 Applying fix on remote server..."
ssh coinjecture@167.172.213.70 << 'EOF'
    echo "📁 Backing up original wallet.py..."
    cp /home/coinjecture/COINjecture/src/tokenomics/wallet.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py.backup
    
    echo "🔄 Replacing with fixed wallet.py..."
    cp /tmp/wallet_fixed.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py
    
    echo "🔄 Restarting API service..."
    sudo systemctl restart coinjecture-api.service
    
    echo "✅ Signature validation fix applied!"
    echo "📊 Checking API status..."
    sudo systemctl status coinjecture-api.service --no-pager -l
EOF

echo "✅ Signature validation fix deployed!"
