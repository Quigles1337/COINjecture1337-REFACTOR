// Multi-node consensus integration tests
package integration

import (
	"context"
	"crypto/rand"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/p2p"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// TestNode represents a test blockchain node
type TestNode struct {
	ID              int
	ValidatorKey    [32]byte
	Consensus       *consensus.Engine
	Mempool         *mempool.Mempool
	StateManager    *state.StateManager
	P2PManager      *p2p.Manager
	BlocksProduced  int
	BlocksReceived  int
	mu              sync.Mutex
}

// createTestNode creates a test node with all components
func createTestNode(t *testing.T, id int, validators [][32]byte, validatorKey [32]byte, isValidator bool, bootstrapPeers []string) *TestNode {
	log := logger.NewLogger("info")

	// Create in-memory state manager
	dbPath := fmt.Sprintf(":memory:") // Each node gets its own database
	sm, err := state.NewStateManager(dbPath, log)
	if err != nil {
		t.Fatalf("Node %d: Failed to create state manager: %v", id, err)
	}

	// Create mempool
	mempoolCfg := mempool.Config{
		MaxSize:           1000,
		MaxTxAge:          time.Hour,
		CleanupInterval:   time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, log)

	// Create consensus engine
	consensusCfg := consensus.ConsensusConfig{
		BlockTime:    2 * time.Second,
		Validators:   validators,
		ValidatorKey: validatorKey,
		IsValidator:  isValidator,
	}
	engine := consensus.NewEngine(consensusCfg, mp, sm, log)

	// Create P2P manager
	p2pCfg := p2p.Config{
		ListenAddress:    fmt.Sprintf("/ip4/127.0.0.1/tcp/%d", 9000+id),
		BootstrapPeers:   bootstrapPeers,
		EnableBootstrap:  len(bootstrapPeers) > 0,
		MaxPeers:         10,
		MinPeers:         1,
		QuarantineThreshold: 100,
	}
	p2pMgr := p2p.NewManager(context.Background(), p2pCfg, mp, sm, log)

	node := &TestNode{
		ID:              id,
		ValidatorKey:    validatorKey,
		Consensus:       engine,
		Mempool:         mp,
		StateManager:    sm,
		P2PManager:      p2pMgr,
		BlocksProduced:  0,
		BlocksReceived:  0,
	}

	// Set up block production callback
	engine.SetNewBlockCallback(func(block *consensus.Block) {
		node.mu.Lock()
		node.BlocksProduced++
		node.mu.Unlock()

		// Broadcast to network
		blockMsg := p2p.BlockToP2PMessage(block)
		if err := p2pMgr.BroadcastBlock(blockMsg); err != nil {
			t.Logf("Node %d: Failed to broadcast block: %v", id, err)
		}
	})

	// Set up block receive callback
	p2pMgr.SetConsensusBlockHandler(func(blockMsg *p2p.BlockMessage) error {
		node.mu.Lock()
		node.BlocksReceived++
		node.mu.Unlock()

		// Process via consensus
		block := p2p.P2PMessageToBlock(blockMsg)
		return engine.ProcessBlock(block)
	})

	return node
}

// Start starts the test node
func (n *TestNode) Start(t *testing.T) error {
	// Start P2P
	if err := n.P2PManager.Start(); err != nil {
		return fmt.Errorf("failed to start P2P: %w", err)
	}

	// Give P2P time to initialize
	time.Sleep(500 * time.Millisecond)

	// Start consensus
	if err := n.Consensus.Start(); err != nil {
		return fmt.Errorf("failed to start consensus: %w", err)
	}

	return nil
}

// Stop stops the test node
func (n *TestNode) Stop() {
	n.Consensus.Stop()
	n.P2PManager.Stop()
	n.StateManager.Close()
}

// GetBlockHeight returns the current block height
func (n *TestNode) GetBlockHeight() uint64 {
	return n.Consensus.GetBlockHeight()
}

// GetCurrentBlockHash returns the current block hash
func (n *TestNode) GetCurrentBlockHash() [32]byte {
	block := n.Consensus.GetCurrentBlock()
	if block == nil {
		return [32]byte{}
	}
	return block.BlockHash
}

// TestThreeValidatorConsensus tests basic 3-validator consensus
func TestThreeValidatorConsensus(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	t.Log("=== Testing 3-Validator Consensus ===")

	// Create 3 validators
	validators := make([][32]byte, 3)
	for i := 0; i < 3; i++ {
		rand.Read(validators[i][:])
	}

	// Create nodes
	var nodes []*TestNode
	for i := 0; i < 3; i++ {
		var bootstrapPeers []string
		if i > 0 {
			// Connect to first node
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/9000")}
		}

		node := createTestNode(t, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Start all nodes
	for i, node := range nodes {
		if err := node.Start(t); err != nil {
			t.Fatalf("Failed to start node %d: %v", i, err)
		}
		defer node.Stop()
	}

	// Give network time to connect
	t.Log("Waiting for P2P network to connect...")
	time.Sleep(3 * time.Second)

	// Let consensus run for 20 seconds (should produce ~10 blocks with 2s block time)
	t.Log("Running consensus for 20 seconds...")
	time.Sleep(20 * time.Second)

	// Check results
	t.Log("\n=== Results ===")
	for i, node := range nodes {
		node.mu.Lock()
		produced := node.BlocksProduced
		received := node.BlocksReceived
		node.mu.Unlock()

		height := node.GetBlockHeight()
		blockHash := node.GetCurrentBlockHash()

		t.Logf("Node %d: Height=%d, Hash=%x, Produced=%d, Received=%d",
			i, height, blockHash[:8], produced, received)

		// Each validator should produce ~3-4 blocks (round-robin)
		if node.Consensus.GetBlockHeight() < 5 {
			t.Errorf("Node %d: Expected at least 5 blocks, got %d", i, height)
		}
	}

	// All nodes should converge on same block height and hash
	firstHeight := nodes[0].GetBlockHeight()
	firstHash := nodes[0].GetCurrentBlockHash()

	for i := 1; i < len(nodes); i++ {
		height := nodes[i].GetBlockHeight()
		hash := nodes[i].GetCurrentBlockHash()

		if height != firstHeight {
			t.Errorf("Height mismatch: Node 0 has %d, Node %d has %d", firstHeight, i, height)
		}

		if hash != firstHash {
			t.Errorf("Hash mismatch: Node 0 has %x, Node %d has %x", firstHash[:8], i, hash[:8])
		}
	}

	t.Log("✅ All nodes converged on same chain!")
}

// TestValidatorRotation tests round-robin validator rotation
func TestValidatorRotation(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	t.Log("=== Testing Validator Rotation ===")

	// Create 3 validators
	validators := make([][32]byte, 3)
	for i := 0; i < 3; i++ {
		rand.Read(validators[i][:])
	}

	// Create nodes
	var nodes []*TestNode
	for i := 0; i < 3; i++ {
		var bootstrapPeers []string
		if i > 0 {
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/10000")}
		}

		node := createTestNode(t, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Start all nodes
	for i, node := range nodes {
		if err := node.Start(t); err != nil {
			t.Fatalf("Failed to start node %d: %v", i, err)
		}
		defer node.Stop()
	}

	// Give network time to connect
	time.Sleep(3 * time.Second)

	// Run consensus for 30 seconds (~15 blocks)
	t.Log("Running consensus for 30 seconds...")
	time.Sleep(30 * time.Second)

	// Check that each validator produced blocks
	t.Log("\n=== Block Production ===")
	for i, node := range nodes {
		node.mu.Lock()
		produced := node.BlocksProduced
		node.mu.Unlock()

		t.Logf("Node %d produced %d blocks", i, produced)

		// Each validator should have produced at least 3 blocks (round-robin)
		if produced < 3 {
			t.Errorf("Node %d: Expected at least 3 blocks, produced %d", i, produced)
		}
	}

	t.Log("✅ Validator rotation working correctly!")
}

// TestNetworkPartitionRecovery tests recovery from network partition
func TestNetworkPartitionRecovery(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	t.Log("=== Testing Network Partition Recovery ===")

	// Create 3 validators
	validators := make([][32]byte, 3)
	for i := 0; i < 3; i++ {
		rand.Read(validators[i][:])
	}

	// Create nodes (note: actual network partitioning is hard in tests)
	// This test verifies that nodes can sync when they fall behind
	var nodes []*TestNode
	for i := 0; i < 3; i++ {
		var bootstrapPeers []string
		if i > 0 {
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/11000")}
		}

		node := createTestNode(t, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Start first 2 nodes
	for i := 0; i < 2; i++ {
		if err := nodes[i].Start(t); err != nil {
			t.Fatalf("Failed to start node %d: %v", i, err)
		}
		defer nodes[i].Stop()
	}

	time.Sleep(2 * time.Second)

	// Let first 2 nodes produce blocks
	t.Log("Running 2 nodes for 10 seconds...")
	time.Sleep(10 * time.Second)

	height := nodes[0].GetBlockHeight()
	t.Logf("Nodes have produced %d blocks", height)

	// Start third node (it's behind)
	t.Log("Starting third node (it's behind)...")
	if err := nodes[2].Start(t); err != nil {
		t.Fatalf("Failed to start node 2: %v", err)
	}
	defer nodes[2].Stop()

	// Give it time to sync
	t.Log("Waiting for sync...")
	time.Sleep(10 * time.Second)

	// Check that third node caught up
	height0 := nodes[0].GetBlockHeight()
	height2 := nodes[2].GetBlockHeight()

	t.Logf("Node 0 height: %d, Node 2 height: %d", height0, height2)

	// Should be within 2 blocks (accounting for block production during sync)
	if height0-height2 > 2 && height2-height0 > 2 {
		t.Errorf("Node 2 failed to sync: Node 0 at %d, Node 2 at %d", height0, height2)
	} else {
		t.Log("✅ Node successfully synced after partition!")
	}
}

// TestNonValidatorObserver tests a non-validator observer node
func TestNonValidatorObserver(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	t.Log("=== Testing Non-Validator Observer ===")

	// Create 2 validators
	validators := make([][32]byte, 2)
	for i := 0; i < 2; i++ {
		rand.Read(validators[i][:])
	}

	// Create 1 observer (non-validator)
	var observerKey [32]byte
	rand.Read(observerKey[:])

	// Create nodes
	var nodes []*TestNode

	// Create 2 validators
	for i := 0; i < 2; i++ {
		var bootstrapPeers []string
		if i > 0 {
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/12000")}
		}

		node := createTestNode(t, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Create 1 observer
	observerNode := createTestNode(t, 2, validators, observerKey, false, []string{"/ip4/127.0.0.1/tcp/12000"})
	nodes = append(nodes, observerNode)

	// Start all nodes
	for i, node := range nodes {
		if err := node.Start(t); err != nil {
			t.Fatalf("Failed to start node %d: %v", i, err)
		}
		defer node.Stop()
	}

	time.Sleep(3 * time.Second)

	// Run for 15 seconds
	t.Log("Running for 15 seconds...")
	time.Sleep(15 * time.Second)

	// Check results
	t.Log("\n=== Results ===")
	for i, node := range nodes {
		node.mu.Lock()
		produced := node.BlocksProduced
		received := node.BlocksReceived
		node.mu.Unlock()

		height := node.GetBlockHeight()

		t.Logf("Node %d: Height=%d, Produced=%d, Received=%d", i, height, produced, received)
	}

	// Observer should NOT produce blocks
	observerNode.mu.Lock()
	observerProduced := observerNode.BlocksProduced
	observerNode.mu.Unlock()

	if observerProduced > 0 {
		t.Errorf("Observer produced %d blocks, should be 0", observerProduced)
	}

	// Observer should receive blocks and have same height
	observerHeight := observerNode.GetBlockHeight()
	validatorHeight := nodes[0].GetBlockHeight()

	if observerHeight != validatorHeight {
		t.Errorf("Observer height (%d) doesn't match validator height (%d)", observerHeight, validatorHeight)
	} else {
		t.Log("✅ Observer correctly synced without producing blocks!")
	}
}

// TestHighLoadConsensus tests consensus under transaction load
func TestHighLoadConsensus(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	t.Log("=== Testing High Load Consensus ===")

	// Create 3 validators
	validators := make([][32]byte, 3)
	for i := 0; i < 3; i++ {
		rand.Read(validators[i][:])
	}

	// Create nodes
	var nodes []*TestNode
	for i := 0; i < 3; i++ {
		var bootstrapPeers []string
		if i > 0 {
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/13000")}
		}

		node := createTestNode(t, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Start all nodes
	for i, node := range nodes {
		if err := node.Start(t); err != nil {
			t.Fatalf("Failed to start node %d: %v", i, err)
		}
		defer node.Stop()
	}

	time.Sleep(3 * time.Second)

	// Create test accounts
	accounts := make([][32]byte, 10)
	for i := 0; i < 10; i++ {
		rand.Read(accounts[i][:])
		// Initialize with balance on all nodes
		for _, node := range nodes {
			node.StateManager.CreateAccount(accounts[i], 1000000)
		}
	}

	// Submit transactions continuously
	t.Log("Submitting high transaction load...")
	stopTx := make(chan bool)
	txCount := 0

	go func() {
		for {
			select {
			case <-stopTx:
				return
			default:
				// Create transaction
				var txHash [32]byte
				rand.Read(txHash[:])

				sender := accounts[txCount%len(accounts)]
				recipient := accounts[(txCount+1)%len(accounts)]

				tx := &mempool.Transaction{
					Hash:      txHash,
					From:      sender,
					To:        recipient,
					Amount:    100,
					Nonce:     uint64(txCount / len(accounts)),
					Fee:       10,
					GasLimit:  21000,
					Timestamp: time.Now().Unix(),
					TxType:    1,
					Priority:  10.0,
				}

				// Add to random node's mempool
				nodes[txCount%len(nodes)].Mempool.AddTransaction(tx)
				txCount++

				time.Sleep(100 * time.Millisecond) // 10 TPS
			}
		}
	}()

	// Run for 20 seconds
	time.Sleep(20 * time.Second)
	close(stopTx)

	t.Logf("Submitted %d transactions", txCount)

	// Check that all nodes have same state
	height0 := nodes[0].GetBlockHeight()
	hash0 := nodes[0].GetCurrentBlockHash()

	allMatch := true
	for i := 1; i < len(nodes); i++ {
		height := nodes[i].GetBlockHeight()
		hash := nodes[i].GetCurrentBlockHash()

		if height != height0 || hash != hash0 {
			t.Errorf("Node %d state mismatch: height=%d vs %d, hash=%x vs %x",
				i, height, height0, hash[:8], hash0[:8])
			allMatch = false
		}
	}

	if allMatch {
		t.Log("✅ All nodes maintained consensus under high load!")
	}
}

// BenchmarkMultiNodeThroughput benchmarks multi-node throughput
func BenchmarkMultiNodeThroughput(b *testing.B) {
	// Create 3 validators
	validators := make([][32]byte, 3)
	for i := 0; i < 3; i++ {
		rand.Read(validators[i][:])
	}

	// Create nodes
	var nodes []*TestNode
	for i := 0; i < 3; i++ {
		var bootstrapPeers []string
		if i > 0 {
			bootstrapPeers = []string{fmt.Sprintf("/ip4/127.0.0.1/tcp/14000")}
		}

		node := createTestNode(&testing.T{}, i, validators, validators[i], true, bootstrapPeers)
		nodes = append(nodes, node)
	}

	// Start all nodes
	for _, node := range nodes {
		node.Start(&testing.T{})
		defer node.Stop()
	}

	time.Sleep(3 * time.Second)

	b.ResetTimer()

	// Measure how many blocks produced in benchmark duration
	startHeight := nodes[0].GetBlockHeight()
	startTime := time.Now()

	// Run for benchmark duration
	time.Sleep(10 * time.Second)

	endHeight := nodes[0].GetBlockHeight()
	endTime := time.Now()

	elapsed := endTime.Sub(startTime).Seconds()
	blocksProduced := endHeight - startHeight

	b.ReportMetric(float64(blocksProduced)/elapsed, "blocks/sec")
	b.ReportMetric(elapsed/float64(blocksProduced), "sec/block")
}
