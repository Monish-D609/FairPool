"""
FairPool: Dynamic Fairness Engine
Maintains cumulative driver detour ledgers, computes fairness penalties,
and calculates the Gini coefficient to prevent detour concentration (FR-13).
"""

from __future__ import annotations
from typing import Dict, List, Optional
from fairpool.core.models import DriverOffer, Trip


def compute_gini_coefficient(values: List[float]) -> float:
    """
    Computes the Gini inequality coefficient for a distribution of values.
    Returns:
        0.0 = perfect equality (everyone has equal detour burden)
        1.0 = maximum inequality (one driver absorbs all detours)
    """
    if not values or len(values) <= 1:
        return 0.0
    arr = sorted([max(0.0, float(v)) for v in values])
    n = len(arr)
    s = sum(arr)
    if s <= 1e-6:
        return 0.0
    index_sum = sum((2 * i - n - 1) * val for i, val in enumerate(arr, 1))
    return float(index_sum / (n * s))


class FairnessEngine:
    """
    Dynamic Fairness Ledger and Penalty Assessor.
    Balances detours across driver cohorts over rolling epochs.
    """

    def __init__(
        self,
        fairness_weight: float = 0.45,
        max_ratio_to_mean: float = 1.75,
        enable_fairness: bool = True,
    ):
        self.fairness_weight = fairness_weight
        self.max_ratio_to_mean = max_ratio_to_mean
        self.enable_fairness = enable_fairness
        # driver_id -> cumulative detour minutes
        self.driver_cumulative_detours: Dict[str, float] = {}

    def register_driver(self, driver_id: str, initial_detour: float = 0.0) -> None:
        if driver_id not in self.driver_cumulative_detours:
            self.driver_cumulative_detours[driver_id] = initial_detour

    def get_group_mean_detour(self) -> float:
        if not self.driver_cumulative_detours:
            return 0.0
        return sum(self.driver_cumulative_detours.values()) / len(self.driver_cumulative_detours)

    def calculate_trip_penalty(self, trip: Trip) -> float:
        """
        Calculates the fairness penalty for a candidate trip.
        If the driver has accumulated higher detours than peers,
        incur a penalty proportional to the detour overload.
        """
        if not self.enable_fairness:
            return 0.0

        driver_id = trip.driver_id
        hist = self.driver_cumulative_detours.get(driver_id, 0.0)
        mean_detour = self.get_group_mean_detour()

        # Penalty components:
        # 1. Historical variance above peer group mean
        excess_over_mean = max(0.0, hist - mean_detour)
        # 2. Trip marginal detour impact
        marginal_detour = trip.driver_detour_min

        # Weighted penalty in units equivalent to km saved
        penalty = self.fairness_weight * (excess_over_mean * 0.15 + marginal_detour * 0.1)

        # Enforce strict cap if historical detour exceeds allowed ratio of mean
        if mean_detour > 5.0 and hist > mean_detour * self.max_ratio_to_mean:
            penalty += 50.0  # heavy penalty to avoid selection

        return penalty

    def apply_assigned_trips(self, trips: List[Trip]) -> None:
        """Updates driver cumulative detour history after confirmed batch match."""
        for trip in trips:
            curr = self.driver_cumulative_detours.get(trip.driver_id, 0.0)
            self.driver_cumulative_detours[trip.driver_id] = curr + trip.driver_detour_min

    def get_cohort_gini(self) -> float:
        """Computes current Gini coefficient of cumulative detours across drivers."""
        return compute_gini_coefficient(list(self.driver_cumulative_detours.values()))

    def reset(self) -> None:
        self.driver_cumulative_detours.clear()
