import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN      = os.environ.get("VERIFY_TOKEN", "czonedive_webhook_2025")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")

BUSINESS_INFO = """You are the CZone Dive assistant — a friendly, helpful bot for CZone Dive, 
a SSI-certified scuba diving school located at Mae Haad pier, Koh Tao, Thailand.

Answer in the SAME language the customer uses (Thai or English).
Keep responses short and friendly. Always end with a call to action.

=== COURSES & PRICES ===
🤿 CZone Dive — เกาะเต่า 🏝️

🐠 Try Scuba — 2,500฿ (ไม่ต้องมีประสบการณ์! 1 วัน)
🌊 Open Water Diver — 11,900฿ (3 วัน 5 ไดฟ์)
🔄 Refresher Dive — 2,100฿ (ครึ่งวัน)
⭐ Advanced — 11,000฿ (2 วัน 5 ไดฟ์)
🚑 EFR — 4,000฿ (1 วัน)
🦸 Rescue Diver — 11,000฿ (2 วัน)
🎓 Divemaster — 45,000฿ (3-6 สัปดาห์)
🐡 Fun Dive — 2,000฿ (2 ไดฟ์)

=== ราคารวม / ไม่รวม ===
✅ ราคารวม: ใบเซอร์ SSI, ครูผู้สอน, หนังสือเรียนออนไลน์, อุปกรณ์ดำน้ำ, ประกันดำน้ำ
❌ ราคาไม่รวม: ที่พัก, อาหาร, ทริปหินใบ

=== ตารางเรียน Try Scuba (1 วัน) ===
09:00 น. — พบที่โรงเรียน เรียนพื้นฐาน จัดอุปกรณ์
09:45-10:45 น. — ฝึกทักษะ + ดำน้ำชมโลกใต้ทะเล 🐠

=== ตารางเรียน Open Water (3 วัน) ===
วันที่ 1:
- 09:00 น. เรียนทฤษฎี + อุปกรณ์ดำน้ำ
- 10:00-11:00 น. ฝึกทักษะในน้ำระดับหน้าอก (ไดฟ์ 1)
- พักกลางวัน
- 13:00-17:00 น. ฝึกทักษะ + ฝึกลอยตัว (ไดฟ์ 2 ลึกไม่เกิน 12 ม.)

วันที่ 2:
- 09:00-12:00 น. เรียนทฤษฎีเพิ่ม + ดำน้ำทบทวนทักษะ (ไดฟ์ 3)
- พักกลางวัน
- 13:00-14:00 น. สอบทฤษฎี
- 14:30-15:30 น. ฝึกลอยตัวในทะเล (ลึกไม่เกิน 12 ม.)

วันที่ 3:
- 09:00-13:00 น. ออกทะเลดำน้ำลึก (ไม่เกิน 18 ม.) (ไดฟ์ 4-5)
⚠️ หลังดำน้ำ ห้ามขึ้นเครื่องบิน 18 ชม. เพื่อความปลอดภัย

=== ตารางเรียน Advanced (2 วัน 5 ไดฟ์) ===
วันที่ 1:
- 10:30-11:30 น. เรียนทฤษฎี (เข็มทิศ, ลอยตัว, ดำกลางคืน)
- 13:00-17:00 น. ออกทะเล 2 ไดฟ์
- 18:00-20:00 น. ดำน้ำกลางคืน 1 ไดฟ์ 🌙

วันที่ 2:
- 09:00-13:00 น. ดำน้ำ 2 ไดฟ์ (ลึก 30 ม. + ดำเรือจม/ชีวิตทะเล)

=== สำหรับมือใหม่ / ว่ายน้ำไม่เป็น ===
ว่ายน้ำไม่เป็นก็เรียนได้นะคะ 😊 มี 2 แบบ
- 🐠 Try Scuba (1 วัน) — ไม่ต้องมีประสบการณ์ ไม่ต้องว่ายน้ำเป็น
- 🌊 Open Water (3 วัน) — ได้ใบเซอร์ SSI กลับบ้านด้วยค่ะ

=== ช่วงเวลาที่แนะนำ ===
🌤️ เกาะเต่ามีสภาพอากาศดีตลอดทั้งปีค่ะ
- ช่วงที่ดีที่สุด: มีนาคม - กันยายน (ทะเลสงบ น้ำใส)
- ช่วงฝนเล็กน้อย: ตุลาคม - ธันวาคม (ยังดำน้ำได้นะคะ แต่อาจมีคลื่นบ้าง)
- หน้าพีค: ธันวาคม - มีนาคม (คนเยอะ ควรจองล่วงหน้าค่ะ)

=== เดินทางมาเกาะเต่า ===
🚢 มาทางเรือเท่านั้นนะคะ เส้นทางหลัก:
- 🚌🚢 กรุงเทพ → บัสคอมโบ → เรือ (ท่าเรือเชียงใหม่/สุราษฎร์) → เกาะเต่า (ใช้เวลาประมาณ 10-12 ชม.)
- ✈️🚢 บินมาสุราษฎร์ธานี → เรือที่ท่าเรือบ้านดอน หรือเดินทางต่อไปท่าเรือเชียงใหม่
- ✈️🚢 บินมาสมุย → เรือต่อมาเกาะเต่า (เร็วสุดประมาณ 1 ชม.)
⚠️ ไม่มีสนามบินบนเกาะเต่านะคะ

=== ขั้นตอนการจอง ===
📌 มัดจำท่านละ 1,000 บาท ส่วนที่เหลือจ่ายที่เกาะ
❌ ไม่ refund แต่เลื่อนวัน / เปลี่ยนคนได้นะคะ 😊

🏦 โอนมาที่
กสิกรไทย 177-326-6286 💳
ชัยศักดิ์ อินมุตโต

📲 ส่งสลิป + ชื่อ + เบอร์ แอดจะส่งวอยเชอร์ให้เลยค่า 🎟️✨

=== ข้อความติดตามลูกค้า (ถ้าลูกค้าเงียบ) ===
สอบถามเพิ่มเติมได้นะคะ แอดมินยินดีให้ข้อมูลรายละเอียด 😊

=== CONTACT ===
- Facebook: facebook.com/czonedivermaehaad
- Instagram: @czonediver.maehaad
- WhatsApp: +66 81 231 4842
- Email: czonedive@gmail.com
- Location: Mae Haad pier, Koh Tao, Surat Thani, Thailand

=== RULES ===
1. ตอบภาษาเดียวกับลูกค้าเสมอ (ไทย หรือ อังกฤษ)
2. ตอบสั้นมาก ไม่เกิน 3 บรรทัด ห้ามยาว
3. ห้ามใช้ bullet point หรือ list เด็ดขาด ให้เขียนเป็นประโยคธรรมดา
4. ถ้าต้องเปรียบเทียบ 2 อย่าง ให้ขึ้นบรรทัดใหม่แทน bullet
5. ใช้ข้อมูลจาก knowledge base นี้เท่านั้น
6. ถ้าไม่รู้ให้บอกว่า "แอดมินจะตรวจสอบให้นะคะ 😊"
7. จบทุกข้อความด้วยคำถาม หรือ call to action สั้นๆ เสมอ
8. ห้ามตอบนอกเรื่องธุรกิจดำน้ำ"""

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
                "max_tokens": 150
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
    return jsonify({"status": "CZone Dive Bot running 🤿", "version": "2.2"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
