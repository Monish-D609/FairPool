"""
FairPool: Baseline Matching Algorithms
Implements:
1. No-Pooling Baseline: Every rider/driver travels independently.
2. Greedy Nearest-Pair Matching: Sequential greedy heuristic pairing riders to vehicles.
"""

from __future__ import annotations
import time
from typing import List, Dict, Set, Tuple
from fairpool.core.models import (
    RiderRequest,
    DriverOffer,
    Trip,
    RouteStop,
    StopType,
    BatchMatchResult,
)
from fairpool.core.graph import RoadNetwork


def calculate_gini(values: List[float]) -> float:
    """Computes the Gini coefficient for a list of non-negative values."""
    if not values or len(values) <= 1:
        return 0.0
    val_sorted = sorted([max(0.0, v) for v in values])
    n = len(val_sorted)
    sum_vals = sum(val_sorted)
    if sum_vals == 0:
        return 0.0
    cumulative = 0.0
    for i, v in enumerate(val_sorted, 1):
        cumulative += (2 * i - n - 1) * v
    return cumulative / (n * sum_vals)


class NoPoolingBaseline:
    """
    Simulates the uncoordinated status quo where every commuter travels solo.
    Zero vehicle-km saved, zero detours, 0% pooling match rate.
    """

    def __init__(self, road_net: RoadNetwork):
        self.road_net = road_net

    def run(self, requests: List[RiderRequest], offers: List[DriverOffer]) -> BatchMatchResult:
        start_time = time.perf_counter()

        # Compute direct distances
        driver_vkm = sum(self.road_net.distance_km(o.origin_id, o.destination_id) for o in offers)
        rider_vkm = sum(self.road_net.distance_km(r.origin_id, r.destination_id) for r in requests)
        total_baseline_vkm = driver_vkm + rider_vkm

        runtime_ms = (time.perf_counter() - start_time) * 1000.0

        return BatchMatchResult(
            batch_id="baseline_no_pool",
            matched_trips=[],
            unmatched_request_ids=[r.id for r in requests],
            unused_offer_ids=[o.id for o in offers],
            total_vkm_saved=0.0,
            total_vkm_baseline_no_pool=total_baseline_vkm,
            total_vkm_pooled=total_baseline_vkm,
            match_rate_percent=0.0,
            mean_driver_detour_min=0.0,
            p90_driver_detour_min=0.0,
            mean_rider_detour_min=0.0,
            p90_rider_detour_min=0.0,
            gini_driver_detour=0.0,
            runtime_ms=runtime_ms,
            algorithm_name="No-Pooling Baseline",
        )


class GreedyNearestPairMatcher:
    """
    Greedy Nearest-Pair Matching (First-Come Nearest-Feasible Pair).
    Sequentially pairs each rider request to the nearest available driver offer
    that satisfies capacity and detour constraints, without global optimization.
    """

    def __init__(self, road_net: RoadNetwork):
        self.road_net = road_net

    def run(self, requests: List[RiderRequest], offers: List[DriverOffer]) -> BatchMatchResult:
        start_time = time.perf_counter()

        # Baseline distances
        driver_solo_vkm = {o.id: self.road_net.distance_km(o.origin_id, o.destination_id) for o in offers}
        rider_solo_vkm = {r.id: self.road_net.distance_km(r.origin_id, r.destination_id) for r in requests}
        total_baseline_vkm = sum(driver_solo_vkm.values()) + sum(rider_solo_vkm.values())

        matched_trips: List[Trip] = []
        matched_req_ids: Set[str] = set()
        matched_offer_ids: Set[str] = set()

        driver_detours: List[float] = []
        rider_detours: List[float] = []

        # Sort requests by earliest departure time
        sorted_requests = sorted(requests, key=lambda r: r.earliest_departure)

        for req in sorted_requests:
            if req.id in matched_req_ids:
                continue

            best_offer: Optional[DriverOffer] = None
            best_detour: float = float('inf')
            best_trip: Optional[Trip] = None

            r_direct_time = self.road_net.travel_time_min(req.origin_id, req.destination_id)
            max_r_time = r_direct_time * (1.0 + req.max_detour_ratio)

            for offer in offers:
                if offer.id in matched_offer_ids:
                    continue

                # Feasibility check for single pair: Driver Origin -> Rider Pickup -> Rider Dropoff -> Driver Dest
                # Timing:
                t0 = offer.departure_time
                t_pickup = t0 + self.road_net.travel_time_min(offer.origin_id, req.origin_id)
                t_dropoff = t_pickup + self.road_net.travel_time_min(req.origin_id, req.destination_id)
                t_driver_dest = t_dropoff + self.road_net.travel_time_min(req.destination_id, offer.destination_id)

                driver_direct_time = self.road_net.travel_time_min(offer.origin_id, offer.destination_id)
                d_detour = max(0.0, (t_driver_dest - t0) - driver_direct_time)

                # Check constraints
                if d_detour > offer.max_driver_detour_min:
                    continue
                if t_pickup < req.earliest_departure or t_dropoff > req.latest_arrival:
                    continue
                r_trip_time = t_dropoff - t_pickup
                if r_trip_time > max_r_time:
                    continue

                # Check if this offer gives the smallest driver detour
                if d_detour < best_detour:
                    best_detour = d_detour
                    best_offer = offer

                    # Calculate distances
                    dist_pooled = (
                        self.road_net.distance_km(offer.origin_id, req.origin_id) +
                        self.road_net.distance_km(req.origin_id, req.destination_id) +
                        self.road_net.distance_km(req.destination_id, offer.destination_id)
                    )
                    saved_km = (driver_solo_vkm[offer.id] + rider_solo_vkm[req.id]) - dist_pooled

                    stops = [
                        RouteStop(location_id=offer.origin_id, stop_type=StopType.DRIVER_ORIGIN, estimated_arrival=t0, occupancy_after_stop=1),
                        RouteStop(location_id=req.origin_id, stop_type=StopType.PICKUP, rider_id=req.rider_id, request_id=req.id, estimated_arrival=t_pickup, occupancy_after_stop=2),
                        RouteStop(location_id=req.destination_id, stop_type=StopType.DROPOFF, rider_id=req.rider_id, request_id=req.id, estimated_arrival=t_dropoff, occupancy_after_stop=1),
                        RouteStop(location_id=offer.destination_id, stop_type=StopType.DRIVER_DESTINATION, estimated_arrival=t_driver_dest, occupancy_after_stop=0),
                    ]

                    best_trip = Trip(
                        id=f"trip_greedy_{offer.id}_{req.id}",
                        offer_id=offer.id,
                        driver_id=offer.driver_id,
                        request_ids=[req.id],
                        stops=stops,
                        total_travel_time=t_driver_dest - t0,
                        total_distance_km=dist_pooled,
                        solo_driver_distance_km=driver_solo_vkm[offer.id],
                        saved_distance_km=max(0.0, saved_km),
                        driver_detour_min=d_detour,
                        rider_detours_min={req.id: max(0.0, r_trip_time - r_direct_time)},
                    )

            if best_offer and best_trip and best_trip.saved_distance_km > 0:
                matched_trips.append(best_trip)
                matched_req_ids.add(req.id)
                matched_offer_ids.add(best_offer.id)
                driver_detours.append(best_trip.driver_detour_min)
                rider_detours.extend(best_trip.rider_detours_min.values())

        # Unmatched & unused
        unmatched_reqs = [r.id for r in requests if r.id not in matched_req_ids]
        unused_offers = [o.id for o in offers if o.id not in matched_offer_ids]

        # Vehicle distance metrics
        vkm_saved = sum(t.saved_distance_km for t in matched_trips)
        vkm_pooled = total_baseline_vkm - vkm_saved
        match_rate = (len(matched_req_ids) / len(requests) * 100.0) if requests else 0.0

        runtime_ms = (time.perf_counter() - start_time) * 1000.0

        p90_driver = sorted(driver_detours)[int(0.9 * len(driver_detours))] if driver_detours else 0.0
        p90_rider = sorted(rider_detours)[int(0.9 * len(rider_detours))] if rider_detours else 0.0

        return BatchMatchResult(
            batch_id="baseline_greedy_pair",
            matched_trips=matched_trips,
            unmatched_request_ids=unmatched_reqs,
            unused_offer_ids=unused_offers,
            total_vkm_saved=vkm_saved,
            total_vkm_baseline_no_pool=total_baseline_vkm,
            total_vkm_pooled=vkm_pooled,
            match_rate_percent=match_rate,
            mean_driver_detour_min=sum(driver_detours) / len(driver_detours) if driver_detours else 0.0,
            p90_driver_detour_min=p90_driver,
            mean_rider_detour_min=sum(rider_detours) / len(rider_detours) if rider_detours else 0.0,
            p90_rider_detour_min=p90_rider,
            gini_driver_detour=calculate_gini(driver_detours),
            runtime_ms=runtime_ms,
            algorithm_name="Greedy Nearest-Pair Matcher",
        )
