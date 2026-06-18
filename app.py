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

COURSES & PRICES:
- Try Scuba: 1 day, ฿2,500/person (no experience needed)
- Open Water Diver (OW): 3 days, 5 dives, ฿11,900/person
- Refresher Dive: half day, 1 dive, ฿2,100/person
- Advanced Adventurer (AOW): 2 days, 5 dives, ฿11,000/person
- Emergency First Response (EFR): 1 day, no diving, ฿4,000/person
- Rescue Diver: 2 days, 4 dives, ฿11,000/person
- Divemaster: 3-6 weeks, ฿45,000/person
- Fun Dive: 2 dives, ฿2,000/person (certified divers only)

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

# Groq deprecated "llama3-8b-8192" — use a currently supported model instead.
# See https://console.groq.com/docs/models for the up-to-date list.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")


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
    if not GROQ_API_KEY:
        print("Groq error: GROQ_API_KEY is not set")
        return "ขออภัยครับ ระบบมีปัญหาชั่วคราว กรุณาติดต่อ +66 81 231 4842 หรือ czonedive@gmail.com 🤿"

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": BUSINESS_INFO},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 300
            },
            timeout=20
        )

        data = response.json()

        # If Groq returned an error payload, log the real reason instead of
        # crashing on data["choices"] and printing a useless KeyError.
        if "error" in data:
            print(f"Groq API error ({response.status_code}): {data['error']}")
            return "ขออภัยครับ ระบบมีปัญหาชั่วคราว กรุณาติดต่อ +66 81 231 4842 หรือ czonedive@gmail.com 🤿"

        if not response.ok or "choices" not in data:
            print(f"Groq unexpected response ({response.status_code}): {data}")
            return "ขออภัยครับ ระบบมีปัญหาชั่วคราว กรุณาติดต่อ +66 81 231 4842 หรือ czonedive@gmail.com 🤿"

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Groq error: {e}")
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
        if not r.ok:
            print(f"Send error body: {r.text}")
    except Exception as e:
        print(f"Send error: {e}")


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "CZone Dive Bot running 🤿", "version": "2.0"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
