from flask import Flask, redirect
import db

db.init_db()
from dashboard import bp as dash_bp
from demo import bp as demo_bp
from phishing import bp as phish_bp
from sim import bp as sim_bp
from ussd import bp as ussd_bp

app = Flask(__name__)
for b in (phish_bp, sim_bp, ussd_bp, dash_bp, demo_bp):
    app.register_blueprint(b)


@app.route("/")
def home():
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
