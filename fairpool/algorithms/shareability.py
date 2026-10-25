"""
FairPool: Shareability Graph Engine
Constructs pairwise feasibility relations between requests and driver vehicles.
Prunes incompatible combinations before trip enumeration (FR-10).
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional
from itertools import permutations
from fairpool.core.models import (
    RiderRequest,
    DriverOffer,
    StopType,
    RouteStop,
)
from fairpool.core.graph import RoadNetwork


class ShareabilityGraph:
    """
    Shareability Graph representation:
    - Nodes: Rider requests R and Driver vehicles V
    - Edges:
      1. (v, r): Vehicle v can serve request r
      2. (v, r1, r2): Vehicle v can serve both r1 and r2 together
    """

    def __init__(self, road_net: RoadNetwork):
        self.road_net = road_net
        # v_id -> set of r_id that can be served singly
        self.vehicle_request_edges: Dict[str, Set[str]] = {}
        # v_id -> set of frozenset({r1_id, r2_id}) that can be served as a pair
        self.vehicle_pair_edges: Dict[str, Set[frozenset]] = {}

    def is_single_request_feasible(self, offer: DriverOffer, req: RiderRequest) -> bool:
        """Checks if vehicle can serve single request without constraint violations."""
        t0 = offer.departure_time
        t_pickup = t0 + self.road_net.travel_time_min(offer.origin_id, req.origin_id)
        t_dropoff = t_pickup + self.road_net.travel_time_min(req.origin_id, req.destination_id)
        t_dest = t_dropoff + self.road_net.travel_time_min(req.destination_id, offer.destination_id)

        driver_direct = self.road_net.travel_time_min(offer.origin_id, offer.destination_id)
        driver_detour = max(0.0, (t_dest - t0) - driver_direct)

        if driver_detour > offer.max_driver_detour_min:
            return False

        if t_pickup < req.earliest_departure or t_dropoff > req.latest_arrival:
            return False

        r_direct = self.road_net.travel_time_min(req.origin_id, req.destination_id)
        if (t_dropoff - t_pickup) > r_direct * (1.0 + req.max_detour_ratio):
            return False

        return True

    def is_pair_feasible(self, offer: DriverOffer, r1: RiderRequest, r2: RiderRequest) -> bool:
        """
        Checks if vehicle can serve requests r1 and r2 simultaneously.
        Evaluates valid stop orderings:
        Driver Origin -> {Pickups & Dropoffs} -> Driver Destination
        Subject to:
        - Pickup precedes Dropoff for each rider
        - Vehicle capacity not exceeded at any stop
        - All rider and driver time windows and detour limits respected
        """
        # Intermediate stops to order: P1, D1, P2, D2
        stops_def = [
            ("P1", r1.origin_id, r1, StopType.PICKUP),
            ("D1", r1.destination_id, r1, StopType.DROPOFF),
            ("P2", r2.origin_id, r2, StopType.PICKUP),
            ("D2", r2.destination_id, r2, StopType.DROPOFF),
        ]

        t0 = offer.departure_time
        driver_direct = self.road_net.travel_time_min(offer.origin_id, offer.destination_id)

        # Valid permutations of 4 stops: P1 before D1 and P2 before D2
        for perm in permutations(stops_def):
            names = [s[0] for s in perm]
            if names.index("P1") > names.index("D1") or names.index("P2") > names.index("D2"):
                continue

            # Simulate trajectory
            curr_loc = offer.origin_id
            curr_time = t0
            curr_occ = 1  # driver
            feasible = True
            rider_pickup_time: Dict[str, float] = {}

            for code, loc_id, req, stype in perm:
                travel = self.road_net.travel_time_min(curr_loc, loc_id)
                curr_time += travel
                curr_loc = loc_id

                if stype == StopType.PICKUP:
                    curr_occ += 1
                    if curr_occ > offer.capacity + 1:
                        feasible = False
                        break
                    # Wait if arrived before earliest departure
                    if curr_time < req.earliest_departure:
                        curr_time = req.earliest_departure
                    rider_pickup_time[req.id] = curr_time

                elif stype == StopType.DROPOFF:
                    curr_occ -= 1
                    if curr_time > req.latest_arrival:
                        feasible = False
                        break
                    r_travel_time = curr_time - rider_pickup_time[req.id]
                    r_direct = self.road_net.travel_time_min(req.origin_id, req.destination_id)
                    if r_travel_time > r_direct * (1.0 + req.max_detour_ratio):
                        feasible = False
                        break

            if not feasible:
                continue

            # Finally check driver arrival at destination
            curr_time += self.road_net.travel_time_min(curr_loc, offer.destination_id)
            d_detour = max(0.0, (curr_time - t0) - driver_direct)
            if d_detour <= offer.max_driver_detour_min:
                return True

        return False

    def build(self, requests: List[RiderRequest], offers: List[DriverOffer]) -> None:
        """Constructs the shareability graph across all requests and offers."""
        for offer in offers:
            self.vehicle_request_edges[offer.id] = set()
            self.vehicle_pair_edges[offer.id] = set()

            # 1. Single-request feasibility
            for req in requests:
                if self.is_single_request_feasible(offer, req):
                    self.vehicle_request_edges[offer.id].add(req.id)

            # 2. Pairwise feasibility among singly-feasible requests
            feasible_singles = list(self.vehicle_request_edges[offer.id])
            req_by_id = {r.id: r for r in requests}

            for i in range(len(feasible_singles)):
                r1_id = feasible_singles[i]
                r1 = req_by_id[r1_id]
                for j in range(i + 1, len(feasible_singles)):
                    r2_id = feasible_singles[j]
                    r2 = req_by_id[r2_id]
                    if self.is_pair_feasible(offer, r1, r2):
                        self.vehicle_pair_edges[offer.id].add(frozenset([r1_id, r2_id]))
