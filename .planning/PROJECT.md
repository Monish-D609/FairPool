# FairPool: Fair, Optimised Carpool Matching Engine

## 1. Executive Overview
FairPool is an algorithmic ride-pooling and carpool matching platform engineered for university campuses and corporate workplaces. It solves the inefficiency of single-occupancy vehicle commutes and the unfairness of ad-hoc carpooling where the same drivers absorb excessive detour burdens.

Unlike single-vehicle navigation or greedy pairwise ride-hailing heuristics, FairPool formulates ride-sharing as a multi-stage combinatorial optimization problem:
1. Building time-windowed **Shareability Graphs** over road networks.
2. Enumerating admissible trips with precedence-constrained pickup and drop-off sequences.
3. Solving a **Fairness-Constrained Set Packing Assignment** using exact and high-speed heuristic solvers.
4. Dynamically rebalancing cumulative driver detours over rolling epochs to ensure equitable burden distribution (minimizing Gini coefficient of detour disparity).

## 2. Core Value Proposition & Pain Point
- **Pain Point:** Commuters suffer high fuel and travel costs, congestion, and parking crunches. Existing apps focus on 1-to-1 routing or commercial taxi dispatch without equitable driver detour rotation. In informal campus carpools, altruistic drivers suffer disproportionate detours, leading to carpool collapse.
- **FairPool Solution:** Provides mathematically bounded detours for riders ($\le \delta_i$), guarantees maximum vehicle capacity $C_v$, maximizes total vehicle-kilometers saved, and enforces dynamic fairness rotation across participating drivers.

## 3. Algorithmic Stack
- **Graph & Travel Times:** Network graph $G = (V, E)$ with travel time metric $t(u, v)$ (Dijkstra / all-pairs shortest paths / Haversine distance network).
- **Shareability Graph:** Pairwise feasibility verification over temporal windows $[e_i, l_i]$ and maximum detour limits.
- **Trip Enumeration:** Subgraph clique enumeration up to capacity $C \le 4$, evaluating valid pickup-dropoff permutations $(2k)! / 2^k$ with subset pruning.
- **Assignment Engine:** Set Packing Optimization:
  - Exact Branch-and-Bound / Integer Linear Program for optimal benchmark evaluation.
  - Greedy / Local Search heuristic achieving $< 10$ ms execution on 200+ request batches.
- **Fairness Controller:** Cumulative detour tracking, variance bounds, and multi-objective penalty weights.
- **Baselines & Benchmark Harness:** Side-by-side comparison with No-Pooling, Greedy Nearest-Pair, and Fairness-Ablated models across synthetic and empirical campus commute distributions.

## 4. UI/UX Architecture
- Follows `ui-ux-pro-max` guidelines:
  - Bento Box Grid + Data-Dense Operations Dashboard.
  - Dark Slate-Navy palette (`#0F172A`, `#1E293B`, `#2563EB`, `#10B981`).
  - Google Fonts: `Outfit` (headings) + `DM Sans` (body) + `Fira Code` (metrics & computational matrices).
  - Interactive Map / Node Visualizer showing vehicle trajectories, pickup sequences, and real-time detour metrics.
  - Interactive Replay & Benchmark Inspector.
