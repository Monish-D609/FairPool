# Product Requirements Document (PRD)

**Product:** FairPool (working title)
**Tagline:** Fair, optimised carpool matching for campuses and offices
**Document:** PRD v1.0

---

## 1. Summary

FairPool is a web application that groups people travelling to and from the same campus or workplace into shared rides. A batched matching engine decides who rides with whom and in what pickup order, subject to each person's detour and waiting limits, while spreading the inconvenience fairly across users over time. The project is evaluated on actual outcome, so the product is designed around a live pilot and a reproducible benchmark.

## 2. Problem

- Many commuters to the same destination travel alone, which wastes seats, fuel and money.
- Informal carpooling (chat groups, notice boards) does not scale, and the same few people end up absorbing detours.
- Existing maps and routing tools find the best route for one person. They do not decide how a group of people should be split across vehicles.

## 3. Goals

| ID | Goal | Measure |
|----|------|---------|
| G1 | Reduce total vehicle distance for the same set of riders | Vehicle-km saved against the no-pooling baseline |
| G2 | Keep individual inconvenience bounded | Percent of trips within each user's detour and wait limits |
| G3 | Distribute detours fairly | Spread of detour time across drivers (for example, Gini coefficient or max-min ratio) |
| G4 | Beat simple matching | Higher total savings than greedy nearest-pair matching on identical requests |
| G5 | Prove real-world use | A live pilot with real users and recorded results |

Numeric targets for G1 to G5 are set after the first baseline run (see section 10), so they reflect real data rather than guesses.

## 4. Non-goals

- Replacing public transit or building a commercial ride-hailing service.
- Payments, billing or driver payouts.
- Native mobile apps.
- Real-time live vehicle tracking for the first release.
- City-wide scale; the target is one campus or office cluster.

## 5. Target users

| Persona | Description |
|---------|-------------|
| Rider | Student or employee without a vehicle who wants a cheap, predictable commute |
| Driver | Student or employee with a car or bike who has spare seats |
| Coordinator | Campus or organisation contact who wants visibility and control |

See URS.md for detailed needs.

## 6. Scope and features

### 6.1 MVP (must ship for the pilot)

1. **Verified sign-up** limited to an organisation (email domain check).
2. **Ride requests and offers** with origin, destination, time window, seats, and detour or wait limits.
3. **Batched matching engine** that runs on a fixed time window, builds a feasibility graph and assigns trips.
4. **Fairness constraint** capping per-user detour and tracking cumulative burden so it is rotated across drivers.
5. **Match confirmation view** showing pickup order and times.
6. **Cancellation and re-matching.**
7. **Coordinator dashboard** with aggregate metrics.
8. **Simulator and benchmark harness** that replays request datasets against several algorithms.

### 6.2 Later (if time allows)

- Recurring rides.
- Rider and driver ratings.
- Saved savings summary (money, time, emissions estimate).
- Anonymised data export.

## 7. The algorithmic core (summary)

The detailed specification is in SRS.md. In short:

1. Compute travel times between points from a road-network graph.
2. Build a shareability graph: which requests can be served together within their limits.
3. Enumerate feasible trips per vehicle up to its capacity.
4. Solve an assignment (integer program or an approximation) that maximises total savings subject to fairness constraints.
5. Re-run each batch window, handling new, cancelled and unmatched requests.

Baselines for comparison: no pooling, greedy nearest-pair matching, and first-come-first-served insertion.

## 8. Success metrics

**Algorithm (simulation, same data for every method)**

- Vehicle-km saved
- Mean and 90th-percentile detour per rider
- Match rate (percent of requests pooled)
- Fairness spread across drivers
- Runtime per batch window

**Real world (pilot)**

- Number of real users and completed shared trips
- Vehicle-km saved in the pilot
- User satisfaction from a short survey
- Repeat usage over the pilot period

## 9. Data

- **Road network:** OpenStreetMap extract for the pilot area.
- **Requests for benchmarking:** (a) real pilot requests, (b) anonymised or synthetic requests generated to mimic commute patterns (shared morning and evening peaks), and (c) a public mobility dataset if one fits.
- **Privacy:** store approximate locations where possible, no sharing of exact home addresses between users, and anonymise anything exported.

## 10. Plan

| Phase | Output |
|-------|--------|
| 1. Setup | Road graph, data model, baseline greedy matcher, simulator |
| 2. Core algorithm | Shareability graph, trip enumeration, assignment solver, first benchmark |
| 3. Fairness | Fairness constraint, ablation study (with and without) |
| 4. Product | Web app, verification, request and match flow, dashboard |
| 5. Pilot | Real users, data collection, survey |
| 6. Report | Final benchmark, pilot results, complexity analysis, writeup |

Targets for goals G1 to G5 are fixed at the end of phase 2, once the baseline numbers exist.

## 11. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Too few pilot users for pooling to happen | Recruit one defined group (a department or hostel block) with similar destinations; also report simulation at larger scale |
| The project looks like a routing wrapper | Make matching quality against baselines the headline result |
| Matching is too slow | Limit batch size, cap trip size, use the approximate solver |
| Privacy concerns block adoption | Organisation-only access, approximate pickup points, clear data policy |
| Existing patents on parts of the published method | Use for the course; note the patents in the report; check before any commercial use |

## 12. Deliverables for evaluation

1. Live deployment link.
2. Public repository with README and one-command benchmark.
3. Benchmark report with tables comparing all methods.
4. Pilot results summary.
5. Algorithm writeup with complexity analysis.
