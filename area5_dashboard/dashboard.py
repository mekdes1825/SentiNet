"""Part 3: dashboard pages and JSON API (the browser polls /api/state)."""
import json, time
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from db import VISIBLE, execute, query
from detection import human_risk
from events import log_event
from phishing import SCENARIOS

bp = Blueprint("dash", __name__)


def _alert(a):
    return {"id": a["id"], "user_id": a["user_id"], "user": a["name"], "phone": a["phone"],
            "score": a["score"], "level": a["level"], "rules": json.loads(a["rules"]),
            "explanation": json.loads(a["explanation"]), "recommended": json.loads(a["recommended"]),
            "status": a["status"], "first_ts": a["first_ts"], "updated": a["updated"],
            "restricted": bool(a["restricted"])}


ALERT_SQL = ("SELECT a.*,u.name,u.phone,u.restricted FROM alerts a JOIN users u ON u.id=a.user_id ")


@bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@bp.route("/api/state")
def state():
    alerts = [_alert(a) for a in query(ALERT_SQL + "ORDER BY (a.status='open') DESC, a.updated DESC LIMIT 30")]
    counts = {r["event_type"]: r["n"] for r in
              query("SELECT event_type, COUNT(*) n FROM events WHERE source<>'detector' "
                    "GROUP BY event_type")}
    target_ids = [r["user_id"] for r in query("SELECT DISTINCT user_id FROM targets")]
    hris = {uid: human_risk(uid) for uid in target_ids}
    open_alerts = [a for a in alerts if a["status"] == "open"]
    top = {}
    for a in open_alerts:
        top[a["user_id"]] = max(top.get(a["user_id"], 0), a["score"])

    users = []
    for u in query(f"SELECT * FROM users WHERE {VISIBLE} ORDER BY id"):
        users.append({"name": u["name"], "phone": u["phone"], "sim_state": u["sim_state"],
                      "device": u["device_id"], "hri": human_risk(u["id"]) if u["id"] in hris else None,
                      "risk": top.get(u["id"], 0), "restricted": bool(u["restricted"])})

    seen = {}
    for e in query("SELECT user_id,event_type,details FROM events WHERE source='phishing'"):
        seen.setdefault((json.loads(e["details"]).get("campaign_id"), e["user_id"]), set()).add(e["event_type"])
    by_scn = {}
    for t in query("SELECT t.user_id,t.campaign_id,c.scenario FROM targets t JOIN campaigns c ON c.id=t.campaign_id"):
        row = by_scn.setdefault(t["scenario"], [0, 0])
        row[0] += 1
        row[1] += "credential_submission_attempt" in seen.get((t["campaign_id"], t["user_id"]), set())
    scenario_rates = [{"scenario": SCENARIOS[k]["label"], "rate": round(100 * v[1] / v[0])}
                      for k, v in by_scn.items()]

    events = [{"id": e["id"], "ts": e["ts"], "source": e["source"], "type": e["event_type"],
               "user": e["name"], "details": json.loads(e["details"] or "{}")}
              for e in query("SELECT e.*,u.name FROM events e LEFT JOIN users u ON u.id=e.user_id "
                             "ORDER BY e.id DESC LIMIT 40")]
    return jsonify({
        "now": time.time(), "alerts": alerts, "users": users, "events": events,
        "counts": counts, "scenario_rates": scenario_rates,
        "metrics": {"active": len(open_alerts),
                    "top_level": max((a["level"] for a in open_alerts),
                                     key=lambda l: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(l), default="None"),
                    "hri": round(sum(hris.values()) / len(hris)) if hris else 0,
                    "sim": counts.get("sim_reregistration", 0),
                    "pin_reset": counts.get("pin_reset_requested", 0),
                    "failed": counts.get("pin_failed", 0),
                    "flagged_transfers": sum(1 for a in open_alerts if "R5" in a["rules"])}})


@bp.route("/api/alerts/<int:aid>")
def alert_detail(aid):
    a = query(ALERT_SQL + "WHERE a.id=?", (aid,), one=True)
    if not a:
        abort(404)
    tl = [{"ts": e["ts"], "source": e["source"], "type": e["event_type"],
           "details": json.loads(e["details"] or "{}")}
          for e in query("SELECT * FROM events WHERE user_id=? AND ts>=? ORDER BY ts,id LIMIT 80",
                         (a["user_id"], a["first_ts"] - 900))]
    return jsonify({"alert": _alert(a), "timeline": tl})


@bp.route("/api/alerts/<int:aid>/action", methods=["POST"])
def alert_action(aid):
    a = query("SELECT * FROM alerts WHERE id=?", (aid,), one=True)
    if not a:
        abort(404)
    act = (request.get_json(force=True) or {}).get("action")
    if act == "restrict":
        execute("UPDATE users SET restricted=1 WHERE id=?", (a["user_id"],))
        log_event("response", "transfers_restricted", user_id=a["user_id"])
    elif act == "release":
        execute("UPDATE users SET restricted=0 WHERE id=?", (a["user_id"],))
        log_event("response", "transfers_released", user_id=a["user_id"])
    elif act == "resolve":
        execute("UPDATE alerts SET status='resolved', updated=? WHERE id=?", (time.time(), aid))
    else:
        abort(400)
    return jsonify(ok=True)


@bp.route("/rules", methods=["GET", "POST"])
def rules():
    if request.method == "POST":
        rid = request.form["id"]
        execute("UPDATE rules SET window_sec=?, points=?, enabled=? WHERE id=?",
                (request.form.get("window_sec", type=int, default=0),
                 request.form.get("points", type=int, default=0),
                 1 if request.form.get("enabled") else 0, rid))
        return redirect(url_for("dash.rules"))
    return render_template("rules.html", rules=query("SELECT * FROM rules ORDER BY id"))
