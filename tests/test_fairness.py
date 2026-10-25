"""
Unit tests for Fairness Engine, Gini coefficient computation, and driver detour rotation.
"""

import pytest
from fairpool.algorithms.fairness import compute_gini_coefficient, FairnessEngine
from fairpool.core.models import Trip, RouteStop, StopType


def test_gini_extremes():
    # Perfect equality: all values identical -> Gini 0.0
    assert abs(compute_gini_coefficient([5.0, 5.0, 5.0, 5.0])) < 1e-4

    # Extreme inequality: one person has all detour
    gini_extreme = compute_gini_coefficient([0.0, 0.0, 0.0, 100.0])
    assert gini_extreme > 0.70


def test_fairness_penalty_penalizes_high_detour_driver():
    engine = FairnessEngine(enable_fairness=True, fairness_weight=1.0)
    # Driver 1 has 40 min cumulative detour, Driver 2 has 2 min
    engine.register_driver("drv_overloaded", initial_detour=40.0)
    engine.register_driver("drv_fresh", initial_detour=2.0)

    # Candidate trip for drv_overloaded
    trip1 = Trip(
        id="t1",
        offer_id="o1",
        driver_id="drv_overloaded",
        request_ids=["r1"],
        stops=[],
        total_travel_time=30.0,
        total_distance_km=15.0,
        solo_driver_distance_km=10.0,
        saved_distance_km=8.0,
        driver_detour_min=8.0,
    )

    # Candidate trip for drv_fresh with same marginal detour
    trip2 = Trip(
        id="t2",
        offer_id="o2",
        driver_id="drv_fresh",
        request_ids=["r2"],
        stops=[],
        total_travel_time=30.0,
        total_distance_km=15.0,
        solo_driver_distance_km=10.0,
        saved_distance_km=8.0,
        driver_detour_min=8.0,
    )

    pen1 = engine.calculate_trip_penalty(trip1)
    pen2 = engine.calculate_trip_penalty(trip2)

    # Overloaded driver must receive significantly higher penalty
    assert pen1 > pen2
