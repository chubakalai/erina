import os
from flask import Flask, send_file, redirect

app = Flask(__name__)

# Erina routes
@app.route("/erina")
def serve_erina():
    return send_file("erina.html")

@app.route("/erina.html")
def redirect_erina():
    return redirect("/erina", code=301)

# Erinacine A Chromatography routes
@app.route("/erinacine-a-flash-chromatography-albreht-et-al")
def serve_chromatography():
    return send_file("erinacine-a-flash-chromatography-albreht-et-al.html")

@app.route("/erinacine-a-flash-chromatography-albreht-et-al.html")
def redirect_chromatography():
    return redirect("/erinacine-a-flash-chromatography-albreht-et-al", code=301)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
