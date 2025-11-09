// Transaction commands

use crate::keystore::Keystore;
use crate::rpc_client::RpcClient;
use anyhow::{anyhow, Result};
use coinject_core::{Address, Balance, Ed25519Signature, PublicKey, Transaction, TransferTransaction, TimeLockTransaction};
use colored::*;
use ed25519_dalek::Signer;

/// Send tokens to an address
pub async fn send_tokens(
    from: &str,
    to_address: &str,
    amount: Balance,
    client: &RpcClient,
) -> Result<()> {
    println!("{}", "Preparing transaction...".dimmed());

    // Load sender account from keystore
    let keystore = Keystore::new()?;
    let sender = keystore.get_account(from)?;

    // Parse recipient address
    let to_address = to_address.trim_start_matches("0x");
    let to_bytes = hex::decode(to_address)
        .map_err(|e| anyhow!("Invalid recipient address: {}", e))?;

    if to_bytes.len() != 32 {
        return Err(anyhow!("Recipient address must be 32 bytes (64 hex chars)"));
    }

    let mut to_addr_bytes = [0u8; 32];
    to_addr_bytes.copy_from_slice(&to_bytes);
    let to = Address::from_bytes(to_addr_bytes);

    // Parse sender address
    let from_bytes = hex::decode(&sender.address)?;
    let mut from_addr_bytes = [0u8; 32];
    from_addr_bytes.copy_from_slice(&from_bytes);
    let from_addr = Address::from_bytes(from_addr_bytes);

    // Parse public key
    let public_key_bytes = hex::decode(&sender.public_key)?;
    let mut pk_bytes = [0u8; 32];
    pk_bytes.copy_from_slice(&public_key_bytes);
    let public_key = PublicKey::from_bytes(pk_bytes);

    // Get current nonce
    let nonce = client.get_nonce(&sender.address).await?;

    // Fee calculation for EIP-1559 style fee market
    // Default: 1000 base fee + 500 priority fee = 1500 total
    // TODO: Query actual base fee from RPC and make priority fee configurable
    let fee = 1500u128; // base_fee (1000) + priority_fee (500)

    println!();
    println!("{}", "Transaction Details".cyan().bold());
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("From:   {} ({})", sender.name.cyan(), sender.address);
    println!("To:     {}", to_address);
    println!("Amount: {} tokens", format_balance(amount));
    println!("Fee:    {} tokens", format_balance(fee));
    println!("Nonce:  {}", nonce);
    println!();

    // Create unsigned transaction for signing
    let signing_message = create_signing_message(&from_addr, &to, amount, fee, nonce, &public_key);

    // Sign transaction
    println!("{}", "Signing transaction...".dimmed());
    let signing_key = keystore.get_signing_key(from)?;
    let sig = signing_key.sign(&signing_message);
    let sig_bytes = sig.to_bytes();

    // Create signed transaction
    let signed_tx = Transaction::Transfer(TransferTransaction {
        from: from_addr,
        to,
        amount,
        fee,
        nonce,
        public_key,
        signature: Ed25519Signature::from_bytes(sig_bytes),
    });

    // Serialize and encode
    let signed_tx_bytes = bincode::serialize(&signed_tx)?;
    let tx_hex = hex::encode(&signed_tx_bytes);

    // Submit to network
    println!("{}", "Broadcasting transaction...".dimmed());

    match client.submit_transaction(&tx_hex).await {
        Ok(tx_hash) => {
            println!();
            println!("{}", "✅ Transaction Submitted Successfully".green().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("Transaction Hash: {}", tx_hash.green());
            println!();
            println!("Check status with:");
            println!("  coinject-wallet transaction status {}", tx_hash);
        }
        Err(e) => {
            println!();
            println!("{}", "❌ Transaction Failed".red().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("Error: {}", e);
        }
    }

    Ok(())
}

/// Create a time-locked transaction
pub async fn create_timelock(
    from: &str,
    recipient_address: &str,
    amount: Balance,
    unlock_in_seconds: i64,
    client: &RpcClient,
) -> Result<()> {
    println!("{}", "Preparing time-lock transaction...".dimmed());

    // Load sender account from keystore
    let keystore = Keystore::new()?;
    let sender = keystore.get_account(from)?;

    // Parse recipient address
    let recipient_address = recipient_address.trim_start_matches("0x");
    let recipient_bytes = hex::decode(recipient_address)
        .map_err(|e| anyhow!("Invalid recipient address: {}", e))?;

    if recipient_bytes.len() != 32 {
        return Err(anyhow!("Recipient address must be 32 bytes (64 hex chars)"));
    }

    let mut recipient_addr_bytes = [0u8; 32];
    recipient_addr_bytes.copy_from_slice(&recipient_bytes);
    let recipient = Address::from_bytes(recipient_addr_bytes);

    // Parse sender address
    let from_bytes = hex::decode(&sender.address)?;
    let mut from_addr_bytes = [0u8; 32];
    from_addr_bytes.copy_from_slice(&from_bytes);
    let from_addr = Address::from_bytes(from_addr_bytes);

    // Parse public key
    let public_key_bytes = hex::decode(&sender.public_key)?;
    let mut pk_bytes = [0u8; 32];
    pk_bytes.copy_from_slice(&public_key_bytes);
    let public_key = PublicKey::from_bytes(pk_bytes);

    // Calculate unlock time
    let current_time = chrono::Utc::now().timestamp();
    let unlock_time = current_time + unlock_in_seconds;

    // Get current nonce
    let nonce = client.get_nonce(&sender.address).await?;

    // Fee calculation
    let fee = 1500u128;

    println!();
    println!("{}", "Time-Lock Transaction Details".cyan().bold());
    println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    println!("From:       {} ({})", sender.name.cyan(), sender.address);
    println!("Recipient:  {}", recipient_address);
    println!("Amount:     {} tokens", format_balance(amount));
    println!("Fee:        {} tokens", format_balance(fee));
    println!("Unlock In:  {} seconds", unlock_in_seconds);
    println!("Unlock At:  {}", chrono::DateTime::from_timestamp(unlock_time, 0)
        .map(|dt| dt.to_rfc3339())
        .unwrap_or_else(|| "Invalid timestamp".to_string()));
    println!("Nonce:      {}", nonce);
    println!();

    // Create signing message for time-lock
    let signing_message = create_timelock_signing_message(
        &from_addr,
        &recipient,
        amount,
        unlock_time,
        fee,
        nonce,
        &public_key,
    );

    // Sign transaction
    println!("{}", "Signing transaction...".dimmed());
    let signing_key = keystore.get_signing_key(from)?;
    let sig = signing_key.sign(&signing_message);
    let sig_bytes = sig.to_bytes();

    // Create signed transaction
    let signed_tx = Transaction::TimeLock(TimeLockTransaction {
        from: from_addr,
        recipient,
        amount,
        unlock_time,
        fee,
        nonce,
        public_key,
        signature: Ed25519Signature::from_bytes(sig_bytes),
    });

    // Serialize and encode
    let signed_tx_bytes = bincode::serialize(&signed_tx)?;
    let tx_hex = hex::encode(&signed_tx_bytes);

    // Submit to network
    println!("{}", "Broadcasting transaction...".dimmed());

    match client.submit_transaction(&tx_hex).await {
        Ok(tx_hash) => {
            println!();
            println!("{}", "✅ Time-Lock Transaction Submitted Successfully".green().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("Transaction Hash: {}", tx_hash.green());
            println!();
            println!("Funds are now locked until: {}",
                chrono::DateTime::from_timestamp(unlock_time, 0)
                    .map(|dt| dt.to_rfc3339())
                    .unwrap_or_else(|| "Invalid timestamp".to_string()).yellow());
            println!();
            println!("Check status with:");
            println!("  coinject-wallet transaction status {}", tx_hash);
        }
        Err(e) => {
            println!();
            println!("{}", "❌ Transaction Failed".red().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("Error: {}", e);
        }
    }

    Ok(())
}

/// Get transaction status
pub async fn get_transaction_status(tx_hash: &str, client: &RpcClient) -> Result<()> {
    let tx_hash = tx_hash.trim_start_matches("0x");

    println!("{}", "Querying transaction status...".dimmed());

    match client.get_transaction_status(tx_hash).await {
        Ok(status) => {
            println!();
            println!("{}", "Transaction Status".cyan().bold());
            println!("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
            println!("TX Hash: {}", status.tx_hash);

            let status_text = match status.status.as_str() {
                "pending" => status.status.yellow(),
                "confirmed" => status.status.green(),
                "failed" => status.status.red(),
                _ => status.status.normal(),
            };
            println!("Status:  {}", status_text.bold());

            if let Some(height) = status.block_height {
                println!("Block:   #{}", height);
            }
        }
        Err(e) => {
            println!("{}", format!("❌ Failed to get transaction status: {}", e).red());
        }
    }

    Ok(())
}

// Helper functions

/// Create the signing message (matches TransferTransaction::signing_message in core)
fn create_signing_message(
    from: &Address,
    to: &Address,
    amount: Balance,
    fee: Balance,
    nonce: u64,
    public_key: &PublicKey,
) -> Vec<u8> {
    let mut msg = Vec::new();
    msg.extend_from_slice(from.as_bytes());
    msg.extend_from_slice(to.as_bytes());
    msg.extend_from_slice(&amount.to_le_bytes());
    msg.extend_from_slice(&fee.to_le_bytes());
    msg.extend_from_slice(&nonce.to_le_bytes());
    msg.extend_from_slice(public_key.as_bytes());
    msg
}

/// Create the signing message for TimeLock (matches TimeLockTransaction::signing_message in core)
fn create_timelock_signing_message(
    from: &Address,
    recipient: &Address,
    amount: Balance,
    unlock_time: i64,
    fee: Balance,
    nonce: u64,
    public_key: &PublicKey,
) -> Vec<u8> {
    let mut msg = Vec::new();
    msg.extend_from_slice(from.as_bytes());
    msg.extend_from_slice(recipient.as_bytes());
    msg.extend_from_slice(&amount.to_le_bytes());
    msg.extend_from_slice(&unlock_time.to_le_bytes());
    msg.extend_from_slice(&fee.to_le_bytes());
    msg.extend_from_slice(&nonce.to_le_bytes());
    msg.extend_from_slice(public_key.as_bytes());
    msg
}

fn format_balance(balance: u128) -> String {
    // Format with thousand separators
    let balance_str = balance.to_string();
    let mut result = String::new();
    let mut count = 0;

    for c in balance_str.chars().rev() {
        if count > 0 && count % 3 == 0 {
            result.insert(0, ',');
        }
        result.insert(0, c);
        count += 1;
    }

    result
}
