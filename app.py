import os
import threading
import logging
import random
import requests
from flask import Flask, render_template_string, jsonify, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Cấu hình logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

app = Flask(__name__)

# Token cố định của bạn
BOT_TOKEN = "9059045461:AAEJiXeyPOu6H4OtJvcrnV9FUDiJPQUJasg"
KEY_STORAGE_URL = "https://shopcloudphone.onrender.com/kho-key.txt"
cached_keys = []

def fetch_keys_from_web():
    try:
        response = requests.get(KEY_STORAGE_URL, timeout=10)
        if response.status_code == 200:
            keys = [line.strip() for line in response.text.splitlines() if line.strip()]
            return keys
    except Exception as e:
        print(f"Lỗi khi tải kho key: {e}")
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Xin chào {user_name}! 👋 Chào mừng bạn đến với bot phát key của ShopCloudPhone.\n\n"
        "Bấm /laykey để nhận ngay một key miễn phí nhé!"
    )

async def get_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cached_keys
    if not cached_keys:
        cached_keys = fetch_keys_from_web()

    if not cached_keys:
        await update.message.reply_text("⚠️ Kho key trên hệ thống hiện đang trống hoặc chưa có dữ liệu. Vui lòng quay lại sau!")
        return

    selected_key = random.choice(cached_keys)
    cached_keys.remove(selected_key)

    await update.message.reply_text(
        f"🎉 **Nhận key thành công!**\n\n🔑 Key của bạn: `{selected_key}`\n\n*(Hãy sao chép key để sử dụng trên hệ thống)*",
        parse_mode="Markdown"
    )

def run_telegram_bot():
    """Hàm chạy bot Telegram dưới dạng background thread độc lập"""
    try:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("laykey", get_key))
        print("🤖 Bot Telegram đang chạy ngầm trực tiếp trong Flask...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"Lỗi chạy bot: {e}")

@app.route('/')
def home():
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Gà Gaming - Telegram Bot Hub 24/7</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
                .container { max-width: 900px; width: 100%; }
                header { text-align: center; margin-bottom: 25px; }
                .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; box-sizing: border-box; }
                .status { padding: 15px; border-radius: 8px; background: #0f172a; font-weight: bold; color: #22c55e; text-align: center; border: 1px solid #334155; font-size: 16px; }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h2>🤖 Hệ Thống Treo Bot Telegram 24/7</h2>
                    <p style="color: #94a3b8; font-size: 14px;">Bot phát key đang chạy tự động trực tiếp trên server</p>
                </header>
                <div class="card">
                    <h3>⚙️ Trạng Thái Hoạt Động</h3>
                    <div class="status">🟢 Bot Telegram đang hoạt động ngầm 24/7 với Token: 9059045461...</div>
                </div>
            </div>
        </body>
        </html>
    """)

if __name__ == '__main__':
    # Khởi động Bot Telegram chạy ngầm bằng Thread ngay khi Flask vừa bật
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
