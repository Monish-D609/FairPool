"""
FairPool: Commuter Dataset Generator
Synthesizes realistic morning and evening campus commute distributions
with clustered residential origins and academic destination hubs (FR-21).
"""

from __future__ import annotations
import random
from typing import List, Tuple
from fairpool.core.models import RiderRequest, DriverOffer
from fairpool.core.graph import RoadNetwork


class CommuterDatasetGenerator:
    """
    Generates synthetic commuter batches modeling university campus commute patterns.
    Uses seeded pseudo-random generation to ensure 100% reproducible benchmarks.
    """

    def __init__(self, road_net: RoadNetwork, seed: int = 42):
        self.road_net = road_net
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_commute_batch(
        self,
        num_requests: int = 50,
        num_offers: int = 25,
        commute_direction: str = "INBOUND",  # INBOUND (home -> campus) or OUTBOUND (campus -> home)
        time_window_span_min: float = 60.0,
    ) -> Tuple[List[RiderRequest], List[DriverOffer]]:
        """
        Generates requests and offers for a single batch window.
        """
        campus_destinations = [
            node_id for node_id, loc in self.road_net.nodes.items() if loc.is_campus_hub
        ]
        residential_origins = [
            node_id for node_id, loc in self.road_net.nodes.items() if not loc.is_campus_hub
        ]

        if commute_direction == "INBOUND":
            origins_pool = residential_origins
            destinations_pool = campus_destinations
        else:
            origins_pool = campus_destinations
            destinations_pool = residential_origins

        # Generate Driver Offers
        offers: List[DriverOffer] = []
        for i in range(num_offers):
            orig = self.rng.choice(origins_pool)
            dest = self.rng.choice(destinations_pool)
            # Ensure origin != destination
            while dest == orig:
                dest = self.rng.choice(destinations_pool)

            # Departure times centered around peak hour (e.g., 8:00 AM = minute 30)
            dep_time = max(0.0, self.rng.gauss(time_window_span_min * 0.45, 12.0))
            cap = self.rng.choice([2, 3, 3, 4])  # mostly 3 spare seats
            max_detour = self.rng.uniform(12.0, 22.0)

            offer = DriverOffer(
                id=f"drv_{i+1:03d}",
                driver_id=f"driver_u{i+1:03d}",
                origin_id=orig,
                destination_id=dest,
                departure_time=round(dep_time, 1),
                capacity=cap,
                max_driver_detour_min=round(max_detour, 1),
                cumulative_detour_min=0.0,
            )
            offer.direct_distance_km = self.road_net.distance_km(orig, dest)
            offer.direct_travel_time = self.road_net.travel_time_min(orig, dest)
            offers.append(offer)

        # Generate Rider Requests
        requests: List[RiderRequest] = []
        for j in range(num_requests):
            orig = self.rng.choice(origins_pool)
            dest = self.rng.choice(destinations_pool)
            while dest == orig:
                dest = self.rng.choice(destinations_pool)

            direct_time = self.road_net.travel_time_min(orig, dest)
            direct_dist = self.road_net.distance_km(orig, dest)

            # Earliest departure around peak hour
            earliest_dep = max(0.0, self.rng.gauss(time_window_span_min * 0.45, 14.0))
            # Allowed latest arrival provides detour tolerance
            max_detour_ratio = self.rng.choice([0.25, 0.30, 0.35, 0.40])
            buffer_min = direct_time * max_detour_ratio + self.rng.uniform(8.0, 15.0)
            latest_arr = earliest_dep + direct_time + buffer_min

            req = RiderRequest(
                id=f"req_{j+1:03d}",
                rider_id=f"rider_u{j+1:03d}",
                origin_id=orig,
                destination_id=dest,
                earliest_departure=round(earliest_dep, 1),
                latest_arrival=round(latest_arr, 1),
                max_detour_ratio=max_detour_ratio,
                direct_travel_time=direct_time,
                direct_distance_km=direct_dist,
            )
            requests.append(req)

        return requests, offers
