EV_SPECS = {
    "tesla model 3": {"battery_kwh": 57.5, "cons_kwh_per_km": 0.15},
    "tesla model y": {"battery_kwh": 75.0, "cons_kwh_per_km": 0.17},
    "nissan leaf": {"battery_kwh": 40.0, "cons_kwh_per_km": 0.18},
    "hyundai kona": {"battery_kwh": 64.0, "cons_kwh_per_km": 0.16},
    "bmw i4": {"battery_kwh": 83.9, "cons_kwh_per_km": 0.19},
}


DEFAULT = {"battery_kwh": 60.0, "cons_kwh_per_km": 0.17}


def get_spec(model: str):
    if not model: return DEFAULT
    return EV_SPECS.get(model.lower().strip(), DEFAULT)


def estimate_range_km(model: str, soc: float) -> float:
    s = get_spec(model); total_km = s["battery_kwh"]/s["cons_kwh_per_km"]
    return round(total_km*(soc/100.0), 1)


def estimate_charge_time_range_minutes(model: str, soc: float, to_soc: float = 100.0, min_kw=50, max_kw=150) -> tuple[int,int]:
    s = get_spec(model); need_kwh = s["battery_kwh"]*max(0,(to_soc-soc))/100.0
    if need_kwh <= 0: return (0, 0)
    return (int(round((need_kwh/max_kw)*60)), int(round((need_kwh/min_kw)*60)))