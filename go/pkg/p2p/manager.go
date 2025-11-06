// P2P network manager - orchestrates all P2P components
package p2p

import (
	"context"
	"fmt"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/config"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
	pubsub "github.com/libp2p/go-libp2p-pubsub"
)

// Manager orchestrates all P2P networking components
type Manager struct {
	// Configuration
	config config.P2PConfig
	log    *logger.Logger

	// Core P2P components
	host          *Host
	txGossip      *TransactionGossip
	blockGossip   *BlockGossip
	cidGossip     *CIDGossip
	peerScoring   *PeerScoring

	// Application components
	mempool *mempool.Mempool
	state   *state.StateManager

	// Consensus engine callback
	onConsensusBlock func(*BlockMessage) error

	// Shutdown
	ctx    context.Context
	cancel context.CancelFunc
}

// NewManager creates a new P2P manager with all components
func NewManager(
	ctx context.Context,
	cfg config.P2PConfig,
	mp *mempool.Mempool,
	sm *state.StateManager,
	log *logger.Logger,
) (*Manager, error) {
	ctx, cancel := context.WithCancel(ctx)

	m := &Manager{
		config:  cfg,
		log:     log,
		mempool: mp,
		state:   sm,
		ctx:     ctx,
		cancel:  cancel,
	}

	log.WithFields(logger.Fields{
		"port":               cfg.Port,
		"max_peers":          cfg.MaxPeers,
		"equilibrium_lambda": cfg.EquilibriumLambda,
		"broadcast_interval": cfg.BroadcastInterval,
	}).Info("Initializing P2P manager")

	return m, nil
}

// Start initializes and starts all P2P components
func (m *Manager) Start(ctx context.Context) error {
	m.log.Info("Starting P2P network manager")

	// 1. Create libp2p host with DHT
	host, err := NewHost(
		m.ctx,
		m.config.Port,
		m.config.BootstrapPeers,
		m.config.MaxPeers,
		m.log,
	)
	if err != nil {
		return fmt.Errorf("failed to create libp2p host: %w", err)
	}
	m.host = host

	m.log.WithFields(logger.Fields{
		"peer_id": host.ID().String(),
		"addrs":   host.Addrs(),
	}).Info("libp2p host started")

	// 2. Create pubsub instance (shared by all gossip protocols)
	ps, err := pubsub.NewGossipSub(m.ctx, host.GetHost())
	if err != nil {
		return fmt.Errorf("failed to create pubsub: %w", err)
	}

	// 3. Initialize peer scoring
	m.peerScoring = NewPeerScoring(
		m.ctx,
		m.config.QuarantineThreshold,
		BanThreshold,
		m.log,
	)

	// 4. Initialize transaction gossip (integrates with mempool)
	txGossip, err := NewTransactionGossip(
		m.ctx,
		host.GetHost(),
		m.mempool,
		m.state,
		m.log,
	)
	if err != nil {
		return fmt.Errorf("failed to create transaction gossip: %w", err)
	}
	m.txGossip = txGossip

	// 5. Initialize block gossip (with callback for block processing)
	blockGossip, err := NewBlockGossip(
		m.ctx,
		host.GetHost(),
		ps,
		m.log,
		m.handleBlockReceived,
	)
	if err != nil {
		return fmt.Errorf("failed to create block gossip: %w", err)
	}
	m.blockGossip = blockGossip

	// 6. Initialize CID gossip (equilibrium timing)
	cidGossip, err := NewCIDGossip(
		m.ctx,
		host.GetHost(),
		ps,
		m.config.EquilibriumLambda,
		m.config.EquilibriumLambda, // λ = η for perfect equilibrium
		m.log,
		m.handleCIDReceived,
	)
	if err != nil {
		return fmt.Errorf("failed to create CID gossip: %w", err)
	}
	m.cidGossip = cidGossip

	m.log.WithFields(logger.Fields{
		"peer_id":       host.ID().String(),
		"peer_count":    host.PeerCount(),
		"tx_gossip":     "enabled",
		"block_gossip":  "enabled",
		"cid_gossip":    "enabled",
		"peer_scoring":  "enabled",
	}).Info("P2P manager started successfully")

	return nil
}

// Stop shuts down all P2P components
func (m *Manager) Stop() {
	m.log.Info("Stopping P2P manager")

	// Shutdown in reverse order
	if m.cidGossip != nil {
		m.cidGossip.Close()
	}
	if m.blockGossip != nil {
		m.blockGossip.Close()
	}
	if m.txGossip != nil {
		m.txGossip.Close()
	}
	if m.peerScoring != nil {
		m.peerScoring.Close()
	}
	if m.host != nil {
		m.host.Close()
	}

	m.cancel()
	m.log.Info("P2P manager stopped")
}

// ==================== PUBLIC API ====================

// BroadcastTransaction queues a transaction for network broadcast
func (m *Manager) BroadcastTransaction(tx *mempool.Transaction) {
	if m.txGossip != nil {
		m.txGossip.BroadcastTransaction(tx)
	}
}

// BroadcastBlock broadcasts a block to the network
func (m *Manager) BroadcastBlock(block *BlockMessage) error {
	if m.blockGossip != nil {
		return m.blockGossip.BroadcastBlock(block)
	}
	return fmt.Errorf("block gossip not initialized")
}

// SetConsensusBlockHandler sets the callback for received blocks
func (m *Manager) SetConsensusBlockHandler(handler func(*BlockMessage) error) {
	m.onConsensusBlock = handler
}

// AnnounceCID announces a CID to the network (equilibrium gossip)
func (m *Manager) AnnounceCID(cid string, cidType string, blockNumber uint64) {
	if m.cidGossip == nil {
		return
	}

	switch cidType {
	case "problem":
		m.cidGossip.AnnounceProblemCID(cid, blockNumber, 0)
	case "solution":
		m.cidGossip.AnnounceSolutionCID(cid, "", blockNumber, 0)
	case "block":
		m.cidGossip.AnnounceBlockCID(cid, blockNumber, 0)
	default:
		m.log.WithField("type", cidType).Warn("Unknown CID type")
	}
}

// PeerCount returns number of connected peers
func (m *Manager) PeerCount() int {
	if m.host != nil {
		return m.host.PeerCount()
	}
	return 0
}

// GetPeerID returns local peer ID
func (m *Manager) GetPeerID() string {
	if m.host != nil {
		return m.host.ID().String()
	}
	return ""
}

// GetPeerScore returns a peer's reputation score
func (m *Manager) GetPeerScore(peerID string) int {
	if m.peerScoring == nil {
		return InitialPeerScore
	}
	// TODO: Convert string to peer.ID
	return InitialPeerScore
}

// GetNetworkStats returns P2P network statistics
func (m *Manager) GetNetworkStats() map[string]interface{} {
	stats := make(map[string]interface{})

	// Host stats
	if m.host != nil {
		stats["peer_id"] = m.host.ID().String()
		stats["peer_count"] = m.host.PeerCount()
		stats["addrs"] = m.host.Addrs()
	}

	// Peer scoring stats
	if m.peerScoring != nil {
		scoringStats := m.peerScoring.GetStats()
		for k, v := range scoringStats {
			stats["scoring_"+k] = v
		}
	}

	// CID gossip stats
	if m.cidGossip != nil {
		stats["cid_queue_size"] = m.cidGossip.GetQueueSize()
		stats["equilibrium_ratio"] = m.cidGossip.GetEquilibriumRatio()
	}

	// Mempool stats
	if m.mempool != nil {
		stats["mempool_size"] = m.mempool.Size()
	}

	return stats
}

// ==================== INTERNAL HANDLERS ====================

// handleBlockReceived processes blocks received from network
func (m *Manager) handleBlockReceived(block *BlockMessage) error {
	m.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"tx_count":     len(block.Transactions),
	}).Info("Processing block from network")

	// Forward to consensus engine if callback is set
	if m.onConsensusBlock != nil {
		if err := m.onConsensusBlock(block); err != nil {
			m.log.WithError(err).WithField("block_number", block.BlockNumber).Error("Consensus engine rejected block")
			return err
		}
	} else {
		m.log.Warn("No consensus engine callback set - block not processed")
	}

	return nil
}

// handleCIDReceived processes CIDs received from network
func (m *Manager) handleCIDReceived(cid *CIDMessage) error {
	m.log.WithFields(logger.Fields{
		"cid":          cid.CID,
		"type":         cid.Type,
		"block_number": cid.BlockNumber,
		"publisher":    cid.Publisher,
	}).Info("Processing CID from network")

	// TODO: Fetch CID content from IPFS
	// TODO: Validate content matches CID
	// TODO: Store in local IPFS node
	// TODO: Update pin quorum tracking

	// For now, just log
	m.log.WithField("cid", cid.CID).Debug("CID processing complete (stub)")

	return nil
}

// ==================== BACKWARD COMPATIBILITY ====================

// BroadcastCID is a backward-compatible wrapper for AnnounceCID
func (m *Manager) BroadcastCID(cid string) error {
	m.AnnounceCID(cid, "unknown", 0)
	return nil
}

// AddPeer manually adds a peer (for testing)
func (m *Manager) AddPeer(id, address string) error {
	m.log.WithFields(logger.Fields{
		"peer_id": id,
		"address": address,
	}).Debug("Manual peer add (deprecated)")
	return nil
}

// QuarantinePeer quarantines a misbehaving peer
func (m *Manager) QuarantinePeer(id string, reason string) error {
	m.log.WithFields(logger.Fields{
		"peer_id": id,
		"reason":  reason,
	}).Warn("Manual peer quarantine (use peer scoring instead)")
	// TODO: Convert string to peer.ID and use peerScoring
	return nil
}
