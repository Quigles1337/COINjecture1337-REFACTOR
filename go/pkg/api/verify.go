//go:build cgo
// +build cgo

package api

import (
	"errors"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
)

// verifyProofWithRust verifies a proof using Rust consensus engine via CGO.
//
// This function is only available when CGO is enabled.
func verifyProofWithRust(proof *struct {
	ProblemType string
	Tier        string
	Elements    []int
	Target      int
	Solution    []int
	Commitment  string
	Timestamp   int64
}, tierStr string) (bool, error) {
	// Convert tier string to HardwareTier enum
	var tier consensus.HardwareTier
	switch tierStr {
	case "MOBILE":
		tier = consensus.TierMobile
	case "DESKTOP":
		tier = consensus.TierDesktop
	case "WORKSTATION":
		tier = consensus.TierWorkstation
	case "SERVER":
		tier = consensus.TierServer
	case "CLUSTER":
		tier = consensus.TierCluster
	default:
		return false, errors.New("invalid tier")
	}

	// Convert []int to []int64 for elements
	elements := make([]int64, len(proof.Elements))
	for i, e := range proof.Elements {
		elements[i] = int64(e)
	}

	// Convert []int to []uint32 for solution indices
	indices := make([]uint32, len(proof.Solution))
	for i, s := range proof.Solution {
		if s < 0 {
			return false, errors.New("solution indices must be non-negative")
		}
		indices[i] = uint32(s)
	}

	// Create consensus structures
	problem := &consensus.SubsetSumProblem{
		ProblemType: 0, // SubsetSum
		Tier:        tier,
		Elements:    elements,
		Target:      int64(proof.Target),
		Timestamp:   proof.Timestamp,
	}

	solution := &consensus.SubsetSumSolution{
		Indices:   indices,
		Timestamp: time.Now().Unix(), // Current timestamp for solution
	}

	// Budget limits (tier-appropriate)
	budget := &consensus.VerifyBudget{
		MaxOps:         100000,
		MaxDurationMs:  10000, // 10 seconds max
		MaxMemoryBytes: 100_000_000, // 100MB max
	}

	// Call Rust verification via CGO
	isValid, err := consensus.VerifySubsetSum(problem, solution, budget)
	if err != nil {
		return false, err
	}

	return isValid, nil
}
