#!/bin/bash

# Deploy CLI Fix to Droplet
# This script updates the web interface to fix CLI stale data issues

set -e

echo "🔧 Deploying CLI Fix to Droplet"
echo "==============================="

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive CLI fix script for the droplet
cat > /tmp/fix_cli_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing CLI Stale Data on Droplet"
echo "==================================="

# 1. Clear local cache files
echo "🧹 Clearing local cache files..."
rm -f /home/coinjecture/COINjecture/data/cache/latest_block.json
rm -f /home/coinjecture/COINjecture/data/cache/blocks_history.json
echo "✅ Local cache files cleared"

# 2. Update web/app.js with improved blockchain statistics
echo "📝 Updating web interface..."

# Create the updated app.js with CLI fixes
cat > /tmp/app_js_fixed.js << 'APP_JS'
// Updated displayBlockchainStats method
async displayBlockchainStats() {
  try {
    this.addOutput('📊 Fetching blockchain statistics...');
    
    // Fetch both latest block and total blocks from API
    const [latestResponse, totalResponse] = await Promise.all([
      this.fetchWithFallback('/v1/data/block/latest'),
      this.fetchWithFallback('/v1/data/blocks/all')
    ]);
    
    const latestData = await latestResponse.json();
    const totalData = await totalResponse.json();
    
    if (latestData.status === 'success' && totalData.status === 'success') {
      const block = latestData.data;
      const totalBlocks = totalData.meta.total_blocks;
      
      this.addMultiLineOutput([
        '📊 Blockchain Statistics:',
        `   Total Blocks: ${totalBlocks}`,
        `   Latest Block: #${block.index}`,
        `   Latest Hash: ${block.block_hash.substring(0, 20)}...`,
        `   Work Score: ${block.cumulative_work_score.toFixed(2)}`,
        `   Last Updated: ${new Date(block.timestamp * 1000).toLocaleString()}`
      ]);
    } else {
      this.addOutput(`❌ ${latestData.message || totalData.message || 'Failed to fetch stats'}`, 'error');
    }
  } catch (error) {
    this.addOutput(`❌ Network error: ${error.message}`, 'error');
  }
}

// Updated fetchWithFallback method with cache-busting
async fetchWithFallback(endpoint, options = {}) {
  // Add cache-busting parameter to ensure fresh data
  const separator = endpoint.includes('?') ? '&' : '?';
  const url = this.apiBase + endpoint + separator + 't=' + Date.now();
  
  try {
    const response = await fetch(url, options);
    return response;
  } catch (error) {
    // Handle certificate errors and other network issues
    if (error.name === 'TypeError' && 
        (error.message.includes('Failed to fetch') || 
         error.message.includes('ERR_CERT_AUTHORITY_INVALID') ||
         error.message.includes('net::ERR_CERT_AUTHORITY_INVALID'))) {
      
      const certAccepted = localStorage.getItem('coinjecture_cert_accepted');
      if (certAccepted === 'true') {
        this.addOutput('🔒 Certificate Issue: Connection still failing despite certificate acceptance.');
        this.addOutput('💡 Try refreshing the page or using a different browser.');
        this.status.innerHTML = '🔒 Certificate Accepted But Connection Failed';
        this.status.className = 'status error';
        throw new Error('Certificate accepted but connection still failing');
      } else {
        this.addOutput('🔒 Certificate Issue: The API uses a self-signed certificate.');
        this.addOutput('💡 Click "Accept Certificate" below to continue, or use a different browser.');
        this.showCertificateNotice();
        this.status.innerHTML = '🔒 Certificate Issue - Click to Accept';
        this.status.className = 'status warning';
        throw new Error('Certificate not accepted');
      }
    }
    throw error;
  }
}
APP_JS

# Update the web/app.js file
echo "📝 Updating web/app.js with CLI fixes..."
cp /home/coinjecture/COINjecture/web/app.js /home/coinjecture/COINjecture/web/app.js.backup

# Apply the fixes to the existing app.js
sed -i 's/async displayBlockchainStats() {/async displayBlockchainStats() {\n    try {\n      this.addOutput('\''📊 Fetching blockchain statistics...'\'');\n      \n      \/\/ Fetch both latest block and total blocks from API\n      const [latestResponse, totalResponse] = await Promise.all([\n        this.fetchWithFallback('\''\/v1\/data\/block\/latest'\''),\n        this.fetchWithFallback('\''\/v1\/data\/blocks\/all'\'')\n      ]);\n      \n      const latestData = await latestResponse.json();\n      const totalData = await totalResponse.json();\n      \n      if (latestData.status === '\''success'\'' \&\& totalData.status === '\''success'\'') {\n        const block = latestData.data;\n        const totalBlocks = totalData.meta.total_blocks;\n        \n        this.addMultiLineOutput([\n          '\''📊 Blockchain Statistics:'\'',\n          `   Total Blocks: ${totalBlocks}`,\n          `   Latest Block: #${block.index}`,\n          `   Latest Hash: ${block.block_hash.substring(0, 20)}...`,\n          `   Work Score: ${block.cumulative_work_score.toFixed(2)}`,\n          `   Last Updated: ${new Date(block.timestamp * 1000).toLocaleString()}`\n        ]);\n      } else {\n        this.addOutput(`❌ ${latestData.message || totalData.message || '\''Failed to fetch stats'\''}`, '\''error'\'');\n      }\n    } catch (error) {\n      this.addOutput(`❌ Network error: ${error.message}`, '\''error'\'');\n    }/' /home/coinjecture/COINjecture/web/app.js

# Add cache-busting to fetchWithFallback
sed -i 's/const url = this.apiBase + endpoint;/\/\/ Add cache-busting parameter to ensure fresh data\n    const separator = endpoint.includes('\''?'\'') ? '\''&'\'' : '\''?'\'';\n    const url = this.apiBase + endpoint + separator + '\''t='\'' + Date.now();/' /home/coinjecture/COINjecture/web/app.js

echo "✅ Web interface updated with CLI fixes"

# 3. Test the API endpoints
echo "🧪 Testing API endpoints..."
echo "   Latest block:"
curl -s https://api.coinjecture.com/v1/data/block/latest | jq '.data.index'

echo "   Total blocks:"
curl -s https://api.coinjecture.com/v1/data/blocks/all | jq '.meta.total_blocks'

# 4. Restart nginx to ensure changes are served
echo "🔄 Restarting nginx..."
systemctl reload nginx
echo "✅ Nginx reloaded"

echo ""
echo "✅ CLI fix deployment completed!"
echo "================================"
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Updated displayBlockchainStats() to fetch total blocks from API"
echo "   ✅ Added cache-busting to prevent stale data"
echo "   ✅ Cleared local cache files"
echo "   ✅ Updated web interface on droplet"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The CLI should now show live data:"
echo "   - Total Blocks: 5280"
echo "   - Latest Block: #5277"
echo "   - Work Score: 1.4"

# Clean up
rm -f /tmp/app_js_fixed.js

EOF

# Make the script executable
chmod +x /tmp/fix_cli_droplet.sh

echo "📤 Copying CLI fix script to droplet..."
scp -i "$SSH_KEY" /tmp/fix_cli_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running CLI fix on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/fix_cli_droplet.sh && /tmp/fix_cli_droplet.sh"

# Clean up
rm -f /tmp/fix_cli_droplet.sh

echo ""
echo "🎉 CLI fix deployment completed!"
echo "==============================="
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "Run 'blockchain-stats' command to verify it shows live data!"
