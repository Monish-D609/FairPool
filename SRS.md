# Software Requirements Specification (SRS)

**Product:** FairPool (working title)
**Document:** SRS v1.0
**Related documents:** URS.md (user needs), PRD.md (product goals and scope)

---

## 1. Introduction

### 1.1 Purpose
This SRS specifies the functional and non-functional requirements of FairPool, a web system that matches riders and drivers into shared rides for a campus or office.

### 1.2 Scope
FairPool accepts ride requests and offers, computes shared-ride assignments in batches, enforces per-user detour and waiting limits plus a fairness rule, and reports aggregate results. It also includes a simulator and benchmark harness used to compare algorithms.

### 1.3 Definitions

| Term | Meaning |
|------|---------|
| Request | A rider's wish to travel from an origin to a destination within a time window |
| Offer | A driver's trip with a route, departure time and free seats |
| Trip | A set of requests served in sequence by one vehicle |
| Batch window | Fixed interval during which requests are collected before matching |
| Shareability graph | Graph whose nodes are requests and vehicles, with edges where sharing is feasible |
| Detour | Extra travel time for a person compared with travelling directly |

## 2. Overall description

### 2.1 Product perspective
Standalone web application with a backend matching service, a database, and a road-network routing component. It uses OpenStreetMap data.

### 2.2 User classes
Rider, Driver, Coordinator (see URS.md section 3).

### 2.3 Operating environment
- Browser: current mobile and desktop browsers.
- Backend: a Linux server or container platform.
- No native app.

### 2.4 Assumptions and dependencies
- A road-network extract for the pilot area is available.
- Users have a smartphone with a browser.
- A routing engine or local graph library supplies travel times.

### 2.5 Constraints
- One campus or office cluster; not designed for city-scale demand in the first release.
- Zero monetary cost to pilot users.

## 3. Functional requirements

Each requirement is tagged with the user need it satisfies.

### 3.1 Accounts and access

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-1 | The system shall allow sign-up only with an email address in an allowed organisation domain. | UR-C2, UR-T1 |
| FR-2 | The system shall verify the email before the account can create requests or offers. | UR-T1 |
| FR-3 | A coordinator shall be able to suspend or reinstate a user. | UR-C4 |

### 3.2 Requests and offers

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-4 | A rider shall be able to submit a request with origin, destination, earliest departure, latest arrival and maximum accepted detour percentage. | UR-R1, UR-R3 |
| FR-5 | A driver shall be able to submit an offer with origin, destination, departure time, free seats and maximum accepted detour. | UR-D1, UR-D2 |
| FR-6 | The system shall let users cancel a pending or matched request or offer. | UR-R4 |
| FR-7 | The system shall store exact locations privately and expose only approximate or agreed pickup points to other users. | UR-T2 |

### 3.3 Matching engine

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-8 | The engine shall collect requests and offers during a configurable batch window and process them together. | UR-R2 |
| FR-9 | The engine shall compute travel times between all relevant points from the road-network graph. | UR-R3 |
| FR-10 | The engine shall build a shareability graph linking requests that can be served in the same vehicle without violating any rider's time window or detour limit. | UR-R3, UR-D2 |
| FR-11 | The engine shall enumerate feasible trips for each vehicle up to its seat capacity, with a pickup and drop-off order. | UR-D3 |
| FR-12 | The engine shall select an assignment of trips to vehicles that maximises total vehicle-distance savings, such that each request is in at most one trip and each vehicle has at most one trip. | UR-C1 |
| FR-13 | The engine shall apply a fairness rule: no driver's cumulative detour over a rolling period shall exceed a configurable multiple of the group average, and ties shall prefer the driver with the lowest cumulative detour. | UR-D4 |
| FR-14 | Requests that cannot be pooled shall be marked unmatched, and the user shall be offered the nearest alternative time window if one exists. | Section 6 of URS |
| FR-15 | On cancellation, the engine shall re-plan only the affected trips where possible, without changing confirmed trips for other users unless they consent. | UR-R4 |
| FR-16 | The engine shall enforce a configurable time limit per batch and return the best assignment found if the limit is reached. | NFR-1 |

### 3.4 User interface

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-17 | The system shall show a matched user their pickup time, pickup order, and co-rider display names. | UR-R2, UR-R5, UR-D3 |
| FR-18 | The driver shall confirm or decline a proposed trip; a decline shall return the riders to the next batch. | UR-D3 |
| FR-19 | The system shall provide a coordinator dashboard showing trips shared, vehicle-km saved, mean and 90th-percentile detour, match rate, and fairness spread. | UR-C1 |
| FR-20 | The system shall let a coordinator export anonymised aggregate data as CSV. | UR-C3 |

### 3.5 Simulator and benchmark

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-21 | The simulator shall replay a dataset of requests and offers through each configured algorithm. | UR-E2 |
| FR-22 | The harness shall implement at least three methods: no pooling, greedy nearest-pair matching, and the FairPool engine. | UR-E2 |
| FR-23 | The harness shall report for each method: vehicle-km, mean and 90th-percentile detour, match rate, fairness spread, and runtime per batch. | UR-E2 |
| FR-24 | A single command shall reproduce all benchmark tables from a fixed random seed. | UR-E1, UR-E2 |
| FR-25 | The harness shall support an ablation run with the fairness rule disabled. | UR-E4 |

## 4. Algorithm specification

### 4.1 Inputs
A batch of requests R, a set of vehicles V (from offers), a road graph G with travel-time function t(a, b), and per-user limits.

### 4.2 Steps
1. **Travel times.** Precompute or query t(a, b) for all origin and destination points in the batch.
2. **Pairwise feasibility.** For each request pair (r1, r2) and each vehicle, test whether serving both in some order meets all time windows and detour limits. Add an edge if so.
3. **Trip enumeration.** For each vehicle, extend feasible single-request trips to pairs, then to larger sets up to the vehicle's capacity, keeping only sets whose every subset is feasible. For each set, find the best pickup and drop-off order by search over valid orderings (small capacity keeps this tractable).
4. **Assignment.** Choose trips to maximise total savings subject to each request and each vehicle being used at most once. Implement two solvers: an exact integer linear program for small batches and a greedy or local-search approximation for large batches.
5. **Fairness adjustment.** Incorporate cumulative detour into the objective or constraints as in FR-13.
6. **Commit and rollover.** Confirm accepted trips; carry unmatched requests into the next batch until their time window expires.

### 4.3 Complexity notes (to be analysed in the report)
- Step 2 is quadratic in the number of requests per vehicle.
- Step 3 grows quickly with vehicle capacity, so capacity is capped (for example, 4) and enumeration is pruned using the subset-feasibility rule.
- Step 4 is NP-hard in general (set packing), which is why the approximation solver exists; the report shall state this and compare solution quality and runtime of both solvers.

## 5. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | A batch of up to 200 requests shall be matched within a configurable limit (default 10 seconds) using the approximate solver. |
| NFR-2 | The web interface shall be usable on a phone screen without horizontal scrolling. |
| NFR-3 | Personal data (email, exact locations) shall be stored encrypted at rest or in a protected database, and transmitted over HTTPS. |
| NFR-4 | The system shall not display other users' exact home addresses. |
| NFR-5 | All matching decisions shall be logged with inputs and outputs so that results are reproducible for the benchmark and auditable. |
| NFR-6 | The system shall be deployed at a public URL for the duration of the evaluation. |
| NFR-7 | The code shall have automated tests for feasibility checking and assignment constraints. |
| NFR-8 | The benchmark shall be reproducible from the repository by following the README. |

## 6. External interfaces

- **User interface:** responsive web pages for riders, drivers and coordinators.
- **Routing data:** OpenStreetMap extract and a local routing library or engine.
- **Database:** relational database for users, requests, offers, trips and logs.
- **Email service:** sends verification and notification emails.
- **Optional map display:** an open-source map tile source for showing pickup points.

## 7. Data model (outline)

| Entity | Key fields |
|--------|------------|
| User | id, org email, role flags, display name, status, cumulative detour |
| Request | id, rider id, origin, destination, earliest departure, latest arrival, max detour %, status |
| Offer | id, driver id, origin, destination, departure time, seats, max detour, status |
| Trip | id, offer id, ordered stops, request ids, planned times, savings |
| BatchLog | id, window start and end, input snapshot, algorithm version, output |

## 8. Verification

| Area | Method |
|------|--------|
| Feasibility checks (FR-10, FR-11) | Unit tests with hand-built cases where the correct answer is known |
| Assignment validity (FR-12) | Property tests: no request or vehicle used twice, all limits respected |
| Fairness (FR-13) | Ablation run comparing detour spread with and without the rule |
| Performance (NFR-1) | Timing tests on synthetic batches of 50, 100 and 200 requests |
| Benchmark (FR-21 to FR-25) | Re-run from a fixed seed and compare output tables |
| User needs | Pilot survey against the M-priority needs in URS.md |

## 9. Traceability

Every functional requirement above lists the user need it satisfies. Every M-priority user need in URS.md is covered by at least one functional requirement and one verification step.

## 10. Open items

1. Choice of routing engine (local graph library vs hosted engine).
2. Exact fairness metric and threshold, to be set after baseline data exists.
3. Vehicle capacity cap and batch window length for the pilot.
