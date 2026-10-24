from flask import Flask, request, send_file, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import os, base64, datetime, binascii

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

SHOTS_DIR = os.environ.get("SHOTS_DIR", "shots")
os.makedirs(SHOTS_DIR, exist_ok=True)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

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

    files = sorted([f for f in os.listdir(SHOTS_DIR) if f.endswith(".jpg")], reverse=True)
    
    html = """
    <!doctype html>
    <html><head><title>Controller Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root { --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --accent: #38bdf8; --danger: #ef4444; }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: var(--accent); font-size: 24px; }
        .btn { background: var(--accent); color: #0f172a; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; text-decoration: none; font-size: 14px; transition: 0.2s; }
        .btn:hover { opacity: 0.8; }
        .btn-danger { background: var(--danger); color: white; width: 100%; margin-top: 10px; }
        
        .stats { display: flex; gap: 15px; margin-bottom: 20px; }
        .stat-box { background: var(--card); padding: 15px 25px; border-radius: 8px; flex: 1; border: 1px solid #334155; }
        .stat-box h3 { margin: 0 0 5px 0; font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .stat-box p { margin: 0; font-size: 28px; font-weight: bold; color: var(--accent); }

        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
        .card { background: var(--card); border-radius: 8px; padding: 15px; border: 1px solid #334155; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .card img { width: 100%; border-radius: 6px; aspect-ratio: 4/3; object-fit: cover; background: #000; }
        .card .info { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 12px; color: #94a3b8; }
        
        .empty { text-align: center; padding: 50px; color: #64748b; font-size: 18px; }
    </style>
    </head><body>
    
    <div class="header">
        <h1>📷 Controller Dashboard</h1>
        <div>
            <button class="btn" onclick="window.location.reload()">🔄 Refresh</button>
            <a href="/" class="btn" style="background:#334155; color:white;">Open Camera</a>
        </div>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>Total Captures</h3>
            <p>""" + str(len(files)) + """</p>
        </div>
        <div class="stat-box">
            <h3>Server Status</h3>
            <p style="color:#10b981">Online</p>
        </div>
    </div>

    <div class="grid">
    """
    
    if not files:
        html += "<div class='empty'>No photos captured yet. Open the camera link to take a photo.</div>"
    
    for f in files:
        html += f"""
        <div class="card">
            <img src="/shots/{f}" loading="lazy">
            <div class="info">
                <span>{f}</span>
            </div>
            <button class="btn btn-danger" onclick="delImg('{f}')">Delete Image</button>
        </div>
        """
    
    html += """
    </div>
    
    <script>
        async function delImg(fn) {
            if(confirm("Are you sure you want to delete this image?")) {
                try {
                    const res = await fetch("/delete/" + fn, { method: "DELETE" });
                    if(res.ok) { window.location.reload(); }
                    else { alert("Failed to delete."); }
                } catch(e) { alert("Error connecting to server."); }
            }
        }
    </script>
    </body></html>
    """
    return html

@app.route("/delete/<filename>", methods=["DELETE"])
def delete_shot(filename):
    auth = request.authorization
    if not check_auth(auth):
        return jsonify(error="Unauthorized"), 401

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
        try:
            img_data = base64.b64decode(b64)
            fn = f"{datetime.datetime.utcnow():%Y%m%d_%H%M%S_%f}.jpg"
            with open(os.path.join(SHOTS_DIR, fn), "wb") as f:
                f.write(img_data)
        except binascii.Error:
            return jsonify(error="Invalid base64"), 400
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
