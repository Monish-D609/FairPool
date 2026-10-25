"""
FairPool: Trip Enumeration Engine
Enumerates candidate trips for each vehicle up to seat capacity (FR-11).
Uses subset-feasibility pruning on the shareability graph and optimizes stop sequences.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple, Optional
from itertools import combinations, permutations
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
    For small groups (1 to 4 riders), finds the optimal stop sequence
    that minimizes detour while respecting all passenger and driver constraints.
    """

    def __init__(self, road_net: RoadNetwork, shareability_graph: ShareabilityGraph):
        self.road_net = road_net
        self.sg = shareability_graph

    def _evaluate_stop_sequence(
        self,
        offer: DriverOffer,
        requests: List[RiderRequest],
        perm_stops: List[Tuple[str, str, RiderRequest, StopType]]
    ) -> Optional[Tuple[List[RouteStop], float, float, float, Dict[str, float]]]:
        """
        Evaluates a concrete sequence of stops.
        Returns:
            (stops_manifest, total_travel_time, total_distance_km, driver_detour_min, rider_detours_dict)
            or None if infeasible.
        """
        t0 = offer.departure_time
        curr_time = t0
        curr_loc = offer.origin_id
        curr_occ = 1  # driver

        stops_manifest: List[RouteStop] = [
            RouteStop(
                location_id=offer.origin_id,
                stop_type=StopType.DRIVER_ORIGIN,
                estimated_arrival=t0,
                occupancy_after_stop=1,
            )
        ]

        total_distance = 0.0
        rider_pickup_time: Dict[str, float] = {}
        rider_detours: Dict[str, float] = {}

        for _, loc_id, req, stype in perm_stops:
            leg_dist = self.road_net.distance_km(curr_loc, loc_id)
            leg_time = self.road_net.travel_time_min(curr_loc, loc_id)

            total_distance += leg_dist
            curr_time += leg_time
            curr_loc = loc_id

            if stype == StopType.PICKUP:
                curr_occ += 1
                if curr_occ > offer.capacity + 1:
                    return None
                # If arriving before earliest departure, wait
                if curr_time < req.earliest_departure:
                    curr_time = req.earliest_departure
                rider_pickup_time[req.id] = curr_time

                stops_manifest.append(
                    RouteStop(
                        location_id=loc_id,
                        stop_type=StopType.PICKUP,
                        rider_id=req.rider_id,
                        request_id=req.id,
                        estimated_arrival=curr_time,
                        occupancy_after_stop=curr_occ,
                    )
                )

            elif stype == StopType.DROPOFF:
                curr_occ -= 1
                if curr_time > req.latest_arrival:
                    return None
                r_direct_time = self.road_net.travel_time_min(req.origin_id, req.destination_id)
                r_travel_time = curr_time - rider_pickup_time[req.id]
                if r_travel_time > r_direct_time * (1.0 + req.max_detour_ratio):
                    return None
                rider_detours[req.id] = max(0.0, r_travel_time - r_direct_time)

                stops_manifest.append(
                    RouteStop(
                        location_id=loc_id,
                        stop_type=StopType.DROPOFF,
                        rider_id=req.rider_id,
                        request_id=req.id,
                        estimated_arrival=curr_time,
                        occupancy_after_stop=curr_occ,
                    )
                )

        # Final leg to driver's destination
        final_dist = self.road_net.distance_km(curr_loc, offer.destination_id)
        final_time = self.road_net.travel_time_min(curr_loc, offer.destination_id)
        total_distance += final_dist
        curr_time += final_time

        driver_direct_time = self.road_net.travel_time_min(offer.origin_id, offer.destination_id)
        driver_detour = max(0.0, (curr_time - t0) - driver_direct_time)

        if driver_detour > offer.max_driver_detour_min:
            return None

        stops_manifest.append(
            RouteStop(
                location_id=offer.destination_id,
                stop_type=StopType.DRIVER_DESTINATION,
                estimated_arrival=curr_time,
                occupancy_after_stop=0,
            )
        )

        total_travel_time = curr_time - t0
        return (stops_manifest, total_travel_time, total_distance, driver_detour, rider_detours)

    def find_best_trip_for_group(
        self, offer: DriverOffer, group: List[RiderRequest]
    ) -> Optional[Trip]:
        """
        Finds the optimal stop ordering for a given group of riders in offer's vehicle.
        Minimizes total distance and detour.
        """
        stops_def = []
        for req in group:
            stops_def.append((f"P_{req.id}", req.origin_id, req, StopType.PICKUP))
            stops_def.append((f"D_{req.id}", req.destination_id, req, StopType.DROPOFF))

        best_result = None
        best_dist = float('inf')

        # Check valid permutations (pickups before dropoffs)
        for perm in permutations(stops_def):
            valid_order = True
            indices = {s[0]: idx for idx, s in enumerate(perm)}
            for req in group:
                if indices[f"P_{req.id}"] > indices[f"D_{req.id}"]:
                    valid_order = False
                    break
            if not valid_order:
                continue

            result = self._evaluate_stop_sequence(offer, group, list(perm))
            if result is not None:
                manifest, travel_time, dist, driver_detour, rider_detours = result
                if dist < best_dist:
                    best_dist = dist
                    best_result = (manifest, travel_time, dist, driver_detour, rider_detours)

        if best_result is None:
            return None

        manifest, travel_time, dist, driver_detour, rider_detours = best_result

        # Calculate distance savings
        driver_solo = self.road_net.distance_km(offer.origin_id, offer.destination_id)
        riders_solo = sum(self.road_net.distance_km(r.origin_id, r.destination_id) for r in group)
        saved_km = (driver_solo + riders_solo) - dist

        if saved_km <= 0.05:  # trip must save distance over separate vehicles
            return None

        req_ids = [r.id for r in group]
        return Trip(
            id=f"trip_{offer.id}_{'-'.join(req_ids)}",
            offer_id=offer.id,
            driver_id=offer.driver_id,
            request_ids=req_ids,
            stops=manifest,
            total_travel_time=travel_time,
            total_distance_km=dist,
            solo_driver_distance_km=driver_solo,
            saved_distance_km=saved_km,
            driver_detour_min=driver_detour,
            rider_detours_min=rider_detours,
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
                    # Check if all pairs are feasible
                    p1 = frozenset([triplet[0], triplet[1]])
                    p2 = frozenset([triplet[1], triplet[2]])
                    p3 = frozenset([triplet[0], triplet[2]])
                    if p1 in pair_edges and p2 in pair_edges and p3 in pair_edges:
                        group = [req_by_id[r_id] for r_id in triplet]
                        trip = self.find_best_trip_for_group(offer, group)
                        if trip:
                            all_candidate_trips.append(trip)

            # 4. Size 4 trips (if capacity allows and all sub-triplets feasible)
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
