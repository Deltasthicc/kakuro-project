# Kakuro AI Solver (CSD311 Project)

This project implements an AI-based solver for Kakuro puzzles using **Constraint Satisfaction Problem (CSP)** techniques.

## Method Overview

- **Representation**: Each white cell is a variable with domain {1..9}.  
- **Constraints**:
  - Each run (horizontal or vertical) must sum to its clue.
  - Digits in a run must be all different.
- **Algorithm**:
  - Precompute all valid combinations of digits for each run length and sum.
  - Use **backtracking search** with:
    - MRV (Minimum Remaining Values) + degree heuristic for variable ordering.
    - LCV (Least Constraining Value) for value ordering.
    - Forward checking and domain reduction (similar to RDV algorithm).
    - Sum feasibility pruning for each run.

## Folder Structure

```text
kakuro_ai_solver/
├── main.py                # Command-line entrypoint
├── kakuro/
│   ├── __init__.py
│   ├── model.py           # Cell, Run, KakuroPuzzle classes
│   ├── parser.py          # Reads puzzle files
│   ├── combinations.py    # Precomputed digit-sum combinations
│   └── csp_solver.py      # CSP solver (backtracking + heuristics)
└── puzzles/
    └── sample1.txt        # Example puzzle
