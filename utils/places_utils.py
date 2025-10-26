import os, requests, polyline

from dotenv import load_dotenv
load_dotenv()

GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")


def _ck(key):
    if not key: raise RuntimeError("Missing GOOGLE_API_KEY. Add it to .env")

def nearby_places_by_type(lat: float, lon: float, ptype: str, radius_m: int = 4000, per_type: int = 4, key: str | None = None):
    api_key = key or GOOGLE_KEY; _ck(api_key)
    url = ("https://maps.googleapis.com/maps/api/place/nearbysearch/json"
           f"?location={lat},{lon}&radius={radius_m}&type={ptype}&key={api_key}")
    

    r = requests.get(url, timeout=30); r.raise_for_status()
    data = r.json(); results = []
    for p in data.get("results", [])[:per_type]:
        place_id = p.get("place_id"); name = p.get("name")
        det_url = ("https://maps.googleapis.com/maps/api/place/details/json"
                   f"?place_id={place_id}&fields=name,opening_hours,rating&key={api_key}")
        d = requests.get(det_url, timeout=20).json()
        opening = (d.get("result", {}) or {}).get("opening_hours", {}) or {}
        results.append({
            "name": name,
            "place_id": place_id,
            "rating": p.get("rating"),
            "lat": p.get("geometry", {}).get("location", {}).get("lat"),
            "lon": p.get("geometry", {}).get("location", {}).get("lng"),
            "open_now": opening.get("open_now"),
            "hours": opening.get("weekday_text", []),
            "gmaps": f"https://www.google.com/maps/search/?api=1&query={name.replace(' ','+') if name else ''}",
        })
    return results



def directions_points(origin_lat, origin_lon, dest_lat, dest_lon, key: str | None = None):
    api_key = key or GOOGLE_KEY; _ck(api_key)
    url = ("https://maps.googleapis.com/maps/api/directions/json"
           f"?origin={origin_lat},{origin_lon}&destination={dest_lat},{dest_lon}&key={api_key}")
    



    r = requests.get(url, timeout=30); r.raise_for_status(); data = r.json()
    if not data.get("routes"): return []
    pts = data["routes"][0]["overview_polyline"]["points"]; return polyline.decode(pts)