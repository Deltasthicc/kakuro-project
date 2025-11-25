# main.py

import argparse

from kakuro import load_puzzle, solve_kakuro, KakuroPuzzle


def print_solution(puzzle: KakuroPuzzle, assignment: dict) -> None:
    """
    Print the solved puzzle as a grid, with:
      - numbers in white cells
      - clues in black cells
    """
    for r in range(puzzle.rows):
        row_str = []
        for c in range(puzzle.cols):
            cell = puzzle.grid[r][c]
            if cell.is_black:
                parts = []
                if cell.across_sum is not None:
                    parts.append(f"A{cell.across_sum}")
                if cell.down_sum is not None:
                    parts.append(f"D{cell.down_sum}")
                if not parts:
                    row_str.append("X")
                else:
                    row_str.append("".join(parts))
            else:
                val = assignment.get((r, c), 0)
                row_str.append(str(val))
        print(" ".join(row_str))


def get_heuristic_flags(method: str):
    """
    Map a method name to (use_mrv, use_lcv).
    """
    if method == "basic":
        return False, False
    elif method == "mrv":
        return True, False
    elif method == "lcv":
        return False, True
    elif method == "full":
        return True, True
    else:
        raise ValueError(f"Unknown method: {method}")

CELL_W = 7  # width of each printed cell (tweak if you want)


def format_clue_cell(cell) -> str:
    """
    Format a black clue cell like typical Kakuro:
      - down\across
      - "  \16" if only across 16
      - "23\  " if only down 23
      - "      " if pure black (no clues)
    """
    if cell.across_sum is None and cell.down_sum is None:
        return " " * CELL_W  # pure black

    down = cell.down_sum
    across = cell.across_sum

    down_str = f"{down:2d}" if down is not None else "  "
    across_str = f"{across:2d}" if across is not None else "  "

    core = f"{down_str}\\{across_str}"  # e.g. "17\24"
    return core.center(CELL_W)


def format_white_cell(val: int | None) -> str:
    """
    Format a white cell with a digit centered.
    """
    if val is None:
        txt = " "
    else:
        txt = str(val)
    return txt.center(CELL_W)


def print_pretty_board(puzzle, assignment: dict) -> None:
    """
    Pretty print: clues as d\a, digits centered, all in a clean grid.
    """
    for r in range(puzzle.rows):
        row_cells = []
        for c in range(puzzle.cols):
            cell = puzzle.grid[r][c]
            if cell.is_black:
                row_cells.append(format_clue_cell(cell))
            else:
                v = assignment.get((r, c))
                row_cells.append(format_white_cell(v))
        print("".join(row_cells))

def print_digits_only(puzzle, assignment: dict) -> None:
    for r in range(puzzle.rows):
        row_str = []
        for c in range(puzzle.cols):
            cell = puzzle.grid[r][c]
            if cell.is_black:
                row_str.append(" . ")
            else:
                v = assignment.get((r, c), 0)
                row_str.append(f"{v:2d}")
        print(" ".join(row_str))


def main():
    parser = argparse.ArgumentParser(description="Kakuro AI Solver (CSP-based)")
    parser.add_argument(
        "puzzle_file",
        type=str,
        help="Path to puzzle text file",
    )
    parser.add_argument(
        "--method",
        choices=["basic", "mrv", "lcv", "full"],
        default="full",
        help="Heuristic combination: "
             "basic=no MRV/LCV, mrv=MRV only, lcv=LCV only, full=MRV+LCV",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run and compare all heuristic combinations on this puzzle.",
    )

    args = parser.parse_args()

    if args.compare:
        configs = [
            ("basic", False, False),
            ("mrv", True, False),
            ("lcv", False, True),
            ("full", True, True),
        ]
        for name, use_mrv, use_lcv in configs:
            puzzle = load_puzzle(args.puzzle_file)
            solution, stats = solve_kakuro(puzzle, use_mrv=use_mrv, use_lcv=use_lcv)
            ok = puzzle.check_solution(solution)
            print(f"\n=== Method: {name} (MRV={use_mrv}, LCV={use_lcv}) ===")
            print(f"Nodes: {stats.nodes}, backtracks: {stats.backtracks}, "
                  f"time: {stats.time:.6f} s")
            print(f"Solution valid? {ok}")
            # Only print full grid for the 'full' method (or change as you like)
            if name == "full":
                print("\nSolved puzzle (full):")
                print_pretty_board(puzzle, solution)
    else:
        puzzle = load_puzzle(args.puzzle_file)
        use_mrv, use_lcv = get_heuristic_flags(args.method)
        solution, stats = solve_kakuro(puzzle, use_mrv=use_mrv, use_lcv=use_lcv)
        ok = puzzle.check_solution(solution)
        print(f"Method: {args.method} (MRV={use_mrv}, LCV={use_lcv})")
        print(f"Nodes: {stats.nodes}, backtracks: {stats.backtracks}, "
              f"time: {stats.time:.6f} s")
        print(f"Solution valid? {ok}")
        print("\nKakuro-style grid:")
        print_pretty_board(puzzle, solution)
        print("\nDigits-only view:")
        print_digits_only(puzzle, solution) 


if __name__ == "__main__":
    main()
