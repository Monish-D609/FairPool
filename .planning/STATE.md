# FairPool Project Memory State

## Current Position
- **Active Phase:** Phase 1 (Algorithmic Foundation & Baselines) & Phase 2 (Shareability Graph & Set Packing Solvers).
- **Git Remote:** `https://github.com/Monish-D609/FairPool` (branch: `main`).
- **Core Technology:** Python 3.12 (Algorithmic Core, FastAPI backend, Benchmark CLI) + Modern Vanilla JS/CSS (Bento Box Dark Mode Web Dashboard).

## Key Decisions Made
1. **Algorithmic Modeling:** Graph-theoretic formulation following Santi et al. (Shareability Graph) + Alonso-Mora et al. (Trip-Vehicle Assignment) combined with our novel Dynamic Cumulative Fairness constraint.
2. **Deterministic Reproducibility:** Benchmarks use fixed seeds to allow 100% reproducible scientific comparisons against baselines.
3. **Dual Solvers:** Exact solver for optimal verification + Greedy/Local Search solver for NFR-1 scale (200 requests < 10 seconds).
4. **UI Design Standard:** Built with `ui-ux-pro-max` - Bento Box Grid, Slate-Navy dark theme, emerald green fairness indicators, electric blue routes, Outfit + DM Sans typography.

## Next Immediate Steps
1. Implement the core Python package:
   - `fairpool/core/graph.py` (Road network, Dijkstra, Haversine, distance matrix).
   - `fairpool/core/models.py` (Rider requests, Driver offers, Trips, Match results).
   - `fairpool/algorithms/baselines.py` (No-pooling baseline and Greedy Nearest-Pair baseline).
   - `fairpool/algorithms/shareability.py` (Temporal & spatial pairwise feasibility graph).
   - `fairpool/algorithms/enumeration.py` (Trip permutation generator with precedence constraints).
   - `fairpool/algorithms/solver.py` (Set packing exact & greedy approximation solvers).
   - `fairpool/algorithms/fairness.py` (Dynamic fairness engine, Gini coefficient, cumulative tracking).
2. Commit and push each modular step to GitHub!
