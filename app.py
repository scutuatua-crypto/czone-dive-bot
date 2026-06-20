import os
import hmac
import hashlib
import logging
import requests
from flask import Flask, request, abort
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("czone-dive-bot")

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
APP_SECRET = os.environ.get("APP_SECRET", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

claude = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = """คุณคือแอดมินของ CZone Dive ร้านสอนดำน้ำที่เกาะเต่า ตอบลูกค้าเป็นภาษาไทยเป็นหลัก
(ใช้ภาษาอังกฤษถ้าลูกค้าพิมพ์ภาษาอังกฤษมา) ด้วยน้ำเสียงเป็นกันเองและช่วยเหลือ

ข้อมูลคอร์ส (SSI Certified):
- Try Scuba (1 วัน, ไม่ต้องมีประสบการณ์): 2,500 บาท / คน
- Open Water Diver (3 วัน, 5 ไดฟ์): 11,900 บาท / คน
- Refresher (ครึ่งวัน, 1 ไดฟ์): 2,100 บาท / คน
- Advanced Open Water (2 วัน, 5 ไดฟ์): 11,000 บาท / คน
- Emergency First Response - EFR (1 วัน, ไม่มีไดฟ์): 4,000 บาท / คน
- Rescue Diver (2 วัน, 4 ไดฟ์): 11,000 บาท / คน
- Divemaster (3-6 สัปดาห์, ระดับ Pro): 45,000 บาท / คน

ที่อยู่: เกาะเต่า, สุราษฎร์ธานี
ติดต่อ: czonedive@gmail.com, WhatsApp +66 81 231 4842

ถ้าลูกค้าถามเรื่องคอร์ส ราคา หรือการจอง ให้ตอบข้อมูลด้านบนและถามว่าให้แอดมินเช็คคิวให้ไหม
ถ้าลูกค้าถามเรื่องทั่วไป (ท่องเที่ยว, สภาพอากาศ, กิจกรรม) ให้ตอบได้อย่างเป็นธรรมชาติ
ตอบสั้น กระชับ เหมาะกับแชท ไม่ต้องยาวเกินไป"""


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify the request actually came from Meta using the App Secret."""
    if not APP_SECRET:
        logger.warning("APP_SECRET not set — skipping signature verification (INSECURE)")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        APP_SECRET.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    received = signature_header.split("sha256=")[-1]
    return hmac.compare_digest(expected, received)


def ask_claude(user_message: str) -> str:
    """Get a reply from Claude. Falls back to a safe default on any failure."""
    if not claude:
        logger.error("ANTHROPIC_API_KEY not configured")
        return "ขออภัยค่ะ ระบบขัดข้องชั่วคราว รบกวนรอแอดมินตอบกลับนะคะ"
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return "ขออภัยค่ะ ระบบขัดข้องชั่วคราว รบกวนรอแอดมินตอบกลับนะคะ"


def send_reply(recipient_id: str, text: str, platform: str = "facebook"):
    """Send a reply back via the Messenger/Instagram Send API."""
    url = f"https://graph.facebook.com/v21.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            logger.error(f"Send API error ({platform}): {r.status_code} {r.text}")
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        logger.warning("Webhook verification failed: token mismatch")
        return "Forbidden", 403

    # POST: incoming message event
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.get_data(), signature):
        logger.warning("Invalid webhook signature — rejecting request")
        abort(403)

    data = request.get_json(silent=True) or {}

    try:
        for entry in data.get("entry", []):
            messaging_events = entry.get("messaging", [])
            for event in messaging_events:
                sender_id = event.get("sender", {}).get("id")
                message = event.get("message", {})

                # Skip echoes (messages the page itself sent) to avoid loops
                if message.get("is_echo"):
                    continue

                text = message.get("text")
                if not sender_id or not text:
                    continue

                platform = entry.get("messaging_product", "facebook")
                reply = ask_claude(text)
                send_reply(sender_id, reply, platform=platform)

    except Exception as e:
        logger.error(f"Error processing webhook payload: {e}")
        # Still return 200 so Meta doesn't keep retrying a malformed payload
        return "OK", 200

    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "CZone Dive Bot is running 🤿", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
