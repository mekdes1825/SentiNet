import os, sys

# The modules live in per-area folders but import each other with flat names
# (from db import ..., from events import ..., from detection import ...).
# area4_detection comes BEFORE sim_swap so `import events` resolves to
# area4_detection/events.py (log_event), not sim_swap/events.py.
ROOT = os.path.dirname(os.path.abspath(__file__))
AREAS = ["area4_detection", "area1_phishing", "area5_dashboard", "sim_swap"]
for _a in reversed(AREAS):
    sys.path.insert(0, os.path.join(ROOT, _a))

from flask import Flask, redirect
from jinja2 import ChoiceLoader, FileSystemLoader
import db

db.init_db()
from dashboard import bp as dash_bp
from demo import bp as demo_bp
from phishing import bp as phish_bp
from sim import bp as sim_bp
from ussd import bp as ussd_bp

# Shared CSS/JS live in area5_dashboard/static; templates are spread over the area folders.
app = Flask(__name__, static_folder=os.path.join(ROOT, "area5_dashboard", "static"))
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(ROOT, "templates")),
    FileSystemLoader(os.path.join(ROOT, "area1_phishing", "templates")),
    FileSystemLoader(os.path.join(ROOT, "area5_dashboard", "templates")),
])
for b in (phish_bp, sim_bp, ussd_bp, dash_bp, demo_bp):
    app.register_blueprint(b)


@app.route("/")
def home():
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)