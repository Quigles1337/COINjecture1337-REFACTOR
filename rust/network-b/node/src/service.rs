// Node Service
// Main orchestrator tying all components together

use crate::chain::ChainState;
use crate::config::NodeConfig;
use crate::genesis::{create_genesis_block, GenesisConfig};
use crate::validator::BlockValidator;
use coinject_consensus::{Miner, MiningConfig};
use coinject_core::Address;
use coinject_mempool::{ProblemMarketplace, TransactionPool};
use coinject_network::{NetworkConfig, NetworkEvent, NetworkService};
use coinject_rpc::{RpcServer, RpcServerState};
use coinject_state::AccountState;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{mpsc, RwLock};
use tokio::time;

/// Main node service coordinating all blockchain components
pub struct CoinjectNode {
    config: NodeConfig,
    chain: Arc<ChainState>,
    state: Arc<AccountState>,
    validator: Arc<BlockValidator>,
    marketplace: Arc<RwLock<ProblemMarketplace>>,
    tx_pool: Arc<RwLock<TransactionPool>>,
    miner: Option<Arc<RwLock<Miner>>>,
    network: Option<NetworkService>,
    rpc: Option<RpcServer>,
    shutdown_tx: mpsc::Sender<()>,
    shutdown_rx: mpsc::Receiver<()>,
}

impl CoinjectNode {
    /// Create and initialize a new node
    pub async fn new(config: NodeConfig) -> Result<Self, Box<dyn std::error::Error>> {
        println!("🚀 Initializing COINjecture Network B Node...");
        println!();

        // Validate configuration
        config.validate()?;

        // Create data directories
        std::fs::create_dir_all(&config.data_dir)?;
        std::fs::create_dir_all(config.state_db_path())?;
        std::fs::create_dir_all(config.chain_db_path())?;

        // Initialize genesis block
        println!("📦 Loading genesis block...");
        let genesis = create_genesis_block(GenesisConfig::default());
        let genesis_hash = genesis.header.hash();
        println!("   Genesis hash: {:?}", genesis_hash);
        println!();

        // Initialize chain state
        println!("⛓️  Initializing blockchain state...");
        let chain = Arc::new(ChainState::new(config.chain_db_path(), &genesis)?);
        let best_height = chain.best_block_height().await;
        println!("   Best height: {}", best_height);
        println!();

        // Initialize account state
        println!("💰 Initializing account state...");
        let state = Arc::new(AccountState::new(config.state_db_path())?);

        // Apply genesis if this is a new chain
        if best_height == 0 {
            println!("   Applying genesis block to state...");
            let genesis_addr = genesis.header.miner;
            let genesis_reward = genesis.coinbase.reward;
            state.set_balance(&genesis_addr, genesis_reward)?;
            println!("   Genesis account funded with {} tokens", genesis_reward);
        }
        println!();

        // Initialize validator
        let validator = Arc::new(BlockValidator::new(config.difficulty));

        // Initialize mempool components
        let marketplace = Arc::new(RwLock::new(ProblemMarketplace::new()));
        let tx_pool = Arc::new(RwLock::new(TransactionPool::new()));

        // Initialize miner if enabled
        let miner = if config.mine {
            println!("⛏️  Initializing miner...");
            let miner_address = if let Some(ref addr_hex) = config.miner_address {
                let addr_bytes = hex::decode(addr_hex)?;
                if addr_bytes.len() != 32 {
                    return Err("Invalid miner address length".into());
                }
                let mut bytes = [0u8; 32];
                bytes.copy_from_slice(&addr_bytes);
                Address::from_bytes(bytes)
            } else {
                // Use genesis address as default
                genesis.header.miner
            };

            let mining_config = MiningConfig {
                miner_address,
                target_block_time: Duration::from_secs(config.block_time),
                min_difficulty: config.difficulty,
                max_difficulty: config.difficulty + 20,
            };

            println!("   Miner address: {}", hex::encode(miner_address.as_bytes()));
            println!("   Target block time: {}s", config.block_time);
            println!();

            Some(Arc::new(RwLock::new(Miner::new(mining_config))))
        } else {
            None
        };

        // Create shutdown channel
        let (shutdown_tx, shutdown_rx) = mpsc::channel(1);

        Ok(CoinjectNode {
            config,
            chain,
            state,
            validator,
            marketplace,
            tx_pool,
            miner,
            network: None,
            rpc: None,
            shutdown_tx,
            shutdown_rx,
        })
    }

    /// Start the node services
    pub async fn start(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        // Start P2P network
        println!("🌐 Starting P2P network...");
        let network_config = NetworkConfig {
            listen_addr: self.config.p2p_addr.clone(),
            chain_id: self.config.chain_id.clone(),
            max_peers: self.config.max_peers,
            enable_mdns: true,
        };

        let (mut network_service, mut event_rx) = NetworkService::new(network_config)?;
        network_service.start_listening(&self.config.p2p_addr)?;
        network_service.subscribe_topics()?;

        println!("   Listening on: {}", self.config.p2p_addr);
        println!();

        // Start RPC server
        println!("🔌 Starting JSON-RPC server...");
        let rpc_addr = self.config.rpc_socket_addr()?;

        let rpc_state = Arc::new(RpcServerState {
            account_state: Arc::clone(&self.state),
            blockchain: Arc::clone(&self.chain) as Arc<dyn coinject_rpc::BlockchainReader>,
            marketplace: Arc::clone(&self.marketplace),
            chain_id: self.config.chain_id.clone(),
            best_height: self.chain.best_height_ref(),
            best_hash: self.chain.best_hash_ref(),
            genesis_hash: self.chain.genesis_hash(),
            peer_count: Arc::new(RwLock::new(0)),
        });

        let rpc_server = RpcServer::new(rpc_addr, rpc_state).await?;
        println!("   RPC listening on: {}", rpc_addr);
        println!();

        self.network = Some(network_service);
        self.rpc = Some(rpc_server);

        // Start event loop
        println!("✅ Node is ready!");
        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        println!();

        // Spawn network event handler
        let chain = Arc::clone(&self.chain);
        let state = Arc::clone(&self.state);
        let validator = Arc::clone(&self.validator);

        tokio::spawn(async move {
            while let Some(event) = event_rx.recv().await {
                Self::handle_network_event(event, &chain, &state, &validator).await;
            }
        });

        // Start mining loop if enabled
        if let Some(ref miner) = self.miner {
            let miner = Arc::clone(miner);
            let chain = Arc::clone(&self.chain);
            let tx_pool = Arc::clone(&self.tx_pool);

            tokio::spawn(async move {
                Self::mining_loop(miner, chain, tx_pool).await;
            });
        }

        Ok(())
    }

    /// Handle network events
    async fn handle_network_event(
        event: NetworkEvent,
        chain: &Arc<ChainState>,
        state: &Arc<AccountState>,
        validator: &Arc<BlockValidator>,
    ) {
        match event {
            NetworkEvent::BlockReceived { block, peer } => {
                println!("📥 Received block {} from {:?}", block.header.height, peer);

                // Get current best block
                let best_height = chain.best_block_height().await;
                let best_hash = chain.best_block_hash().await;

                // Validate block
                match validator.validate_block(&block, &best_hash, best_height + 1) {
                    Ok(()) => {
                        // Store block
                        match chain.store_block(&block).await {
                            Ok(is_new_best) => {
                                if is_new_best {
                                    // Apply to state
                                    if let Err(e) = validator.apply_block(&block, state) {
                                        println!("❌ Failed to apply block to state: {}", e);
                                    } else {
                                        println!("✅ Block accepted and applied to chain");
                                    }
                                }
                            }
                            Err(e) => println!("❌ Failed to store block: {}", e),
                        }
                    }
                    Err(e) => {
                        println!("❌ Block validation failed: {}", e);
                    }
                }
            }
            NetworkEvent::TransactionReceived { tx: _, peer } => {
                println!("📨 Received transaction from {:?}", peer);
                // TODO: Add to transaction pool
            }
            NetworkEvent::PeerConnected(peer) => {
                println!("🤝 Peer connected: {:?}", peer);
            }
            NetworkEvent::PeerDisconnected(peer) => {
                println!("👋 Peer disconnected: {:?}", peer);
            }
            _ => {}
        }
    }

    /// Mining loop
    async fn mining_loop(
        miner: Arc<RwLock<Miner>>,
        chain: Arc<ChainState>,
        _tx_pool: Arc<RwLock<TransactionPool>>,
    ) {
        let mut interval = time::interval(Duration::from_secs(10));

        loop {
            interval.tick().await;

            let best_height = chain.best_block_height().await;
            let best_hash = chain.best_block_hash().await;

            println!("⛏️  Mining block {}...", best_height + 1);

            // TODO: Select transactions from pool
            let transactions = vec![];

            // Mine block
            let mut miner_lock = miner.write().await;
            if let Some(block) = miner_lock
                .mine_block(best_hash, best_height + 1, transactions)
                .await
            {
                println!("🎉 Mined new block {}!", block.header.height);
                drop(miner_lock);

                // Store block
                if let Err(e) = chain.store_block(&block).await {
                    println!("❌ Failed to store mined block: {}", e);
                }

                // TODO: Broadcast to network
            } else {
                println!("❌ Mining failed");
            }
        }
    }

    /// Wait for shutdown signal
    pub async fn wait_for_shutdown(&mut self) {
        self.shutdown_rx.recv().await;
        println!("🛑 Shutting down node...");
    }

    /// Trigger shutdown
    pub fn shutdown(&self) {
        let _ = self.shutdown_tx.try_send(());
    }
}
