"""Scripted scenarios that drive the real routes, so the dashboard has live data to react to."""
import threading, time
from flask import Blueprint, abort, current_app, jsonify, render_template
from db import ATTACKER_DEVICE, SEED_USERS, query, reset_db
from phishing import create_campaign

bp = Blueprint("demo", __name__)
PAUSE = 1.5
_lock = threading.Lock()
PINS = {i: s[2] for i, s in enumerate(SEED_USERS, start=1)}


def user(i):
    return query("SELECT * FROM users WHERE id=?", (i,), one=True)


def call(c, i, device, steps):
    u, sid, last = user(i), None, None
    for text in steps:                       # first step "" = dial
        last = c.post("/ussd/api", json={"phone": u["phone"], "device_id": device,
                                         "session_id": sid, "text": text}).get_json()
        sid = last.get("session_id")
        if last["end"]:
            break
    time.sleep(PAUSE)
    return last


def drill(c):
    _, tokens = create_campaign("Awareness drill", "verification", "am", [1, 2, 3, 4, 5, 6])
    depth = {1: 4, 2: 1, 3: 2, 4: 3, 5: 0, 6: 1}          # how far each participant went
    for uid, d in depth.items():
        t = tokens[uid]
        if d >= 1: c.get(f"/p/{t}")
        if d >= 2: c.get(f"/p/{t}/login")
        if d >= 3: c.post(f"/p/{t}/interact")
        if d >= 4:
            c.post(f"/p/{t}/submit"); c.get(f"/p/{t}/learn")
        time.sleep(0.4)


def normal(c):
    call(c, 2, "DEV-HOME-02", ["", "1", PINS[2]])                         # balance
    call(c, 3, "DEV-HOME-03", ["", "2", "0900000004", "200", PINS[3]])    # small transfer
    call(c, 6, "DEV-HOME-06", ["", "3", PINS[6], "5555"])                 # PIN change
    call(c, 4, "DEV-HOME-04", ["", "1", "0000", PINS[4]])                 # one typo, then OK


def brute(c):
    call(c, 5, "DEV-HOME-05", ["", "1", "0001", "0002", "0003"])          # three wrong PINs


def attack(c):
    c.post("/sim/1/swap"); time.sleep(PAUSE)                              # SIM re-registration
    call(c, 1, ATTACKER_DEVICE, ["", "4", "9999"])                        # reset the victim's PIN
    call(c, 1, ATTACKER_DEVICE, ["", "2", "0900000099", "8000", "9999"])  # drain attempt


SCENARIOS = {"drill": [drill], "normal": [normal], "brute": [brute], "attack": [attack],
             "full": [drill, normal, attack]}


@bp.route("/demo")
def page():
    return render_template("demo.html")


@bp.route("/demo/run/<name>", methods=["POST"])
def run(name):
    if name not in SCENARIOS:
        abort(404)
    if not _lock.acquire(blocking=False):
        return jsonify(ok=False, msg="A scenario is already running."), 409
    app = current_app._get_current_object()

    def work():
        try:
            c = app.test_client()
            for fn in SCENARIOS[name]:
                fn(c)
        finally:
            _lock.release()
    threading.Thread(target=work, daemon=True).start()
    return jsonify(ok=True)


@bp.route("/demo/reset", methods=["POST"])
def reset():
    reset_db()
    return jsonify(ok=True)
