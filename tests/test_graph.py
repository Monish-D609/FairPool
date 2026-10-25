"""
Unit tests for FairPool Road Network and Travel Time calculations.
"""

import pytest
from fairpool.core.graph import RoadNetwork, create_default_campus_network, haversine_distance_km


def test_haversine_symmetry():
    lat1, lon1 = 12.9716, 77.5946
    lat2, lon2 = 12.9735, 77.5975
    d12 = haversine_distance_km(lat1, lon1, lat2, lon2)
    d21 = haversine_distance_km(lat2, lon2, lat1, lon1)
    assert abs(d12 - d21) < 1e-6
    assert d12 > 0.0


def test_default_campus_network_connectivity():
    net = create_default_campus_network()
    assert len(net.nodes) >= 12

    # Verify every node is reachable from IIT Madras
    hub_id = "IIT_MADRAS"
    dist_map, time_map = net.dijkstra(hub_id)

    for node_id in net.nodes:
        assert dist_map[node_id] < float('inf'), f"Node {node_id} unreachable from {hub_id}"
        assert time_map[node_id] < float('inf'), f"Node {node_id} unreachable from {hub_id}"


def test_triangle_inequality():
    net = create_default_campus_network()
    # d(u, w) <= d(u, v) + d(v, w)
    d_hub_tambaram = net.distance_km("IIT_MADRAS", "TAMBARAM")
    d_hub_guindy = net.distance_km("IIT_MADRAS", "GUINDY")
    d_guindy_tambaram = net.distance_km("GUINDY", "TAMBARAM")
    assert d_hub_tambaram <= (d_hub_guindy + d_guindy_tambaram) + 1e-5
