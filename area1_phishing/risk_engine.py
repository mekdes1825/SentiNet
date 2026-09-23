RISK_POINTS = {
    "phishing_viewed": 10,
    "phishing_clicked": 30,
    "form_submitted": 60
}


def calculate_risk(events):
    """
    Calculate the Human Risk Score for a simulation session.

    Each behavioral action contributes to the score only once.
    Repeated page refreshes therefore do not artificially
    increase the participant's risk score.

    Sensitive information such as passwords, PINs, and OTPs
    is never processed by this engine.
    """

    score = 0

    unique_events = set(events)

    for event in unique_events:
        score += RISK_POINTS.get(event, 0)

    return min(score, 100)


def get_risk_level(score):
    """
    Convert a numerical risk score into a human-readable level.
    """

    if score >= 70:
        return "High"

    if score >= 40:
        return "Medium"

    return "Low"