import os
import json
from fastapi import APIRouter, Query
from backend.spatial.dynamic_domain import INDIAN_DAMS_DATABASE, generate_dynamic_domain_gis

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/search")
def search_locations(q: str = Query(..., min_length=1, description="Search dam, river, city, village or district")):
    query = q.lower().strip()
    results = []
    
    for loc in INDIAN_DAMS_DATABASE:
        if (query in loc["name"].lower() or 
            query in loc["river"].lower() or 
            query in loc["type"].lower() or 
            query in loc["state"].lower()):
            results.append(loc)

    # If no exact match in pre-indexed database, create dynamic searchable result for query
    if not results:
        title = q.strip().title()
        is_river = "river" in query
        is_dam = "dam" in query or "barrage" in query
        dam_title = title if is_dam else f"{title} Dam"
        river_title = title if is_river else f"{title} River"
        results.append({
            "id": f"loc-dynamic-{abs(hash(query)) % 10000}",
            "name": dam_title,
            "type": "Dam / Reservoir" if is_dam else "River System",
            "state": "National Study Domain",
            "country": "India",
            "river": river_title,
            "lat": 23.5,
            "lng": 78.5,
            "zoom": 12,
            "dam_height_m": 120.0,
            "reservoir_level_m": 450.0,
            "reservoir_volume_mcm": 2400.0,
            "description": f"Dynamically generated study domain for {title} flood simulation."
        })

    return results

@router.get("/domain/{domain_id}")
def get_domain_datasets(domain_id: str = "tehri", dam_name: str = None, river_name: str = None):
    """Return GIS layers dynamically generated for ANY requested dam/river domain."""
    domain_gis = generate_dynamic_domain_gis(dam_name=dam_name or domain_id, river_name=river_name)
    return {
        "dams": domain_gis["dams"],
        "river": domain_gis["river"],
        "villages": domain_gis["villages"],
        "infra": domain_gis["infra"],
        "dam_metadata": domain_gis["dam_metadata"],
        "dam_name": domain_gis.get("dam_name"),
        "river_name": domain_gis.get("river_name")
    }
