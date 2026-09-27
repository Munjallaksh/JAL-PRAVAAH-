import unittest
from backend.spatial.hydro_routing import (
    predict_flood_wave_attenuation_and_extinction,
    haversine_km,
    get_river_regime
)

class TestHydroRoutingSolver(unittest.TestCase):

    def setUp(self):
        self.tehri_coords = [
            [78.4803, 30.3781], [78.5020, 30.3540], [78.5280, 30.2780],
            [78.5610, 30.2210], [78.5980, 30.1470], [78.5520, 30.1210],
            [78.4820, 30.1150], [78.4120, 30.1080], [78.3450, 30.1340],
            [78.2980, 30.1020], [78.2676, 30.0869], [78.2480, 30.0410],
            [78.2120, 29.9850], [78.1642, 29.9457], [78.1320, 29.9010]
        ]

    def test_haversine_calculation(self):
        """Verify geodesic distance calculation between Tehri and Devprayag."""
        d = haversine_km([78.4803, 30.3781], [78.5980, 30.1470])
        self.assertTrue(25.0 < d < 40.0)

    def test_river_regime_lookup(self):
        """Verify hydraulic parameters for major Indian rivers."""
        bhagirathi = get_river_regime("Bhagirathi River")
        self.assertEqual(bhagirathi["bankfull_cumecs"], 1400.0)
        self.assertTrue(bhagirathi["slope_canyon"] > bhagirathi["slope_plain"])

        sutlej = get_river_regime("Sutlej River")
        self.assertEqual(sutlej["bankfull_cumecs"], 2200.0)

    def test_dam_breach_origin_coordinates(self):
        """Verify that flood wave starts exactly at the dam breach point."""
        res = predict_flood_wave_attenuation_and_extinction(
            dam_name="Tehri Dam",
            river_name="Bhagirathi River",
            dam_coords=[78.4803, 30.3781],
            dam_height_m=260.5,
            reservoir_level_m=820.0,
            reservoir_volume_mcm=3540.0,
            breach_width_m=200.0,
            breach_formation_time_hrs=2.0,
            river_coords=self.tehri_coords
        )

        origin = res["origin"]
        self.assertEqual(origin["coords"], [78.4803, 30.3781])
        self.assertEqual(origin["dam_name"], "Tehri Dam")
        self.assertTrue(origin["peak_discharge_cumecs"] > 10000.0)
        self.assertEqual(res["active_river_coords"][0], [78.4803, 30.3781])

    def test_predicted_termination_and_attenuation(self):
        """Verify that flood wave stops at a predicted termination coordinate with valid physical reason."""
        res = predict_flood_wave_attenuation_and_extinction(
            dam_name="Tehri Dam",
            river_name="Bhagirathi River",
            dam_coords=[78.4803, 30.3781],
            dam_height_m=260.5,
            reservoir_level_m=820.0,
            reservoir_volume_mcm=3540.0,
            breach_width_m=200.0,
            breach_formation_time_hrs=2.0,
            river_coords=self.tehri_coords
        )

        termination = res["termination"]
        self.assertIsNotNone(termination["coords"])
        self.assertTrue(termination["reach_distance_km"] > 50.0)
        self.assertTrue(len(termination["reason"]) > 10)
        self.assertTrue(res["attenuation_ratio_percent"] > 80.0)
        self.assertEqual(res["active_river_coords"][-1], termination["coords"])

    def test_breach_scale_sensitivity(self):
        """Verify that smaller breach terminates earlier than catastrophic breach."""
        small_res = predict_flood_wave_attenuation_and_extinction(
            dam_name="Tehri Dam",
            river_name="Bhagirathi River",
            dam_coords=[78.4803, 30.3781],
            dam_height_m=260.5,
            reservoir_level_m=820.0,
            reservoir_volume_mcm=3540.0,
            breach_width_m=50.0,
            breach_formation_time_hrs=3.0,
            river_coords=self.tehri_coords
        )

        large_res = predict_flood_wave_attenuation_and_extinction(
            dam_name="Tehri Dam",
            river_name="Bhagirathi River",
            dam_coords=[78.4803, 30.3781],
            dam_height_m=260.5,
            reservoir_level_m=820.0,
            reservoir_volume_mcm=3540.0,
            breach_width_m=300.0,
            breach_formation_time_hrs=1.5,
            river_coords=self.tehri_coords
        )

        self.assertTrue(small_res["origin"]["peak_discharge_cumecs"] < large_res["origin"]["peak_discharge_cumecs"])
        self.assertTrue(small_res["termination"]["reach_distance_km"] <= large_res["termination"]["reach_distance_km"])

if __name__ == "__main__":
    unittest.main()
