# Kakuro AI Solver (CSD311 Project)

An AI-based Kakuro puzzle solver built on classic **Constraint Satisfaction Problem (CSP)** techniques: domain reduction, sum–feasibility filtering, forward checking, and heuristic backtracking (MRV, Degree, LCV). This README fully documents the code, architecture, puzzle format, and reasoning methodology.

---
## 1. Kakuro Recap
Kakuro is a numeric crossword: fill white cells with digits 1–9 so that:
1. Each contiguous horizontal or vertical run matches the clue sum in the black clue cell that starts it.
2. Digits inside a run are all distinct.

We treat each white cell as a variable. Horizontal and vertical runs impose all-different + sum constraints.

---
## 2. Puzzle File Format (`puzzles/*.txt`)
First line: `rows cols` (two integers). Each subsequent row has `cols` tokens separated by spaces:

Token types:
- `.` : white cell (variable)
- `X` : pure black (no clues)
- `A<number>` : black with across (horizontal) sum
- `D<number>` : black with down (vertical) sum
- `A<number>D<number>` : black with both across and down clues

Example (fragment):
```
5 5
X A16 . . D7
... (etc)
```
The parser (`parser.py`) converts each token into a `Cell` dataclass instance.

---
## 3. Code Structure Overview
```
main.py                # CLI entrypoint / printing utilities
run_all.py             # Batch benchmark runner (all puzzles, all heuristics)
kakuro/
  __init__.py          # Re-exports load_puzzle / solve_kakuro
  parser.py            # File -> KakuroPuzzle
  model.py             # Cell, Run, KakuroPuzzle (run extraction + validation)
  combinations.py      # Precomputed (length,sum)->digit combinations
  csp_solver.py        # CSP search + heuristics + forward checking
puzzles/               # Sample inputs (sample1..sample11, extendable)
```

---
## 4. Data Model (`model.py`)
### `Cell`
Fields: `row`, `col`, `is_black`, optional `across_sum`, `down_sum`.

### `Run`
Represents a contiguous horizontal or vertical sequence of white cells plus a target `total`. Only white cells are stored (`cells: List[(row,col)]`).

### `KakuroPuzzle`
Responsible for:
- Storing grid.
- Extracting runs from clue cells (`_extract_runs`):
  - For each black clue with an across sum: scan right until black.
  - For each with a down sum: scan downward until black.
- Mapping each white cell to its participating run IDs (`cell_to_runs`).
- Listing all variable coordinates (`variables`).
- Validating a final assignment (`check_solution`).

Validation checks:
1. Every run fully assigned.
2. Digits within a run distinct.
3. Sum equals target clue.

---
## 5. Parsing (`parser.py`)
Reads puzzle file, constructs grid of `Cell`, instantiates `KakuroPuzzle`. Uses helper `_parse_clue_token` to interpret tokens.

---
## 6. Combination Precomputation (`combinations.py`)
Builds `COMBO_TABLE`: for every `(length, sum)` stores all distinct digit tuples from 1–9 meeting that length and sum. This accelerates domain filtering and feasibility checks.

---
## 7. Solver Architecture (`csp_solver.py`)
Key type aliases:
- `Var = (row, col)`
- `Assignment = Dict[Var,int]`
- `Domains = Dict[Var, Set[int]]`

### 7.1 Domain Initialization (`initialize_domains`)
Starts each variable with `{1..9}` then iteratively narrows domains using run combination constraints:
- For a run of length L with target T, only digits appearing in at least one combination in `COMBO_TABLE[(L,T)]` remain admissible across that run.
- Repeats until no change (fixed-point pruning).

### 7.2 Neighbor Graph (`build_neighbors`)
For each variable, neighbors are other variables in the same runs. Used by heuristics (Degree, LCV impact counting).

### 7.3 Run Feasibility (`is_run_feasible`)
Given a partial assignment for a run:
1. Reject if duplicate digits.
2. If fully assigned, sum must equal target.
3. If partial, ensure current sum < target.
4. Compute remaining sum needed and check plausible bounds using smallest / largest available distinct digits.
5. Optionally confirm there exists a combination of remaining digits that achieves the remaining sum.

### 7.4 Local Consistency (`is_consistent`)
Tentatively assign `var = value`, verify all runs that include `var` remain feasible via `is_run_feasible`. Revert assignment afterwards.

### 7.5 Forward Checking (`forward_check`)
After assigning a value to `var`, remove that digit from domains of other cells in the same runs (enforces run distinctness early). If any domain becomes empty -> fail.

### 7.6 Variable Ordering (`select_unassigned_variable`)
Modes:
1. Basic: first unassigned.
2. MRV: choose variable with smallest remaining domain size; tie-break using degree heuristic (higher number of neighbors first) to reduce branching factor.

### 7.7 Value Ordering (`order_domain_values`)
Modes:
1. Basic: ascending numeric order.
2. LCV: For each candidate value count conflicts (how many neighbor domains would lose that value). Sort by ascending conflict count (least constraining first).

### 7.8 Backtracking Loop (`backtrack`)
Pseudocode (conceptual):
```
def backtrack(assignment):
    if all variables assigned: return assignment
    var = select_unassigned_variable(...)
    for value in order_domain_values(var,...):
        if is_consistent(var,value,...):
            assign var=value
            if forward_check(var,value,...):
                result = backtrack(assignment)
                if result: return result
            undo assignment & domain changes
    record backtrack
    return failure
```
Metrics: `SolverStats` counts nodes (states visited), backtracks (dead ends), and elapsed wall-clock time.

### 7.9 Top-Level Solve (`solve_kakuro`)
1. Initialize domains.
2. Build neighbors.
3. Run backtracking with selected heuristics.
4. Return solution + statistics (raises if unsolved).

---
## 8. CLI (`main.py`)
Arguments:
- `puzzle_file`: path to puzzle text file.
- `--method {basic|mrv|lcv|full}`: toggles heuristics.
- `--compare`: runs all four configurations sequentially.

Workflow when solving a single puzzle:
1. Load puzzle.
2. Map method -> `(use_mrv, use_lcv)` flags.
3. Call `solve_kakuro`.
4. Validate solution with `puzzle.check_solution`.
5. Print stats and a pretty board with centered digits and Kakuro-style clues (format: `down\across`). Pure black cells become blank regions.

---
## 9. Output Formats
Example (pretty board style): each cell width is uniform; clue cells show `down\across` with right/left alignment for readability. White cells contain solved digits centered.

Stats Example:
```
Method: full (MRV=True, LCV=True)
Nodes: 1234, backtracks: 56, time: 0.048321 s
Solution valid? True
```
Interpretation:
- Nodes: number of recursive states explored.
- Backtracks: dead ends requiring reversal.
- Time: performance benchmark.

---
## 10. Heuristic Effects
- MRV: reduces branching early, often fewer nodes.
- Degree tie-break: focuses on variables participating in more constraints.
- LCV: encourages choices that preserve flexibility (larger remaining domains for others).
- Forward checking: prevents wasted descent into impossible states.
- Sum feasibility pruning: strong domain shrink before search.

Combined (`full`) typically yields lowest backtracks.

---
## 11. Extensibility Ideas
- Add arc consistency (AC-3) for stronger pre-solving.
- Implement iterative deepening or depth-first with ordering refinements.
- Parallel run of different heuristic mixes.
- GUI or web front-end for interactive puzzle input.
- Caching of feasibility results for runs (memoization).

---
## 12. Troubleshooting
| Symptom | Possible Cause | Action |
|---------|----------------|--------|
| "No solution found" | Invalid puzzle file / contradictory clues | Recheck sums, run smaller test puzzle |
| Extremely long runtime | Large puzzle with weak heuristics | Use `--method full` or add more pruning |
| Wrong digits printed | Modified code bypassed `check_solution` | Ensure validation step still called |

---
## 13. Quick Start
Run with compare (Windows PowerShell):
```
python main.py puzzles/sample3.txt --compare
```
Single heuristic:
```
python main.py puzzles/sample5.txt --method full
```

Batch benchmarking across all puzzles (writes CSV):
```
python run_all.py --puzzles-dir puzzles --csv results.csv
```
Demo mode (subset only):
```
python run_all.py --demo
```

---
## 14. Glossary
- **Run**: Contiguous white cells governed by a clue sum.
- **Domain**: Set of possible digits for a variable.
- **Forward Checking**: Remove inconsistent values from neighbor domains immediately after assignment.
- **MRV**: Minimum Remaining Values heuristic.
- **LCV**: Least Constraining Value heuristic.
- **Backtrack**: Reverting an assignment after reaching inconsistency.

---
## 15. Design Rationale Summary
The solver favors readability + classic CSP patterns over micro-optimizations. Precomputing combinations shifts cost from per-node reasoning to a one-time setup step. Heuristics are modular: toggled via flags for experimentation and classroom demonstration.

---
## 16. Verification
`KakuroPuzzle.check_solution` guarantees correctness post-search. You can independently verify a solution file by writing a small script that loads & validates — or intentionally perturb a digit to confirm validation fails.

---
## 17. Limitations
- Some truncated lines in excerpts (e.g., comments inside `csp_solver.py`) in documentation do not affect core logic; the actual code drives behavior.
- No advanced consistency (e.g., full arc consistency) yet.
- Assumes well-formed puzzle files; minimal error recovery beyond basic validation.
- Batch runner `run_all.py` executes puzzles sequentially (no parallelism); for very large sets you could parallelize externally.

---
## 18. License / Usage
No license header added here; adapt according to course requirements or organization policy.

---
## 19. Batch Runner & Benchmarking (`run_all.py`)
Purpose: Automate solver runs over every `*.txt` in `puzzles/` for each heuristic configuration (`basic`, `mrv`, `lcv`, `full`). Captures performance metrics to stdout and (optionally) a CSV.

Features:
- Prints raw puzzle file first (for human inspection / reproducibility).
- Reuses a single parsed puzzle object per file for all methods (avoids repeated I/O).
- Aggregates rows: puzzle name, method flags, nodes, backtracks, time, validity.
- Optional demo subset (`--demo`) to keep quick classroom demonstrations fast.

Example command:
```
python run_all.py --puzzles-dir puzzles --csv benchmark.csv
```

## 20. CSV Output Schema
Columns written when `--csv` is provided:
| Column      | Description                               |
|-------------|-------------------------------------------|
| puzzle      | Base filename without extension           |
| file        | Original filename                         |
| method      | Heuristic label                           |
| use_mrv     | 0/1 flag                                  |
| use_lcv     | 0/1 flag                                  |
| nodes       | Total search states explored              |
| backtracks  | Dead-end reversions                       |
| time_sec    | Elapsed wall-clock seconds                |
| valid       | 0/1 solution validity check               |

## 21. Adding New Puzzles
1. Create a `.txt` file in `puzzles/` following the token format (Section 2).
2. Ensure first line has correct `rows cols` count.
3. Run a single solve to verify:
  ```
  python main.py puzzles/your_puzzle.txt --method full
  ```
4. Include in batch runs automatically (unless using `--demo`).

## 22. Demo Mode
`run_all.py --demo` limits execution to a curated set (`DEMO_PUZZLES`) for faster live presentations. Edit `DEMO_PUZZLES` set in the script to tailor.

## 23. Performance Guidance
- High `nodes` + low `backtracks` suggests broad but efficient exploration (perhaps domains still large).
- High `backtracks` means heuristic ordering could be improved; try `full`.
- Compare `basic` vs `full` to quantify heuristic impact for reports.
- Time dominated by constraint checks; large puzzles benefit from further pruning (e.g., future AC-3 addition).

## 24. Future Benchmark Extensions
- Parallel process pool for large puzzle suites.
- Persist intermediate stats (e.g., per-depth node counts).
- Add memory usage sampling.
- Integrate a visualization notebook rendering search progression.

---
### End
Feel free to extend heuristics, integrate AC-3, or build analytics over the CSV output. The modular breakdown aims to be both a teaching aid and a practical solver/benchmark harness.
