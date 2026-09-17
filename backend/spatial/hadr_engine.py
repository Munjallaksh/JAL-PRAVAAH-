from typing import List, Dict, Any

def compute_hadr_priorities(villages: List[Dict[str, Any]], impact_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute HADR (Humanitarian Assistance & Disaster Relief) Priority Ranks for affected settlements.
    
    Scoring Formula:
    Score = (Pop / 1000) * 2.5 + MaxDepth * 4.0 + (MaxVel) * 2.0 + (10 / (ArrivalHours + 0.1)) * 3.0 + InfraWeight
    
    Disclaimer: Decision-support output — not an authoritative evacuation order.
    """
    prioritized_list = []

    for v in villages:
        props = v.get("properties", {})
        pop = props.get("population", 0)
        depth = props.get("flood_depth_m", 0.0)
        vel = props.get("velocity_mps", 0.0)
        arrival_min = props.get("arrival_time_min", 999)
        arrival_hrs = arrival_min / 60.0
        hospitals = props.get("hospital_count", 0)
        schools = props.get("school_count", 0)
        criticality = props.get("criticality", "MEDIUM")

        if depth <= 0.05 and arrival_min > 360:
            continue  # Minimal exposure

        # Multi-factor score
        pop_score = (pop / 500.0) * 2.5
        depth_score = min(depth, 10.0) * 4.0
        vel_score = min(vel, 8.0) * 2.0
        time_urgency = (10.0 / (arrival_hrs + 0.2)) * 3.5
        infra_score = hospitals * 8.0 + schools * 2.0

        if criticality == "CRITICAL":
            infra_score += 15.0

        total_score = round(pop_score + depth_score + vel_score + time_urgency + infra_score, 1)

        # Categorize Priority
        if total_score >= 65.0 or (arrival_hrs < 1.5 and pop > 5000):
            priority_level = "PRIORITY 1 (CRITICAL)"
            color = "#ef4444"  # Red
            action = "Immediate air evacuation & mass flood warning alert dispatch. Deploy NDRF swift water rescue boats."
        elif total_score >= 35.0 or (arrival_hrs < 3.0 and pop > 1000):
            priority_level = "PRIORITY 2 (HIGH)"
            color = "#f97316"  # Orange
            action = "Pre-position medical rapid response teams & establish high-ground shelter staging centers."
        else:
            priority_level = "PRIORITY 3 (MEDIUM)"
            color = "#eab308"  # Yellow
            action = "Monitor wave propagation timeline & issue precautionary road closure notifications."

        # Format arrival time display
        if arrival_min < 60:
            arrival_str = f"{int(arrival_min)} mins"
        else:
            hrs = int(arrival_min // 60)
            mins = int(arrival_min % 60)
            arrival_str = f"{hrs}h {mins}m"

        prioritized_list.append({
            "settlement_id": props.get("id"),
            "name": props.get("name"),
            "district": props.get("district"),
            "score": total_score,
            "priority_level": priority_level,
            "badge_color": color,
            "population": pop,
            "arrival_time_min": arrival_min,
            "arrival_time_formatted": arrival_str,
            "max_depth_m": round(depth, 2),
            "max_velocity_mps": round(vel, 2),
            "hospitals_at_risk": hospitals,
            "recommended_action": action,
            "road_access_status": "CUT_OFF" if depth > 1.2 or vel > 3.0 else ("HAZARDOUS" if depth > 0.5 else "ACCESSIBLE"),
            "coordinates": v.get("geometry", {}).get("coordinates", [])
        })

    # Sort descending by priority score
    prioritized_list.sort(key=lambda x: x["score"], reverse=True)
    return prioritized_list
