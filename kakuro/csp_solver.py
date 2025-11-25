# kakuro/csp_solver.py

import copy
from itertools import combinations
from typing import Dict, Tuple, Set, List, Optional

from .model import KakuroPuzzle, Run
from .combinations import COMBO_TABLE

Var = Tuple[int, int]  # (row, col)
Assignment = Dict[Var, int]
Domains = Dict[Var, Set[int]]


DIGITS: Set[int] = set(range(1, 10))


def build_neighbors(puzzle: KakuroPuzzle) -> Dict[Var, Set[Var]]:
    neighbors: Dict[Var, Set[Var]] = {v: set() for v in puzzle.variables}
    for run in puzzle.runs.values():
        for v in run.cells:
            if v not in neighbors:
                neighbors[v] = set()
            for w in run.cells:
                if w != v:
                    neighbors[v].add(w)
    return neighbors


def initialize_domains(puzzle: KakuroPuzzle) -> Domains:
    """
    Start with full domain {1..9} for each white cell, then
    shrink based on run sum constraints using combination table.
    """
    domains: Domains = {v: DIGITS.copy() for v in puzzle.variables}

    changed = True
    while changed:
        changed = False
        for run in puzzle.runs.values():
            length = len(run.cells)
            combos = COMBO_TABLE.get((length, run.total), [])
            if not combos:
                # No possible combination at all -> puzzle unsatisfiable
                raise ValueError(
                    f"No combinations for run {run.run_id} with length {length} and sum {run.total}"
                )

            # Union of digits that appear in any valid combo
            valid_digits = set()
            for comb in combos:
                valid_digits.update(comb)

            # Intersect with each cell's domain
            for cell in run.cells:
                before = domains[cell]
                after = before & valid_digits
                if not after:
                    raise ValueError(
                        f"Domain wipeout at cell {cell} in run {run.run_id}"
                    )
                if after != before:
                    domains[cell] = after
                    changed = True

    return domains


def is_run_feasible(run: Run, assignment: Assignment) -> bool:
    """
    Check if the current partial assignment is compatible with this run:
    - no repeated digits
    - partial sum not already too large
    - it's still possible to reach the target sum with remaining cells.
    """
    assigned_cells = [cell for cell in run.cells if cell in assignment]
    if not assigned_cells:
        return True  # nothing assigned yet -> trivially feasible

    values = [assignment[cell] for cell in assigned_cells]

    # No duplicates within the run
    if len(values) != len(set(values)):
        return False

    current_sum = sum(values)
    remaining_cells = len(run.cells) - len(assigned_cells)

    # If all cells filled, sum must match exactly
    if remaining_cells == 0:
        return current_sum == run.total

    # If sum already exceeds total, impossible
    if current_sum >= run.total:
        return False

    remaining = run.total - current_sum
    used_digits = set(values)
    available_digits = DIGITS - used_digits

    # Quick bounds check
    if remaining_cells > len(available_digits):
        return False  # not enough distinct digits left

    sorted_avail = sorted(available_digits)
    min_possible = sum(sorted_avail[:remaining_cells])
    max_possible = sum(sorted_avail[-remaining_cells:])
    if remaining < min_possible or remaining > max_possible:
        return False

    # More precise: check if there is some combination that sums to remaining
    for comb in combinations(available_digits, remaining_cells):
        if sum(comb) == remaining:
            return True

    return False


def is_consistent(
    var: Var,
    value: int,
    assignment: Assignment,
    puzzle: KakuroPuzzle,
) -> bool:
    """
    Check local consistency of assigning var = value:
    - With runs that include this variable.
    """
    # Temporarily assign
    assignment[var] = value

    try:
        for run_id in puzzle.cell_to_runs.get(var, []):
            run = puzzle.runs[run_id]
            if not is_run_feasible(run, assignment):
                return False
    finally:
        # Undo temporary assignment
        assignment.pop(var)

    return True


def forward_check(
    var: Var,
    value: int,
    assignment: Assignment,
    domains: Domains,
    puzzle: KakuroPuzzle,
) -> bool:
    """
    Forward checking step:
    - Remove 'value' from domains of other cells in the same runs (since digits in a run must be unique).
    """
    for run_id in puzzle.cell_to_runs.get(var, []):
        run = puzzle.runs[run_id]
        for cell in run.cells:
            if cell == var:
                continue
            if cell in assignment:
                continue
            if value in domains[cell]:
                new_dom = domains[cell] - {value}
                if not new_dom:
                    return False
                domains[cell] = new_dom
    return True


def is_complete(assignment: Assignment, variables: List[Var]) -> bool:
    return len(assignment) == len(variables)


def select_unassigned_variable(
    assignment: Assignment,
    variables: List[Var],
    domains: Domains,
    neighbors: Dict[Var, Set[Var]],
) -> Var:
    """
    MRV (Minimum Remaining Values) + degree heuristic.
    """
    unassigned = [v for v in variables if v not in assignment]

    def key_fn(var: Var):
        return (len(domains[var]), -len(neighbors[var]))

    return min(unassigned, key=key_fn)


def order_domain_values(
    var: Var,
    assignment: Assignment,
    domains: Domains,
    neighbors: Dict[Var, Set[Var]],
) -> List[int]:
    """
    LCV (Least Constraining Value) heuristic.
    """
    def conflict_count(val: int) -> int:
        count = 0
        for n in neighbors[var]:
            if n not in assignment and val in domains[n]:
                count += 1
        return count

    values = list(domains[var])
    values.sort(key=conflict_count)
    return values


def backtrack(
    assignment: Assignment,
    variables: List[Var],
    domains: Domains,
    puzzle: KakuroPuzzle,
    neighbors: Dict[Var, Set[Var]],
) -> Optional[Assignment]:
    if is_complete(assignment, variables):
        return assignment

    var = select_unassigned_variable(assignment, variables, domains, neighbors)

    for value in order_domain_values(var, assignment, domains, neighbors):
        if is_consistent(var, value, assignment, puzzle):
            new_assignment = assignment.copy()
            new_assignment[var] = value

            new_domains = copy.deepcopy(domains)
            if not forward_check(var, value, new_assignment, new_domains, puzzle):
                continue

            result = backtrack(
                new_assignment,
                variables,
                new_domains,
                puzzle,
                neighbors,
            )
            if result is not None:
                return result

    return None


def solve_kakuro(puzzle: KakuroPuzzle) -> Assignment:
    """
    High-level solve function.
    """
    domains = initialize_domains(puzzle)
    neighbors = build_neighbors(puzzle)
    assignment: Assignment = {}

    solution = backtrack(
        assignment,
        puzzle.variables,
        domains,
        puzzle,
        neighbors,
    )

    if solution is None:
        raise ValueError("No solution found for this Kakuro puzzle.")

    return solution
