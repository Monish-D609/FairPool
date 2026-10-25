"""
FairPool: Trip Enumeration Engine (High-Performance Branch-and-Bound Permutations)
Enumerates candidate trips for each vehicle up to seat capacity (FR-11).
Uses subset-feasibility pruning on the shareability graph and optimized recursive stop ordering.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional
from itertools import combinations
from fairpool.core.models import (
    RiderRequest,
    DriverOffer,
    Trip,
    RouteStop,
    StopType,
)
from fairpool.core.graph import RoadNetwork
from fairpool.algorithms.shareability import ShareabilityGraph


class TripEnumerator:
    """
    Generates all admissible trips for each vehicle.
    Uses branch-and-bound recursive search to find optimal stop sequences
    without evaluating infeasible permutation prefixes.
    """

    def __init__(self, road_net: RoadNetwork, shareability_graph: ShareabilityGraph):
        self.road_net = road_net
        self.sg = shareability_graph

    def find_best_trip_for_group(
        self, offer: DriverOffer, group: List[RiderRequest]
    ) -> Optional[Trip]:
        """
        Finds the optimal stop ordering for a given group of riders in offer's vehicle.
        Uses depth-first search with pruning on capacity, time windows, and detour.
        """
        t0 = offer.departure_time
        driver_direct_time = self.road_net.travel_time_min(offer.origin_id, offer.destination_id)
        driver_solo = self.road_net.distance_km(offer.origin_id, offer.destination_id)
        riders_solo = sum(self.road_net.distance_km(r.origin_id, r.destination_id) for r in group)

        best_solution: Dict[str, Any] = {
            "dist": float('inf'),
            "manifest": None,
            "travel_time": 0.0,
            "driver_detour": 0.0,
            "rider_detours": {},
        }

        # Prepare pickups and dropoffs
        pickups = {r.id: r for r in group}
        dropoffs = {r.id: r for r in group}

        def dfs(
            curr_loc: str,
            curr_time: float,
            curr_dist: float,
            curr_occ: int,
            picked_up: Set[str],
            dropped_off: Set[str],
            pickup_times: Dict[str, float],
            manifest: List[RouteStop],
        ):
            # Prune if current distance already worse than best found
            if curr_dist >= best_solution["dist"]:
                return

            # All picked up and dropped off -> return to driver destination
            if len(dropped_off) == len(group):
                final_dist = self.road_net.distance_km(curr_loc, offer.destination_id)
                final_time = self.road_net.travel_time_min(curr_loc, offer.destination_id)
                total_dist = curr_dist + final_dist
                if total_dist >= best_solution["dist"]:
                    return

                total_time = curr_time + final_time
                d_detour = max(0.0, (total_time - t0) - driver_direct_time)
                if d_detour > offer.max_driver_detour_min:
                    return

                # Record best
                final_manifest = list(manifest) + [
                    RouteStop(
                        location_id=offer.destination_id,
                        stop_type=StopType.DRIVER_DESTINATION,
                        estimated_arrival=total_time,
                        occupancy_after_stop=0,
                    )
                ]
                # Compute rider detours
                r_detours = {}
                for r in group:
                    r_direct = self.road_net.travel_time_min(r.origin_id, r.destination_id)
                    drop_stop = next(s for s in final_manifest if s.request_id == r.id and s.stop_type == StopType.DROPOFF)
                    r_travel = drop_stop.estimated_arrival - pickup_times[r.id]
                    r_detours[r.id] = max(0.0, r_travel - r_direct)

                best_solution["dist"] = total_dist
                best_solution["manifest"] = final_manifest
                best_solution["travel_time"] = total_time - t0
                best_solution["driver_detour"] = d_detour
                best_solution["rider_detours"] = r_detours
                return

            # Option A: Try Pickups for riders not yet picked up
            if curr_occ < offer.capacity + 1:
                for rid, req in pickups.items():
                    if rid not in picked_up:
                        leg_dist = self.road_net.distance_km(curr_loc, req.origin_id)
                        leg_time = self.road_net.travel_time_min(curr_loc, req.origin_id)
                        arr_time = curr_time + leg_time
                        # Wait if arrived early
                        act_time = max(arr_time, req.earliest_departure)

                        # Detour quick check to destination
                        min_est_remaining = self.road_net.travel_time_min(req.origin_id, offer.destination_id)
                        if (act_time + min_est_remaining - t0) - driver_direct_time > offer.max_driver_detour_min:
                            continue

                        stop = RouteStop(
                            location_id=req.origin_id,
                            stop_type=StopType.PICKUP,
                            rider_id=req.rider_id,
                            request_id=req.id,
                            estimated_arrival=act_time,
                            occupancy_after_stop=curr_occ + 1,
                        )
                        pickup_times[rid] = act_time
                        picked_up.add(rid)
                        manifest.append(stop)

                        dfs(
                            req.origin_id,
                            act_time,
                            curr_dist + leg_dist,
                            curr_occ + 1,
                            picked_up,
                            dropped_off,
                            pickup_times,
                            manifest,
                        )

                        manifest.pop()
                        picked_up.remove(rid)
                        del pickup_times[rid]

            # Option B: Try Dropoffs for riders picked up but not dropped off
            for rid in list(picked_up):
                if rid not in dropped_off:
                    req = dropoffs[rid]
                    leg_dist = self.road_net.distance_km(curr_loc, req.destination_id)
                    leg_time = self.road_net.travel_time_min(curr_loc, req.destination_id)
                    arr_time = curr_time + leg_time

                    if arr_time > req.latest_arrival:
                        continue

                    r_direct = self.road_net.travel_time_min(req.origin_id, req.destination_id)
                    r_travel = arr_time - pickup_times[rid]
                    if r_travel > r_direct * (1.0 + req.max_detour_ratio):
                        continue

                    stop = RouteStop(
                        location_id=req.destination_id,
                        stop_type=StopType.DROPOFF,
                        rider_id=req.rider_id,
                        request_id=req.id,
                        estimated_arrival=arr_time,
                        occupancy_after_stop=curr_occ - 1,
                    )
                    dropped_off.add(rid)
                    manifest.append(stop)

                    dfs(
                        req.destination_id,
                        arr_time,
                        curr_dist + leg_dist,
                        curr_occ - 1,
                        picked_up,
                        dropped_off,
                        pickup_times,
                        manifest,
                    )

                    manifest.pop()
                    dropped_off.remove(rid)

        # Initial call
        initial_manifest = [
            RouteStop(
                location_id=offer.origin_id,
                stop_type=StopType.DRIVER_ORIGIN,
                estimated_arrival=t0,
                occupancy_after_stop=1,
            )
        ]
        dfs(
            offer.origin_id,
            t0,
            0.0,
            1,
            set(),
            set(),
            {},
            initial_manifest,
        )

        if best_solution["manifest"] is None:
            return None

        saved_km = (driver_solo + riders_solo) - best_solution["dist"]
        if saved_km <= 0.05:
            return None

        req_ids = [r.id for r in group]
        return Trip(
            id=f"trip_{offer.id}_{'-'.join(req_ids)}",
            offer_id=offer.id,
            driver_id=offer.driver_id,
            request_ids=req_ids,
            stops=best_solution["manifest"],
            total_travel_time=best_solution["travel_time"],
            total_distance_km=best_solution["dist"],
            solo_driver_distance_km=driver_solo,
            saved_distance_km=saved_km,
            driver_detour_min=best_solution["driver_detour"],
            rider_detours_min=best_solution["rider_detours"],
        )

    def enumerate_candidate_trips(
        self, requests: List[RiderRequest], offers: List[DriverOffer], max_capacity_cap: int = 4
    ) -> List[Trip]:
        """
        Enumerates all candidate trips across all vehicles up to vehicle capacity.
        Applies subset-feasibility pruning using the shareability graph.
        """
        req_by_id = {r.id: r for r in requests}
        all_candidate_trips: List[Trip] = []

        for offer in offers:
            cand_requests = list(self.sg.vehicle_request_edges.get(offer.id, set()))
            if not cand_requests:
                continue

            eff_cap = min(offer.capacity, max_capacity_cap)

            # 1. Size 1 trips
            for r_id in cand_requests:
                trip = self.find_best_trip_for_group(offer, [req_by_id[r_id]])
                if trip:
                    all_candidate_trips.append(trip)

            # 2. Size 2 trips (from shareability pair edges)
            pair_edges = self.sg.vehicle_pair_edges.get(offer.id, set())
            for pair in pair_edges:
                r1_id, r2_id = list(pair)
                trip = self.find_best_trip_for_group(offer, [req_by_id[r1_id], req_by_id[r2_id]])
                if trip:
                    all_candidate_trips.append(trip)

            # 3. Size 3 trips (pruned: all 3 sub-pairs must be feasible)
            if eff_cap >= 3 and len(cand_requests) >= 3:
                for triplet in combinations(cand_requests, 3):
                    p1 = frozenset([triplet[0], triplet[1]])
                    p2 = frozenset([triplet[1], triplet[2]])
                    p3 = frozenset([triplet[0], triplet[2]])
                    if p1 in pair_edges and p2 in pair_edges and p3 in pair_edges:
                        group = [req_by_id[r_id] for r_id in triplet]
                        trip = self.find_best_trip_for_group(offer, group)
                        if trip:
                            all_candidate_trips.append(trip)

            # 4. Size 4 trips (pruned: all sub-triplets feasible)
            if eff_cap >= 4 and len(cand_requests) >= 4:
                for quad in combinations(cand_requests, 4):
                    sub_triplets_valid = True
                    for triplet in combinations(quad, 3):
                        p1 = frozenset([triplet[0], triplet[1]])
                        p2 = frozenset([triplet[1], triplet[2]])
                        p3 = frozenset([triplet[0], triplet[2]])
                        if not (p1 in pair_edges and p2 in pair_edges and p3 in pair_edges):
                            sub_triplets_valid = False
                            break
                    if sub_triplets_valid:
                        group = [req_by_id[r_id] for r_id in quad]
                        trip = self.find_best_trip_for_group(offer, group)
                        if trip:
                            all_candidate_trips.append(trip)

        return all_candidate_trips
