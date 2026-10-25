# User Requirements Specification (URS)

**Project:** FairPool (working title): fair ride-pooling and carpool matching for campuses and offices
**Document:** URS v1.0
**Context:** Open innovation project, Algorithms course

---

## 1. Purpose

This document records what the people who will use or be affected by FairPool need from it, in their own terms. It does not describe how the system is built; that is covered in SRS.md. Product goals and scope are in PRD.md.

## 2. Background

People who travel to the same campus or workplace from nearby areas often drive or ride alone. Informal carpool groups (chat groups, notice boards) are hard to coordinate, and they tend to favour whoever organises them. FairPool matches riders and drivers automatically, keeps detours and waiting within each person's limits, and spreads the inconvenience of sharing fairly.

## 3. Stakeholders and user groups

| ID | Group | Description | Main interest |
|----|-------|-------------|---------------|
| S1 | Rider | Student or employee who needs a lift | Low cost, short wait, predictable pickup |
| S2 | Driver | Student or employee with a car or bike seat | Small detour, reliable co-riders, fair reward |
| S3 | Coordinator / Admin | Campus transport office, department or HR contact | Fewer vehicles, visibility into usage, safety |
| S4 | Evaluator | Course instructor | Verifiable real-world outcome and algorithmic depth |

## 4. User needs

Priority: **M** = must have, **S** = should have, **C** = could have.

### 4.1 Riders

| ID | Need | Priority |
|----|------|----------|
| UR-R1 | I can request a ride by entering my pickup point, destination and time window. | M |
| UR-R2 | I am told my assigned pickup time and vehicle before I leave. | M |
| UR-R3 | My total trip time never exceeds a limit I set (for example, 20% longer than a direct trip). | M |
| UR-R4 | I can cancel a request, and the system re-plans without penalising others unfairly. | M |
| UR-R5 | I can see who I am riding with (name and rating only) before confirming. | S |
| UR-R6 | I can request a recurring ride (for example, every weekday morning). | S |
| UR-R7 | I can see how much money and time I saved compared with riding alone. | C |

### 4.2 Drivers

| ID | Need | Priority |
|----|------|----------|
| UR-D1 | I can offer a trip with my route, departure time and number of free seats. | M |
| UR-D2 | I set the maximum detour I will accept. | M |
| UR-D3 | I am shown the full pickup order and expected arrival time before accepting. | M |
| UR-D4 | I am not given the longest detours every time; the load is shared across drivers over time. | M |
| UR-D5 | I can see my contribution (trips given, distance shared, estimated emissions avoided). | C |

### 4.3 Coordinators

| ID | Need | Priority |
|----|------|----------|
| UR-C1 | I can see aggregate usage: trips shared, vehicle-km saved, average detour and wait. | M |
| UR-C2 | I can restrict participation to verified members of my organisation. | M |
| UR-C3 | I can export anonymised data for reporting. | S |
| UR-C4 | I can disable or suspend a user who misbehaves. | S |

### 4.4 Evaluator

| ID | Need | Priority |
|----|------|----------|
| UR-E1 | A live, working deployment I can open and try. | M |
| UR-E2 | A reproducible benchmark showing the algorithm beats simple baselines on the same data. | M |
| UR-E3 | Evidence from real users in a pilot, not only simulation. | M |
| UR-E4 | Clear explanation of the algorithms used, their complexity and their limits. | M |

## 5. Trust, safety and privacy needs

| ID | Need | Priority |
|----|------|----------|
| UR-T1 | Only verified members of my organisation can see or join my trips. | M |
| UR-T2 | My exact home address is not shown to other users; only an approximate or agreed pickup point is shared. | M |
| UR-T3 | I can report a problem with a trip. | S |
| UR-T4 | My data is not sold or shared outside the organisation. | M |

## 6. Constraints stated by users

- The service must work on a phone browser without installing an app.
- Pilot users will not tolerate frequent failed matches; a ride that cannot be pooled should fall back to a clear "no match" message with an alternative time suggestion.
- Cost to users must be zero for the pilot.

## 7. Acceptance of user needs

A user need is considered satisfied when the corresponding requirement in SRS.md passes its verification step and, for all **M** needs, at least three pilot users confirm it in a short feedback survey.

## 8. Open questions

1. Which organisation (campus, department or workplace) will host the pilot?
2. Will drivers be rewarded in money, credits or not at all in the pilot?
3. What verification method is acceptable (organisation email domain, ID number)?
