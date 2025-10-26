import os, requests

from dotenv import load_dotenv
load_dotenv()

OCM_KEY = os.getenv("OPENCHARGEMAP_API_KEY")



def query_chargers(lat: float, lon: float, radius_km: float = 8.0, maxresults: int = 60, key: str | None = None):
    params = {"output":"json","latitude":lat,"longitude":lon,"distance":radius_km,"distanceunit":"KM","maxresults":maxresults}
    headers = {}; api_key = key or OCM_KEY
    if api_key: headers["X-API-Key"] = api_key
    r = requests.get("https://api.openchargemap.io/v3/poi/", params=params, headers=headers, timeout=30)
    r.raise_for_status(); return r.json()




def status_color(poi: dict) -> str:
    st = poi.get("StatusType") or {}
    if st.get("IsOperational") is True: return "green"
    title = (st.get("Title") or "").lower()
    if "not" in title or "planned" in title or "fault" in title or "removed" in title: return "red"
    return "green"


def summarize(pois: list[dict]) -> list[dict]:
    out = []
    for c in pois:
        addr = c.get("AddressInfo", {}) or {}
        op = c.get("OperatorInfo", {}) or {}
        cons = c.get("Connections", []) or []
        conns = []; max_kw = None
        for conn in cons:
            ctype = (conn.get("ConnectionType", {}) or {}).get("Title")
            kw = conn.get("PowerKW")
            if isinstance(kw, (int,float)): max_kw = max(max_kw or 0, kw)
            conns.append(f"{ctype or 'Unknown'} {int(kw)}kW" if kw else (ctype or "Unknown"))
        
        
        out.append({"title": addr.get("Title","Unknown"),
                    "lat": addr.get("Latitude"), "lon": addr.get("Longitude"),
                    "network": op.get("Title","Unknown"),
                    "connectors": ", ".join([x for x in conns if x]) or "Unknown",
                    "max_power_kw": (int(max_kw) if max_kw else None),
                    "status_color": status_color(c),
                    "google_maps_nav": f"https://www.google.com/maps/dir/?api=1&destination={addr.get('Latitude')},{addr.get('Longitude')}"})
    
    
    
    
    out.sort(key=lambda x: x.get("max_power_kw") or 0, reverse=True); return out