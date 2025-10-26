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
