import os
import json
import hmac
import hashlib
import requests
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# ============================================================
# CONFIG — set these as Environment Variables on Render
# ============================================================
VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "czonedive_webhook_2025")
PAGE_ACCESS_TOKEN  = os.environ.get("PAGE_ACCESS_TOKEN", "")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
APP_SECRET         = os.environ.get("APP_SECRET", "")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# CZONE DIVE KNOWLEDGE BASE
# ============================================================
BUSINESS_INFO = """
You are the CZone Dive assistant — a friendly, helpful bot for CZone Dive, 
a SSI-certified scuba diving school located at Mae Haad pier, Koh Tao, Thailand.

COURSES & PRICES:
- Try Scuba: 1 day, ฿2,500/person (no experience needed)
- Open Water Diver (OW): 3 days, 5 dives, ฿11,900/person
- Refresher Dive: half day, 1 dive, ฿2,100/person
- Advanced Adventurer (AOW): 2 days, 5 dives, ฿11,000/person
- Emergency First Response (EFR): 1 day, no diving, ฿4,000/person
- Rescue Diver: 2 days, 4 dives, ฿11,000/person
- Divemaster: 3-6 weeks, ฿45,000/person
- Fun Dive: 2 dives, ฿2,000/person (certified divers only, OW required)

CONTACT:
- Facebook: facebook.com/czonedivermaehaad
- Instagram: @czonediver.maehaad
- WhatsApp: +66 81 231 4842
- Email: czonedive@gmail.com
- Location: Mae Haad pier, Koh Tao, Surat Thani, Thailand

BOOKING:
- Contact via Facebook, Instagram, WhatsApp or Email
- All equipment included in course prices
- SSI certified instructors
- Small groups (max 4 students per instructor)
- Teaching in English

RULES FOR RESPONDING:
1. If asked about courses, prices, booking, diving schedules, equipment, 
   or anything related to CZone Dive business — answer using the info above.
2. If asked about travel to Koh Tao, weather, local activities, restaurants, 
   accommodation, or general questions — answer helpfully and freely.
3. Always be friendly and encouraging. Use occasional emojis 🤿🌊
4. Keep responses concise (2-4 sentences max for simple questions).
5. Always end business-related replies with a call to action 
   (book now, contact us, etc).
6. Reply in the SAME language the customer uses (Thai or English).
"""

# ============================================================
# WEBHOOK VERIFICATION
# ============================================================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode  = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


# ============================================================
# RECEIVE MESSAGES
# ============================================================
@app.route("/webhook", methods=["POST"])
def receive_message():
    body = request.get_json()
    print(f"📩 Incoming: {json.dumps(body, indent=2)}")

    if body.get("object") in ("page", "instagram"):
        for entry in body.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event and not event["message"].get("is_echo"):
                    sender_id = event["sender"]["id"]
                    text = event["message"].get("text", "")
                    if text:
                        reply = generate_reply(text)
                        send_message(sender_id, reply)

            # Instagram uses different structure
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    sender_id = msg.get("sender", {}).get("id") or msg.get("from", {}).get("id")
                    text = msg.get("text", {})
                    if isinstance(text, dict):
                        text = text.get("body", "")
                    if text and sender_id:
                        reply = generate_reply(text)
                        send_message(sender_id, reply)

    return "OK", 200


# ============================================================
# GENERATE REPLY WITH CLAUDE
# ============================================================
def generate_reply(user_message: str) -> str:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=BUSINESS_INFO,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"❌ Claude error: {e}")
        return "Sorry, we're having a technical issue. Please contact us directly at +66 81 231 4842 or czonedive@gmail.com 🤿"


# ============================================================
# SEND MESSAGE BACK
# ============================================================
def send_message(recipient_id: str, text: str):
    url = f"https://graph.facebook.com/v21.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}

    try:
        r = requests.post(url, json=payload, headers=headers, params=params)
        print(f"📤 Sent: {r.status_code} {r.text}")
    except Exception as e:
        print(f"❌ Send error: {e}")


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "CZone Dive Bot running 🤿", "version": "1.0"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
