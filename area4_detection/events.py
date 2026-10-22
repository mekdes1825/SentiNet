"""Single entry point for every event. Writes SQLite + a JSON-lines file, then runs detection."""
import json, logging, os, time
from db import BASE, query, execute
import detection

os.makedirs(os.path.join(BASE, "logs"), exist_ok=True)
logger = logging.getLogger("sentinet.events")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    h = logging.FileHandler(os.path.join(BASE, "logs", "events.jsonl"), encoding="utf-8")
    h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(h)


def log_event(source, event_type, user_id=None, session_id=None, device_id=None, **details):
    phone = None
    if user_id:
        u = query("SELECT phone FROM users WHERE id=?", (user_id,), one=True)
        phone = u["phone"] if u else None
    ts = time.time()
    eid = execute("INSERT INTO events(ts,source,event_type,user_id,phone,session_id,device_id,details)"
                  " VALUES(?,?,?,?,?,?,?,?)",
                  (ts, source, event_type, user_id, phone, session_id, device_id, json.dumps(details)))
    logger.info(json.dumps({"id": eid, "ts": ts, "source": source, "event": event_type,
                            "user_id": user_id, "session": session_id, "device": device_id,
                            "details": details}))
    if user_id:
        detection.evaluate(user_id)
    return eid
