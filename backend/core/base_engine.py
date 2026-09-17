from abc import ABC, abstractmethod
from typing import Dict, Any, Callable
from backend.core.validator import SimulationParameters, ValidationResult

class BaseSimulationEngine(ABC):
    """
    Common Abstract Interface for all Hydrodynamic Simulation Engines (SPH, Delft3D, Demo Hydraulic).
    """

    @abstractmethod
    def validate_inputs(self, params: SimulationParameters, domain_data: Dict[str, Any]) -> ValidationResult:
        """Validate input parameters against physical domain constraints."""
        pass

    @abstractmethod
    def prepare_model(self, job_id: str, params: SimulationParameters, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up computational domain, grid, initial water levels, and boundary conditions."""
        pass

    @abstractmethod
    def run(self, job_id: str, params: SimulationParameters, prep_data: Dict[str, Any], progress_cb: Callable[[int, str], None]) -> Dict[str, Any]:
        """Execute the hydrodynamic simulation solver and emit live progress updates."""
        pass

    @abstractmethod
    def monitor(self, job_id: str) -> Dict[str, Any]:
        """Check solver process execution status, memory footprint, and log convergence."""
        pass

    @abstractmethod
    def parse_results(self, job_id: str, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw model particle/mesh output into spatial velocity, depth, and arrival time fields."""
        pass

    @abstractmethod
    def postprocess(self, job_id: str, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate GeoJSON GIS vector layers, rasters, and summary statistics."""
        pass
