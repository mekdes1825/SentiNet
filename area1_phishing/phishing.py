"""Part 1: phishing simulation. Never reads or stores anything the participant types."""
import json, secrets, time
from flask import Blueprint, abort, redirect, render_template, request, url_for
from db import VISIBLE, execute, query
from detection import human_risk
from events import log_event

bp = Blueprint("phish", __name__)
FAKE_URL = "sentipay-verify.example/login"   # fictional, deliberately suspicious

SCENARIOS = {
    "verification": {"label": "Account verification", "flags": ["url", "generic", "urgency", "pin"],
        "en": "Dear customer, your SentiPay account needs verification. Confirm your details within 24 hours: {link}",
        "am": "ውድ ደንበኛ፣ የ SentiPay አካውንትዎ መረጋገጥ አለበት። በ24 ሰዓት ውስጥ መረጃዎን ያረጋግጡ፦ {link}"},
    "alert": {"label": "Security alert", "flags": ["url", "urgency", "pin", "sender"],
        "en": "SentiPay security alert: unusual activity was detected on your account. Secure it now: {link}",
        "am": "የ SentiPay የደህንነት ማስጠንቀቂያ፦ በአካውንትዎ ላይ ያልተለመደ እንቅስቃሴ ተገኝቷል። አሁኑኑ ያስጠብቁ፦ {link}"},
    "pinreset": {"label": "PIN-reset notice", "flags": ["url", "urgency", "pin", "sender"],
        "en": "We received a PIN reset request for your account. If this wasn't you, cancel it here: {link}",
        "am": "ለአካውንትዎ የ PIN ዳግም ማስጀመሪያ ጥያቄ ደርሶናል። እርስዎ ካልጠየቁ እዚህ ይሰርዙ፦ {link}"},
    "prize": {"label": "Prize message", "flags": ["url", "prize", "pin", "sender"],
        "en": "Congratulations! You won 5,000 ETB in the SentiPay lucky draw. Claim your prize: {link}",
        "am": "እንኳን ደስ አለዎት! በ SentiPay ዕጣ 5,000 ብር አሸንፈዋል። ሽልማትዎን ይቀበሉ፦ {link}"},
    "urgent": {"label": "Urgent account warning", "flags": ["url", "urgency", "generic", "pin"],
        "en": "URGENT: Your SentiPay account will be closed in 1 hour. Log in now to keep it: {link}",
        "am": "አስቸኳይ! የ SentiPay አካውንትዎ በ1 ሰዓት ውስጥ ይዘጋል። ለማስቀጠል አሁኑኑ ይግቡ፦ {link}"},
}
FLAGS = {
    "url": {"en": f"The link ({FAKE_URL}) is not an official SentiPay address.",
            "am": f"ሊንኩ ({FAKE_URL}) ኦፊሴላዊ የ SentiPay አድራሻ አይደለም።"},
    "urgency": {"en": "It pressures you to act immediately.",
                "am": "ወዲያውኑ እንዲያደርጉ ጫና ያደርጋል።"},
    "pin": {"en": "Real providers never ask for your PIN or OTP through a link.",
            "am": "እውነተኛ አገልግሎት ሰጪዎች PIN ወይም OTP በሊንክ በጭራሽ አይጠይቁም።"},
    "generic": {"en": "It greets you as 'customer' instead of using your name.",
                "am": "በስምዎ ሳይሆን 'ደንበኛ' ብሎ ሰላምታ ይሰጣል።"},
    "prize": {"en": "A prize you never entered for is classic bait.",
              "am": "ያልተሳተፉበት ሽልማት የተለመደ ማታለያ ነው።"},
    "sender": {"en": "The sender is an ordinary phone number, not the official short code.",
               "am": "ላኪው ኦፊሴላዊ አጭር ቁጥር ሳይሆን ተራ ስልክ ቁጥር ነው።"},
}
ACTION = {"en": "What to do: do not tap the link, call the official number on the back of your card, "
                "and report the message.",
          "am": "ምን ማድረግ፦ ሊንኩን አይጫኑ፣ ኦፊሴላዊውን ቁጥር ይደውሉ፣ መልዕክቱን ያሳውቁ።"}


def create_campaign(name, scenario, lang, user_ids):
    cid = execute("INSERT INTO campaigns(name,scenario,lang,created) VALUES(?,?,?,?)",
                  (name, scenario, lang, time.time()))
    tokens = {}
    for uid in user_ids:
        tok = secrets.token_urlsafe(6)
        execute("INSERT INTO targets(campaign_id,user_id,token) VALUES(?,?,?)", (cid, uid, tok))
        tokens[uid] = tok
    return cid, tokens


def campaign_results():
    seen = {}
    for e in query("SELECT user_id,event_type,details FROM events WHERE source='phishing'"):
        cid = json.loads(e["details"]).get("campaign_id")
        seen.setdefault((cid, e["user_id"]), set()).add(e["event_type"])
    out = []
    for c in query("SELECT * FROM campaigns ORDER BY id DESC LIMIT 5"):
        rows = []
        for t in query("SELECT t.token,u.id uid,u.name FROM targets t JOIN users u ON u.id=t.user_id "
                       "WHERE t.campaign_id=?", (c["id"],)):
            s = seen.get((c["id"], t["uid"]), set())
            rows.append({"name": t["name"], "token": t["token"], "opened": "message_opened" in s,
                         "clicked": "link_clicked" in s, "focus": "form_interaction" in s,
                         "submitted": "credential_submission_attempt" in s,
                         "hri": human_risk(t["uid"])})
        out.append({"c": c, "label": SCENARIOS[c["scenario"]]["label"], "rows": rows})
    return out


@bp.route("/admin/phishing", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST":
        ids = request.form.getlist("users", type=int)
        if not request.form.get("consent"):
            error = "Confirm that every participant has agreed to take part."
        elif not ids:
            error = "Pick at least one participant."
        elif request.form.get("scenario") not in SCENARIOS:
            error = "Pick a scenario."
        else:
            create_campaign(request.form.get("name") or "Untitled drill", request.form["scenario"],
                            "am" if request.form.get("lang") == "am" else "en", ids)
            return redirect(url_for("phish.admin"))
    users = query(f"SELECT id,name FROM users WHERE {VISIBLE} ORDER BY id")
    return render_template("phish_admin.html", users=users, scenarios=SCENARIOS,
                           results=campaign_results(), error=error)


def _target(token):
    t = query("SELECT t.token,t.user_id,t.campaign_id,c.scenario,c.lang FROM targets t "
              "JOIN campaigns c ON c.id=t.campaign_id WHERE t.token=?", (token,), one=True)
    if not t:
        abort(404)
    return t


def _log(t, etype):
    log_event("phishing", etype, user_id=t["user_id"], campaign_id=t["campaign_id"],
              scenario=t["scenario"])


@bp.route("/p/<token>")
def message(token):
    t = _target(token)
    _log(t, "message_opened")
    before, after = SCENARIOS[t["scenario"]][t["lang"]].split("{link}")
    return render_template("phish_msg.html", t=t, before=before, after=after, fake_url=FAKE_URL)


@bp.route("/p/<token>/login")
def login(token):
    t = _target(token)
    _log(t, "link_clicked")
    return render_template("phish_login.html", t=t)


@bp.route("/p/<token>/interact", methods=["POST"])
def interact(token):
    _log(_target(token), "form_interaction")
    return "", 204


@bp.route("/p/<token>/submit", methods=["POST"])
def submit(token):
    # request.form is deliberately never read: we record THAT a submission happened, not WHAT was typed.
    _log(_target(token), "credential_submission_attempt")
    return redirect(url_for("phish.learn", token=token))


@bp.route("/p/<token>/learn")
def learn(token):
    t = _target(token)
    _log(t, "teachable_moment_viewed")
    lang = t["lang"]
    flags = [FLAGS[f][lang] for f in SCENARIOS[t["scenario"]]["flags"]]
    return render_template("phish_learn.html", flags=flags, action=ACTION[lang], lang=lang)
