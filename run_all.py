#!/usr/bin/env python3
"""
Batch runner for Kakuro AI solver.

Runs all .txt puzzles in the puzzles/ folder with all methods:
    - basic
    - mrv
    - lcv
    - full

You can also use --demo to only run a subset of puzzles.

Now also prints the puzzle grid (raw text from the .txt file)
before showing the statistics.

Updated:
- Sort puzzles in natural numeric order (sample1, sample2, ..., sample15)
- Print the solved grid (answer) once per puzzle.
"""

import os
import csv
import argparse

from kakuro.parser import load_puzzle
from kakuro.csp_solver import solve_kakuro

# Methods and their (use_mrv, use_lcv) flags
METHODS = {
    "basic": (False, False),
    "mrv":   (True,  False),
    "lcv":   (False, True),
    "full":  (True,  True),
}

# Optional: demo subset (edit if you want)
DEMO_PUZZLES = {
    "sample1.txt",
    "sample2.txt",
    "sample3.txt",
    "sample4.txt",
    "sample5.txt",
}


def puzzle_sort_key(filename: str) -> int:
    """
    Extract the integer in filenames like 'sample12.txt'
    so puzzles sort as sample1, sample2, ..., sample10, ..., sample15.
    """
    digits = "".join(ch for ch in filename if ch.isdigit())
    return int(digits) if digits else 0


def print_puzzle_file(path: str) -> None:
    """Print the raw puzzle grid from the text file."""
    print("Puzzle grid (from file):")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                print("  " + line.rstrip())
    except OSError as e:
        print(f"  [Error reading puzzle file: {e}]")
    print()  # blank line


def lookup_cell_value(solution, row_idx: int, col_idx: int):
    """
    Try to find the value for a given (row, col) in the solution mapping.

    We don't know exactly how your CSP keys cells, so we try several common
    conventions:
      - (row, col) 0-based
      - (row+1, col+1) 1-based
      - "row,col" 0-based string
      - "row+1,col+1" 1-based string

    If none of these exist, return None.
    """
    candidates = (
        (row_idx, col_idx),
        (row_idx + 1, col_idx + 1),
        f"{row_idx},{col_idx}",
        f"{row_idx + 1},{col_idx + 1}",
    )

    for key in candidates:
        if key in solution:
            return solution[key]

    return None


def print_solved_grid(path: str, solution) -> None:
    """
    Print the puzzle grid with '.' cells replaced by the solved digits.

    We re-open the original text file so we can keep 'X', 'Axx', 'Dyy', etc.
    exactly as in the puzzle, and only fill numbers into '.' cells.
    """
    print("Solved grid (filled values):")
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = True
            row_idx = 0  # row index for CSP (0-based for the first puzzle row)
            for raw_line in f:
                line = raw_line.rstrip()

                # First line contains dimensions "rows cols" → just print as-is.
                if first_line:
                    print("  " + line)
                    first_line = False
                    continue

                tokens = line.split()
                solved_tokens = []
                col_idx = 0

                for tok in tokens:
                    if tok == ".":  # fillable cell
                        val = lookup_cell_value(solution, row_idx, col_idx)
                        solved_tokens.append(str(val) if val is not None else ".")
                        col_idx += 1
                    else:
                        # clue or block; keep as-is
                        solved_tokens.append(tok)
                        col_idx += 1

                print("  " + " ".join(solved_tokens))
                row_idx += 1

    except OSError as e:
        print(f"  [Error reading puzzle file for solved grid: {e}]")

    print()  # blank line at the end


def run_all(puzzles_dir: str, output_csv: str | None = None, demo_only: bool = False) -> None:
    # Collect rows for CSV
    results = []

    # Find all .txt puzzles
    puzzle_files = [
        f for f in os.listdir(puzzles_dir)
        if f.lower().endswith(".txt")
    ]
    # ✅ sort numerically (sample1, sample2, ..., sample15)
    puzzle_files = sorted(puzzle_files, key=puzzle_sort_key)

    if demo_only:
        # Keep only the demo puzzles (if present)
        puzzle_files = [f for f in puzzle_files if f in DEMO_PUZZLES]

    if not puzzle_files:
        print(f"No .txt puzzles found in {puzzles_dir} (demo_only={demo_only})")
        return

    print(f"Found {len(puzzle_files)} puzzles in '{puzzles_dir}' (demo_only={demo_only}):")
    for f in puzzle_files:
        print(f"  - {f}")
    print()

    for fname in puzzle_files:
        path = os.path.join(puzzles_dir, fname)
        puzzle_name = os.path.splitext(fname)[0]

        print("==============================")
        print(f"Puzzle: {puzzle_name} ({fname})")
        print("==============================")

        # Show the grid from the text file
        print_puzzle_file(path)

        # Load puzzle once for all methods
        puzzle = load_puzzle(path)

        # We will store the first solution we see and print that grid once at the end
        first_solution = None

        for method_name, (use_mrv, use_lcv) in METHODS.items():
            print(f"--- Method: {method_name} (MRV={use_mrv}, LCV={use_lcv}) ---")

            solution, stats = solve_kakuro(
                puzzle,
                use_mrv=use_mrv,
                use_lcv=use_lcv,
            )

            print(
                f"Nodes: {stats.nodes}, "
                f"backtracks: {stats.backtracks}, "
                f"time: {stats.time:.6f} s"
            )

            ok = puzzle.check_solution(solution)
            print(f"Solution valid? {ok}")
            print()

            # Remember the first valid solution we see (they should all be the same)
            if first_solution is None and ok:
                first_solution = solution

            results.append({
                "puzzle": puzzle_name,
                "file": fname,
                "method": method_name,
                "use_mrv": int(use_mrv),
                "use_lcv": int(use_lcv),
                "nodes": stats.nodes,
                "backtracks": stats.backtracks,
                "time_sec": f"{stats.time:.6f}",
                "valid": int(bool(ok)),
            })

        # After all methods, print the solved grid once
        if first_solution is not None:
            print_solved_grid(path, first_solution)

        print()  # extra spacing between puzzles

    # Write CSV if requested
    if output_csv is not None:
        print(f"Writing results to {output_csv} ...")
        fieldnames = [
            "puzzle",
            "file",
            "method",
            "use_mrv",
            "use_lcv",
            "nodes",
            "backtracks",
            "time_sec",
            "valid",
        ]
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Run Kakuro solver on all puzzles in a folder."
    )
    parser.add_argument(
        "--puzzles-dir",
        default="puzzles",
        help="Directory containing .txt puzzle files (default: puzzles)",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Optional path to write CSV summary (e.g., results.csv)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run only a subset of puzzles (DEMO_PUZZLES) instead of all",
    )

    args = parser.parse_args()
    run_all(args.puzzles_dir, args.csv, demo_only=args.demo)


if __name__ == "__main__":
    main()
