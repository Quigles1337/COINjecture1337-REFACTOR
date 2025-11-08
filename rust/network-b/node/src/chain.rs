// Chain State Manager
// Block storage, best chain tracking, and chain reorganization

use coinject_core::{Block, BlockHeader, Hash};
use sled::Db;
use std::path::Path;
use std::sync::Arc;
use thiserror::Error;
use tokio::sync::RwLock;

#[derive(Error, Debug)]
pub enum ChainError {
    #[error("Database error: {0}")]
    DatabaseError(#[from] sled::Error),
    #[error("Block not found")]
    BlockNotFound,
    #[error("Invalid block height")]
    InvalidHeight,
    #[error("Serialization error: {0}")]
    SerializationError(#[from] bincode::Error),
    #[error("Genesis block mismatch")]
    GenesisMismatch,
}

/// Chain state manager handling block storage and retrieval
pub struct ChainState {
    /// Sled database for block storage
    db: Db,
    /// Best block height
    best_height: Arc<RwLock<u64>>,
    /// Best block hash
    best_hash: Arc<RwLock<Hash>>,
    /// Genesis hash for network verification
    genesis_hash: Hash,
}

impl ChainState {
    /// Create or open chain state database
    pub fn new<P: AsRef<Path>>(path: P, genesis_block: &Block) -> Result<Self, ChainError> {
        let db = sled::open(path)?;

        let genesis_hash = genesis_block.header.hash();

        // Check if genesis exists
        if let Some(stored_genesis) = db.get(b"genesis_hash")? {
            let stored_hash = Hash::from_bytes(
                stored_genesis
                    .as_ref()
                    .try_into()
                    .map_err(|_| ChainError::GenesisMismatch)?,
            );

            if stored_hash != genesis_hash {
                return Err(ChainError::GenesisMismatch);
            }
        } else {
            // Store genesis block
            db.insert(b"genesis_hash", genesis_hash.as_bytes())?;
            Self::store_block_raw(&db, genesis_block)?;
            db.insert(b"best_height", &0u64.to_le_bytes())?;
            db.insert(b"best_hash", genesis_hash.as_bytes())?;
        }

        // Load best height and hash
        let best_height = db
            .get(b"best_height")?
            .map(|bytes| u64::from_le_bytes(bytes.as_ref().try_into().unwrap()))
            .unwrap_or(0);

        let best_hash = db
            .get(b"best_hash")?
            .map(|bytes| Hash::from_bytes(bytes.as_ref().try_into().unwrap()))
            .unwrap_or(genesis_hash);

        Ok(ChainState {
            db,
            best_height: Arc::new(RwLock::new(best_height)),
            best_hash: Arc::new(RwLock::new(best_hash)),
            genesis_hash,
        })
    }

    /// Store a block in the database
    fn store_block_raw(db: &Db, block: &Block) -> Result<(), ChainError> {
        let block_bytes = bincode::serialize(block)?;
        let hash = block.header.hash();

        // Store by hash
        db.insert(hash.as_bytes(), block_bytes.as_slice())?;

        // Store hash by height (for quick height lookups)
        let height_key = format!("height:{}", block.header.height);
        db.insert(height_key.as_bytes(), hash.as_bytes())?;

        Ok(())
    }

    /// Store a block and update best chain if needed
    pub async fn store_block(&self, block: &Block) -> Result<bool, ChainError> {
        let block_hash = block.header.hash();
        let block_height = block.header.height;

        // Store the block
        Self::store_block_raw(&self.db, block)?;

        // Check if this extends the best chain
        let current_best_height = *self.best_height.read().await;

        if block_height > current_best_height {
            // New best block
            *self.best_height.write().await = block_height;
            *self.best_hash.write().await = block_hash;

            self.db.insert(b"best_height", &block_height.to_le_bytes())?;
            self.db.insert(b"best_hash", block_hash.as_bytes())?;

            println!("New best block: height={} hash={:?}", block_height, block_hash);
            return Ok(true);
        }

        Ok(false)
    }

    /// Get block by hash
    pub fn get_block_by_hash(&self, hash: &Hash) -> Result<Option<Block>, ChainError> {
        match self.db.get(hash.as_bytes())? {
            Some(bytes) => {
                let block: Block = bincode::deserialize(&bytes)?;
                Ok(Some(block))
            }
            None => Ok(None),
        }
    }

    /// Get block by height
    pub fn get_block_by_height(&self, height: u64) -> Result<Option<Block>, ChainError> {
        let height_key = format!("height:{}", height);
        match self.db.get(height_key.as_bytes())? {
            Some(hash_bytes) => {
                let hash = Hash::from_bytes(hash_bytes.as_ref().try_into().unwrap());
                self.get_block_by_hash(&hash)
            }
            None => Ok(None),
        }
    }

    /// Get block header by height
    pub fn get_header_by_height(&self, height: u64) -> Result<Option<BlockHeader>, ChainError> {
        Ok(self.get_block_by_height(height)?.map(|b| b.header))
    }

    /// Get the best block height
    pub async fn best_block_height(&self) -> u64 {
        *self.best_height.read().await
    }

    /// Get the best block hash
    pub async fn best_block_hash(&self) -> Hash {
        *self.best_hash.read().await
    }

    /// Get the best block
    pub async fn best_block(&self) -> Result<Option<Block>, ChainError> {
        let hash = self.best_block_hash().await;
        self.get_block_by_hash(&hash)
    }

    /// Get genesis hash
    pub fn genesis_hash(&self) -> Hash {
        self.genesis_hash
    }

    /// Get shared reference to best height
    pub fn best_height_ref(&self) -> Arc<RwLock<u64>> {
        Arc::clone(&self.best_height)
    }

    /// Get shared reference to best hash
    pub fn best_hash_ref(&self) -> Arc<RwLock<Hash>> {
        Arc::clone(&self.best_hash)
    }

    /// Check if a block exists
    pub fn has_block(&self, hash: &Hash) -> Result<bool, ChainError> {
        Ok(self.db.contains_key(hash.as_bytes())?)
    }

    /// Get chain statistics
    pub async fn get_stats(&self) -> ChainStats {
        ChainStats {
            best_height: self.best_block_height().await,
            best_hash: self.best_block_hash().await,
            genesis_hash: self.genesis_hash,
        }
    }
}

/// Chain statistics
#[derive(Debug, Clone)]
pub struct ChainStats {
    pub best_height: u64,
    pub best_hash: Hash,
    pub genesis_hash: Hash,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::genesis::{create_genesis_block, GenesisConfig};

    #[tokio::test]
    async fn test_chain_initialization() {
        let temp_dir = std::env::temp_dir().join("coinject-chain-test-init");
        let _ = std::fs::remove_dir_all(&temp_dir);

        let genesis = create_genesis_block(GenesisConfig::default());
        let chain = ChainState::new(&temp_dir, &genesis).unwrap();

        assert_eq!(chain.best_block_height().await, 0);
        assert_eq!(chain.genesis_hash(), genesis.header.hash());

        let _ = std::fs::remove_dir_all(&temp_dir);
    }

    #[tokio::test]
    async fn test_block_storage() {
        let temp_dir = std::env::temp_dir().join("coinject-chain-test-storage");
        let _ = std::fs::remove_dir_all(&temp_dir);

        let genesis = create_genesis_block(GenesisConfig::default());
        let chain = ChainState::new(&temp_dir, &genesis).unwrap();

        // Retrieve genesis
        let retrieved = chain.get_block_by_height(0).unwrap().unwrap();
        assert_eq!(retrieved.header.height, 0);

        let _ = std::fs::remove_dir_all(&temp_dir);
    }
}

// Implement BlockchainReader trait for RPC access
impl coinject_rpc::BlockchainReader for ChainState {
    fn get_block_by_height(&self, height: u64) -> Result<Option<Block>, String> {
        self.get_block_by_height(height).map_err(|e| e.to_string())
    }

    fn get_block_by_hash(&self, hash: &Hash) -> Result<Option<Block>, String> {
        self.get_block_by_hash(hash).map_err(|e| e.to_string())
    }

    fn get_header_by_height(&self, height: u64) -> Result<Option<BlockHeader>, String> {
        self.get_header_by_height(height).map_err(|e| e.to_string())
    }
}
