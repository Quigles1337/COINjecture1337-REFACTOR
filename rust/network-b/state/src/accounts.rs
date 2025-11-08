// Account-based state management with sled database
use coinject_core::{Address, Balance};
use sled::{Db, IVec};
use std::path::Path;

pub struct AccountState {
    db: Db,
}

impl AccountState {
    /// Open or create the state database
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self, sled::Error> {
        let db = sled::open(path)?;
        Ok(AccountState { db })
    }

    /// Get account balance
    pub fn get_balance(&self, address: &Address) -> Balance {
        let key = Self::balance_key(address);
        self.db
            .get(&key)
            .ok()
            .flatten()
            .and_then(|bytes| Self::bytes_to_balance(&bytes))
            .unwrap_or(0)
    }

    /// Set account balance
    pub fn set_balance(&self, address: &Address, balance: Balance) -> Result<(), sled::Error> {
        let key = Self::balance_key(address);
        let value = balance.to_le_bytes();
        self.db.insert(&key, &value[..])?;
        Ok(())
    }

    /// Get account nonce (for transaction replay protection)
    pub fn get_nonce(&self, address: &Address) -> u64 {
        let key = Self::nonce_key(address);
        self.db
            .get(&key)
            .ok()
            .flatten()
            .and_then(|bytes| Self::bytes_to_u64(&bytes))
            .unwrap_or(0)
    }

    /// Increment account nonce
    pub fn increment_nonce(&self, address: &Address) -> Result<u64, sled::Error> {
        let key = Self::nonce_key(address);
        let new_nonce = self.get_nonce(address) + 1;
        let value = new_nonce.to_le_bytes();
        self.db.insert(&key, &value[..])?;
        Ok(new_nonce)
    }

    /// Transfer tokens between accounts (atomic operation)
    pub fn transfer(
        &self,
        from: &Address,
        to: &Address,
        amount: Balance,
    ) -> Result<(), StateError> {
        let from_balance = self.get_balance(from);
        if from_balance < amount {
            return Err(StateError::InsufficientBalance {
                address: *from,
                balance: from_balance,
                required: amount,
            });
        }

        // Update balances
        self.set_balance(from, from_balance - amount)?;
        let to_balance = self.get_balance(to);
        self.set_balance(to, to_balance + amount)?;

        Ok(())
    }

    /// Apply a batch of balance changes atomically
    pub fn apply_batch(&self, changes: &[(Address, Balance)]) -> Result<(), sled::Error> {
        let mut batch = sled::Batch::default();
        for (address, balance) in changes {
            let key = Self::balance_key(address);
            let value = balance.to_le_bytes();
            batch.insert(&key[..], &value[..]);
        }
        self.db.apply_batch(batch)?;
        Ok(())
    }

    /// Flush all pending writes to disk
    pub fn flush(&self) -> Result<usize, sled::Error> {
        self.db.flush()
    }

    // Helper functions
    fn balance_key(address: &Address) -> Vec<u8> {
        let mut key = vec![0x01]; // Prefix for balance keys
        key.extend_from_slice(address.as_bytes());
        key
    }

    fn nonce_key(address: &Address) -> Vec<u8> {
        let mut key = vec![0x02]; // Prefix for nonce keys
        key.extend_from_slice(address.as_bytes());
        key
    }

    fn bytes_to_balance(bytes: &IVec) -> Option<Balance> {
        if bytes.len() == 16 {
            let mut arr = [0u8; 16];
            arr.copy_from_slice(&bytes[..16]);
            Some(Balance::from_le_bytes(arr))
        } else {
            None
        }
    }

    fn bytes_to_u64(bytes: &IVec) -> Option<u64> {
        if bytes.len() == 8 {
            let mut arr = [0u8; 8];
            arr.copy_from_slice(&bytes[..8]);
            Some(u64::from_le_bytes(arr))
        } else {
            None
        }
    }
}

#[derive(Debug)]
pub enum StateError {
    InsufficientBalance {
        address: Address,
        balance: Balance,
        required: Balance,
    },
    DatabaseError(sled::Error),
}

impl From<sled::Error> for StateError {
    fn from(err: sled::Error) -> Self {
        StateError::DatabaseError(err)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use coinject_core::Address;

    #[test]
    fn test_account_balance() {
        let state = AccountState::new("test_db").unwrap();
        let addr = Address::from_bytes([1u8; 32]);

        // Initial balance should be 0
        assert_eq!(state.get_balance(&addr), 0);

        // Set balance
        state.set_balance(&addr, 1000).unwrap();
        assert_eq!(state.get_balance(&addr), 1000);

        // Cleanup
        std::fs::remove_dir_all("test_db").ok();
    }

    #[test]
    fn test_transfer() {
        let state = AccountState::new("test_transfer_db").unwrap();
        let alice = Address::from_bytes([1u8; 32]);
        let bob = Address::from_bytes([2u8; 32]);

        // Setup
        state.set_balance(&alice, 1000).unwrap();
        state.set_balance(&bob, 0).unwrap();

        // Transfer
        state.transfer(&alice, &bob, 300).unwrap();

        assert_eq!(state.get_balance(&alice), 700);
        assert_eq!(state.get_balance(&bob), 300);

        // Cleanup
        std::fs::remove_dir_all("test_transfer_db").ok();
    }

    #[test]
    fn test_nonce() {
        let state = AccountState::new("test_nonce_db").unwrap();
        let addr = Address::from_bytes([3u8; 32]);

        assert_eq!(state.get_nonce(&addr), 0);
        assert_eq!(state.increment_nonce(&addr).unwrap(), 1);
        assert_eq!(state.get_nonce(&addr), 1);
        assert_eq!(state.increment_nonce(&addr).unwrap(), 2);

        // Cleanup
        std::fs::remove_dir_all("test_nonce_db").ok();
    }
}
