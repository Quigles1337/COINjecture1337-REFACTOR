#!/usr/bin/env python3
"""
Parity Monitor - Real-time validation dashboard for legacy vs refactored cutover

This tool monitors the dual-run parity validator in real-time, tracking:
- Match/drift rates per function
- Performance comparisons (legacy vs refactored)
- Automatic rollback triggers
- Prometheus metrics export

Usage:
    # Start monitoring
    python parity_monitor.py

    # Check parity stats
    python parity_monitor.py --stats

    # Force rollback if drift rate > threshold
    python parity_monitor.py --check-rollback --threshold 0.01

Exit codes:
    0 - Parity validated, no issues
    1 - Drift detected above threshold
    2 - Script error
"""

import argparse
import json
import logging
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FunctionStats:
    """Statistics for a single function"""
    function_name: str
    matches: int = 0
    drifts: int = 0
    legacy_avg_ms: float = 0.0
    refactored_avg_ms: float = 0.0
    legacy_times: List[float] = field(default_factory=list)
    refactored_times: List[float] = field(default_factory=list)

    @property
    def total_calls(self) -> int:
        return self.matches + self.drifts

    @property
    def drift_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.drifts / self.total_calls

    @property
    def match_rate(self) -> float:
        return 1.0 - self.drift_rate

    @property
    def speedup(self) -> float:
        """Speedup factor: legacy_time / refactored_time"""
        if self.refactored_avg_ms == 0:
            return 0.0
        return self.legacy_avg_ms / self.refactored_avg_ms


class ParityMonitor:
    """Real-time parity monitoring and alerting"""

    def __init__(self, log_file: str = "/tmp/parity.log"):
        self.log_file = Path(log_file)
        self.function_stats: Dict[str, FunctionStats] = defaultdict(
            lambda: FunctionStats(function_name="unknown")
        )
        self.start_time = datetime.now()

    def parse_log_line(self, line: str):
        """Parse a log line and update stats"""
        try:
            # Look for parity match/drift patterns
            if "parity ✓" in line:
                self._parse_match(line)
            elif "PARITY DRIFT ✗" in line:
                self._parse_drift(line)
        except Exception as e:
            logger.debug(f"Failed to parse line: {e}")

    def _parse_match(self, line: str):
        """Parse a parity match log line"""
        # Example: compute_header_hash: parity ✓ (legacy=5.23ms, refactored=1.45ms)
        import re

        # Extract function name
        func_match = re.search(r'(\w+):\s*parity ✓', line)
        if not func_match:
            return

        func_name = func_match.group(1)

        # Extract times
        legacy_match = re.search(r'legacy=([0-9.]+)ms', line)
        refactored_match = re.search(r'refactored=([0-9.]+)ms', line)

        if legacy_match and refactored_match:
            legacy_ms = float(legacy_match.group(1))
            refactored_ms = float(refactored_match.group(1))

            stats = self.function_stats[func_name]
            stats.function_name = func_name
            stats.matches += 1
            stats.legacy_times.append(legacy_ms)
            stats.refactored_times.append(refactored_ms)
            stats.legacy_avg_ms = sum(stats.legacy_times) / len(stats.legacy_times)
            stats.refactored_avg_ms = sum(stats.refactored_times) / len(stats.refactored_times)

    def _parse_drift(self, line: str):
        """Parse a parity drift log line"""
        import re

        func_match = re.search(r'(\w+):\s*PARITY DRIFT', line)
        if not func_match:
            return

        func_name = func_match.group(1)
        stats = self.function_stats[func_name]
        stats.function_name = func_name
        stats.drifts += 1

    def get_overall_stats(self) -> Dict:
        """Get overall parity statistics"""
        total_matches = sum(s.matches for s in self.function_stats.values())
        total_drifts = sum(s.drifts for s in self.function_stats.values())
        total_calls = total_matches + total_drifts

        return {
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_calls": total_calls,
            "total_matches": total_matches,
            "total_drifts": total_drifts,
            "match_rate": total_matches / total_calls if total_calls > 0 else 0.0,
            "drift_rate": total_drifts / total_calls if total_calls > 0 else 0.0,
            "functions_tested": len(self.function_stats),
        }

    def print_report(self):
        """Print a formatted parity report"""
        overall = self.get_overall_stats()

        print("\n" + "=" * 80)
        print("                   PARITY VALIDATION REPORT")
        print("=" * 80)
        print(f"Start Time:        {overall['start_time']}")
        print(f"Uptime:            {overall['uptime_seconds']:.1f}s")
        print(f"Total Calls:       {overall['total_calls']}")
        print(f"Match Rate:        {overall['match_rate']*100:.2f}%")
        print(f"Drift Rate:        {overall['drift_rate']*100:.2f}%")
        print(f"Functions:         {overall['functions_tested']}")
        print("=" * 80)
        print()

        # Per-function breakdown
        print("PER-FUNCTION STATISTICS:")
        print("-" * 80)
        print(f"{'Function':<30} {'Calls':<10} {'Match%':<10} {'Speedup':<10}")
        print("-" * 80)

        for func_name, stats in sorted(self.function_stats.items()):
            print(
                f"{func_name:<30} "
                f"{stats.total_calls:<10} "
                f"{stats.match_rate*100:>6.2f}%   "
                f"{stats.speedup:>6.2f}x"
            )

        print("=" * 80)
        print()

        # Alert if any drifts detected
        if overall['total_drifts'] > 0:
            print("⚠️  WARNING: PARITY DRIFTS DETECTED!")
            print()
            print("Functions with drifts:")
            for func_name, stats in self.function_stats.items():
                if stats.drifts > 0:
                    print(f"  - {func_name}: {stats.drifts} drifts ({stats.drift_rate*100:.2f}%)")
            print()

    def check_rollback_condition(self, threshold: float = 0.01) -> bool:
        """
        Check if drift rate exceeds threshold (triggers rollback).

        Args:
            threshold: Maximum acceptable drift rate (default 1%)

        Returns:
            True if rollback should be triggered
        """
        overall = self.get_overall_stats()
        drift_rate = overall['drift_rate']

        if drift_rate > threshold:
            logger.error(
                f"ROLLBACK TRIGGERED: Drift rate {drift_rate*100:.2f}% "
                f"exceeds threshold {threshold*100:.2f}%"
            )
            return True

        logger.info(f"Parity healthy: {drift_rate*100:.4f}% drift rate")
        return False

    def export_prometheus_metrics(self, output_file: str = "/tmp/parity_metrics.prom"):
        """Export metrics in Prometheus format"""
        lines = []

        # Overall metrics
        overall = self.get_overall_stats()
        lines.append("# HELP coinjecture_parity_match_rate Match rate (0-1)")
        lines.append("# TYPE coinjecture_parity_match_rate gauge")
        lines.append(f"coinjecture_parity_match_rate {overall['match_rate']}")
        lines.append("")

        lines.append("# HELP coinjecture_parity_drift_rate Drift rate (0-1)")
        lines.append("# TYPE coinjecture_parity_drift_rate gauge")
        lines.append(f"coinjecture_parity_drift_rate {overall['drift_rate']}")
        lines.append("")

        # Per-function metrics
        lines.append("# HELP coinjecture_parity_function_drifts_total Drifts per function")
        lines.append("# TYPE coinjecture_parity_function_drifts_total counter")
        for func_name, stats in self.function_stats.items():
            lines.append(f'coinjecture_parity_function_drifts_total{{function="{func_name}"}} {stats.drifts}')
        lines.append("")

        lines.append("# HELP coinjecture_parity_speedup Performance speedup (legacy/refactored)")
        lines.append("# TYPE coinjecture_parity_speedup gauge")
        for func_name, stats in self.function_stats.items():
            lines.append(f'coinjecture_parity_speedup{{function="{func_name}"}} {stats.speedup:.2f}')

        Path(output_file).write_text("\n".join(lines))
        logger.info(f"Exported Prometheus metrics to {output_file}")


def tail_logs(log_file: Path, monitor: ParityMonitor):
    """Tail log file and monitor in real-time"""
    try:
        with open(log_file, 'r') as f:
            # Seek to end
            f.seek(0, 2)

            print(f"Monitoring {log_file} for parity events...")
            print("Press Ctrl+C to stop and show report\n")

            while True:
                line = f.readline()
                if line:
                    monitor.parse_log_line(line)
                else:
                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        monitor.print_report()
    except FileNotFoundError:
        logger.error(f"Log file not found: {log_file}")
        sys.exit(2)


def main():
    parser = argparse.ArgumentParser(description="Parity validation monitor")
    parser.add_argument(
        "--log-file",
        default="/tmp/parity.log",
        help="Path to parity log file"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print current stats and exit"
    )
    parser.add_argument(
        "--check-rollback",
        action="store_true",
        help="Check if rollback should be triggered"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.01,
        help="Drift rate threshold for rollback (default 1%%)"
    )
    parser.add_argument(
        "--export-metrics",
        action="store_true",
        help="Export Prometheus metrics"
    )
    parser.add_argument(
        "--metrics-file",
        default="/tmp/parity_metrics.prom",
        help="Prometheus metrics output file"
    )

    args = parser.parse_args()

    monitor = ParityMonitor(log_file=args.log_file)

    # Parse existing logs
    log_path = Path(args.log_file)
    if log_path.exists():
        logger.info(f"Parsing existing logs from {log_path}...")
        with open(log_path, 'r') as f:
            for line in f:
                monitor.parse_log_line(line)

    # Handle different modes
    if args.stats:
        monitor.print_report()
        sys.exit(0)

    if args.check_rollback:
        should_rollback = monitor.check_rollback_condition(args.threshold)
        monitor.print_report()
        sys.exit(1 if should_rollback else 0)

    if args.export_metrics:
        monitor.export_prometheus_metrics(args.metrics_file)
        sys.exit(0)

    # Default: tail logs in real-time
    tail_logs(log_path, monitor)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(2)
