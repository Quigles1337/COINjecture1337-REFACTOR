from __future__ import annotations
from enum import Enum


class AggregationStrategy(Enum):
    ANY = "any"
    BEST = "best"
    MULTIPLE = "multiple"
    STATISTICAL = "statistical"


def is_open_for_more(aggregation: AggregationStrategy, *, existing_count: int, params: dict) -> bool:
    if aggregation == AggregationStrategy.ANY:
        return existing_count == 0
    if aggregation == AggregationStrategy.BEST:
        return existing_count < int(params.get("max_blocks", 1))
    if aggregation == AggregationStrategy.MULTIPLE:
        return existing_count < int(params.get("target_count", 1))
    if aggregation == AggregationStrategy.STATISTICAL:
        return existing_count < int(params.get("sample_size", 0))
    return False


