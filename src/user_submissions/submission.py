from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
import time

from .aggregation import AggregationStrategy, is_open_for_more


@dataclass
class SolutionRecord:
    block_number: int
    block_hash: str
    miner_address: str

    problem_instance: dict
    solution: Any

    solution_quality: float
    work_score: float
    solve_time: float
    energy_used: float

    verified: bool
    verification_time: float

    bounty_paid: float = 0.0
    bonus_paid: float = 0.0

    timestamp: float = field(default_factory=lambda: time.time())


@dataclass
class ProblemSubmission:
    problem_type: str
    problem_template: dict
    seeding_strategy: str

    aggregation: AggregationStrategy
    aggregation_params: dict

    bounty_per_solution: float
    min_quality: float

    status: Literal['open', 'partially_filled', 'complete', 'expired'] = 'open'

    solutions_collected: list[SolutionRecord] = field(default_factory=list)

    def is_accepting_solutions(self) -> bool:
        if self.status in ['complete', 'expired']:
            return False
        return is_open_for_more(self.aggregation, existing_count=len(self.solutions_collected), params=self.aggregation_params)

    def update_status_after_append(self) -> None:
        if not self.is_accepting_solutions():
            # If full, mark complete; else if some collected, partially_filled
            if len(self.solutions_collected) > 0:
                self.status = 'complete'
            else:
                self.status = 'open'
        else:
            self.status = 'partially_filled' if len(self.solutions_collected) > 0 else 'open'


