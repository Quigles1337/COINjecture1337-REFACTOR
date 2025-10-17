from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .aggregation import AggregationStrategy
from .submission import ProblemSubmission, SolutionRecord

# Import from core.blockchain instead of Blockchain
try:
    from ..core.blockchain import HardwareType, ProblemTier
except ImportError:
    from core.blockchain import HardwareType, ProblemTier


@dataclass
class ProblemPool:
    pending_problems: dict[str, ProblemSubmission] = field(default_factory=dict)
    current_block: int = 0

    def add_submission(self, submission_id: str, submission: ProblemSubmission) -> None:
        self.pending_problems[submission_id] = submission

    def get_submission(self, submission_id: str) -> Optional[ProblemSubmission]:
        return self.pending_problems.get(submission_id)

    def get_priority_score(self, submission: ProblemSubmission, current_block: int) -> float:
        base_reward = submission.bounty_per_solution
        urgency_multiplier = 1.0
        if submission.aggregation == AggregationStrategy.ANY:
            urgency_multiplier = 2.0
        elif submission.aggregation == AggregationStrategy.BEST:
            solutions_count = len(submission.solutions_collected)
            early_decay = float(submission.aggregation_params.get('early_bonus_decay', 0.95))
            urgency_multiplier = early_decay ** solutions_count
        elif submission.aggregation == AggregationStrategy.MULTIPLE:
            target = int(submission.aggregation_params.get('target_count', 1))
            remaining = max(0, target - len(submission.solutions_collected))
            urgency_multiplier = 1.0 + (remaining / max(1, target))
        elif submission.aggregation == AggregationStrategy.STATISTICAL:
            urgency_multiplier = 0.8
        return base_reward * urgency_multiplier

    def select_problem_for_mining(self, miner_tier: ProblemTier, miner_hardware: HardwareType) -> Optional[Tuple[str, ProblemSubmission]]:
        eligible = [
            (sid, p) for sid, p in self.pending_problems.items()
            if p.is_accepting_solutions()
        ]
        if not eligible:
            return None
        scored = [
            (sid, p, self.get_priority_score(p, self.current_block))
            for sid, p in eligible
        ]
        sid, best, _ = max(scored, key=lambda x: x[2])
        return sid, best

    def record_solution(self, submission_id: str, record: SolutionRecord) -> None:
        submission = self.pending_problems.get(submission_id)
        if not submission:
            return
        submission.solutions_collected.append(record)
        submission.update_status_after_append()


