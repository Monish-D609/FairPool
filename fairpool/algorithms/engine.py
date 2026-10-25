"""
FairPool: Core Matching Engine Orchestrator
Coordinates Road Network, Shareability Graph, Trip Enumeration,
Dynamic Fairness balancing, and Set-Packing Assignment.
"""

from __future__ import annotations
import time
from typing import List, Dict, Set, Optional
from fairpool.core.models import (
    RiderRequest,
    DriverOffer,
    Trip,
    BatchMatchResult,
)
from fairpool.core.graph import RoadNetwork
from fairpool.algorithms.shareability import ShareabilityGraph
from fairpool.algorithms.enumeration import TripEnumerator
from fairpool.algorithms.fairness import FairnessEngine, compute_gini_coefficient
from fairpool.algorithms.solver import ExactILPSolver, GreedyApproximationSolver


class FairPoolEngine:
    """
    Main algorithmic engine for FairPool.
    Executes batched matching passes, evaluates metrics, and enforces fairness constraints.
    """

    def __init__(
        self,
        road_net: RoadNetwork,
        fairness_engine: Optional[FairnessEngine] = None,
        use_exact_solver: bool = False,
        enable_fairness: bool = True,
        max_capacity_cap: int = 4,
    ):
        self.road_net = road_net
        self.use_exact_solver = use_exact_solver
        self.enable_fairness = enable_fairness
        self.max_capacity_cap = max_capacity_cap
        self.fairness_engine = fairness_engine or FairnessEngine(enable_fairness=enable_fairness)

    def match_batch(
        self,
        requests: List[RiderRequest],
        offers: List[DriverOffer],
        batch_id: str = "batch_001",
    ) -> BatchMatchResult:
        start_time = time.perf_counter()

        # Precompute direct travel distances and times for requests and offers
        driver_solo_vkm: Dict[str, float] = {}
        for o in offers:
            o.direct_distance_km = self.road_net.distance_km(o.origin_id, o.destination_id)
            o.direct_travel_time = self.road_net.travel_time_min(o.origin_id, o.destination_id)
            driver_solo_vkm[o.id] = o.direct_distance_km
            self.fairness_engine.register_driver(o.driver_id, o.cumulative_detour_min)

        rider_solo_vkm: Dict[str, float] = {}
        for r in requests:
            r.direct_distance_km = self.road_net.distance_km(r.origin_id, r.destination_id)
            r.direct_travel_time = self.road_net.travel_time_min(r.origin_id, r.destination_id)
            rider_solo_vkm[r.id] = r.direct_distance_km

        total_baseline_no_pool = sum(driver_solo_vkm.values()) + sum(rider_solo_vkm.values())

        if not requests or not offers:
            runtime_ms = (time.perf_counter() - start_time) * 1000.0
            return BatchMatchResult(
                batch_id=batch_id,
                matched_trips=[],
                unmatched_request_ids=[r.id for r in requests],
                unused_offer_ids=[o.id for o in offers],
                total_vkm_saved=0.0,
                total_vkm_baseline_no_pool=total_baseline_no_pool,
                total_vkm_pooled=total_baseline_no_pool,
                match_rate_percent=0.0,
                mean_driver_detour_min=0.0,
                p90_driver_detour_min=0.0,
                mean_rider_detour_min=0.0,
                p90_rider_detour_min=0.0,
                gini_driver_detour=0.0,
                runtime_ms=runtime_ms,
                algorithm_name="FairPool Engine",
            )

        # Step 1: Build Shareability Graph
        sg = ShareabilityGraph(self.road_net)
        sg.build(requests, offers)

        # Step 2: Enumerate Candidate Trips with Subset Pruning
        enumerator = TripEnumerator(self.road_net, sg)
        candidate_trips = enumerator.enumerate_candidate_trips(
            requests, offers, max_capacity_cap=self.max_capacity_cap
        )

        # Step 3: Apply Dynamic Fairness Penalties
        for trip in candidate_trips:
            trip.fairness_penalty = self.fairness_engine.calculate_trip_penalty(trip)

        # Step 4: Solve Set-Packing Assignment
        all_req_ids = [r.id for r in requests]
        all_offer_ids = [o.id for o in offers]

        if self.use_exact_solver and len(requests) <= 80:
            solver = ExactILPSolver()
        else:
            solver = GreedyApproximationSolver()

        matched_trips = solver.solve(candidate_trips, all_req_ids, all_offer_ids)

        # Update Driver Fairness History
        self.fairness_engine.apply_assigned_trips(matched_trips)

        # Collect matched/unmatched sets
        matched_req_ids: Set[str] = set()
        matched_offer_ids: Set[str] = set()
        driver_detours: List[float] = []
        rider_detours: List[float] = []

        for trip in matched_trips:
            matched_offer_ids.add(trip.offer_id)
            driver_detours.append(trip.driver_detour_min)
            for rid in trip.request_ids:
                matched_req_ids.add(rid)
            for detour in trip.rider_detours_min.values():
                rider_detours.append(detour)

        # Update request statuses
        for req in requests:
            req.status = "MATCHED" if req.id in matched_req_ids else "UNMATCHED"

        for offer in offers:
            offer.status = "ASSIGNED" if offer.id in matched_offer_ids else "AVAILABLE"
            offer.cumulative_detour_min = self.fairness_engine.driver_cumulative_detours.get(
                offer.driver_id, 0.0
            )

        unmatched_req_ids = [r.id for r in requests if r.id not in matched_req_ids]
        unused_offer_ids = [o.id for o in offers if o.id not in matched_offer_ids]

        # Calculate Aggregate Metrics
        total_vkm_saved = sum(t.saved_distance_km for t in matched_trips)
        total_vkm_pooled = total_baseline_no_pool - total_vkm_saved
        match_rate = (len(matched_req_ids) / len(requests) * 100.0) if requests else 0.0

        mean_driver_detour = sum(driver_detours) / len(driver_detours) if driver_detours else 0.0
        p90_driver_detour = (
            sorted(driver_detours)[int(0.9 * len(driver_detours))] if driver_detours else 0.0
        )

        mean_rider_detour = sum(rider_detours) / len(rider_detours) if rider_detours else 0.0
        p90_rider_detour = (
            sorted(rider_detours)[int(0.9 * len(rider_detours))] if rider_detours else 0.0
        )

        # Gini across all participating drivers in the cohort
        gini_detour = self.fairness_engine.get_cohort_gini()

        runtime_ms = (time.perf_counter() - start_time) * 1000.0

        alg_label = (
            "FairPool (Exact ILP)"
            if (self.use_exact_solver and len(requests) <= 80)
            else "FairPool (Approximation)"
        )
        if not self.enable_fairness:
            alg_label += " [No-Fairness Ablation]"

        return BatchMatchResult(
            batch_id=batch_id,
            matched_trips=matched_trips,
            unmatched_request_ids=unmatched_req_ids,
            unused_offer_ids=unused_offer_ids,
            total_vkm_saved=total_vkm_saved,
            total_vkm_baseline_no_pool=total_baseline_no_pool,
            total_vkm_pooled=total_vkm_pooled,
            match_rate_percent=match_rate,
            mean_driver_detour_min=mean_driver_detour,
            p90_driver_detour_min=p90_driver_detour,
            mean_rider_detour_min=mean_rider_detour,
            p90_rider_detour_min=p90_rider_detour,
            gini_driver_detour=gini_detour,
            runtime_ms=runtime_ms,
            algorithm_name=alg_label,
        )
