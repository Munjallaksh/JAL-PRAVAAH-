import os
import zipfile
import shapefile

def export_to_shapefile_zip(results: dict, output_zip_path: str) -> str:
    """
    Generate complete ESRI Shapefile bundle (.shp, .shx, .dbf, .prj)
    and pack into a ZIP archive.
    """
    base_name = os.path.splitext(output_zip_path)[0]
    shp_path = f"{base_name}.shp"

    w = shapefile.Writer(base_name, shapefile.POLYGON)
    w.field("SCENARIO", "C", 40)
    w.field("ENGINE", "C", 20)
    w.field("PEAK_FLOW", "N", 10, 2)
    w.field("MAX_DEPTH", "N", 8, 2)

    features = results.get("max_inundation", {}).get("features", [])
    for f in features:
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        if geom.get("type") == "Polygon":
            coords = geom.get("coordinates", [[]])[0]
            w.poly([coords])
            w.record(
                props.get("scenario_id", "SCN-001"),
                props.get("engine", "SPH"),
                props.get("peak_flow_cumecs", 15000.0),
                props.get("max_depth_m", 5.0)
            )

    w.close()

    # Write WGS84 EPSG:4326 PRJ file
    prj_content = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'
    with open(f"{base_name}.prj", "w") as prj_file:
        prj_file.write(prj_content)

    # Package component files into ZIP archive
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for ext in [".shp", ".shx", ".dbf", ".prj"]:
            file_to_add = f"{base_name}{ext}"
            if os.path.exists(file_to_add):
                z.write(file_to_add, arcname=os.path.basename(file_to_add))
                os.remove(file_to_add)

    return output_zip_path
