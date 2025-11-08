// JSON-RPC Server for COINjecture Network B
// Provides wallet and client API access

use coinject_core::{Address, Balance, Block, BlockHeader, Hash, Transaction};
use coinject_mempool::{MarketplaceStats, ProblemSubmission, ProblemMarketplace};
use coinject_state::AccountState;
use jsonrpsee::{
    core::{async_trait, RpcResult},
    proc_macros::rpc,
    server::{Server, ServerHandle},
    types::ErrorObjectOwned,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;

/// RPC error codes
const INVALID_PARAMS: i32 = -32602;
const INTERNAL_ERROR: i32 = -32603;
const NOT_FOUND: i32 = -32001;

/// Chain information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChainInfo {
    pub chain_id: String,
    pub best_height: u64,
    pub best_hash: String,
    pub genesis_hash: String,
    pub peer_count: usize,
}

/// Account information response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccountInfo {
    pub address: String,
    pub balance: Balance,
    pub nonce: u64,
}

/// Transaction status response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionStatus {
    pub tx_hash: String,
    pub status: String, // "pending", "confirmed", "failed"
    pub block_height: Option<u64>,
}

/// Problem marketplace response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProblemInfo {
    pub problem_id: String,
    pub submitter: String,
    pub bounty: Balance,
    pub min_work_score: f64,
    pub status: String,
    pub submitted_at: i64,
    pub expires_at: i64,
}

/// JSON-RPC API definition
#[rpc(server, client)]
pub trait CoinjectRpc {
    /// Get account balance
    #[method(name = "account_getBalance")]
    async fn get_balance(&self, address: String) -> RpcResult<Balance>;

    /// Get account nonce
    #[method(name = "account_getNonce")]
    async fn get_nonce(&self, address: String) -> RpcResult<u64>;

    /// Get account information
    #[method(name = "account_getInfo")]
    async fn get_account_info(&self, address: String) -> RpcResult<AccountInfo>;

    /// Submit transaction
    #[method(name = "transaction_submit")]
    async fn submit_transaction(&self, tx_hex: String) -> RpcResult<String>;

    /// Get transaction status
    #[method(name = "transaction_getStatus")]
    async fn get_transaction_status(&self, tx_hash: String) -> RpcResult<TransactionStatus>;

    /// Get block by height
    #[method(name = "chain_getBlock")]
    async fn get_block(&self, height: u64) -> RpcResult<Option<Block>>;

    /// Get latest block
    #[method(name = "chain_getLatestBlock")]
    async fn get_latest_block(&self) -> RpcResult<Option<Block>>;

    /// Get block header by height
    #[method(name = "chain_getBlockHeader")]
    async fn get_block_header(&self, height: u64) -> RpcResult<Option<BlockHeader>>;

    /// Get chain information
    #[method(name = "chain_getInfo")]
    async fn get_chain_info(&self) -> RpcResult<ChainInfo>;

    /// Get open problems from marketplace
    #[method(name = "marketplace_getOpenProblems")]
    async fn get_open_problems(&self) -> RpcResult<Vec<ProblemInfo>>;

    /// Get problem by ID
    #[method(name = "marketplace_getProblem")]
    async fn get_problem(&self, problem_id: String) -> RpcResult<Option<ProblemInfo>>;

    /// Get marketplace statistics
    #[method(name = "marketplace_getStats")]
    async fn get_marketplace_stats(&self) -> RpcResult<MarketplaceStats>;
}

/// RPC server state
pub struct RpcServerState {
    pub account_state: Arc<AccountState>,
    pub marketplace: Arc<RwLock<ProblemMarketplace>>,
    pub chain_id: String,
    pub best_height: Arc<RwLock<u64>>,
    pub best_hash: Arc<RwLock<Hash>>,
    pub genesis_hash: Hash,
    pub peer_count: Arc<RwLock<usize>>,
}

/// RPC server implementation
pub struct RpcServerImpl {
    state: Arc<RpcServerState>,
}

impl RpcServerImpl {
    pub fn new(state: Arc<RpcServerState>) -> Self {
        RpcServerImpl { state }
    }

    /// Parse hex address to Address type
    fn parse_address(&self, address: &str) -> RpcResult<Address> {
        let bytes = hex::decode(address.trim_start_matches("0x"))
            .map_err(|e| ErrorObjectOwned::owned(INVALID_PARAMS, e.to_string(), None::<()>))?;

        if bytes.len() != 32 {
            return Err(ErrorObjectOwned::owned(
                INVALID_PARAMS,
                "Address must be 32 bytes",
                None::<()>,
            ));
        }

        let mut addr_bytes = [0u8; 32];
        addr_bytes.copy_from_slice(&bytes);
        Ok(Address::from_bytes(addr_bytes))
    }

    /// Parse hex hash to Hash type
    fn parse_hash(&self, hash: &str) -> RpcResult<Hash> {
        let bytes = hex::decode(hash.trim_start_matches("0x"))
            .map_err(|e| ErrorObjectOwned::owned(INVALID_PARAMS, e.to_string(), None::<()>))?;

        if bytes.len() != 32 {
            return Err(ErrorObjectOwned::owned(
                INVALID_PARAMS,
                "Hash must be 32 bytes",
                None::<()>,
            ));
        }

        let mut hash_bytes = [0u8; 32];
        hash_bytes.copy_from_slice(&bytes);
        Ok(Hash::from_bytes(hash_bytes))
    }

    /// Convert ProblemSubmission to ProblemInfo
    fn problem_to_info(&self, problem: &ProblemSubmission) -> ProblemInfo {
        ProblemInfo {
            problem_id: hex::encode(problem.problem_id.as_bytes()),
            submitter: hex::encode(problem.submitter.as_bytes()),
            bounty: problem.bounty,
            min_work_score: problem.min_work_score,
            status: format!("{:?}", problem.status),
            submitted_at: problem.submitted_at,
            expires_at: problem.expires_at,
        }
    }
}

#[async_trait]
impl CoinjectRpcServer for RpcServerImpl {
    async fn get_balance(&self, address: String) -> RpcResult<Balance> {
        let addr = self.parse_address(&address)?;
        Ok(self.state.account_state.get_balance(&addr))
    }

    async fn get_nonce(&self, address: String) -> RpcResult<u64> {
        let addr = self.parse_address(&address)?;
        Ok(self.state.account_state.get_nonce(&addr))
    }

    async fn get_account_info(&self, address: String) -> RpcResult<AccountInfo> {
        let addr = self.parse_address(&address)?;
        let balance = self.state.account_state.get_balance(&addr);
        let nonce = self.state.account_state.get_nonce(&addr);

        Ok(AccountInfo {
            address: address.clone(),
            balance,
            nonce,
        })
    }

    async fn submit_transaction(&self, tx_hex: String) -> RpcResult<String> {
        let tx_bytes = hex::decode(tx_hex.trim_start_matches("0x"))
            .map_err(|e| ErrorObjectOwned::owned(INVALID_PARAMS, e.to_string(), None::<()>))?;

        let tx: Transaction = bincode::deserialize(&tx_bytes)
            .map_err(|e| ErrorObjectOwned::owned(INVALID_PARAMS, e.to_string(), None::<()>))?;

        // Basic validation
        if !tx.verify_signature() {
            return Err(ErrorObjectOwned::owned(
                INVALID_PARAMS,
                "Invalid transaction signature",
                None::<()>,
            ));
        }

        let tx_hash = tx.hash();

        // TODO: Add to mempool
        // For now, just return the hash
        Ok(hex::encode(tx_hash.as_bytes()))
    }

    async fn get_transaction_status(&self, tx_hash: String) -> RpcResult<TransactionStatus> {
        let _hash = self.parse_hash(&tx_hash)?;

        // TODO: Implement transaction tracking
        // For now, return placeholder
        Ok(TransactionStatus {
            tx_hash: tx_hash.clone(),
            status: "unknown".to_string(),
            block_height: None,
        })
    }

    async fn get_block(&self, _height: u64) -> RpcResult<Option<Block>> {
        // TODO: Implement block storage and retrieval
        // For now, return None
        Ok(None)
    }

    async fn get_latest_block(&self) -> RpcResult<Option<Block>> {
        // TODO: Implement block storage
        Ok(None)
    }

    async fn get_block_header(&self, _height: u64) -> RpcResult<Option<BlockHeader>> {
        // TODO: Implement block header retrieval
        Ok(None)
    }

    async fn get_chain_info(&self) -> RpcResult<ChainInfo> {
        let best_height = *self.state.best_height.read().await;
        let best_hash = *self.state.best_hash.read().await;
        let peer_count = *self.state.peer_count.read().await;

        Ok(ChainInfo {
            chain_id: self.state.chain_id.clone(),
            best_height,
            best_hash: hex::encode(best_hash.as_bytes()),
            genesis_hash: hex::encode(self.state.genesis_hash.as_bytes()),
            peer_count,
        })
    }

    async fn get_open_problems(&self) -> RpcResult<Vec<ProblemInfo>> {
        let marketplace = self.state.marketplace.read().await;
        let problems = marketplace.get_open_problems();

        Ok(problems.iter().map(|p| self.problem_to_info(p)).collect())
    }

    async fn get_problem(&self, problem_id: String) -> RpcResult<Option<ProblemInfo>> {
        let hash = self.parse_hash(&problem_id)?;
        let marketplace = self.state.marketplace.read().await;

        Ok(marketplace.get_problem(&hash).map(|p| self.problem_to_info(p)))
    }

    async fn get_marketplace_stats(&self) -> RpcResult<MarketplaceStats> {
        let marketplace = self.state.marketplace.read().await;
        Ok(marketplace.get_stats())
    }
}

/// RPC server handle
pub struct RpcServer {
    handle: ServerHandle,
    addr: SocketAddr,
}

impl RpcServer {
    /// Create and start new RPC server
    pub async fn new(
        listen_addr: SocketAddr,
        state: Arc<RpcServerState>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let server = Server::builder().build(listen_addr).await?;
        let addr = server.local_addr()?;

        let rpc_impl = RpcServerImpl::new(state);
        let handle = server.start(rpc_impl.into_rpc());

        println!("JSON-RPC server listening on {}", addr);

        Ok(RpcServer { handle, addr })
    }

    /// Get the listening address
    pub fn local_addr(&self) -> SocketAddr {
        self.addr
    }

    /// Stop the server
    pub fn stop(self) -> Result<(), Box<dyn std::error::Error>> {
        self.handle.stop()?;
        Ok(())
    }

    /// Wait for the server to finish
    pub async fn stopped(self) {
        self.handle.stopped().await;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_address_parsing() {
        let temp_dir = std::env::temp_dir().join("coinject-rpc-test-addr");
        let _ = std::fs::remove_dir_all(&temp_dir);

        let state = Arc::new(RpcServerState {
            account_state: Arc::new(AccountState::new(&temp_dir).unwrap()),
            marketplace: Arc::new(RwLock::new(ProblemMarketplace::new())),
            chain_id: "test".to_string(),
            best_height: Arc::new(RwLock::new(0)),
            best_hash: Arc::new(RwLock::new(Hash::ZERO)),
            genesis_hash: Hash::ZERO,
            peer_count: Arc::new(RwLock::new(0)),
        });

        let rpc = RpcServerImpl::new(state);

        // Valid 32-byte hex address
        let addr_hex = "0x0000000000000000000000000000000000000000000000000000000000000001";
        let result = rpc.parse_address(addr_hex);
        assert!(result.is_ok());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_hash_parsing() {
        let temp_dir = std::env::temp_dir().join("coinject-rpc-test-hash");
        let _ = std::fs::remove_dir_all(&temp_dir);

        let state = Arc::new(RpcServerState {
            account_state: Arc::new(AccountState::new(&temp_dir).unwrap()),
            marketplace: Arc::new(RwLock::new(ProblemMarketplace::new())),
            chain_id: "test".to_string(),
            best_height: Arc::new(RwLock::new(0)),
            best_hash: Arc::new(RwLock::new(Hash::ZERO)),
            genesis_hash: Hash::ZERO,
            peer_count: Arc::new(RwLock::new(0)),
        });

        let rpc = RpcServerImpl::new(state);

        // Valid 32-byte hex hash
        let hash_hex = "0x0000000000000000000000000000000000000000000000000000000000000001";
        let result = rpc.parse_hash(hash_hex);
        assert!(result.is_ok());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}
