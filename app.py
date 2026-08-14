import os
from flask import Flask, send_file, redirect

app = Flask(__name__)

# Primary route serving the file
@app.route("/erina")
def serve_erina():
    return send_file("erina.html")

# Redirect /erina.html to /erina
@app.route("/erina.html")
def redirect_erina():
    return redirect("/erina", code=301)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
