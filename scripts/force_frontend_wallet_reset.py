#!/usr/bin/env python3
"""
Force frontend to use configured wallet address by clearing localStorage
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_frontend_wallet_reset():
    """Force frontend to use configured wallet address"""
    
    logger.info("=== Force Frontend Wallet Reset ===")
    
    # Paths
    web_dir = "/home/coinjecture/COINjecture/web"
    
    try:
        # Create a JavaScript snippet to clear localStorage and force wallet reset
        js_snippet = """
// Force clear localStorage and reset wallet
localStorage.removeItem('coinjecture_wallet');
console.log('Cleared localStorage wallet data');

// Force page reload to reset wallet state
window.location.reload();
"""
        
        # Create a temporary HTML file with the reset script
        reset_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Wallet Reset</title>
</head>
<body>
    <h1>Resetting Wallet...</h1>
    <p>Clearing localStorage and resetting wallet to use configured address.</p>
    <script>
        {js_snippet}
    </script>
</body>
</html>
"""
        
        # Write the reset HTML file
        reset_file = os.path.join(web_dir, "wallet-reset.html")
        with open(reset_file, 'w') as f:
            f.write(reset_html)
        
        logger.info(f"Created wallet reset file: {reset_file}")
        
        # Also create a JavaScript file that can be included in the main app
        js_file = os.path.join(web_dir, "wallet-reset.js")
        with open(js_file, 'w') as f:
            f.write(js_snippet)
        
        logger.info(f"Created wallet reset JS file: {js_file}")
        
        # Update the main app.js to include wallet reset on load
        app_js_path = os.path.join(web_dir, "app.js")
        
        # Read current app.js
        with open(app_js_path, 'r') as f:
            app_js_content = f.read()
        
        # Add wallet reset logic at the beginning of the init method
        wallet_reset_code = """
    // Force use configured wallet address
    this.forceConfiguredWallet();
"""
        
        # Find the init method and add the wallet reset code
        if 'init() {' in app_js_content:
            app_js_content = app_js_content.replace(
                'init() {\n    // Initialize navigation',
                f'init() {{\n    // Force use configured wallet address\n    this.forceConfiguredWallet();\n    \n    // Initialize navigation'
            )
            
            # Add the forceConfiguredWallet method
            force_wallet_method = """
  forceConfiguredWallet() {
    // Clear any existing wallet data
    localStorage.removeItem('coinjecture_wallet');
    
    // Set the configured wallet address
    this.configuredWalletAddress = "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33";
    
    // Override wallet creation to use configured address
    this.originalCreateOrLoadWallet = this.createOrLoadWallet;
    this.createOrLoadWallet = async () => {
      return {
        address: this.configuredWalletAddress,
        publicKey: "configured_public_key",
        keyPair: null,
        created: Date.now()
      };
    };
  }
"""
            
            # Add the method before the existing methods
            if 'async createOrLoadWallet() {' in app_js_content:
                app_js_content = app_js_content.replace(
                    'async createOrLoadWallet() {',
                    f'{force_wallet_method}\n  async createOrLoadWallet() {{'
                )
            
            # Write the updated app.js
            with open(app_js_path, 'w') as f:
                f.write(app_js_content)
            
            logger.info("✅ Updated app.js to force configured wallet address")
        else:
            logger.error("❌ Could not find init() method in app.js")
            return False
        
        # Restart API service to serve updated files
        logger.info("Restarting API service...")
        result = subprocess.run(['systemctl', 'restart', 'coinjecture-api'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ API service restarted successfully")
        else:
            logger.error(f"❌ Failed to restart API service: {result.stderr}")
            return False
        
        logger.info("✅ Frontend wallet reset completed")
        logger.info("Frontend will now use configured wallet address: BEANSa93eefd297ae59e963d0977319690ffbc55e2b33")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in force frontend wallet reset: {e}")
        return False

if __name__ == "__main__":
    success = force_frontend_wallet_reset()
    if success:
        print("✅ Frontend wallet reset completed successfully")
    else:
        print("❌ Failed to reset frontend wallet")
        sys.exit(1)
