"""
Reference data used by the agents.

Everything here is static, public-domain style reference data:
city coordinates (for weather + distance), IATA codes, a relative cost index,
approximate monthly climate normals (fallback when live weather is unavailable),
and per-person daily spend benchmarks by travel style.

NOTE: Climate normals and spend figures are approximations for planning only.
"""

from math import radians, sin, cos, asin, sqrt

# month index 1..12 -> (avg_high_c, avg_low_c, rainy_days)
_SG = {m: (31, 25, d) for m, d in zip(range(1, 13), [12, 9, 12, 14, 14, 13, 13, 14, 13, 15, 19, 19])}

CITIES = {
    # ---------------- Origins (major Indian hubs) ----------------
    "Mumbai":    {"iata": "BOM", "lat": 19.0760, "lon": 72.8777, "country": "India", "cost_index": 1.15, "origin": True,  "dest": True},
    "Delhi":     {"iata": "DEL", "lat": 28.6139, "lon": 77.2090, "country": "India", "cost_index": 1.10, "origin": True,  "dest": True},
    "Bengaluru": {"iata": "BLR", "lat": 12.9716, "lon": 77.5946, "country": "India", "cost_index": 1.05, "origin": True,  "dest": False},
    "Chennai":   {"iata": "MAA", "lat": 13.0827, "lon": 80.2707, "country": "India", "cost_index": 1.00, "origin": True,  "dest": False},
    "Kolkata":   {"iata": "CCU", "lat": 22.5726, "lon": 88.3639, "country": "India", "cost_index": 0.95, "origin": True,  "dest": False},
    "Hyderabad": {"iata": "HYD", "lat": 17.3850, "lon": 78.4867, "country": "India", "cost_index": 1.00, "origin": True,  "dest": False},
    "Pune":      {"iata": "PNQ", "lat": 18.5204, "lon": 73.8567, "country": "India", "cost_index": 1.00, "origin": True,  "dest": False},
    "Ahmedabad": {"iata": "AMD", "lat": 23.0225, "lon": 72.5714, "country": "India", "cost_index": 0.95, "origin": True,  "dest": False},
    # ---------------- Destinations ----------------
    "Goa":       {"iata": "GOI", "lat": 15.4909, "lon": 73.8278, "country": "India", "cost_index": 1.10, "origin": False, "dest": True},
    "Jaipur":    {"iata": "JAI", "lat": 26.9124, "lon": 75.7873, "country": "India", "cost_index": 0.90, "origin": False, "dest": True},
    "Udaipur":   {"iata": "UDR", "lat": 24.5854, "lon": 73.7125, "country": "India", "cost_index": 1.00, "origin": False, "dest": True},
    "Kochi":     {"iata": "COK", "lat": 9.9312,  "lon": 76.2673, "country": "India", "cost_index": 0.90, "origin": False, "dest": True},
    "Varanasi":  {"iata": "VNS", "lat": 25.3176, "lon": 82.9739, "country": "India", "cost_index": 0.80, "origin": False, "dest": True},
    "Dubai":     {"iata": "DXB", "lat": 25.2048, "lon": 55.2708, "country": "UAE", "cost_index": 1.80, "origin": False, "dest": True},
    "Singapore": {"iata": "SIN", "lat": 1.3521,  "lon": 103.8198, "country": "Singapore", "cost_index": 2.00, "origin": False, "dest": True},
    "Bangkok":   {"iata": "BKK", "lat": 13.7563, "lon": 100.5018, "country": "Thailand", "cost_index": 1.20, "origin": False, "dest": True},
}

CLIMATE_NORMALS = {
    "Goa":      dict(zip(range(1, 13), [(32,20,0),(32,21,0),(32,23,0),(33,25,1),(33,27,3),(30,25,22),(29,24,27),(29,24,25),(30,24,15),(32,24,6),(33,22,2),(33,21,0)])),
    "Jaipur":   dict(zip(range(1, 13), [(22,8,1),(25,11,1),(31,16,1),(37,22,1),(40,26,2),(39,28,5),(34,26,12),(32,25,12),(33,24,6),(33,19,1),(29,13,0),(24,9,0)])),
    "Udaipur":  dict(zip(range(1, 13), [(24,8,0),(28,11,0),(33,16,0),(37,21,0),(39,25,1),(36,26,5),(31,24,12),(29,23,12),(31,22,6),(33,18,1),(30,13,0),(26,9,0)])),
    "Kochi":    dict(zip(range(1, 13), [(32,23,1),(32,24,1),(33,25,2),(33,26,6),(32,26,12),(29,24,23),(29,23,22),(29,23,18),(30,24,13),(30,24,14),(31,24,8),(32,23,2)])),
    "Delhi":    dict(zip(range(1, 13), [(20,7,2),(24,10,2),(30,15,2),(36,21,1),(40,26,2),(39,28,5),(35,27,12),(34,27,12),(34,25,6),(33,19,1),(28,13,0),(23,8,1)])),
    "Mumbai":   dict(zip(range(1, 13), [(31,19,0),(32,20,0),(33,23,0),(33,25,0),(34,27,1),(32,27,17),(30,26,26),(30,25,24),(31,25,15),(33,24,4),(34,22,1),(33,20,0)])),
    "Varanasi": dict(zip(range(1, 13), [(22,9,1),(26,12,1),(33,17,1),(39,22,0),(41,27,1),(39,29,6),(34,27,14),(33,27,13),(33,26,9),(32,21,2),(29,14,0),(24,10,0)])),
    "Dubai":    dict(zip(range(1, 13), [(24,14,1),(25,15,1),(29,18,1),(33,21,0),(38,25,0),(40,28,0),(41,30,0),(41,30,0),(39,27,0),(35,23,0),(30,19,0),(26,16,1)])),
    "Singapore": _SG,
    "Bangkok":  dict(zip(range(1, 13), [(32,22,2),(33,24,3),(34,26,4),(35,27,6),(34,27,15),(33,26,16),(33,26,17),(32,26,19),(32,25,21),(32,25,16),(31,24,6),(31,22,1)])),
}

# Per-person, per-day spend on food + local transport + activities (INR),
# before applying the destination cost_index.
DAILY_SPEND = {"Budget": 1200, "Moderate": 2200, "Luxury": 5000}

# Hotel star band each travel style prefers.
STYLE_STARS = {"Budget": (2, 3), "Moderate": (3, 4), "Luxury": (4, 5)}

INTERESTS = ["beach", "heritage", "culture", "food", "nature", "adventure",
             "shopping", "nightlife", "spiritual", "art", "family"]


def origins():
    return [c for c, v in CITIES.items() if v["origin"]]


def destinations():
    return [c for c, v in CITIES.items() if v["dest"]]


def haversine_km(a: str, b: str) -> float:
    """Great-circle distance between two catalogued cities."""
    ca, cb = CITIES[a], CITIES[b]
    lat1, lon1, lat2, lon2 = map(radians, [ca["lat"], ca["lon"], cb["lat"], cb["lon"]])
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def is_international(origin: str, dest: str) -> bool:
    return CITIES[origin]["country"] != CITIES[dest]["country"]
