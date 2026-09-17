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

@router.get("/{job_id}/geojson")
def download_geojson(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    content = export_to_geojson(job["results"])
    return Response(content=content, media_type="application/geo+json", headers={"Content-Disposition": f"attachment; filename=flood_{job_id}.geojson"})

@router.get("/{job_id}/kml")
def download_kml(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    content = export_to_kml(job["results"])
    return Response(content=content, media_type="application/vnd.google-earth.kml+xml", headers={"Content-Disposition": f"attachment; filename=flood_{job_id}.kml"})

@router.get("/{job_id}/shp")
def download_shapefile(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    zip_path = os.path.join(settings.EXPORT_DIR, f"flood_{job_id}_shp.zip")
    export_to_shapefile_zip(job["results"], zip_path)
    return FileResponse(path=zip_path, filename=f"flood_{job_id}_shp.zip", media_type="application/zip")

@router.get("/{job_id}/csv")
def download_csv(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    content = export_to_csv(job["results"])
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=hadr_priorities_{job_id}.csv"})

@router.get("/{job_id}/pdf")
def download_pdf(job_id: str):
    job = orchestrator.get_job_status(job_id)
    if not job or job["status"] != "COMPLETE":
        raise HTTPException(status_code=400, detail="Job results not ready.")
    pdf_path = os.path.join(settings.EXPORT_DIR, f"HADR_Executive_Report_{job_id}.pdf")
    generate_pdf_report(job["results"], pdf_path)
    return FileResponse(path=pdf_path, filename=f"HADR_Executive_Report_{job_id}.pdf", media_type="application/pdf")
