"""
Integration tests for FairPool FastAPI REST endpoints.
Verifies FR-1, FR-6, FR-15, FR-20, and API contract invariants.
"""

import pytest
from fastapi.testclient import TestClient
from fairpool.api.app import app

client = TestClient(app)


def test_api_network():
    res = client.get("/api/network")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 12


def test_api_domain_verification_fr1():
    # Valid campus email domain
    valid_payload = {
        "rider_id": "scholar@campus.edu",
        "origin_id": "TAMBARAM",
        "destination_id": "IIT_MADRAS",
        "earliest_departure": 0.0,
        "latest_arrival": 45.0,
        "max_detour_ratio": 0.35,
    }
    res_valid = client.post("/api/requests", json=valid_payload)
    assert res_valid.status_code == 200

    # Invalid public external domain
    invalid_payload = {
        "rider_id": "intruder@unauthorized-domain.com",
        "origin_id": "TAMBARAM",
        "destination_id": "IIT_MADRAS",
        "earliest_departure": 0.0,
        "latest_arrival": 45.0,
        "max_detour_ratio": 0.35,
    }
    res_invalid = client.post("/api/requests", json=invalid_payload)
    assert res_invalid.status_code == 422 or res_invalid.status_code == 400


def test_api_cancellation_fr6():
    # Submit request
    payload = {
        "rider_id": "cancel_test@campus.edu",
        "origin_id": "TAMBARAM",
        "destination_id": "IIT_MADRAS",
        "earliest_departure": 5.0,
        "latest_arrival": 45.0,
        "max_detour_ratio": 0.35,
    }
    post_res = client.post("/api/requests", json=payload)
    assert post_res.status_code == 200
    req_id = post_res.json()["request"]["id"]

    # Cancel request
    del_res = client.delete(f"/api/requests/{req_id}")
    assert del_res.status_code == 200
    assert "successfully cancelled" in del_res.json()["message"]


def test_api_generate_and_match():
    # Reset first
    client.post("/api/reset")

    # Generate small sample
    gen_res = client.post(
        "/api/generate-sample",
        json={"num_requests": 15, "num_offers": 8, "direction": "INBOUND", "seed": 42},
    )
    assert gen_res.status_code == 200

    # Match
    match_res = client.post(
        "/api/match",
        json={"algorithm": "fairpool", "enable_fairness": True, "use_exact_solver": False},
    )
    assert match_res.status_code == 200
    res_data = match_res.json()
    assert "matched_trips" in res_data
    assert len(res_data["matched_trips"]) > 0
    assert res_data["total_vkm_saved"] > 0


def test_api_export_anonymized_csv_fr20():
    # Export CSV
    csv_res = client.get("/api/export-csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    content = csv_res.text
    assert "Trip_ID" in content
    assert "Anonymized_Driver_Hash" in content
    assert "Saved_Distance_Km" in content
