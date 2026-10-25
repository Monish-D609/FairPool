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

    # Verify every node is reachable from Central Admin
    admin_id = "ADMIN"
    dist_map, time_map = net.dijkstra(admin_id)

    for node_id in net.nodes:
        assert dist_map[node_id] < float('inf'), f"Node {node_id} unreachable from {admin_id}"
        assert time_map[node_id] < float('inf'), f"Node {node_id} unreachable from {admin_id}"


def test_triangle_inequality():
    net = create_default_campus_network()
    # d(u, w) <= d(u, v) + d(v, w)
    d_admin_metro = net.distance_km("ADMIN", "METRO_EAST")
    d_admin_cs = net.distance_km("ADMIN", "CS_BLOCK")
    d_cs_metro = net.distance_km("CS_BLOCK", "METRO_EAST")
    assert d_admin_metro <= (d_admin_cs + d_cs_metro) + 1e-5
