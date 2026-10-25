"""
FairPool: Road Network & Travel Time Engine (Chennai Metropolitan Corridor)
Provides shortest path calculations, Dijkstra's algorithm, Haversine distance,
and a realistic Chennai Metropolitan commute network linking residential suburbs
(Tambaram, Porur, Anna Nagar, Velachery, OMR, etc.) to destination campus hubs
(IIT Madras, Anna University, Tidel Park).
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
    Weighted directed road network graph G = (V, E, W).
    Supports shortest-path travel time queries t(u, v) using Dijkstra's algorithm,
    precomputed all-pairs shortest paths, and dynamic point-to-point queries.
    """

    def __init__(self, avg_speed_kmh: float = 32.0):
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
        # Factor road circuity (1.25x direct geodesic for city roads)
        road_dist_km = dist_km * 1.25
        travel_time_min = (road_dist_km / max(speed, 10.0)) * 60.0

        self.adj[u].append((v, road_dist_km, speed, travel_time_min))
        if bidirectional:
            self.adj[v].append((u, road_dist_km, speed, travel_time_min))

    def dijkstra(self, source: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Dijkstra's shortest path from source to all reachable nodes."""
        dist: Dict[str, float] = {node: float('inf') for node in self.nodes}
        times: Dict[str, float] = {node: float('inf') for node in self.nodes}

        if source not in self.nodes:
            return dist, times

        dist[source] = 0.0
        times[source] = 0.0
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
            cached = self._time_matrix[(u, v)]
            if cached < float('inf'):
                return cached

        if u in self.nodes and v in self.nodes:
            _, time_map = self.dijkstra(u)
            t = time_map.get(v, float('inf'))
            if t < float('inf'):
                self._time_matrix[(u, v)] = t
                return t

            # Fallback to geodesic estimate if disconnected
            dist = self.distance_km(u, v)
            return (dist / self.avg_speed_kmh) * 60.0

        # Arbitrary coordinate point fallback
        return 15.0

    def distance_km(self, u: str, v: str) -> float:
        if u == v:
            return 0.0
        if (u, v) in self._distance_matrix:
            cached = self._distance_matrix[(u, v)]
            if cached < float('inf'):
                return cached

        if u in self.nodes and v in self.nodes:
            dist_map, _ = self.dijkstra(u)
            d = dist_map.get(v, float('inf'))
            if d < float('inf'):
                self._distance_matrix[(u, v)] = d
                return d
            # Fallback to direct haversine
            return haversine_distance_km(
                self.nodes[u].lat, self.nodes[u].lng,
                self.nodes[v].lat, self.nodes[v].lng
            ) * 1.25

        return 10.0

    def to_dict(self) -> Dict:
        """Serializes network for front-end Google Map rendering."""
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
                        "distance_km": round(dist, 2),
                        "speed_kmh": speed,
                        "travel_time_min": round(travel_time, 2),
                    })
        return {
            "city": "Chennai",
            "center": {"lat": 13.0067, "lng": 80.2200},
            "nodes": [loc.to_dict() for loc in self.nodes.values()],
            "edges": edges,
        }


def create_default_campus_network() -> RoadNetwork:
    """
    Creates the Chennai Metropolitan City-to-Campus Commuter Corridor.
    Central Academic & Tech Hubs:
      - IIT Madras (Main Academic Core)
      - Anna University (Guindy Campus)
      - Tidel Park (OMR Technology Center)
    City Residential Origin Clusters across Chennai:
      - Tambaram, Chromepet, Porur, Anna Nagar, Kilpauk, Nungambakkam,
        T. Nagar, Alwarpet, Velachery, Medavakkam, Adyar, Thiruvanmiyur,
        Perungudi, Sholinganallur, Siruseri, Guindy.
    """
    net = RoadNetwork(avg_speed_kmh=35.0)

    # Destination Academic / Corporate Hubs
    net.add_node("IIT_MADRAS", "IIT Madras Academic Complex", 12.9915, 80.2337, is_campus_hub=True)
    net.add_node("ANNA_UNIV", "Anna University (Guindy)", 13.0110, 80.2354, is_campus_hub=True)
    net.add_node("TIDEL_PARK", "Tidel Park / OMR Hub", 12.9892, 80.2486, is_campus_hub=True)

    # South Chennai Suburban Ingress (GST Road Corridor)
    net.add_node("TAMBARAM", "Tambaram Railway Gateway", 12.9249, 80.1000, is_campus_hub=False)
    net.add_node("CHROMEPET", "Chromepet GST Road", 12.9516, 80.1462, is_campus_hub=False)
    net.add_node("GUINDY", "Guindy Kathipara Interchange", 13.0067, 80.2030, is_campus_hub=False)

    # South-East IT Corridor (OMR / ECR)
    net.add_node("SIRUSERI", "Siruseri SIPCOT IT Park", 12.8270, 80.2190, is_campus_hub=False)
    net.add_node("SHOLINGANALLUR", "Sholinganallur Junction", 12.9010, 80.2279, is_campus_hub=False)
    net.add_node("PERUNGUDI", "Perungudi OMR Toll", 12.9654, 80.2461, is_campus_hub=False)
    net.add_node("THIRUVANMIYUR", "Thiruvanmiyur ECR Ingress", 12.9830, 80.2590, is_campus_hub=False)
    net.add_node("ADYAR", "Adyar Circle", 13.0012, 80.2565, is_campus_hub=False)

    # Central & South-Central Residential Districts
    net.add_node("VELACHERY", "Velachery Transit Hub", 12.9800, 80.2200, is_campus_hub=False)
    net.add_node("MEDAVAKKAM", "Medavakkam Suburb Center", 12.9171, 80.1923, is_campus_hub=False)
    net.add_node("T_NAGAR", "T. Nagar Panagal Park", 13.0418, 80.2341, is_campus_hub=False)
    net.add_node("ALWARPET", "Alwarpet TTK Road", 13.0334, 80.2520, is_campus_hub=False)

    # West & North-West Residential Corridors
    net.add_node("PORUR", "Porur Tollway & Lake", 13.0382, 80.1565, is_campus_hub=False)
    net.add_node("ANNA_NAGAR", "Anna Nagar Tower Circle", 13.0850, 80.2100, is_campus_hub=False)
    net.add_node("KILPAUK", "Kilpauk EVR Periyar Salai", 13.0784, 80.2412, is_campus_hub=False)
    net.add_node("NUNGAMBAKKAM", "Nungambakkam High Road", 13.0595, 80.2425, is_campus_hub=False)

    # Connect Highway & Arterial Edges
    # 1. GST Road Arterial Corridor
    net.add_edge("TAMBARAM", "CHROMEPET", speed_kmh=45.0)
    net.add_edge("CHROMEPET", "GUINDY", speed_kmh=45.0)
    net.add_edge("GUINDY", "IIT_MADRAS", speed_kmh=35.0)
    net.add_edge("GUINDY", "ANNA_UNIV", speed_kmh=35.0)

    # 2. OMR IT Expressway Corridor
    net.add_edge("SIRUSERI", "SHOLINGANALLUR", speed_kmh=50.0)
    net.add_edge("SHOLINGANALLUR", "PERUNGUDI", speed_kmh=45.0)
    net.add_edge("PERUNGUDI", "TIDEL_PARK", speed_kmh=40.0)
    net.add_edge("TIDEL_PARK", "IIT_MADRAS", speed_kmh=30.0)

    # 3. Velachery & Medavakkam Arterials
    net.add_edge("MEDAVAKKAM", "VELACHERY", speed_kmh=40.0)
    net.add_edge("VELACHERY", "IIT_MADRAS", speed_kmh=30.0)
    net.add_edge("VELACHERY", "GUINDY", speed_kmh=35.0)
    net.add_edge("VELACHERY", "TIDEL_PARK", speed_kmh=35.0)

    # 4. Coastal / Adyar / ECR Arterials
    net.add_edge("THIRUVANMIYUR", "ADYAR", speed_kmh=35.0)
    net.add_edge("THIRUVANMIYUR", "TIDEL_PARK", speed_kmh=35.0)
    net.add_edge("ADYAR", "IIT_MADRAS", speed_kmh=30.0)
    net.add_edge("ADYAR", "ANNA_UNIV", speed_kmh=30.0)

    # 5. Central Chennai Corridors (Kilpauk -> Nungambakkam -> T. Nagar -> Alwarpet -> IIT)
    net.add_edge("KILPAUK", "NUNGAMBAKKAM", speed_kmh=30.0)
    net.add_edge("NUNGAMBAKKAM", "T_NAGAR", speed_kmh=30.0)
    net.add_edge("T_NAGAR", "ALWARPET", speed_kmh=30.0)
    net.add_edge("ALWARPET", "ANNA_UNIV", speed_kmh=35.0)
    net.add_edge("ANNA_UNIV", "IIT_MADRAS", speed_kmh=30.0)

    # 6. West Corridor (Anna Nagar -> Porur -> Guindy)
    net.add_edge("ANNA_NAGAR", "PORUR", speed_kmh=40.0)
    net.add_edge("ANNA_NAGAR", "NUNGAMBAKKAM", speed_kmh=35.0)
    net.add_edge("PORUR", "GUINDY", speed_kmh=40.0)

    # 7. Cross-connecting Links
    net.add_edge("SHOLINGANALLUR", "MEDAVAKKAM", speed_kmh=40.0)
    net.add_edge("T_NAGAR", "GUINDY", speed_kmh=35.0)

    net.compute_all_pairs()
    return net
