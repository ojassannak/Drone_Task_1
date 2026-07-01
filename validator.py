import json
import jsonschema

MAX_ALTITUDE_M = 50
MAX_SPEED_M_S  = 15
MAX_OFFSET_M   = 500

def validate_mission(raw: dict, schema_path="schema.json") -> tuple:

    # check if LLM itself flagged an error
    if "error" in raw:
        return False, f"LLM refused: {raw['error']}"

    # check JSON schema structure
    with open(schema_path) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(raw, schema)
    except jsonschema.ValidationError as e:
        return False, f"Schema invalid: {e.message}"

    # hard safety rules — LLM cannot override these
    if raw["altitude_m"] > MAX_ALTITUDE_M:
        return False, f"altitude {raw['altitude_m']}m exceeds ceiling {MAX_ALTITUDE_M}m"

    if raw["speed_m_s"] > MAX_SPEED_M_S:
        return False, f"speed {raw['speed_m_s']}m/s exceeds limit {MAX_SPEED_M_S}m/s"

    for i, wp in enumerate(raw["waypoints"]):
        dist = (wp["lat_offset_m"]**2 + wp["lon_offset_m"]**2) ** 0.5
        if dist > MAX_OFFSET_M:
            return False, f"waypoint {i} is {dist:.0f}m from home, exceeds {MAX_OFFSET_M}m geofence"

    return True, raw
