import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from backend.core.orchestrator import orchestrator
from backend.exporters.geojson_exporter import export_to_geojson
from backend.exporters.kml_exporter import export_to_kml
from backend.exporters.shapefile_exporter import export_to_shapefile_zip
from backend.exporters.csv_exporter import export_to_csv
from backend.exporters.pdf_report_exporter import generate_pdf_report
from backend.config import settings

router = APIRouter(prefix="/exports", tags=["Exports"])

def _get_dam_slug(results: dict) -> str:
    dam_name = results.get("dam_name") or results.get("max_inundation", {}).get("features", [{}])[0].get("properties", {}).get("dam_name") or "Dam"
    return str(dam_name).replace(" ", "_").replace("/", "-").strip()

@router.get("/{job_id}/geojson")
def download_geojson(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    slug = _get_dam_slug(job["results"])
    content = export_to_geojson(job["results"])
    return Response(
        content=content,
        media_type="application/geo+json",
        headers={"Content-Disposition": f"attachment; filename=flood_{slug}_{job_id}.geojson"}
    )

@router.get("/{job_id}/kml")
def download_kml(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    slug = _get_dam_slug(job["results"])
    content = export_to_kml(job["results"])
    return Response(
        content=content,
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": f"attachment; filename=flood_{slug}_{job_id}.kml"}
    )

@router.get("/{job_id}/shp")
def download_shapefile(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    slug = _get_dam_slug(job["results"])
    zip_filename = f"flood_{slug}_{job_id}_shp.zip"
    zip_path = os.path.join(settings.EXPORT_DIR, zip_filename)
    export_to_shapefile_zip(job["results"], zip_path)
    return FileResponse(path=zip_path, filename=zip_filename, media_type="application/zip")

@router.get("/{job_id}/csv")
def download_csv(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    slug = _get_dam_slug(job["results"])
    content = export_to_csv(job["results"])
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=hadr_priorities_{slug}_{job_id}.csv"}
    )

@router.get("/{job_id}/pdf")
def download_pdf(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    slug = _get_dam_slug(job["results"])
    pdf_filename = f"JAL_PRAVAAH_Report_{slug}_{job_id}.pdf"
    pdf_path = os.path.join(settings.EXPORT_DIR, pdf_filename)
    generate_pdf_report(job["results"], pdf_path)
    return FileResponse(path=pdf_path, filename=pdf_filename, media_type="application/pdf")
