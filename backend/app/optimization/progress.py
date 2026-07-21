"""
Live progress tracking for one grid search run.

ProgressTracker is deliberately mutable (unlike every frozen domain
model in this codebase) - it's an in-process counter `executor.py`
updates after every combination, not a domain record to be passed
around and compared; `snapshot()` is what produces the frozen,
point-in-time `OptimizationProgress` a caller can actually read/log.
"""

import time

from app.optimization.models import OptimizationProgress


class ProgressTracker:
    def __init__(self, total_combinations: int) -> None:
        self._total_combinations = total_combinations
        self._completed = 0
        self._failed = 0
        self._start_time = time.perf_counter()

    def record(self, *, failed: bool) -> None:
        self._completed += 1
        if failed:
            self._failed += 1

    def snapshot(self) -> OptimizationProgress:
        elapsed = time.perf_counter() - self._start_time
        remaining = self._total_combinations - self._completed

        estimated_remaining: float | None = None
        if self._completed > 0 and remaining > 0:
            average_seconds_per_combination = elapsed / self._completed
            estimated_remaining = average_seconds_per_combination * remaining

        return OptimizationProgress(
            total_combinations=self._total_combinations,
            completed=self._completed,
            failed=self._failed,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=estimated_remaining,
        )
