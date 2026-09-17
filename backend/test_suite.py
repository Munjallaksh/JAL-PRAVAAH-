import unittest
from backend.core.validator import SimulationParameters, validate_simulation_inputs
from backend.core.demo_engine import DemoHydraulicEngine
from backend.core.sph_engine import SPHEngine
from backend.core.delft3d_engine import Delft3DEngine
from backend.spatial.crs_utils import calculate_metric_area_sqkm, haversine_distance_km
from backend.spatial.spatial_ops import perform_impact_analysis
from backend.spatial.hadr_engine import compute_hadr_priorities
from backend.spatial.validation_metrics import compute_spatial_validation

class TestFloodPlatform(unittest.TestCase):

    def test_input_validation(self):
        params = SimulationParameters(
            scenario_type="DAM_BREAK",
            breach_width_m=100.0,
            breach_formation_time_min=30.0,
            simulation_duration_hours=6.0,
            engine_type="SPH"
        )
        res = validate_simulation_inputs(params, {"length_m": 575.0, "height_m": 260.5})
        self.assertTrue(res.is_valid)

    def test_sph_engine_execution(self):
        engine = SPHEngine()
        params = SimulationParameters(scenario_type="DAM_BREAK", breach_width_m=100.0, engine_type="SPH")
        prep = engine.prepare_model("TEST-001", params, {})
        output = engine.parse_results("TEST-001", prep)
        self.assertIn("max_inundation", output)
        self.assertGreater(output["peak_flow_cumecs"], 0)

    def test_spatial_impact_and_hadr(self):
        engine = DemoHydraulicEngine()
        params = SimulationParameters(scenario_type="DAM_BREAK", breach_width_m=100.0, engine_type="DEMO_HYDRAULIC")
        prep = engine.prepare_model("TEST-002", params, {})
        output = engine.parse_results("TEST-002", prep)
        
        # Test spatial ops
        mock_villages = {
            "features": [
                {
                    "type": "Feature",
                    "properties": {"id": "v1", "name": "Test Village A", "population": 1500, "distance_downstream_km": 10.0, "criticality": "HIGH", "hospital_count": 1},
                    "geometry": {"type": "Point", "coordinates": [78.489, 30.365]}
                }
            ]
        }
        mock_infra = {"features": []}

        impact = perform_impact_analysis(output["max_inundation"], mock_villages, mock_infra)
        self.assertGreaterEqual(impact["inundated_area_sqkm"], 0)

        priorities = compute_hadr_priorities(impact["affected_villages_detail"], impact)
        self.assertGreater(len(priorities), 0)
        self.assertEqual(priorities[0]["name"], "Test Village A")

if __name__ == "__main__":
    unittest.main()
