"""Helpers module."""


def get_risk_level(score: float) -> str:
    """Convert numerical risk score to risk level string."""
    if score >= 80:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    elif score >= 20:
        return "Low"
    return "Clean"


def generate_incident_id() -> str:
    """Generate a unique incident ID in TL-XXXX format."""
    import random
    return f"TL-{random.randint(1000, 9999)}"
