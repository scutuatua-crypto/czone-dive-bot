import os
import time
import requests
from flask import Flask, request, jsonify
from threading import Thread

app = Flask(__name__)

VERIFY_TOKEN      = os.environ.get("VERIFY_TOKEN", "czonedive_webhook_2025")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")

processed_messages = set()

# Human Takeover — เก็บเวลาที่แอดมินตอบล่าสุดต่อ conversation
# { sender_id: timestamp }
human_takeover = {}
TAKEOVER_TIMEOUT = 5 * 60  # 5 นาที

BUSINESS_INFO = """You are the CZone Dive assistant — a friendly, helpful bot for CZone Dive, 
a SSI-certified scuba diving school located at Mae Haad pier, Koh Tao, Thailand.

=== COURSES & PRICES ===
🤿 CZone Dive — เกาะเต่า 🏝️

🐠 Try Scuba — 2,500฿ (1 วัน ไม่ต้องมีประสบการณ์!)
🌊 Open Water Diver — 11,900฿ (3 วัน 5 ไดฟ์)
🔄 Refresher Dive — 2,100฿ (ครึ่งวัน)
⭐ Advanced — 11,000฿ (2 วัน 5 ไดฟ์)
🚑 EFR — 4,000฿ (1 วัน)
🦸 Rescue Diver — 11,000฿ (2 วัน)
🎓 Divemaster — 45,000฿ (3-6 สัปดาห์)
🐡 Fun Dive — 2,000฿ (2 ไดฟ์)

=== ราคารวม / ไม่รวม ===
✅ รวม: ใบเซอร์ SSI, ครูผู้สอน, หนังสือเรียนออนไลน์, อุปกรณ์ดำน้ำ, ประกันดำน้ำ
❌ ไม่รวม: ที่พัก, อาหาร, ทริปหินใบ

=== ตารางเรียน ===
ถ้าลูกค้าถามตาราง ให้ตอบแค่นี้:
"แอดจะส่งตารางเรียนให้นะคะ 📅 สอบถามเพิ่มเติมได้เลยนะคะ 😊"

=== สำหรับมือใหม่ / ว่ายน้ำไม่เป็น ===
ว่ายน้ำไม่เป็นก็เรียนได้นะคะ 😊
🐠 Try Scuba (1 วัน) — ไม่ต้องว่ายน้ำเป็น ไม่ต้องมีประสบการณ์
🌊 Open Water (3 วัน) — ได้ใบเซอร์ SSI กลับบ้าน

=== ช่วงเวลาที่แนะนำ ===
🌤️ มีนาคม - กันยายน ทะเลสงบ น้ำใส ดีที่สุดค่ะ
🌧️ ตุลาคม - ธันวาคม อาจมีคลื่นบ้าง แต่ยังดำน้ำได้นะคะ
📅 ธันวาคม - มีนาคม คนเยอะ ควรจองล่วงหน้าค่ะ

=== เดินทางมาเกาะเต่า ===
🚢 มาทางเรือเท่านั้นนะคะ
🚌 กรุงเทพ → บัสคอมโบ + เรือ ใช้เวลาประมาณ 10-12 ชม.
✈️ บินมาสุราษฎร์ธานี หรือสมุย แล้วต่อเรือมาเกาะเต่าค่ะ

=== ขั้นตอนการจอง (บอกเมื่อลูกค้าถามหรือพร้อมจองเท่านั้น) ===
💰 มัดจำท่านละ 1,000฿ ส่วนที่เหลือจ่ายที่เกาะ
❌ ไม่ refund แต่เลื่อนวัน / เปลี่ยนคนได้นะคะ 😊
🏦 กสิกรไทย 177-326-6286 ชัยศักดิ์ อินมุตโต
📲 ส่งสลิป + ชื่อ + เบอร์ แอดจะส่งวอยเชอร์ให้เลยค่า 🎟️

=== CONTACT ===
📘 Facebook: facebook.com/czonedivermaehaad
📸 Instagram: @czonediver.maehaad
📱 WhatsApp: +66 81 231 4842
📧 Email: czonedive@gmail.com
📍 Mae Haad pier, Koh Tao

=== RULES ===
1. ตอบภาษาเดียวกับลูกค้าเสมอ (ไทย หรือ อังกฤษ)
2. ตอบให้ครบตามที่ลูกค้าถาม ถ้าถามเยอะตอบเยอะ ถ้าถามสั้นตอบสั้น
3. ห้ามใช้ bullet point หรือ "-" นำหน้าเด็ดขาด ให้ขึ้นบรรทัดใหม่แทน
4. ใส่อีโมจิทุกบรรทัด ให้ดูน่ารักและเป็นกันเอง
5. ห้ามพูดเรื่องจองหรือมัดจำ จนกว่าลูกค้าจะถามเองหรือบอกว่าสนใจจอง
6. ห้ามใช้ภาษาแข็งๆ เป็นทางการ ให้ใช้ภาษาพูดสบายๆ
7. จบทุกข้อความด้วย "สอบถามเพิ่มเติมได้เลยนะคะ 😊" หรือคำถามสั้นๆ
8. ถ้าไม่รู้ให้บอกว่า "แอดมินจะตรวจสอบให้นะคะ 😊"
9. ห้ามตอบนอกเรื่องธุรกิจดำน้ำ
10. ห้ามใช้ภาษาอื่นนอกจากไทยหรืออังกฤษเด็ดขาด"""

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
                msg = event.get("message", {})
                sender_id = event["sender"]["id"]
                is_echo = msg.get("is_echo", False)

                # ถ้าแอดมินตอบเอง (is_echo = True) → บันทึก takeover
                if is_echo:
                    human_takeover[sender_id] = time.time()
                    print(f"Human takeover: {sender_id}")
                    continue

                # เช็ค dedup
                mid = msg.get("mid", "")
                if mid and mid in processed_messages:
                    continue
                if mid:
                    processed_messages.add(mid)
                    if len(processed_messages) > 1000:
                        processed_messages.pop()

                text = msg.get("text", "")
                if not text:
                    continue

                # เช็ค Human Takeover — ถ้าแอดมินตอบใน 5 นาทีที่ผ่านมา bot หยุด
                last_human = human_takeover.get(sender_id, 0)
                if time.time() - last_human < TAKEOVER_TIMEOUT:
                    print(f"Bot paused (human takeover active): {sender_id}")
                    continue

                Thread(target=handle_message, args=(sender_id, text)).start()

    return "OK", 200

def handle_message(sender_id: str, text: str):
    reply = generate_reply(text)
    send_message(sender_id, reply)

def generate_reply(user_message: str) -> str:
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": BUSINESS_INFO},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 400
            }
        )
        data = response.json()
        print(f"Groq raw response: {data}")
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq error: {e}")
        return "ขออภัยค่ะ ระบบมีปัญหาชั่วคราว กรุณาติดต่อ +66 81 231 4842 หรือ czonedive@gmail.com 🤿"

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
    return jsonify({"status": "CZone Dive Bot running 🤿", "version": "2.5"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
