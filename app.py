from flask import Flask, request, send_file, jsonify
import os, base64, datetime, json

app = Flask(__name__)
SHOTS_DIR = os.environ.get("SHOTS_DIR", "shots")
os.makedirs(SHOTS_DIR, exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024  # 5 MB


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/shot", methods=["POST"])
def shot():
    if request.content_length and request.content_length > MAX_BYTES:
        return jsonify(error="payload too large"), 413

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify(error="bad json"), 400

    b64 = (data.get("img") or "").split(",", 1)[-1]
    if not b64:
        return jsonify(error="no image"), 400

    try:
        blob = base64.b64decode(b64)
    except Exception:
        return jsonify(error="bad base64"), 400

    fn = os.path.join(
        SHOTS_DIR,
        f"{datetime.datetime.utcnow():%Y%m%d_%H%M%S_%f}.jpg",
    )
    with open(fn, "wb") as f:
        f.write(blob)

    print("saved", fn, len(blob), "bytes", flush=True)
    return "", 204


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )
