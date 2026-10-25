"""
FairPool: Road Network & Travel Time Engine
Provides shortest path calculations, Dijkstra's algorithm, Haversine distance,
and a realistic campus + commuter corridor network topology.
"""

from __future__ import annotations
import math
import heapq
from typing import Dict, List, Tuple, Optional
from fairpool.core.models import Location


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class RoadNetwork:
    """
    Weighted directed road network graph G = (V, E, W)
    Supports shortest-path travel time queries t(u, v) using Dijkstra's algorithm
    and precomputed all-pairs shortest paths for fast batch lookups.
    """

    def __init__(self, avg_speed_kmh: float = 30.0):
        self.avg_speed_kmh = avg_speed_kmh
        self.nodes: Dict[str, Location] = {}
        # adjacency: u -> [(v, distance_km, speed_kmh, travel_time_min)]
        self.adj: Dict[str, List[Tuple[str, float, float, float]]] = {}
        self._distance_matrix: Dict[Tuple[str, str], float] = {}
        self._time_matrix: Dict[Tuple[str, str], float] = {}

    def add_node(self, node_id: str, name: str, lat: float, lng: float, is_campus_hub: bool = False) -> Location:
        loc = Location(id=node_id, name=name, lat=lat, lng=lng, is_campus_hub=is_campus_hub)
        self.nodes[node_id] = loc
        if node_id not in self.adj:
            self.adj[node_id] = []
        return loc

    def add_edge(self, u: str, v: str, speed_kmh: Optional[float] = None, bidirectional: bool = True) -> None:
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Nodes {u} or {v} do not exist in network")

        speed = speed_kmh or self.avg_speed_kmh
        dist_km = haversine_distance_km(
            self.nodes[u].lat, self.nodes[u].lng,
            self.nodes[v].lat, self.nodes[v].lng
        )
        # travel time in minutes: (dist / speed) * 60
        travel_time_min = (dist_km / max(speed, 5.0)) * 60.0

        self.adj[u].append((v, dist_km, speed, travel_time_min))
        if bidirectional:
            self.adj[v].append((u, dist_km, speed, travel_time_min))

    def dijkstra(self, source: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Dijkstra's shortest path from source to all reachable nodes.
        Returns:
            (dist_dict, time_dict)
        """
        dist: Dict[str, float] = {node: float('inf') for node in self.nodes}
        times: Dict[str, float] = {node: float('inf') for node in self.nodes}

        dist[source] = 0.0
        times[source] = 0.0

        # priority queue stores (current_time, node)
        pq: List[Tuple[float, str]] = [(0.0, source)]

        while pq:
            curr_time, u = heapq.heappop(pq)

            if curr_time > times[u]:
                continue

            for v, edge_dist, _, edge_time in self.adj.get(u, []):
                new_time = curr_time + edge_time
                if new_time < times[v]:
                    times[v] = new_time
                    dist[v] = dist[u] + edge_dist
                    heapq.heappush(pq, (new_time, v))

        return dist, times

    def compute_all_pairs(self) -> None:
        """Precomputes and caches all-pairs shortest travel times and distances."""
        for u in self.nodes:
            dist_map, time_map = self.dijkstra(u)
            for v in self.nodes:
                self._distance_matrix[(u, v)] = dist_map.get(v, float('inf'))
                self._time_matrix[(u, v)] = time_map.get(v, float('inf'))

    def travel_time_min(self, u: str, v: str) -> float:
        if u == v:
            return 0.0
        if (u, v) in self._time_matrix:
            return self._time_matrix[(u, v)]
        _, time_map = self.dijkstra(u)
        t = time_map.get(v, float('inf'))
        self._time_matrix[(u, v)] = t
        return t

    def distance_km(self, u: str, v: str) -> float:
        if u == v:
            return 0.0
        if (u, v) in self._distance_matrix:
            return self._distance_matrix[(u, v)]
        dist_map, _ = self.dijkstra(u)
        d = dist_map.get(v, float('inf'))
        self._distance_matrix[(u, v)] = d
        return d

    def to_dict(self) -> Dict:
        """Serializes network for front-end rendering."""
        edges = []
        seen = set()
        for u, neighbors in self.adj.items():
            for v, dist, speed, travel_time in neighbors:
                pair = tuple(sorted([u, v]))
                if pair not in seen:
                    seen.add(pair)
                    edges.append({
                        "from": u,
                        "to": v,
                        "distance_km": round(dist, 3),
                        "speed_kmh": speed,
                        "travel_time_min": round(travel_time, 2),
                    })
        return {
            "nodes": [loc.to_dict() for loc in self.nodes.values()],
            "edges": edges,
        }


def create_default_campus_network() -> RoadNetwork:
    """
    Creates a rich, realistic University Campus & Suburban Commuter Corridor.
    Coordinates centered around an academic cluster:
    - Academic Core: Central Admin, CS Block, Engineering Quad, Main Library, Science Arena
    - Residential & Hostels: North Hostels, South Hostels, Scholar Housing
    - Commuter Origins: East Metro Station, Tech Park Crossing, West Suburb Hub, Riverdale Heights
    """
    net = RoadNetwork(avg_speed_kmh=35.0)

    # Campus Core Nodes
    net.add_node("ADMIN", "Central Admin Building", 12.9716, 77.5946, is_campus_hub=True)
    net.add_node("CS_BLOCK", "Computer Science Complex", 12.9735, 77.5975, is_campus_hub=True)
    net.add_node("ENG_QUAD", "Engineering Quadrangle", 12.9695, 77.5980, is_campus_hub=True)
    net.add_node("LIBRARY", "Central University Library", 12.9725, 77.5910, is_campus_hub=True)
    net.add_node("SCI_ARENA", "Science & Innovation Arena", 12.9760, 77.5935, is_campus_hub=True)

    # Student Hostels & On-Campus Housing
    net.add_node("HOSTEL_N", "North Student Residences", 12.9810, 77.5920, is_campus_hub=False)
    net.add_node("HOSTEL_S", "South Student Residences", 12.9640, 77.5960, is_campus_hub=False)
    net.add_node("STAFF_QTRS", "Faculty & Staff Quarters", 12.9680, 77.5870, is_campus_hub=False)

    # Major Commuter Ingress & Suburban Gateways
    net.add_node("METRO_EAST", "East Metro Interchange", 12.9720, 77.6150, is_campus_hub=False)
    net.add_node("TECH_PARK", "Tech Park Junction", 12.9850, 77.6100, is_campus_hub=False)
    net.add_node("WEST_SUBURB", "West Suburb Transit Hub", 12.9650, 77.5750, is_campus_hub=False)
    net.add_node("RIVERDALE", "Riverdale Residential Circle", 12.9550, 77.5890, is_campus_hub=False)
    net.add_node("NORTH_GATE", "Campus Main North Gate", 12.9780, 77.5950, is_campus_hub=True)
    net.add_node("SOUTH_GATE", "Campus South Security Gate", 12.9660, 77.5930, is_campus_hub=True)

    # Campus Arteries (Inner Ring)
    net.add_edge("ADMIN", "CS_BLOCK", speed_kmh=25.0)
    net.add_edge("ADMIN", "LIBRARY", speed_kmh=25.0)
    net.add_edge("ADMIN", "ENG_QUAD", speed_kmh=25.0)
    net.add_edge("CS_BLOCK", "ENG_QUAD", speed_kmh=25.0)
    net.add_edge("CS_BLOCK", "SCI_ARENA", speed_kmh=25.0)
    net.add_edge("SCI_ARENA", "NORTH_GATE", speed_kmh=30.0)
    net.add_edge("LIBRARY", "STAFF_QTRS", speed_kmh=30.0)
    net.add_edge("ENG_QUAD", "SOUTH_GATE", speed_kmh=30.0)

    # Hostel connections
    net.add_edge("NORTH_GATE", "HOSTEL_N", speed_kmh=35.0)
    net.add_edge("SOUTH_GATE", "HOSTEL_S", speed_kmh=35.0)
    net.add_edge("STAFF_QTRS", "SOUTH_GATE", speed_kmh=30.0)

    # External Commute Expressways & Arterials
    net.add_edge("CS_BLOCK", "METRO_EAST", speed_kmh=45.0)
    net.add_edge("METRO_EAST", "TECH_PARK", speed_kmh=50.0)
    net.add_edge("TECH_PARK", "NORTH_GATE", speed_kmh=40.0)
    net.add_edge("LIBRARY", "WEST_SUBURB", speed_kmh=45.0)
    net.add_edge("WEST_SUBURB", "RIVERDALE", speed_kmh=45.0)
    net.add_edge("RIVERDALE", "SOUTH_GATE", speed_kmh=40.0)
    net.add_edge("HOSTEL_N", "TECH_PARK", speed_kmh=40.0)
    net.add_edge("HOSTEL_S", "RIVERDALE", speed_kmh=35.0)

    # Precompute all pairs shortest paths for instant lookups
    net.compute_all_pairs()
    return net
