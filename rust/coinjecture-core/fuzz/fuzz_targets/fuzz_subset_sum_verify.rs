//! Fuzz target for subset sum verification
//!
//! CRITICAL: This tests defense against DoS attacks via:
//! - Malformed proofs
//! - Out-of-bounds indices
//! - Duplicate indices
//! - Integer overflows
//! - Budget exhaustion
//!
//! Verification MUST respect budget limits and never hang/crash.

#![no_main]

use libfuzzer_sys::{fuzz_target, arbitrary::{Arbitrary, Unstructured}};
use coinjecture_core::*;

#[derive(Debug)]
struct FuzzInput {
    problem: Problem,
    solution: Solution,
    budget: VerifyBudget,
}

impl<'a> Arbitrary<'a> for FuzzInput {
    fn arbitrary(u: &mut Unstructured<'a>) -> arbitrary::Result<Self> {
        // Generate tier
        let tier_val = u.int_in_range(1..=5)?;
        let tier = HardwareTier::from_u8(tier_val).unwrap();

        let (min_elem, max_elem) = tier.element_range();

        // Generate element count (may exceed tier limits - that's the fuzz!)
        let elem_count = u.int_in_range(0..=64)?;

        // Generate elements (may cause overflow - that's intentional!)
        let elements: Vec<i64> = (0..elem_count)
            .map(|_| u.arbitrary().unwrap_or(0))
            .collect();

        // Generate target (arbitrary, may not be achievable)
        let target: i64 = u.arbitrary()?;

        let problem = Problem {
            problem_type: ProblemType::SubsetSum,
            tier,
            elements,
            target,
            timestamp: u.arbitrary().unwrap_or(0),
        };

        // Generate solution indices (may be out of bounds - that's the fuzz!)
        let num_indices = u.int_in_range(0..=32)?;
        let indices: Vec<u32> = (0..num_indices)
            .map(|_| u.arbitrary().unwrap_or(0))
            .collect();

        let solution = Solution {
            indices,
            timestamp: u.arbitrary().unwrap_or(0),
        };

        // Generate budget (may be too restrictive - that's intentional!)
        let budget = VerifyBudget {
            max_ops: u.arbitrary().unwrap_or(1000),
            max_duration_ms: u.arbitrary().unwrap_or(100),
            max_memory_bytes: u.arbitrary().unwrap_or(1024 * 1024),
        };

        Ok(FuzzInput {
            problem,
            solution,
            budget,
        })
    }
}

fuzz_target!(|input: FuzzInput| {
    // Try to verify - should NEVER panic
    // Should ALWAYS respect budget limits
    // Should ALWAYS return within reasonable time

    let start = std::time::Instant::now();

    let result = verify::verify_solution(&input.problem, &input.solution, &input.budget);

    let duration = start.elapsed();

    // CRITICAL: Verification must complete quickly even on malformed input
    assert!(
        duration.as_millis() < 5000,
        "Verification took too long: {:?}",
        duration
    );

    // If verification succeeded, validate the result
    if let Ok(verify_result) = result {
        // Budget limits were respected
        assert!(
            verify_result.ops_used <= input.budget.max_ops,
            "Ops exceeded budget: {} > {}",
            verify_result.ops_used,
            input.budget.max_ops
        );
    }

    // All other results (errors) are acceptable
});
