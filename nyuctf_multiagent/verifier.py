"""simple output verification helpers.

this provides a quick surface-level check comparing retrieved hints to executor summaries.
"""
import difflib
from typing import Tuple


def verify_output(hint: str, result: str, threshold: float = 0.25) -> Tuple[bool, float]:
    """return (ok, score) using a quick sequence-similarity metric.

    this shallow check is useful to catch large drifts; for production, swap in semantic or rule-based verification.
    """
    if not hint or not result:
        return False, 0.0
    score = difflib.SequenceMatcher(None, hint, result).quick_ratio()
    return score >= threshold, score
