//go:build !cgo
// +build !cgo

package api

import "errors"

// verifyProofWithRust stub for when CGO is disabled.
//
// This allows the code to compile without CGO, but verification will fail at runtime.
// To enable proof verification, build with CGO_ENABLED=1.
func verifyProofWithRust(proof *struct {
	ProblemType string
	Tier        string
	Elements    []int
	Target      int
	Solution    []int
	Commitment  string
	Timestamp   int64
}, tierStr string) (bool, error) {
	return false, errors.New("proof verification requires CGO (build with CGO_ENABLED=1 and Rust library)")
}
