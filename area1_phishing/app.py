from flask import Flask, render_template, request, session, redirect, jsonify
import uuid

from database import (
    init_database,
    record_event,
    get_session_events,
    get_session_event_details,
    create_campaign,
    get_campaign,
    get_active_campaigns
)

from risk_engine import calculate_risk, get_risk_level, RISK_POINTS

app = Flask(__name__)
app.secret_key = "sentinet-development-key"

init_database()


@app.route("/")
def home():
    language = request.args.get("lang", "en")

    if language not in ["en", "am"]:
        language = "en"

    return render_template("index.html", language=language)


@app.route("/admin")
def admin():
    campaigns = get_active_campaigns()

    return render_template(
        "admin.html",
        campaigns=campaigns
    )


@app.route("/admin/campaigns", methods=["POST"])
def create_campaign_route():
    name = request.form.get("name", "").strip()
    language = request.form.get("language", "en").strip()
    sender = request.form.get("sender", "").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()
    warning = request.form.get("warning", "").strip()
    button_text = request.form.get("button_text", "").strip()

    if language not in ["en", "am"]:
        language = "en"

    if not name or not sender or not subject or not message or not button_text:
        return "Required campaign information is missing.", 400

    campaign_id = create_campaign(
        name=name,
        language=language,
        sender=sender,
        subject=subject,
        message=message,
        warning=warning,
        button_text=button_text
    )

    return redirect(f"/admin?created={campaign_id}")


@app.route("/start")
def start_simulation():
    session["session_id"] = uuid.uuid4().hex

    campaign_id = request.args.get("campaign_id")

    if campaign_id:
        try:
            campaign_id = int(campaign_id)
        except ValueError:
            campaign_id = None

    if campaign_id:
        campaign = get_campaign(campaign_id)

        if campaign is None or not campaign["active"]:
            return "Campaign not found or inactive.", 404

        session["campaign_id"] = campaign_id
        session["language"] = campaign["language"]

        return redirect("/phishing")

    language = request.args.get("lang", "en")

    if language not in ["en", "am"]:
        language = "en"

    session["language"] = language
    session.pop("campaign_id", None)

    return redirect(f"/phishing?lang={language}")


@app.route("/phishing")
def phishing():
    if "session_id" not in session:
        session["session_id"] = uuid.uuid4().hex

    language = session.get(
        "language",
        request.args.get("lang", "en")
    )

    if language not in ["en", "am"]:
        language = "en"

    session["language"] = language

    campaign = None

    campaign_id = session.get("campaign_id")

    if campaign_id:
        campaign = get_campaign(campaign_id)

        if campaign is None or not campaign["active"]:
            session.pop("campaign_id", None)
            campaign = None

    record_event(
        "phishing_viewed",
        session["session_id"]
    )

    return render_template(
        "phishing.html",
        language=language,
        campaign=campaign
    )


@app.route("/phishing-click")
def phishing_click():
    if "session_id" not in session:
        return redirect("/")

    language = session.get(
        "language",
        request.args.get("lang", "en")
    )

    if language not in ["en", "am"]:
        language = "en"

    session["language"] = language

    record_event(
        "phishing_clicked",
        session["session_id"]
    )

    return render_template(
        "mock_login.html",
        language=language
    )


@app.route("/mock-login", methods=["GET", "POST"])
def mock_login():
    if "session_id" not in session:
        return redirect("/")

    language = session.get(
        "language",
        request.form.get("language", "en")
    )

    if language not in ["en", "am"]:
        language = "en"

    if request.method == "POST":
        user_id = request.form.get(
            "user_id",
            ""
        ).strip()

        record_event(
            "form_submitted",
            session["session_id"],
            user_id if user_id else None
        )

        events = get_session_events(
            session["session_id"]
        )

        score = calculate_risk(events)
        risk_level = get_risk_level(score)

        event_breakdown = []

        for event_type, points in RISK_POINTS.items():
            event_breakdown.append({
                "event_type": event_type,
                "points": points,
                "occurred": event_type in events
            })

        return render_template(
            "result.html",
            score=score,
            risk_level=risk_level,
            language=language,
            event_breakdown=event_breakdown
        )

    return render_template(
        "mock_login.html",
        language=language
    )


@app.route("/api/events/<session_id>")
def session_events_api(session_id):
    events = get_session_event_details(session_id)

    return jsonify({
        "session_id": session_id,
        "events": events
    })


@app.route("/api/risk/<session_id>")
def session_risk_api(session_id):
    events = get_session_events(session_id)

    score = calculate_risk(events)
    risk_level = get_risk_level(score)

    return jsonify({
        "session_id": session_id,
        "score": score,
        "risk_level": risk_level
    })


if __name__ == "__main__":
    app.run(debug=True)