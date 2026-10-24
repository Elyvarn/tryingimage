from flask import Flask, request, send_file, jsonify, render_template_string, Response
import os, base64, datetime

app = Flask(__name__)
SHOTS_DIR = os.environ.get("SHOTS_DIR", "shots")
os.makedirs(SHOTS_DIR, exist_ok=True)

# SET THIS IN RENDER ENVIRONMENT VARIABLES. If not set, password is "admin123"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def check_auth(auth):
    return auth and auth.username == "admin" and auth.password == ADMIN_PASSWORD

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/gallery")
def gallery():
    auth = request.authorization
    if not check_auth(auth):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})

    files = sorted(os.listdir(SHOTS_DIR), reverse=True)
    
    html = """
    <!doctype html>
    <html><head><title>Admin Gallery</title>
    <style>
        body { font-family: system-ui; background: #0f172a; color: #e2e8f0; padding: 20px; }
        h1 { color: #38bdf8; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
        .card { background: #1e293b; padding: 10px; border-radius: 8px; text-align: center; }
        img { width: 100%; border-radius: 4px; }
        button { background: #ef4444; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer; width: 100%; margin-top: 10px; }
        button:hover { background: #dc2626; }
    </style>
    <script>
        // Auto refresh every 5 seconds
        setTimeout(() => { location.reload(); }, 5000);
        async function delImg(fn) {
            if(confirm("Delete this image?")) {
                await fetch("/delete/" + fn, { method: "DELETE" });
                location.reload();
            }
        }
    </script>
    </head><body>
    <h1>📷 Controller Gallery</h1>
    <p>Auto-refreshes every 5 seconds. <a href="/" style="color:#38bdf8">Go to Camera</a></p>
    <div class="grid">
    """
    
    if not files:
        html += "<p>No photos captured yet.</p>"
    
    for f in files:
        if f.endswith(".jpg"):
            html += f"""
            <div class="card">
                <img src="/shots/{f}">
                <p style="font-size:12px; opacity:0.7">{f}</p>
                <button onclick="delImg('{f}')">Delete</button>
            </div>
            """
    
    html += "</div></body></html>"
    return html

@app.route("/delete/<filename>", methods=["DELETE"])
def delete_shot(filename):
    auth = request.authorization
    if not check_auth(auth):
        return jsonify(error="Unauthorized"), 401

    # Security: prevent directory traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        return jsonify(error="Invalid filename"), 400
        
    filepath = os.path.join(SHOTS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify(success=True)
    return jsonify(error="Not found"), 404

@app.route("/shots/<filename>")
def serve_shot(filename):
    auth = request.authorization
    if not check_auth(auth):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})
    
    filepath = os.path.join(SHOTS_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify(error="Not found"), 404

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
