import os
from functools import wraps
from flask import Flask, send_file, redirect, abort, jsonify, request, session, url_for

app = Flask(__name__)

# Required for session signing. Use a strong random key in production.
app.secret_key = os.environ.get("SECRET_KEY", "moria-secret-key-change-me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASEPICS_DIR = os.path.join(BASE_DIR, "basepics")

# Decorator to restrict routes to unlocked sessions
def require_unlocked(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("unlocked"):
            # Return 401 for API requests, redirect to / for page requests
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

# Verification endpoint called by index.html
@app.route("/api/verify-doors", methods=["POST"])
def verify_doors():
    data = request.get_json() or {}
    word = data.get("incantation", "").strip().lower()

    if word in ["mellon", "friend"]:
        session["unlocked"] = True  # Set session flag
        return jsonify({"success": True, "redirect": "/api/basepics"})

    return jsonify({"success": False, "message": "The stone remains silent."}), 401

# PROTECTED: Requires session["unlocked"] == True
@app.route("/basepics/<filename>")
@require_unlocked
def serve_basepic(filename):
    file_path = os.path.join(BASEPICS_DIR, filename)
    if os.path.isfile(file_path) and os.path.commonpath([BASEPICS_DIR, file_path]) == BASEPICS_DIR:
        return send_file(file_path)
    abort(404)

# PROTECTED: Requires session["unlocked"] == True
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
