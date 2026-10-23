"""Rule-based behavioural detection. Re-evaluated after every logged event."""
import json, time
from db import query, execute

LEVELS = [(80, "CRITICAL"), (50, "HIGH"), (25, "MEDIUM"), (0, "LOW")]
HRI_POINTS = {"message_opened": 10, "link_clicked": 30, "form_interaction": 20,
              "credential_submission_attempt": 40}
SENSITIVE = ("pin_reset_requested", "pin_changed", "transfer_initiated")
RECOMMENDED = {
    "LOW": ["Keep monitoring the account"],
    "MEDIUM": ["Keep monitoring the account", "Ask the owner to confirm recent activity"],
    "HIGH": ["Require additional verification", "Notify the account owner",
             "Review recent account activity"],
    "CRITICAL": ["Temporarily restrict transfers", "Require additional verification",
                 "Notify the account owner", "Review recent account activity",
                 "Investigate the SIM re-registration"],
}


def level_for(score):
    for threshold, name in LEVELS:
        if score >= threshold:
            return name


def human_risk(user_id):
    """0-100. Each phishing behaviour counts once per user."""
    rows = query("SELECT DISTINCT event_type FROM events WHERE user_id=? AND source='phishing'",
                 (user_id,))
    return min(100, sum(HRI_POINTS.get(r["event_type"], 0) for r in rows))


def evaluate(user_id):
    rules = {r["id"]: r for r in query("SELECT * FROM rules")}
    now = time.time()
    last = query("SELECT MAX(updated) m FROM alerts WHERE user_id=? AND status='resolved'",
                 (user_id,), one=True)["m"] or 0
    since = max(now - 3600, last)
    evs = []
    for e in query("SELECT * FROM events WHERE user_id=? AND ts>? ORDER BY ts,id", (user_id, since)):
        d = dict(e)
        d["details"] = json.loads(d["details"] or "{}")
        evs.append(d)

    def of(*types):
        return [e for e in evs if e["event_type"] in types]

    def on(rid):
        return rid in rules and rules[rid]["enabled"]

    fired = {}
    if on("R1"):
        w = rules["R1"]["window_sec"]
        for p in of("pin_reset_requested"):
            for s in of("sim_reregistration"):
                d = p["ts"] - s["ts"]
                if 0 <= d <= w:
                    fired["R1"] = f"PIN reset requested {int(d)}s after a SIM re-registration (limit {w}s)."
    if on("R2"):
        w = rules["R2"]["window_sec"]
        f = of("pin_failed")
        if f:
            n = len([e for e in f if f[-1]["ts"] - e["ts"] <= w])
            if n >= 3:
                fired["R2"] = f"{n} wrong PIN entries within {w}s."
    if on("R3"):
        w = rules["R3"]["window_sec"]
        for s in of("session_created"):
            if s["details"].get("new_device"):
                for a in of(*SENSITIVE):
                    d = a["ts"] - s["ts"]
                    if 0 <= d <= w:
                        fired["R3"] = (f"{a['event_type'].replace('_', ' ')} came {int(d)}s after a "
                                       f"session from an unfamiliar handset.")
    if on("R4"):
        w = rules["R4"]["window_sec"]
        for s in of("sim_reregistration"):
            n = len([e for e in of("pin_reset_completed", "pin_changed", "transfer_initiated")
                     if 0 <= e["ts"] - s["ts"] <= w])
            if n >= 2:
                fired["R4"] = f"{n} account changes within {w}s of a SIM re-registration."
    if on("R5"):
        w = rules["R5"]["window_sec"]
        for r in of("pin_reset_completed"):
            for t in of("transfer_initiated"):
                d = t["ts"] - r["ts"]
                if 0 <= d <= w:
                    fired["R5"] = (f"Transfer of {t['details'].get('amount', '?')} ETB started "
                                   f"{int(d)}s after a PIN reset.")
    if on("R6") and fired:
        hri = human_risk(user_id)
        if hri >= 60:
            fired["R6"] = f"This user fell for a phishing simulation (Human Risk Index {hri}/100)."

    score = min(100, sum(rules[r]["points"] for r in fired))
    if score < 25:
        return None
    level = level_for(score)
    expl = [{"rule": r, "name": rules[r]["name"], "text": t} for r, t in fired.items()]
    open_a = query("SELECT * FROM alerts WHERE user_id=? AND status='open' ORDER BY id DESC LIMIT 1",
                   (user_id,), one=True)
    if open_a is None:
        aid = execute("INSERT INTO alerts(user_id,first_ts,updated,score,level,rules,explanation,"
                      "recommended) VALUES(?,?,?,?,?,?,?,?)",
                      (user_id, now, now, score, level, json.dumps(list(fired)), json.dumps(expl),
                       json.dumps(RECOMMENDED[level])))
        _mark(user_id, "alert_raised", level, score)
        return aid
    if open_a["score"] != score or set(json.loads(open_a["rules"])) != set(fired):
        execute("UPDATE alerts SET updated=?,score=?,level=?,rules=?,explanation=?,recommended=? "
                "WHERE id=?", (now, score, level, json.dumps(list(fired)), json.dumps(expl),
                               json.dumps(RECOMMENDED[level]), open_a["id"]))
        if level != open_a["level"]:
            _mark(user_id, "alert_escalated", level, score)
    return open_a["id"]


def _mark(user_id, etype, level, score):
    u = query("SELECT phone FROM users WHERE id=?", (user_id,), one=True)
    execute("INSERT INTO events(ts,source,event_type,user_id,phone,details) VALUES(?,?,?,?,?,?)",
            (time.time(), "detector", etype, user_id, u["phone"],
             json.dumps({"level": level, "score": score})))
