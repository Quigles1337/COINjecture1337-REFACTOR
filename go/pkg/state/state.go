// Account and escrow state management with SQLite persistence
package state

import (
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	_ "modernc.org/sqlite" // Pure-Go SQLite driver (no CGO required)
)

// Account represents an account state
type Account struct {
	Address   [32]byte  // Ed25519 public key (64-char hex = 32 bytes)
	Balance   uint64    // Balance in wei
	Nonce     uint64    // Transaction nonce (replay protection)
	CreatedAt time.Time // First transaction timestamp
	UpdatedAt time.Time // Last activity timestamp
}

// Escrow represents a bounty escrow
type Escrow struct {
	ID            [32]byte   // Deterministic escrow ID
	Submitter     [32]byte   // Submitter address
	Amount        uint64     // Locked amount (wei)
	ProblemHash   [32]byte   // Problem hash
	CreatedBlock  uint64     // Creation block
	ExpiryBlock   uint64     // Expiry block
	State         uint8      // 0=Locked, 1=Released, 2=Refunded
	Recipient     *[32]byte  // Solver address (nil if unreleased)
	SettledBlock  *uint64    // Settlement block (nil if unsettled)
	SettlementTx  *[32]byte  // Settlement transaction hash
	CreatedAt     time.Time  // Creation timestamp
	UpdatedAt     time.Time  // Last update timestamp
}

// EscrowState constants
const (
	EscrowLocked   uint8 = 0
	EscrowReleased uint8 = 1
	EscrowRefunded uint8 = 2
)

// StateManager manages account and escrow state with SQL persistence
type StateManager struct {
	db  *sql.DB
	log *logger.Logger
	mu  sync.RWMutex
}

// NewStateManager creates a new state manager
func NewStateManager(dbPath string, log *logger.Logger) (*StateManager, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Enable WAL mode for better concurrency
	_, err = db.Exec("PRAGMA journal_mode=WAL")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to enable WAL: %w", err)
	}

	// Enable foreign keys
	_, err = db.Exec("PRAGMA foreign_keys=ON")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to enable foreign keys: %w", err)
	}

	sm := &StateManager{
		db:  db,
		log: log,
	}

	log.WithField("db_path", dbPath).Info("State manager initialized")

	return sm, nil
}

// Close closes the database connection
func (sm *StateManager) Close() error {
	return sm.db.Close()
}

// ==================== ACCOUNT STATE ====================

// GetAccount retrieves an account by address
func (sm *StateManager) GetAccount(address [32]byte) (*Account, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	addressHex := fmt.Sprintf("%x", address)

	var account Account
	var createdAtUnix, updatedAtUnix int64

	err := sm.db.QueryRow(`
		SELECT address, balance, nonce, created_at, updated_at
		FROM accounts
		WHERE address = ?
	`, addressHex).Scan(
		new(string),       // address (discard, we already have it)
		&account.Balance,
		&account.Nonce,
		&createdAtUnix,
		&updatedAtUnix,
	)

	if err == sql.ErrNoRows {
		// Account doesn't exist - return zero state
		return &Account{
			Address:   address,
			Balance:   0,
			Nonce:     0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}, nil
	}

	if err != nil {
		return nil, fmt.Errorf("failed to query account: %w", err)
	}

	account.Address = address
	account.CreatedAt = time.Unix(createdAtUnix, 0)
	account.UpdatedAt = time.Unix(updatedAtUnix, 0)

	return &account, nil
}

// CreateAccount creates a new account with initial balance
func (sm *StateManager) CreateAccount(address [32]byte, balance uint64) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	addressHex := fmt.Sprintf("%x", address)
	now := time.Now().Unix()

	_, err := sm.db.Exec(`
		INSERT INTO accounts (address, balance, nonce, created_at, updated_at)
		VALUES (?, ?, 0, ?, ?)
	`, addressHex, balance, now, now)

	if err != nil {
		return fmt.Errorf("failed to create account: %w", err)
	}

	sm.log.WithFields(logger.Fields{
		"address": fmt.Sprintf("%x", address[:8]),
		"balance": balance,
	}).Info("Account created")

	return nil
}

// UpdateAccount updates an account's balance and nonce
func (sm *StateManager) UpdateAccount(address [32]byte, balance uint64, nonce uint64) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	addressHex := fmt.Sprintf("%x", address)

	result, err := sm.db.Exec(`
		UPDATE accounts
		SET balance = ?, nonce = ?, updated_at = strftime('%s', 'now')
		WHERE address = ?
	`, balance, nonce, addressHex)

	if err != nil {
		return fmt.Errorf("failed to update account: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to check rows affected: %w", err)
	}

	if rows == 0 {
		// Account doesn't exist, create it (without locking again)
		now := time.Now().Unix()
		_, err = sm.db.Exec(`
			INSERT INTO accounts (address, balance, nonce, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?)
		`, addressHex, balance, nonce, now, now)

		if err != nil {
			return fmt.Errorf("failed to create account: %w", err)
		}

		sm.log.WithFields(logger.Fields{
			"address": fmt.Sprintf("%x", address[:8]),
			"balance": balance,
		}).Info("Account created")
	} else {
		sm.log.WithFields(logger.Fields{
			"address": fmt.Sprintf("%x", address[:8]),
			"balance": balance,
			"nonce":   nonce,
		}).Debug("Account updated")
	}

	return nil
}

// ApplyTransaction applies a transaction to account state
//
// This performs the actual state transition:
// - Deduct amount + fee from sender
// - Add amount to recipient
// - Increment sender nonce
func (sm *StateManager) ApplyTransaction(from, to [32]byte, amount, fee uint64) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	tx, err := sm.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Get sender account
	sender, err := sm.getAccountTx(tx, from)
	if err != nil {
		return fmt.Errorf("failed to get sender account: %w", err)
	}

	// Calculate total cost
	totalCost := amount + fee
	if sender.Balance < totalCost {
		return fmt.Errorf("insufficient balance: have %d, need %d", sender.Balance, totalCost)
	}

	// Deduct from sender
	sender.Balance -= totalCost
	sender.Nonce++

	if err := sm.updateAccountTx(tx, from, sender.Balance, sender.Nonce); err != nil {
		return fmt.Errorf("failed to update sender: %w", err)
	}

	// Get recipient account
	recipient, err := sm.getAccountTx(tx, to)
	if err != nil {
		return fmt.Errorf("failed to get recipient account: %w", err)
	}

	// Add to recipient
	recipient.Balance += amount

	if err := sm.updateAccountTx(tx, to, recipient.Balance, recipient.Nonce); err != nil {
		return fmt.Errorf("failed to update recipient: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	sm.log.WithFields(logger.Fields{
		"from":   fmt.Sprintf("%x", from[:8]),
		"to":     fmt.Sprintf("%x", to[:8]),
		"amount": amount,
		"fee":    fee,
	}).Info("Transaction applied")

	return nil
}

// Helper: get account within transaction
func (sm *StateManager) getAccountTx(tx *sql.Tx, address [32]byte) (*Account, error) {
	addressHex := fmt.Sprintf("%x", address)

	var account Account
	var createdAtUnix, updatedAtUnix int64

	err := tx.QueryRow(`
		SELECT balance, nonce, created_at, updated_at
		FROM accounts
		WHERE address = ?
	`, addressHex).Scan(
		&account.Balance,
		&account.Nonce,
		&createdAtUnix,
		&updatedAtUnix,
	)

	if err == sql.ErrNoRows {
		// Account doesn't exist - return zero state
		return &Account{
			Address:   address,
			Balance:   0,
			Nonce:     0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}, nil
	}

	if err != nil {
		return nil, err
	}

	account.Address = address
	account.CreatedAt = time.Unix(createdAtUnix, 0)
	account.UpdatedAt = time.Unix(updatedAtUnix, 0)

	return &account, nil
}

// Helper: update account within transaction
func (sm *StateManager) updateAccountTx(tx *sql.Tx, address [32]byte, balance, nonce uint64) error {
	addressHex := fmt.Sprintf("%x", address)

	result, err := tx.Exec(`
		UPDATE accounts
		SET balance = ?, nonce = ?, updated_at = strftime('%s', 'now')
		WHERE address = ?
	`, balance, nonce, addressHex)

	if err != nil {
		return err
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rows == 0 {
		// Account doesn't exist, create it
		now := time.Now().Unix()
		_, err = tx.Exec(`
			INSERT INTO accounts (address, balance, nonce, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?)
		`, addressHex, balance, nonce, now, now)
		return err
	}

	return nil
}

// ==================== STATE ROLLBACK & REPLAY ====================

// ClearAccountState clears all account state (for chain reorganization)
func (sm *StateManager) ClearAccountState() error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	_, err := sm.db.Exec("DELETE FROM accounts")
	if err != nil {
		return fmt.Errorf("failed to clear accounts: %w", err)
	}

	sm.log.Warn("Account state cleared for chain reorganization")
	return nil
}

// ClearEscrowState clears all escrow state (for chain reorganization)
func (sm *StateManager) ClearEscrowState() error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	_, err := sm.db.Exec("DELETE FROM escrows")
	if err != nil {
		return fmt.Errorf("failed to clear escrows: %w", err)
	}

	sm.log.Warn("Escrow state cleared for chain reorganization")
	return nil
}

// GetAccountSnapshot returns a snapshot of all accounts
func (sm *StateManager) GetAccountSnapshot() (map[[32]byte]*Account, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	snapshot := make(map[[32]byte]*Account)

	rows, err := sm.db.Query(`
		SELECT address, balance, nonce, created_at, updated_at
		FROM accounts
	`)
	if err != nil {
		return nil, fmt.Errorf("failed to query accounts: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var addressHex string
		var account Account
		var createdAtUnix, updatedAtUnix int64

		if err := rows.Scan(&addressHex, &account.Balance, &account.Nonce, &createdAtUnix, &updatedAtUnix); err != nil {
			return nil, fmt.Errorf("failed to scan account: %w", err)
		}

		var address [32]byte
		fmt.Sscanf(addressHex, "%x", &address)
		account.Address = address
		account.CreatedAt = time.Unix(createdAtUnix, 0)
		account.UpdatedAt = time.Unix(updatedAtUnix, 0)

		snapshot[address] = &account
	}

	return snapshot, nil
}

// RestoreAccountSnapshot restores accounts from a snapshot
func (sm *StateManager) RestoreAccountSnapshot(snapshot map[[32]byte]*Account) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	// Clear existing state
	if _, err := sm.db.Exec("DELETE FROM accounts"); err != nil {
		return fmt.Errorf("failed to clear accounts: %w", err)
	}

	// Restore snapshot
	for _, account := range snapshot {
		addressHex := fmt.Sprintf("%x", account.Address)
		_, err := sm.db.Exec(`
			INSERT INTO accounts (address, balance, nonce, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?)
		`, addressHex, account.Balance, account.Nonce, account.CreatedAt.Unix(), account.UpdatedAt.Unix())

		if err != nil {
			return fmt.Errorf("failed to restore account: %w", err)
		}
	}

	sm.log.WithField("accounts_restored", len(snapshot)).Info("Account snapshot restored")
	return nil
}

// ==================== ESCROW STATE ====================

// GetEscrow retrieves an escrow by ID
func (sm *StateManager) GetEscrow(id [32]byte) (*Escrow, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	idHex := fmt.Sprintf("%x", id)

	var escrow Escrow
	var submitterHex, problemHashHex, recipientHex, settlementTxHex sql.NullString
	var settledBlock sql.NullInt64
	var createdAtUnix, updatedAtUnix int64

	err := sm.db.QueryRow(`
		SELECT id, submitter, amount, problem_hash, created_block, expiry_block,
			   state, recipient, settled_block, settlement_tx, created_at, updated_at
		FROM escrows
		WHERE id = ?
	`, idHex).Scan(
		new(string), // id (discard, we already have it)
		&submitterHex,
		&escrow.Amount,
		&problemHashHex,
		&escrow.CreatedBlock,
		&escrow.ExpiryBlock,
		&escrow.State,
		&recipientHex,
		&settledBlock,
		&settlementTxHex,
		&createdAtUnix,
		&updatedAtUnix,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("escrow not found: %x", id[:8])
	}

	if err != nil {
		return nil, fmt.Errorf("failed to query escrow: %w", err)
	}

	escrow.ID = id

	// Parse submitter
	if submitterHex.Valid {
		var submitter [32]byte
		fmt.Sscanf(submitterHex.String, "%x", &submitter)
		escrow.Submitter = submitter
	}

	// Parse problem hash
	if problemHashHex.Valid {
		var problemHash [32]byte
		fmt.Sscanf(problemHashHex.String, "%x", &problemHash)
		escrow.ProblemHash = problemHash
	}

	// Parse optional recipient
	if recipientHex.Valid {
		var recipient [32]byte
		fmt.Sscanf(recipientHex.String, "%x", &recipient)
		escrow.Recipient = &recipient
	}

	// Parse optional settled block
	if settledBlock.Valid {
		block := uint64(settledBlock.Int64)
		escrow.SettledBlock = &block
	}

	// Parse optional settlement tx
	if settlementTxHex.Valid {
		var settlementTx [32]byte
		fmt.Sscanf(settlementTxHex.String, "%x", &settlementTx)
		escrow.SettlementTx = &settlementTx
	}

	escrow.CreatedAt = time.Unix(createdAtUnix, 0)
	escrow.UpdatedAt = time.Unix(updatedAtUnix, 0)

	return &escrow, nil
}

// CreateEscrow creates a new escrow
func (sm *StateManager) CreateEscrow(escrow *Escrow) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	idHex := fmt.Sprintf("%x", escrow.ID)
	submitterHex := fmt.Sprintf("%x", escrow.Submitter)
	problemHashHex := fmt.Sprintf("%x", escrow.ProblemHash)
	now := time.Now().Unix()

	_, err := sm.db.Exec(`
		INSERT INTO escrows (id, submitter, amount, problem_hash, created_block, expiry_block,
							 state, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, idHex, submitterHex, escrow.Amount, problemHashHex, escrow.CreatedBlock,
		escrow.ExpiryBlock, EscrowLocked, now, now)

	if err != nil {
		return fmt.Errorf("failed to create escrow: %w", err)
	}

	sm.log.WithFields(logger.Fields{
		"id":            fmt.Sprintf("%x", escrow.ID[:8]),
		"submitter":     fmt.Sprintf("%x", escrow.Submitter[:8]),
		"amount":        escrow.Amount,
		"created_block": escrow.CreatedBlock,
		"expiry_block":  escrow.ExpiryBlock,
	}).Info("Escrow created")

	return nil
}

// ReleaseEscrow releases an escrow to the solver
func (sm *StateManager) ReleaseEscrow(id [32]byte, recipient [32]byte, settledBlock uint64, settlementTx [32]byte) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	idHex := fmt.Sprintf("%x", id)
	recipientHex := fmt.Sprintf("%x", recipient)
	settlementTxHex := fmt.Sprintf("%x", settlementTx)

	result, err := sm.db.Exec(`
		UPDATE escrows
		SET state = ?, recipient = ?, settled_block = ?, settlement_tx = ?,
			updated_at = strftime('%s', 'now')
		WHERE id = ? AND state = ?
	`, EscrowReleased, recipientHex, settledBlock, settlementTxHex, idHex, EscrowLocked)

	if err != nil {
		return fmt.Errorf("failed to release escrow: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to check rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("escrow not found or already settled: %x", id[:8])
	}

	sm.log.WithFields(logger.Fields{
		"id":        fmt.Sprintf("%x", id[:8]),
		"recipient": fmt.Sprintf("%x", recipient[:8]),
	}).Info("Escrow released")

	return nil
}

// RefundEscrow refunds an escrow to the submitter
func (sm *StateManager) RefundEscrow(id [32]byte, settledBlock uint64, settlementTx [32]byte) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	idHex := fmt.Sprintf("%x", id)
	settlementTxHex := fmt.Sprintf("%x", settlementTx)

	result, err := sm.db.Exec(`
		UPDATE escrows
		SET state = ?, settled_block = ?, settlement_tx = ?,
			updated_at = strftime('%s', 'now')
		WHERE id = ? AND state = ?
	`, EscrowRefunded, settledBlock, settlementTxHex, idHex, EscrowLocked)

	if err != nil {
		return fmt.Errorf("failed to refund escrow: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to check rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("escrow not found or already settled: %x", id[:8])
	}

	sm.log.WithFields(logger.Fields{
		"id": fmt.Sprintf("%x", id[:8]),
	}).Info("Escrow refunded")

	return nil
}
