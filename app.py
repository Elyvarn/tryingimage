from flask import Flask, request, send_file, jsonify, render_template_string
import os, base64, datetime

app = Flask(__name__)
SHOTS_DIR = os.environ.get("SHOTS_DIR", "shots")
os.makedirs(SHOTS_DIR, exist_ok=True)

@app.route("/")
def index():
    return send_file("index.html")

# --- CONTROLLER PAGE ---
@app.route("/gallery")
def gallery():
    files = sorted(os.listdir(SHOTS_DIR), reverse=True)
    html = "<h1>Captured Photos</h1>"
    html += "<p><a href='/'>Go to Camera</a></p><hr>"
    for f in files:
        if f.endswith(".jpg"):
            html += f"<div style='margin:10px; border:1px solid #ccc; padding:5px; display:inline-block;'>"
            html += f"<p>{f}</p><img src='/shots/{f}' width='300'></div>"
    if not files:
        html += "<p>No photos yet.</p>"
    return html

# --- SERVE THE IMAGES ---
@app.route("/shots/<filename>")
def serve_shot(filename):
    return send_file(os.path.join(SHOTS_DIR, filename))

@app.route("/shot", methods=["POST"])
def shot():
    data = request.get_json(force=True)
    b64 = (data.get("img") or "").split(",", 1)[-1]
    if b64:
        fn = f"{datetime.datetime.utcnow():%Y%m%d_%H%M%S_%f}.jpg"
        with open(os.path.join(SHOTS_DIR, fn), "wb") as f:
            f.write(base64.b64decode(b64))
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
