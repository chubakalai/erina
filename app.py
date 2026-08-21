import os
from flask import Flask, send_file, redirect, abort, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASEPICS_DIR = os.path.join(BASE_DIR, "basepics")

# Serve static images from /basepics/
@app.route("/basepics/<filename>")
def serve_basepic(filename):
    file_path = os.path.join(BASEPICS_DIR, filename)
    if os.path.isfile(file_path) and os.path.commonpath([BASEPICS_DIR, file_path]) == BASEPICS_DIR:
        return send_file(file_path)
    abort(404)

# API endpoint to list all .png and .jpg images
@app.route("/api/basepics")
def list_basepics():
    if not os.path.exists(BASEPICS_DIR):
        return jsonify([])
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    images = [
        f for f in os.listdir(BASEPICS_DIR) 
        if f.lower().endswith(valid_extensions)
    ]
    return jsonify(images)

@app.route("/")
def index():
    # Serves index.html as the home page if accessed at /
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        return send_file(index_path)
    abort(404)

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
