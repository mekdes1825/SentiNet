"""Part 2a: simulated SIM re-registration (a state change on a fictional number)."""
import re
from flask import Blueprint, redirect, render_template, request, url_for
from db import ATTACKER_DEVICE, PHONE_RE, VISIBLE, create_account, execute, query, weak_hash
from events import log_event

bp = Blueprint("sim", __name__)


def swap(user_id, to_state="attacker"):
    u = query("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    new_dev = ATTACKER_DEVICE if to_state == "attacker" else u["home_device"]
    execute("UPDATE users SET sim_state=?, device_id=? WHERE id=?",
            ("attacker" if to_state == "attacker" else "victim", new_dev, user_id))
    etype = "sim_reregistration" if to_state == "attacker" else "sim_restored"
    log_event("sim", etype, user_id=user_id, device_id=new_dev, from_state=u["sim_state"],
              to_state=to_state, old_device=u["device_id"], new_device=new_dev)


@bp.route("/sim")
def page():
    users = query(f"SELECT * FROM users WHERE {VISIBLE} ORDER BY id")
    return render_template("sim.html", users=users, error=request.args.get("error"))


@bp.route("/sim/add", methods=["POST"])
def add():
    f = request.form
    name, phone, pin = f.get("name", "").strip(), f.get("phone", "").strip(), f.get("pin", "").strip()
    bal = f.get("balance", type=float, default=0)
    err = None
    if not name:
        err = "Enter a name."
    elif not re.fullmatch(PHONE_RE, phone):
        err = "Number must be 10 digits starting with 09, for example 0900000123."
    elif not re.fullmatch(r"\d{4}", pin):
        err = "PIN must be 4 digits."
    elif bal < 0:
        err = "Balance cannot be negative."
    if err:
        return redirect(url_for("sim.page", error=err))
    old = query("SELECT * FROM users WHERE phone=?", (phone,), one=True)
    if old and not old["name"].startswith("External "):
        return redirect(url_for("sim.page", error="That number already has an account."))
    if old:        # upgrade an auto-created recipient to a full account
        execute("UPDATE users SET name=?, pin_hash=?, balance=balance+? WHERE id=?",
                (name, weak_hash(pin), bal, old["id"]))
    else:
        create_account(name, phone, pin, bal)
    return redirect(url_for("sim.page"))


@bp.route("/sim/<int:uid>/swap", methods=["POST"])
def do_swap(uid):
    swap(uid, "attacker")
    return redirect(url_for("sim.page"))


@bp.route("/sim/<int:uid>/restore", methods=["POST"])
def do_restore(uid):
    swap(uid, "victim")
    return redirect(url_for("sim.page"))
