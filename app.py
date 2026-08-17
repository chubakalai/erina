import os
from flask import Flask, send_file, redirect, abort

app = Flask(__name__)

# Base route default
@app.route("/")
def index():
    return redirect("/erina")

# Catch-all clean route (e.g. /erina, /11480, /erinacine-a-flash-chromatography-albreht-et-al)
@app.route("/<page_name>")
def serve_page(page_name):
    filename = f"{page_name}.html"
    if os.path.exists(filename):
        return send_file(filename)
    abort(404)

# Handle .html requests by redirecting to clean URLs
@app.route("/<page_name>.html")
def redirect_html(page_name):
    return redirect(f"/{page_name}", code=301)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
