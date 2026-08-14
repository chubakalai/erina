import os
from flask import Flask, send_file

app = Flask(__name__)

@app.route("/")
@app.route("/erina.html")
def serve_erina():
    return send_file("erina.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
