"""
Simulated travel inventory ("mock APIs").

Real flight/hotel APIs (Amadeus, Skyscanner, Booking.com) need paid or
approved partner keys, so the prototype uses a deterministic simulator that
behaves like an API: same query -> same results, prices react to distance,
days-to-departure, weekends and destination cost level.

Swap `search_flights` / `search_hotels` for a real provider later without
changing the agents (they only depend on the returned dict shape).
"""

import hashlib
import random
from datetime import date, datetime, timedelta

from data import CITIES, haversine_km, is_international

DOMESTIC_AIRLINES = [("IndiGo", "6E"), ("Air India", "AI"), ("Akasa Air", "QP"),
                     ("Air India Express", "IX"), ("SpiceJet", "SG")]
INTL_AIRLINES = {
    "Dubai": [("Emirates", "EK"), ("IndiGo", "6E"), ("Air India", "AI"), ("flydubai", "FZ")],
    "Singapore": [("Singapore Airlines", "SQ"), ("IndiGo", "6E"), ("Air India", "AI"), ("Scoot", "TR")],
    "Bangkok": [("Thai Airways", "TG"), ("IndiGo", "6E"), ("Air India", "AI"), ("Thai AirAsia", "FD")],
}

HOTEL_AREAS = {
    "Goa": ["Calangute", "Candolim", "Panaji", "Anjuna", "Palolem", "Colva"],
    "Jaipur": ["C-Scheme", "Old City (Pink City)", "Bani Park", "Amer Road", "Malviya Nagar"],
    "Udaipur": ["Lake Pichola", "Lal Ghat", "Fateh Sagar", "Hiran Magri", "Ambamata"],
    "Kochi": ["Fort Kochi", "Marine Drive", "MG Road", "Mattancherry", "Kakkanad"],
    "Varanasi": ["Assi Ghat", "Dashashwamedh", "Godowlia", "Cantonment", "Sarnath"],
    "Delhi": ["Connaught Place", "Paharganj", "Aerocity", "Karol Bagh", "South Delhi"],
    "Mumbai": ["Colaba", "Bandra", "Juhu", "Andheri", "Lower Parel"],
    "Dubai": ["Deira", "Bur Dubai", "Dubai Marina", "Downtown", "Jumeirah"],
    "Singapore": ["Marina Bay", "Little India", "Chinatown", "Orchard", "Bugis"],
    "Bangkok": ["Sukhumvit", "Silom", "Riverside", "Siam", "Khao San"],
}
HOTEL_PREFIX = ["Sea Breeze", "Heritage", "Royal", "Lotus", "Palm Grove", "Urban Nest",
                "Sunrise", "Crescent", "Banyan", "Coral", "Amber", "Saffron", "Orchid", "Harbour"]
HOTEL_SUFFIX = {2: ["Inn", "Stay", "Hostel & Rooms"], 3: ["Residency", "Hotel", "Suites"],
                4: ["Grand", "Boutique Hotel", "Resort"], 5: ["Palace", "Luxury Resort", "Grand Hotel & Spa"]}
AMENITIES = ["Free Wi-Fi", "Breakfast included", "Pool", "Airport shuttle", "Gym",
             "Spa", "Sea/Lake view", "Free cancellation", "Family rooms", "24h front desk"]
BASE_NIGHT = {2: 1800, 3: 3500, 4: 6500, 5: 13000}  # INR per room-night at cost_index 1.0


def _rng(*parts) -> random.Random:
    seed = int(hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def _as_date(d) -> date:
    return d if isinstance(d, date) else datetime.strptime(str(d), "%Y-%m-%d").date()


def search_flights(origin: str, dest: str, travel_date, travellers: int = 1, today=None) -> list[dict]:
    """Return ~7 flight options for one direction on one date (price is per person, INR)."""
    travel_date = _as_date(travel_date)
    today = _as_date(today) if today else date.today()
    km = haversine_km(origin, dest)
    intl = is_international(origin, dest) or is_international(dest, origin)
    rng = _rng("F", origin, dest, travel_date.isoformat())

    if intl:
        intl_city = dest if CITIES[dest]["country"] != "India" else origin
        airlines = INTL_AIRLINES.get(intl_city, DOMESTIC_AIRLINES)
        base = 5000 + 3.2 * km
    else:
        airlines = DOMESTIC_AIRLINES
        base = 2000 + 3.2 * km

    days_out = max((travel_date - today).days, 0)
    if days_out < 7:
        demand = 1.55
    elif days_out < 21:
        demand = 1.20
    elif days_out < 60:
        demand = 1.00
    else:
        demand = 0.92
    if travel_date.weekday() in (4, 5, 6):
        demand *= 1.08

    flights = []
    for i in range(7):
        name, code = rng.choice(airlines)
        stops = 0 if rng.random() < (0.65 if km < 1800 else 0.5) else 1
        hour = rng.choice([5, 6, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23])
        minute = rng.choice([0, 10, 25, 40, 55])
        dur_min = int(km / 720 * 60 + 35 + (rng.randint(95, 210) if stops else rng.randint(0, 20)))
        dep = datetime.combine(travel_date, datetime.min.time()).replace(hour=hour, minute=minute)
        arr = dep + timedelta(minutes=dur_min)
        price = base * demand * rng.uniform(0.82, 1.30) * (0.85 if stops else 1.0)
        if name in ("Emirates", "Singapore Airlines", "Thai Airways"):
            price *= 1.25
        if hour in (5, 23):
            price *= 0.9  # red-eye discount
        flights.append({
            "id": f"{code}{rng.randint(100, 989)}-{travel_date:%m%d}",
            "airline": name,
            "flight_no": f"{code} {rng.randint(100, 989)}",
            "from": origin, "to": dest,
            "from_iata": CITIES[origin]["iata"], "to_iata": CITIES[dest]["iata"],
            "date": travel_date.isoformat(),
            "depart": dep.strftime("%H:%M"),
            "arrive": arr.strftime("%H:%M") + (" (+1)" if arr.date() > dep.date() else ""),
            "duration_min": dur_min,
            "stops": stops,
            "price_pp": int(round(price, -1)),
            "total_price": int(round(price, -1)) * travellers,
            "baggage": "15 kg check-in" if not intl else "25-30 kg check-in",
            "refundable": rng.random() < 0.3,
            "source": "simulated",
        })
    return sorted(flights, key=lambda f: f["price_pp"])


def search_hotels(city: str, check_in, check_out, travellers: int = 1) -> list[dict]:
    """Return ~10 hotels; price is per room-night (INR). Rooms = ceil(travellers/2)."""
    check_in, check_out = _as_date(check_in), _as_date(check_out)
    nights = max((check_out - check_in).days, 1)
    rooms = -(-travellers // 2)
    rng = _rng("H", city, check_in.isoformat())
    cost_index = CITIES[city]["cost_index"]
    peak = 1.25 if check_in.month in (12, 1) or (check_in.month == 5 and city not in ("Dubai",)) else 1.0
    if city in ("Goa", "Kochi") and check_in.month in (6, 7, 8):
        peak = 0.75  # monsoon off-season

    used, hotels = set(), []
    stars_plan = [2, 2, 3, 3, 3, 4, 4, 4, 5, 5]
    for i, stars in enumerate(stars_plan):
        while True:
            name = f"{rng.choice(HOTEL_PREFIX)} {rng.choice(HOTEL_SUFFIX[stars])}"
            if name not in used:
                used.add(name)
                break
        nightly = BASE_NIGHT[stars] * cost_index * peak * rng.uniform(0.8, 1.25)
        rating = round(min(4.9, max(3.2, rng.gauss(3.4 + 0.3 * stars, 0.25))), 1)
        amen = rng.sample(AMENITIES, k=min(len(AMENITIES), 2 + stars))
        hotels.append({
            "id": f"H-{city[:3].upper()}-{i + 1:02d}",
            "name": name,
            "city": city,
            "area": rng.choice(HOTEL_AREAS.get(city, ["City Centre"])),
            "stars": stars,
            "rating": rating,
            "reviews": rng.randint(80, 4200),
            "price_per_night": int(round(nightly, -1)),
            "rooms": rooms,
            "nights": nights,
            "total_price": int(round(nightly, -1)) * rooms * nights,
            "amenities": amen,
            "free_cancellation": "Free cancellation" in amen,
            "source": "simulated",
        })
    return sorted(hotels, key=lambda h: h["price_per_night"])
