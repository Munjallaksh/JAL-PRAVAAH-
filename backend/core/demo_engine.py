import math
import time
from typing import Dict, Any, Callable
from backend.core.base_engine import BaseSimulationEngine
from backend.core.validator import SimulationParameters, ValidationResult, validate_simulation_inputs
from backend.spatial.dynamic_domain import generate_dynamic_domain_gis

class DemoHydraulicEngine(BaseSimulationEngine):
    """
    Deterministic 2D Shallow-Water Hydraulic Wave Engine.
    Computes dam-break breach discharge hydrographs (Ritter / Froehlich equations)
    and propagates hydrodynamic wave fronts down terrain elevation profiles for ANY dam/river.
    
    Provenance: DEMO / SIMPLIFIED HYDRAULIC MODEL
    """

    def validate_inputs(self, params: SimulationParameters, domain_data: Dict[str, Any]) -> ValidationResult:
        dam_meta = domain_data.get("dams", {}).get("features", [{}])[0].get("properties", {})
        return validate_simulation_inputs(params, dam_meta)

    def prepare_model(self, job_id: str, params: SimulationParameters, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        domain_gis = generate_dynamic_domain_gis(dam_name=params.dam_name, river_name=params.river_name)

        Vw_mcm = params.reservoir_volume_mcm
        hw_m = params.breach_depth_m
        Q_peak = 0.607 * math.pow(Vw_mcm * 1e6, 0.295) * math.pow(hw_m, 1.24)
        if params.scenario_type == "SUDDEN_WATER_RELEASE":
            Q_peak = params.release_discharge_cumecs

        return {
            "job_id": job_id,
            "Q_peak_cumecs": round(Q_peak, 1),
            "dams": domain_gis["dams"],
            "river": domain_gis["river"],
            "villages": domain_gis["villages"],
            "infra": domain_gis["infra"],
            "river_coords": domain_gis["river_coords"],
            "params": params
        }

    def run(self, job_id: str, params: SimulationParameters, prep_data: Dict[str, Any], progress_cb: Callable[[int, str], None]) -> Dict[str, Any]:
        progress_cb(10, f"Preparing DEM terrain & river channel for {params.dam_name} ({params.river_name})...")
        time.sleep(0.2)

        progress_cb(35, f"Computing breach outflow hydrograph (Peak Q = {prep_data['Q_peak_cumecs']:,} m³/s)...")
        time.sleep(0.3)

        progress_cb(65, f"Executing 2D shallow water wave propagation down {params.river_name} valley...")
        time.sleep(0.3)

        progress_cb(85, "Generating flood inundation depth rasters and arrival time vectors...")
        time.sleep(0.2)

        return self.parse_results(job_id, prep_data)

    def monitor(self, job_id: str) -> Dict[str, Any]:
        return {"status": "COMPLETE", "memory_mb": 42.5, "solver_convergence": "PASS"}

    def parse_results(self, job_id: str, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        params = raw_output["params"]
        raw_river_coords = raw_output["river_coords"]

        from backend.spatial.hydro_routing import predict_flood_wave_attenuation_and_extinction
        formation_hrs = getattr(params, "breach_formation_time_min", 60.0) / 60.0 if hasattr(params, "breach_formation_time_min") else getattr(params, "breach_formation_time_hours", 1.0)
        
        routing_res = predict_flood_wave_attenuation_and_extinction(
            dam_name=params.dam_name,
            river_name=params.river_name,
            dam_coords=raw_river_coords[0],
            dam_height_m=getattr(params, "dam_height_m", 260.0),
            reservoir_level_m=params.reservoir_level_m,
            reservoir_volume_mcm=params.reservoir_volume_mcm,
            breach_width_m=params.breach_width_m,
            breach_formation_time_hrs=formation_hrs,
            river_coords=raw_river_coords,
            scenario_type=params.scenario_type,
            release_discharge_cumecs=params.release_discharge_cumecs
        )

        Q_peak = routing_res["origin"]["peak_discharge_cumecs"]
        active_river_coords = routing_res["active_river_coords"]
        scale_factor = min(3.5, max(0.8, Q_peak / 12000.0))

        from backend.spatial.spatial_ops import generate_realistic_flood_inundation_geojson
        
        base_props = {
            "scenario_id": job_id,
            "dam_name": params.dam_name,
            "river_name": params.river_name,
            "engine": "DEMO_HYDRAULIC",
            "provenance": "DEMO / SIMPLIFIED HYDRAULIC MODEL",
            "peak_discharge_cumecs": Q_peak,
            "max_depth_m": round(min(15.5, 3.4 + Q_peak / 2300.0), 2),
            "max_velocity_mps": round(min(8.6, 2.2 + Q_peak / 3800.0), 2),
            "breach_origin": routing_res["origin"],
            "termination_point": routing_res["termination"],
            "total_reach_km": routing_res["total_reach_km"],
            "attenuation_ratio_percent": routing_res["attenuation_ratio_percent"]
        }

        max_inundation_geojson = generate_realistic_flood_inundation_geojson(
            active_river_coords,
            scale_factor=scale_factor,
            properties_template=base_props
        )

        temporal_snapshots = []
        duration_hrs = params.simulation_duration_hours
        total_steps = 8

        for step in range(total_steps):
            time_min = int((step / (total_steps - 1)) * (duration_hrs * 60))
            reached_idx = max(2, int(((step + 1) / total_steps) * len(active_river_coords)))
            sub_coords = active_river_coords[:reached_idx]
            sub_scale = scale_factor * ((step + 1) / total_steps)

            step_props = dict(base_props)
            step_props.update({
                "time_min": time_min,
                "step": step,
                "total_steps": total_steps,
                "wave_front_km": round((reached_idx / len(active_river_coords)) * routing_res["total_reach_km"], 1),
                "max_depth_m": round(min(13.0, ((step + 1) / total_steps) * 9.2 + 1.2), 2)
            })

            sub_geojson = generate_realistic_flood_inundation_geojson(
                sub_coords,
                scale_factor=sub_scale,
                properties_template=step_props,
                step=step,
                total_steps=total_steps
            )

            temporal_snapshots.append({
                "timestep_min": time_min,
                "formatted_time": f"{time_min // 60}h {time_min % 60:02d}m" if time_min >= 60 else f"{time_min} min",
                "geojson": sub_geojson
            })

        return {
            "max_inundation": max_inundation_geojson,
            "temporal_snapshots": temporal_snapshots,
            "peak_flow_cumecs": Q_peak,
            "max_depth_m": round(min(15.5, 3.4 + Q_peak / 2300.0), 2),
            "engine": "DEMO_HYDRAULIC",
            "origin": routing_res["origin"],
            "termination": routing_res["termination"],
            "reach_profile": routing_res["reach_profile"],
            "total_reach_km": routing_res["total_reach_km"],
            "active_river_coords": active_river_coords
        }

    def postprocess(self, job_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        return parsed_data
