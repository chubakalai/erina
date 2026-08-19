import os
from flask import Flask, send_file, redirect, abort

app = Flask(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route("/<path:filename>")
def serve_html(filename):
    """
    Dynamically serve HTML files and handle redirects for clean URLs
    """
    # If filename ends with .html, redirect to clean URL
    if filename.endswith('.html'):
        clean_path = filename[:-5]  # Remove .html extension
        return redirect(f"/{clean_path}", code=301)
    
    # Try to serve the HTML file
    html_file = f"{filename}.html"
    file_path = os.path.join(BASE_DIR, html_file)
    
    # Check if file exists and is safe (prevent directory traversal)
    if os.path.isfile(file_path) and os.path.commonpath([BASE_DIR, file_path]) == BASE_DIR:
        return send_file(file_path)
    
    # If not found, try serving without .html extension
    if os.path.isfile(os.path.join(BASE_DIR, filename)):
        return send_file(os.path.join(BASE_DIR, filename))
    
    abort(404)

@app.route("/")
def index():
    """Serve index.html for the root route"""
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.isfile(index_path):
        return send_file(index_path)
    
    # List available HTML files if no index.html exists
    html_files = [f for f in os.listdir(BASE_DIR) if f.endswith('.html')]
    if html_files:
        links = "".join(f'<li><a href="/{f[:-5]}">{f}</a></li>' for f in sorted(html_files))
        return f"<h1>Available Pages</h1><ul>{links}</ul>"
    
    return "No HTML files found", 404

@app.errorhandler(404)
def not_found(e):
    return "Page not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
