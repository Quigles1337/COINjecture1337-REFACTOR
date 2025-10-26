#!/bin/bash

# Fix All Stale Data Issues
# This script creates a comprehensive fix for all stale data in the frontend

set -e

echo "🔧 Fixing All Stale Data Issues"
echo "=============================="

# Create a completely clean HTML file without any hardcoded help text
cat > /tmp/index-clean.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
  <title>COINjecture</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="icon" href="data:,">
</head>
<body>
  <!-- Navigation Bar -->
  <nav class="navbar">
    <div class="nav-container">
      <div class="nav-brand">
        <span class="brand-text">COINjecture</span>
        <span class="brand-subtitle">Utility-Based Computational Work Blockchain</span>
        <span class="brand-ticker">$BEANS</span>
      </div>
      <div class="nav-links">
        <a href="#terminal" class="nav-link active" data-page="terminal">Terminal</a>
        <a href="#api" class="nav-link" data-page="api">API Docs</a>
        <a href="#download" class="nav-link" data-page="download">Download CLI</a>
        <a href="#proof" class="nav-link" data-page="proof">Proof</a>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content">
    <!-- Terminal Page -->
    <div id="page-terminal" class="page active">
      <div class="terminal-container">
        <div class="terminal-header">
          <div class="terminal-title">🚀 COINjecture Web CLI ($BEANS)</div>
          <div class="wallet-dashboard" id="wallet-dashboard" style="display: none;">
            <div class="wallet-info">
              <span class="wallet-address" id="wallet-address">Loading...</span>
              <button class="copy-btn" id="copy-address-btn" title="Copy Address">📋</button>
            </div>
            <div class="rewards-info">
              <span class="rewards-total" id="rewards-total">0 BEANS</span>
              <span class="blocks-mined" id="blocks-mined">0 blocks</span>
            </div>
          </div>
          <div class="status" id="network-status">🌐 Connecting...</div>
        </div>
    
    <div class="terminal-output" id="terminal-output">
      <div class="output">coinjectured$ <span class="cursor">█</span></div>
    </div>
    
    <div class="terminal-input">
      <input type="text" id="command-input" placeholder="Type a command..." autocomplete="off">
    </div>
  </div>
</div>

    <!-- API Documentation Page -->
    <div id="page-api" class="page">
      <div class="api-docs">
        <h1>API Documentation</h1>
        
        <div class="api-section">
          <h2>Live API Endpoints</h2>
          <div class="endpoint-list">
            <div class="endpoint">
              <span class="method">GET</span>
              <span class="path">/v1/data/block/latest</span>
              <span class="description">Get latest blockchain block</span>
            </div>
            <div class="endpoint">
              <span class="method">GET</span>
              <span class="path">/v1/data/block/{index}</span>
              <span class="description">Get block by index</span>
            </div>
            <div class="endpoint">
              <span class="method">GET</span>
              <span class="path">/v1/peers</span>
              <span class="description">List connected peers</span>
            </div>
            <div class="endpoint">
              <span class="method">GET</span>
              <span class="path">/v1/display/telemetry/latest</span>
              <span class="description">Get network telemetry</span>
            </div>
            <div class="endpoint">
              <span class="method">POST</span>
              <span class="path">/v1/mine</span>
              <span class="description">Start mining operation</span>
            </div>
          </div>
          
          <div class="api-info">
            <h3>Base URL</h3>
            <code>https://api.coinjecture.com</code>
          </div>
          
          <div class="api-test">
            <h3>Test API</h3>
            <button id="test-api-btn" class="test-btn">Test Connection</button>
            <div id="api-test-result"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Download Page -->
    <div id="page-download" class="page">
      <div class="download-section">
        <h1>Download COINjecture CLI</h1>
        
        <div class="download-options">
          <div class="download-card">
            <h2>macOS (Recommended)</h2>
            <div class="download-item">
              <h3>COINjecture-macOS-v3.6.6-Final.zip</h3>
              <p>Complete CLI package with zero security warnings</p>
              <ul>
                <li>✅ Zero Security Warnings</li>
                <li>✅ No Python Required</li>
                <li>✅ Interactive Menu</li>
                <li>✅ Direct CLI Access</li>
                <li>✅ Network Integration</li>
              </ul>
              <a href="https://github.com/beanapologist/COINjecture/releases/download/v3.6.6/COINjecture-macOS-v3.6.6-Final.zip" class="download-btn">Download (39.2 MB)</a>
            </div>
          </div>
        </div>
        
        <div class="installation-steps">
          <h2>Installation Instructions</h2>
          <ol>
            <li>Download the zip file above</li>
            <li>Extract and run <code>./install.sh</code></li>
            <li>COINjecture launches automatically! 🚀</li>
          </ol>
        </div>
        
        <div class="other-platforms">
          <h2>Other Platforms</h2>
          <p>Windows Coming Soon</p>
          <p>Linux Coming Soon</p>
        </div>
      </div>
    </div>

    <!-- Proof Page -->
    <div id="page-proof" class="page">
      <div class="proof-section">
        <h1>Critical Complex Equilibrium Proof</h1>
        
        <div class="proof-content">
          <h2>Mathematical Foundation</h2>
          <div class="proof-document">
            <h3>Critical_Complex_Equilibrium_Proof.pdf</h3>
            <p>Complete mathematical proof of COINjecture's equilibrium properties and computational work validation.</p>
            <ul>
              <li>✅ Equilibrium Analysis</li>
              <li>✅ Computational Work Proof</li>
              <li>✅ Mathematical Rigor</li>
              <li>✅ Peer Review Ready</li>
              <li>✅ Academic Standard</li>
            </ul>
            <div class="proof-links">
              <a href="https://coinjecture.com/Critical_Complex_Equilibrium_Proof.pdf" class="proof-link">📄 View Proof (PDF)</a>
              <a href="https://coinjecture.com/Critical_Complex_Equilibrium_Proof.pdf" class="proof-link">🔗 Direct S3 Link</a>
            </div>
          </div>
          
          <div class="proof-overview">
            <h2>Proof Overview</h2>
            <p>This comprehensive mathematical proof establishes the theoretical foundation for COINjecture's blockchain architecture, demonstrating:</p>
            <ul>
              <li><strong>Equilibrium Properties:</strong> Mathematical proof of system stability</li>
              <li><strong>Computational Work:</strong> Validation of NP-Complete problem solving</li>
              <li><strong>Economic Incentives:</strong> Proof of work reward mechanisms</li>
              <li><strong>Network Security:</strong> Cryptographic security guarantees</li>
            </ul>
          </div>
          
          <div class="proof-section">
            <h2>Academic Standards</h2>
            <div class="academic-info">
              <p>This proof follows rigorous mathematical standards and is suitable for:</p>
              <ul>
                <li>Academic peer review</li>
                <li>Cryptocurrency research</li>
                <li>Blockchain protocol analysis</li>
                <li>Mathematical verification</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
  
  <script src="./app.js"></script>
</body>
</html>
EOF

# Create the fixed app.js with unified endpoints
cat > /tmp/app-fixed.js << 'APPJS'
/**
 * COINjecture Web Interface - Unified Endpoints
 * All data fetched from single API source: https://api.coinjecture.com
 */

class WebInterface {
  constructor() {
    // Unified API endpoint
    this.apiBase = 'https://api.coinjecture.com';
    this.output = document.getElementById('terminal-output');
    this.input = document.getElementById('command-input');
    this.status = document.getElementById('network-status');
    this.history = [];
    this.historyIndex = -1;
    
    // Wallet dashboard elements
    this.walletDashboard = document.getElementById('wallet-dashboard');
    this.walletAddress = document.getElementById('wallet-address');
    this.rewardsTotal = document.getElementById('rewards-total');
    this.blocksMined = document.getElementById('blocks-mined');
    this.copyAddressBtn = document.getElementById('copy-address-btn');
    
    // Rewards refresh interval
    this.rewardsRefreshInterval = null;
    
    this.wallet = null;
    this.isProcessing = false;
    
    this.init();
  }
  
  async init() {
    this.setupEventListeners();
    this.updateNetworkStatus();
    this.initAPITesting();
    this.initCopyAddressButton();
    
    // Start periodic updates
    setInterval(() => this.updateNetworkStatus(), 30000);
    this.checkWalletStatus();
  }
  
  setupEventListeners() {
    if (this.input) {
      this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
      this.input.addEventListener('input', (e) => this.handleInput(e));
    }
    
    if (this.copyAddressBtn) {
      this.copyAddressBtn.addEventListener('click', () => this.copyAddress());
    }
    
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.showPage(link.dataset.page);
      });
    });
    
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-page]')) {
        e.preventDefault();
        this.showPage(e.target.dataset.page);
      }
    });
    
    document.addEventListener('click', (e) => {
      const targetPage = e.target.dataset.page;
      if (targetPage === 'terminal' && this.input) {
        setTimeout(() => this.input.focus(), 100);
      }
    });
  }
  
  initAPITesting() {
    const testButton = document.getElementById('test-api-btn');
    if (testButton) {
      testButton.addEventListener('click', () => this.testAPIConnection());
    }
  }
  
  async testAPIConnection() {
    const resultDiv = document.getElementById('api-test-result');
    resultDiv.innerHTML = 'Testing connection...';
    resultDiv.className = 'test-result';
    
    try {
      const response = await this.fetchWithFallback('/v1/data/block/latest');
      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        resultDiv.innerHTML = `✅ Connection successful!<br>Latest block: #${data.data.index}<br>Hash: ${data.data.block_hash.substring(0, 16)}...`;
        resultDiv.className = 'test-result success';
      } else {
        resultDiv.innerHTML = `❌ Connection failed: ${data.message || 'Unknown error'}`;
        resultDiv.className = 'test-result error';
      }
    } catch (error) {
      resultDiv.innerHTML = `❌ Connection error: ${error.message}`;
      resultDiv.className = 'test-result error';
    }
  }
  
  showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
      page.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`page-${pageId}`);
    if (targetPage) {
      targetPage.classList.add('active');
    }
    
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-page="${pageId}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }
    
    if (pageId === 'terminal' && this.input) {
      setTimeout(() => this.input.focus(), 100);
    }
  }
  
  handleKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const command = this.input.value.trim();
      if (command) {
        this.addOutput(`coinjectured$ ${command}`);
        this.history.push(command);
        this.historyIndex = this.history.length;
        this.input.value = '';
        this.processCommand(command);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (this.historyIndex > 0) {
        this.historyIndex--;
        this.input.value = this.history[this.historyIndex];
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (this.historyIndex < this.history.length - 1) {
        this.historyIndex++;
        this.input.value = this.history[this.historyIndex];
      } else {
        this.historyIndex = this.history.length;
        this.input.value = '';
      }
    }
  }
  
  handleInput(e) {
    if (this.input) {
      this.input.style.width = Math.max(200, this.input.value.length * 8 + 20) + 'px';
    }
  }
  
  async processCommand(command) {
    const [cmd, ...args] = command.split(' ');
    
    switch(cmd) {
      case 'blockchain-stats':
        await this.displayBlockchainStats();
        break;
      case 'help':
        this.showHelp();
        break;
      case 'get-block':
        await this.handleGetBlock(args);
        break;
      case 'peers':
        await this.handlePeers();
        break;
      case 'telemetry-status':
        await this.handleTelemetryStatus();
        break;
      case 'mine':
        await this.handleMine(args);
        break;
      case 'submit-problem':
        await this.handleSubmitProblem();
        break;
      case 'wallet-generate':
        await this.handleWalletGenerate();
        break;
      case 'wallet-info':
        this.handleWalletInfo();
        break;
      case 'rewards':
        this.handleRewards();
        break;
      case 'export-wallet':
        this.handleExportWallet();
        break;
      case 'copy-address':
        this.copyAddress();
        break;
      case 'clear':
        this.clearOutput();
        break;
      default:
        this.addOutput(`❌ Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
    }
  }
  
  showHelp() {
    const helpLines = [
      'Available commands:',
      '  get-block --latest     Get latest block',
      '  blockchain-stats      Show blockchain statistics',
      '  get-block --index <n>  Get block by index',
      '  peers                  List connected peers',
      '  telemetry-status       Check network status',
      '  mine --tier <tier>     Start mining (mobile|desktop|server)',
      '  submit-problem         Submit computational problem',
      '  wallet-generate        Create new wallet',
      '  wallet-info            Show wallet details',
      '  rewards                Show mining rewards breakdown',
      '  export-wallet          Export wallet details for backup',
      '  copy-address           Copy wallet address to clipboard',
      '  help                   Show this help',
      '  clear                  Clear terminal',
      '',
      'Mobile tips:',
      '  • Swipe up/down for command history',
      '  • Tap and hold for text selection',
      '  • Use Tab for auto-complete'
    ];
    
    this.addMultiLineOutput(helpLines);
  }
  
  async handleGetBlock(args) {
    try {
      const isLatest = args.includes('--latest');
      const indexArg = args.find(arg => arg.startsWith('--index='));
      const index = indexArg ? indexArg.split('=')[1] : null;
      
      let endpoint;
      if (isLatest) {
        endpoint = `${this.apiBase}/v1/data/block/latest`;
      } else if (index) {
        endpoint = `${this.apiBase}/v1/data/block/${index}`;
      } else {
        this.addOutput('❌ Use --latest or --index=<number>', 'error');
        return;
      }
      
      this.addOutput('📦 Fetching block data...');
      const response = await this.fetchWithFallback(endpoint);
      const data = await response.json();
      
      if (data.status === 'success') {
        const block = data.data;
        this.addMultiLineOutput([
          `✅ Block #${block.index}`,
          `   Hash: ${block.block_hash}`,
          `   Previous: ${block.previous_hash}`,
          `   Timestamp: ${new Date(block.timestamp * 1000).toLocaleString()}`,
          `   Work Score: ${block.cumulative_work_score}`,
          `   Capacity: ${block.mining_capacity}`,
          `   Transactions: ${block.transactions ? block.transactions.length : 0}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Block not found'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handlePeers() {
    try {
      this.addOutput('🌐 Fetching peer information...');
      const response = await this.fetchWithFallback('/v1/peers');
      const data = await response.json();
      
      if (data.status === 'success') {
        const peers = data.data;
        if (peers.length > 0) {
          this.addMultiLineOutput([
            '🌐 Connected Peers:',
            ...peers.map(peer => `   ${peer.address}:${peer.port} (${peer.status})`)
          ]);
        } else {
          this.addOutput('🌐 No peers connected');
        }
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch peers'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleTelemetryStatus() {
    try {
      this.addOutput('📊 Fetching network telemetry...');
      const response = await this.fetchWithFallback('/v1/display/telemetry/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const telemetry = data.data;
        this.addMultiLineOutput([
          '📊 Network Telemetry:',
          `   Active Miners: ${telemetry.active_miners || 0}`,
          `   Total Blocks: ${telemetry.total_blocks || 0}`,
          `   Network Hash Rate: ${telemetry.hash_rate || 'N/A'}`,
          `   Last Update: ${new Date(telemetry.timestamp * 1000).toLocaleString()}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch telemetry'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleMine(args) {
    try {
      const tierArg = args.find(arg => arg.startsWith('--tier='));
      const tier = tierArg ? tierArg.split('=')[1] : 'mobile';
      
      if (!['mobile', 'desktop', 'server'].includes(tier)) {
        this.addOutput('❌ Invalid tier. Use: mobile, desktop, or server', 'error');
        return;
      }
      
      this.addOutput(`⛏️  Starting mining with ${tier} tier...`);
      
      if (!this.wallet) {
        this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
        return;
      }
      
      const response = await this.fetchWithFallback('/v1/mine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tier: tier,
          miner_address: this.wallet.address
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.addOutput(`✅ Mining started successfully!`, 'success');
        this.addOutput(`💰 Miner Address: ${this.wallet.address}`);
        this.addOutput(`⚡ Tier: ${tier}`);
        this.addOutput(`🔗 Mining ID: ${data.data.mining_id || 'N/A'}`);
        
        this.startRewardsRefresh();
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to start mining'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleSubmitProblem() {
    try {
      this.addOutput('🧮 Submitting computational problem...');
      
      const problem = {
        type: 'subset_sum',
        target: 15,
        numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        timestamp: Date.now()
      };
      
      const response = await this.fetchWithFallback('/v1/submit-problem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(problem)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        this.addOutput(`✅ Problem submitted successfully!`, 'success');
        this.addOutput(`🆔 Problem ID: ${data.data.problem_id || 'N/A'}`);
        this.addOutput(`🎯 Target: ${problem.target}`);
        this.addOutput(`📊 Numbers: [${problem.numbers.join(', ')}]`);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to submit problem'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleWalletGenerate() {
    try {
      this.addOutput('🔑 Generating new wallet...');
      
      const keyPair = await this.generateKeyPair();
      
      this.wallet = {
        address: keyPair.address,
        publicKey: keyPair.publicKey,
        privateKey: keyPair.privateKey,
        created: new Date().toISOString()
      };
      
      localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
      
      this.addOutput(`✅ Wallet generated successfully!`, 'success');
      this.addOutput(`🔑 Address: ${this.wallet.address}`);
      this.addOutput(`🔐 Public Key: ${this.wallet.publicKey}`);
      this.addOutput(`💾 Wallet saved to browser storage`);
      
      this.updateWalletDashboard();
      
    } catch (error) {
      this.addOutput(`❌ Failed to generate wallet: ${error.message}`, 'error');
    }
  }
  
  handleWalletInfo() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    this.addMultiLineOutput([
      '💰 Wallet Information',
      `Address: ${this.wallet.address}`,
      `Public Key: ${this.wallet.publicKey}`,
      `Created: ${new Date(this.wallet.created).toLocaleString()}`,
      '',
      'This wallet is used for mining rewards and token transactions.',
      'Your private key is securely stored in your browser.'
    ]);
  }
  
  handleRewards() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    const rewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
    const totalRewards = rewards[this.wallet.address] || 0;
    const blocksMined = rewards[`${this.wallet.address}_blocks`] || 0;
    
    this.addMultiLineOutput([
      '💰 Current Rewards:',
      `${totalRewards} BEANS (${blocksMined} blocks mined)`,
      '',
      'This wallet is used for mining rewards and token transactions.',
      'Your private key is securely stored in your browser.',
      '',
      '💡 Commands:',
      '  • "copy-address" - Copy address to clipboard',
      '  • "rewards" - Show detailed rewards breakdown',
      '  • "export-wallet" - Export wallet for backup',
      '  • "mine --tier=mobile" - Start earning $BEANS tokens!'
    ]);
  }
  
  handleExportWallet() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    const exportData = {
      address: this.wallet.address,
      publicKey: this.wallet.publicKey,
      privateKey: this.wallet.privateKey,
      created: this.wallet.created,
      exported: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `coinjecture-wallet-${this.wallet.address.substring(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    this.addOutput(`✅ Wallet exported successfully!`, 'success');
    this.addOutput(`📁 File: coinjecture-wallet-${this.wallet.address.substring(0, 8)}.json`);
    this.addOutput(`🔐 Keep your private key secure and never share it!`);
  }
  
  copyAddress() {
    if (!this.wallet) {
      this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.', 'info');
      return;
    }
    
    navigator.clipboard.writeText(this.wallet.address).then(() => {
      this.addOutput(`✅ Address copied to clipboard: ${this.wallet.address}`, 'success');
    }).catch(() => {
      this.addOutput(`❌ Failed to copy address. Please copy manually: ${this.wallet.address}`, 'error');
    });
  }
  
  clearOutput() {
    if (this.output) {
      this.output.innerHTML = '<div class="output">coinjectured$ <span class="cursor">█</span></div>';
    }
  }
  
  addOutput(text, type = 'normal') {
    if (!this.output) return;
    
    const outputDiv = document.createElement('div');
    outputDiv.className = `output ${type}`;
    outputDiv.innerHTML = text;
    
    this.output.appendChild(outputDiv);
    this.output.scrollTop = this.output.scrollHeight;
  }
  
  addMultiLineOutput(lines) {
    lines.forEach(line => {
      this.addOutput(line);
    });
  }
  
  async generateKeyPair() {
    try {
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: 'Ed25519',
          namedCurve: 'Ed25519'
        },
        true,
        ['sign', 'verify']
      );
      
      const publicKeyBuffer = await window.crypto.subtle.exportKey('raw', keyPair.publicKey);
      const publicKeyHex = Array.from(new Uint8Array(publicKeyBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      const privateKeyBuffer = await window.crypto.subtle.exportKey('pkcs8', keyPair.privateKey);
      const privateKeyHex = Array.from(new Uint8Array(privateKeyBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      const address = `BEANS${publicKeyHex.substring(0, 40)}`;
      
      return {
        address,
        publicKey: publicKeyHex,
        privateKey: privateKeyHex
      };
    } catch (error) {
      throw new Error(`Key generation failed: ${error.message}`);
    }
  }
  
  checkWalletStatus() {
    const storedWallet = localStorage.getItem('coinjecture_wallet');
    if (storedWallet) {
      try {
        this.wallet = JSON.parse(storedWallet);
        this.updateWalletDashboard();
        this.startRewardsRefresh();
      } catch (error) {
        console.error('Failed to load wallet:', error);
        localStorage.removeItem('coinjecture_wallet');
      }
    }
  }
  
  updateWalletDashboard() {
    if (!this.wallet || !this.walletDashboard) return;
    
    if (this.walletAddress) {
      this.walletAddress.textContent = this.wallet.address;
    }
    
    const rewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
    const totalRewards = rewards[this.wallet.address] || 0;
    const blocksMined = rewards[`${this.wallet.address}_blocks`] || 0;
    
    if (this.rewardsTotal) {
      this.rewardsTotal.textContent = `${totalRewards} BEANS`;
    }
    
    if (this.blocksMined) {
      this.blocksMined.textContent = `${blocksMined} blocks`;
    }
    
    this.walletDashboard.style.display = 'block';
  }
  
  startRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
    }
    
    this.rewardsRefreshInterval = setInterval(() => {
      this.updateRewardsDashboard();
    }, 30000);
  }
  
  async updateRewardsDashboard() {
    if (!this.wallet) return;
    
    try {
      const response = await this.fetchWithFallback(`/v1/rewards/${this.wallet.address}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        const rewards = data.data;
        const totalRewards = rewards.total_rewards || 0;
        const blocksMined = rewards.blocks_mined || 0;
        
        const storedRewards = JSON.parse(localStorage.getItem('coinjecture_rewards') || '{}');
        storedRewards[this.wallet.address] = totalRewards;
        storedRewards[`${this.wallet.address}_blocks`] = blocksMined;
        localStorage.setItem('coinjecture_rewards', JSON.stringify(storedRewards));
        
        this.updateWalletDashboard();
      }
    } catch (error) {
      console.error('Failed to update rewards:', error);
    }
  }
  
  stopRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
      this.rewardsRefreshInterval = null;
    }
  }

  // Display blockchain statistics - UNIFIED ENDPOINT
  async displayBlockchainStats() {
    try {
      this.addOutput('📊 Fetching blockchain statistics...');
      const response = await this.fetchWithFallback('/v1/data/block/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const block = data.data;
        this.addMultiLineOutput([
          '📊 Blockchain Statistics:',
          `   Latest Block: #${block.index}`,
          `   Latest Hash: ${block.block_hash.substring(0, 20)}...`,
          `   Work Score: ${block.cumulative_work_score.toFixed(2)}`,
          `   Last Updated: ${new Date(block.timestamp * 1000).toLocaleString()}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to fetch stats'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async updateNetworkStatus() {
    try {
      const response = await this.fetchWithFallback('/v1/data/block/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const block = data.data;
        this.status.innerHTML = `🌐 Live Network: Block #${block.index} | Hash: ${block.block_hash.substring(0, 16)}... | Work: ${block.cumulative_work_score.toFixed(2)}`;
        this.status.className = 'status connected';
        
        localStorage.setItem('coinjecture_cert_accepted', 'true');
      } else {
        this.status.innerHTML = '🌐 Network: Offline';
        this.status.className = 'status offline';
      }
    } catch (error) {
      if (error.message.includes('Certificate not accepted')) {
        this.status.innerHTML = '🔒 Certificate Required - Click Link Above';
        this.status.className = 'status error';
      } else {
        this.status.innerHTML = '🌐 Network: Connection Error';
        this.status.className = 'status error';
      }
    }
  }
  
  async fetchWithFallback(endpoint, options = {}) {
    const url = this.apiBase + endpoint;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      console.log('API call failed:', error);
      throw error;
    }
  }
  
  initCopyAddressButton() {
    if (this.copyAddressBtn) {
      this.copyAddressBtn.addEventListener('click', () => {
        if (this.wallet) {
          navigator.clipboard.writeText(this.wallet.address).then(() => {
            this.addOutput(`✅ Address copied: ${this.wallet.address}`, 'success');
          }).catch(() => {
            this.addOutput(`❌ Copy failed. Address: ${this.wallet.address}`, 'error');
          });
        }
      });
    }
  }
}

// Download CLI function (global for onclick)
function downloadCLI(platform) {
  if (platform === 'macos') {
    window.open('https://github.com/beanapologist/COINjecture/releases/download/v3.6.6/COINjecture-macOS-v3.6.6-Final.zip', '_blank');
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new WebInterface();
});
APPJS

echo "✅ Created clean HTML and fixed JavaScript files"
echo "📁 Files created:"
echo "   - /tmp/index-clean.html (no hardcoded help text)"
echo "   - /tmp/app-fixed.js (unified endpoints)"

echo ""
echo "🚀 Deploying to S3..."

# Deploy to S3
cd /Users/sarahmarin/Downloads/COINjecture-main\ 4/web
cp /tmp/index-clean.html index.html
cp /tmp/app-fixed.js app.js
./deploy-s3.sh

echo ""
echo "🔄 Clearing CloudFront cache..."
cd /Users/sarahmarin/Downloads/COINjecture-main\ 4
python3 scripts/clear_cloudfront_cache.py

echo ""
echo "✅ All stale data issues fixed!"
echo "==============================="
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Removed all hardcoded help text from HTML"
echo "   ✅ Unified all endpoints to use https://api.coinjecture.com"
echo "   ✅ Fixed blockchain-stats to fetch live data"
echo "   ✅ Removed duplicate command handlers"
echo "   ✅ Clean HTML without stale data"
echo ""
echo "🧪 Test the frontend now:"
echo "   https://coinjecture.com"
echo ""
echo "The 'blockchain-stats' command should now show live data (5000+ blocks)!"
echo "The help text should be clean without any hardcoded block counts!"

# Clean up
rm -f /tmp/index-clean.html /tmp/app-fixed.js

echo ""
echo "🎉 Frontend stale data fix completed!"
