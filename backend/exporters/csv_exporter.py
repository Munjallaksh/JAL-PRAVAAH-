import csv
import io

def export_to_csv(results: dict) -> str:
    """Generate CSV string for HADR priorities and affected settlements."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Priority Rank", "Settlement Name", "District", "Priority Level",
        "Population Exposed", "Arrival Time (min)", "Max Flood Depth (m)",
        "Max Velocity (m/s)", "Hospitals at Risk", "Recommended HADR Action"
    ])

    priorities = results.get("hadr_priorities", [])
    for idx, p in enumerate(priorities, start=1):
        writer.writerow([
            idx,
            p.get("name"),
            p.get("district"),
            p.get("priority_level"),
            p.get("population"),
            p.get("arrival_time_min"),
            p.get("max_depth_m"),
            p.get("max_velocity_mps"),
            p.get("hospitals_at_risk"),
            p.get("recommended_action")
        ])

    return output.getvalue()
