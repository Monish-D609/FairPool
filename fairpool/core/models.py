"""
FairPool: Core Data Models
Represents riders, drivers, road network nodes, trips, and batch assignment results.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
import uuid


class StopType(str, Enum):
    DRIVER_ORIGIN = "DRIVER_ORIGIN"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    DRIVER_DESTINATION = "DRIVER_DESTINATION"


@dataclass
class Location:
    id: str
    name: str
    lat: float
    lng: float
    is_campus_hub: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "is_campus_hub": self.is_campus_hub,
        }


@dataclass
class RiderRequest:
    id: str
    rider_id: str
    origin_id: str
    destination_id: str
    earliest_departure: float  # minutes from simulation epoch
    latest_arrival: float      # minutes from simulation epoch
    max_detour_ratio: float = 0.35  # e.g., 0.35 means max trip time <= 1.35 * direct_time
    status: str = "PENDING"     # PENDING, MATCHED, UNMATCHED, COMPLETED, CANCELLED
    direct_travel_time: float = 0.0
    direct_distance_km: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rider_id": self.rider_id,
            "origin_id": self.origin_id,
            "destination_id": self.destination_id,
            "earliest_departure": self.earliest_departure,
            "latest_arrival": self.latest_arrival,
            "max_detour_ratio": self.max_detour_ratio,
            "status": self.status,
            "direct_travel_time": round(self.direct_travel_time, 2),
            "direct_distance_km": round(self.direct_distance_km, 2),
        }


@dataclass
class DriverOffer:
    id: str
    driver_id: str
    origin_id: str
    destination_id: str
    departure_time: float      # minutes from simulation epoch
    capacity: int = 3          # spare seats (typically 2-4)
    max_driver_detour_min: float = 18.0  # max acceptable extra time over direct route
    cumulative_detour_min: float = 0.0   # historical detour tracked for fairness rotation
    status: str = "AVAILABLE"  # AVAILABLE, ASSIGNED, COMPLETED, CANCELLED
    direct_travel_time: float = 0.0
    direct_distance_km: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "origin_id": self.origin_id,
            "destination_id": self.destination_id,
            "departure_time": self.departure_time,
            "capacity": self.capacity,
            "max_driver_detour_min": self.max_driver_detour_min,
            "cumulative_detour_min": round(self.cumulative_detour_min, 2),
            "status": self.status,
            "direct_travel_time": round(self.direct_travel_time, 2),
            "direct_distance_km": round(self.direct_distance_km, 2),
        }


@dataclass
class RouteStop:
    location_id: str
    stop_type: StopType
    rider_id: Optional[str] = None
    request_id: Optional[str] = None
    estimated_arrival: float = 0.0  # minutes from epoch
    occupancy_after_stop: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location_id": self.location_id,
            "stop_type": self.stop_type.value,
            "rider_id": self.rider_id,
            "request_id": self.request_id,
            "estimated_arrival": round(self.estimated_arrival, 2),
            "occupancy_after_stop": self.occupancy_after_stop,
        }


@dataclass
class Trip:
    id: str
    offer_id: str
    driver_id: str
    request_ids: List[str]
    stops: List[RouteStop]
    total_travel_time: float
    total_distance_km: float
    solo_driver_distance_km: float
    saved_distance_km: float
    driver_detour_min: float
    rider_detours_min: Dict[str, float] = field(default_factory=dict)
    fairness_penalty: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "offer_id": self.offer_id,
            "driver_id": self.driver_id,
            "request_ids": self.request_ids,
            "stops": [s.to_dict() for s in self.stops],
            "total_travel_time": round(self.total_travel_time, 2),
            "total_distance_km": round(self.total_distance_km, 2),
            "solo_driver_distance_km": round(self.solo_driver_distance_km, 2),
            "saved_distance_km": round(self.saved_distance_km, 2),
            "driver_detour_min": round(self.driver_detour_min, 2),
            "rider_detours_min": {k: round(v, 2) for k, v in self.rider_detours_min.items()},
            "fairness_penalty": round(self.fairness_penalty, 2),
        }


@dataclass
class BatchMatchResult:
    batch_id: str
    matched_trips: List[Trip]
    unmatched_request_ids: List[str]
    unused_offer_ids: List[str]
    total_vkm_saved: float
    total_vkm_baseline_no_pool: float
    total_vkm_pooled: float
    match_rate_percent: float
    mean_driver_detour_min: float
    p90_driver_detour_min: float
    mean_rider_detour_min: float
    p90_rider_detour_min: float
    gini_driver_detour: float
    runtime_ms: float
    algorithm_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "matched_trips": [t.to_dict() for t in self.matched_trips],
            "unmatched_request_ids": self.unmatched_request_ids,
            "unused_offer_ids": self.unused_offer_ids,
            "total_vkm_saved": round(self.total_vkm_saved, 2),
            "total_vkm_baseline_no_pool": round(self.total_vkm_baseline_no_pool, 2),
            "total_vkm_pooled": round(self.total_vkm_pooled, 2),
            "match_rate_percent": round(self.match_rate_percent, 2),
            "mean_driver_detour_min": round(self.mean_driver_detour_min, 2),
            "p90_driver_detour_min": round(self.p90_driver_detour_min, 2),
            "mean_rider_detour_min": round(self.mean_rider_detour_min, 2),
            "p90_rider_detour_min": round(self.p90_rider_detour_min, 2),
            "gini_driver_detour": round(self.gini_driver_detour, 4),
            "runtime_ms": round(self.runtime_ms, 2),
            "algorithm_name": self.algorithm_name,
        }
