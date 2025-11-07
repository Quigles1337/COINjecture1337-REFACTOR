// Database schema initialization
package state

import (
	"database/sql"
	"fmt"
)

// InitializeDB creates the database schema
func InitializeDB(dbPath string) error {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}
	defer db.Close()

	// Create accounts table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS accounts (
			address TEXT PRIMARY KEY,
			balance INTEGER NOT NULL DEFAULT 0,
			nonce INTEGER NOT NULL DEFAULT 0,
			created_at INTEGER NOT NULL,
			updated_at INTEGER NOT NULL
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create accounts table: %w", err)
	}

	// Create escrows table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS escrows (
			id TEXT PRIMARY KEY,
			submitter TEXT NOT NULL,
			amount INTEGER NOT NULL,
			problem_hash TEXT NOT NULL,
			created_block INTEGER NOT NULL,
			expiry_block INTEGER NOT NULL,
			state INTEGER NOT NULL DEFAULT 0,
			recipient TEXT,
			settled_block INTEGER,
			settlement_tx TEXT,
			created_at INTEGER NOT NULL,
			updated_at INTEGER NOT NULL
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create escrows table: %w", err)
	}

	// Create blocks table
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS blocks (
			block_number INTEGER PRIMARY KEY,
			block_hash BLOB NOT NULL,
			parent_hash BLOB NOT NULL,
			state_root BLOB NOT NULL,
			tx_root BLOB NOT NULL,
			timestamp INTEGER NOT NULL,
			validator BLOB NOT NULL,
			difficulty INTEGER NOT NULL,
			nonce INTEGER NOT NULL,
			gas_limit INTEGER NOT NULL,
			gas_used INTEGER NOT NULL,
			extra_data BLOB,
			tx_count INTEGER NOT NULL,
			tx_data BLOB,
			created_at INTEGER NOT NULL
		)
	`)
	if err != nil {
		return fmt.Errorf("failed to create blocks table: %w", err)
	}

	// Create indexes for performance
	_, err = db.Exec(`CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(block_hash)`)
	if err != nil {
		return fmt.Errorf("failed to create block hash index: %w", err)
	}

	_, err = db.Exec(`CREATE INDEX IF NOT EXISTS idx_accounts_balance ON accounts(balance)`)
	if err != nil {
		return fmt.Errorf("failed to create accounts balance index: %w", err)
	}

	return nil
}
