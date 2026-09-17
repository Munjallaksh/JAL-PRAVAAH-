from shapely.geometry import shape
from backend.spatial.crs_utils import project_geometry_to_utm

def compute_spatial_validation(modeled_geojson, observed_geojson):
    """
    Compute rigorous spatial validation metrics between modeled flood extent and observed flood extent:
    - Intersection over Union (IoU)
    - Precision
    - Recall
    - F1 Score
    - Area Difference (sq km)
    """
    try:
        # Extract features
        mod_features = modeled_geojson.get("features", [])
        obs_features = observed_geojson.get("features", [])

        if not mod_features or not obs_features:
            return {
                "available": False,
                "reason": "Missing modeled or observed flood geometries for validation comparison."
            }

        # Combine into single shapely multipolygons
        mod_geoms = [shape(f["geometry"]) for f in mod_features if f.get("geometry")]
        obs_geoms = [shape(f["geometry"]) for f in obs_features if f.get("geometry")]

        if not mod_geoms or not obs_geoms:
            return {"available": False, "reason": "No valid spatial geometries present."}

        mod_union = mod_geoms[0]
        for g in mod_geoms[1:]:
            mod_union = mod_union.union(g)

        obs_union = obs_geoms[0]
        for g in obs_geoms[1:]:
            obs_union = obs_union.union(g)

        # Convert to UTM metric projection
        mod_utm = project_geometry_to_utm(mod_union)
        obs_utm = project_geometry_to_utm(obs_union)

        area_modeled = mod_utm.area / 1e6
        area_observed = obs_utm.area / 1e6

        intersection_geom = mod_utm.intersection(obs_utm)
        area_intersection = intersection_geom.area / 1e6

        union_geom = mod_utm.union(obs_utm)
        area_union = union_geom.area / 1e6

        iou = (area_intersection / area_union) if area_union > 0 else 0.0
        precision = (area_intersection / area_modeled) if area_modeled > 0 else 0.0
        recall = (area_intersection / area_observed) if area_observed > 0 else 0.0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "available": True,
            "modeled_area_sqkm": round(area_modeled, 2),
            "observed_area_sqkm": round(area_observed, 2),
            "intersection_area_sqkm": round(area_intersection, 2),
            "area_difference_sqkm": round(area_modeled - area_observed, 2),
            "iou": round(iou, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "validation_class": "STRONG_AGREEMENT" if iou > 0.65 else ("MODERATE_AGREEMENT" if iou > 0.40 else "POOR_AGREEMENT")
        }
    except Exception as e:
        return {
            "available": False,
            "reason": f"Validation computation error: {str(e)}"
        }
