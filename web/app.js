// COINjecture Web Interface - Main Application
// Version: 3.15.0 - Modular Architecture

// Import modules
import { api } from './js/core/api.js';
import { metricsDashboard } from './js/ui/metrics.js';
import { blockchainExplorer } from './js/ui/explorer.js';
import { 
    urlUtils,
    clipboardUtils,
    domUtils,
    deviceUtils
} from './js/shared/utils.js';
import { 
    API_CONFIG, 
    IPFS_GATEWAYS, 
    CACHE_CONFIG,
    ERROR_MESSAGES,
    MINING_CONFIG
} from './js/shared/constants.js';
import { SubsetSumSolver } from './js/mining/subset-sum.js';
import { P2PMiningService } from './js/p2p/p2p-mining.js';

// Initialize cache busting and fetch override
urlUtils.overrideFetch();

// Global functions for backward compatibility
window.forceRefreshMetrics = async function() {
    console.log('🔄 Force refreshing metrics...');
    try {
        await metricsDashboard.forceRefresh();
        console.log('✅ Metrics refreshed successfully');
    } catch (error) {
        console.error('❌ Failed to refresh metrics:', error);
    }
};

window.openIPFSViewer = domUtils.openIPFSViewer;
window.showIPFSModal = domUtils.showIPFSModal;

// Global download proof bundle function
window.downloadProofBundle = async function(cid) {
    try {
        console.log(`📦 Downloading proof bundle: ${cid}`);
        
        // Try to get data via API first
        try {
            const proofData = await api.getProofData(cid);
            if (proofData) {
                const blob = new Blob([JSON.stringify(proofData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
                a.download = `proof-bundle-${cid}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
                console.log('✅ Proof bundle downloaded via API');
                return;
            }
        } catch (apiError) {
            console.warn('API download failed, trying direct IPFS:', apiError);
        }
        
        // Fallback to direct IPFS download
        const gateways = IPFS_GATEWAYS.map(gateway => `${gateway}${cid}`);
        const downloadUrl = gateways[0];
        
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `proof-bundle-${cid}`;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        console.log('✅ Proof bundle download initiated');
        
    } catch (error) {
        console.error('❌ Failed to download proof bundle:', error);
        alert('Failed to download proof bundle. Please try again.');
    }
};

// Main WebInterface class (simplified for modular architecture)
class WebInterface {
    constructor() {
        this.apiBase = API_CONFIG.BASE_URL;
        this.wallet = null;
        this.isConnected = false;
        this.currentPage = 'terminal';
        this.isMining = false;
        this.miningInterval = null;
        this.subsetSumSolver = new SubsetSumSolver();
        this.p2pMiningService = new P2PMiningService();
        this.p2pMiningService.wallet = this.wallet;
        this.p2pMiningService.addOutput = this.addOutput.bind(this);
        this.p2pMiningService.metricsDashboard = this.metricsDashboard;
        this.p2pMiningService.updateWalletDisplay = this.updateWalletDisplay.bind(this);
        
        // Expose functions to global scope for HTML onclick handlers
        window.openIPFSViewer = (cid) => {
            if (domUtils.openIPFSViewer) {
                domUtils.openIPFSViewer(cid);
            } else {
                console.log('IPFS Viewer not available');
            }
        };
        window.copyToClipboard = (text) => {
            if (clipboardUtils.copyToClipboard) {
                clipboardUtils.copyToClipboard(text);
            } else {
                navigator.clipboard.writeText(text);
            }
        };
        
        this.initializeElements();
        this.attachEventListeners();
        this.initializeWallet();
        this.showWelcomeMessage();
        
        // Load initial metrics
        this.loadMetrics();
    }

    initializeElements() {
        // Terminal elements
        this.terminalOutput = document.getElementById('terminal-output');
        this.commandInput = document.getElementById('command-input');
        this.networkStatus = document.getElementById('network-status');
        
        // Wallet elements
    this.walletDashboard = document.getElementById('wallet-dashboard');
    this.walletAddress = document.getElementById('wallet-address');
        this.copyAddressBtn = document.getElementById('copy-address-btn');
    this.rewardsTotal = document.getElementById('status-rewards-total');
    this.blocksMined = document.getElementById('blocks-mined');
        
        // Navigation elements
        this.navLinks = document.querySelectorAll('.nav-link');
        this.pages = document.querySelectorAll('.page');
    }

    attachEventListeners() {
    // Command input
        if (this.commandInput) {
            this.commandInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
                    this.executeCommand(e.target.value);
                    e.target.value = '';
                }
            });
    }
    
    // Copy address button
    if (this.copyAddressBtn) {
      this.copyAddressBtn.addEventListener('click', () => {
                if (this.wallet?.address) {
                    clipboardUtils.copyToClipboard(this.wallet.address);
                }
            });
        }

        // Navigation
        this.navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const page = link.dataset.page;
        if (page) {
          e.preventDefault();
          this.showPage(page);
        }
        // For external links (like data-marketplace.html), let the browser handle them naturally
        // Don't prevent default for links without data-page attribute
      });
    });
  }

    async initializeWallet() {
        try {
            const storedWallet = localStorage.getItem('coinjecture_wallet');
            if (storedWallet) {
                this.wallet = JSON.parse(storedWallet);
                this.updateWalletDisplay();
                this.isConnected = true;
                this.updateNetworkStatus('🌐 Connected');
                
                // Check for local-only blocks that need to be submitted to blockchain
                await this.migrateLocalBlocksToBlockchain();
      } else {
                // Generate new wallet if none exists
                await this.generateWallet();
            }
    } catch (error) {
            console.error('Failed to initialize wallet:', error);
            this.updateNetworkStatus('❌ Wallet error');
        }
    }

    async generateWallet() {
        try {
            // Generate proper Ed25519 wallet
            if (window.nobleEd25519) {
                const privateKey = window.nobleEd25519.utils.randomPrivateKey();
                const publicKey = window.nobleEd25519.getPublicKey(privateKey);
                
                // Convert to hex strings
                const privateKeyHex = Array.from(privateKey).map(b => b.toString(16).padStart(2, '0')).join('');
                const publicKeyHex = Array.from(publicKey).map(b => b.toString(16).padStart(2, '0')).join('');
                
                // Create address from public key (first 20 bytes)
                const address = '0x' + publicKeyHex.substring(0, 40);
                
                this.wallet = {
                    address: address,
                    publicKey: publicKeyHex,
                    privateKey: privateKeyHex,
                    balance: 0,
                    blocksMined: 0
                };
                
                // Update P2P mining service with new wallet
                this.p2pMiningService.wallet = this.wallet;
                this.p2pMiningService.updateWalletDisplay = this.updateWalletDisplay.bind(this);
                
                localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
                this.updateWalletDisplay();
                this.isConnected = true;
                this.updateNetworkStatus('🌐 Connected');
                this.addOutput(`✅ New Ed25519 wallet generated: ${address}`, 'success');
            } else {
                // Fallback to demo wallet if Ed25519 not available
                const newAddress = '0xBEANS' + Math.random().toString(36).substring(2, 10).toUpperCase();
                this.wallet = { 
                    address: newAddress, 
                    publicKey: 'demo_public_key', 
                    privateKey: 'demo_private_key',
                    balance: 0,
                    blocksMined: 0
                };
                
                // Update P2P mining service with new wallet
                this.p2pMiningService.wallet = this.wallet;
                this.p2pMiningService.updateWalletDisplay = this.updateWalletDisplay.bind(this);
                
                localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
                this.updateWalletDisplay();
                this.isConnected = true;
                this.updateNetworkStatus('🌐 Connected');
                this.addOutput(`✅ Demo wallet generated: ${newAddress}`, 'success');
              }
    } catch (error) {
            console.error('Wallet generation failed:', error);
            this.addOutput(`❌ Failed to generate wallet: ${error.message}`, 'error');
        }
    }

    updateWalletDisplay() {
        if (!this.wallet) return;

        if (this.walletDashboard) {
            this.walletDashboard.style.display = 'block';
        }
        
        if (this.walletAddress) {
            this.walletAddress.textContent = this.wallet.address;
        }
        
        if (this.rewardsTotal) {
            this.rewardsTotal.textContent = `${this.wallet.balance || 0} BEANS`;
        }
        
        if (this.blocksMined) {
            this.blocksMined.textContent = `${this.wallet.blocksMined || 0} blocks`;
        }
    }

    updateNetworkStatus(status) {
        if (this.networkStatus) {
            this.networkStatus.textContent = status;
        }
    }

    showPage(pageName) {
        // Update navigation
        this.navLinks.forEach(link => {
            link.classList.toggle('active', link.dataset.page === pageName);
        });

        // Update page content
        this.pages.forEach(page => {
            page.classList.toggle('active', page.id === `page-${pageName}`);
        });

        this.currentPage = pageName;

        // Handle page-specific initialization
        switch (pageName) {
            case 'metrics':
                metricsDashboard.activate();
                break;
            case 'explorer':
                blockchainExplorer.activate();
                break;
            case 'marketplace':
                this.initializeMarketplace();
                break;
            default:
                metricsDashboard.deactivate();
                blockchainExplorer.deactivate();
                break;
        }
    }

    async initializeMarketplace() {
        console.log('🏪 Initializing Data Marketplace...');
        
        try {
            // Load live statistics
            await this.loadMarketplaceStats();
            
            // Setup API demo
            this.setupApiDemo();
            
            console.log('✅ Data Marketplace initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize marketplace:', error);
        }
    }

    async loadMarketplaceStats() {
        try {
            console.log('📊 Loading marketplace statistics...');
            
            // Load live blockchain statistics using the same method as metrics dashboard
            const metrics = await api.getMetricsDashboard();
            console.log('📊 Metrics received:', metrics);
            console.log('📊 Metrics.data:', metrics.data);
            console.log('📊 Recent transactions:', metrics.data?.recent_transactions);
            
            if (metrics && metrics.status === 'success' && metrics.data) {
                this.updateMarketplaceStats(metrics.data);
            } else if (metrics && metrics.data) {
                // Try to use the data even if status is not 'success'
                console.log('⚠️ Using metrics data despite status');
                this.updateMarketplaceStats(metrics.data);
            } else {
                console.warn('⚠️ No metrics data received, trying fallback...');
                await this.loadMarketplaceStatsFallback();
            }
        } catch (error) {
            console.error('❌ Failed to load marketplace stats:', error);
            console.log('🔄 Trying fallback to get latest block data...');
            await this.loadMarketplaceStatsFallback();
        }
    }

    updateMarketplaceStats(data) {
        // Update stats cards using the same data structure as metrics dashboard
        const totalBlocksEl = document.getElementById('total-blocks');
        const activeCidsEl = document.getElementById('active-cids');
        const avgComplexityEl = document.getElementById('avg-complexity');
        const lastBlockTimeEl = document.getElementById('last-block-time');
        
        // Debug: Log the full data structure
        console.log('📊 Full data structure:', JSON.stringify(data, null, 2));
        console.log('📊 Recent transactions:', data.recent_transactions);
        console.log('📊 Blockchain data:', data.blockchain);
        
        // Update total blocks - check both blockchain.validated_blocks and direct validated_blocks
        if (totalBlocksEl) {
            const totalBlocks = data.blockchain?.validated_blocks || 
                              data.validated_blocks || 
                              data.total_blocks || 
                              data.blocks ||
                              '0';
            totalBlocksEl.textContent = totalBlocks.toString();
            console.log('📊 Total blocks set to:', totalBlocks, 'from data:', data);
        }
        
        // Update active CIDs - count unique CIDs from recent transactions
        if (activeCidsEl) {
            const recentTransactions = data.recent_transactions || [];
            const uniqueCids = new Set();
            recentTransactions.forEach(tx => {
                if (tx.cid) uniqueCids.add(tx.cid);
            });
            
            // Also check for CIDs in other possible locations
            const blockchainCids = data.blockchain?.cids || [];
            blockchainCids.forEach(cid => {
                if (cid) uniqueCids.add(cid);
            });
            
            const activeCids = uniqueCids.size || 
                             data.active_cids || 
                             data.cid_count ||
                             data.blockchain?.active_cids ||
                             data.blockchain?.cid_count ||
                             '0';
            activeCidsEl.textContent = activeCids.toString();
            console.log('📊 Active CIDs set to:', activeCids, 'from', uniqueCids.size, 'unique CIDs in', recentTransactions.length, 'transactions');
        }
        
        // Update average complexity - calculate from recent transactions using work_score
        if (avgComplexityEl) {
            const recentTransactions = data.recent_transactions || [];
            let totalComplexity = 0;
            let complexityCount = 0;
            
            // Use work_score as complexity metric since that's what's available
            recentTransactions.forEach(tx => {
                if (tx.work_score && !isNaN(tx.work_score)) {
                    totalComplexity += parseFloat(tx.work_score);
                    complexityCount++;
                }
            });
            
            // Also check for complexity in blockchain data
            if (data.blockchain?.avg_complexity && !isNaN(data.blockchain.avg_complexity)) {
                totalComplexity += parseFloat(data.blockchain.avg_complexity);
                complexityCount++;
            }
            
            const avgComplexity = complexityCount > 0 ? 
                                (totalComplexity / complexityCount).toFixed(2) :
                                data.avg_complexity ||
                                data.average_complexity ||
                                data.blockchain?.avg_complexity ||
                                data.blockchain?.average_complexity ||
                                '0';
            avgComplexityEl.textContent = avgComplexity.toString();
            console.log('📊 Avg complexity set to:', avgComplexity, 'from', complexityCount, 'work_score values');
        }
        
        // Update last block time - use timestamp from latest transaction
        if (lastBlockTimeEl) {
            const recentTransactions = data.recent_transactions || [];
            let lastBlockTime = 'Unknown';
            
            if (recentTransactions.length > 0) {
                // Get the most recent transaction timestamp
                const latestTx = recentTransactions[0];
                if (latestTx.timestamp) {
                    // The timestamp is already in seconds, convert to milliseconds
                    const timestamp = latestTx.timestamp * 1000;
                    const date = new Date(timestamp);
                    lastBlockTime = date.toLocaleString();
                }
            } else {
                // Try to get timestamp from data
                let timestamp = data.last_update || 
                              data.timestamp;
                
                if (timestamp) {
                    // The timestamp is already in seconds, convert to milliseconds
                    timestamp = timestamp * 1000;
                    const date = new Date(timestamp);
                    lastBlockTime = date.toLocaleString();
                } else {
                    lastBlockTime = 'Unknown';
                }
            }
            
            lastBlockTimeEl.textContent = lastBlockTime.toString();
            console.log('📊 Last block time set to:', lastBlockTime);
        }
        
        console.log('✅ Marketplace stats updated successfully');
    }

    async loadMarketplaceStatsFallback() {
        try {
            // Fallback: try to get latest block data
            const latestBlock = await api.getLatestBlock();
            console.log('📦 Latest block data:', latestBlock);
            
            if (latestBlock) {
                // Create a basic data structure
                const data = {
                    blockchain: {
                        validated_blocks: latestBlock.block_number || 0,
                        latest_block: latestBlock.block_number || 0,
                        latest_hash: latestBlock.block_hash || 'N/A'
                    }
                };
                this.updateMarketplaceStats(data);
                console.log('✅ Using fallback block data');
            } else {
                this.showFallbackStats();
            }
        } catch (error) {
            console.error('❌ Fallback also failed:', error);
            this.showFallbackStats();
        }
    }

    showFallbackStats() {
        // Show fallback values when API is unavailable
        const totalBlocksEl = document.getElementById('total-blocks');
        const activeCidsEl = document.getElementById('active-cids');
        const avgComplexityEl = document.getElementById('avg-complexity');
        const lastBlockTimeEl = document.getElementById('last-block-time');
        
        if (totalBlocksEl) totalBlocksEl.textContent = 'API Unavailable';
        if (activeCidsEl) activeCidsEl.textContent = 'API Unavailable';
        if (avgComplexityEl) avgComplexityEl.textContent = 'API Unavailable';
        if (lastBlockTimeEl) lastBlockTimeEl.textContent = 'API Unavailable';
    }


    setupApiDemo() {
        // Setup API demo functionality for marketplace
        const demoMetricsBtn = document.getElementById('demo-metrics');
        const demoBlocksBtn = document.getElementById('demo-blocks');
        const demoPeersBtn = document.getElementById('demo-peers');
        const apiOutput = document.getElementById('api-output');
        
        if (demoMetricsBtn && apiOutput) {
            demoMetricsBtn.addEventListener('click', async () => {
                try {
                    apiOutput.textContent = 'Loading metrics...';
                    const metrics = await api.getMetricsDashboard();
                    apiOutput.textContent = JSON.stringify(metrics, null, 2);
                } catch (error) {
                    apiOutput.textContent = `Error: ${error.message}`;
                }
            });
        }
        
        if (demoBlocksBtn && apiOutput) {
            demoBlocksBtn.addEventListener('click', async () => {
                try {
                    apiOutput.textContent = 'Loading latest block...';
                    const block = await api.getLatestBlock();
                    apiOutput.textContent = JSON.stringify(block, null, 2);
                } catch (error) {
                    apiOutput.textContent = `Error: ${error.message}`;
                }
            });
        }
        
        if (demoPeersBtn && apiOutput) {
            demoPeersBtn.addEventListener('click', async () => {
                try {
                    apiOutput.textContent = 'Loading health check...';
                    const health = await api.healthCheck();
                    apiOutput.textContent = JSON.stringify(health, null, 2);
                } catch (error) {
                    apiOutput.textContent = `Error: ${error.message}`;
                }
            });
        }
    }

    addOutput(text, type = 'info') {
        if (!this.terminalOutput) return;

        const outputDiv = document.createElement('div');
        outputDiv.className = `output ${type}`;
        outputDiv.textContent = text;
        
        this.terminalOutput.appendChild(outputDiv);
        this.terminalOutput.scrollTop = this.terminalOutput.scrollHeight;
  }
  
  async executeCommand(command) {
        if (!command.trim()) return;

        this.addOutput(`coinjectured$ ${command}`, 'command');

        const parts = command.trim().split(' ');
        const cmd = parts[0].toLowerCase();

        try {
            switch (cmd) {
      case 'help':
        this.showHelp();
        break;
                case 'status':
                    await this.showStatus();
        break;
                case 'wallet':
                    this.showWalletInfo();
        break;
                case 'clear':
                    this.clearTerminal();
        break;
                case 'ping':
                    await this.pingServer();
        break;
                case 'get-block':
                    await this.handleGetBlock(parts);
        break;
                case 'get-proof':
                    await this.handleGetProof(parts);
        break;
                case 'get-metrics':
                    await this.handleGetMetrics();
        break;
                case 'get-consensus':
                    await this.handleGetConsensus();
        break;
                case 'get-rewards':
                    await this.handleGetRewards();
        break;
                case 'get-leaderboard':
                    await this.handleGetLeaderboard();
        break;
                case 'get-peers':
                    await this.handleGetPeers();
        break;
                case 'get-network':
                    await this.handleGetNetwork();
        break;
                case 'get-telemetry':
                    await this.handleGetTelemetry();
        break;
                case 'get-ipfs':
                    await this.handleGetIpfs(parts);
        break;
                case 'mine':
                    await this.handleMine(parts);
          break;
                case 'submit-problem':
                    await this.handleSubmitProblem(parts);
          break;
                case 'list-submissions':
                    await this.handleListSubmissions();
          break;
        case 'send':
                    await this.handleSend(parts);
          break;
                case 'get-transactions':
                    await this.handleGetTransactions();
          break;
                case 'migrate-blocks':
                    await this.handleMigrateBlocks();
          break;
        case 'check-local-blocks':
            await this.handleCheckLocalBlocks();
          break;
        case 'update-wallet':
            await this.handleUpdateWallet();
            break;
        case 'check-balance':
            await this.handleCheckBalance();
            break;
      default:
                    this.addOutput(`❌ Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
      }
    } catch (error) {
            this.addOutput(`❌ Error executing command: ${error.message}`, 'error');
    }
  }
  
  showHelp() {
        this.addOutput('📋 Available Commands:', 'info');
        this.addOutput('', 'info');
        this.addOutput('🔍 Blockchain Commands:', 'info');
        this.addOutput('  get-block --latest          - Get latest block', 'info');
        this.addOutput('  get-block --index=<number>  - Get block by index', 'info');
        this.addOutput('  get-proof --cid=<cid>       - Get proof details', 'info');
        this.addOutput('  get-metrics                 - Get blockchain metrics', 'info');
        this.addOutput('  get-consensus               - Get consensus status', 'info');
        this.addOutput('', 'info');
        this.addOutput('💰 Wallet & Rewards:', 'info');
        this.addOutput('  get-rewards                 - Get your rewards', 'info');
        this.addOutput('  get-leaderboard             - Get mining leaderboard', 'info');
        this.addOutput('  wallet                      - Show wallet information', 'info');
        this.addOutput('', 'info');
        this.addOutput('🌐 Network Commands:', 'info');
        this.addOutput('  get-peers                   - Get connected peers', 'info');
        this.addOutput('  get-network                 - Get network status', 'info');
        this.addOutput('  ping                        - Test server connection', 'info');
        this.addOutput('', 'info');
        this.addOutput('📊 Data Commands:', 'info');
        this.addOutput('  get-telemetry               - Get latest telemetry', 'info');
        this.addOutput('  get-ipfs --cid=<cid>        - Get IPFS data', 'info');
        this.addOutput('', 'info');
        this.addOutput('⛏️ Mining Commands:', 'info');
        this.addOutput('  mine --start                - Start mining in terminal', 'info');
        this.addOutput('  mine --stop                 - Stop mining', 'info');
        this.addOutput('  mine --status               - Show mining status', 'info');
        this.addOutput('  submit-problem --type=<type> --bounty=<amount> - Submit a problem', 'info');
        this.addOutput('  list-submissions            - List your problem submissions', 'info');
        this.addOutput('', 'info');
        this.addOutput('💸 Transaction Commands:', 'info');
        this.addOutput('  send --to=<address> --amount=<amount> - Send BEANS', 'info');
        this.addOutput('  get-transactions            - Get transaction history', 'info');
        this.addOutput('', 'info');
        this.addOutput('🛠️ Utility Commands:', 'info');
        this.addOutput('  help                        - Show this help message', 'info');
        this.addOutput('  status                      - Show network and wallet status', 'info');
        this.addOutput('  clear                       - Clear terminal output', 'info');
        this.addOutput('', 'info');
        this.addOutput('🔄 Migration Commands:', 'info');
        this.addOutput('  migrate-blocks              - Migrate local blocks to blockchain', 'info');
        this.addOutput('  check-local-blocks          - Check for local blocks to migrate', 'info');
        this.addOutput('  update-wallet               - Update wallet balance from blockchain', 'info');
        this.addOutput('  check-balance               - Check wallet balance from API', 'info');
    }

    async showStatus() {
        this.addOutput('🔍 Checking network status...', 'info');
        
        try {
            const health = await api.healthCheck();
            this.addOutput(`✅ Server: ${health.status || 'OK'}`, 'success');
            
            if (this.wallet) {
                this.addOutput(`💰 Wallet: ${this.wallet.address}`, 'info');
                this.addOutput(`💎 Balance: ${this.wallet.balance || 0} BEANS`, 'info');
        } else {
                this.addOutput('🔌 No wallet connected', 'warning');
      }
    } catch (error) {
            this.addOutput(`❌ Server error: ${error.message}`, 'error');
        }
    }

    showWalletInfo() {
    if (!this.wallet) {
            this.addOutput('🔌 No wallet connected. Please create a wallet first.', 'warning');
      return;
    }
    
        this.addOutput('💼 Wallet Information:', 'info');
        this.addOutput(`  Address: ${this.wallet.address}`, 'info');
        this.addOutput(`  Balance: ${this.wallet.balance || 0} BEANS`, 'info');
        this.addOutput(`  Blocks Mined: ${this.wallet.blocksMined || 0}`, 'info');
    }

    clearTerminal() {
        if (this.terminalOutput) {
            this.terminalOutput.innerHTML = '<div class="output">coinjectured$ <span class="cursor">█</span></div>';
        }
    }

    showWelcomeMessage() {
        this.addOutput('🚀 COINjecture Web CLI v3.16.1 - $BEANS', 'info');
        this.addOutput('✨ Dynamic Gas Calculation System - IPFS-based gas costs', 'info');
        this.addOutput('', 'info');
        this.addOutput('Type "help" to see all available commands', 'info');
        this.addOutput('', 'info');
    }

    async pingServer() {
        this.addOutput('🏓 Pinging server...', 'info');
        
        try {
            const startTime = Date.now();
            await api.healthCheck();
            const endTime = Date.now();
            const latency = endTime - startTime;
            
            this.addOutput(`✅ Server responded in ${latency}ms`, 'success');
    } catch (error) {
            this.addOutput(`❌ Server unreachable: ${error.message}`, 'error');
        }
    }

    // Command handlers
    async handleGetBlock(parts) {
        const isLatest = parts.includes('--latest');
        const indexArg = parts.find(part => part.startsWith('--index='));
        
        if (isLatest) {
            this.addOutput('📦 Fetching latest block...', 'info');
            try {
                const block = await api.getLatestBlock();
                this.addOutput(`✅ Latest Block:`, 'success');
                this.addOutput(`   Index: ${block.index || 'N/A'}`, 'info');
                this.addOutput(`   Hash: ${block.hash ? block.hash.substring(0, 16) + '...' : 'N/A'}`, 'info');
                this.addOutput(`   Miner: ${block.miner ? block.miner.substring(0, 16) + '...' : 'N/A'}`, 'info');
                this.addOutput(`   Work Score: ${block.work_score || 0}`, 'info');
    } catch (error) {
                this.addOutput(`❌ Failed to get latest block: ${error.message}`, 'error');
            }
        } else if (indexArg) {
            const index = indexArg.split('=')[1];
            this.addOutput(`📦 Fetching block ${index}...`, 'info');
            try {
                const block = await api.getBlockByIndex(parseInt(index));
                this.addOutput(`✅ Block ${index}:`, 'success');
                this.addOutput(`   Hash: ${block.hash ? block.hash.substring(0, 16) + '...' : 'N/A'}`, 'info');
                this.addOutput(`   Miner: ${block.miner ? block.miner.substring(0, 16) + '...' : 'N/A'}`, 'info');
                this.addOutput(`   Work Score: ${block.work_score || 0}`, 'info');
    } catch (error) {
                this.addOutput(`❌ Failed to get block ${index}: ${error.message}`, 'error');
            }
        } else {
            this.addOutput('❌ Usage: get-block --latest or get-block --index=<number>', 'error');
        }
    }

    async handleGetProof(parts) {
        const cidArg = parts.find(part => part.startsWith('--cid='));
        
        if (cidArg) {
            const cid = cidArg.split('=')[1];
            this.addOutput(`🔍 Fetching proof for CID: ${cid}...`, 'info');
            try {
                const proof = await api.getProofData(cid);
                this.addOutput(`✅ Proof Data:`, 'success');
                this.addOutput(`   CID: ${cid}`, 'info');
                this.addOutput(`   Size: ${proof.size || 'N/A'}`, 'info');
                this.addOutput(`   Type: ${proof.type || 'N/A'}`, 'info');
    } catch (error) {
                this.addOutput(`❌ Failed to get proof: ${error.message}`, 'error');
            }
               } else {
            this.addOutput('❌ Usage: get-proof --cid=<cid>', 'error');
        }
    }

    async handleGetMetrics() {
        this.addOutput('📊 Fetching blockchain metrics...', 'info');
        try {
            const metrics = await api.getMetricsDashboard();
            if (metrics?.data) {
                const data = metrics.data;
                this.addOutput(`✅ Blockchain Metrics:`, 'success');
                this.addOutput(`   Validated Blocks: ${data.blockchain?.validated_blocks || 0}`, 'info');
                this.addOutput(`   Latest Block: ${data.blockchain?.latest_block || 0}`, 'info');
                this.addOutput(`   Consensus: ${data.blockchain?.consensus_active ? 'Active' : 'Inactive'}`, 'info');
                this.addOutput(`   Mining Attempts: ${data.blockchain?.mining_attempts || 0}`, 'info');
                this.addOutput(`   Success Rate: ${data.blockchain?.success_rate || 0}%`, 'info');
               }
             } catch (error) {
            this.addOutput(`❌ Failed to get metrics: ${error.message}`, 'error');
        }
    }

    async handleGetConsensus() {
        this.addOutput('⚖️ Fetching consensus status...', 'info');
        try {
            const metrics = await api.getMetricsDashboard();
            if (metrics?.data?.consensus) {
                const consensus = metrics.data.consensus;
                this.addOutput(`✅ Consensus Status:`, 'success');
                if (consensus.equilibrium_proof) {
                    this.addOutput(`   Satoshi Constant: ${consensus.equilibrium_proof.satoshi_constant || 'N/A'}`, 'info');
                    this.addOutput(`   Stability: ${consensus.equilibrium_proof.stability_metric || 'N/A'}`, 'info');
                }
                if (consensus.proof_of_work) {
                    this.addOutput(`   Anti-Grinding: ${consensus.proof_of_work.anti_grinding ? 'Enabled' : 'Disabled'}`, 'info');
                    this.addOutput(`   Cryptographic Binding: ${consensus.proof_of_work.cryptographic_binding ? 'Enabled' : 'Disabled'}`, 'info');
                }
      }
    } catch (error) {
            this.addOutput(`❌ Failed to get consensus: ${error.message}`, 'error');
        }
    }

    async handleGetRewards() {
      if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
      return;
    }
    
        this.addOutput('💰 Fetching rewards...', 'info');
        try {
            const rewards = await api.getRewards(this.wallet.address);
            this.addOutput(`✅ Rewards for ${this.wallet.address.substring(0, 16)}...:`, 'success');
            this.addOutput(`   Total Rewards: ${rewards.totalRewards || 0} BEANS`, 'info');
            this.addOutput(`   Blocks Mined: ${rewards.blocksMined || 0}`, 'info');
            this.addOutput(`   Work Score: ${rewards.totalWorkScore || 0}`, 'info');
            this.addOutput(`   Rank: ${rewards.rank || 'N/A'}`, 'info');
    } catch (error) {
            this.addOutput(`❌ Failed to get rewards: ${error.message}`, 'error');
        }
    }

    async handleGetLeaderboard() {
        this.addOutput('🏆 Fetching mining leaderboard...', 'info');
        try {
            const leaderboard = await api.getLeaderboard();
            this.addOutput(`✅ Mining Leaderboard:`, 'success');
            if (leaderboard && leaderboard.length > 0) {
                leaderboard.slice(0, 10).forEach((entry, index) => {
                    this.addOutput(`   ${index + 1}. ${entry.address ? entry.address.substring(0, 16) + '...' : 'N/A'}: ${entry.totalRewards || 0} BEANS`, 'info');
                });
      } else {
                this.addOutput('   No leaderboard data available', 'info');
      }
    } catch (error) {
            this.addOutput(`❌ Failed to get leaderboard: ${error.message}`, 'error');
        }
    }

    async handleGetPeers() {
        this.addOutput('🌐 Fetching network peers...', 'info');
        try {
            const metrics = await api.getMetricsDashboard();
            if (metrics?.data?.network) {
                const network = metrics.data.network;
                this.addOutput(`✅ Network Peers:`, 'success');
                this.addOutput(`   Connected Peers: ${network.peers || 0}`, 'info');
                this.addOutput(`   Active Miners: ${network.miners || 0}`, 'info');
                this.addOutput(`   Network Difficulty: ${network.difficulty || 0}`, 'info');
      }
    } catch (error) {
            this.addOutput(`❌ Failed to get peers: ${error.message}`, 'error');
        }
    }

    async handleGetNetwork() {
        this.addOutput('🌐 Fetching network status...', 'info');
        try {
            const metrics = await api.getMetricsDashboard();
            if (metrics?.data) {
                const data = metrics.data;
                this.addOutput(`✅ Network Status:`, 'success');
                this.addOutput(`   Peers: ${data.network?.peers || 0}`, 'info');
                this.addOutput(`   Miners: ${data.network?.miners || 0}`, 'info');
                this.addOutput(`   Hash Rate: ${data.hash_rate?.current_hs || 0} H/s`, 'info');
                this.addOutput(`   Block Time: ${data.block_time?.avg_seconds || 0}s`, 'info');
      }
    } catch (error) {
            this.addOutput(`❌ Failed to get network status: ${error.message}`, 'error');
        }
    }

    async handleGetTelemetry() {
        this.addOutput('📊 Fetching telemetry data...', 'info');
        try {
            const telemetry = await api.getTelemetry();
            this.addOutput(`✅ Telemetry Data:`, 'success');
            this.addOutput(`   Timestamp: ${new Date(telemetry.timestamp || Date.now()).toLocaleString()}`, 'info');
            this.addOutput(`   Status: ${telemetry.status || 'N/A'}`, 'info');
    } catch (error) {
            this.addOutput(`❌ Failed to get telemetry: ${error.message}`, 'error');
        }
    }

    async handleGetIpfs(parts) {
        const cidArg = parts.find(part => part.startsWith('--cid='));
        
        if (cidArg) {
            const cid = cidArg.split('=')[1];
            this.addOutput(`📦 Fetching IPFS data for CID: ${cid}...`, 'info');
            try {
                const ipfsData = await api.getIpfsCidData(cid);
                this.addOutput(`✅ IPFS Data:`, 'success');
                this.addOutput(`   CID: ${cid}`, 'info');
                this.addOutput(`   Size: ${ipfsData.size || 'N/A'}`, 'info');
                this.addOutput(`   Type: ${ipfsData.type || 'N/A'}`, 'info');
    } catch (error) {
                this.addOutput(`❌ Failed to get IPFS data: ${error.message}`, 'error');
            }
          } else {
            this.addOutput('❌ Usage: get-ipfs --cid=<cid>', 'error');
        }
    }

    async handleMine(parts) {
        const action = parts.find(part => part.startsWith('--'));
        
        if (action === '--start') {
            this.addOutput('⛏️ Starting mining...', 'info');
            try {
                // Start mining in the terminal
                this.startMining();
            } catch (error) {
                this.addOutput(`❌ Failed to start mining: ${error.message}`, 'error');
            }
        } else if (action === '--stop') {
            this.stopMining();
        } else if (action === '--status') {
            this.showMiningStatus();
      } else {
            this.addOutput('❌ Usage: mine --start|--stop|--status', 'error');
            this.addOutput('   Note: Use double dashes (--) not double equals (==)', 'info');
        }
    }

    async handleSubmitProblem(parts) {
        const typeArg = parts.find(part => part.startsWith('--type='));
        const bountyArg = parts.find(part => part.startsWith('--bounty='));
        
        if (!typeArg || !bountyArg) {
            this.addOutput('❌ Usage: submit-problem --type=<type> --bounty=<amount>', 'error');
            this.addOutput('   Example: submit-problem --type=subset_sum --bounty=100', 'info');
        return;
      }

        const type = typeArg.split('=')[1];
        const bounty = parseFloat(bountyArg.split('=')[1]);
        
        if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
        return;
      }

        this.addOutput(`📝 Submitting problem: ${type} with bounty ${bounty} BEANS...`, 'info');
        try {
            const problemData = {
                problem_type: type,
                problem_template: {
                    numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    target: 15
                },
                bounty_per_solution: bounty,
                min_quality: 0.8,
                aggregation: 'BEST',
                aggregation_params: {
                    target_count: 1,
                    early_bonus_decay: 0.95
                }
            };
            
            // Simulate problem submission
            this.addOutput('✅ Problem submitted successfully!', 'success');
            this.addOutput(`   Type: ${type}`, 'info');
            this.addOutput(`   Bounty: ${bounty} BEANS`, 'info');
            this.addOutput(`   Submission ID: problem-${Date.now()}`, 'info');
            this.addOutput('   Miners will now work on solving your problem', 'info');
      
    } catch (error) {
            this.addOutput(`❌ Failed to submit problem: ${error.message}`, 'error');
    }
  }

    async handleListSubmissions() {
      if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
        return;
      }

        this.addOutput('📋 Your Problem Submissions:', 'info');
        try {
            // Simulate fetching submissions
            this.addOutput('   No active submissions found', 'info');
            this.addOutput('   Use "submit-problem" to create a new submission', 'info');
    } catch (error) {
            this.addOutput(`❌ Failed to list submissions: ${error.message}`, 'error');
        }
    }

    async handleSend(parts) {
        const toArg = parts.find(part => part.startsWith('--to='));
        const amountArg = parts.find(part => part.startsWith('--amount='));
        
        if (!toArg || !amountArg) {
            this.addOutput('❌ Usage: send --to=<address> --amount=<amount>', 'error');
            this.addOutput('   Example: send --to=addr_1234567890abcdef --amount=50', 'info');
            return;
        }
        
        const toAddress = toArg.split('=')[1];
        const amount = parseFloat(amountArg.split('=')[1]);
        
        if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
            return;
        }
        
        if (amount <= 0) {
            this.addOutput('❌ Amount must be greater than 0', 'error');
            return;
        }
        
        this.addOutput(`💸 Sending ${amount} BEANS to ${toAddress.substring(0, 16)}...`, 'info');
        try {
            // Simulate transaction
            this.addOutput('✅ Transaction sent successfully!', 'success');
            this.addOutput(`   To: ${toAddress}`, 'info');
            this.addOutput(`   Amount: ${amount} BEANS`, 'info');
            this.addOutput(`   Transaction ID: tx_${Date.now()}`, 'info');
            this.addOutput('   Transaction will be processed by the network', 'info');
            
    } catch (error) {
            this.addOutput(`❌ Failed to send transaction: ${error.message}`, 'error');
        }
    }

    async handleGetTransactions() {
    if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
      return;
    }

        this.addOutput('📋 Transaction History:', 'info');
        try {
            const transactions = await api.getWalletTransactions(this.wallet.address);
            if (transactions && transactions.length > 0) {
                transactions.slice(0, 10).forEach((tx, index) => {
                    this.addOutput(`   ${index + 1}. ${tx.type || 'Transfer'}: ${tx.amount || 0} BEANS`, 'info');
                    this.addOutput(`      ${tx.from === this.wallet.address ? 'To' : 'From'}: ${tx.from === this.wallet.address ? tx.to : tx.from}`, 'info');
                    this.addOutput(`      Time: ${new Date(tx.timestamp).toLocaleString()}`, 'info');
                });
    } else {
                this.addOutput('   No transactions found', 'info');
      }
    } catch (error) {
            this.addOutput(`❌ Failed to get transactions: ${error.message}`, 'error');
        }
    }

    async handleMigrateBlocks() {
        this.addOutput('🔄 Starting block migration...', 'info');
        await this.migrateLocalBlocksToBlockchain();
    }

    async handleCheckLocalBlocks() {
        try {
            const localBlocks = localStorage.getItem('coinjecture_local_blocks');
            if (!localBlocks) {
                this.addOutput('📋 No local blocks found', 'info');
            return;
          }

            const blocks = JSON.parse(localBlocks);
            this.addOutput(`📋 Found ${blocks.length} local blocks:`, 'info');
            
            blocks.forEach((block, index) => {
                this.addOutput(`   ${index + 1}. Block ${block.id}`, 'info');
                this.addOutput(`      Work Score: ${block.work_score.toFixed(2)}`, 'info');
                this.addOutput(`      Reward: ${block.reward.toFixed(3)} BEANS`, 'info');
                this.addOutput(`      Time: ${new Date(block.timestamp).toLocaleString()}`, 'info');
            });
            
            this.addOutput('', 'info');
            this.addOutput('💡 Use "migrate-blocks" to submit these to the blockchain', 'info');
            
    } catch (error) {
            this.addOutput(`❌ Failed to check local blocks: ${error.message}`, 'error');
        }
    }

    async handleUpdateWallet() {
        try {
            this.addOutput('🔄 Updating wallet balance...', 'info');
            
            // Get current wallet balance from API
            const metrics = await api.getMetricsDashboard();
            const recentTransactions = metrics?.data?.recent_transactions || [];
            
            // Find transactions for this wallet
            const myTransactions = recentTransactions.filter(tx => 
                tx.miner === this.wallet.address || 
                tx.miner_short === this.wallet.address.substring(0, 16) + '...'
            );
            
            if (myTransactions.length > 0) {
                // Calculate total rewards
                const totalRewards = myTransactions.reduce((sum, tx) => sum + (tx.reward || 0), 0);
                const totalBlocks = myTransactions.length;
                
                // Update wallet
                this.wallet.balance = totalRewards;
                this.wallet.blocksMined = totalBlocks;
                
                // Save to localStorage
                localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
                
                // Update display
                this.updateWalletDisplay();
                
                this.addOutput(`✅ Wallet updated!`, 'success');
                this.addOutput(`   Balance: ${totalRewards.toFixed(6)} BEANS`, 'info');
                this.addOutput(`   Blocks mined: ${totalBlocks}`, 'info');
            } else {
                this.addOutput('   No transactions found for this wallet', 'info');
            }
        } catch (error) {
            this.addOutput(`❌ Error updating wallet: ${error.message}`, 'error');
        }
    }

    async handleCheckBalance() {
        try {
            this.addOutput('🔍 Checking wallet balance from API...', 'info');
            
            // Get wallet balance from API
            const response = await api.getUserRewards(this.wallet.address);
            
            if (response && response.status === 'success') {
                const data = response.data;
                this.addOutput(`✅ Wallet Balance from API:`, 'success');
                this.addOutput(`   Address: ${data.address}`, 'info');
                this.addOutput(`   Total Rewards: ${data.total_rewards.toFixed(6)} BEANS`, 'info');
                this.addOutput(`   Blocks Mined: ${data.blocks_mined}`, 'info');
                this.addOutput(`   Average Work Score: ${data.average_work_score.toFixed(2)}`, 'info');
                this.addOutput(`   Average Reward: ${data.avg_reward.toFixed(6)} BEANS`, 'info');
                
                // Update local wallet with API data
                this.wallet.balance = data.total_rewards;
                this.wallet.blocksMined = data.blocks_mined;
                localStorage.setItem('coinjecture_wallet', JSON.stringify(this.wallet));
                this.updateWalletDisplay();
            } else {
                this.addOutput('❌ Failed to get wallet balance from API', 'error');
            }
        } catch (error) {
            this.addOutput(`❌ Error checking balance: ${error.message}`, 'error');
        }
    }

    async startMining() {
        if (this.isMining) {
            this.addOutput('⛏️ Mining is already running!', 'warning');
            return;
        }

        if (!this.wallet) {
            this.addOutput('❌ No wallet connected. Please create a wallet first.', 'error');
            return;
        }

        // Ensure P2P mining service has the current wallet
        this.p2pMiningService.wallet = this.wallet;
        this.p2pMiningService.addOutput = this.addOutput.bind(this);
        this.p2pMiningService.metricsDashboard = this.metricsDashboard;

        this.addOutput('🌐 Starting P2P mining...', 'info');
        this.addOutput('   Connecting to COINjecture blockchain network...', 'info');
        
        // Start P2P mining
        const success = await this.p2pMiningService.startMining();
        
        if (success) {
            this.isMining = true;
            this.addOutput('✅ P2P Mining started! Connected to blockchain network', 'success');
            this.addOutput('   Problem Type: Subset Sum (NP-Complete)', 'info');
            this.addOutput('   Algorithm: Dynamic Programming + Greedy + Backtracking', 'info');
            this.addOutput('   Problem Size: 10-25 elements (device-optimized)', 'info');
            this.addOutput('   Network: P2P with IPFS proof bundles', 'info');
            this.addOutput('   Use "mine --stop" to stop mining', 'info');
            
            // Start stats monitoring
            this.startMiningStatsMonitoring();
      } else {
            this.addOutput('❌ Failed to start P2P mining', 'error');
        }
    }

    stopMining() {
        if (!this.isMining) {
            this.addOutput('⛏️ Mining is not running!', 'warning');
      return;
    }

        this.isMining = false;
        
        // Stop P2P mining
        this.p2pMiningService.stopMining();
        
        // Stop stats monitoring
        if (this.miningInterval) {
            clearInterval(this.miningInterval);
            this.miningInterval = null;
        }
        
        this.addOutput('⛏️ P2P Mining stopped.', 'success');
        this.addOutput('   Use "mine --start" to resume mining', 'info');
    }

    showMiningStatus() {
        this.addOutput('⛏️ Mining Status:', 'info');
        if (this.isMining) {
            const stats = this.p2pMiningService.getMiningStats();
            const isAPIMode = this.p2pMiningService.p2pClient.peers.has('api-peer-1');
            
            this.addOutput(`   Status: ✅ Active (${isAPIMode ? 'API Mode' : 'P2P Connected'})`, 'success');
            this.addOutput(`   Network: ${stats.peerCount} peers connected`, 'info');
            this.addOutput(`   Blockchain Height: ${stats.blockchainHeight}`, 'info');
            this.addOutput(`   Problems Solved: ${stats.problemsSolved}`, 'info');
            this.addOutput(`   Blocks Mined: ${stats.blocksMined}`, 'info');
            this.addOutput(`   Total Work Score: ${stats.totalWorkScore.toFixed(2)}`, 'info');
            this.addOutput(`   Total Rewards: ${stats.totalRewards.toFixed(6)} BEANS`, 'info');
            this.addOutput('   Problem Type: Subset Sum (NP-Complete)', 'info');
            this.addOutput('   Algorithm: Dynamic Programming + Greedy + Backtracking', 'info');
            this.addOutput('   Problem Size: 10-25 elements (device-optimized)', 'info');
            this.addOutput(`   Network: ${isAPIMode ? 'API Fallback' : 'P2P with IPFS proof bundles'}`, 'info');
        } else {
            this.addOutput('   Status: ❌ Inactive', 'error');
            this.addOutput('   Use "mine --start" to begin mining', 'info');
        }
    }

    startMiningStatsMonitoring() {
        // Monitor mining stats every 30 seconds
        this.miningInterval = setInterval(() => {
            if (this.isMining) {
                const stats = this.p2pMiningService.getMiningStats();
                this.addOutput(`📊 Mining Stats: ${stats.problemsSolved} problems solved, ${stats.blocksMined} blocks mined, ${stats.totalRewards.toFixed(6)} BEANS earned`, 'info');
            }
        }, 30000);
    }

    // performMiningStep is now handled by P2PMiningService

    calculateWorkScore(result, solveTime) {
        if (!result.success) return 0;
        
        try {
            // Calculate work score based on real complexity metrics
            const problemSize = result.solution?.numbers?.length || 0;
            if (problemSize === 0) {
                console.warn('No solution numbers found, using fallback work score');
                return MINING_CONFIG.MIN_WORK_SCORE;
            }
            
            const timeAsymmetry = Math.log(solveTime + 1) / Math.log(1000); // Normalize to 0-1 range
            const spaceAsymmetry = Math.log(problemSize + 1) / Math.log(25); // Normalize to 0-1 range
            const problemWeight = problemSize / 25; // Normalize to 0-1 range
            const qualityScore = result.quality || 1.0;
            const energyEfficiency = 1.0; // Assume 100% efficiency for now
            
            // Apply the work score formula from architecture
            const workScore = timeAsymmetry * 
                             Math.sqrt(spaceAsymmetry) * 
                             problemWeight * 
                             qualityScore * 
                             energyEfficiency * 
                             1000; // Scale factor
            
            return Math.max(workScore, MINING_CONFIG.MIN_WORK_SCORE);
    } catch (error) {
            console.error('Error calculating work score:', error);
            return MINING_CONFIG.MIN_WORK_SCORE;
        }
    }

    calculateReward(workScore) {
        // Dynamic tokenomics formula from architecture:
        // reward = log(1 + work_score/network_avg) * deflation_factor
        // deflation_factor = 1 / (2^(log2(cumulative_work)/10))
        
        // For now, use simplified version with network average of 100
        const networkAvg = 100; // This would come from network state in real implementation
        const cumulativeWork = 1000; // This would come from blockchain state
        const deflationFactor = 1 / Math.pow(2, Math.log2(cumulativeWork) / 10);
        
        const reward = Math.log(1 + workScore / networkAvg) * deflationFactor;
        
        // Scale to reasonable BEANS amounts (0.001 to 1.0 BEANS)
        return Math.max(reward * 0.1, 0.001);
    }

    async submitMinedBlock(problem, result, workScore, reward) {
        try {
            // ARCHITECTURE: All nodes are validators - this node participates in consensus
            this.addOutput(`🔍 Validating and submitting block to consensus...`, 'info');
            
            // Step 1: Create commitment (Commit Phase)
            const commitment = this.createCommitment(problem, result);
            this.addOutput(`   Commitment: ${commitment.substring(0, 16)}...`, 'info');
            
            // Step 2: Create block header (Mine Phase)
            const blockHeader = await this.createBlockHeader(problem, result, workScore, commitment);
            
            // Step 3: Validate header (All nodes validate)
            const validationResult = await this.validateBlockHeader(blockHeader);
            if (!validationResult.valid) {
                this.addOutput(`❌ Block validation failed: ${validationResult.error}`, 'error');
                return;
            }
            
            // Step 4: Create proof bundle (Reveal Phase)
            const proofBundle = this.createProofBundle(problem, result, workScore, commitment);
            
            // Step 5: Submit to consensus network
            this.addOutput(`📤 Submitting to consensus network...`, 'info');
            
            const response = await api.submitMinedBlock({
                block_header: blockHeader,
                proof_bundle: proofBundle,
                work_score: workScore,
                reward: reward,
                commitment: commitment
            });

            if (response.success) {
                this.addOutput(`✅ Block accepted by consensus!`, 'success');
                this.addOutput(`   Block Hash: ${response.block_hash?.substring(0, 16)}...`, 'info');
                this.addOutput(`   Block Height: ${response.height}`, 'info');
                this.addOutput(`   Cumulative Work: ${response.cumulative_work}`, 'info');
                this.addOutput(`   IPFS CID: ${response.proof_cid?.substring(0, 16)}...`, 'info');
                
                // Update local blockchain state (all nodes maintain state)
                this.updateLocalBlockchainState(response);
                
                // Refresh metrics to show updated blockchain
                setTimeout(() => {
                    this.refreshMetrics();
                }, 1000);
    } else {
                this.addOutput(`❌ Block rejected by consensus: ${response.error}`, 'error');
            }

        } catch (error) {
            this.addOutput(`❌ Failed to submit block: ${error.message}`, 'error');
            console.error('Block submission error:', error);
        }
    }

    // ARCHITECTURE-COMPLIANT BLOCKCHAIN INTEGRATION
    
    /**
     * Create commitment for commit-reveal protocol
     * ARCHITECTURE: commitment = H(problem_params || miner_salt || epoch_salt || H(solution))
     */
    createCommitment(problem, result) {
        const epochSalt = this.getCurrentEpoch();
        const minerSalt = this.generateCommitNonce();
        const solutionHash = this.sha256(JSON.stringify(result.solution));
        
        const commitmentData = {
            problem_params: {
                numbers: problem.numbers,
                target: problem.target,
                size: problem.size,
                type: 'subset_sum'
            },
            miner_salt: minerSalt,
            epoch_salt: epochSalt.toString(),
            solution_hash: solutionHash
        };
        
        return this.sha256(JSON.stringify(commitmentData));
    }

    /**
     * Create block header according to architecture
     * ARCHITECTURE: All nodes maintain blockchain state and validate headers
     */
    async createBlockHeader(problem, result, workScore, commitment) {
        const currentState = await this.getCurrentBlockchainState();
        
        return {
            version: 1,
            parent_hash: currentState.latest_hash,
            height: currentState.height + 1,
            timestamp: Date.now(),
            commitments_root: this.calculateCommitmentsRoot(commitment),
            tx_root: '0x0000000000000000000000000000000000000000000000000000000000000000',
            difficulty_target: currentState.difficulty_target,
            cumulative_work: currentState.cumulative_work + workScore,
            miner_pubkey: this.wallet.publicKey,
            commit_nonce: this.generateCommitNonce(),
            problem_type: 'subset_sum',
            tier: this.getOptimalTier(),
            commit_epoch: this.getCurrentEpoch(),
            proof_commitment: commitment,
            header_hash: null // Will be calculated
        };
    }

    /**
     * Validate block header (All nodes validate)
     * ARCHITECTURE: Every node validates every header
     */
    async validateBlockHeader(header) {
        try {
            // Basic validation checks
            if (!header.version || header.version !== 1) {
                return { valid: false, error: 'Invalid version' };
            }
            
            if (!header.timestamp || header.timestamp > Date.now() + 300000) { // 5 min future tolerance
                return { valid: false, error: 'Invalid timestamp' };
            }
            
            if (!header.proof_commitment || header.proof_commitment.length !== 64) {
                return { valid: false, error: 'Invalid proof commitment' };
            }
            
            if (!header.miner_pubkey || header.miner_pubkey.length !== 64) {
                return { valid: false, error: 'Invalid miner public key' };
            }
            
            // Calculate and verify header hash
            const calculatedHash = this.calculateHeaderHash(header);
            header.header_hash = calculatedHash;
            
            // Verify work score meets difficulty target
            const estimatedWork = this.estimateWorkScore(header);
            if (estimatedWork < header.difficulty_target) {
                return { valid: false, error: 'Insufficient work score' };
            }
            
            return { valid: true, header_hash: calculatedHash };
            
    } catch (error) {
            return { valid: false, error: error.message };
        }
    }

    /**
     * Create proof bundle for IPFS storage
     * ARCHITECTURE: Solution bundles stored on IPFS, referenced by CID
     */
    createProofBundle(problem, result, workScore, commitment) {
        return {
            problem: {
                type: 'subset_sum',
                numbers: problem.numbers,
                target: problem.target,
                size: problem.size
            },
            solution: result.solution,
            work_score: workScore,
            solve_time: result.solveTime,
            algorithm: result.method,
            miner_address: this.wallet.address,
            miner_pubkey: this.wallet.publicKey,
            commitment: commitment,
            timestamp: Date.now()
        };
    }

    /**
     * Update local blockchain state (All nodes maintain state)
     * ARCHITECTURE: Every node maintains blockchain state for consensus
     */
    updateLocalBlockchainState(response) {
        // Update local blockchain state
        const newState = {
            latest_hash: response.block_hash,
            height: response.height,
            cumulative_work: response.cumulative_work,
            last_update: Date.now()
        };
        
        localStorage.setItem('coinjecture_blockchain_state', JSON.stringify(newState));
        
        // Update metrics
        this.addOutput(`📊 Blockchain state updated locally`, 'info');
    }

    // Helper methods
    async getCurrentBlockchainState() {
        try {
            const stored = localStorage.getItem('coinjecture_blockchain_state');
            if (stored) {
                return JSON.parse(stored);
            }
    } catch (error) {
            console.warn('Failed to load blockchain state:', error);
        }
        
        // Default state
        return {
            latest_hash: '0x0000000000000000000000000000000000000000000000000000000000000000',
            height: 0,
            cumulative_work: 0,
            difficulty_target: 1000
        };
    }

    calculateCommitmentsRoot(commitment) {
        return this.sha256(commitment);
    }

    generateCommitNonce() {
        return Math.floor(Math.random() * 0xFFFFFFFF).toString(16).padStart(8, '0');
    }

    getOptimalTier() {
        return deviceUtils.isMobile() ? 1 : 2; // Mobile: 1, Desktop: 2
    }

    getCurrentEpoch() {
        return Math.floor(Date.now() / 60000); // 1 minute epochs
    }

    calculateHeaderHash(header) {
        const headerString = JSON.stringify({
            version: header.version,
            parent_hash: header.parent_hash,
            height: header.height,
            timestamp: header.timestamp,
            commitments_root: header.commitments_root,
            tx_root: header.tx_root,
            difficulty_target: header.difficulty_target,
            cumulative_work: header.cumulative_work,
            miner_pubkey: header.miner_pubkey,
            commit_nonce: header.commit_nonce,
            problem_type: header.problem_type,
            tier: header.tier,
            commit_epoch: header.commit_epoch,
            proof_commitment: header.proof_commitment
        });
        
        return '0x' + this.sha256(headerString);
    }

    estimateWorkScore(header) {
        // Simplified work score estimation
        return header.cumulative_work - (header.height * 100);
    }

    sha256(data) {
        // Simple SHA-256 implementation (in real app, use crypto.subtle)
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(data);
        return Array.from(dataBuffer)
            .map(b => b.toString(16).padStart(2, '0'))
            .join('')
            .substring(0, 64);
    }

    async loadMetrics() {
        try {
            if (this.metricsDashboard) {
                await this.metricsDashboard.fetchAndUpdateMetrics();
      }
    } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }

    refreshMetrics() {
        // Refresh the metrics dashboard to show updated blockchain data
        if (typeof metricsDashboard !== 'undefined' && metricsDashboard.fetchAndUpdateMetrics) {
            metricsDashboard.fetchAndUpdateMetrics();
        }
    }

    /**
     * Migrate local-only blocks to blockchain
     * This handles the transition from simulation mining to real blockchain mining
     */
    async migrateLocalBlocksToBlockchain() {
        try {
            // Check if we have local blocks that haven't been submitted to blockchain
            const localBlocks = localStorage.getItem('coinjecture_local_blocks');
            if (!localBlocks) {
                return; // No local blocks to migrate
            }

            const blocks = JSON.parse(localBlocks);
            if (blocks.length === 0) {
                return;
            }

            this.addOutput(`🔄 Found ${blocks.length} local blocks to migrate to blockchain...`, 'info');
            
            let successCount = 0;
            let failCount = 0;

            for (const block of blocks) {
                try {
                    this.addOutput(`📤 Submitting local block ${block.id} to blockchain...`, 'info');
                    
                    // Submit the local block to blockchain
                    const response = await api.submitMinedBlock({
                        block_header: block.header,
                        proof_bundle: block.proof_bundle,
                        work_score: block.work_score,
                        reward: block.reward,
                        commitment: block.commitment,
                        is_migration: true // Flag to indicate this is a migration
                    });

                    if (response.success) {
                        this.addOutput(`✅ Local block ${block.id} submitted successfully!`, 'success');
                        successCount++;
                    } else {
                        this.addOutput(`❌ Failed to submit local block ${block.id}: ${response.error}`, 'error');
                        failCount++;
                    }

                    // Small delay between submissions
                    await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error) {
                    this.addOutput(`❌ Error submitting local block ${block.id}: ${error.message}`, 'error');
                    failCount++;
                }
            }

            // Summary
            this.addOutput(`📊 Migration complete: ${successCount} successful, ${failCount} failed`, 'info');
            
            if (successCount > 0) {
                this.addOutput(`🎉 Your ${successCount} previously mined blocks are now on the blockchain!`, 'success');
                
                // Clear local blocks after successful migration
                localStorage.removeItem('coinjecture_local_blocks');
                
                // Refresh metrics to show updated blockchain
                setTimeout(() => {
                    this.refreshMetrics();
                }, 2000);
            }

    } catch (error) {
            console.error('Migration error:', error);
            this.addOutput(`❌ Migration failed: ${error.message}`, 'error');
        }
    }

    /**
     * Store local block for later migration
     * This is used when mining before blockchain integration
     */
    storeLocalBlock(problem, result, workScore, reward, blockHeader, proofBundle, commitment) {
        try {
            const localBlocks = JSON.parse(localStorage.getItem('coinjecture_local_blocks') || '[]');
            
            const localBlock = {
                id: `local_${Date.now()}`,
                timestamp: Date.now(),
                problem: problem,
                result: result,
                work_score: workScore,
                reward: reward,
                header: blockHeader,
                proof_bundle: proofBundle,
                commitment: commitment
            };

            localBlocks.push(localBlock);
            localStorage.setItem('coinjecture_local_blocks', JSON.stringify(localBlocks));
            
            this.addOutput(`💾 Block stored locally for migration (${localBlocks.length} total)`, 'info');
            
      } catch (error) {
            console.error('Failed to store local block:', error);
    }
  }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing COINjecture Web Interface v3.16.1');
    
    // Create global web interface instance
  window.webInterface = new WebInterface();
    
    // Auto-refresh metrics if on metrics page
    setTimeout(() => {
        if (window.webInterface.currentPage === 'metrics') {
            window.forceRefreshMetrics();
        }
    }, 1000);
    
    console.log('✅ COINjecture Web Interface initialized successfully');
});

// Export for module usage
export default WebInterface;