from flask import Flask, request, jsonify
from flask_cors import CORS
import time, db

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)
db.init()

# session_id -> last click timestamp
_rate = {}
COOLDOWN = 3  # seconds

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/click", methods=["POST"])
def click():
    data = request.get_json(silent=True) or {}
    sid = str(data.get("session_id", "anon"))[:64]
    now = time.time()
    last = _rate.get(sid, 0)
    if now - last < COOLDOWN:
        return jsonify({"ok": False, "wait": round(COOLDOWN - (now - last), 1)}), 429
    _rate[sid] = now
    return jsonify({"ok": True})

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}
    nick = str(data.get("nick", "")).strip().upper()[:4]
    score = int(data.get("score", 0))
    if len(nick) < 1 or score < 1:
        return jsonify({"ok": False, "error": "invalid"}), 400
    db.submit(nick, score)
    return jsonify({"ok": True})

@app.route("/leaderboard")
def leaderboard():
    return jsonify(db.leaderboard())

@app.route("/health")
def health():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
