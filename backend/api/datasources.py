"""JAL-PRAVAAH DATA SOURCES API ROUTER
Exposes endpoints for querying the Master Provider Registry, searching datasets,
generating simulation/validation manifests, and computing data readiness reports.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from backend.datasources.models import (
    DataSourceProvider,
    QualityAssessment,
    SimulationInputManifest,
    ValidationManifest,
    DataReadinessReport
)
from backend.datasources.master_registry import (
    MASTER_DATA_PROVIDERS,
    get_provider_by_id,
    get_all_providers,
    search_providers
)
from backend.datasources.quality_engine import (
    evaluate_dataset_quality,
    generate_simulation_input_manifest,
    generate_validation_manifest,
    generate_data_readiness_report,
    DATA_SELECTION_PRIORITY_CHAINS
)

router = APIRouter(prefix="/datasources", tags=["Data Sources Registry"])

@router.get("/registry", response_model=List[DataSourceProvider])
def list_all_providers():
    """Returns the full master catalog of all registered data providers."""
    return get_all_providers()

@router.get("/categories")
def get_categories_overview():
    """Returns all data categories with provider counts and protocol breakdowns."""
    categories: dict = {}
    protocols: dict = {"STAC": 0, "WMS/WFS/WMTS": 0, "REST": 0, "DIRECT_DOWNLOAD": 0}
    tier_counts: dict = {}

    for p in MASTER_DATA_PROVIDERS.values():
        cat = p.category.value
        categories[cat] = categories.get(cat, 0) + 1
        tier = p.authority_tier.value
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        if p.stac_available:
            protocols["STAC"] += 1
        if p.wms_available or p.wfs_available or p.wmts_available or p.api_type == "OGC_API":
            protocols["WMS/WFS/WMTS"] += 1
        if p.rest_available or p.api_type == "REST":
            protocols["REST"] += 1
        if p.download_available:
            protocols["DIRECT_DOWNLOAD"] += 1

    return {
        "total_providers": len(MASTER_DATA_PROVIDERS),
        "categories": categories,
        "protocols": protocols,
        "authority_tiers": tier_counts
    }

@router.get("/search", response_model=List[DataSourceProvider])
def search_data_providers(
    q: Optional[str] = Query(None, description="Search term (e.g. DEM, Rainfall, Flood, Dam, River, Population, Satellite, Hydrology, Buildings, Roads)"),
    category: Optional[str] = Query(None, description="Category filter (INDIA, SATELLITE, TERRAIN, HYDROLOGY, RAINFALL, FLOOD, POPULATION, BUILDINGS, LAND COVER, MAPS / GEOCODING, CLIMATE)"),
    protocol: Optional[str] = Query(None, description="Protocol filter (STAC, WMS, REST, DOWNLOAD)"),
    authority: Optional[str] = Query(None, description="Authority tier filter")
):
    """Searches and filters data providers matching keywords and protocol options."""
    return search_providers(query=q, category=category, protocol=protocol, authority_tier=authority)

@router.get("/provider/{provider_id}", response_model=DataSourceProvider)
def get_provider_details(provider_id: str):
    """Retrieve complete metadata, licensing, endpoints, and limitations for a single provider."""
    provider = get_provider_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Data provider '{provider_id}' not found in registry.")
    return provider

@router.get("/quality-assessment", response_model=QualityAssessment)
def assess_dataset_quality(
    provider_id: str = Query(..., description="Provider ID (e.g. copernicus-dem)"),
    variable: str = Query(..., description="Variable name (e.g. Elevation DSM)"),
    resolution_m: float = Query(30.0, description="Spatial resolution in meters"),
    aoi_coverage_pct: float = Query(100.0, description="AOI coverage percentage"),
    missing_data_pct: float = Query(0.0, description="Missing void fraction percentage")
):
    """Computes dynamic data quality score, freshness, and human-readable explanation."""
    return evaluate_dataset_quality(
        provider_id=provider_id,
        variable=variable,
        resolution_m=resolution_m,
        aoi_coverage_pct=aoi_coverage_pct,
        missing_data_pct=missing_data_pct,
        is_dsm_for_dtm=(provider_id == "copernicus-dem" and "Elevation" in variable)
    )

@router.get("/readiness", response_model=DataReadinessReport)
def get_data_readiness_report(
    dam_name: str = Query("Tehri Dam", description="Target dam or reservoir name"),
    river_name: str = Query("Bhagirathi River", description="Target river name")
):
    """Generates the Section 55 DATA READINESS REPORT across all 9 core hydrodynamic domains."""
    return generate_data_readiness_report(dam_name=dam_name, river_name=river_name)

@router.get("/manifest/simulation", response_model=SimulationInputManifest)
def get_simulation_manifest(
    dam_name: str = Query("Tehri Dam", description="Target dam name"),
    river_name: str = Query("Bhagirathi River", description="Target river reach")
):
    """Generates simulation_input_manifest.json before simulation execution (Section 53)."""
    return generate_simulation_input_manifest(dam_name=dam_name, river_name=river_name)

@router.get("/manifest/validation", response_model=ValidationManifest)
def get_validation_manifest(
    job_id: str = Query("JOB-SAR-VAL-001", description="Simulation or validation job ID"),
    satellite_provider: str = Query("Copernicus Sentinel-1 SAR", description="Satellite provider name"),
    satellite_product: str = Query("Sentinel-1A IW GRD C-SAR", description="Satellite product name")
):
    """Generates validation_manifest.json for empirical SAR vs Modelled flood comparison (Section 54)."""
    return generate_validation_manifest(
        job_id=job_id,
        satellite_provider=satellite_provider,
        satellite_product=satellite_product
    )

@router.get("/priorities")
def get_selection_priority_chains():
    """Returns the priority fallback chains for each domain variable (Section 35)."""
    return {
        "priority_chains": DATA_SELECTION_PRIORITY_CHAINS,
        "standard_hierarchy": [
            "PRIMARY AUTHORITATIVE (National Government Authorities)",
            "SECONDARY AUTHORITATIVE (National Specialised Bodies)",
            "NATIONAL OPEN DATA (data.gov.in / National Portals)",
            "GLOBAL SCIENTIFIC DATA (Copernicus, NASA, ESA, JAXA, ECMWF)",
            "OPEN DATA (OpenStreetMap, Community Catalogs)",
            "USER UPLOAD (Authorized Field Rasters / GeoJSON)",
            "DEMO DATA (Strictly Labeled Benchmark Fallback)"
        ]
    }
