# kakuro/combinations.py

from itertools import combinations
from typing import Dict, List, Tuple


def build_combo_table() -> Dict[Tuple[int, int], List[Tuple[int, ...]]]:
    """
    Precompute all combinations of digits 1..9 with no repetition,
    keyed by (length, sum). Used for reasoning about runs.
    """
    table: Dict[Tuple[int, int], List[Tuple[int, ...]]] = {}
    digits = range(1, 10)

    for length in range(1, 10):  # allow length 1..9, just in case
        for combo in combinations(digits, length):
            total = sum(combo)
            table.setdefault((length, total), []).append(combo)

    return table


# Create a global table we can reuse
COMBO_TABLE = build_combo_table()
