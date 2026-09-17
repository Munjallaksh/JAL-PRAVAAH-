import json

def export_to_geojson(results: dict) -> str:
    """Return GeoJSON string representation of max flood inundation layer."""
    return json.dumps(results.get("max_inundation", {}), indent=2)
