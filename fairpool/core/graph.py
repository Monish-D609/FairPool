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

    def update_node_position(self, node_id: str, lat: float, lng: float) -> bool:
        """Updates GPS coordinates of a node and refreshes edge distances & cache."""
        if node_id not in self.nodes:
            return False
        self.nodes[node_id].lat = lat
        self.nodes[node_id].lng = lng
        self._distance_matrix.clear()
        self._time_matrix.clear()

        # Update edge weights in adjacency list
        for u in self.adj:
            updated_list = []
            for v, dist_km, speed, time_min in self.adj[u]:
                if u == node_id or v == node_id:
                    d = haversine_distance_km(
                        self.nodes[u].lat, self.nodes[u].lng,
                        self.nodes[v].lat, self.nodes[v].lng
                    ) * 1.25
                    t = (d / max(speed, 10.0)) * 60.0
                    updated_list.append((v, d, speed, t))
                else:
                    updated_list.append((v, dist_km, speed, time_min))
            self.adj[u] = updated_list
        return True

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
            "center": {"lat": 12.84085, "lng": 80.15393},
            "nodes": [loc.to_dict() for loc in self.nodes.values()],
            "edges": edges,
        }

    def add_custom_location(
        self,
        node_id: str,
        name: str,
        lat: float,
        lng: float,
        connect_to: Optional[str] = None,
        speed_kmh: float = 45.0,
        is_campus_hub: bool = False,
    ) -> Location:
        """Adds a new location node dynamically and connects it into the network."""
        if node_id in self.nodes:
            self.update_node_position(node_id, lat, lng)
            return self.nodes[node_id]

        loc = self.add_node(node_id, name, lat, lng, is_campus_hub=is_campus_hub)

        target = connect_to if (connect_to and connect_to in self.nodes) else None
        if not target:
            # Find closest existing node
            best_dist = float("inf")
            for other_id, other_loc in self.nodes.items():
                if other_id == node_id:
                    continue
                d = haversine_distance_km(lat, lng, other_loc.lat, other_loc.lng)
                if d < best_dist:
                    best_dist = d
                    target = other_id

        if target:
            self.add_edge(node_id, target, speed_kmh=speed_kmh, bidirectional=True)

        self._distance_matrix.clear()
        self._time_matrix.clear()
        self.compute_all_pairs()
        return loc

    def add_suburb_from_catalog(self, suburb_id: str) -> Optional[Location]:
        """Adds an authorized Chennai suburb from the catalog to the live network."""
        entry = EXPANDED_SUBURBS_CATALOG.get(suburb_id)
        if not entry:
            return None
        return self.add_custom_location(
            node_id=suburb_id,
            name=entry["name"],
            lat=entry["lat"],
            lng=entry["lng"],
            connect_to=entry.get("connect_to"),
            speed_kmh=entry.get("speed_kmh", 45.0),
        )


# Catalog of extended Chennai suburbs available to be added when commuters book or offer rides
EXPANDED_SUBURBS_CATALOG: Dict[str, Dict] = {
    "PERUNGALATHUR": {
        "name": "Perungalathur Gateway",
        "lat": 12.9050,
        "lng": 80.0880,
        "connect_to": "VANDALUR",
        "speed_kmh": 50.0,
    },
    "GUDUVANCHERY": {
        "name": "Guduvanchery GST Hub",
        "lat": 12.8450,
        "lng": 80.0620,
        "connect_to": "VANDALUR",
        "speed_kmh": 50.0,
    },
    "URAPAKKAM": {
        "name": "Urapakkam Suburb",
        "lat": 12.8680,
        "lng": 80.0720,
        "connect_to": "VANDALUR",
        "speed_kmh": 50.0,
    },
    "CHROMEPET": {
        "name": "Chromepet GST Road",
        "lat": 12.9516,
        "lng": 80.1462,
        "connect_to": "TAMBARAM",
        "speed_kmh": 45.0,
    },
    "CAMP_ROAD": {
        "name": "Camp Road / Selaiyur",
        "lat": 12.9150,
        "lng": 80.1420,
        "connect_to": "TAMBARAM",
        "speed_kmh": 45.0,
    },
    "MEDAVAKKAM": {
        "name": "Medavakkam Suburb Center",
        "lat": 12.9171,
        "lng": 80.1923,
        "connect_to": "MAMBAKKAM",
        "speed_kmh": 45.0,
    },
    "SITHALAPAKKAM": {
        "name": "Sithalapakkam Suburb",
        "lat": 12.8850,
        "lng": 80.1870,
        "connect_to": "MAMBAKKAM",
        "speed_kmh": 45.0,
    },
    "SIRUSERI": {
        "name": "Siruseri SIPCOT IT Park",
        "lat": 12.8270,
        "lng": 80.2190,
        "connect_to": "KELAMBAKKAM",
        "speed_kmh": 45.0,
    },
    "NAVALUR": {
        "name": "Navalur OMR Junction",
        "lat": 12.8520,
        "lng": 80.2260,
        "connect_to": "KELAMBAKKAM",
        "speed_kmh": 50.0,
    },
    "SHOLINGANALLUR": {
        "name": "Sholinganallur Junction",
        "lat": 12.9010,
        "lng": 80.2279,
        "connect_to": "MAMBAKKAM",
        "speed_kmh": 45.0,
    },
    "VELACHERY": {
        "name": "Velachery Transit Hub",
        "lat": 12.9800,
        "lng": 80.2200,
        "connect_to": "TAMBARAM",
        "speed_kmh": 40.0,
    },
    "PORUR": {
        "name": "Porur Tollway & Lake",
        "lat": 13.0382,
        "lng": 80.1565,
        "connect_to": "TAMBARAM",
        "speed_kmh": 45.0,
    },
    "GUINDY": {
        "name": "Guindy Kathipara Interchange",
        "lat": 13.0067,
        "lng": 80.2030,
        "connect_to": "TAMBARAM",
        "speed_kmh": 45.0,
    },
    "ANNA_NAGAR": {
        "name": "Anna Nagar Tower Circle",
        "lat": 13.0850,
        "lng": 80.2100,
        "connect_to": "TAMBARAM",
        "speed_kmh": 40.0,
    },
}


def create_default_campus_network() -> RoadNetwork:
    """
    Creates the default streamlined 6-point Chennai City-to-Campus Corridor,
    centered strictly around VIT Chennai on the Vandalur-Kelambakkam Main Road.
    Exact 6 nodes in default view:
      1. VIT Chennai (Campus Hub) - 12.84085, 80.15393
      2. Kandigai Junction - 12.8480, 80.1415
      3. Mambakkam Junction - 12.8360, 80.1780
      4. Vandalur Crescent / Zoo - 12.8913, 80.0812
      5. Kelambakkam Bus Terminus - 12.7915, 80.2210
      6. Tambaram Railway Gateway - 12.9249, 80.1000
    """
    net = RoadNetwork(avg_speed_kmh=42.0)

    # 1. Sole Destination/Campus Hub
    net.add_node("VIT_CHENNAI", "VIT Chennai (Vandalur-Kelambakkam Rd)", 12.84085, 80.15393, is_campus_hub=True)

    # 2. Vandalur-Kelambakkam Main Road Core Commute Origins (West & East)
    net.add_node("KANDIGAI", "Kandigai Junction", 12.8480, 80.1415, is_campus_hub=False)
    net.add_node("MAMBAKKAM", "Mambakkam Junction", 12.8360, 80.1780, is_campus_hub=False)
    net.add_node("VANDALUR", "Vandalur Crescent / Zoo", 12.8913, 80.0812, is_campus_hub=False)
    net.add_node("KELAMBAKKAM", "Kelambakkam Bus Terminus", 12.7915, 80.2210, is_campus_hub=False)
    net.add_node("TAMBARAM", "Tambaram Railway Gateway", 12.9249, 80.1000, is_campus_hub=False)

    # Core arterial corridor connections
    net.add_edge("TAMBARAM", "VANDALUR", speed_kmh=50.0)
    net.add_edge("VANDALUR", "KANDIGAI", speed_kmh=50.0)
    net.add_edge("KANDIGAI", "VIT_CHENNAI", speed_kmh=50.0)
    net.add_edge("VIT_CHENNAI", "MAMBAKKAM", speed_kmh=50.0)
    net.add_edge("MAMBAKKAM", "KELAMBAKKAM", speed_kmh=50.0)

    net.compute_all_pairs()
    return net

