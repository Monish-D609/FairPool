# FairPool Development Roadmap

## Phase 1: Algorithmic Foundation & Baselines [COMPLETED]
- [x] Road network & travel time engine with Dijkstra / geodesic distance matrix.
- [x] Commuter request & driver offer data models with temporal window constraints.
- [x] Baseline 1: Solo Travel / No-Pooling benchmark.
- [x] Baseline 2: Greedy Nearest-Pair heuristic matcher.
- [x] Verification tests for baseline models.

## Phase 2: Shareability Graph & Set Packing Solvers [COMPLETED]
- [x] Pairwise shareability graph construction with temporal/spatial pruning.
- [x] Capacity-constrained ($k \le 4$) trip permutation generator with precedence constraints.
- [x] Exact Set-Packing Assignment Solver (MILP branch-and-cut).
- [x] High-Speed Greedy/Local Search Approximation Solver for 200+ request batches.
- [x] Unit & integration test coverage for matching correctness.

## Phase 3: Dynamic Fairness Engine & Ablation Study [COMPLETED]
- [x] Rolling cumulative driver detour tracker.
- [x] Fairness-aware objective function (Gini coefficient minimization & variance penalty).
- [x] Fairness ablation harness (comparing FairPool with vs without fairness constraints).
- [x] Tie-breaking heuristic for driver burden rotation.

## Phase 4: Deterministic Benchmark Harness & Simulation Engine [COMPLETED]
- [x] Commute peak distribution synthetic request generator (morning/evening rush hours).
- [x] One-command reproducible benchmark runner (`python run.py --benchmark`).
- [x] Metric generation: vehicle-km saved, mean/P90 detour, match rate, Gini coefficient, runtime.
- [x] Exportable benchmark reports (Markdown, JSON, Table).

## Phase 5: Production Web Application & UI/UX Experience [COMPLETED]
- [x] Sleek Bento Box Dark Theme UI (`ui-ux-pro-max` standard).
- [x] Interactive live simulation visualizer: road network, nodes, vehicle routes, and stop sequences.
- [x] Rider Portal: ride request submission, detour preview, match status.
- [x] Driver Portal: offer submission, manifest review, confirmation.
- [x] Coordinator Operations Dashboard: live KPIs, emissions avoided, fairness spread, algorithm comparison charts.
- [x] REST API backend serving real-time requests, matching batches, and simulator runs.

## Phase 6: Pilot Deployment, Documentation & Git Sync [COMPLETED]
- [x] Fast, zero-dependency local dev server and runner (`run.py`).
- [x] Full project documentation (README, algorithmic complexity analysis, DAA viva guide).
- [x] Complete git push sync to `https://github.com/Monish-D609/FairPool`.
