from flask import Flask, request
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ==================== CONFIG ====================
VERIFY_TOKEN = "Tokisaki"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1321797789079961630/sg6geaquzxtWxUjky9vv072iB9Kd_jhDppFS-Di1glDqvqDbpD7uawGNI9gfWmk0nTA2"
FB_ACCESS_TOKEN = "EAAxpQGKiCoMBRZA77bWHjjh74ZASOO1DdJuSEfwhZALeZBMaJOwZCjnPceUZCNgwTsFvS9pEDcQCIcOCiZCO2dOyiTq20dRo967hL7NUxLzeTtPqx968gkX1zzz8JKDfay3gGeZCyLmyrP7TxTfAD6ZCQZCAxWEvtJLX7wp0Wxlk6AAskAZCxdDLHZCxM7YU7D1h8EZA2pIMXUa1v7ANJqBmiuJAnu6q2lQZDZD"
THAI_TZ = timezone(timedelta(hours=7))
# ================================================


def get_user_name(sender_id):
    url = f"https://graph.facebook.com/{sender_id}"
    params = {
        "fields": "first_name,last_name",
        "access_token": FB_ACCESS_TOKEN
    }
    try:
        res = requests.get(url, params=params).json()
        print("User data:", res)
        return f"{res.get('first_name', '')} {res.get('last_name', '')}".strip()
    except Exception as e:
        print("Error getting user:", e)
        return f"Unknown ({sender_id})"


def get_thai_time():
    now = datetime.now(THAI_TZ)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def send_to_discord(embed: dict):
    payload = {"embeds": [embed]}
    res = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print("Discord response:", res.status_code, res.text)


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
    print("=== Received data ===")
    print(data)
    object_type = data.get('object')
    print("Object type:", object_type)

    if object_type == 'page':
        for entry in data.get('entry', []):
            for event in entry.get('messaging', []):
                if 'message' in event:
                    handle_message(event)
            for change in entry.get('changes', []):
                if change.get('field') == 'feed':
                    val = change.get('value', {})
                    if val.get('item') == 'comment':
                        handle_comment(val)

    return 'OK', 200


def handle_message(event):
    sender_id = event['sender']['id']
    message_text = event.get('message', {}).get('text', '(ไม่มีข้อความ/เป็นสติกเกอร์หรือรูป)')
    attachments = event.get('message', {}).get('attachments', [])
    name = get_user_name(sender_id)
    time_str = get_thai_time()

    extra = ""
    if attachments:
        types = [a.get('type', 'unknown') for a in attachments]
        extra = f"\n📎 **ไฟล์แนบ:** {', '.join(types)}"

    embed = {
        "title": "📩 มีคนทักมาใน Facebook Page!",
        "color": 0x1877F2,
        "fields": [
            {"name": "👤 ชื่อ", "value": name, "inline": True},
            {"name": "🆔 Sender ID", "value": f"`{sender_id}`", "inline": True},
            {"name": "💬 ข้อความ", "value": message_text + extra, "inline": False},
            {"name": "🕐 เวลา (ไทย)", "value": time_str, "inline": False},
        ],
        "footer": {"text": "Facebook Messenger → Discord"}
    }
    send_to_discord(embed)


def handle_comment(val):
    sender_id = val.get('sender_id', 'unknown')
    sender_name = val.get('sender_name', get_user_name(sender_id))
    comment_text = val.get('message', '(ไม่มีข้อความ)')
    post_id = val.get('post_id', 'unknown')
    time_str = get_thai_time()

    embed = {
        "title": "🗨️ มีคนคอมเมนต์ในโพสต์!",
        "color": 0x42B72A,
        "fields": [
            {"name": "👤 ชื่อ", "value": sender_name, "inline": True},
            {"name": "🆔 Sender ID", "value": f"`{sender_id}`", "inline": True},
            {"name": "💬 คอมเมนต์", "value": comment_text, "inline": False},
            {"name": "📌 Post ID", "value": f"`{post_id}`", "inline": True},
            {"name": "🕐 เวลา (ไทย)", "value": time_str, "inline": True},
        ],
        "footer": {"text": "Facebook Comment → Discord"}
    }
    send_to_discord(embed)


if __name__ == '__main__':
    app.run(port=5000, debug=True)
