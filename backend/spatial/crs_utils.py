import math
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform

# WGS84 (EPSG:4326) to UTM Zone 44N (EPSG:32644) for Northern India (Uttarakhand / Tehri)
transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
transformer_to_wgs84 = Transformer.from_crs("EPSG:32644", "EPSG:4326", always_xy=True)

def project_geometry_to_utm(geom_shapely):
    """Project a WGS84 Shapely geometry to metric UTM Zone 44N."""
    return transform(transformer_to_utm.transform, geom_shapely)

def project_geometry_to_wgs84(geom_shapely):
    """Project a metric UTM Zone 44N Shapely geometry back to WGS84."""
    return transform(transformer_to_wgs84.transform, geom_shapely)

def calculate_metric_area_sqkm(geom_wgs84):
    """Calculate exact polygon area in square kilometers using UTM metric projection."""
    geom_utm = project_geometry_to_utm(geom_wgs84)
    return geom_utm.area / 1e6

def calculate_metric_length_km(geom_wgs84):
    """Calculate line length in kilometers using UTM metric projection."""
    geom_utm = project_geometry_to_utm(geom_wgs84)
    return geom_utm.length / 1000.0

def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Haversine distance formula in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
