// Consensus-P2P integration utilities
package p2p

import (
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
)

// BlockToP2PMessage converts a consensus.Block to a p2p.BlockMessage
func BlockToP2PMessage(block *consensus.Block) *BlockMessage {
	// Convert transactions
	txs := make([]TransactionInBlock, len(block.Transactions))
	for i, tx := range block.Transactions {
		txs[i] = TransactionInBlock{
			TxHash:    tx.Hash,
			From:      tx.From,
			To:        tx.To,
			Amount:    tx.Amount,
			Nonce:     tx.Nonce,
			Fee:       tx.Fee,
			Signature: tx.Signature,
		}
	}

	return &BlockMessage{
		BlockNumber:  block.BlockNumber,
		ParentHash:   block.ParentHash,
		StateRoot:    block.StateRoot,
		TxRoot:       block.TxRoot,
		Timestamp:    block.Timestamp,
		Miner:        block.Validator, // Note: Miner field = Validator in PoA
		Difficulty:   block.Difficulty,
		Nonce:        block.Nonce,
		Transactions: txs,
		BlockHash:    block.BlockHash,
	}
}

// P2PMessageToBlock converts a p2p.BlockMessage to a consensus.Block
func P2PMessageToBlock(msg *BlockMessage) *consensus.Block {
	// Convert transactions
	txs := make([]*mempool.Transaction, len(msg.Transactions))
	for i, tx := range msg.Transactions {
		txs[i] = &mempool.Transaction{
			Hash:      tx.TxHash,
			From:      tx.From,
			To:        tx.To,
			Amount:    tx.Amount,
			Nonce:     tx.Nonce,
			Fee:       tx.Fee,
			Signature: tx.Signature,
			// Note: Some fields can't be reconstructed from wire format
			// GasLimit, GasPrice, Data, Timestamp, TxType, AddedAt, Priority
			// These are not critical for block validation
		}
	}

	return &consensus.Block{
		BlockNumber:  msg.BlockNumber,
		ParentHash:   msg.ParentHash,
		StateRoot:    msg.StateRoot,
		TxRoot:       msg.TxRoot,
		Timestamp:    msg.Timestamp,
		Validator:    msg.Miner, // Note: Miner field = Validator in PoA
		Difficulty:   msg.Difficulty,
		Nonce:        msg.Nonce,
		Transactions: txs,
		BlockHash:    msg.BlockHash,
		// GasLimit and GasUsed are not transmitted (can be recomputed)
		// ExtraData is not transmitted (not critical)
	}
}
