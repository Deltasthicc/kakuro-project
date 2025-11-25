# main.py

import argparse
from typing import Tuple

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


def main():
    parser = argparse.ArgumentParser(description="Kakuro AI Solver (CSP-based)")
    parser.add_argument(
        "puzzle_file",
        type=str,
        help="Path to puzzle text file",
    )

    args = parser.parse_args()

    puzzle = load_puzzle(args.puzzle_file)
    solution = solve_kakuro(puzzle)

    print("Solved puzzle:")
    print_solution(puzzle, solution)


if __name__ == "__main__":
    main()
