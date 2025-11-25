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


def run_all(puzzles_dir: str, output_csv: str | None = None, demo_only: bool = False) -> None:
    # Collect rows for CSV
    results = []

    # Find all .txt puzzles
    puzzle_files = [
        f for f in os.listdir(puzzles_dir)
        if f.lower().endswith(".txt")
    ]
    puzzle_files.sort()

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
