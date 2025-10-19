/**
 * COINjecture Web Interface
 * Multi-page interface with terminal, API docs, and download
 */

// Wait for @noble/ed25519 to load
async function waitForNobleEd25519() {
  let attempts = 0;
  while (attempts < 50) {
    if (window.nobleEd25519 || window.ed25519) {
      return window.nobleEd25519 || window.ed25519;
    }
    await new Promise(resolve => setTimeout(resolve, 100));
    attempts++;
  }
  throw new Error('@noble/ed25519 library failed to load');
}

class WebInterface {
  constructor() {
    // Use production API endpoint
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
    
    // Validate browser support for Ed25519
    this.validateBrowserSupport();
    
    // Add certificate notice to the page
    this.addCertificateNotice();
    this.isProcessing = false;
    this.wallet = null; // Store wallet for persistent mining
    
    this.init();
  }
  
  validateBrowserSupport() {
    // Check if Web Crypto API is available
    if (!crypto.subtle) {
      this.addOutput('❌ Web Crypto API not available. Please use HTTPS.');
      throw new Error('Web Crypto API not available. Use HTTPS.');
    }
    
    // Check if Ed25519 is supported
    try {
      crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
    } catch (e) {
      this.addOutput('❌ Ed25519 not supported in this browser. Please use a modern browser.');
      throw new Error('Ed25519 not supported in this browser');
    }
    
    console.log('✅ Browser supports Ed25519 cryptography');
  }
  
  init() {
    // Initialize navigation
    this.initNavigation();
    
    // Initialize terminal if it exists
    if (this.input) {
      this.input.focus();
      this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
      this.input.addEventListener('input', (e) => this.handleInput(e));
      
      // Touch events for mobile (passive listeners for better performance)
      this.output.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
      this.output.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: true });
      
      // Show initial help
      this.addOutput('Type "help" for available commands or start with "get-block --latest"');
    }
    
    // Initialize API testing
    this.initAPITesting();
    
    // Check for existing wallet
    this.checkWalletStatus();
    
    // Initialize copy address button
    this.initCopyAddressButton();
    
    // Auto-refresh network status
    this.updateNetworkStatus();
    setInterval(() => this.updateNetworkStatus(), 10000);
  }
  
  initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = link.dataset.page;
        
        // Update active nav link
        navLinks.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        
        // Show target page
        pages.forEach(page => page.classList.remove('active'));
        document.getElementById(`page-${targetPage}`).classList.add('active');
        
        // Focus terminal input if switching to terminal
        if (targetPage === 'terminal' && this.input) {
          setTimeout(() => this.input.focus(), 100);
        }
  });
});
  }
  
  initAPITesting() {
    const testButton = document.getElementById('test-api');
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
        resultDiv.innerHTML = `❌ API responded with error: ${data.message || 'Unknown error'}`;
        resultDiv.className = 'test-result error';
      }
    } catch (error) {
      resultDiv.innerHTML = `❌ Connection failed: ${error.message}`;
      resultDiv.className = 'test-result error';
    }
  }
  
  handleKeyDown(e) {
    if (this.isProcessing) return;
    
    if (e.key === 'Enter') {
      e.preventDefault();
      this.executeCommand();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.navigateHistory(-1);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.navigateHistory(1);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      this.autoComplete();
    }
  }
  
  handleInput(e) {
    // Auto-resize input for mobile
    this.input.style.width = Math.max(200, this.input.value.length * 8 + 20) + 'px';
  }
  
  handleTouchStart(e) {
    this.touchStartY = e.touches[0].clientY;
  }
  
  handleTouchMove(e) {
    if (!this.touchStartY) return;
    
    const touchY = e.touches[0].clientY;
    const deltaY = this.touchStartY - touchY;
    
    // Swipe up/down for history
    if (Math.abs(deltaY) > 50) {
      e.preventDefault();
      if (deltaY > 0) {
        this.navigateHistory(-1);
      } else {
        this.navigateHistory(1);
      }
      this.touchStartY = touchY;
    }
  }
  
  async executeCommand() {
    const command = this.input.value.trim();
    if (!command) return;
    
    this.isProcessing = true;
    
    // Add to history
    this.history.push(command);
    this.historyIndex = this.history.length;
    
    // Show command
    this.addCommandLine(command);
    
    // Clear input
    this.input.value = '';
    this.input.style.width = '200px';
    
    // Execute command
    try {
      await this.processCommand(command);
    } catch (error) {
      this.addOutput(`❌ Error: ${error.message}`, 'error');
    } finally {
      this.isProcessing = false;
    }
  }
  
  addCommandLine(command) {
    const line = document.createElement('div');
    line.className = 'output-line';
    line.innerHTML = `<span class="prompt">coinjectured$</span> <span class="command">${this.escapeHtml(command)}</span>`;
    this.output.appendChild(line);
    this.scrollToBottom();
  }
  
  addOutput(text, type = 'output') {
    const line = document.createElement('div');
    line.className = `output-line ${type}`;
    line.innerHTML = `<span class="output">${this.escapeHtml(text)}</span>`;
    this.output.appendChild(line);
    this.scrollToBottom();
  }
  
  addMultiLineOutput(lines, type = 'output') {
    lines.forEach(line => this.addOutput(line, type));
  }
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  scrollToBottom() {
    this.output.scrollTop = this.output.scrollHeight;
  }
  
  navigateHistory(direction) {
    if (this.history.length === 0) return;
    
    this.historyIndex += direction;
    this.historyIndex = Math.max(0, Math.min(this.history.length, this.historyIndex));
    
    if (this.historyIndex === this.history.length) {
      this.input.value = '';
    } else {
      this.input.value = this.history[this.historyIndex];
    }
    this.input.style.width = Math.max(200, this.input.value.length * 8 + 20) + 'px';
  }
  
  autoComplete() {
    const command = this.input.value.trim();
    const suggestions = [
      'get-block', 'peers', 'telemetry-status', 'mine', 'submit-problem',
      'wallet-generate', 'wallet-info', 'help', 'clear'
    ];
    
    const match = suggestions.find(s => s.startsWith(command));
    if (match) {
      this.input.value = match;
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
        await this.handleSubmitProblem(args);
        break;
      case 'wallet-generate':
        await this.handleWalletGenerate(args);
        break;
      case 'wallet-info':
        await this.handleWalletInfo(args);
        break;
      case 'rewards':
        await this.handleRewards(args);
        break;
      case 'export-wallet':
        await this.handleExportWallet(args);
        break;
      case 'copy-address':
        await this.handleCopyAddress(args);
        break;
      case 'clear':
        this.clearTerminal();
        break;
      default:
        this.addOutput(`Unknown command: ${cmd}. Type "help" for available commands.`, 'error');
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
      const response = await fetch(endpoint);
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
      this.addOutput('🌐 Fetching peer list...');
      const response = await this.fetchWithFallback('/v1/peers');
      const data = await response.json();
      
      if (data.status === 'success') {
        const peers = data.data;
        if (peers.length > 0) {
          this.addOutput(`✅ Found ${peers.length} peers:`);
          peers.forEach((peer, i) => {
            this.addOutput(`   ${i + 1}. ${peer.address} (${peer.status})`);
          });
        } else {
          this.addOutput('📡 No peers connected');
        }
      } else {
        this.addOutput(`❌ ${data.message || 'Failed to get peers'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleTelemetryStatus() {
    try {
      this.addOutput('📊 Checking telemetry status...');
      const response = await this.fetchWithFallback('/v1/display/telemetry/latest');
      const data = await response.json();
      
      if (data.status === 'success') {
        const telemetry = data.data;
        this.addMultiLineOutput([
          '✅ Network Status:',
          `   Active Miners: ${telemetry.active_miners || 'N/A'}`,
          `   Total Blocks: ${telemetry.total_blocks || 'N/A'}`,
          `   Network Hash Rate: ${telemetry.network_hash_rate || 'N/A'}`,
          `   Last Update: ${new Date(telemetry.last_update * 1000).toLocaleString()}`
        ]);
      } else {
        this.addOutput(`❌ ${data.message || 'Telemetry unavailable'}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }
  
  async handleMine(args) {
    const tierArg = args.find(arg => arg.startsWith('--tier='));
    const tier = tierArg ? tierArg.split('=')[1] : 'mobile';
    
    if (!['mobile', 'desktop', 'server'].includes(tier)) {
      this.addOutput('❌ Invalid tier. Use: mobile, desktop, or server', 'error');
      return;
    }
    
    try {
      this.addOutput(`⛏️  Starting REAL mining with ${tier} tier...`);
      
      // Get current blockchain state for real mining
      this.addOutput('📡 Fetching current blockchain state...');
      const statusResponse = await this.fetchWithFallback('/v1/data/block/latest');
      
      if (!statusResponse.ok) {
        throw new Error(`Network error: ${statusResponse.status}`);
      }
      
      const statusData = await statusResponse.json();
      if (statusData.status !== 'success') {
        throw new Error('Failed to get blockchain state');
      }
      
      const currentBlock = statusData.data;
      this.addOutput(`✅ Connected to blockchain - Latest block: #${currentBlock.index}`);
      
      // Generate REAL subset sum problem based on tier
      this.addOutput('🧮 Generating subset sum problem...');
      const problemSize = tier === 'mobile' ? 8 : tier === 'desktop' ? 12 : 16;
      const problem = this.generateSubsetSumProblem(problemSize);
      
      this.addOutput(`🔍 Solving NP-Complete problem (${problemSize} elements)...`);
      const startTime = Date.now();
      
      // REAL computational work - solve the actual problem
      const solution = this.solveSubsetSum(problem);
      const solveTime = (Date.now() - startTime) / 1000;
      
      if (!solution) {
        throw new Error('Failed to solve problem');
      }
      
      this.addOutput(`✅ Solution found in ${solveTime.toFixed(3)}s: [${solution.join(', ')}]`);
      
      // Verify the solution
      this.addOutput('🔍 Verifying solution...');
      const isValid = this.verifySubsetSum(problem, solution);
      
      if (!isValid) {
        throw new Error('Solution verification failed');
      }
      
      this.addOutput('✅ Solution verified!');
      
      // Create REAL block data
      const blockHash = this.calculateBlockHash(currentBlock, problem, solution);
      const workScore = this.calculateWorkScore(problem, solution, solveTime);
      
      this.addOutput('📡 Submitting block to network...');
      
      // Generate IPFS CID for proof data
      const proofData = {
        problem: problem,
        solution: solution,
        solve_time: solveTime,
        tier: tier,
        timestamp: Date.now()
      };
      const cid = 'Qm' + btoa(JSON.stringify(proofData)).replace(/[^a-zA-Z0-9]/g, '').substring(0, 44);
      
      // Get or create persistent wallet for this miner
      if (!this.wallet) {
        this.wallet = await this.createOrLoadWallet();
      }
      
      // Use configured miner address from config/miner_wallet.json
      const minerAddress = "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33";
      const keyPair = this.wallet.keyPair;
      const publicKey = this.wallet.publicKey;
      
      // Create the complete block data first
      const blockData = {
        block_hash: blockHash,
        block_index: currentBlock.index + 1,
        previous_hash: currentBlock.block_hash, // Use current blockchain tip as previous hash
        capacity: tier.toUpperCase(),
        cid: cid,
        event_id: `web-mining-${Date.now()}-${tier}`,
        miner_address: minerAddress,
        ts: Math.floor(Date.now() / 1000), // Integer Unix timestamp
        work_score: Math.round(workScore * 100) / 100 // Round to 2 decimal places
      };
      
      // Python-compatible JSON dumps with sort_keys=True and DEFAULT separators (', ', ': ')
      function pythonJsonDumps(obj) {
        const sortedKeys = Object.keys(obj).sort();
        let result = '{';
        sortedKeys.forEach((key, index) => {
          if (index > 0) result += ', '; // Space after comma (Python default)
          result += `"${key}": `; // Space after colon (Python default)
          const value = obj[key];
          if (typeof value === 'string') {
            result += `"${value}"`;
          } else if (typeof value === 'number') {
            // Python formats numbers intelligently
            result += String(value);
          } else if (value === null) {
            result += 'null';
          } else {
            result += JSON.stringify(value);
          }
        });
        result += '}';
        return result;
      }
      
      const canonicalJson = pythonJsonDumps(blockData);
      console.log('=== CANONICALIZATION DEBUG ===');
      console.log('Canonical JSON:', canonicalJson);
      console.log('Length:', canonicalJson.length);
      
      const dataBuffer = new TextEncoder().encode(canonicalJson);
      
      
      // Create signature using browser's native Ed25519
      const signatureBuffer = await crypto.subtle.sign(
        { name: "Ed25519" },
        keyPair.privateKey,
        dataBuffer
      );
      const signatureHex = Array.from(new Uint8Array(signatureBuffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
      
      // DEBUG: Log the signature calculation
      console.log('=== SIGNATURE DEBUG ===');
      console.log('Using browser native Ed25519 with Python-compatible JSON');
      console.log('Block data object:', blockData);
      console.log('Canonical JSON string:', canonicalJson);
      console.log('Public key:', publicKey);
      console.log('Generated signature:', signatureHex);
      console.log('Signature length:', signatureHex.length);
      console.log('Public key length:', publicKey.length);
      
      
      // Add signature and public_key to the block data
      blockData.signature = signatureHex;
      blockData.public_key = publicKey;
      
      // DEBUG: Log the signature details
      console.log('=== WEB INTERFACE DEBUG ===');
      console.log('Complete block data being sent:', blockData);
      console.log('Signature being sent:', signatureHex);
      console.log('Public key being sent:', publicKey);
      console.log('Canonical JSON that was signed:', canonicalJson);
      
      const submitResponse = await this.fetchWithFallback('/v1/ingest/block', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(blockData)
      });
      
      if (submitResponse.ok) {
        const result = await submitResponse.json();
        this.addMultiLineOutput([
          '🎉 REAL mining completed successfully!',
          `   Tier: ${tier}`,
          `   Problem Size: ${problemSize} elements`,
          `   Target: ${problem.target}`,
          `   Solution: [${solution.join(', ')}]`,
          `   Work Score: ${workScore.toFixed(2)}`,
          `   Solve Time: ${solveTime.toFixed(3)}s`,
          `   Block Hash: ${blockHash.substring(0, 16)}...`,
          `   Network Response: ${result.status || 'Success'}`,
          '',
          '✅ Block successfully mined and submitted to COINjecture network!'
        ]);
      } else {
        // Get detailed error information
        const errorText = await submitResponse.text();
        this.addOutput(`⚠️  Network submission failed: ${submitResponse.status}`);
        this.addOutput(`   Error details: ${errorText}`);
        
        // Still show successful mining results even if network submission failed
        this.addMultiLineOutput([
          '🎉 REAL mining completed successfully!',
          `   Tier: ${tier}`,
          `   Problem Size: ${problemSize} elements`,
          `   Target: ${problem.target}`,
          `   Solution: [${solution.join(', ')}]`,
          `   Work Score: ${workScore.toFixed(2)}`,
          `   Solve Time: ${solveTime.toFixed(3)}s`,
          `   Block Hash: ${blockHash.substring(0, 16)}...`,
          '',
          '⚠️  Block mined but network submission failed',
          '💡 For full network integration, use the desktop COINjecture CLI'
        ]);
      }
      
    } catch (error) {
      this.addOutput(`❌ Mining error: ${error.message}`, 'error');
      this.addOutput('💡 Check network connection and try again');
    }
  }
  
  generateSubsetSumProblem(size) {
    const numbers = [];
    for (let i = 0; i < size; i++) {
      numbers.push(Math.floor(Math.random() * 100) + 1);
    }
    
    // Create a target that has a solution
    const subset = numbers.slice(0, Math.floor(size / 2));
    const target = subset.reduce((sum, num) => sum + num, 0);
    
    return {
      numbers: numbers,
      target: target,
      size: size
    };
  }
  
  solveSubsetSum(problem) {
    // REAL subset sum solver using dynamic programming
    const { numbers, target } = problem;
    const n = numbers.length;
    const dp = Array(target + 1).fill(false);
    const parent = Array(target + 1).fill(-1);
    
    dp[0] = true;
    
    for (let i = 0; i < n; i++) {
      for (let j = target; j >= numbers[i]; j--) {
        if (dp[j - numbers[i]] && !dp[j]) {
          dp[j] = true;
          parent[j] = i;
        }
      }
    }
    
    if (!dp[target]) {
      return null;
    }
    
    // Reconstruct solution
    const solution = [];
    let current = target;
    while (current > 0) {
      const index = parent[current];
      solution.push(numbers[index]);
      current -= numbers[index];
    }
    
    return solution;
  }
  
  verifySubsetSum(problem, solution) {
    const sum = solution.reduce((a, b) => a + b, 0);
    return sum === problem.target;
  }
  
  calculateBlockHash(previousBlock, problem, solution) {
    const data = `${previousBlock.block_hash}${JSON.stringify(problem)}${JSON.stringify(solution)}${Date.now()}`;
    return '0x' + Array.from({length: 64}, (_, i) => {
      const char = data.charCodeAt(i % data.length);
      return char.toString(16).padStart(2, '0');
    }).join('');
  }
  
  calculateWorkScore(problem, solution, solveTime) {
    const complexity = Math.pow(2, problem.size);
    const efficiency = solveTime > 0 ? complexity / solveTime : complexity * 1000;
    const workScore = Math.max(efficiency * 0.1, problem.size * 0.5);
    
    // Ensure work_score is always a finite number
    return isFinite(workScore) ? workScore : problem.size * 0.5;
  }
  
  async createOrLoadWallet() {
    // Check if wallet exists in localStorage
    const storedWallet = localStorage.getItem('coinjecture_wallet');
    
    if (storedWallet) {
      return await this.loadWallet(storedWallet);
    }
    
    // Generate new Ed25519 keypair using browser's native crypto
    this.addOutput('🔑 Creating new secure wallet...');
    
    const keyPair = await crypto.subtle.generateKey(
      { name: "Ed25519" },
      true,  // extractable
      ["sign", "verify"]
    );
    
    // Export keys for storage
    const privateKeyPkcs8 = await crypto.subtle.exportKey("pkcs8", keyPair.privateKey);
    const publicKeyRaw = await crypto.subtle.exportKey("raw", keyPair.publicKey);
    
    // Convert to hex for storage
    const privateKeyHex = Array.from(new Uint8Array(privateKeyPkcs8))
      .map(b => b.toString(16).padStart(2, '0')).join('');
    const publicKeyHex = Array.from(new Uint8Array(publicKeyRaw))
      .map(b => b.toString(16).padStart(2, '0')).join('');
    
    // Generate address from public key
    const addressBuffer = await crypto.subtle.digest('SHA-256', publicKeyRaw);
    const address = 'web-' + Array.from(new Uint8Array(addressBuffer))
      .map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    
    // Store wallet
    const walletData = {
      address: address,
      privateKey: privateKeyHex,
      publicKey: publicKeyHex,
      created: Date.now()
    };
    
    localStorage.setItem('coinjecture_wallet', JSON.stringify(walletData));
    
    const wallet = {
      address: address,
      publicKey: publicKeyHex,
      keyPair: keyPair,
      created: walletData.created
    };
    
    this.addOutput(`🔑 Created new wallet: ${address} ($BEANS)`);
    return wallet;
  }
  
  async loadWallet(storedWallet) {
    try {
      const walletData = JSON.parse(storedWallet);
      
      // DEBUG: Log wallet data
      console.log('=== WALLET LOADING DEBUG ===');
      console.log('Private key length:', walletData.privateKey ? walletData.privateKey.length : 'undefined');
      console.log('Public key length:', walletData.publicKey ? walletData.publicKey.length : 'undefined');
      
      // Convert hex back to bytes
      const privateKeyBytes = new Uint8Array(
        walletData.privateKey.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
      );
      const publicKeyBytes = new Uint8Array(
        walletData.publicKey.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
      );
      
      // Import keys back into crypto.subtle
      const privateKey = await crypto.subtle.importKey(
        "pkcs8",
        privateKeyBytes,
        { name: "Ed25519" },
        true,
        ["sign"]
      );
      
      const publicKey = await crypto.subtle.importKey(
        "raw",
        publicKeyBytes,
        { name: "Ed25519" },
        true,
        ["verify"]
      );
      
      const wallet = {
        address: walletData.address,
        publicKey: walletData.publicKey,
        keyPair: { privateKey, publicKey },
        created: walletData.created
      };
      
      this.addOutput(`🔑 Loaded existing wallet: ${walletData.address} ($BEANS)`);
      return wallet;
    } catch (error) {
      console.log('Failed to load stored wallet:', error);
      // Fall through to create new wallet
      return await this.createOrLoadWallet();
    }
  }
  
  async checkWalletStatus() {
    try {
      const storedWallet = localStorage.getItem('coinjecture_wallet');
      if (storedWallet) {
        const walletData = JSON.parse(storedWallet);
        this.addOutput(`🔑 Wallet loaded: ${walletData.address} ($BEANS)`);
        
        // Load wallet and start rewards refresh
        this.wallet = await this.createOrLoadWallet();
        this.startRewardsRefresh();
      } else {
        this.addOutput('💡 No wallet found. Use "wallet-generate" to create one.');
      }
    } catch (error) {
      console.log('Wallet status check failed:', error);
    }
  }
  
  async createSimpleSignature(data, privateKey) {
    // Create a simple hash-based signature for testing
    const dataString = JSON.stringify(data, Object.keys(data).sort());
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(dataString);
    
    // Create a simple HMAC-like signature
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    
    // Convert to hex string
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
  
  async handleSubmitProblem(args) {
    this.addMultiLineOutput([
      '💰 Problem Submission',
      '',
      'To submit a computational problem:',
      '1. Use the full COINjecture CLI',
      '2. Run: coinjectured submit-problem --type subset_sum --bounty 100',
      '',
      'Web CLI supports problem viewing only.',
      'Use the desktop CLI for problem submission.'
    ]);
  }
  
  async handleWalletGenerate(args) {
    try {
      // Check if wallet already exists
      const existingWallet = localStorage.getItem('coinjecture_wallet');
      if (existingWallet) {
        const walletData = JSON.parse(existingWallet);
        this.addMultiLineOutput([
          '⚠️  Wallet already exists!',
          '',
          `Current wallet: ${walletData.address}`,
          `Created: ${new Date(walletData.created).toLocaleString()}`,
          '',
          'To create a new wallet, clear your browser data first.',
          'Or use the desktop CLI for multiple wallets.'
        ]);
        return;
      }
      
      // Create new wallet
      this.addOutput('🔑 Generating new wallet...');
      this.wallet = await this.createOrLoadWallet();
      
      // Start rewards refresh for new wallet
      this.startRewardsRefresh();
      
      this.addMultiLineOutput([
        '✅ New wallet generated successfully!',
        '',
        `Address: ${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`,
        `Public Key: ${this.wallet.publicKey.substring(0, 16)}...`,
        `Created: ${new Date(this.wallet.created).toLocaleString()}`,
        '',
        '🔐 Your private key is securely stored in your browser.',
        '⚠️  For security, use desktop CLI for serious mining operations.',
        '',
        '💡 Use "wallet-info" to view wallet details',
        '💡 Use "rewards" to see your mining earnings',
        '💡 Use "mine --tier=mobile" to start earning $BEANS tokens!'
      ]);
      
    } catch (error) {
      this.addOutput(`❌ Wallet generation failed: ${error.message}`, 'error');
    }
  }
  
  async handleWalletInfo(args) {
    if (!this.wallet) {
      this.wallet = await this.createOrLoadWallet();
    }
    
    // Get current rewards
    let rewardsInfo = '';
    try {
      const response = await this.fetchWithFallback(`/v1/rewards/${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          const rewards = data.data;
          rewardsInfo = `💰 Current Rewards: ${rewards.total_rewards} BEANS (${rewards.blocks_mined} blocks mined)`;
        }
      }
    } catch (error) {
      rewardsInfo = '💰 Rewards: Unable to fetch (check network connection)';
    }
    
    this.addMultiLineOutput([
      '💰 Wallet Information',
      '',
      `Address: ${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`,
      `Public Key: ${this.wallet.publicKey}`,
      `Created: ${new Date(this.wallet.created).toLocaleString()}`,
      '',
      rewardsInfo,
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
  
  clearTerminal() {
    this.output.innerHTML = '';
    this.addOutput('🚀 COINjecture Web CLI');
    this.addOutput('Terminal cleared.');
  }
  
  // Add certificate notice to help users
  addCertificateNotice() {
    const notice = document.createElement('div');
    notice.id = 'certificate-notice';
    
    // Detect mobile device for better styling
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    notice.style.cssText = `
      position: fixed;
      top: 10px;
      ${isMobile ? 'left: 10px; right: 10px;' : 'right: 10px;'}
      background: #ff6b6b;
      color: white;
      padding: 15px;
      border-radius: 8px;
      font-size: ${isMobile ? '14px' : '12px'};
      max-width: ${isMobile ? '100%' : '300px'};
      z-index: 1000;
      display: none;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    
    if (isMobile) {
      notice.innerHTML = `
        <strong>🔒 SSL Certificate Required</strong><br><br>
        <strong>📱 Mobile Steps:</strong><br>
        1. Tap the link below<br>
        2. Tap "Advanced" or "Details"<br>
        3. Tap "Proceed to site"<br>
        4. Return and refresh<br><br>
        <a href="https://167.172.213.70" target="_blank" style="color: white; text-decoration: underline; font-weight: bold;">🔗 Accept Certificate</a>
      `;
    } else {
      notice.innerHTML = `
        <strong>🔒 SSL Certificate Required</strong><br>
        Click <a href="https://167.172.213.70" target="_blank" style="color: white; text-decoration: underline;">here</a> to accept the certificate, then refresh this page.
      `;
    }
    
    document.body.appendChild(notice);
  }

  // Helper method to handle API calls with certificate handling
  async fetchWithFallback(endpoint, options = {}) {
    // Add cache-busting parameter to ensure fresh data
    const separator = endpoint.includes('?') ? '&' : '?';
    const url = this.apiBase + endpoint + separator + 't=' + Date.now();
    
    try {
      const response = await fetch(url, options);
      return response;
    } catch (error) {
      // Check for certificate errors (network level)
      if (error.name === 'TypeError' && 
          (error.message.includes('Failed to fetch') || 
           error.message.includes('ERR_CERT_AUTHORITY_INVALID') ||
           error.message.includes('net::ERR_CERT_AUTHORITY_INVALID'))) {
        
        // Check if certificate has been accepted before
        const certAccepted = localStorage.getItem('coinjecture_cert_accepted');
        if (certAccepted === 'true') {
          // Certificate was accepted but still failing - try alternative approach
          this.addOutput('🔒 Certificate Issue: Even though certificate was accepted, connection is still failing.');
          this.addOutput('This may be due to browser security policies or network restrictions.');
          this.addOutput('');
          this.addOutput('💡 Alternative Solutions:');
          this.addOutput('1. Try using a different browser');
          this.addOutput('2. Disable browser security features temporarily');
          this.addOutput('3. Use a VPN or different network');
          this.addOutput('4. Contact support for assistance');
          
          this.status.innerHTML = '🔒 Certificate Accepted But Connection Failed';
          this.status.className = 'status error';
          throw new Error('Certificate accepted but connection still failing');
        }
        
        // Detect mobile device
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // Show user-friendly message about certificate
        this.addOutput('🔒 SSL Certificate Notice:');
        this.addOutput('The server uses a self-signed certificate.');
        this.addOutput('This is normal for development servers.');
        this.addOutput('');
        
        if (isMobile) {
          this.addOutput('📱 Mobile Instructions:');
          this.addOutput('1. Tap the link below to open the server');
          this.addOutput('2. Tap "Advanced" or "Details"');
          this.addOutput('3. Tap "Proceed to site" or "Continue"');
          this.addOutput('4. Return here and refresh the page');
          this.addOutput('');
          this.addOutput('🔗 Direct link: https://167.172.213.70');
        } else {
          this.addOutput('🖥️ Desktop Instructions:');
          this.addOutput('1. Click the link below to open the server');
          this.addOutput('2. Click "Advanced" or "Show Details"');
          this.addOutput('3. Click "Proceed to site" or "Continue"');
          this.addOutput('4. Return here and refresh the page');
          this.addOutput('');
          this.addOutput('🔗 Direct link: https://167.172.213.70');
        }
        
        // Add certificate acceptance button
        this.addOutput('');
        this.addOutput('✅ After accepting the certificate, refresh the page manually.');
        
        // Set status to show certificate issue
        this.status.innerHTML = '🔒 Certificate Required - Click Link Above';
        this.status.className = 'status error';
        
        // Show the certificate notice
        const notice = document.getElementById('certificate-notice');
        if (notice) {
          notice.style.display = 'block';
        }
        
        throw new Error('Certificate not accepted. Please accept the certificate first.');
      }
      // Handle mobile-specific network errors
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
      
      if (isMobile && error.message.includes('Failed to fetch')) {
        this.addOutput('📱 Mobile Network Error:');
        this.addOutput('Connection failed. This may be due to:');
        this.addOutput('• Mobile data restrictions');
        this.addOutput('• Corporate firewall');
        this.addOutput('• Network security settings');
        this.addOutput('');
        this.addOutput('💡 Try switching between WiFi and mobile data');
        this.addOutput('or use a different network connection.');
      }
      
      console.log('API call failed:', error);
      throw error;
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
        
        // Mark certificate as accepted if we got a successful response
        localStorage.setItem('coinjecture_cert_accepted', 'true');
      } else {
        this.status.innerHTML = '🌐 Network: Offline';
        this.status.className = 'status offline';
      }
    } catch (error) {
      // Check if it's a certificate error
      if (error.message.includes('Certificate not accepted')) {
        this.status.innerHTML = '🔒 Certificate Required - Click Link Above';
        this.status.className = 'status error';
      } else {
        this.status.innerHTML = '🌐 Network: Connection Error';
        this.status.className = 'status error';
      }
    }
  }

  // Initialize copy address button
  initCopyAddressButton() {
    if (this.copyAddressBtn) {
      this.copyAddressBtn.addEventListener('click', () => {
        if (this.wallet) {
          this.copyToClipboard(BEANSa93eefd297ae59e963d0977319690ffbc55e2b33);
          this.addOutput('📋 Wallet address copied to clipboard');
        } else {
          this.addOutput('❌ No wallet found. Use "wallet-generate" to create one.', 'error');
        }
      });
    }
  }

  // Copy text to clipboard
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    }
  }

  // Handle rewards command
  async handleRewards(args) {
    if (!this.wallet) {
      this.wallet = await this.createOrLoadWallet();
    }

    try {
      this.addOutput('💰 Fetching mining rewards...');
      const response = await this.fetchWithFallback(`/v1/rewards/${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          const rewards = data.data;
          
          this.addMultiLineOutput([
            '💰 Mining Rewards Breakdown',
            '',
            `Total Rewards: ${rewards.total_rewards} BEANS`,
            `Blocks Mined: ${rewards.blocks_mined}`,
            `Total Work Score: ${rewards.total_work_score}`,
            `Average Work Score: ${rewards.average_work_score}`,
            '',
            '📊 Recent Mining Activity:'
          ]);

          // Show last 5 blocks
          const recentBlocks = rewards.rewards_breakdown.slice(0, 5);
          for (const block of recentBlocks) {
            this.addOutput(`   Block #${block.block_index}: ${block.total_reward} BEANS (Work: ${block.work_score})`);
          }

          if (rewards.blocks_mined > 5) {
            this.addOutput(`   ... and ${rewards.blocks_mined - 5} more blocks`);
          }

          this.addOutput('');
          this.addOutput('💡 Use "mine --tier=mobile" to earn more rewards!');
        } else {
          this.addOutput(`❌ Error: ${data.message || 'Failed to get rewards'}`, 'error');
        }
      } else {
        this.addOutput(`❌ API Error: ${response.status}`, 'error');
      }
    } catch (error) {
      this.addOutput(`❌ Network error: ${error.message}`, 'error');
    }
  }

  // Handle export wallet command
  async handleExportWallet(args) {
    if (!this.wallet) {
      this.wallet = await this.createOrLoadWallet();
    }

    this.addMultiLineOutput([
      '🔐 Wallet Export Information',
      '',
      '⚠️  WARNING: Keep this information secure!',
      '   Anyone with access to your private key can control your wallet.',
      '',
      '📋 Wallet Details:',
      `   Address: ${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`,
      `   Public Key: ${this.wallet.publicKey}`,
      `   Private Key: ${this.wallet.keyPair.privateKey ? 'Available (stored securely)' : 'Not accessible'}`,
      `   Created: ${new Date(this.wallet.created).toLocaleString()}`,
      '',
      '💡 Backup Instructions:',
      '   1. Write down your private key on paper',
      '   2. Store it in a secure location',
      '   3. Never share it with anyone',
      '   4. Consider using a hardware wallet for large amounts',
      '',
      '🔄 To restore this wallet:',
      '   Use the private key to import the wallet in another COINjecture client'
    ]);
  }

  // Handle copy address command
  async handleCopyAddress(args) {
    if (!this.wallet) {
      this.wallet = await this.createOrLoadWallet();
    }

    try {
      await this.copyToClipboard(BEANSa93eefd297ae59e963d0977319690ffbc55e2b33);
      this.addOutput(`📋 Wallet address copied to clipboard: ${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`);
    } catch (error) {
      this.addOutput(`❌ Failed to copy address: ${error.message}`, 'error');
    }
  }

  // Update rewards dashboard
  async updateRewardsDashboard() {
    if (!this.wallet) return;

    try {
      const response = await this.fetchWithFallback(`/v1/rewards/${BEANSa93eefd297ae59e963d0977319690ffbc55e2b33}`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          const rewards = data.data;
          
          // Update dashboard elements
          if (this.walletAddress) {
            this.walletAddress.textContent = BEANSa93eefd297ae59e963d0977319690ffbc55e2b33.substring(0, 16) + '...';
          }
          if (this.rewardsTotal) {
            this.rewardsTotal.textContent = `${rewards.total_rewards} BEANS`;
          }
          if (this.blocksMined) {
            this.blocksMined.textContent = `${rewards.blocks_mined} blocks`;
          }
          if (this.walletDashboard) {
            this.walletDashboard.style.display = 'flex';
          }
        }
      }
    } catch (error) {
      // Silently fail for dashboard updates
      console.log('Dashboard update failed:', error);
    }
  }

  // Start rewards refresh interval
  startRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
    }
    
    // Update immediately
    this.updateRewardsDashboard();
    
    // Then update every 30 seconds
    this.rewardsRefreshInterval = setInterval(() => {
      this.updateRewardsDashboard();
    }, 30000);
  }

  // Stop rewards refresh interval
  stopRewardsRefresh() {
    if (this.rewardsRefreshInterval) {
      clearInterval(this.rewardsRefreshInterval);
      this.rewardsRefreshInterval = null;
    }
  }

  // Display blockchain statistics
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
}

// Download CLI function (global for onclick)
function downloadCLI(platform) {
  if (platform === 'macos') {
    // Create download link to GitHub releases
    const link = document.createElement('a');
    link.href = 'https://github.com/beanapologist/COINjecture/releases/download/v3.9.10/COINjecture-macOS-v3.6.6-Final.zip';
    link.download = 'COINjecture-macOS-v3.6.6-Final.zip';
    link.target = '_blank';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show download feedback
    const downloadCard = document.querySelector('.download-card');
    if (downloadCard) {
      const message = document.createElement('div');
      message.innerHTML = '🚀 <strong>Download started!</strong><br>Check your Downloads folder for COINjecture-macOS-v3.6.6-Final.zip';
      message.style.color = '#9d7ce8';
      message.style.marginTop = '16px';
      message.style.fontWeight = 'bold';
      message.style.padding = '12px';
      message.style.background = '#1a1a1a';
      message.style.border = '1px solid #9d7ce8';
      message.style.borderRadius = '6px';
      downloadCard.appendChild(message);
      
      // Remove message after 8 seconds
      setTimeout(() => {
        if (message.parentNode) {
          message.parentNode.removeChild(message);
        }
      }, 8000);
    }
  }
}

  // Initialize interface when page loads
document.addEventListener('DOMContentLoaded', () => {
  new WebInterface();
});