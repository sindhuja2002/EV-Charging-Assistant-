import os, requests, polyline
from dotenv import load_dotenv
load_dotenv()
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")



def _ck(key):
    if not key: raise RuntimeError("Missing GOOGLE_API_KEY. Add it to .env")


def get_directions(start: str, dest: str, key: str | None = None) -> dict:
    api_key = key or GOOGLE_KEY; _ck(api_key)
    url = ("https://maps.googleapis.com/maps/api/directions/json"
           f"?origin={start}&destination={dest}&key={api_key}")
    r = requests.get(url, timeout=30); r.raise_for_status()
    data = r.json()
    if not data.get("routes"): raise ValueError("No route found from Google Directions API.")
    return data



def get_route_points(dirs: dict):
    pts = dirs["routes"][0]["overview_polyline"]["points"]
    return polyline.decode(pts)



def get_leg_info(dirs: dict):
    leg = dirs["routes"][0]["legs"][0]
    return {"distance_km": leg["distance"]["value"]/1000.0,
            "duration_min": leg["duration"]["value"]/60.0,
            "start_address": leg.get("start_address",""),
            "end_address": leg.get("end_address","")}
