# kakuro/parser.py

from typing import Tuple, List
from .model import Cell, KakuroPuzzle


def _parse_clue_token(token: str) -> Tuple[bool, int, int]:
    """
    Parse a token into (is_black, across_sum, down_sum).
    Rules:
      "."  -> white cell
      "X"  -> black, no clues
      "A16" -> black, across_sum = 16
      "D7"  -> black, down_sum = 7
      "A23D4" -> black, across_sum = 23, down_sum = 4
    """
    if token == ".":
        return False, None, None
    if token == "X":
        return True, None, None

    # It's a clue cell
    is_black = True
    across_sum = None
    down_sum = None

    i = 0
    while i < len(token):
        if token[i] == "A":
            i += 1
            num = []
            while i < len(token) and token[i].isdigit():
                num.append(token[i])
                i += 1
            across_sum = int("".join(num))
        elif token[i] == "D":
            i += 1
            num = []
            while i < len(token) and token[i].isdigit():
                num.append(token[i])
                i += 1
            down_sum = int("".join(num))
        else:
            # Unexpected character
            raise ValueError(f"Invalid clue token: {token}")

    return is_black, across_sum, down_sum


def load_puzzle(path: str) -> KakuroPuzzle:
    with open(path, "r") as f:
        header = f.readline().strip()
        if not header:
            raise ValueError("Puzzle file is empty or missing header line 'rows cols'.")

        parts = header.split()
        if len(parts) != 2:
            raise ValueError("First line must be: <rows> <cols>")

        rows, cols = map(int, parts)

        grid: List[List[Cell]] = []
        for r in range(rows):
            line = f.readline()
            if not line:
                raise ValueError(f"Not enough rows in puzzle file (expected {rows}).")
            tokens = line.strip().split()
            if len(tokens) != cols:
                raise ValueError(f"Row {r}: expected {cols} tokens, got {len(tokens)}")

            row_cells: List[Cell] = []
            for c, token in enumerate(tokens):
                is_black, across_sum, down_sum = _parse_clue_token(token)
                cell = Cell(
                    row=r,
                    col=c,
                    is_black=is_black,
                    across_sum=across_sum,
                    down_sum=down_sum,
                )
                row_cells.append(cell)
            grid.append(row_cells)

    return KakuroPuzzle(rows, cols, grid)
