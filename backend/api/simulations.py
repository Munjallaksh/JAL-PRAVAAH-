import os
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.core.validator import SimulationParameters, validate_simulation_inputs
from backend.core.orchestrator import orchestrator
from backend.config import settings

router = APIRouter(prefix="/simulations", tags=["Simulations"])

from backend.spatial.dynamic_domain import generate_dynamic_domain_gis

def _load_domain_data(dam_name: str = None):
    return generate_dynamic_domain_gis(dam_name=dam_name)

@router.post("/run")
def start_simulation(params: SimulationParameters):
    domain_data = _load_domain_data(params.dam_name)
    dam_props = domain_data["dams"]["features"][0]["properties"] if domain_data.get("dams", {}).get("features") else {}
    validation = validate_simulation_inputs(params, dam_props)
    
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors, "warnings": validation.warnings})

    job_id = orchestrator.create_job(params, domain_data)
    return {
        "job_id": job_id,
        "status": "QUEUED",
        "warnings": validation.warnings,
        "message": f"Simulation job {job_id} dispatched to background worker using engine {params.engine_type}."
    }

@router.get("/{job_id}/status")
def get_simulation_status(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Simulation job {job_id} not found.")

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress_percent": job["progress_percent"],
        "current_step": job["current_step"],
        "engine": job["engine"],
        "logs": job["logs"],
        "error": job["error"]
    }

@router.get("/{job_id}/results")
def get_simulation_results(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Simulation job {job_id} not found.")

    if job["status"] != "COMPLETE":
        return {
            "status": job["status"],
            "progress_percent": job["progress_percent"],
            "message": "Simulation is still running or pending completion."
        }

    return job["results"]
