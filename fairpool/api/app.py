"""
FairPool: FastAPI Application & REST Service
Exposes endpoints for road network, commuter requests/offers,
batch matching, live benchmark harness, anonymized CSV export (FR-20),
cancellation handling (FR-6, FR-15), and institutional domain verification (FR-1).
"""

from __future__ import annotations
import os
import io
import csv
import copy
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from fairpool.core.models import RiderRequest, DriverOffer, Trip, BatchMatchResult
from fairpool.core.graph import RoadNetwork, create_default_campus_network, EXPANDED_SUBURBS_CATALOG
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

# Allowed Institutional Email Domains (FR-1)
ALLOWED_DOMAINS = [
    "vit.ac.in",
    "vitstudent.ac.in",
    "chennai.vit.ac.in",
    "campus.edu",
    "university.ac.in",
    "office.org",
    "fairpool.local",
    "gmail.com",
    "outlook.com",
    "yahoo.com",
]

# Global Simulation & System State
road_net: RoadNetwork = create_default_campus_network()
fairness_ledger: FairnessEngine = FairnessEngine(enable_fairness=True)
engine: FairPoolEngine = FairPoolEngine(road_net, fairness_engine=fairness_ledger, enable_fairness=True)

requests_pool: List[RiderRequest] = []
offers_pool: List[DriverOffer] = []
latest_match_result: Optional[BatchMatchResult] = None
match_history: List[BatchMatchResult] = []


def validate_institutional_email(email: str) -> bool:
    """Verifies that an email belongs to an allowed organization domain (FR-1)."""
    email = email.strip()
    if "@" not in email:
        # Allow internal mock IDs like rider_u001 or simple handles
        return True
    domain = email.split("@")[-1].lower()
    return any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS)


# Pydantic Request Schemas with Domain Validation (FR-1)
class CreateRiderRequest(BaseModel):
    rider_id: str
    origin_id: str
    destination_id: str
    earliest_departure: float
    latest_arrival: float
    max_detour_ratio: float = 0.35

    @field_validator("rider_id")
    @classmethod
    def check_email_domain(cls, v: str) -> str:
        if "@" in v and not validate_institutional_email(v):
            raise ValueError(
                f"Email domain not permitted. Must belong to an authorized institution: {', '.join(ALLOWED_DOMAINS)}"
            )
        return v


class CreateDriverOffer(BaseModel):
    driver_id: str
    origin_id: str
    destination_id: str
    departure_time: float
    capacity: int = 3
    max_driver_detour_min: float = 18.0

    @field_validator("driver_id")
    @classmethod
    def check_email_domain(cls, v: str) -> str:
        if "@" in v and not validate_institutional_email(v):
            raise ValueError(
                f"Email domain not permitted. Must belong to an authorized institution: {', '.join(ALLOWED_DOMAINS)}"
            )
        return v


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


class UpdateNodeLocation(BaseModel):
    lat: float
    lng: float


class CreateNodePayload(BaseModel):
    id: Optional[str] = None
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    catalog_id: Optional[str] = None
    connect_to: Optional[str] = None


# API Endpoints
@app.get("/api/network")
def get_network() -> Dict[str, Any]:
    """Returns road network nodes and edges for map visualization."""
    return road_net.to_dict()


@app.get("/api/catalog")
def get_suburbs_catalog() -> Dict[str, Any]:
    """Returns Chennai suburbs catalog and whether they are currently rendered on the map."""
    suburbs = []
    for cid, data in EXPANDED_SUBURBS_CATALOG.items():
        suburbs.append({
            "id": cid,
            "name": data["name"],
            "lat": data["lat"],
            "lng": data["lng"],
            "is_active": cid in road_net.nodes,
        })
    return {"catalog": suburbs}


@app.post("/api/nodes")
def add_node(payload: CreateNodePayload) -> Dict[str, Any]:
    """Dynamically adds a new suburb or landmark pin to the road network."""
    if payload.catalog_id and payload.catalog_id in EXPANDED_SUBURBS_CATALOG:
        loc = road_net.add_suburb_from_catalog(payload.catalog_id)
        if not loc:
            raise HTTPException(status_code=400, detail="Failed to add suburb from catalog")
        return {
            "message": f"Added {loc.name} to the network",
            "node": loc.to_dict(),
            "network": road_net.to_dict(),
        }

    if payload.lat is None or payload.lng is None:
        raise HTTPException(status_code=400, detail="Coordinates (lat, lng) are required for custom points")

    node_id = payload.id or payload.name.upper().replace(" ", "_")[:18]
    loc = road_net.add_custom_location(
        node_id=node_id,
        name=payload.name,
        lat=payload.lat,
        lng=payload.lng,
        connect_to=payload.connect_to,
    )
    return {
        "message": f"Added custom node {loc.name}",
        "node": loc.to_dict(),
        "network": road_net.to_dict(),
    }


@app.patch("/api/nodes/{node_id}")
def update_node_location(node_id: str, data: UpdateNodeLocation) -> Dict[str, Any]:
    """Dynamically moves a pin/node on the map and updates road distances."""
    success = road_net.update_node_position(node_id, data.lat, data.lng)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": f"Node {node_id} updated", "node": road_net.nodes[node_id].to_dict()}


@app.get("/api/state")
def get_state() -> Dict[str, Any]:
    """Returns current system pool and match stats."""
    # Auto-seed if brand new cold start
    if not requests_pool and not offers_pool:
        gen = CommuterDatasetGenerator(road_net, seed=42)
        reqs, offs = gen.generate_commute_batch(num_requests=12, num_offers=5)
        requests_pool.extend(reqs)
        offers_pool.extend(offs)
        for o in offs:
            fairness_ledger.register_driver(o.driver_id, 0.0)

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
        "allowed_domains": ALLOWED_DOMAINS,
    }


@app.post("/api/requests")
def submit_request(req_in: CreateRiderRequest) -> Dict[str, Any]:
    """Submits a single rider request with instant route validation (FR-1, FR-4)."""
    # Auto-expand suburb from catalog if requested origin was not yet added
    if req_in.origin_id not in road_net.nodes and req_in.origin_id in EXPANDED_SUBURBS_CATALOG:
        road_net.add_suburb_from_catalog(req_in.origin_id)

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


@app.delete("/api/requests/{request_id}")
def cancel_request(request_id: str) -> Dict[str, Any]:
    """Cancels a pending or matched rider request (FR-6, FR-15)."""
    target = next((r for r in requests_pool if r.id == request_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Request not found")

    target.status = "CANCELLED"
    requests_pool.remove(target)
    return {"message": f"Request {request_id} successfully cancelled", "request_id": request_id}


@app.post("/api/offers")
def submit_offer(offer_in: CreateDriverOffer) -> Dict[str, Any]:
    """Submits a single driver offer (FR-1, FR-5)."""
    # Auto-expand suburb from catalog if requested origin was not yet added
    if offer_in.origin_id not in road_net.nodes and offer_in.origin_id in EXPANDED_SUBURBS_CATALOG:
        road_net.add_suburb_from_catalog(offer_in.origin_id)

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


@app.delete("/api/offers/{offer_id}")
def cancel_offer(offer_id: str) -> Dict[str, Any]:
    """Cancels an available driver offer (FR-6, FR-15)."""
    target = next((o for o in offers_pool if o.id == offer_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Offer not found")

    target.status = "CANCELLED"
    offers_pool.remove(target)
    return {"message": f"Offer {offer_id} successfully cancelled", "offer_id": offer_id}


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
        gen = CommuterDatasetGenerator(road_net, seed=42)
        reqs, offs = gen.generate_commute_batch(num_requests=25, num_offers=12)
        requests_pool.extend(reqs)
        offers_pool.extend(offs)
        for o in offs:
            fairness_ledger.register_driver(o.driver_id, 0.0)

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
    """Executes multi-algorithm benchmark comparison on identical dataset (FR-21 to FR-25)."""
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


@app.get("/api/export-csv")
def export_anonymized_csv() -> Response:
    """
    Exports anonymized aggregate trip and matching data as CSV (FR-20, UR-C3).
    Ensures privacy by omitting exact coordinates and user private identifiers.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Trip_ID",
        "Anonymized_Driver_Hash",
        "Num_Passengers",
        "Total_Trip_Distance_Km",
        "Saved_Distance_Km",
        "Driver_Detour_Min",
        "Mean_Rider_Detour_Min",
        "Stops_Count",
        "Algorithm_Dispatched",
    ])

    if latest_match_result and latest_match_result.matched_trips:
        for idx, trip in enumerate(latest_match_result.matched_trips, 1):
            anon_driver = f"DRV_ANON_{hash(trip.driver_id) % 10000:04d}"
            r_detours = list(trip.rider_detours_min.values())
            mean_r_detour = sum(r_detours) / len(r_detours) if r_detours else 0.0

            writer.writerow([
                trip.id,
                anon_driver,
                len(trip.request_ids),
                round(trip.total_distance_km, 2),
                round(trip.saved_distance_km, 2),
                round(trip.driver_detour_min, 2),
                round(mean_r_detour, 2),
                len(trip.stops),
                latest_match_result.algorithm_name,
            ])
    else:
        # If no trips matched yet, provide empty row
        writer.writerow(["NO_DATA", "N/A", 0, 0.0, 0.0, 0.0, 0.0, 0, "None"])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fairpool_anonymized_trips.csv"},
    )


@app.post("/api/reset")
def reset_system() -> Dict[str, Any]:
    """Resets all simulation pools, history, fairness ledger, and road network to default 6 pins."""
    global road_net, latest_match_result
    road_net = create_default_campus_network()
    requests_pool.clear()
    offers_pool.clear()
    latest_match_result = None
    match_history.clear()
    fairness_ledger.reset()
    return {"message": "System state successfully reset to default 6 corridor pins"}


# Serve static web files if public or web directory exists
root_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
public_dir = os.path.join(root_project_dir, "public")
web_dir = os.path.join(root_project_dir, "web")
static_dir = public_dir if os.path.exists(public_dir) else web_dir
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
