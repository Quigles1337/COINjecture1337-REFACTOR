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
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{mpsc, RwLock};
use tokio::time;

/// Commands that can be sent to the network task
enum NetworkCommand {
    BroadcastBlock(coinject_core::Block),
    BroadcastTransaction(coinject_core::Transaction),
    BroadcastStatus { best_height: u64, best_hash: coinject_core::Hash, genesis_hash: coinject_core::Hash },
    RequestBlocks { from_height: u64, to_height: u64 },
}

/// Main node service coordinating all blockchain components
pub struct CoinjectNode {
    config: NodeConfig,
    chain: Arc<ChainState>,
    state: Arc<AccountState>,
    validator: Arc<BlockValidator>,
    marketplace: Arc<RwLock<ProblemMarketplace>>,
    tx_pool: Arc<RwLock<TransactionPool>>,
    miner: Option<Arc<RwLock<Miner>>>,
    network_cmd_tx: Option<mpsc::UnboundedSender<NetworkCommand>>,
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
            network_cmd_tx: None,
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

        // Create command channel for network operations
        let (network_cmd_tx, mut network_cmd_rx) = mpsc::unbounded_channel::<NetworkCommand>();

        // Start RPC server
        println!("🔌 Starting JSON-RPC server...");
        let rpc_addr = self.config.rpc_socket_addr()?;

        let rpc_state = Arc::new(RpcServerState {
            account_state: Arc::clone(&self.state),
            blockchain: Arc::clone(&self.chain) as Arc<dyn coinject_rpc::BlockchainReader>,
            marketplace: Arc::clone(&self.marketplace),
            tx_pool: Arc::clone(&self.tx_pool),
            chain_id: self.config.chain_id.clone(),
            best_height: self.chain.best_height_ref(),
            best_hash: self.chain.best_hash_ref(),
            genesis_hash: self.chain.genesis_hash(),
            peer_count: Arc::new(RwLock::new(0)),
        });

        let rpc_server = RpcServer::new(rpc_addr, rpc_state).await?;
        println!("   RPC listening on: {}", rpc_addr);
        println!();

        self.network_cmd_tx = Some(network_cmd_tx.clone());
        self.rpc = Some(rpc_server);

        // Start event loop
        println!("✅ Node is ready!");
        println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        println!();

        // Spawn network task (processes events and commands)
        tokio::task::spawn_local(async move {
            let mut network = network_service;
            loop {
                tokio::select! {
                    // Process network events
                    _ = network.process_events() => {},

                    // Handle commands from other tasks
                    Some(cmd) = network_cmd_rx.recv() => {
                        match cmd {
                            NetworkCommand::BroadcastBlock(block) => {
                                if let Err(e) = network.broadcast_block(block) {
                                    eprintln!("Failed to broadcast block: {}", e);
                                }
                            }
                            NetworkCommand::BroadcastTransaction(tx) => {
                                if let Err(e) = network.broadcast_transaction(tx) {
                                    eprintln!("Failed to broadcast transaction: {}", e);
                                }
                            }
                            NetworkCommand::BroadcastStatus { best_height, best_hash, genesis_hash } => {
                                if let Err(e) = network.broadcast_status(best_height, best_hash, genesis_hash) {
                                    eprintln!("Failed to broadcast status: {}", e);
                                }
                            }
                            NetworkCommand::RequestBlocks { from_height, to_height } => {
                                println!("📡 Requesting blocks {}-{} from network", from_height, to_height);
                                if let Err(e) = network.request_blocks(from_height, to_height) {
                                    eprintln!("Failed to request blocks: {}", e);
                                }
                            }
                        }
                    }
                }
            }
        });

        // Create block buffer for out-of-order blocks
        let block_buffer: Arc<RwLock<HashMap<u64, coinject_core::Block>>> = Arc::new(RwLock::new(HashMap::new()));

        // Spawn network event handler
        let chain = Arc::clone(&self.chain);
        let state = Arc::clone(&self.state);
        let validator = Arc::clone(&self.validator);
        let tx_pool = Arc::clone(&self.tx_pool);
        let network_tx_for_events = network_cmd_tx.clone();
        let buffer_for_events = Arc::clone(&block_buffer);

        tokio::spawn(async move {
            while let Some(event) = event_rx.recv().await {
                Self::handle_network_event(event, &chain, &state, &validator, &tx_pool, &network_tx_for_events, &buffer_for_events).await;
            }
        });

        // Spawn periodic status broadcast task
        let chain_for_status = Arc::clone(&self.chain);
        let genesis_hash = self.chain.genesis_hash();
        let network_tx_for_status = network_cmd_tx.clone();

        tokio::spawn(async move {
            let mut interval = time::interval(Duration::from_secs(10));
            loop {
                interval.tick().await;
                let best_height = chain_for_status.best_block_height().await;
                let best_hash = chain_for_status.best_block_hash().await;

                if let Err(e) = network_tx_for_status.send(NetworkCommand::BroadcastStatus {
                    best_height,
                    best_hash,
                    genesis_hash,
                }) {
                    eprintln!("Failed to send status broadcast command: {}", e);
                }
            }
        });

        // Start mining loop if enabled
        if let Some(ref miner) = self.miner {
            let miner = Arc::clone(miner);
            let chain = Arc::clone(&self.chain);
            let state = Arc::clone(&self.state);
            let tx_pool = Arc::clone(&self.tx_pool);
            let network_tx = network_cmd_tx.clone();

            tokio::spawn(async move {
                Self::mining_loop(miner, chain, state, tx_pool, network_tx).await;
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
        tx_pool: &Arc<RwLock<TransactionPool>>,
        network_tx: &mpsc::UnboundedSender<NetworkCommand>,
        block_buffer: &Arc<RwLock<HashMap<u64, coinject_core::Block>>>,
    ) {
        match event {
            NetworkEvent::BlockReceived { block, peer } => {
                println!("📥 Received block {} from {:?}", block.header.height, peer);

                let best_height = chain.best_block_height().await;
                let expected_height = best_height + 1;

                // Check if block is the next sequential block we need
                if block.header.height == expected_height {
                    // This is the next block we need - validate and apply immediately
                    let best_hash = chain.best_block_hash().await;

                    match validator.validate_block(&block, &best_hash, expected_height) {
                        Ok(()) => {
                            // Store and apply block
                            match chain.store_block(&block).await {
                                Ok(is_new_best) => {
                                    if is_new_best {
                                        // Apply block transactions to state
                                        match Self::apply_block_transactions(&block, state) {
                                            Ok(applied_txs) => {
                                                println!("✅ Block {} accepted and applied to chain", block.header.height);

                                                // Remove only successfully applied transactions from pool
                                                let mut pool = tx_pool.write().await;
                                                for tx_hash in &applied_txs {
                                                    pool.remove(tx_hash);
                                                }
                                                drop(pool);

                                                // After applying this block, try to apply buffered blocks sequentially
                                                Self::process_buffered_blocks(
                                                    chain,
                                                    state,
                                                    validator,
                                                    tx_pool,
                                                    block_buffer,
                                                ).await;
                                            }
                                            Err(e) => {
                                                println!("❌ Failed to apply block transactions: {}", e);
                                            }
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
                } else if block.header.height > expected_height {
                    // Future block - add to buffer for later processing
                    let mut buffer = block_buffer.write().await;

                    // Only buffer if we don't already have it
                    if !buffer.contains_key(&block.header.height) {
                        println!(
                            "🗃️  Buffering future block {} (expected: {}, buffer size: {})",
                            block.header.height,
                            expected_height,
                            buffer.len() + 1
                        );
                        buffer.insert(block.header.height, block);
                    }
                } else {
                    // Old block we already have - ignore it
                    println!("⏭️  Ignoring old block {} (current height: {})", block.header.height, best_height);
                }
            }
            NetworkEvent::TransactionReceived { tx, peer } => {
                println!("📨 Received transaction {:?} from {:?}", tx.hash(), peer);

                // Validate and add to transaction pool
                if tx.verify_signature() {
                    let mut pool = tx_pool.write().await;
                    match pool.add(tx) {
                        Ok(hash) => println!("✅ Added transaction {:?} to pool", hash),
                        Err(e) => println!("❌ Failed to add transaction to pool: {}", e),
                    }
                } else {
                    println!("❌ Invalid transaction signature, rejecting");
                }
            }
            NetworkEvent::PeerConnected(peer) => {
                println!("🤝 Peer connected: {:?}", peer);
            }
            NetworkEvent::PeerDisconnected(peer) => {
                println!("👋 Peer disconnected: {:?}", peer);
            }
            NetworkEvent::StatusUpdate { peer, best_height, best_hash } => {
                let our_height = chain.best_block_height().await;

                println!(
                    "📊 Status update from {:?}: height {} (ours: {})",
                    peer, best_height, our_height
                );

                // If peer is ahead, trigger sync
                if best_height > our_height + 1 {
                    let sync_from = our_height + 1;
                    let sync_to = best_height;

                    println!(
                        "🔄 Peer is ahead! Requesting blocks {}-{} for sync",
                        sync_from, sync_to
                    );

                    // Request missing blocks (in chunks of 100 to avoid overwhelming)
                    let chunk_size = 100u64;
                    let mut current = sync_from;

                    while current <= sync_to {
                        let end = std::cmp::min(current + chunk_size - 1, sync_to);

                        if let Err(e) = network_tx.send(NetworkCommand::RequestBlocks {
                            from_height: current,
                            to_height: end,
                        }) {
                            eprintln!("Failed to send RequestBlocks command: {}", e);
                            break;
                        }

                        current = end + 1;
                    }
                }
            }
            NetworkEvent::BlocksRequested { peer, from_height, to_height } => {
                println!(
                    "📮 Blocks requested by {:?}: heights {}-{}",
                    peer, from_height, to_height
                );

                // Respond by broadcasting the requested blocks
                let mut sent_count = 0;
                for height in from_height..=to_height {
                    match chain.get_block_by_height(height) {
                        Ok(Some(block)) => {
                            if let Err(e) = network_tx.send(NetworkCommand::BroadcastBlock(block)) {
                                eprintln!("Failed to broadcast block {}: {}", height, e);
                                break;
                            }
                            sent_count += 1;
                        }
                        Ok(None) => {
                            // We don't have this block, stop
                            break;
                        }
                        Err(e) => {
                            eprintln!("Error fetching block {}: {}", height, e);
                            break;
                        }
                    }
                }

                if sent_count > 0 {
                    println!("📤 Sent {} blocks in response to sync request", sent_count);
                }
            }
        }
    }

    /// Process buffered blocks sequentially
    async fn process_buffered_blocks(
        chain: &Arc<ChainState>,
        state: &Arc<AccountState>,
        validator: &Arc<BlockValidator>,
        tx_pool: &Arc<RwLock<TransactionPool>>,
        block_buffer: &Arc<RwLock<HashMap<u64, coinject_core::Block>>>,
    ) {
        loop {
            let best_height = chain.best_block_height().await;
            let next_height = best_height + 1;

            // Check if we have the next sequential block in buffer
            let block_opt = {
                let mut buffer = block_buffer.write().await;
                buffer.remove(&next_height)
            };

            match block_opt {
                Some(block) => {
                    println!("🔄 Processing buffered block {} from buffer", next_height);

                    let best_hash = chain.best_block_hash().await;

                    // Validate the buffered block
                    match validator.validate_block(&block, &best_hash, next_height) {
                        Ok(()) => {
                            // Store and apply
                            match chain.store_block(&block).await {
                                Ok(is_new_best) => {
                                    if is_new_best {
                                        match Self::apply_block_transactions(&block, state) {
                                            Ok(applied_txs) => {
                                                println!("✅ Buffered block {} applied to chain", next_height);

                                                // Remove only successfully applied transactions from pool
                                                let mut pool = tx_pool.write().await;
                                                for tx_hash in &applied_txs {
                                                    pool.remove(tx_hash);
                                                }
                                                drop(pool);

                                                // Continue loop to check for next sequential block
                                            }
                                            Err(e) => {
                                                println!("❌ Failed to apply buffered block transactions: {}", e);
                                                break;
                                            }
                                        }
                                    } else {
                                        break;
                                    }
                                }
                                Err(e) => {
                                    println!("❌ Failed to store buffered block: {}", e);
                                    break;
                                }
                            }
                        }
                        Err(e) => {
                            println!("❌ Buffered block validation failed: {}", e);
                            break;
                        }
                    }
                }
                None => {
                    // No more sequential blocks in buffer
                    break;
                }
            }
        }
    }

    /// Apply block transactions to account state
    /// Returns a vector of successfully applied transaction hashes
    fn apply_block_transactions(
        block: &coinject_core::Block,
        state: &Arc<AccountState>,
    ) -> Result<Vec<coinject_core::Hash>, String> {
        // Apply coinbase reward
        let miner = block.header.miner;
        let reward = block.coinbase.reward;
        let current_balance = state.get_balance(&miner);
        state.set_balance(&miner, current_balance + reward)
            .map_err(|e| format!("Failed to set miner balance: {}", e))?;

        let mut applied_txs = Vec::new();

        // Apply regular transactions
        for tx in &block.transactions {
            // Validate transaction before applying
            let sender_balance = state.get_balance(&tx.from);

            // Check if sender has sufficient balance
            if sender_balance < tx.amount + tx.fee {
                println!("⚠️  Skipping transaction {:?}: insufficient balance (has: {}, needs: {})",
                    tx.hash(), sender_balance, tx.amount + tx.fee);
                continue; // Skip this transaction and continue with the rest
            }

            // Apply the transaction
            match Self::apply_single_transaction(tx, state) {
                Ok(()) => {
                    applied_txs.push(tx.hash());
                }
                Err(e) => {
                    println!("⚠️  Skipping transaction {:?}: {}", tx.hash(), e);
                    continue; // Skip this transaction and continue with the rest
                }
            }
        }

        if applied_txs.len() < block.transactions.len() {
            println!("📊 Applied {}/{} transactions from block",
                applied_txs.len(), block.transactions.len());
        }

        Ok(applied_txs)
    }

    /// Apply a single transaction to state
    fn apply_single_transaction(
        tx: &coinject_core::Transaction,
        state: &Arc<AccountState>,
    ) -> Result<(), String> {
        // Deduct from sender
        let sender_balance = state.get_balance(&tx.from);
        state.set_balance(&tx.from, sender_balance - tx.amount - tx.fee)
            .map_err(|e| format!("Failed to set sender balance: {}", e))?;
        state.set_nonce(&tx.from, tx.nonce + 1)
            .map_err(|e| format!("Failed to set sender nonce: {}", e))?;

        // Credit recipient
        let recipient_balance = state.get_balance(&tx.to);
        state.set_balance(&tx.to, recipient_balance + tx.amount)
            .map_err(|e| format!("Failed to set recipient balance: {}", e))?;

        // Fee goes to miner (already included in reward calculation)
        Ok(())
    }

    /// Mining loop
    async fn mining_loop(
        miner: Arc<RwLock<Miner>>,
        chain: Arc<ChainState>,
        state: Arc<AccountState>,
        tx_pool: Arc<RwLock<TransactionPool>>,
        network_tx: mpsc::UnboundedSender<NetworkCommand>,
    ) {
        let mut interval = time::interval(Duration::from_secs(10));

        loop {
            interval.tick().await;

            let best_height = chain.best_block_height().await;
            let best_hash = chain.best_block_hash().await;

            println!("⛏️  Mining block {}...", best_height + 1);

            // Select transactions from pool (top 100 by fee)
            let pool = tx_pool.read().await;
            let transactions = pool.get_top_n(100);
            drop(pool);

            println!("   Including {} transactions", transactions.len());

            // Mine block
            let mut miner_lock = miner.write().await;
            if let Some(block) = miner_lock
                .mine_block(best_hash, best_height + 1, transactions.clone())
                .await
            {
                println!("🎉 Mined new block {}!", block.header.height);
                drop(miner_lock);

                // Store block
                if let Err(e) = chain.store_block(&block).await {
                    println!("❌ Failed to store mined block: {}", e);
                    continue;
                }

                // Apply block transactions to state
                let applied_txs = match Self::apply_block_transactions(&block, &state) {
                    Ok(txs) => txs,
                    Err(e) => {
                        println!("❌ Failed to apply mined block transactions: {}", e);
                        continue;
                    }
                };

                // Remove only successfully applied transactions from pool
                let mut pool = tx_pool.write().await;
                for tx_hash in &applied_txs {
                    pool.remove(tx_hash);
                }
                drop(pool);

                // Broadcast to network
                if let Err(e) = network_tx.send(NetworkCommand::BroadcastBlock(block)) {
                    println!("❌ Failed to send broadcast command: {}", e);
                } else {
                    println!("📡 Broadcasted block to network");
                }
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
