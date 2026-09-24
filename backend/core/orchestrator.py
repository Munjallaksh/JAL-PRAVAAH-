import uuid
import threading
import time
from typing import Dict, Any, Optional
from backend.core.validator import SimulationParameters
from backend.core.demo_engine import DemoHydraulicEngine
from backend.core.sph_engine import SPHEngine
from backend.core.delft3d_engine import Delft3DEngine
from backend.spatial.dynamic_domain import generate_dynamic_domain_gis
from backend.spatial.spatial_ops import perform_impact_analysis
from backend.spatial.hadr_engine import compute_hadr_priorities

class JobOrchestrator:
    """
    Simulation Job System for asynchronous background hydrodynamic runs across ANY Indian dam / river.
    Manages queueing, progress tracking, engine execution, impact analysis, and HADR priority generation.
    """

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.engines = {
            "DEMO_HYDRAULIC": DemoHydraulicEngine(),
            "SPH": SPHEngine(),
            "DELFT3D": Delft3DEngine()
        }

    def create_job(self, params: SimulationParameters, domain_data: Dict[str, Any] = None) -> str:
        job_id = f"SCN-{time.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        
        # Dynamically generate GIS study domain for selected Dam / River
        active_gis = generate_dynamic_domain_gis(dam_name=params.dam_name, river_name=params.river_name)

        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "progress_percent": 0,
            "current_step": "Job queued in background worker...",
            "engine": params.engine_type,
            "params": params.dict(),
            "start_time": time.time(),
            "end_time": None,
            "logs": [f"Job {job_id} created for {params.dam_name} ({params.river_name}) using engine {params.engine_type}"],
            "results": None,
            "error": None
        }

        # Spawn background execution thread
        t = threading.Thread(target=self._run_job_thread, args=(job_id, params, active_gis), daemon=True)
        t.start()

        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    def _run_job_thread(self, job_id: str, params: SimulationParameters, domain_data: Dict[str, Any]):
        job = self.jobs[job_id]
        
        try:
            job["status"] = "PREPARING"
            job["progress_percent"] = 10
            job["current_step"] = f"Preparing terrain DEM & river domain for {params.dam_name}..."
            job["logs"].append(f"Domain GIS generated for {params.dam_name} ({params.river_name}).")
            time.sleep(0.3)

            engine = self.engines.get(params.engine_type, self.engines["DEMO_HYDRAULIC"])

            def update_progress(percent: int, message: str):
                job["progress_percent"] = min(90, max(15, percent))
                job["current_step"] = message
                job["logs"].append(f"[{percent}%] {message}")

            job["status"] = "RUNNING"
            prep_data = engine.prepare_model(job_id, params, domain_data)
            raw_results = engine.run(job_id, params, prep_data, update_progress)

            job["status"] = "POST-PROCESSING"
            job["progress_percent"] = 92
            job["current_step"] = "Performing spatial impact analysis & HADR priority scoring..."
            job["logs"].append("Spatial intersection with population & critical infrastructure.")

            max_flood = raw_results["max_inundation"]
            villages = domain_data.get("villages", {})
            infra = domain_data.get("infra", {})

            impact = perform_impact_analysis(max_flood, villages, infra)
            hadr_priorities = compute_hadr_priorities(impact["affected_villages_detail"], impact)

            job["results"] = {
                "job_id": job_id,
                "dam_name": params.dam_name,
                "river_name": params.river_name,
                "scenario_type": params.scenario_type,
                "max_inundation": max_flood,
                "temporal_snapshots": raw_results["temporal_snapshots"],
                "peak_flow_cumecs": raw_results["peak_flow_cumecs"],
                "max_depth_m": raw_results["max_depth_m"],
                "impact_summary": impact,
                "hadr_priorities": hadr_priorities,
                "engine": params.engine_type,
                "provenance": max_flood["features"][0]["properties"].get("provenance", "SIMULATION OUTPUT")
            }

            job["status"] = "COMPLETE"
            job["progress_percent"] = 100
            job["current_step"] = "Simulation and GIS post-processing complete."
            job["end_time"] = time.time()
            job["logs"].append("Simulation run finished successfully.")

        except Exception as e:
            job["status"] = "FAILED"
            job["error"] = str(e)
            job["logs"].append(f"FATAL ERROR: {str(e)}")

orchestrator = JobOrchestrator()
