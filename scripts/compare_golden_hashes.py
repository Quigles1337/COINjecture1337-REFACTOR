#!/usr/bin/env python3
"""
Cross-Platform Golden Hash Comparison Script

This script compares golden vector test outputs across different platforms
to ensure deterministic consensus behavior.

Usage:
    python compare_golden_hashes.py <artifacts_dir>

Exit codes:
    0 - All hashes match (determinism validated)
    1 - Hash mismatch detected (CONSENSUS FAILURE)
    2 - Script error
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import re

def extract_hashes_from_test_output(content: str) -> dict:
    """
    Extract hash values from cargo test output.

    Looks for patterns like:
      Expected: abc123...
      Actual:   abc123...
      Hash: abc123...
    """
    hashes = {}

    # Pattern for "Expected: <hash>" or "Actual: <hash>" or "Hash: <hash>"
    pattern = r'(?:Expected|Actual|Hash):\s+([0-9a-f]{64})'

    # Also capture test names
    test_pattern = r'Testing:\s+(\w+)'
    current_test = None

    for line in content.split('\n'):
        # Check for test name
        test_match = re.search(test_pattern, line)
        if test_match:
            current_test = test_match.group(1)

        # Check for hash
        hash_match = re.search(pattern, line)
        if hash_match and current_test:
            hash_val = hash_match.group(1)
            hashes[current_test] = hash_val

    return hashes

def load_all_artifacts(artifacts_dir: Path) -> dict:
    """
    Load all test output artifacts from CI.

    Returns dict: {
        'platform-name': {'test_name': 'hash_value', ...},
        ...
    }
    """
    all_hashes = {}

    for artifact_dir in artifacts_dir.iterdir():
        if not artifact_dir.is_dir():
            continue

        platform_name = artifact_dir.name.replace('golden-hashes-', '')

        # Find the test output file
        output_file = artifact_dir / 'golden_output.txt'
        if not output_file.exists():
            print(f"WARNING: No golden_output.txt found in {artifact_dir}")
            continue

        content = output_file.read_text(encoding='utf-8', errors='ignore')
        hashes = extract_hashes_from_test_output(content)

        if hashes:
            all_hashes[platform_name] = hashes
            print(f"✓ Loaded {len(hashes)} hashes from {platform_name}")
        else:
            print(f"WARNING: No hashes extracted from {platform_name}")

    return all_hashes

def compare_hashes(all_hashes: dict) -> tuple[bool, list]:
    """
    Compare hashes across all platforms.

    Returns (success: bool, mismatches: list)
    """
    if not all_hashes:
        return False, ["No hash data found"]

    # Group by test name
    tests_by_name = defaultdict(dict)
    for platform, hashes in all_hashes.items():
        for test_name, hash_val in hashes.items():
            tests_by_name[test_name][platform] = hash_val

    mismatches = []
    all_match = True

    print("\n" + "=" * 60)
    print("DETERMINISM VALIDATION RESULTS")
    print("=" * 60)

    for test_name, platform_hashes in sorted(tests_by_name.items()):
        print(f"\nTest: {test_name}")

        # Get unique hash values
        unique_hashes = set(platform_hashes.values())

        if len(unique_hashes) == 1:
            # All platforms agree
            hash_val = list(unique_hashes)[0]
            print(f"  ✅ ALL PLATFORMS MATCH: {hash_val[:16]}...")
            print(f"     Validated on {len(platform_hashes)} platforms")
        else:
            # CONSENSUS FAILURE
            all_match = False
            print(f"  ❌ HASH MISMATCH DETECTED!")
            for platform, hash_val in sorted(platform_hashes.items()):
                print(f"     {platform}: {hash_val}")
            mismatches.append({
                'test': test_name,
                'platforms': platform_hashes
            })

    return all_match, mismatches

def generate_report(all_hashes: dict, all_match: bool, mismatches: list):
    """Generate detailed markdown report for CI."""
    report = []
    report.append("# Determinism Validation Report\n")
    report.append(f"**Status**: {'✅ PASS' if all_match else '❌ FAIL'}\n")
    report.append(f"**Platforms Tested**: {len(all_hashes)}\n")

    if all_match:
        report.append("\n## ✅ Success\n")
        report.append("All golden vector hashes match across all platforms.")
        report.append("Consensus is deterministic.\n")
    else:
        report.append("\n## ❌ Critical Failure\n")
        report.append("**CONSENSUS BREAKING CHANGE DETECTED**\n")
        report.append(f"Found {len(mismatches)} test(s) with hash mismatches:\n")

        for mismatch in mismatches:
            report.append(f"\n### Test: `{mismatch['test']}`\n")
            report.append("```")
            for platform, hash_val in sorted(mismatch['platforms'].items()):
                report.append(f"{platform}: {hash_val}")
            report.append("```\n")

        report.append("\n### Action Required\n")
        report.append("1. Investigate codec or serialization differences")
        report.append("2. Review recent changes to consensus-critical code")
        report.append("3. Check for platform-specific behavior")
        report.append("4. Update golden vectors if this is an intentional change")
        report.append("5. Ensure CODEOWNERS approval before merging\n")

    # Write report
    report_path = Path('determinism_report.md')
    report_path.write_text('\n'.join(report))
    print(f"\nReport written to: {report_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: compare_golden_hashes.py <artifacts_dir>")
        sys.exit(2)

    artifacts_dir = Path(sys.argv[1])
    if not artifacts_dir.exists():
        print(f"ERROR: Artifacts directory not found: {artifacts_dir}")
        sys.exit(2)

    print("=" * 60)
    print("COINjecture Golden Hash Comparison")
    print("=" * 60)

    # Load all test outputs
    all_hashes = load_all_artifacts(artifacts_dir)

    if not all_hashes:
        print("\nERROR: No valid hash data found")
        sys.exit(2)

    # Compare hashes
    all_match, mismatches = compare_hashes(all_hashes)

    # Generate report
    generate_report(all_hashes, all_match, mismatches)

    # Exit with appropriate code
    if all_match:
        print("\n" + "=" * 60)
        print("✅ DETERMINISM VALIDATED - All platforms produce identical hashes")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ DETERMINISM FAILURE - Consensus breaking change detected!")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
