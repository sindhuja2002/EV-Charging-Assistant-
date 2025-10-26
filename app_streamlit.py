import os
import streamlit as st
from dotenv import load_dotenv
import folium


from streamlit.components.v1 import html as st_html
from utils.prompt_parser import parse_prompt
from utils.route_utils import get_directions, get_route_points, get_leg_info
from utils.charger_utils import query_chargers, summarize
from utils.range import estimate_range_km, estimate_charge_time_range_minutes, estimate_drive_time_minutes
from utils.places_utils import nearby_places_by_type, directions_points

st.set_page_config(page_title="EV Trip Assistant — v4.10", page_icon="⚡", layout="wide")
load_dotenv()

#  UIHeader (scrolls with page) 
st_html("""
<style>
  .lovable-bg { position: fixed; inset: 0;
    background: linear-gradient(135deg, #3b82f6, #ec4899, #f43f5e, #f59e0b);
    background-size: 400% 400%; animation: grad 12s ease infinite; z-index: -2; }
  @keyframes grad { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }
  .center-wrap { display:flex; flex-direction:column; align-items:center; gap:14px; padding: 24px 16px; }
  .headline { font-size: 40px; font-weight: 800; color: #0f172a; text-shadow: 0 1px 2px rgba(0,0,0,0.1); }
  .subtitle { font-size: 16px; color: #0f172a; opacity: 0.9; }
  .chatbar-wrap { display:flex; align-items:center; gap:12px; width:min(980px, 92vw); }
  .chatbar { display:flex; flex:1; align-items:center; gap:12px;
    background:#0b0b0b; color:#fff; border:1px solid rgba(255,255,255,0.18);
    border-radius: 999px; padding: 10px 14px; box-shadow: 0 12px 34px rgba(0,0,0,0.25); }
  .mic-btn { width:40px; height:40px; border-radius:999px; display:grid; place-items:center; border:1px solid rgba(255,255,255,0.25); cursor:pointer; position:relative; }
  .mic-ring { position:absolute; inset:-6px; border-radius:999px; background: conic-gradient(from 0deg, rgba(236,72,153,.55), rgba(244,63,94,.55), rgba(245,158,11,.55), rgba(236,72,153,.55)); filter: blur(8px); opacity: 0; transition: opacity .2s ease; }
  .mic-btn.listening .mic-ring { opacity:1; animation: pulse 1.2s ease-in-out infinite; }
  @keyframes pulse { 0%{ transform: scale(1); opacity:.7;} 50%{ transform: scale(1.06); opacity:1;} 100%{ transform: scale(1); opacity:.7;} }
  .listen { text-align:center; color:#0f172a; font-size:12px; min-height:18px; }
</style>
<div class="lovable-bg"></div>
<div class="center-wrap">
  <div class="headline">Build your next EV Trip Assistant ⚡</div>
  <div class="subtitle">Plan your charge stops and activities in the meantime — by just chatting</div>
</div>
""", height=160)


# Chat bar
with st.form("trip_form", clear_on_submit=False):
    st_html("""
    <div style='display:flex;justify-content:center;margin-top:-20px;'>
      <div style='display:flex;align-items:center;gap:10px;background:#0b0b0b;
                  color:#fff;border-radius:999px;padding:10px 16px;width:min(980px,92vw);
                  box-shadow:0 10px 28px rgba(0,0,0,0.25);'>
        <div id='mic' class='mic-btn' title='Voice input' 
             style='background:rgba(255,255,255,0.08);border-radius:50%;padding:6px;cursor:pointer;position:relative;'>
          <div class='mic-ring'></div>
          <svg width='20' height='20' viewBox='0 0 24 24' fill='#fff' xmlns='http://www.w3.org/2000/svg'>
            <path d='M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 14 0h-2Z'/>
            <path d='M13 19.938V22h-2v-2.062A8.01 8.01 0 0 1 4 12h2a6 6 0 0 0 12 0h2a8.01 8.01 0 0 1-7 7.938Z'/>
          </svg>
        </div>
        <script>
          function setTripText(val){
            const inp = window.parent.document.querySelector('input[placeholder="Helsinki to Lahti, 20% charge, Tesla Model 3"]');
            if (inp){ inp.value = val; inp.dispatchEvent(new Event('input', { bubbles: true })); }
          }
          const mic = document.getElementById('mic');
          let rec=null;
          if('webkitSpeechRecognition' in window || 'SpeechRecognition' in window){
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            rec = new SR(); rec.lang='en-US'; rec.interimResults=false; rec.maxAlternatives=1;
            rec.onstart=()=>{ mic.style.boxShadow='0 0 10px #f43f5e'; };
            rec.onend=()=>{ mic.style.boxShadow='none'; };
            rec.onerror=()=>{ mic.style.boxShadow='none'; };
            rec.onresult=(e)=>{ const text=e.results[0][0].transcript; setTripText(text); };
            mic.addEventListener('click', ()=>{ try{ rec.start(); }catch(e){} });
          } else { mic.style.opacity=0.5; mic.title='Speech recognition not supported in this browser'; }
        </script>
    """, height=80)
    trip_text = st.text_input(
        label="Trip input",
        value=st.session_state.get("last_prompt", ""),
        key="trip_text",
        placeholder="Helsinki to Lahti, 20% charge, Tesla Model 3",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Trip Planner", use_container_width=False)

#main logic
def pick_point(pts, frac: float):
    idx = max(0, min(len(pts)-1, int(len(pts)*frac)))
    return pts[idx]


def rating_stars(r):
    if r is None: return ""
    full = int(round(float(r))); return "⭐"*max(1, min(full, 5))


def render_charging_section(pts, info, model, soc):
    total_km = info["distance_km"]; total_min = info["duration_min"]
    rng = estimate_range_km(model, soc); rng_drive_min = estimate_drive_time_minutes(rng)
    mn, mx = estimate_charge_time_range_minutes(model, soc)

    st.markdown("### 🔋 Wanna know Something Interesting")
    st.success(f"**a)** Total journey: **{total_km:.1f} km** · **~{total_min:.0f} min**\n\n"
               f"**b)** With **{soc}%** in your **{model}**, you can ride about **{rng:.0f} km** (~**{rng_drive_min} min** at 60 km/h)\n\n"
               f"**c)** To reach 100% from {soc}%: **~{mn}–{mx} minutes** (150kW → 50kW fast chargers)")

    tiers = [
        ("First slow charger point Suggestions", 0.25, lambda kw: (kw or 0) < 50),
        ("Second medium charger point Suggestions", 0.5, lambda kw: 50 <= (kw or 0) < 150),
        ("Third fast charger point Suggestions", 0.75, lambda kw: (kw or 0) >= 150),
    ]
    for title, frac, pred in tiers:
        with st.expander(f"🔽 {title}", expanded=False):
            lat, lon = pick_point(pts, frac)
            raw = query_chargers(lat, lon, radius_km=8.0, maxresults=60)
            chargers = [c for c in summarize(raw) if pred(c.get("max_power_kw"))]
            if not chargers:
                st.warning("No chargers found for this power tier near this segment."); continue
            m = folium.Map(location=[lat, lon], zoom_start=11, control_scale=True)
            folium.CircleMarker([lat, lon], radius=3, color="#333", fill=True, fill_opacity=0.8, tooltip="Suggestion center").add_to(m)
            for ch in chargers[:40]:
                tooltip = f"{ch['title']} ({ch['network']})"
                popup = f"""<b>⚡ {ch['title']}</b><br>
Network: {ch['network']}<br>
Connectors: {ch['connectors']}<br>
Max power: {ch.get('max_power_kw','?')} kW<br>
<a href='{ch['google_maps_nav']}' target='_blank'>Navigate in Google Maps</a>"""
                icon_color = "green" if ch.get("status_color") == "green" else "red"
                folium.Marker([ch["lat"], ch["lon"]], tooltip=tooltip, popup=popup,
                              icon=folium.Icon(color=icon_color, icon="bolt")).add_to(m)
            st_html(m.get_root().render(), height=440)



def render_activity_section(pts):
    st.markdown("---")
    st.markdown("### Hey Babe, What would you like to do while charging?")
    c1 = st.button("☕ Café", use_container_width=True)
    c2 = st.button("🍽️ Restaurant", use_container_width=True)
    c3 = st.button("🛍️ Shopping Mall", use_container_width=True)
    c4 = st.button("🏬 Department Store", use_container_width=True)
    c5 = st.button("🎡 Tourist Spot", use_container_width=True)
    type_map = {"cafe": c1, "restaurant": c2, "shopping_mall": c3, "department_store": c4, "tourist_attraction": c5}
    chosen = None
    for t, pressed in type_map.items():
        if pressed:
            chosen = t; break
    if chosen:
        st.session_state["activity"] = chosen

    if not st.session_state.get("activity"):
        return

    with st.spinner("Planning your trip..."):
        label_map = {"cafe":"Café","restaurant":"Restaurant","shopping_mall":"Shopping Mall","department_store":"Department Store","tourist_attraction":"Tourist Spot"}
        act_label = label_map.get(st.session_state["activity"], st.session_state["activity"].title())
        seg_points = [pick_point(pts, 0.25), pick_point(pts, 0.5), pick_point(pts, 0.75)]
        all_places = []
        for lat, lon in seg_points:
            places = nearby_places_by_type(lat, lon, ptype=st.session_state["activity"], radius_m=4000, per_type=4)
            all_places.append(places)
        total_found = sum(len(x) for x in all_places)
        st.markdown("###  Wanna know Interesting Activitiy Spots Nearby")
        st.info(f"Found **{total_found} {act_label.lower()}s** along your route.")

        titles = [f"First {act_label} Suggestions", f"Second {act_label} Suggestions", f"Third {act_label} Suggestions"]
        for title, seg_places, (seg_lat, seg_lon) in zip(titles, all_places, seg_points):
            with st.expander(f"🔽 {title}", expanded=False):
                if not seg_places:
                    st.warning(f"No {act_label.lower()}s near this segment."); continue
                for p in seg_places:
                    name = p["name"]
                    hours = " / ".join(p.get("hours", [])[:2]) if p.get("hours") else "Hours not available"
                    stars = " " + ("· " + ("⭐"*max(1, min(int(round(float(p.get('rating') or 0))), 5)))) if p.get("rating") else ""
                    st.markdown(f"**{name}**{stars}")
                    st.caption(hours)

                    raw = query_chargers(p["lat"], p["lon"], radius_km=6.0, maxresults=40)
                    chargers = summarize(raw)
                    if not chargers:
                        st.warning("No nearby chargers found for this place."); continue
                    ch = chargers[0]
                    ic = "green" if ch.get("status_color") == "green" else "red"

                    cols = st.columns(2, gap="large")
                    with cols[0]:
                        m1 = folium.Map(location=[p["lat"], p["lon"]], zoom_start=13, control_scale=True)
                        folium.Marker([p["lat"], p["lon"]], popup=f"{p['name']}<br><a href='{p['gmaps']}' target='_blank'>Open in Google Maps</a>", icon=folium.Icon(color="red", icon="info-sign")).add_to(m1)
                        pop = f"""<b>⚡ {ch['title']}</b><br>
Network: {ch['network']}<br>
Connectors: {ch['connectors']}<br>
Max power: {ch.get('max_power_kw','?')} kW<br>
<a href='{ch['google_maps_nav']}' target='_blank'>Navigate to charger</a>"""
                        folium.Marker([ch["lat"], ch["lon"]], popup=pop, icon=folium.Icon(color=ic, icon="bolt")).add_to(m1)
                        st_html(m1.get_root().render(), height=360)
                    with cols[1]:
                        route_pts = directions_points(ch["lat"], ch["lon"], p["lat"], p["lon"])
                        if route_pts:
                            mid = route_pts[len(route_pts)//2]
                            m2 = folium.Map(location=[mid[0], mid[1]], zoom_start=13, control_scale=True)
                            folium.PolyLine(route_pts, weight=4).add_to(m2)
                            folium.Marker([ch["lat"], ch["lon"]], tooltip="Charger", icon=folium.Icon(color=ic, icon="bolt")).add_to(m2)
                            folium.Marker([p["lat"], p["lon"]], tooltip=p["name"], icon=folium.Icon(color="red", icon="info-sign")).add_to(m2)
                            st_html(m2.get_root().render(), height=360)
                        else:
                            st.warning("No route found from charger to this place.")
                    st.markdown("---")

# Trip render control 
if submitted and trip_text.strip():
    with st.spinner("Planning your trip..."):
        st.session_state["last_prompt"] = trip_text.strip()
        parsed = parse_prompt(st.session_state["last_prompt"])
        model = parsed.get("model") or "Tesla Model 3"
        soc = parsed.get("soc") if parsed.get("soc") is not None else 40
        start = parsed.get("start"); dest = parsed.get("dest")
        if not (start and dest):
            st.error("I couldn't detect **start** and **destination**. Please type like: *Helsinki to Lahti, 20% charge, Tesla Model 3*.")
        else:
            dirs = get_directions(start, dest)
            info = get_leg_info(dirs); pts = get_route_points(dirs)
            st.session_state["last_route"] = {"pts": pts, "info": info, "model": model, "soc": soc}
    # Render after spinner
    if st.session_state.get("last_route"):
        render_charging_section(st.session_state["last_route"]["pts"],
                                st.session_state["last_route"]["info"],
                                st.session_state["last_route"]["model"],
                                st.session_state["last_route"]["soc"])
        render_activity_section(st.session_state["last_route"]["pts"])

# Re-render last state if present (when user scrolls or clicks activity without resubmitting)
elif st.session_state.get("last_route"):
    render_charging_section(st.session_state["last_route"]["pts"],
                            st.session_state["last_route"]["info"],
                            st.session_state["last_route"]["model"],
                            st.session_state["last_route"]["soc"])
    render_activity_section(st.session_state["last_route"]["pts"])
