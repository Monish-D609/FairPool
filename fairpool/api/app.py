"""
FairPool: FastAPI Application & REST Service
Exposes endpoints for road network, commuter requests/offers,
batch matching, live benchmark harness, and static frontend serving.
"""

from __future__ import annotations
import os
import copy
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fairpool.core.models import RiderRequest, DriverOffer, Trip, BatchMatchResult
from fairpool.core.graph import RoadNetwork, create_default_campus_network
from fairpool.algorithms.fairness import FairnessEngine
from fairpool.algorithms.engine import FairPoolEngine
from fairpool.algorithms.baselines import NoPoolingBaseline, GreedyNearestPairMatcher
from fairpool.simulation.generator import CommuterDatasetGenerator
from fairpool.simulation.benchmark import BenchmarkHarness

app = FastAPI(
    title="FairPool API",
    description="Algorithmic Carpool & Ride-Pooling Matching Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Simulation & System State
road_net: RoadNetwork = create_default_campus_network()
fairness_ledger: FairnessEngine = FairnessEngine(enable_fairness=True)
engine: FairPoolEngine = FairPoolEngine(road_net, fairness_engine=fairness_ledger, enable_fairness=True)

requests_pool: List[RiderRequest] = []
offers_pool: List[DriverOffer] = []
latest_match_result: Optional[BatchMatchResult] = None
match_history: List[BatchMatchResult] = []


# Pydantic Request Schemas
class CreateRiderRequest(BaseModel):
    rider_id: str
    origin_id: str
    destination_id: str
    earliest_departure: float
    latest_arrival: float
    max_detour_ratio: float = 0.35


class CreateDriverOffer(BaseModel):
    driver_id: str
    origin_id: str
    destination_id: str
    departure_time: float
    capacity: int = 3
    max_driver_detour_min: float = 18.0


class MatchOptions(BaseModel):
    algorithm: str = "fairpool"  # "fairpool", "greedy", "no_pool"
    enable_fairness: bool = True
    use_exact_solver: bool = False
    fairness_weight: float = 0.45


class GenerateBatchOptions(BaseModel):
    num_requests: int = 25
    num_offers: int = 12
    direction: str = "INBOUND"
    seed: int = 42


# API Endpoints
@app.get("/api/network")
def get_network() -> Dict[str, Any]:
    """Returns road network nodes and edges for map visualization."""
    return road_net.to_dict()


@app.get("/api/state")
def get_state() -> Dict[str, Any]:
    """Returns current system pool and match stats."""
    mean_hist_detour = fairness_ledger.get_group_mean_detour()
    gini = fairness_ledger.get_cohort_gini()

    return {
        "num_requests": len(requests_pool),
        "num_offers": len(offers_pool),
        "requests": [r.to_dict() for r in requests_pool],
        "offers": [o.to_dict() for o in offers_pool],
        "latest_result": latest_match_result.to_dict() if latest_match_result else None,
        "cohort_gini": round(gini, 4),
        "mean_cumulative_detour_min": round(mean_hist_detour, 2),
        "driver_cumulative_detours": {
            k: round(v, 2) for k, v in fairness_ledger.driver_cumulative_detours.items()
        },
    }


@app.post("/api/requests")
def submit_request(req_in: CreateRiderRequest) -> Dict[str, Any]:
    """Submits a single rider request with instant route validation."""
    if req_in.origin_id not in road_net.nodes or req_in.destination_id not in road_net.nodes:
        raise HTTPException(status_code=400, detail="Invalid origin or destination node ID")

    direct_time = road_net.travel_time_min(req_in.origin_id, req_in.destination_id)
    direct_dist = road_net.distance_km(req_in.origin_id, req_in.destination_id)

    new_req = RiderRequest(
        id=f"req_{len(requests_pool)+1:03d}",
        rider_id=req_in.rider_id,
        origin_id=req_in.origin_id,
        destination_id=req_in.destination_id,
        earliest_departure=req_in.earliest_departure,
        latest_arrival=req_in.latest_arrival,
        max_detour_ratio=req_in.max_detour_ratio,
        direct_travel_time=direct_time,
        direct_distance_km=direct_dist,
    )
    requests_pool.append(new_req)
    return {"message": "Request submitted", "request": new_req.to_dict()}


@app.post("/api/offers")
def submit_offer(offer_in: CreateDriverOffer) -> Dict[str, Any]:
    """Submits a single driver offer."""
    if offer_in.origin_id not in road_net.nodes or offer_in.destination_id not in road_net.nodes:
        raise HTTPException(status_code=400, detail="Invalid origin or destination node ID")

    direct_time = road_net.travel_time_min(offer_in.origin_id, offer_in.destination_id)
    direct_dist = road_net.distance_km(offer_in.origin_id, offer_in.destination_id)

    new_offer = DriverOffer(
        id=f"drv_{len(offers_pool)+1:03d}",
        driver_id=offer_in.driver_id,
        origin_id=offer_in.origin_id,
        destination_id=offer_in.destination_id,
        departure_time=offer_in.departure_time,
        capacity=offer_in.capacity,
        max_driver_detour_min=offer_in.max_driver_detour_min,
        direct_travel_time=direct_time,
        direct_distance_km=direct_dist,
    )
    offers_pool.append(new_offer)
    fairness_ledger.register_driver(new_offer.driver_id, 0.0)
    return {"message": "Offer submitted", "offer": new_offer.to_dict()}


@app.post("/api/generate-sample")
def generate_sample(opts: GenerateBatchOptions) -> Dict[str, Any]:
    """Generates synthetic campus commute batch requests and offers."""
    gen = CommuterDatasetGenerator(road_net, seed=opts.seed)
    reqs, offs = gen.generate_commute_batch(
        num_requests=opts.num_requests,
        num_offers=opts.num_offers,
        commute_direction=opts.direction,
    )
    requests_pool.clear()
    offers_pool.clear()
    requests_pool.extend(reqs)
    offers_pool.extend(offs)

    for o in offs:
        fairness_ledger.register_driver(o.driver_id, 0.0)

    return {
        "message": f"Generated {len(reqs)} requests and {len(offs)} offers",
        "requests_count": len(reqs),
        "offers_count": len(offs),
    }


@app.post("/api/match")
def run_match(opts: MatchOptions) -> Dict[str, Any]:
    """Runs matching algorithm on current batch pool."""
    global latest_match_result
    if not requests_pool or not offers_pool:
        raise HTTPException(status_code=400, detail="Requests or offers pool is empty")

    if opts.algorithm == "no_pool":
        matcher = NoPoolingBaseline(road_net)
        res = matcher.run(copy.deepcopy(requests_pool), copy.deepcopy(offers_pool))
    elif opts.algorithm == "greedy":
        matcher = GreedyNearestPairMatcher(road_net)
        res = matcher.run(copy.deepcopy(requests_pool), copy.deepcopy(offers_pool))
    else:
        # FairPool engine
        fairness_ledger.enable_fairness = opts.enable_fairness
        fairness_ledger.fairness_weight = opts.fairness_weight
        eng = FairPoolEngine(
            road_net,
            fairness_engine=fairness_ledger,
            use_exact_solver=opts.use_exact_solver,
            enable_fairness=opts.enable_fairness,
        )
        res = eng.match_batch(
            requests_pool,
            offers_pool,
            batch_id=f"batch_{len(match_history)+1:03d}",
        )

    latest_match_result = res
    match_history.append(res)
    return res.to_dict()


@app.post("/api/benchmark")
def run_benchmark(opts: GenerateBatchOptions) -> Dict[str, Any]:
    """Executes multi-algorithm benchmark comparison on identical dataset."""
    harness = BenchmarkHarness(road_net, seed=opts.seed)
    single_res = harness.run_single_batch_comparison(
        num_requests=opts.num_requests,
        num_offers=opts.num_offers,
        commute_direction=opts.direction,
    )

    epoch_res = harness.run_multi_epoch_fairness_study(
        num_epochs=5,
        requests_per_epoch=opts.num_requests,
        num_drivers=opts.num_offers,
    )

    return {
        "single_batch": {k: v.to_dict() for k, v in single_res.items()},
        "multi_epoch_study": epoch_res,
        "markdown_table": harness.format_markdown_table(single_res),
    }


@app.post("/api/reset")
def reset_system() -> Dict[str, Any]:
    """Resets all simulation pools, history, and fairness ledger."""
    global latest_match_result
    requests_pool.clear()
    offers_pool.clear()
    latest_match_result = None
    match_history.clear()
    fairness_ledger.reset()
    return {"message": "System state successfully reset"}


# Serve static web files if web directory exists
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web")
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
