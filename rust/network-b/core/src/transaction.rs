use crate::{Address, Balance, Ed25519Signature, Hash, PublicKey};
use serde::{Deserialize, Serialize};

/// Transaction types supported by Network B
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Transaction {
    /// Simple transfer from one account to another
    Transfer(TransferTransaction),
    /// Time-locked transaction that unlocks at a specific time
    TimeLock(TimeLockTransaction),
    /// Conditional escrow with multi-party signing
    Escrow(EscrowTransaction),
    /// Payment channel operations
    Channel(ChannelTransaction),
    /// TrustLine operations with dimensional economics
    TrustLine(TrustLineTransaction),
}

/// Simple transfer transaction (original transaction type)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TransferTransaction {
    /// Sender address
    pub from: Address,
    /// Recipient address
    pub to: Address,
    /// Amount to transfer
    pub amount: Balance,
    /// Transaction fee
    pub fee: Balance,
    /// Nonce (prevents replay attacks)
    pub nonce: u64,
    /// Sender's public key
    pub public_key: PublicKey,
    /// Ed25519 signature
    pub signature: Ed25519Signature,
}

/// Time-locked transaction that releases funds at a specific time
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeLockTransaction {
    /// Sender address (locks funds from their account)
    pub from: Address,
    /// Recipient address (who can claim after unlock)
    pub recipient: Address,
    /// Amount to lock
    pub amount: Balance,
    /// Unix timestamp when funds unlock
    pub unlock_time: i64,
    /// Transaction fee
    pub fee: Balance,
    /// Nonce
    pub nonce: u64,
    /// Sender's public key
    pub public_key: PublicKey,
    /// Ed25519 signature
    pub signature: Ed25519Signature,
}

/// Conditional escrow transaction with multi-party signing
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EscrowTransaction {
    /// Type of escrow operation
    pub escrow_type: EscrowType,
    /// Unique escrow identifier
    pub escrow_id: Hash,
    /// Sender/initiator address
    pub from: Address,
    /// Transaction fee
    pub fee: Balance,
    /// Nonce
    pub nonce: u64,
    /// Initiator's public key
    pub public_key: PublicKey,
    /// Ed25519 signature
    pub signature: Ed25519Signature,
    /// Additional signatures (for release/refund)
    pub additional_signatures: Vec<(Address, Ed25519Signature)>,
}

/// Type of escrow operation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum EscrowType {
    /// Create new escrow
    Create {
        recipient: Address,
        arbiter: Option<Address>,
        amount: Balance,
        timeout: i64, // Unix timestamp
        conditions_hash: Hash,
    },
    /// Release escrowed funds to recipient
    Release,
    /// Refund escrowed funds to sender
    Refund,
}

/// Payment channel transaction
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChannelTransaction {
    /// Type of channel operation
    pub channel_type: ChannelType,
    /// Unique channel identifier
    pub channel_id: Hash,
    /// Initiator address
    pub from: Address,
    /// Transaction fee
    pub fee: Balance,
    /// Nonce
    pub nonce: u64,
    /// Initiator's public key
    pub public_key: PublicKey,
    /// Ed25519 signature
    pub signature: Ed25519Signature,
    /// Additional signatures (for cooperative close)
    pub additional_signatures: Vec<(Address, Ed25519Signature)>,
}

/// Type of channel operation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum ChannelType {
    /// Open a new payment channel
    Open {
        participant_a: Address,
        participant_b: Address,
        deposit_a: Balance,
        deposit_b: Balance,
        timeout: i64, // Dispute timeout in seconds
    },
    /// Update channel state (off-chain, for reference)
    Update {
        sequence: u64,
        balance_a: Balance,
        balance_b: Balance,
    },
    /// Close channel cooperatively
    CooperativeClose {
        final_balance_a: Balance,
        final_balance_b: Balance,
    },
    /// Close channel unilaterally (dispute)
    UnilateralClose {
        sequence: u64,
        balance_a: Balance,
        balance_b: Balance,
        dispute_proof: Vec<u8>,
    },
}

/// TrustLine transaction with dimensional economics
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrustLineTransaction {
    /// Type of trustline operation
    pub trustline_type: TrustLineType,
    /// Unique trustline identifier
    pub trustline_id: Hash,
    /// Initiator address
    pub from: Address,
    /// Transaction fee
    pub fee: Balance,
    /// Nonce
    pub nonce: u64,
    /// Initiator's public key
    pub public_key: PublicKey,
    /// Ed25519 signature
    pub signature: Ed25519Signature,
}

/// Type of trustline operation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum TrustLineType {
    /// Create a new bilateral trustline
    Create {
        account_b: Address,
        limit_a_to_b: Balance,
        limit_b_to_a: Balance,
        quality_in: u16,           // Basis points (0-10000)
        quality_out: u16,          // Basis points (0-10000)
        ripple_enabled: bool,
        dimensional_scale: u8,     // 1-8
    },
    /// Update credit limits on existing trustline
    UpdateLimits {
        limit_a_to_b: Option<Balance>,
        limit_b_to_a: Option<Balance>,
    },
    /// Freeze trustline
    Freeze,
    /// Close trustline (requires zero balance)
    Close,
    /// Evolve phase parameter (periodic dimensional adjustment)
    EvolvePhase {
        delta_tau: f64,
    },
}

impl Transaction {
    /// Create and sign a new transfer transaction
    pub fn new_transfer(
        from: Address,
        to: Address,
        amount: Balance,
        fee: Balance,
        nonce: u64,
        keypair: &crate::crypto::KeyPair,
    ) -> Self {
        let transfer = TransferTransaction::new(from, to, amount, fee, nonce, keypair);
        Transaction::Transfer(transfer)
    }

    /// Create and sign a new time-lock transaction
    pub fn new_timelock(
        from: Address,
        recipient: Address,
        amount: Balance,
        unlock_time: i64,
        fee: Balance,
        nonce: u64,
        keypair: &crate::crypto::KeyPair,
    ) -> Self {
        let timelock = TimeLockTransaction::new(from, recipient, amount, unlock_time, fee, nonce, keypair);
        Transaction::TimeLock(timelock)
    }

    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        match self {
            Transaction::Transfer(tx) => tx.verify_signature(),
            Transaction::TimeLock(tx) => tx.verify_signature(),
            Transaction::Escrow(tx) => tx.verify_signature(),
            Transaction::Channel(tx) => tx.verify_signature(),
            Transaction::TrustLine(tx) => tx.verify_signature(),
        }
    }

    /// Calculate transaction hash
    pub fn hash(&self) -> Hash {
        let serialized = bincode::serialize(self).unwrap_or_default();
        Hash::new(&serialized)
    }

    /// Check if transaction is valid (basic checks)
    pub fn is_valid(&self) -> bool {
        match self {
            Transaction::Transfer(tx) => tx.is_valid(),
            Transaction::TimeLock(tx) => tx.is_valid(),
            Transaction::Escrow(tx) => tx.is_valid(),
            Transaction::Channel(tx) => tx.is_valid(),
            Transaction::TrustLine(tx) => tx.is_valid(),
        }
    }

    /// Get the sender address
    pub fn from(&self) -> &Address {
        match self {
            Transaction::Transfer(tx) => &tx.from,
            Transaction::TimeLock(tx) => &tx.from,
            Transaction::Escrow(tx) => &tx.from,
            Transaction::Channel(tx) => &tx.from,
            Transaction::TrustLine(tx) => &tx.from,
        }
    }

    /// Get the transaction fee
    pub fn fee(&self) -> Balance {
        match self {
            Transaction::Transfer(tx) => tx.fee,
            Transaction::TimeLock(tx) => tx.fee,
            Transaction::Escrow(tx) => tx.fee,
            Transaction::Channel(tx) => tx.fee,
            Transaction::TrustLine(tx) => tx.fee,
        }
    }

    /// Get the nonce
    pub fn nonce(&self) -> u64 {
        match self {
            Transaction::Transfer(tx) => tx.nonce,
            Transaction::TimeLock(tx) => tx.nonce,
            Transaction::Escrow(tx) => tx.nonce,
            Transaction::Channel(tx) => tx.nonce,
            Transaction::TrustLine(tx) => tx.nonce,
        }
    }

    /// Get the recipient address (only for Transfer transactions)
    /// Returns None for other transaction types
    pub fn to(&self) -> Option<&Address> {
        match self {
            Transaction::Transfer(tx) => Some(&tx.to),
            _ => None,
        }
    }

    /// Get the transfer amount (only for Transfer transactions)
    /// Returns None for other transaction types
    pub fn amount(&self) -> Option<Balance> {
        match self {
            Transaction::Transfer(tx) => Some(tx.amount),
            _ => None,
        }
    }
}

impl TransferTransaction {
    /// Create and sign a new transfer transaction
    pub fn new(
        from: Address,
        to: Address,
        amount: Balance,
        fee: Balance,
        nonce: u64,
        keypair: &crate::crypto::KeyPair,
    ) -> Self {
        let public_key = keypair.public_key();

        // Create unsigned transaction
        let mut tx = TransferTransaction {
            from,
            to,
            amount,
            fee,
            nonce,
            public_key,
            signature: Ed25519Signature::from_bytes([0u8; 64]),
        };

        // Sign it
        let message = tx.signing_message();
        tx.signature = keypair.sign(&message);

        tx
    }

    /// Get message to sign (excludes signature)
    fn signing_message(&self) -> Vec<u8> {
        let mut msg = Vec::new();
        msg.extend_from_slice(self.from.as_bytes());
        msg.extend_from_slice(self.to.as_bytes());
        msg.extend_from_slice(&self.amount.to_le_bytes());
        msg.extend_from_slice(&self.fee.to_le_bytes());
        msg.extend_from_slice(&self.nonce.to_le_bytes());
        msg.extend_from_slice(self.public_key.as_bytes());
        msg
    }

    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        let message = self.signing_message();
        self.public_key.verify(&message, &self.signature)
    }

    /// Check if transaction is valid (basic checks)
    pub fn is_valid(&self) -> bool {
        // 1. Signature must be valid
        if !self.verify_signature() {
            return false;
        }

        // 2. Sender address must match public key
        if self.from != self.public_key.to_address() {
            return false;
        }

        // 3. Amount must be non-zero
        if self.amount == 0 {
            return false;
        }

        true
    }
}

impl TimeLockTransaction {
    /// Create and sign a new time-lock transaction
    pub fn new(
        from: Address,
        recipient: Address,
        amount: Balance,
        unlock_time: i64,
        fee: Balance,
        nonce: u64,
        keypair: &crate::crypto::KeyPair,
    ) -> Self {
        let public_key = keypair.public_key();

        // Create unsigned transaction
        let mut tx = TimeLockTransaction {
            from,
            recipient,
            amount,
            unlock_time,
            fee,
            nonce,
            public_key,
            signature: Ed25519Signature::from_bytes([0u8; 64]),
        };

        // Sign it
        let message = tx.signing_message();
        tx.signature = keypair.sign(&message);

        tx
    }

    /// Get message to sign
    fn signing_message(&self) -> Vec<u8> {
        let mut msg = Vec::new();
        msg.extend_from_slice(self.from.as_bytes());
        msg.extend_from_slice(self.recipient.as_bytes());
        msg.extend_from_slice(&self.amount.to_le_bytes());
        msg.extend_from_slice(&self.unlock_time.to_le_bytes());
        msg.extend_from_slice(&self.fee.to_le_bytes());
        msg.extend_from_slice(&self.nonce.to_le_bytes());
        msg.extend_from_slice(self.public_key.as_bytes());
        msg
    }

    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        let message = self.signing_message();
        self.public_key.verify(&message, &self.signature)
    }

    /// Check if transaction is valid
    pub fn is_valid(&self) -> bool {
        // 1. Signature must be valid
        if !self.verify_signature() {
            return false;
        }

        // 2. Sender address must match public key
        if self.from != self.public_key.to_address() {
            return false;
        }

        // 3. Amount must be non-zero
        if self.amount == 0 {
            return false;
        }

        // 4. Unlock time must be in the future
        let now = chrono::Utc::now().timestamp();
        if self.unlock_time <= now {
            return false;
        }

        true
    }
}

impl EscrowTransaction {
    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        let message = self.signing_message();
        if !self.public_key.verify(&message, &self.signature) {
            return false;
        }

        // Verify additional signatures for release/refund operations
        match &self.escrow_type {
            EscrowType::Release | EscrowType::Refund => {
                // At least one additional signature required
                if self.additional_signatures.is_empty() {
                    return false;
                }

                for (_addr, _sig) in &self.additional_signatures {
                    // TODO: Verify each additional signature
                    // This requires storing the public keys associated with addresses
                }
            }
            _ => {}
        }

        true
    }

    /// Get message to sign
    fn signing_message(&self) -> Vec<u8> {
        let mut msg = Vec::new();
        msg.extend_from_slice(self.escrow_id.as_bytes());
        msg.extend_from_slice(self.from.as_bytes());
        msg.extend_from_slice(&self.fee.to_le_bytes());
        msg.extend_from_slice(&self.nonce.to_le_bytes());
        msg.extend_from_slice(self.public_key.as_bytes());

        // Include escrow type specific data
        match &self.escrow_type {
            EscrowType::Create { recipient, amount, timeout, .. } => {
                msg.extend_from_slice(recipient.as_bytes());
                msg.extend_from_slice(&amount.to_le_bytes());
                msg.extend_from_slice(&timeout.to_le_bytes());
            }
            _ => {}
        }

        msg
    }

    /// Check if transaction is valid
    pub fn is_valid(&self) -> bool {
        // 1. Signature must be valid
        if !self.verify_signature() {
            return false;
        }

        // 2. Sender address must match public key
        if self.from != self.public_key.to_address() {
            return false;
        }

        true
    }
}

impl ChannelTransaction {
    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        let message = self.signing_message();
        self.public_key.verify(&message, &self.signature)
    }

    /// Get message to sign
    fn signing_message(&self) -> Vec<u8> {
        let mut msg = Vec::new();
        msg.extend_from_slice(self.channel_id.as_bytes());
        msg.extend_from_slice(self.from.as_bytes());
        msg.extend_from_slice(&self.fee.to_le_bytes());
        msg.extend_from_slice(&self.nonce.to_le_bytes());
        msg.extend_from_slice(self.public_key.as_bytes());

        // Include channel type specific data
        match &self.channel_type {
            ChannelType::Open { deposit_a, deposit_b, .. } => {
                msg.extend_from_slice(&deposit_a.to_le_bytes());
                msg.extend_from_slice(&deposit_b.to_le_bytes());
            }
            ChannelType::CooperativeClose { final_balance_a, final_balance_b } => {
                msg.extend_from_slice(&final_balance_a.to_le_bytes());
                msg.extend_from_slice(&final_balance_b.to_le_bytes());
            }
            _ => {}
        }

        msg
    }

    /// Check if transaction is valid
    pub fn is_valid(&self) -> bool {
        // 1. Signature must be valid
        if !self.verify_signature() {
            return false;
        }

        // 2. Sender address must match public key
        if self.from != self.public_key.to_address() {
            return false;
        }

        true
    }
}

/// Coinbase transaction (block reward)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CoinbaseTransaction {
    /// Miner's address
    pub to: Address,
    /// Block reward (calculated from work score)
    pub reward: Balance,
    /// Block height
    pub height: u64,
}

impl CoinbaseTransaction {
    pub fn new(to: Address, reward: Balance, height: u64) -> Self {
        CoinbaseTransaction { to, reward, height }
    }

    pub fn hash(&self) -> Hash {
        let serialized = bincode::serialize(self).unwrap_or_default();
        Hash::new(&serialized)
    }
}

impl TrustLineTransaction {
    /// Create and sign a new trustline transaction
    pub fn new(
        trustline_type: TrustLineType,
        trustline_id: Hash,
        from: Address,
        fee: Balance,
        nonce: u64,
        keypair: &crate::crypto::KeyPair,
    ) -> Self {
        let public_key = keypair.public_key();

        // Create unsigned transaction
        let mut tx = TrustLineTransaction {
            trustline_type,
            trustline_id,
            from,
            fee,
            nonce,
            public_key,
            signature: Ed25519Signature::from_bytes([0u8; 64]),
        };

        // Sign it
        let message = tx.signing_message();
        tx.signature = keypair.sign(&message);

        tx
    }

    /// Get message to sign (excludes signature)
    fn signing_message(&self) -> Vec<u8> {
        let mut msg = Vec::new();

        // Add trustline_id
        msg.extend_from_slice(self.trustline_id.as_bytes());

        // Add from address
        msg.extend_from_slice(self.from.as_bytes());

        // Add fee
        msg.extend_from_slice(&self.fee.to_le_bytes());

        // Add nonce
        msg.extend_from_slice(&self.nonce.to_le_bytes());

        // Add public key
        msg.extend_from_slice(self.public_key.as_bytes());

        // Add trustline type (serialized)
        if let Ok(type_bytes) = bincode::serialize(&self.trustline_type) {
            msg.extend_from_slice(&type_bytes);
        }

        msg
    }

    /// Verify transaction signature
    pub fn verify_signature(&self) -> bool {
        let message = self.signing_message();
        self.public_key.verify(&message, &self.signature)
    }

    /// Check if transaction is valid (basic checks)
    pub fn is_valid(&self) -> bool {
        // 1. Signature must be valid
        if !self.verify_signature() {
            return false;
        }

        // 2. Sender address must match public key
        if self.from != self.public_key.to_address() {
            return false;
        }

        // 3. Validate trustline type specific constraints
        match &self.trustline_type {
            TrustLineType::Create {
                account_b,
                limit_a_to_b,
                limit_b_to_a,
                quality_in,
                quality_out,
                dimensional_scale,
                ..
            } => {
                // Cannot create trustline with self
                if self.from == *account_b {
                    return false;
                }

                // Limits must be non-zero
                if *limit_a_to_b == 0 && *limit_b_to_a == 0 {
                    return false;
                }

                // Quality parameters must be valid (basis points 0-10000)
                if *quality_in > 10000 || *quality_out > 10000 {
                    return false;
                }

                // Dimensional scale must be 1-8
                if *dimensional_scale < 1 || *dimensional_scale > 8 {
                    return false;
                }
            }
            TrustLineType::UpdateLimits { limit_a_to_b, limit_b_to_a } => {
                // At least one limit must be specified
                if limit_a_to_b.is_none() && limit_b_to_a.is_none() {
                    return false;
                }
            }
            TrustLineType::EvolvePhase { delta_tau } => {
                // Delta tau must be positive and reasonable
                if *delta_tau <= 0.0 || *delta_tau > 100.0 {
                    return false;
                }
            }
            TrustLineType::Freeze | TrustLineType::Close => {
                // No additional validation needed
            }
        }

        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::crypto::KeyPair;

    #[test]
    fn test_transfer_transaction_signing() {
        let keypair = KeyPair::generate();
        let from = keypair.address();
        let to = Address::from_bytes([1u8; 32]);

        let tx = Transaction::new_transfer(from, to, 1000, 10, 1, &keypair);

        assert!(tx.verify_signature());
        assert!(tx.is_valid());
    }

    #[test]
    fn test_invalid_transfer_transaction() {
        let keypair = KeyPair::generate();
        let from = keypair.address();
        let to = Address::from_bytes([1u8; 32]);

        let tx = Transaction::new_transfer(from, to, 1000, 10, 1, &keypair);

        // Tamper with transaction
        if let Transaction::Transfer(mut transfer_tx) = tx {
            transfer_tx.amount = 9999;

            // Signature should no longer be valid
            assert!(!transfer_tx.verify_signature());
        }
    }

    #[test]
    fn test_timelock_transaction() {
        let keypair = KeyPair::generate();
        let from = keypair.address();
        let recipient = Address::from_bytes([1u8; 32]);

        // Set unlock time 1 hour in the future
        let unlock_time = chrono::Utc::now().timestamp() + 3600;

        let tx = Transaction::new_timelock(from, recipient, 5000, unlock_time, 10, 1, &keypair);

        assert!(tx.verify_signature());
        assert!(tx.is_valid());

        // Verify it's a timelock transaction
        if let Transaction::TimeLock(timelock_tx) = tx {
            assert_eq!(timelock_tx.amount, 5000);
            assert_eq!(timelock_tx.unlock_time, unlock_time);
            assert_eq!(timelock_tx.recipient, recipient);
        } else {
            panic!("Expected TimeLock transaction");
        }
    }

    #[test]
    fn test_timelock_past_time_invalid() {
        let keypair = KeyPair::generate();
        let from = keypair.address();
        let recipient = Address::from_bytes([1u8; 32]);

        // Set unlock time in the past
        let unlock_time = chrono::Utc::now().timestamp() - 3600;

        let timelock_tx = TimeLockTransaction::new(from, recipient, 5000, unlock_time, 10, 1, &keypair);

        // Should be invalid because unlock time is in the past
        assert!(!timelock_tx.is_valid());
    }

    #[test]
    fn test_transaction_accessors() {
        let keypair = KeyPair::generate();
        let from = keypair.address();
        let to = Address::from_bytes([1u8; 32]);

        let tx = Transaction::new_transfer(from, to, 1000, 10, 1, &keypair);

        assert_eq!(tx.from(), &from);
        assert_eq!(tx.fee(), 10);
        assert_eq!(tx.nonce(), 1);
    }
}
