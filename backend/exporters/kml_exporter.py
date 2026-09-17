def export_to_kml(results: dict) -> str:
    """Generate KML format string for Google Earth visualization."""
    job_id = results.get("job_id", "SCN-001")
    max_inundation = results.get("max_inundation", {})
    features = max_inundation.get("features", [])

    kml = ['<?xml version="1.0" encoding="UTF-8"?>']
    kml.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    kml.append('<Document>')
    kml.append(f'  <name>Flood Inundation - {job_id}</name>')
    kml.append('  <Style id="floodPoly">')
    kml.append('    <LineStyle><color>ffef4444</color><width>2</width></LineStyle>')
    kml.append('    <PolyStyle><color>7f00a5e9</color></PolyStyle>')
    kml.append('  </Style>')

    for f in features:
        geom = f.get("geometry", {})
        if geom.get("type") == "Polygon":
            coords = geom.get("coordinates", [[]])[0]
            coord_str = " ".join([f"{c[0]},{c[1]},0" for c in coords])
            kml.append('  <Placemark>')
            kml.append('    <name>Maximum Flood Inundation Zone</name>')
            kml.append('    <styleUrl>#floodPoly</styleUrl>')
            kml.append('    <Polygon>')
            kml.append('      <outerBoundaryIs><LinearRing>')
            kml.append(f'        <coordinates>{coord_str}</coordinates>')
            kml.append('      </LinearRing></outerBoundaryIs>')
            kml.append('    </Polygon>')
            kml.append('  </Placemark>')

    kml.append('</Document>')
    kml.append('</kml>')

    return "\n".join(kml)
