import unittest
from backend.datasources import (
    MASTER_DATA_PROVIDERS,
    get_provider_by_id,
    search_providers,
    evaluate_dataset_quality,
    generate_simulation_input_manifest,
    generate_validation_manifest,
    generate_data_readiness_report,
    DATA_SELECTION_PRIORITY_CHAINS
)
from backend.datasources.models import DataQualityScore, DataFreshness, AuthorityTier

class TestDataSourcesRegistry(unittest.TestCase):

    def test_provider_registration_completeness(self):
        """Verify all essential Indian and Global data providers are registered."""
        required_providers = [
            "cwc-india", "india-wris", "nrld-india", "isro-bhuvan", "isro-bhoonidhi",
            "ndem-india", "mosdac-isro", "imd-india", "datagov-india", "survey-of-india",
            "gsi-india", "nrsc-isro", "vedas-isro", "indian-flood-data", "copernicus-dataspace",
            "sentinel-1", "sentinel-2", "sentinel-3", "sentinel-5p", "nisar", "landsat",
            "modis", "viirs", "noaa-data", "copernicus-dem", "nasadem", "srtm", "alos-aw3d30",
            "fabdem", "merit-dem", "tandem-x", "usgs-3dep", "hydrosheds", "hydrorivers",
            "hydrobasins", "merit-hydro", "global-river-widths", "global-dam-watch", "grand",
            "gpm-imerg", "trmm", "era5", "era5-land", "glofas", "swot", "jrc-surface-water",
            "esa-worldcover", "worldpop", "ghsl", "gpw", "osm", "microsoft-buildings",
            "google-open-buildings", "road-network", "critical-infrastructure",
            "nighttime-lights", "historical-flood", "copernicus-ems", "nominatim",
            "basemaps-master", "ogc-provider", "stac-provider", "planetary-computer",
            "gee", "chirps", "cmorph", "mswep", "gefs", "gfs", "ecmwf-weather",
            "usgs-hazards", "state-data-provider", "municipal-gis"
        ]
        for pid in required_providers:
            prov = get_provider_by_id(pid)
            self.assertIsNotNone(prov, f"Required provider '{pid}' missing from master registry.")
            self.assertTrue(len(prov.official_name) > 0)
            self.assertTrue(prov.website.startswith("http"))
            self.assertIsInstance(prov.health.status.value, str)

    def test_no_fake_endpoints_rule(self):
        """Verify that any configured API endpoint is an authentic URL or None (Section 48)."""
        for pid, prov in MASTER_DATA_PROVIDERS.items():
            if prov.official_api_endpoint:
                self.assertTrue(
                    prov.official_api_endpoint.startswith("http://") or prov.official_api_endpoint.startswith("https://"),
                    f"Invalid endpoint scheme for provider {pid}"
                )
                self.assertNotIn("fake", prov.official_api_endpoint.lower())
                self.assertNotIn("example.com", prov.official_api_endpoint.lower())

    def test_search_by_keywords(self):
        """Verify Section 51 search requirements for key hydrological terms."""
        terms = ["DEM", "Rainfall", "Flood", "Dam", "River", "Population", "Satellite", "Hydrology", "Buildings", "Roads"]
        for term in terms:
            results = search_providers(query=term)
            self.assertGreater(len(results), 0, f"Search query '{term}' yielded 0 providers.")

    def test_quality_engine_evaluation(self):
        """Verify Section 37 & 38 Quality Engine computations and explanation."""
        # High quality complete DEM
        assessment = evaluate_dataset_quality(
            provider_id="copernicus-dem",
            variable="Elevation DSM GLO-30",
            resolution_m=30.0,
            aoi_coverage_pct=100.0,
            missing_data_pct=0.4,
            is_dsm_for_dtm=True
        )
        self.assertEqual(assessment.quality, DataQualityScore.HIGH)
        self.assertEqual(assessment.completeness_pct, 99.6)
        self.assertIn("Surface DSM requires hydro-conditioning", assessment.explanation)

    def test_simulation_manifest_generation(self):
        """Verify Section 53 simulation_input_manifest.json structure and verification hash."""
        manifest = generate_simulation_input_manifest(
            dam_name="Tehri Dam",
            river_name="Bhagirathi River",
            aoi_bbox=[78.20, 30.10, 78.60, 30.50]
        )
        self.assertTrue(manifest.manifest_id.startswith("SIM-MAN-"))
        self.assertEqual(manifest.dam_name, "Tehri Dam")
        self.assertEqual(manifest.river_name, "Bhagirathi River")
        self.assertIsNotNone(manifest.dem_source)
        self.assertIsNotNone(manifest.rainfall_source)
        self.assertIsNotNone(manifest.satellite_source)
        self.assertIsNotNone(manifest.hydrology_source)
        self.assertEqual(len(manifest.verification_hash), 64)  # Valid SHA-256

    def test_validation_manifest_generation(self):
        """Verify Section 54 validation_manifest.json metrics for SAR comparison."""
        val = generate_validation_manifest(
            job_id="JOB-TEST-001",
            satellite_provider="Copernicus Sentinel-1 SAR",
            satellite_product="Sentinel-1A IW GRD",
            iou_score=0.856
        )
        self.assertEqual(val.job_id, "JOB-TEST-001")
        self.assertEqual(val.iou, 0.856)
        self.assertGreater(val.precision, 0.5)
        self.assertEqual(len(val.verification_hash), 64)

    def test_data_readiness_report(self):
        """Verify Section 55 priority fallback and readiness report."""
        report = generate_data_readiness_report("Tehri Dam", "Bhagirathi River")
        self.assertEqual(report.overall_readiness, "FULL_READINESS")
        self.assertEqual(len(report.domains), 9)  # 9 core domains
        domains = [d.domain for d in report.domains]
        for expected in ["DAM", "RIVER", "DEM", "HYDROLOGY", "RAINFALL", "SATELLITE", "POPULATION", "INFRASTRUCTURE", "LAND_COVER"]:
            self.assertIn(expected, domains)

if __name__ == "__main__":
    unittest.main()
