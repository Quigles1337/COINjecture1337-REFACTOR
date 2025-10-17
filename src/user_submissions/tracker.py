from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .submission import ProblemSubmission
from .aggregation import AggregationStrategy


@dataclass
class SubmissionTracker:
    pool: 'ProblemPool'

    def get_submission_status(self, submission_id: str) -> dict:
        submission: Optional[ProblemSubmission] = self.pool.get_submission(submission_id)
        if not submission:
            return {"error": "not_found"}

        if submission.aggregation == AggregationStrategy.ANY:
            return {
                'mode': 'ANY',
                'status': 'solved' if submission.solutions_collected else 'pending',
                'solution': submission.solutions_collected[0].__dict__ if submission.solutions_collected else None,
                'solutions_count': len(submission.solutions_collected)
            }
        elif submission.aggregation == AggregationStrategy.BEST:
            solutions = sorted(submission.solutions_collected, key=lambda s: s.solution_quality, reverse=True)
            return {
                'mode': 'BEST',
                'status': submission.status,
                'solutions_count': len(solutions),
                'best_quality': solutions[0].solution_quality if solutions else None,
                'current_leader': solutions[0].miner_address if solutions else None,
                'quality_progression': [s.solution_quality for s in solutions]
            }
        elif submission.aggregation == AggregationStrategy.MULTIPLE:
            return {
                'mode': 'MULTIPLE',
                'status': submission.status,
                'progress': f"{len(submission.solutions_collected)}/{submission.aggregation_params.get('target_count', 0)}",
                'solutions_count': len(submission.solutions_collected)
            }
        elif submission.aggregation == AggregationStrategy.STATISTICAL:
            return {
                'mode': 'STATISTICAL',
                'status': submission.status,
                'progress': f"{len(submission.solutions_collected)}/{submission.aggregation_params.get('sample_size', 0)}",
            }
        return {'mode': 'UNKNOWN', 'status': submission.status}


