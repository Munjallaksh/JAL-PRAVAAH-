import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf_report(results: dict, output_pdf_path: str) -> str:
    """Generate professional PDF Decision Support & Executive Summary Report using ReportLab."""
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#475569')
    )
    heading_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0284c7'),
        fontName='Helvetica-Bold',
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica-Oblique'
    )

    story = []

    # Title Banner
    story.append(Paragraph("JAL PRAVAAH - DECISION-SUPPORT REPORT", title_style))
    story.append(Spacer(1, 4))
    dam_name = results.get("max_inundation", {}).get("features", [{}])[0].get("properties", {}).get("dam_name") or results.get("dam_name") or "Selected Dam"
    river_name = results.get("max_inundation", {}).get("features", [{}])[0].get("properties", {}).get("river_name") or results.get("river_name") or "Downstream River Reach"
    story.append(Paragraph(f"Scenario ID: <b>{results.get('job_id', 'SCN-2026-00001')}</b> | Engine: <b>{results.get('engine', 'SPH')}</b> | Domain: <b>{dam_name} ({river_name})</b>", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0ea5e9'), spaceBefore=4, spaceAfter=12))

    # Executive Summary Metrics Table
    impact = results.get("impact_summary", {})
    story.append(Paragraph("1. Executive Summary & Impact Key Metrics", heading_style))

    metrics_data = [
        ["Metric Indicator", "Value", "Metric Indicator", "Value"],
        ["Peak Flow Discharge", f"{results.get('peak_flow_cumecs', 0):,} m³/s", "Inundated Area", f"{impact.get('inundated_area_sqkm', 0.0)} km²"],
        ["Maximum Water Depth", f"{results.get('max_depth_m', 0.0)} m", "Population Exposed", f"{impact.get('population_exposed', 0):,} people"],
        ["Buildings Affected", f"{impact.get('buildings_affected', 0):,}", "Roads Flooded", f"{impact.get('roads_affected_km', 0.0)} km"],
        ["Bridges Cut Off", f"{impact.get('bridges_affected_count', 0)}", "Hospitals at Risk", f"{impact.get('hospitals_exposed_count', 0)}"]
    ]

    t_metrics = Table(metrics_data, colWidths=[140, 110, 140, 110])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 14))

    # HADR Emergency Priority Ranking
    story.append(Paragraph("2. HADR Emergency Response Priority Ranking", heading_style))

    hadr_list = results.get("hadr_priorities", [])[:6]
    hadr_table_data = [["Rank", "Settlement", "Priority", "Pop", "Arrival", "Max Depth", "Road Access"]]

    for idx, p in enumerate(hadr_list, start=1):
        hadr_table_data.append([
            f"#{idx}",
            p.get("name", "")[:22],
            p.get("priority_level", "").split()[0],
            f"{p.get('population', 0):,}",
            p.get("arrival_time_formatted", ""),
            f"{p.get('max_depth_m', 0.0)}m",
            p.get("road_access_status", "")
        ])

    t_hadr = Table(hadr_table_data, colWidths=[35, 145, 75, 60, 60, 60, 65])
    t_hadr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ffffff')),
    ]))
    story.append(t_hadr)
    story.append(Spacer(1, 14))

    # Model Provenance & Data Confidence
    story.append(Paragraph("3. Scientific Provenance & Model Uncertainty", heading_style))
    provenance_text = (
        f"<b>Model Engine:</b> {results.get('engine', 'SPH')}<br/>"
        f"<b>Data Provenance Tag:</b> {results.get('provenance', 'SIMULATION OUTPUT')}<br/>"
        f"<b>DEM Terrain:</b> Copernicus 30m Global Elevation Dataset<br/>"
        f"<b>Satellite Observation:</b> Sentinel-1 SAR C-band IW GRDH Change Detection<br/>"
    )
    story.append(Paragraph(provenance_text, body_style))
    story.append(Spacer(1, 14))

    # Mandatory Legal Disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=8, spaceAfter=8))
    disclaimer_text = (
        "<b>IMPORTANT NOTICE:</b> This report is generated by a decision-support prototype platform for emergency response "
        "planning and HADR resource allocation. Outputs represent modeled hydrodynamic estimations based on input geometry and DEM terrain profiles. "
        "This document does NOT constitute an official public warning or evacuation order. Official disaster advisories must be issued by "
        "authoritative disaster management authorities (NDMA / SDMA)."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    return output_pdf_path
