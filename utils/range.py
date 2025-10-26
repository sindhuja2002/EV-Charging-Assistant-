EV_SPECS = {
    "tesla model 3": {"battery_kwh": 57.5, "cons_kwh_per_km": 0.15},
    "tesla model y": {"battery_kwh": 75.0, "cons_kwh_per_km": 0.17},
    "nissan leaf": {"battery_kwh": 40.0, "cons_kwh_per_km": 0.18},
    "hyundai kona": {"battery_kwh": 64.0, "cons_kwh_per_km": 0.16},
    "bmw i4": {"battery_kwh": 83.9, "cons_kwh_per_km": 0.19},
}


DEFAULT = {"battery_kwh": 60.0, "cons_kwh_per_km": 0.17}


ef get_spec(model: str):
    if not model: return DEFAULT
    return EV_SPECS.get(model.lower().strip(), DEFAULT)