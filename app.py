import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN      = os.environ.get("VERIFY_TOKEN", "czonedive_webhook_2025")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")

BUSINESS_INFO = """You are the CZone Dive assistant — a friendly, helpful bot for CZone Dive, 
a SSI-certified scuba diving school located at Mae Haad pier, Koh Tao, Thailand.

COURSES & PRICES (use these when presenting to customers):
🤿 CZone Dive — เกาะเต่า 🏝️

🐠 Try Scuba — 2,500฿ (ไม่ต้องมีประสบการณ์!)
🌊 Open Water Diver — 11,900฿ (3 วัน 5 ไดฟ์)
🔄 Refresher Dive — 2,100฿ (ครึ่งวัน)
⭐ Advanced — 11,000฿ (2 วัน 5 ไดฟ์)
🚑 EFR — 4,000฿ (1 วัน)
🦸 Rescue Diver — 11,000฿ (2 วัน)
🎓 Divemaster — 45,000฿ (3-6 สัปดาห์)
🐡 Fun Dive — 2,000฿ (2 ไดฟ์)

BOOKING PROCESS (use this when customer wants to book):
📌 ขั้นตอนการจอง 🥰

💰 มัดจำท่านละ 1,000 บาท ส่วนที่เหลือจ่ายที่เกาะ
❌ ไม่ refund แต่เลื่อนวัน / เปลี่ยนคนได้นะคะ 😊

🏦 โอนมาที่
กสิกรไทย 177-326-6286 💳
ชัยศักดิ์ อินมุตโต

📲 ส่งสลิป + ชื่อ + เบอร์ แอดจะส่งวอยเชอร์ให้เลยค่า 🎟️✨

CONTACT:
- Facebook: facebook.com/czonedivermaehaad
- Instagram: @czonediver.maehaad
- WhatsApp: +66 81 231 4842
- Email: czonedive@gmail.com
- Location: Mae Haad pier, Koh Tao, Surat Thani, Thailand

RULES:
1. Answer in the SAME language the customer uses (Thai or English)
2. Keep responses short (2-4 sentences)
3. For business questions use info above
4. For other questions (travel, weather etc) answer freely
5. Always end with a call to action"""

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    body = request.get_json()
    if body.get("object") in ("page", "instagram"):
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and not event["message"].get("is_echo"):
                    sender_id = event["sender"]["id"]
                    text = event["message"].get("text", "")
                    if text:
                        reply = generate_reply(text)
                        send_message(sender_id, reply)
    return "OK", 200

def generate_reply(user_message: str) -> str:
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": BUSINESS_INFO},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 300
            }
        )
        data = response.json()
        print(f"Groq raw response: {data}")
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        print(f"Groq raw response: {response.text}")
        return "ขออภัยครับ ระบบมีปัญหาชั่วคราว กรุณาติดต่อ +66 81 231 4842 หรือ czonedive@gmail.com 🤿"

def send_message(recipient_id: str, text: str):
    url = "https://graph.facebook.com/v21.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }
    params = {"access_token": PAGE_ACCESS_TOKEN}
    try:
        r = requests.post(url, json=payload, params=params)
        print(f"Sent: {r.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "CZone Dive Bot running 🤿", "version": "2.1"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
