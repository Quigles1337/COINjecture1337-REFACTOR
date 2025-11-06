-- COINjecture Financial Primitives - Database Schema Migration
-- Version: 4.2.0
-- Author: Quigles1337 <adz@darqlabs.io>
-- Description: Layer 1 financial primitives for $BEANS token economy
--
-- This migration creates tables for:
-- - Account state (balances, nonces)
-- - Transaction history
-- - Bounty escrows
-- - Fee tracking and revenue analytics
--
-- Deployment: Run before testnet migration (after Rust consensus is stable)

-- ============================================================================
-- ACCOUNTS TABLE
-- ============================================================================
-- Stores account balances and nonces (prevents replay attacks)
--
-- Design notes:
-- - address is Ed25519 public key (32 bytes, hex-encoded = 64 chars)
-- - balance is in wei (1 BEANS = 10^18 wei)
-- - nonce increments with each transaction (prevents double-spend)
-- - created_at/updated_at for analytics

CREATE TABLE IF NOT EXISTS accounts (
    -- Primary key: Ed25519 public key (hex-encoded)
    address TEXT PRIMARY KEY NOT NULL CHECK(length(address) = 64),

    -- Balance in wei (10^18 wei = 1 BEANS)
    balance INTEGER NOT NULL DEFAULT 0 CHECK(balance >= 0),

    -- Nonce for replay protection (increments on each transaction)
    nonce INTEGER NOT NULL DEFAULT 0 CHECK(nonce >= 0),

    -- First transaction timestamp
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),

    -- Last activity timestamp
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Index for balance queries (top holders, richlist, etc.)
CREATE INDEX IF NOT EXISTS idx_accounts_balance ON accounts(balance DESC);

-- Index for activity tracking
CREATE INDEX IF NOT EXISTS idx_accounts_updated ON accounts(updated_at DESC);


-- ============================================================================
-- TRANSACTIONS TABLE
-- ============================================================================
-- Historical record of all transactions (immutable audit log)
--
-- Design notes:
-- - tx_hash is SHA-256 of canonical transaction bytes (32 bytes hex = 64 chars)
-- - block_number NULL means tx is in mempool (not yet mined)
-- - fee is in wei, calculated by Rust (gas_limit * gas_price)
-- - data is arbitrary bytes (problem submissions, etc.)

CREATE TABLE IF NOT EXISTS transactions (
    -- Primary key: SHA-256 hash of transaction
    tx_hash TEXT PRIMARY KEY NOT NULL CHECK(length(tx_hash) = 64),

    -- Block inclusion (NULL = mempool, pending)
    block_number INTEGER,
    block_hash TEXT CHECK(block_hash IS NULL OR length(block_hash) = 64),

    -- Transaction type (1=Transfer, 2=ProblemSubmission, 3=BountyPayment)
    tx_type INTEGER NOT NULL CHECK(tx_type IN (1, 2, 3)),

    -- Sender address (Ed25519 public key, hex)
    from_address TEXT NOT NULL CHECK(length(from_address) = 64),

    -- Recipient address
    to_address TEXT NOT NULL CHECK(length(to_address) = 64),

    -- Amount transferred (wei)
    amount INTEGER NOT NULL CHECK(amount >= 0),

    -- Fee paid (wei)
    fee INTEGER NOT NULL CHECK(fee >= 0),

    -- Nonce (for replay protection)
    nonce INTEGER NOT NULL CHECK(nonce >= 0),

    -- Gas parameters
    gas_limit INTEGER NOT NULL CHECK(gas_limit > 0),
    gas_price INTEGER NOT NULL CHECK(gas_price > 0),
    gas_used INTEGER CHECK(gas_used IS NULL OR gas_used <= gas_limit),

    -- Signature (Ed25519, 64 bytes hex = 128 chars)
    signature TEXT NOT NULL CHECK(length(signature) = 128),

    -- Optional data (problem submissions, etc.)
    data BLOB,

    -- Transaction timestamp
    timestamp INTEGER NOT NULL,

    -- Status (0=pending, 1=confirmed, 2=failed)
    status INTEGER NOT NULL DEFAULT 0 CHECK(status IN (0, 1, 2)),

    -- Indexed for queries
    FOREIGN KEY (from_address) REFERENCES accounts(address),
    FOREIGN KEY (to_address) REFERENCES accounts(address)
);

-- Index for sender transaction history
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address, timestamp DESC);

-- Index for recipient transaction history
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address, timestamp DESC);

-- Index for block inclusion queries
CREATE INDEX IF NOT EXISTS idx_tx_block ON transactions(block_number, block_hash);

-- Index for mempool (pending transactions)
CREATE INDEX IF NOT EXISTS idx_tx_pending ON transactions(status, fee DESC) WHERE status = 0;

-- Index for timestamp range queries
CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp DESC);


-- ============================================================================
-- ESCROWS TABLE
-- ============================================================================
-- Bounty escrows for problem submissions (Layer 1 escrow)
--
-- Design notes:
-- - id is deterministic hash of (submitter, problem_hash, created_block)
-- - state transitions: locked (0) → released (1) OR refunded (2)
-- - release requires valid solution (verified by Rust consensus)
-- - refund occurs at expiry_block if unsolved

CREATE TABLE IF NOT EXISTS escrows (
    -- Primary key: deterministic escrow ID
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) = 64),

    -- Submitter address (Ed25519 public key, hex)
    submitter TEXT NOT NULL CHECK(length(submitter) = 64),

    -- Locked amount (wei)
    amount INTEGER NOT NULL CHECK(amount > 0),

    -- Problem hash (identifies which problem this bounty is for)
    problem_hash TEXT NOT NULL CHECK(length(problem_hash) = 64),

    -- Block at which escrow was created
    created_block INTEGER NOT NULL CHECK(created_block >= 0),

    -- Block at which escrow expires (refund becomes available)
    expiry_block INTEGER NOT NULL CHECK(expiry_block > created_block),

    -- Escrow state: 0=locked, 1=released, 2=refunded
    state INTEGER NOT NULL DEFAULT 0 CHECK(state IN (0, 1, 2)),

    -- Recipient address (solver who claimed bounty, NULL if unreleased)
    recipient TEXT CHECK(recipient IS NULL OR length(recipient) = 64),

    -- Block at which escrow was settled (released or refunded)
    settled_block INTEGER CHECK(settled_block IS NULL OR settled_block >= created_block),

    -- Settlement transaction hash
    settlement_tx TEXT CHECK(settlement_tx IS NULL OR length(settlement_tx) = 64),

    -- Timestamps
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),

    FOREIGN KEY (submitter) REFERENCES accounts(address),
    FOREIGN KEY (recipient) REFERENCES accounts(address)
);

-- Index for active escrows (state = locked)
CREATE INDEX IF NOT EXISTS idx_escrows_active ON escrows(state, expiry_block) WHERE state = 0;

-- Index for submitter escrow history
CREATE INDEX IF NOT EXISTS idx_escrows_submitter ON escrows(submitter, created_block DESC);

-- Index for problem bounties (multiple escrows per problem)
CREATE INDEX IF NOT EXISTS idx_escrows_problem ON escrows(problem_hash, state);

-- Index for expiry monitoring (find expired escrows)
CREATE INDEX IF NOT EXISTS idx_escrows_expiry ON escrows(expiry_block) WHERE state = 0;


-- ============================================================================
-- FEE_TRACKING TABLE
-- ============================================================================
-- Track fee distribution for revenue analytics
--
-- Design notes:
-- - Aggregates fees per block for monitoring
-- - Tracks burn/treasury/validator splits
-- - Used for revenue projections and tokenomics analysis

CREATE TABLE IF NOT EXISTS fee_tracking (
    -- Primary key: block number
    block_number INTEGER PRIMARY KEY NOT NULL,

    -- Block hash
    block_hash TEXT NOT NULL CHECK(length(block_hash) = 64),

    -- Total fees collected in this block (wei)
    total_fees INTEGER NOT NULL DEFAULT 0,

    -- Fee distribution (wei)
    miner_reward INTEGER NOT NULL DEFAULT 0,     -- 60%
    burned_amount INTEGER NOT NULL DEFAULT 0,    -- 20%
    treasury_amount INTEGER NOT NULL DEFAULT 0,  -- 15%
    validator_amount INTEGER NOT NULL DEFAULT 0, -- 5%

    -- Transaction count
    tx_count INTEGER NOT NULL DEFAULT 0,

    -- Average fee per transaction
    avg_fee INTEGER NOT NULL DEFAULT 0,

    -- Block timestamp
    timestamp INTEGER NOT NULL,

    -- Constraints
    CHECK(total_fees = miner_reward + burned_amount + treasury_amount + validator_amount),
    CHECK(miner_reward >= 0 AND burned_amount >= 0 AND treasury_amount >= 0 AND validator_amount >= 0)
);

-- Index for revenue analytics (time series)
CREATE INDEX IF NOT EXISTS idx_fee_tracking_timestamp ON fee_tracking(timestamp DESC);


-- ============================================================================
-- SUPPLY_METRICS TABLE
-- ============================================================================
-- Track circulating supply changes (inflation/deflation tracking)
--
-- Design notes:
-- - Updated per block with minting/burning events
-- - Tracks locked supply (escrows)
-- - Critical for tokenomics monitoring

CREATE TABLE IF NOT EXISTS supply_metrics (
    -- Primary key: block number
    block_number INTEGER PRIMARY KEY NOT NULL,

    -- Total supply (all BEANS ever minted)
    total_supply INTEGER NOT NULL CHECK(total_supply >= 0),

    -- Circulating supply (total - locked)
    circulating_supply INTEGER NOT NULL CHECK(circulating_supply >= 0 AND circulating_supply <= total_supply),

    -- Locked supply (in escrows + channels)
    locked_supply INTEGER NOT NULL DEFAULT 0 CHECK(locked_supply >= 0),

    -- Burned cumulative (total BEANS burned to date)
    burned_cumulative INTEGER NOT NULL DEFAULT 0 CHECK(burned_cumulative >= 0),

    -- Supply changes this block
    minted_this_block INTEGER NOT NULL DEFAULT 0,
    burned_this_block INTEGER NOT NULL DEFAULT 0,

    -- Block timestamp
    timestamp INTEGER NOT NULL,

    UNIQUE(block_number)
);

-- Index for supply history tracking
CREATE INDEX IF NOT EXISTS idx_supply_timestamp ON supply_metrics(timestamp DESC);


-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View: Active accounts (balance > 0)
CREATE VIEW IF NOT EXISTS active_accounts AS
SELECT
    address,
    balance,
    nonce,
    created_at,
    updated_at,
    CAST(balance AS REAL) / 1000000000000000000.0 AS balance_beans
FROM accounts
WHERE balance > 0
ORDER BY balance DESC;

-- View: Recent transactions (last 1000)
CREATE VIEW IF NOT EXISTS recent_transactions AS
SELECT
    tx_hash,
    block_number,
    tx_type,
    from_address,
    to_address,
    amount,
    fee,
    timestamp,
    status,
    CAST(amount AS REAL) / 1000000000000000000.0 AS amount_beans,
    CAST(fee AS REAL) / 1000000000000000000.0 AS fee_beans
FROM transactions
ORDER BY timestamp DESC
LIMIT 1000;

-- View: Active escrows (locked, not expired)
CREATE VIEW IF NOT EXISTS active_escrows AS
SELECT
    id,
    submitter,
    amount,
    problem_hash,
    created_block,
    expiry_block,
    CAST(amount AS REAL) / 1000000000000000000.0 AS amount_beans
FROM escrows
WHERE state = 0
ORDER BY created_block DESC;

-- View: Revenue summary (last 30 days)
CREATE VIEW IF NOT EXISTS revenue_summary AS
SELECT
    COUNT(*) AS block_count,
    SUM(total_fees) AS total_fees_wei,
    SUM(burned_amount) AS total_burned_wei,
    AVG(avg_fee) AS avg_fee_per_tx,
    SUM(tx_count) AS total_tx_count,
    CAST(SUM(total_fees) AS REAL) / 1000000000000000000.0 AS total_fees_beans,
    CAST(SUM(burned_amount) AS REAL) / 1000000000000000000.0 AS total_burned_beans
FROM fee_tracking
WHERE timestamp >= strftime('%s', 'now', '-30 days');


-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Trigger: Update account.updated_at on balance/nonce change
CREATE TRIGGER IF NOT EXISTS trigger_accounts_updated_at
AFTER UPDATE OF balance, nonce ON accounts
BEGIN
    UPDATE accounts
    SET updated_at = strftime('%s', 'now')
    WHERE address = NEW.address;
END;

-- Trigger: Update escrow.updated_at on state change
CREATE TRIGGER IF NOT EXISTS trigger_escrows_updated_at
AFTER UPDATE OF state, recipient, settled_block ON escrows
BEGIN
    UPDATE escrows
    SET updated_at = strftime('%s', 'now')
    WHERE id = NEW.id;
END;

-- Trigger: Prevent escrow state rollback (can't unlock after settled)
CREATE TRIGGER IF NOT EXISTS trigger_escrows_no_rollback
BEFORE UPDATE OF state ON escrows
WHEN OLD.state != 0 AND NEW.state = 0
BEGIN
    SELECT RAISE(ABORT, 'Cannot rollback escrow state from settled to locked');
END;


-- ============================================================================
-- INITIAL DATA (Genesis State)
-- ============================================================================

-- Genesis account (treasury for initial distribution)
-- TODO: Replace with actual genesis address
INSERT OR IGNORE INTO accounts (address, balance, nonce, created_at)
VALUES (
    '0000000000000000000000000000000000000000000000000000000000000000',
    1000000000000000000000000,  -- 1 million BEANS initial supply
    0,
    strftime('%s', 'now')
);

-- Initial supply metrics (block 0)
INSERT OR IGNORE INTO supply_metrics (
    block_number,
    total_supply,
    circulating_supply,
    locked_supply,
    burned_cumulative,
    minted_this_block,
    burned_this_block,
    timestamp
)
VALUES (
    0,
    1000000000000000000000000,  -- 1 million BEANS
    1000000000000000000000000,  -- All circulating (nothing locked yet)
    0,
    0,
    1000000000000000000000000,  -- Minted at genesis
    0,
    strftime('%s', 'now')
);


-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL,
    description TEXT
);

INSERT INTO schema_version (version, applied_at, description)
VALUES (1, strftime('%s', 'now'), 'Financial primitives v4.2.0');


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created: 6 (accounts, transactions, escrows, fee_tracking, supply_metrics, schema_version)
-- Indexes created: 13
-- Views created: 4
-- Triggers created: 3
--
-- Next steps:
-- 1. Test migration: sqlite3 test.db < 001_financial_primitives.sql
-- 2. Verify schema: sqlite3 test.db ".schema"
-- 3. Integrate with Go state manager (Phase B)
