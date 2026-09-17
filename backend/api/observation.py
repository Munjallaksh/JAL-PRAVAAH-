import os
import json
from fastapi import APIRouter
from backend.config import settings
from backend.spatial.validation_metrics import compute_spatial_validation
from backend.core.orchestrator import orchestrator

router = APIRouter(prefix="/observation", tags=["Satellite Observation"])

@router.get("/sentinel1")
def get_sentinel1_observation():
    """Return pre-processed Sentinel-1 SAR change detection flood observation layer."""
    path = os.path.join(settings.DATA_DIR, "Sentinel1_Sample.geojson")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

@router.get("/validate/{job_id}")
def validate_model_against_satellite(job_id: str):
    """Compute spatial validation metrics (IoU, Precision, Recall, F1 Score) between modeled flood & satellite observation."""
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        return {
            "available": False,
            "reason": f"Simulation scenario {job_id} is not complete."
        }

    modeled_geojson = job["results"]["max_inundation"]
    path = os.path.join(settings.DATA_DIR, "Sentinel1_Sample.geojson")
    if not os.path.exists(path):
        return {"available": False, "reason": "Sentinel-1 observation data file not found."}

    with open(path, "r", encoding="utf-8") as f:
        observed_geojson = json.load(f)

    return compute_spatial_validation(modeled_geojson, observed_geojson)
