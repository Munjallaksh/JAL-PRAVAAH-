from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SimulationParameters(BaseModel):
    scenario_type: str = Field(..., description="DAM_BREAK, SUDDEN_WATER_RELEASE, NATURAL_RIVER_BLOCKAGE, LAKE_OUTBURST")
    dam_name: str = "Tehri Dam"
    river_name: str = "Bhagirathi River"
    reservoir_level_m: float = 820.0
    reservoir_volume_mcm: float = 3540.0
    dam_height_m: float = 260.5
    breach_width_m: float = 100.0
    breach_depth_m: float = 150.0
    breach_formation_time_min: float = 30.0
    release_discharge_cumecs: float = 8000.0
    release_duration_hours: float = 4.0
    mannings_n: float = 0.035
    simulation_duration_hours: float = 6.0
    timestep_minutes: float = 15.0
    engine_type: str = Field("SPH", description="SPH, DELFT3D, DEMO_HYDRAULIC")

class ValidationResult(BaseModel):
    is_valid: bool = True
    errors: List[str] = []
    warnings: List[str] = []

def validate_simulation_inputs(params: SimulationParameters, dam_metadata: Dict[str, Any] = None) -> ValidationResult:
    """Validate hydraulic simulation input parameters and check for physical consistency."""
    errors = []
    warnings = []

    if params.simulation_duration_hours <= 0:
        errors.append("Simulation duration must be greater than 0 hours.")

    if params.mannings_n < 0.01 or params.mannings_n > 0.15:
        warnings.append(f"Manning's roughness coefficient n={params.mannings_n} is outside standard open-channel hydraulic ranges (0.015 - 0.08).")

    if params.scenario_type == "DAM_BREAK":
        if params.breach_width_m <= 0:
            errors.append("Breach width must be a positive value.")
        if dam_metadata:
            dam_length = dam_metadata.get("length_m", 575.0)
            if params.breach_width_m > dam_length:
                warnings.append(f"Warning: breach width ({params.breach_width_m}m) exceeds total configured dam crest length ({dam_length}m).")
            dam_height = dam_metadata.get("height_m", 260.5)
            if params.breach_depth_m > dam_height:
                warnings.append(f"Warning: breach depth ({params.breach_depth_m}m) exceeds total dam height ({dam_height}m).")

        if params.breach_formation_time_min <= 0:
            errors.append("Breach formation time must be greater than 0 minutes.")
        elif params.breach_formation_time_min < 5.0:
            warnings.append("Breach formation time is under 5 minutes; this represents an instantaneous catastrophic breach.")

    elif params.scenario_type == "SUDDEN_WATER_RELEASE":
        if params.release_discharge_cumecs <= 0:
            errors.append("Release discharge must be positive.")
        if params.release_discharge_cumecs > 50000:
            warnings.append("Release discharge exceeds 50,000 m³/s; extreme hydraulic spillway volume.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
