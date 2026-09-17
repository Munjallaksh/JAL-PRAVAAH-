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
        results.append({
            "id": f"loc-dynamic-{hash(query) % 10000}",
            "name": f"{q.title()} Scenario Domain",
            "type": "Dam / River System",
            "state": "India",
            "country": "India",
            "river": f"{q.title()} River",
            "lat": 22.5,
            "lng": 78.5,
            "zoom": 12,
            "dam_height_m": 120.0,
            "reservoir_level_m": 450.0,
            "reservoir_volume_mcm": 2400.0,
            "description": f"Dynamically generated study domain for {q} flood simulation."
        })

    return results

@router.get("/domain/{domain_id}")
def get_domain_datasets(domain_id: str = "tehri", dam_name: str = None):
    """Return GIS layers dynamically generated for ANY requested dam/river domain."""
    domain_gis = generate_dynamic_domain_gis(dam_name=dam_name or domain_id)
    return {
        "dams": domain_gis["dams"],
        "river": domain_gis["river"],
        "villages": domain_gis["villages"],
        "infra": domain_gis["infra"],
        "dam_metadata": domain_gis["dam_metadata"]
    }
