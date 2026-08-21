import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, send_file, redirect, abort, jsonify, request, session, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-key-for-dev")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASEPICS_DIR = os.path.join(BASE_DIR, "basepics")

def require_unlocked(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("unlocked"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Speak 'friend' first."}), 401
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    abort(404)

@app.route("/api/verify-doors", methods=["POST"])
def verify_doors():
    data = request.get_json() or {}
    # Convert 'l' or '|' back to 'i' for validation
    raw_word = data.get("incantation", "").strip().lower()
    normalized_word = raw_word.replace("|", "i").replace("l", "i")

    if normalized_word == "friend":
        session["unlocked"] = True
        return jsonify({"success": True, "redirect": "/api/basepics"})

    return jsonify({"success": False, "message": "The stone remains silent."}), 401

@app.route("/basepics/<filename>")
@require_unlocked
def serve_basepic(filename):
    file_path = os.path.join(BASEPICS_DIR, filename)
    if os.path.isfile(file_path) and os.path.commonpath([BASEPICS_DIR, file_path]) == BASEPICS_DIR:
        return send_file(file_path)
    abort(404)

@app.route("/api/basepics")
@require_unlocked
def list_basepics():
    if not os.path.exists(BASEPICS_DIR):
        return jsonify([])
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    images = [
        f for f in os.listdir(BASEPICS_DIR) 
        if f.lower().endswith(valid_extensions)
    ]
    return jsonify(images)

@app.route("/<path:filename>")
def serve_html(filename):
    if filename.endswith('.html'):
        return redirect(f"/{filename[:-5]}", code=301)
    
    html_file = f"{filename}.html"
    file_path = os.path.join(BASE_DIR, html_file)
    
    if os.path.isfile(file_path) and os.path.commonpath([BASE_DIR, file_path]) == BASE_DIR:
        return send_file(file_path)
    
    direct_path = os.path.join(BASE_DIR, filename)
    if os.path.isfile(direct_path) and os.path.commonpath([BASE_DIR, direct_path]) == BASE_DIR:
        return send_file(direct_path)
    
    abort(404)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
