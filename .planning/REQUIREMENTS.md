# FairPool Requirements Traceability

## Functional Requirements
- **FR-1:** Institutional Domain Verification (campus/corporate email verification).
- **FR-2:** Account Activation & Role Management (Rider, Driver, Coordinator).
- **FR-3:** Coordinator Governance (user status control, aggregate safety metrics).
- **FR-4:** Rider Request Submission (Origin, Destination, Earliest Departure, Latest Arrival, Max Detour %).
- **FR-5:** Driver Offer Submission (Origin, Destination, Departure Time, Seat Capacity, Max Driver Detour).
- **FR-6:** Request & Offer Lifecycle (Pending, Matched, Dispatched, Cancelled, Rollover).
- **FR-7:** Privacy Protection (Approximate pickup locations, hidden exact private coordinates).
- **FR-8:** Configurable Batch Matching Windows (collect & solve in batched epochs).
- **FR-9:** Travel Time & Road Network Metric Engine ($t(a, b)$ over road network).
- **FR-10:** Shareability Graph Construction (pairwise temporal & spatial feasibility checks).
- **FR-11:** Pruned Trip Enumeration (feasible pickup/drop-off permutations up to vehicle capacity).
- **FR-12:** Set Packing Assignment Solver (Exact ILP/Branch-and-Bound + High-Speed Greedy Approximation).
- **FR-13:** Dynamic Fairness Balancing (cumulative detour tracking, Gini index minimization, load rotation).
- **FR-14:** Graceful Unmatched Fallback (rollover to adjacent time windows).
- **FR-15:** Dynamic Cancellation Re-planning (isolated re-routing of affected trips).
- **FR-16:** Batch Timeout & Real-Time Guarantees (returns best feasible solution within strict budget).
- **FR-17:** Trip Manifest & Match Confirmation (detailed pickup sequence, estimated arrival times).
- **FR-18:** Driver Trip Confirmation & Feedback Loop.
- **FR-19:** Coordinator Operations & Analytics Dashboard (real-time KPIs, savings metrics, fairness radar).
- **FR-20:** Anonymized CSV Dataset Export.
- **FR-21:** Batch Simulation & Replay Engine.
- **FR-22:** Multi-Algorithm Comparison Suite (No-Pooling, Greedy Nearest-Pair, FairPool).
- **FR-23:** Scientific Metric Reporting (Vehicle-km saved, mean/P90 detour, match rate, Gini coefficient, runtime).
- **FR-24:** One-Command Deterministic Benchmark (fixed seed reproducibility).
- **FR-25:** Fairness Ablation Study Mode.

## Non-Functional Requirements
- **NFR-1:** Performance: 200 requests matched within 10 seconds via approximate solver.
- **NFR-2:** Responsiveness: Flawless mobile & desktop presentation without horizontal scrolling.
- **NFR-3:** Data Security & Privacy: No leak of home addresses; org-scoped access.
- **NFR-4:** Reproducibility: Deterministic benchmarking from CLI and Web UI.
- **NFR-5:** Code Quality & Test Coverage: Full unit & property tests for graph algorithms and assignment solvers.
