from flask import Flask, request
import requests
from datetime import datetime, timezone, timedelta
app = Flask(__name__)
VERIFY_TOKEN = "tokisaki"
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/epjeust6ue9o5hfhp7ilx2d1cqdlzv9u"  # ← ใส่ URL จาก Make
THAI_TZ = timezone(timedelta(hours=7))
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == VERIFY_TOKEN:
        return challenge
    return 'Invalid token', 403
@app.route('/webhook', methods=['POST'])
def receive_event():
    data = request.json
    # ส่งต่อไป Make โดยตรง
    requests.post(MAKE_WEBHOOK_URL, json=data)
    return 'OK', 200
if __name__ == '__main__':
    app.run(port=5000, debug=True)
