# kakuro/model.py

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict


@dataclass
class Cell:
    row: int
    col: int
    is_black: bool
    across_sum: Optional[int] = None
    down_sum: Optional[int] = None


@dataclass
class Run:
    run_id: int
    cells: List[Tuple[int, int]]
    total: int


class KakuroPuzzle:
    def __init__(self, rows: int, cols: int, grid: List[List[Cell]]):
        self.rows = rows
        self.cols = cols
        self.grid = grid

        # Will be filled by _extract_runs()
        self.runs: Dict[int, Run] = {}
        self.cell_to_runs: Dict[Tuple[int, int], List[int]] = {}
        self.variables: List[Tuple[int, int]] = []

        self._extract_runs()

    def _extract_runs(self) -> None:
        """Find all horizontal and vertical runs based on clue cells."""
        run_id = 0
        self.cell_to_runs = {}

        # Helper to register run
        def add_run(cells: List[Tuple[int, int]], total: int) -> None:
            nonlocal run_id
            if not cells:
                return
            r = Run(run_id=run_id, cells=cells, total=total)
            self.runs[run_id] = r
            for cell in cells:
                self.cell_to_runs.setdefault(cell, []).append(run_id)
            run_id += 1

        # Collect variables (white cells)
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if not cell.is_black:
                    self.variables.append((r, c))

        # Horizontal runs
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_black and cell.across_sum is not None:
                    # collect white cells to the right
                    cells = []
                    cc = c + 1
                    while cc < self.cols and not self.grid[r][cc].is_black:
                        cells.append((r, cc))
                        cc += 1
                    if cells:
                        add_run(cells, cell.across_sum)

        # Vertical runs
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_black and cell.down_sum is not None:
                    # collect white cells below
                    cells = []
                    rr = r + 1
                    while rr < self.rows and not self.grid[rr][c].is_black:
                        cells.append((rr, c))
                        rr += 1
                    if cells:
                        add_run(cells, cell.down_sum)
                        
    def check_solution(self, assignment: dict) -> bool:
        """
        Verify that an assignment satisfies all Kakuro constraints:
        - every run is fully assigned
        - digits in a run are all distinct
        - sum of each run equals its clue total
        """
        for run in self.runs.values():
            values = []
            for cell in run.cells:
                if cell not in assignment:
                    return False
                values.append(assignment[cell])

            # no duplicates in a run
            if len(values) != len(set(values)):
                return False

            # correct sum
            if sum(values) != run.total:
                return False

        return True

