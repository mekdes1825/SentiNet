"""Part 2b: USSD-style mobile-money simulator with CONTROLLED weaknesses (lab only).
V1 PIN reset trusts the phone number alone   V2 sessions never expire, not bound to a device
V3 no lockout after wrong PINs               V4 PINs hashed with unsalted MD5
Set SENTINET_HARDENED=1 to switch V1 and V2 off."""
import json, re, time, uuid
from flask import Blueprint, jsonify, render_template, request
from db import (ATTACKER_DEVICE, HARDENED, PHONE_RE, VISIBLE, create_account, execute, query,
                weak_hash)
from events import log_event

bp = Blueprint("ussd", __name__)
MENU = ("SentiNet Mobile Money\n1. Check Balance\n2. Transfer Money\n3. Change PIN\n"
        "4. Reset PIN\n5. Account Information\n0. Exit")
IDLE_LIMIT = 120
NEW_PIN = "Enter new 4-digit PIN:"


def _user(phone):
    return query("SELECT * FROM users WHERE phone=?", (phone,), one=True)


def _save(sid, state, data, ended=0):
    execute("UPDATE sessions SET state=?,data=?,last_seen=?,ended=? WHERE id=?",
            (state, json.dumps(data), time.time(), ended, sid))


def process(phone, device_id, sid, text):
    u = _user(phone)
    if not u:
        return {"message": "Invalid number.", "end": True}
    if not sid:                                            # a new dial
        if device_id != u["device_id"]:
            log_event("ussd", "device_rejected", user_id=u["id"], device_id=device_id)
            return {"message": "No service. This handset is not registered for this number.",
                    "end": True}
        sid = uuid.uuid4().hex[:10]
        now = time.time()
        execute("INSERT INTO sessions(id,user_id,device_id,state,data,created,last_seen) "
                "VALUES(?,?,?,?,?,?,?)", (sid, u["id"], device_id, "menu", "{}", now, now))
        log_event("ussd", "session_created", user_id=u["id"], session_id=sid, device_id=device_id,
                  new_device=device_id != u["home_device"])
        return {"session_id": sid, "message": MENU, "end": False}

    s = query("SELECT * FROM sessions WHERE id=?", (sid,), one=True)
    if not s or s["ended"] or s["user_id"] != u["id"]:
        return {"message": "Session ended.", "end": True}
    if HARDENED and (time.time() - s["last_seen"] > IDLE_LIMIT or device_id != s["device_id"]):
        _save(sid, "done", {}, 1)
        return {"message": "Session expired.", "end": True}

    st, data, t = s["state"], json.loads(s["data"] or "{}"), (text or "").strip()
    ctx = dict(user_id=u["id"], session_id=sid, device_id=device_id)

    def go(state, msg, **upd):
        data.update(upd)
        _save(sid, state, data)
        return {"session_id": sid, "message": msg, "end": False}

    def end(msg):
        _save(sid, "done", data, 1)
        return {"session_id": sid, "message": msg, "end": True}

    def pin_ok():
        if weak_hash(t) == u["pin_hash"]:
            log_event("ussd", "auth_success", **ctx)
            return True
        log_event("ussd", "pin_failed", **ctx)
        return False

    if st == "menu":
        if t == "1": return go("bal_pin", "Enter PIN:")
        if t == "2": return go("tr_to", "Enter recipient number:")
        if t == "3": return go("chg_old", "Enter current PIN:")
        if t == "4":
            log_event("ussd", "pin_reset_requested", **ctx)
            if HARDENED:
                return go("rst_verify", "Verification: enter your birth year:")
            return go("rst_new", NEW_PIN)                  # V1: no further verification
        if t == "5":
            return end(f"Name: {u['name']}\nNumber: {u['phone']}\nHandset: {device_id}")
        if t == "0": return end("Goodbye.")
        return go("menu", "Invalid choice.\n" + MENU)

    if st == "bal_pin":
        if pin_ok():
            log_event("ussd", "balance_checked", **ctx)
            return end(f"Balance: {u['balance']:,.2f} ETB")
        return go("bal_pin", "Wrong PIN. Try again:")      # V3: unlimited attempts

    if st == "tr_to":
        to = _user(t)
        if not to and re.fullmatch(PHONE_RE, t):           # unknown but well-formed: make a fictional account
            create_account(f"External {t}", t, "0000", 0)
            to = _user(t)
        if not to or to["id"] == u["id"]:
            return go("tr_to", "Invalid number. Enter a 10-digit number, e.g. 0900000123:")
        return go("tr_amt", f"Send to {to['name']}.\nEnter amount (ETB):", to=to["id"])

    if st == "tr_amt":
        try:
            amt = round(float(t), 2)
        except ValueError:
            amt = 0
        if amt <= 0 or amt > u["balance"]:
            return go("tr_amt", "Invalid or insufficient amount. Enter amount (ETB):")
        return go("tr_pin", f"Enter PIN to send {amt:,.2f} ETB:", amount=amt)

    if st == "tr_pin":
        if not pin_ok():
            return go("tr_pin", "Wrong PIN. Try again:")
        amt, to_id = data["amount"], data["to"]
        log_event("ussd", "transfer_initiated", amount=amt, to_user=to_id, **ctx)
        fresh = _user(phone)
        if fresh["restricted"]:
            execute("INSERT INTO transactions(ts,from_user,to_user,amount,status) VALUES(?,?,?,?,?)",
                    (time.time(), u["id"], to_id, amt, "blocked"))
            log_event("ussd", "transfer_blocked", amount=amt, **ctx)
            return end("Transfers are temporarily restricted on this account. Contact support.")
        execute("UPDATE users SET balance=balance-? WHERE id=?", (amt, u["id"]))
        execute("UPDATE users SET balance=balance+? WHERE id=?", (amt, to_id))
        execute("INSERT INTO transactions(ts,from_user,to_user,amount,status) VALUES(?,?,?,?,?)",
                (time.time(), u["id"], to_id, amt, "completed"))
        log_event("ussd", "transfer_completed", amount=amt, to_user=to_id, **ctx)
        return end(f"Sent {amt:,.2f} ETB. New balance: {fresh['balance'] - amt:,.2f} ETB")

    if st == "chg_old":
        if pin_ok():
            return go("chg_new", NEW_PIN)
        return go("chg_old", "Wrong PIN. Try again:")

    if st == "chg_new":
        if not re.fullmatch(r"\d{4}", t):
            return go("chg_new", "PIN must be 4 digits. " + NEW_PIN)
        execute("UPDATE users SET pin_hash=? WHERE id=?", (weak_hash(t), u["id"]))
        log_event("ussd", "pin_changed", **ctx)
        return end("PIN changed.")

    if st == "rst_verify":
        if t == u["secret_answer"]:
            return go("rst_new", NEW_PIN)
        log_event("ussd", "reset_verification_failed", **ctx)
        return end("Verification failed.")

    if st == "rst_new":
        if not re.fullmatch(r"\d{4}", t):
            return go("rst_new", "PIN must be 4 digits. " + NEW_PIN)
        execute("UPDATE users SET pin_hash=? WHERE id=?", (weak_hash(t), u["id"]))
        log_event("ussd", "pin_reset_completed", **ctx)
        return end("PIN reset successful.")

    return end("Session ended.")


@bp.route("/phone")
def phone():
    users = query(f"SELECT id,name,phone,home_device FROM users WHERE {VISIBLE} ORDER BY id")
    return render_template("phone.html", users=users, attacker=ATTACKER_DEVICE)


@bp.route("/ussd/api", methods=["POST"])
def api():
    j = request.get_json(force=True)
    return jsonify(process(str(j.get("phone", "")).strip(), j.get("device_id", ""),
                           j.get("session_id"), j.get("text", "")))
