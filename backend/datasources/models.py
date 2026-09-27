from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field

# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class ProviderHealthStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMITED = "RATE_LIMITED"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"

class DataFreshness(str, Enum):
    LIVE = "LIVE"
    NEAR_REAL_TIME = "NEAR REAL-TIME"
    RECENT = "RECENT"
    HISTORICAL = "HISTORICAL"
    REANALYSIS = "REANALYSIS"

class DataQualityScore(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNAVAILABLE = "UNAVAILABLE"

class AuthorityTier(str, Enum):
    PRIMARY_AUTHORITATIVE = "PRIMARY AUTHORITATIVE"
    SECONDARY_AUTHORITATIVE = "SECONDARY AUTHORITATIVE"
    NATIONAL_OPEN_DATA = "NATIONAL OPEN DATA"
    GLOBAL_SCIENTIFIC_DATA = "GLOBAL SCIENTIFIC DATA"
    OPEN_DATA = "OPEN DATA"
    STATE_AGENCY = "STATE AGENCY"
    MUNICIPAL = "DISTRICT / MUNICIPAL"
    USER_UPLOAD = "USER UPLOAD"
    DEMO_DATA = "DEMO DATA"

class ProviderCategory(str, Enum):
    INDIA = "INDIA"
    SATELLITE = "SATELLITE"
    TERRAIN = "TERRAIN"
    HYDROLOGY = "HYDROLOGY"
    RAINFALL = "RAINFALL"
    FLOOD = "FLOOD"
    POPULATION = "POPULATION"
    BUILDINGS = "BUILDINGS"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    LAND_COVER = "LAND COVER"
    MAPS_GEOCODING = "MAPS / GEOCODING"
    CLIMATE = "CLIMATE"

# ============================================================
# NORMALIZED DATA MODELS (Section 46)
# ============================================================

class DamRecord(BaseModel):
    """Normalized schema for dams & reservoirs."""
    id: str
    name: str
    official_name: Optional[str] = None
    river: str
    basin: Optional[str] = None
    state: str
    district: Optional[str] = None
    lat: float
    lng: float
    dam_height_m: Optional[float] = None
    crest_length_m: Optional[float] = None
    gross_storage_mcm: Optional[float] = None
    live_storage_mcm: Optional[float] = None
    full_reservoir_level_m: Optional[float] = None
    maximum_water_level_m: Optional[float] = None
    dam_type: Optional[str] = None  # Earthen, Gravity, Rockfill, Arch
    purpose: Optional[str] = None   # Hydroelectric, Irrigation, Flood Control
    year_completed: Optional[int] = None
    owner_operator: Optional[str] = None
    primary_source: str = Field(..., description="CWC, NRLD, India-WRIS, GRanD, Global Dam Watch")
    authority_tier: AuthorityTier = AuthorityTier.PRIMARY_AUTHORITATIVE
    provenance_hash: Optional[str] = None
    is_demo: bool = False

class RiverRecord(BaseModel):
    """Normalized schema for river segments & drainage networks."""
    id: str
    name: str
    basin_name: str
    sub_basin: Optional[str] = None
    stream_order: Optional[int] = None  # Strahler order
    reach_length_km: Optional[float] = None
    mean_width_m: Optional[float] = None
    flow_direction_deg: Optional[float] = None
    states_traversed: List[str] = []
    source_provider: str
    geometry_type: str = "LineString"
    coordinates: Optional[List[List[float]]] = None
    is_demo: bool = False

class HydrologicalStation(BaseModel):
    """Normalized schema for river gauge & hydrological observation posts."""
    station_id: str
    station_name: str
    river: str
    basin: str
    state: str
    district: Optional[str] = None
    managing_agency: str = Field(..., description="CWC, State WRD, India-WRIS, GloFAS")
    lat: float
    lng: float
    zero_gauge_level_m: Optional[float] = None
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    highest_flood_level_m: Optional[float] = None
    highest_flood_date: Optional[str] = None
    telemetry_type: Optional[str] = "AUTOMATIC_TELEMETRIC"  # Manual, Telemetric, Satellite-DCP
    operational_status: str = "ACTIVE"

class HydrologicalObservation(BaseModel):
    """Normalized time-series observation from hydrological post."""
    station_id: str
    station_name: str
    timestamp_utc: str
    water_level_m: Optional[float] = None
    discharge_cumecs: Optional[float] = None
    trend: Optional[str] = "STEADY"  # RISING, FALLING, STEADY
    warning_status: Optional[str] = "NORMAL"  # NORMAL, ABOVE_WARNING, ABOVE_DANGER, RECORD
    data_provider: str
    freshness: DataFreshness = DataFreshness.LIVE
    quality_flag: str = "VALIDATED"
    provenance_hash: Optional[str] = None

class RainfallObservation(BaseModel):
    """Normalized precipitation data from in-situ gauges or satellite grids."""
    station_or_cell_id: str
    latitude: float
    longitude: float
    timestamp_utc: str
    accumulation_window_hours: float = 1.0  # 1hr, 3hr, 24hr
    rainfall_mm: float
    product_name: str = Field(..., description="IMD AWS, MOSDAC IMSRA, GPM IMERG, CHIRPS, ERA5-Land")
    provider: str
    spatial_resolution_km: float
    latency_type: DataFreshness = DataFreshness.NEAR_REAL_TIME
    processing_level: str = "Level-3 Gridded"
    quality_score: DataQualityScore = DataQualityScore.HIGH

class TerrainDataset(BaseModel):
    """Normalized digital elevation model descriptor."""
    dataset_id: str
    dataset_name: str = Field(..., description="Copernicus DEM GLO-30, NASADEM, ALOS AW3D30, FABDEM, MERIT DEM")
    provider: str
    model_type: str = Field(..., description="DSM (Digital Surface Model) or DTM (Bare-Earth Bare-Ground)")
    spatial_resolution_m: float
    vertical_datum: str = "EGM96 / EGM2008"
    horizontal_crs: str = "EPSG:4326"
    coverage: str = "Global / India 100%"
    missing_data_pct: float = 0.0
    quality_score: DataQualityScore = DataQualityScore.HIGH
    scientific_notes: str
    license: str

class SatelliteObservation(BaseModel):
    """Normalized satellite scene record (SAR or Optical)."""
    scene_id: str
    platform: str  # Sentinel-1A, Sentinel-2B, Landsat-9, NISAR
    instrument: str  # C-SAR, MSI, OLI-2, L-SAR
    acquisition_timestamp_utc: str
    orbit_direction: Optional[str] = "DESCENDING"
    relative_orbit: Optional[int] = None
    polarization: Optional[List[str]] = None  # ['VV', 'VH']
    optical_bands: Optional[List[str]] = None  # ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
    cloud_cover_percentage: Optional[float] = None
    spatial_resolution_m: float
    bounding_box: List[float]  # [min_lng, min_lat, max_lng, max_lat]
    provider: str
    access_catalog: str = "Copernicus Data Space Ecosystem STAC"
    freshness: DataFreshness = DataFreshness.HISTORICAL

class PopulationGrid(BaseModel):
    """Normalized population exposure grid."""
    dataset_id: str
    provider: str = Field(..., description="WorldPop, GHSL GHS-POP, GPW v4")
    reference_year: int
    resolution_m: float
    horizontal_crs: str = "EPSG:4326"
    aggregation_method: str = "Random Forest Dasymetric / Census Gridded"
    total_aoi_population: Optional[int] = None
    license: str

class InfrastructureFeature(BaseModel):
    """Normalized critical infrastructure item."""
    id: str
    name: str
    category: str = Field(..., description="HOSPITAL, SCHOOL, POLICE, FIRE_STATION, POWER_SUBSTATION, BRIDGE, CANAL, SHELTER, WTP")
    subcategory: Optional[str] = None
    lat: float
    lng: float
    state: str
    district: Optional[str] = None
    source_provider: str = Field(..., description="Government National, State Portal, OpenStreetMap")
    operational_status: str = "FUNCTIONAL"
    vulnerability_index: Optional[float] = None
    is_demo: bool = False

class FloodObservation(BaseModel):
    """Normalized satellite/hydro observation of flood extent."""
    observation_id: str
    event_name: str
    observation_date_utc: str
    sensor_type: str = "SAR C-Band"  # SAR, Optical, Microwave
    satellite_mission: str
    provider: str
    flood_extent_geojson: Optional[Dict[str, Any]] = None
    flooded_area_sqkm: float
    water_extraction_method: str = "Bimodal Otsu SAR Thresholding + MNDWI Cross-Mask"
    confidence_level: DataQualityScore = DataQualityScore.HIGH
    validation_status: str = "VALIDATED"

# ============================================================
# MASTER PROVIDER REGISTRY MODELS
# ============================================================

class ProviderHealth(BaseModel):
    status: ProviderHealthStatus = ProviderHealthStatus.CONNECTED
    last_checked: str
    last_success: Optional[str] = None
    response_time_ms: Optional[int] = None
    message: str = "Service operational"

class DataSourceProvider(BaseModel):
    id: str
    name: str
    official_name: str
    organization: str
    country: str = "India"  # "India", "Global", "USA", "Europe"
    category: ProviderCategory
    subcategories: List[str] = []
    authority_tier: AuthorityTier
    website: str
    documentation_url: Optional[str] = None
    
    # Protocols and availability (Strictly true/false, no fake endpoints)
    api_available: bool = False
    api_type: Optional[str] = None  # "REST", "STAC", "WMS", "WFS", "WMTS", "WCS", "OGC_API", "OData"
    official_api_endpoint: Optional[str] = None  # None if unavailable, or real documented endpoint URL
    stac_available: bool = False
    wms_available: bool = False
    wfs_available: bool = False
    wmts_available: bool = False
    rest_available: bool = False
    download_available: bool = True
    official_download_portal: Optional[str] = None
    
    # Access and Auth
    auth_required: bool = False
    auth_method: str = "NONE"  # "NONE", "API_KEY", "OAUTH2", "REGISTRATION_REQUIRED", "RESTRICTED_GOV"
    license: str = "Open Data"
    access_restrictions: str = "Public Access"
    
    # Geospatial / Temporal Properties
    spatial_coverage: str = "India (National)"
    spatial_resolution: str = "Variable"
    temporal_coverage: str = "Historical to Present"
    temporal_resolution: str = "Daily / Near Real-Time"
    freshness: DataFreshness = DataFreshness.RECENT
    
    # Data specs
    supported_formats: List[str] = ["GeoJSON", "CSV", "GeoTIFF"]
    variables: List[str] = []
    example_products: List[str] = []
    scientific_limitations: List[str] = []
    
    # Operational health
    health: ProviderHealth
    selection_priority: int = 1  # 1 = top priority in variable category
    notes: str = ""

# ============================================================
# QUALITY ENGINE & MANIFEST MODELS (Sections 37, 38, 53, 54, 55)
# ============================================================

class QualityAssessment(BaseModel):
    source: str
    dataset: str
    version: str
    resolution: str
    time_range: str
    observation_date: str
    aoi_coverage_pct: float
    completeness_pct: float
    missing_data_pct: float
    crs: str
    units: str
    processing_level: str
    source_authority: AuthorityTier
    quality: DataQualityScore
    freshness: DataFreshness
    limitations: List[str]
    explanation: str

class SimulationDatasetSource(BaseModel):
    variable: str
    provider_id: str
    provider_name: str
    dataset_name: str
    version: str
    observation_date: str
    resolution: str
    crs: str
    units: str
    quality: DataQualityScore
    freshness: DataFreshness
    license: str
    attribution: str
    provenance_hash: str
    access_method: str  # "STAC_API", "REST_API", "OFFICIAL_CATALOG_DOWNLOAD", "CACHED_STORE"

class SimulationInputManifest(BaseModel):
    manifest_id: str
    generated_at_utc: str
    dam_name: str
    river_name: str
    aoi_bbox: List[float]
    dam_source: SimulationDatasetSource
    river_source: SimulationDatasetSource
    dem_source: SimulationDatasetSource
    hydrology_source: SimulationDatasetSource
    rainfall_source: SimulationDatasetSource
    satellite_source: SimulationDatasetSource
    population_source: SimulationDatasetSource
    infrastructure_source: SimulationDatasetSource
    land_cover_source: SimulationDatasetSource
    overall_quality: DataQualityScore
    verification_hash: str
    manifest_notes: str

class ValidationManifest(BaseModel):
    job_id: str
    generated_at_utc: str
    modelled_result: str
    observed_result: str
    satellite_provider: str
    satellite_product: str
    acquisition_date: str
    pre_event_date: str
    post_event_date: str
    resolution: str
    crs: str
    processing: str
    iou: float
    precision: float
    recall: float
    f1_score: float
    limitations: List[str]
    verification_hash: str

class DataReadinessDomain(BaseModel):
    domain: str  # "DAM", "RIVER", "DEM", "HYDROLOGY", "RAINFALL", "SATELLITE", "POPULATION", "INFRASTRUCTURE", "LAND_COVER"
    selected_provider: str
    dataset: str
    status: str  # "AVAILABLE", "PARTIAL", "AUTH_REQUIRED", "UNAVAILABLE"
    quality: DataQualityScore
    resolution: str
    coverage_pct: float
    source_tier: AuthorityTier
    fallback_sequence: List[str]

class DataReadinessReport(BaseModel):
    report_id: str
    generated_at_utc: str
    dam_name: str
    river_name: str
    aoi_bbox: List[float]
    overall_readiness: str  # "FULL_READINESS", "PARTIAL_READINESS", "CRITICAL_MISSING"
    readiness_percentage: float
    domains: List[DataReadinessDomain]
    recommendations: List[str]
    compliance_notes: str

class ProviderSearchQuery(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    protocol: Optional[str] = None  # STAC, WMS, REST, DOWNLOAD
    authority_tier: Optional[str] = None
    health_status: Optional[str] = None
