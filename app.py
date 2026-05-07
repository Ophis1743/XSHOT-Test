from flask import Flask, request
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ==================== CONFIG ====================
VERIFY_TOKEN = "trueice1743"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1321797789079961630/sg6geaquzxtWxUjky9vv072iB9Kd_jhDppFS-Di1glDqvqDbpD7uawGNI9gfWmk0nTA2"
FB_ACCESS_TOKEN = "	
1615491719732541|DSq6FKJnlVhPDHyKozND_ARH0Mc"   # ใช้ดึงชื่อคน
THAI_TZ = timezone(timedelta(hours=7))
# ================================================


def get_user_name(sender_id):
    """ดึงชื่อจริงจาก Facebook"""
    url = f"https://graph.facebook.com/{sender_id}"
    params = {
        "fields": "first_name,last_name",
        "access_token": FB_ACCESS_TOKEN
    }
    try:
        res = requests.get(url, params=params).json()
        return f"{res.get('first_name', '')} {res.get('last_name', '')}".strip()
    except:
        return f"Unknown ({sender_id})"


def get_thai_time():
    """เวลาปัจจุบันแบบไทย"""
    now = datetime.now(THAI_TZ)
    return now.strftime("%d/%m/%Y %H:%M:%S")


def send_to_discord(embed: dict):
    """ส่ง embed message ไป Discord"""
    payload = {"embeds": [embed]}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)


# ✅ Verify Webhook
@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == VERIFY_TOKEN:
        return challenge
    return 'Invalid token', 403


# 📩 รับ Events จาก Facebook
@app.route('/webhook', methods=['POST'])
def receive_event():
    data = request.json
    object_type = data.get('object')

    # --- Messages (คนทักมาใน Page) ---
    if object_type == 'page':
        for entry in data.get('entry', []):

            # 💬 Private Message
            for event in entry.get('messaging', []):
                if 'message' in event:
                    handle_message(event)

            # 🗨️ Comment ในโพสต์
            for change in entry.get('changes', []):
                if change.get('field') == 'feed':
                    val = change.get('value', {})
                    if val.get('item') == 'comment':
                        handle_comment(val)

    return 'OK', 200


def handle_message(event):
    """จัดการ Private Message"""
    sender_id = event['sender']['id']
    message_text = event.get('message', {}).get('text', '(ไม่มีข้อความ/เป็นสติกเกอร์หรือรูป)')
    attachments = event.get('message', {}).get('attachments', [])
    name = get_user_name(sender_id)
    time_str = get_thai_time()

    # ตรวจสอบ attachment
    extra = ""
    if attachments:
        types = [a.get('type', 'unknown') for a in attachments]
        extra = f"\n📎 **ไฟล์แนบ:** {', '.join(types)}"

    embed = {
        "title": "📩 มีคนทักมาใน Facebook Page!",
        "color": 0x1877F2,  # สีฟ้า Facebook
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
    """จัดการ Comment ในโพสต์"""
    sender_id = val.get('sender_id', 'unknown')
    sender_name = val.get('sender_name', get_user_name(sender_id))
    comment_text = val.get('message', '(ไม่มีข้อความ)')
    post_id = val.get('post_id', 'unknown')
    time_str = get_thai_time()

    embed = {
        "title": "🗨️ มีคนคอมเมนต์ในโพสต์!",
        "color": 0x42B72A,  # สีเขียว
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
