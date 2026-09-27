import math
import json
from shapely.geometry import shape, Point, LineString, Polygon
from shapely.validation import make_valid
from backend.spatial.crs_utils import project_geometry_to_utm, calculate_metric_area_sqkm, calculate_metric_length_km

def sanitize_geometry(geom):
    """Sanitize and repair self-intersecting or invalid Shapely geometries."""
    if not geom.is_valid:
        try:
            geom = make_valid(geom)
        except Exception:
            geom = geom.buffer(0)
    return geom

def interpolate_smooth_river(coords, target_count=48):
    """Interpolate river coordinates into a smooth Catmull-Rom spline path."""
    if not coords or len(coords) < 3:
        return coords or []
    resampled = []
    num_src = len(coords)
    for i in range(target_count):
        t = (i / max(1, target_count - 1)) * (num_src - 1)
        idx = min(int(t), num_src - 2)
        rem = t - idx
        p0 = coords[max(0, idx - 1)]
        p1 = coords[idx]
        p2 = coords[min(num_src - 1, idx + 1)]
        p3 = coords[min(num_src - 1, idx + 2)]
        
        lng = 0.5 * ((2*p1[0]) + (-p0[0] + p2[0])*rem + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0])*(rem**2) + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0])*(rem**3))
        lat = 0.5 * ((2*p1[1]) + (-p0[1] + p2[1])*rem + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1])*(rem**2) + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1])*(rem**3))
        resampled.append([round(lng, 5), round(lat, 5)])
    return resampled

DEPTH_ZONE_CONFIGS = [
    {
        "zone_id": "zone_fringe",
        "depth_category": "0.1 - 0.5 m",
        "min_depth_m": 0.1,
        "max_depth_m": 0.5,
        "width_ratio": 2.25,
        "fill_color": "#7ccbf9",
        "fill_opacity": 0.55,
        "roughness": 0.38
    },
    {
        "zone_id": "zone_shallow",
        "depth_category": "0.5 - 2 m",
        "min_depth_m": 0.5,
        "max_depth_m": 2.0,
        "width_ratio": 1.60,
        "fill_color": "#3ba7f5",
        "fill_opacity": 0.68,
        "roughness": 0.26
    },
    {
        "zone_id": "zone_moderate",
        "depth_category": "2 - 5 m",
        "min_depth_m": 2.0,
        "max_depth_m": 5.0,
        "width_ratio": 1.10,
        "fill_color": "#1d6dd8",
        "fill_opacity": 0.78,
        "roughness": 0.16
    },
    {
        "zone_id": "zone_deep",
        "depth_category": "5 - 10 m",
        "min_depth_m": 5.0,
        "max_depth_m": 10.0,
        "width_ratio": 0.70,
        "fill_color": "#12499c",
        "fill_opacity": 0.88,
        "roughness": 0.08
    },
    {
        "zone_id": "zone_core",
        "depth_category": "> 10 m",
        "min_depth_m": 10.0,
        "max_depth_m": 16.5,
        "width_ratio": 0.38,
        "fill_color": "#092862",
        "fill_opacity": 0.95,
        "roughness": 0.04
    }
]

def generate_realistic_flood_inundation_geojson(river_coords, scale_factor=1.0, properties_template=None, step=None, total_steps=8):
    """
    Generate realistic multi-tiered flood inundation GeoJSON with 5 contoured depth zones:
    1. > 10 m (Core deep channel)
    2. 5 - 10 m (Deep flood)
    3. 2 - 5 m (Moderate flood)
    4. 0.5 - 2 m (Shallow flood)
    5. 0.1 - 0.5 m (Fringe inundation with natural dendritic valley fingers)
    """
    if not river_coords or len(river_coords) < 2:
        return {"type": "FeatureCollection", "features": []}

    props_base = properties_template or {}
    job_id = props_base.get("scenario_id", "SCN-2026")
    dam_name = props_base.get("dam_name", "Dam")
    river_name = props_base.get("river_name", "River")

    pts = interpolate_smooth_river(river_coords, target_count=max(28, len(river_coords) * 2))
    num_pts = len(pts)

    features = []

    for z_idx, z_cfg in enumerate(DEPTH_ZONE_CONFIGS):
        left_bank = []
        right_bank = []

        for i in range(num_pts):
            pt = pts[i]
            prog = i / max(1, num_pts - 1)

            # Tangent & normal vectors
            if i == 0:
                dx = pts[1][0] - pt[0]
                dy = pts[1][1] - pt[1]
            elif i == num_pts - 1:
                dx = pt[0] - pts[i-1][0]
                dy = pt[1] - pts[i-1][1]
            else:
                dx = pts[i+1][0] - pts[i-1][0]
                dy = pts[i+1][1] - pts[i-1][1]

            length = math.hypot(dx, dy)
            if length == 0:
                length = 1.0
            nx = -dy / length
            ny = dx / length

            # 1. Upper Reservoir dendritic basin (Dam location)
            lake_expansion = 3.2 * max(0.0, 1.0 - prog / 0.18) ** 1.3

            # 2. Confluence pooling basin (e.g. Devprayag / tributary junctions)
            confluence_expansion = 2.4 * math.exp(-((prog - 0.38) / 0.055) ** 2)

            # 3. Downstream alluvial plain expansion (Rishikesh to Haridwar plain)
            plain_expansion = 3.4 * max(0.0, (prog - 0.58) / 0.42) ** 1.35

            # 4. Dendritic valley harmonics (tributaries, side valleys, mountain fingers)
            h1 = math.sin(i * 0.45) * 0.32
            h2 = math.cos(i * 0.90 + 0.3) * 0.22
            h3 = math.sin(i * 1.80) * 0.15
            h4 = math.cos(i * 3.20 + 0.8) * 0.09

            valley_mult = 1.0 + lake_expansion + confluence_expansion + plain_expansion + h1 + h2 + h3 + h4
            base_half_w = 0.0078 * min(3.2, max(0.7, scale_factor)) * max(0.40, valley_mult)

            # Asymmetric lateral expansion into tributary side gullies
            w_ratio = z_cfg["width_ratio"]
            roughness = z_cfg["roughness"]
            rough_left = (math.sin(i * 1.6 + z_idx * 0.8) + 0.4 * math.sin(i * 4.2)) * roughness
            rough_right = (math.cos(i * 1.4 + z_idx * 1.1) + 0.4 * math.cos(i * 3.8)) * roughness

            w_left = base_half_w * w_ratio * max(0.25, 1.0 + rough_left)
            w_right = base_half_w * w_ratio * max(0.25, 1.0 + rough_right)

            left_pt = [round(pt[0] + nx * w_left, 5), round(pt[1] + ny * w_left, 5)]
            right_pt = [round(pt[0] - nx * w_right, 5), round(pt[1] - ny * w_right, 5)]

            left_bank.append(left_pt)
            right_bank.append(right_pt)

        raw_ring = left_bank + right_bank[::-1] + [left_bank[0]]
        
        # Sanitize polygon with Shapely
        try:
            poly_obj = Polygon(raw_ring)
            if not poly_obj.is_valid:
                poly_obj = make_valid(poly_obj)
            if poly_obj.geom_type == 'MultiPolygon':
                poly_obj = max(poly_obj.geoms, key=lambda p: p.area)
            poly_coords = [list(pt) for pt in poly_obj.exterior.coords]
        except Exception:
            poly_coords = raw_ring

        feature_props = dict(props_base)
        feature_props.update({
            "scenario_id": job_id,
            "dam_name": dam_name,
            "river_name": river_name,
            "depth_zone": z_cfg["zone_id"],
            "depth_category": z_cfg["depth_category"],
            "min_depth_m": z_cfg["min_depth_m"],
            "max_depth_m": z_cfg["max_depth_m"],
            "fill_color": z_cfg["fill_color"],
            "fill_opacity": z_cfg["fill_opacity"],
            "wave_front_km": round((len(river_coords) / 16.0) * 105.4, 1)
        })

        features.append({
            "type": "Feature",
            "properties": feature_props,
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords]
            }
        })

    return {
        "type": "FeatureCollection",
        "name": f"Flood_Inundation_{job_id}",
        "features": features
    }

def generate_curved_inundation_polygon(river_coords, scale_factor=1.0):
    """
    Generate realistic 2D flood inundation polygon envelope.
    Returns the outer flood boundary coordinates ring.
    """
    tiered_geojson = generate_realistic_flood_inundation_geojson(river_coords, scale_factor=scale_factor)
    if tiered_geojson.get("features"):
        return tiered_geojson["features"][0]["geometry"]["coordinates"][0]
    return []

def perform_impact_analysis(flood_geojson, villages_geojson, infra_geojson):
    """
    Perform spatial metric intersection analysis between flood inundation outputs
    and population points, building footprints, road polylines, bridges, and critical facilities.
    """
    features = flood_geojson.get("features", [])
    if not features:
        return {
            "inundated_area_sqkm": 0.0,
            "population_exposed": 0,
            "buildings_affected": 0,
            "roads_affected_km": 0.0,
            "bridges_affected_count": 0,
            "hospitals_exposed_count": 0,
            "shelters_exposed_count": 0,
            "villages_affected_count": 0,
            "agricultural_area_sqkm": 0.0,
            "affected_villages_detail": []
        }

    # Extract flood boundary polygon & sanitize geometries
    flood_geoms = [sanitize_geometry(shape(f["geometry"])) for f in features if f.get("geometry")]
    if not flood_geoms:
        return {
            "inundated_area_sqkm": 0.0,
            "population_exposed": 0,
            "buildings_affected": 0,
            "roads_affected_km": 0.0,
            "bridges_affected_count": 0,
            "hospitals_exposed_count": 0,
            "shelters_exposed_count": 0,
            "villages_affected_count": 0,
            "agricultural_area_sqkm": 0.0,
            "affected_villages_detail": []
        }

    flood_union = flood_geoms[0]
    for g in flood_geoms[1:]:
        try:
            flood_union = flood_union.union(g)
        except Exception:
            flood_union = sanitize_geometry(flood_union).union(sanitize_geometry(g))

    flood_union = sanitize_geometry(flood_union)

    # Inundated Area in sq km
    inundated_area_sqkm = calculate_metric_area_sqkm(flood_union)

    # 1. Villages & Population Intersection
    village_features = villages_geojson.get("features", [])
    total_pop_exposed = 0
    affected_villages = []
    
    for v in village_features:
        v_geom = sanitize_geometry(shape(v["geometry"]))
        props = v.get("properties", {})
        pop = props.get("population", 0)
        dist_km = props.get("distance_downstream_km", 10.0)

        # Estimate flood depth and arrival time at village location based on distance from dam
        if flood_union.intersects(v_geom) or flood_union.distance(v_geom) < 0.015:
            estimated_depth = max(0.4, round(6.5 * math.exp(-dist_km / 35.0), 2))
            estimated_vel = max(0.3, round(5.2 * math.exp(-dist_km / 45.0), 2))
            estimated_arrival = max(15, int(dist_km * 1.45 + (100.0 / max(estimated_vel, 0.5))))

            v_copy = json.loads(json.dumps(v))
            v_copy["properties"]["flood_depth_m"] = estimated_depth
            v_copy["properties"]["velocity_mps"] = estimated_vel
            v_copy["properties"]["arrival_time_min"] = estimated_arrival
            
            total_pop_exposed += pop
            affected_villages.append(v_copy)

    # 2. Roads & Infrastructure Intersection
    infra_features = infra_geojson.get("features", [])
    roads_affected_km = 0.0
    bridges_affected = 0
    hospitals_exposed = 0
    shelters_exposed = 0

    for item in infra_features:
        i_geom = sanitize_geometry(shape(item["geometry"]))
        cat = item["properties"].get("category")
        
        if flood_union.intersects(i_geom):
            if cat == "road":
                try:
                    inter = flood_union.intersection(i_geom)
                    roads_affected_km += calculate_metric_length_km(inter)
                except Exception:
                    pass
            elif cat == "bridge":
                bridges_affected += 1
            elif cat == "hospital":
                hospitals_exposed += 1
            elif cat == "shelter":
                shelters_exposed += 1

    estimated_buildings = int(total_pop_exposed / 3.8)
    agricultural_area_sqkm = round(inundated_area_sqkm * 0.42, 2)

    return {
        "inundated_area_sqkm": round(inundated_area_sqkm, 2),
        "population_exposed": total_pop_exposed,
        "buildings_affected": estimated_buildings,
        "roads_affected_km": round(roads_affected_km, 2),
        "bridges_affected_count": bridges_affected,
        "hospitals_exposed_count": hospitals_exposed,
        "shelters_exposed_count": shelters_exposed,
        "villages_affected_count": len(affected_villages),
        "agricultural_area_sqkm": agricultural_area_sqkm,
        "affected_villages_detail": affected_villages
    }
