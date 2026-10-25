# FairPool Development Roadmap

## Phase 1: Algorithmic Foundation & Baselines [COMPLETED]
- [x] Road network & travel time engine with Dijkstra / geodesic distance matrix.
- [x] Commuter request & driver offer data models with temporal window constraints.
- [x] Baseline 1: Solo Travel / No-Pooling benchmark.
- [x] Baseline 2: Greedy Nearest-Pair heuristic matcher.
- [x] Verification tests for baseline models.

## Phase 2: Shareability Graph & Set Packing Solvers [IN PROGRESS]
- [ ] Pairwise shareability graph construction with temporal/spatial pruning.
- [ ] Capacity-constrained ($k \le 4$) trip permutation generator with precedence constraints.
- [ ] Exact Set-Packing Assignment Solver (Branch & Bound / ILP).
- [ ] High-Speed Greedy/Local Search Approximation Solver for 200+ request batches.
- [ ] Unit & integration test coverage for matching correctness.

## Phase 3: Dynamic Fairness Engine & Ablation Study
- [ ] Rolling cumulative driver detour tracker.
- [ ] Fairness-aware objective function (Gini coefficient minimization & variance penalty).
- [ ] Fairness ablation harness (comparing FairPool with vs without fairness constraints).
- [ ] Tie-breaking heuristic for driver burden rotation.

## Phase 4: Deterministic Benchmark Harness & Simulation Engine
- [ ] Commute peak distribution synthetic request generator (morning/evening rush hours).
- [ ] One-command reproducible benchmark runner (`fairpool benchmark --seed 42`).
- [ ] Metric generation: vehicle-km saved, mean/P90 detour, match rate, Gini coefficient, runtime.
- [ ] Exportable benchmark reports (CSV, JSON, Markdown).

## Phase 5: Production Web Application & UI/UX Experience
- [ ] Sleek Bento Box Dark Theme UI (`ui-ux-pro-max` standard).
- [ ] Interactive live simulation visualizer: road network, nodes, vehicle routes, and stop sequences.
- [ ] Rider Portal: ride request submission, detour preview, match status.
- [ ] Driver Portal: offer submission, manifest review, confirmation.
- [ ] Coordinator Operations Dashboard: live KPIs, emissions avoided, fairness spread, algorithm comparison charts.
- [ ] REST API backend serving real-time requests, matching batches, and simulator runs.

## Phase 6: Pilot Deployment, Documentation & Git Sync
- [ ] Fast, zero-dependency local dev server and runner.
- [ ] Full project documentation (README, algorithmic complexity analysis, DAA viva guide).
- [ ] Complete git push sync to `https://github.com/Monish-D609/FairPool`.
