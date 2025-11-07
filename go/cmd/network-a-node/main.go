// COINjecture Network A - Minimal Test Node
// Go-native PoA consensus validator
package main

import (
	"crypto/rand"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

const Version = "4.5.0+-network-a"

func main() {
	// Parse flags
	validatorKeyHex := flag.String("validator-key", "", "Validator public key (32 hex chars)")
	dbPath := flag.String("db", "./data/network-a.db", "Database path")
	blockTime := flag.Duration("block-time", 2*time.Second, "Block production interval")
	flag.Parse()

	fmt.Printf("═══════════════════════════════════════════\n")
	fmt.Printf("  COINjecture Network A Node v%s\n", Version)
	fmt.Printf("═══════════════════════════════════════════\n\n")

	// Create logger
	log := logger.NewLogger("info")

	// Decode or generate validator key
	var validatorKey [32]byte
	if *validatorKeyHex == "" {
		log.Warn("No validator key provided, generating random key...")
		rand.Read(validatorKey[:])
	} else {
		keyBytes, err := hex.DecodeString(*validatorKeyHex)
		if err != nil || len(keyBytes) != 32 {
			log.WithError(err).Fatal("Invalid validator key")
		}
		copy(validatorKey[:], keyBytes)
	}
	fmt.Printf("✓ Validator key: %x\n\n", validatorKey)

	// Initialize database schema
	if err := state.InitializeDB(*dbPath); err != nil {
		log.WithError(err).Fatal("Failed to initialize database schema")
	}
	fmt.Printf("✓ Database schema initialized\n")

	// Create state manager
	stateManager, err := state.NewStateManager(*dbPath, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to create state manager")
	}
	defer stateManager.Close()
	fmt.Printf("✓ State manager initialized\n")

	// Create mempool
	mempoolCfg := mempool.Config{
		MaxSize:           10000,
		MaxTxAge:          1 * time.Hour,
		CleanupInterval:   1 * time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)
	fmt.Printf("✓ Mempool ready (capacity: %d)\n", mempoolCfg.MaxSize)

	// Create consensus config
	consensusCfg := consensus.ConsensusConfig{
		BlockTime:    *blockTime,
		Validators:   [][32]byte{validatorKey},
		ValidatorKey: validatorKey,
		IsValidator:  true,
	}

	// Create consensus engine
	engine := consensus.NewEngine(consensusCfg, mp, stateManager, log)
	fmt.Printf("✓ Consensus engine created\n")
	fmt.Printf("  Block time: %v\n", *blockTime)
	fmt.Printf("  Validators: %d\n\n", len(consensusCfg.Validators))

	// Start consensus engine
	fmt.Println("Starting consensus engine...")
	if err := engine.Start(); err != nil {
		log.WithError(err).Fatal("Failed to start consensus engine")
	}

	fmt.Println("✓ Consensus engine started\n")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("  Network A validator is running")
	fmt.Println("  Press Ctrl+C to stop")
	fmt.Println("═══════════════════════════════════════════\n")

	// Wait for shutdown signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\n\n═══════════════════════════════════════════")
	fmt.Println("  Shutting down gracefully...")
	fmt.Println("═══════════════════════════════════════════\n")

	// Close state manager
	if err := stateManager.Close(); err != nil {
		log.WithError(err).Error("Error closing state manager")
	}

	fmt.Println("✓ Node stopped successfully")
}
