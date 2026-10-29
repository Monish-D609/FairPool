"""
Unit and property tests for Shareability Graph, Trip Enumeration, and Set Packing Assignment.
Verifies FR-10, FR-11, FR-12.
"""

import pytest
from fairpool.core.models import RiderRequest, DriverOffer, StopType
from fairpool.core.graph import create_default_campus_network
from fairpool.algorithms.shareability import ShareabilityGraph
from fairpool.algorithms.enumeration import TripEnumerator
from fairpool.algorithms.engine import FairPoolEngine


def test_pairwise_feasibility():
    net = create_default_campus_network()
    # Offer: Tambaram -> VIT Chennai (leaves at min 0)
    offer = DriverOffer(
        id="off_test1",
        driver_id="drv1",
        origin_id="TAMBARAM",
        destination_id="VIT_CHENNAI",
        departure_time=0.0,
        capacity=3,
        max_driver_detour_min=15.0,
    )

    # Rider: Tambaram -> VIT Chennai (compatible direct route)
    req1 = RiderRequest(
        id="req_test1",
        rider_id="r1",
        origin_id="TAMBARAM",
        destination_id="VIT_CHENNAI",
        earliest_departure=0.0,
        latest_arrival=45.0,
        max_detour_ratio=0.5,
    )

    sg = ShareabilityGraph(net)
    sg.build([req1], [offer])

    assert "req_test1" in sg.vehicle_request_edges[offer.id]


def test_assignment_property_no_duplicate_assignments():
    """
    Property test (FR-12):
    Verify that in the matched solution:
    1. No request is included in more than one trip.
    2. No vehicle is assigned more than once.
    3. Vehicle capacity is respected at every stop.
    """
    net = create_default_campus_network()
    from fairpool.simulation.generator import CommuterDatasetGenerator
    gen = CommuterDatasetGenerator(net, seed=123)
    requests, offers = gen.generate_commute_batch(num_requests=35, num_offers=15)

    engine = FairPoolEngine(net, enable_fairness=True)
    result = engine.match_batch(requests, offers)

    assigned_requests = []
    assigned_offers = []

    for trip in result.matched_trips:
        assert trip.offer_id not in assigned_offers, f"Offer {trip.offer_id} assigned multiple times!"
        assigned_offers.append(trip.offer_id)

        # Check request uniqueness
        for rid in trip.request_ids:
            assert rid not in assigned_requests, f"Request {rid} matched in multiple trips!"
            assigned_requests.append(rid)

        # Check vehicle capacity constraint at each stop
        offer = next(o for o in offers if o.id == trip.offer_id)
        for stop in trip.stops:
            assert stop.occupancy_after_stop <= offer.capacity + 1, (
                f"Stop occupancy {stop.occupancy_after_stop} exceeds vehicle capacity {offer.capacity} + driver"
            )

        # Check precedence constraint: pickup must occur before dropoff
        for rid in trip.request_ids:
            pickup_idx = next(i for i, s in enumerate(trip.stops) if s.request_id == rid and s.stop_type == StopType.PICKUP)
            dropoff_idx = next(i for i, s in enumerate(trip.stops) if s.request_id == rid and s.stop_type == StopType.DROPOFF)
            assert pickup_idx < dropoff_idx, f"Pickup index {pickup_idx} not before dropoff {dropoff_idx} for req {rid}"


def test_exact_vs_greedy_solver_validity():
    """Compares exact ILP and greedy solver on a small batch."""
    net = create_default_campus_network()
    from fairpool.simulation.generator import CommuterDatasetGenerator
    gen = CommuterDatasetGenerator(net, seed=77)
    requests, offers = gen.generate_commute_batch(num_requests=12, num_offers=6)

    engine_exact = FairPoolEngine(net, use_exact_solver=True, enable_fairness=False)
    res_exact = engine_exact.match_batch(requests, offers)

    engine_greedy = FairPoolEngine(net, use_exact_solver=False, enable_fairness=False)
    res_greedy = engine_greedy.match_batch(requests, offers)

    # Exact ILP should save at least as much or more distance as greedy
    assert res_exact.total_vkm_saved >= res_greedy.total_vkm_saved - 0.5
