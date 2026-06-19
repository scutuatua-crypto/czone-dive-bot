import os, requests
from flask import Flask, request
app = Flask(__name__)
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET": return request.args.get("hub.challenge")
    data = request.get_json()
    sender = data["entry"][0]["messaging"][0]["sender"]["id"]
    token = os.environ.get("PAGE_ACCESS_TOKEN", "")
    reply = "สนใจเรียนดำน้ำคอร์สไหนดีครับ?\n\n- Open Water 8,500 บาท\n- Advanced 8,500 บาท\n\nโอนมัดจำ 1,000 บาท\nกสิกร 177-3-26628-6\n\nให้แอดมินเช็คคิวให้เลยไหมครับ?"
    requests.post(f"https://graph.facebook.com/v21.0/me/messages?access_token={token}", 
                  json={"recipient": {"id": sender}, "message": {"text": reply}})
    return "OK", 200
if __name__ == "__main__": app.run(host="0.0.0.0", port=5000)
