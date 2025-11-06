// COINjecture Daemon - Institutional-Grade Blockchain Node
//
// This daemon provides:
// - REST API for block submission and retrieval
// - P2P networking with equilibrium gossip protocol
// - Rate limiting and admission controls
// - IPFS pinning quorum for CID integrity
// - Prometheus metrics and observability
//
// Author: Quigles1337 <adz@alphx.io>
// Version: 4.0.0

package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/api"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/ipfs"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/limiter"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/metrics"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/p2p"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"

	"github.com/spf13/cobra"
)

var (
	// Version info (set by build)
	Version   = "4.0.0"
	GitCommit = "unknown"
	BuildTime = "unknown"
)

// Root command
var rootCmd = &cobra.Command{
	Use:   "coinjectured",
	Short: "COINjecture blockchain daemon",
	Long: `COINjecture daemon - Institutional-grade blockchain node.

Provides REST API, P2P networking, rate limiting, IPFS pinning quorum,
and Prometheus metrics for the COINjecture blockchain.`,
	Run: runDaemon,
}

var (
	configPath string
	logLevel   string
)

func init() {
	rootCmd.Flags().StringVarP(&configPath, "config", "c", "config.yaml", "Path to configuration file")
	rootCmd.Flags().StringVarP(&logLevel, "log-level", "l", "info", "Log level (debug, info, warn, error)")
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func runDaemon(cmd *cobra.Command, args []string) {
	// Initialize logger
	log := logger.NewLogger(logLevel)
	log.WithFields(logger.Fields{
		"version":    Version,
		"git_commit": GitCommit,
		"build_time": BuildTime,
	}).Info("Starting COINjecture daemon")

	// Load configuration
	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		log.WithError(err).Fatal("Failed to load configuration")
	}

	log.WithFields(logger.Fields{
		"api_port":       cfg.API.Port,
		"p2p_port":       cfg.P2P.Port,
		"ipfs_nodes":     len(cfg.IPFS.Nodes),
		"codec_mode":     cfg.Features.CodecMode,
		"rate_limit_enabled": cfg.RateLimiter.Enabled,
	}).Info("Configuration loaded")

	// Initialize components
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 1. Metrics exporter
	metricsExporter := metrics.NewExporter(cfg.Metrics.Port)
	go func() {
		log.WithField("port", cfg.Metrics.Port).Info("Starting metrics server")
		if err := metricsExporter.Start(); err != nil && err != http.ErrServerClosed {
			log.WithError(err).Fatal("Metrics server failed")
		}
	}()

	// 2. Rate limiter
	rateLimiter := limiter.NewRateLimiter(cfg.RateLimiter, log)
	log.Info("Rate limiter initialized")

	// 3. Mempool for transaction management
	mempoolCfg := mempool.Config{
		MaxSize:           10000,
		MaxTxAge:          1 * time.Hour,
		CleanupInterval:   5 * time.Minute,
		PriorityThreshold: 0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)
	log.Info("Mempool initialized")

	// 4. State manager (SQLite)
	stateManager, err := state.NewStateManager("coinjecture.db", log)
	if err != nil {
		log.WithError(err).Fatal("Failed to initialize state manager")
	}
	defer stateManager.Close()
	log.Info("State manager initialized")

	// 5. IPFS client with pinning quorum
	ipfsClient, err := ipfs.NewIPFSClient(cfg.IPFS, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to initialize IPFS client")
	}
	log.WithField("quorum", cfg.IPFS.PinQuorum).Info("IPFS client initialized")

	// 6. P2P network manager
	p2pManager, err := p2p.NewManager(ctx, cfg.P2P, mp, stateManager, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to initialize P2P manager")
	}
	if err := p2pManager.Start(ctx); err != nil {
		log.WithError(err).Fatal("Failed to start P2P network")
	}
	defer p2pManager.Stop()
	log.Info("P2P network started")

	// 7. Consensus engine (PoA)
	var consensusEngine *consensus.Engine
	if cfg.Consensus.Enabled {
		// Parse validator addresses
		validators := make([][32]byte, len(cfg.Consensus.Validators))
		for i, validatorHex := range cfg.Consensus.Validators {
			if len(validatorHex) != 64 {
				log.WithField("validator", validatorHex).Fatal("Invalid validator address length")
			}
			bytes, err := hex.DecodeString(validatorHex)
			if err != nil {
				log.WithError(err).Fatal("Failed to decode validator address")
			}
			copy(validators[i][:], bytes)
		}

		// Parse validator key (or generate random if empty)
		var validatorKey [32]byte
		if cfg.Consensus.ValidatorKey == "" {
			// Generate random validator key for single-node testing
			rand.Read(validatorKey[:])
			log.WithField("validator_key", hex.EncodeToString(validatorKey[:])).Warn("Generated random validator key (for testing only!)")
		} else {
			if len(cfg.Consensus.ValidatorKey) != 64 {
				log.Fatal("Invalid validator key length")
			}
			bytes, err := hex.DecodeString(cfg.Consensus.ValidatorKey)
			if err != nil {
				log.WithError(err).Fatal("Failed to decode validator key")
			}
			copy(validatorKey[:], bytes)
		}

		// If no validators specified, use our key as the only validator
		if len(validators) == 0 {
			validators = [][32]byte{validatorKey}
			log.Info("Single validator mode (this node is the only validator)")
		}

		// Create consensus config
		consensusCfg := consensus.ConsensusConfig{
			BlockTime:    cfg.Consensus.BlockTime,
			Validators:   validators,
			ValidatorKey: validatorKey,
			IsValidator:  true, // Always true in single-node or configured validator
		}

		// Initialize consensus engine
		consensusEngine = consensus.NewEngine(consensusCfg, mp, stateManager, log)

		// Set block callback for P2P broadcasting
		consensusEngine.SetNewBlockCallback(func(block *consensus.Block) {
			log.WithFields(logger.Fields{
				"block_number": block.BlockNumber,
				"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
				"tx_count":     len(block.Transactions),
			}).Info("New block produced, broadcasting to network")

			// Convert and broadcast block via P2P
			blockMsg := p2p.BlockToP2PMessage(block)
			if err := p2pManager.BroadcastBlock(blockMsg); err != nil {
				log.WithError(err).WithField("block_number", block.BlockNumber).Error("Failed to broadcast block")
			}
		})

		// Set P2P block handler to process blocks via consensus engine
		p2pManager.SetConsensusBlockHandler(func(blockMsg *p2p.BlockMessage) error {
			// Convert P2P message to consensus block
			block := p2p.P2PMessageToBlock(blockMsg)

			// Process block via consensus engine
			if err := consensusEngine.ProcessBlock(block); err != nil {
				return fmt.Errorf("consensus engine rejected block: %w", err)
			}

			return nil
		})

		// Start consensus engine
		if err := consensusEngine.Start(); err != nil {
			log.WithError(err).Fatal("Failed to start consensus engine")
		}
		defer consensusEngine.Stop()

		log.WithFields(logger.Fields{
			"block_time":     consensusCfg.BlockTime,
			"validators":     len(consensusCfg.Validators),
			"validator_key":  fmt.Sprintf("%x", validatorKey[:8]),
		}).Info("Consensus engine started")
	} else {
		log.Warn("Consensus engine disabled - no blocks will be produced")
	}

	// 8. API server
	apiServer := api.NewServer(cfg.API, rateLimiter, ipfsClient, p2pManager, mp, stateManager, log)
	go func() {
		log.WithField("port", cfg.API.Port).Info("Starting API server")
		if err := apiServer.Start(); err != nil && err != http.ErrServerClosed {
			log.WithError(err).Fatal("API server failed")
		}
	}()

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	log.Info("COINjecture daemon is running. Press Ctrl+C to stop.")

	<-sigCh
	log.Info("Received shutdown signal, stopping daemon...")

	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	// Stop components
	if err := apiServer.Shutdown(shutdownCtx); err != nil {
		log.WithError(err).Error("API server shutdown error")
	}
	p2pManager.Stop()
	if err := metricsExporter.Shutdown(shutdownCtx); err != nil {
		log.WithError(err).Error("Metrics server shutdown error")
	}

	log.Info("Daemon stopped gracefully")
}
