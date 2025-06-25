from flask import Flask, request
import requests
import os
import psycopg2

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)
cursor = conn.cursor()

def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

def save_to_db(image_url, description):
    cursor.execute(
        "INSERT INTO signals (image_url, description) VALUES (%s, %s)",
        (image_url, description)
    )
    conn.commit()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        # دستور start
        if text == "/start":
            welcome_text = (
                "سلام دلشاد جان!\n"
                "ربات گنج‌یاب دلشاد آماده‌ست.\n"
                "عکس از آثار باستانی بفرست تا بررسی کنم.\n"
                "برای راهنمایی بیشتر از منوی زیر استفاده کن."
            )
            keyboard = {
                "keyboard": [
                    ["/start", "راهنما"],
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            send_message(chat_id, welcome_text, reply_markup=keyboard)
            return {"status": "ok"}

        if text == "راهنما":
            help_text = (
                "🎯 کار با ربات:\n"
                "- عکس آثار باستانی بفرست\n"
                "- من عکس رو ذخیره و تفسیر می‌کنم\n"
                "- اگر سوالی داشتی بنویس"
            )
            send_message(chat_id, help_text)
            return {"status": "ok"}

        if "photo" in data["message"]:
            file_id = data["message"]["photo"][-1]["file_id"]
            get_file_url = f"{TELEGRAM_API}/getFile?file_id={file_id}"
            file_info = requests.get(get_file_url).json()
            file_path = file_info["result"]["file_path"]
            image_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"

            description = "📷 عکس ثبت شد و در حال بررسی است..."
            save_to_db(image_url, description)
            send_message(chat_id, "✅ عکس دریافت شد و ذخیره شد.")
            return {"status": "ok"}

        send_message(chat_id, "📷 لطفاً یک عکس ارسال کنید یا /start را بزنید.")
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(port=5000)